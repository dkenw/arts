"""Render the running water, moving curtain, and drifting air in Still Running."""
import argparse
from pathlib import Path
import os
import shutil
import subprocess
import sys
import numpy as np
from PIL import Image, GifImagePlugin
from mask import wet_weights

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'scene'))
from color import grade_arrays,PAL
from airplate import AirPlate
from clothplate import ClothPlate
from plates import build as draw_plates

DEFAULT_MASTER=HERE.parent/'build'/'still'
WATER_FRAMES=180
COUNT=360
FPS=25
TITLE='Still-Running-flow'
PALETTE=PAL.flatten().tolist()+[0]*(768-3*len(PAL))

class Exposure:
    def __init__(self,air_path=None,cloth_path=None,*,master=DEFAULT_MASTER):
        width,height,self.lamp,self.lens,_=map(int,(master/'final.txt').read_text().split())
        self.shape=(height,width)
        self.hdr=np.fromfile(master/'final.rgb',np.float32).reshape(height,width,3)
        self.ids=np.fromfile(master/'final.id',np.uint8).reshape(self.shape)
        self.depth=np.fromfile(master/'final.depth',np.float32).reshape(self.shape)
        self.roles=np.fromfile(master/'final.roles',np.uint8)
        with Image.open(master/'print.png') as image:
            self.still=np.array(image)
        self.weights=wet_weights(master)
        self.active=self.weights>0
        self.count=int(self.active.sum())
        self.air=AirPlate(air_path,self.shape,COUNT) if air_path is not None else None
        self.cloth=ClothPlate(cloth_path,self.shape,COUNT) if cloth_path is not None else None
        self.base=self.air.clear_grains(self.hdr) if self.air else self.hdr
        self.footprint=self.active|self.air.footprint if self.air else self.active
        if self.cloth:
            self.footprint=self.footprint|self.cloth.footprint

    def grade(self,wet,frame=None):
        wet=Path(wet)
        if frame is None:
            frame=int(wet.stem.rsplit('-',1)[1])
        n=self.count
        with Path(wet).open('rb') as f:
            rgb=np.fromfile(f,np.float32,3*n).reshape(n,3)
            depth=np.fromfile(f,np.float32,n)
            ids=np.fromfile(f,np.uint8,n)
            if len(ids)!=n or f.read(1): raise ValueError(f'Incomplete pass in {wet}')
        hdr=self.base.copy()
        material=self.ids.copy()
        distance=self.depth.copy()
        blend=self.weights[self.active]
        hdr[self.active]=rgb*blend[:,None]+self.base[self.active]*(1-blend[:,None])
        material[self.active]=np.where(blend>.5,ids,material[self.active])
        distance[self.active]=depth*blend+distance[self.active]*(1-blend)
        coverage=np.fromfile(Path(wet).with_suffix('.film'),np.uint8)
        if len(coverage)!=n:
            raise ValueError(f'Incomplete wet-stock coverage for {wet}')
        # Mix the paper and water exposure ramps by camera-sample coverage at
        # their boundary. A 50% crossing then changes smoothly between frames.
        stock_adjust=np.zeros(self.shape,np.float32)
        bath=(ids==18)|(ids==48)
        stock_adjust[self.active]=np.where(bath,coverage/255.0-(ids==48),0)
        cloth_adjust=self.cloth.expose(hdr,distance,material,self.roles,frame) if self.cloth else None
        if self.air:
            self.air.illuminate(hdr,frame)
        ink=grade_arrays(hdr,material,distance,self.roles,self.lamp,self.lens,stock_adjust,cloth_adjust)
        ink[~self.footprint]=self.still[~self.footprint]
        return ink

def indexed(array):
    im=Image.fromarray(array).convert('P')
    im.putpalette(PALETTE)
    return im

def gif(frames,target,scale):
    # A few distant motes and the bath can span most of the frame. A transparent
    # index lets each update encode just the changed pixels inside that rectangle.
    def raster(a):
        im=indexed(a)
        return im if scale==1 else im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    first=raster(frames[0])
    with target.open('wb') as out:
        header,_=GifImagePlugin.getheader(first,info={'loop':0,'optimize':False})
        for block in header:out.write(block)
        previous=None
        for frame in frames:
            gc={'duration':1000//FPS,'disposal':1}
            if previous is None:
                offset=(0,0);tile=first
            else:
                y,x=np.where(frame!=previous)
                if len(x):
                    x0,y0,x1,y1=int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)
                else:
                    x0,y0,x1,y1=0,0,1,1
                patch=frame[y0:y1,x0:x1].copy()
                patch[patch==previous[y0:y1,x0:x1]]=255
                offset=(x0*scale,y0*scale);tile=raster(patch)
                gc['transparency']=255
            for block in GifImagePlugin.getdata(tile,offset=offset,**gc):
                out.write(block)
            previous=frame
        out.write(b';')

def phone_loop(frames,target):
    # Resample the entire RGB frame once, after applying the native palette.
    # A fixed 330-pixel width makes the mobile view reproducible at normal zoom.
    small=[Image.fromarray(PAL[a]).resize((330,190),Image.Resampling.LANCZOS) for a in frames]
    small[0].save(target,format='WEBP',append_images=small[1:],save_all=True,lossless=True,
                  duration=1000//FPS,loop=0,method=4)

def export(frames,out):
    out.mkdir(parents=True,exist_ok=True)
    gif(frames,out/(TITLE+'-native.gif'),1)
    gif(frames,out/(TITLE+'.gif'),2)
    phone_loop(frames,out/'Still-Running-phone.webp')
    # A continuous crop of the two light sources at 3x, sampled from the artwork.
    gif([frame[56:190,98:351] for frame in frames],out/'Still-Running-dust-detail.gif',3)
    ffmpeg=shutil.which('ffmpeg')
    if ffmpeg:
        filters=subprocess.check_output([ffmpeg,'-hide_banner','-filters'],stderr=subprocess.STDOUT)
        # The PNG palette is display-referred sRGB. A matrix conversion to
        # limited-range YCbCr must preserve those nonlinear RGB values.
        if b' zscale ' in filters:
            conversion=('scale=1584:912:flags=neighbor,format=gbrp,'
                        'zscale=matrixin=gbr:primariesin=709:transferin=iec61966-2-1:rangein=full:'
                        'matrix=709:primaries=709:transfer=iec61966-2-1:range=limited:'
                        'chromal=center:filter=spline36')
        else:
            conversion=('scale=1584:912:flags=neighbor+accurate_rnd+full_chroma_int:'
                        'in_range=pc:out_range=tv:out_color_matrix=bt709')
        frame_tags='setparams=range=limited:color_primaries=bt709:color_trc=iec61966-2-1:colorspace=bt709'
        bitstream_tags=('h264_metadata=video_full_range_flag=0:colour_primaries=1:'
                        'transfer_characteristics=13:matrix_coefficients=1')
        args=[ffmpeg,'-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24',
              '-video_size','528x304','-framerate',str(FPS),'-i','-','-vf',
              conversion+',format=yuv420p,'+frame_tags,
              '-c:v','libx264','-profile:v','high','-crf','9','-preset','slow',
              '-color_range','tv','-color_primaries','bt709','-color_trc','iec61966-2-1',
              '-colorspace','bt709','-bsf:v',bitstream_tags,'-movflags','+faststart+write_colr',
              str(out/(TITLE+'.mp4'))]
        with subprocess.Popen(args,stdin=subprocess.PIPE) as proc:
            for frame in frames:proc.stdin.write(PAL[frame].tobytes())
            proc.stdin.close()
            if proc.wait():raise RuntimeError('Video export failed.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--master',type=Path,default=DEFAULT_MASTER,
                        help='Directory of scene buffers produced by the static renderer.')
    parser.add_argument('--work',type=Path,default=Path('flow-work'))
    parser.add_argument('--output',type=Path,default=Path('.'))
    parser.add_argument('--samples',type=int,choices=[4,9,16,25,36,49,64],default=25)
    parser.add_argument('--threads',type=int,default=min(8,os.cpu_count() or 1))
    parser.add_argument('--encode-only',action='store_true')
    args=parser.parse_args();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True)
    master=args.master.resolve()
    if not (master/'final.txt').is_file():
        parser.error('The scene buffers are missing. Run the top-level render.py, or pass --master after rendering the still.')
    exposure=Exposure(master=master)
    if not args.encode_only:
        compiler=os.environ.get('CXX') or shutil.which('c++')
        draw_plates(work);exposure.active.astype('u1').tofile(work/'active.u8')
        for name in ('flow','air','cloth'):
            subprocess.run([compiler,'-std=c++17','-O3','-ffast-math','-pthread',str(HERE/(name+'.cpp')),
                            '-o',str(work/name)],check=True)
        threads=str(max(1,args.threads))
        subprocess.run([str(work/'air'),str(work),str(master)],check=True)
        subprocess.run([str(work/'cloth'),str(work),'12',threads],check=True)
        subprocess.run([str(work/'flow'),str(work),str(args.samples),threads,
                        '0',str(WATER_FRAMES-1),'1'],check=True)
    exposure=Exposure(work/'air.bin',work/'cloth.bin',master=master)
    frames=[exposure.grade(work/f'flow-{i%WATER_FRAMES:03d}.wet',i) for i in range(COUNT)]
    export(frames,args.output.resolve())

if __name__=='__main__':
    main()

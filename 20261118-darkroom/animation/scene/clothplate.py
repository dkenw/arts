"""Paired radiance exposures of the free hem and the surfaces it shades."""
from pathlib import Path
import struct
import numpy as np
from scipy.ndimage import binary_dilation

SAMPLE=np.dtype([('rgb','<f4',3),('depth','<f4'),('cotton','<f4'),('mat','u1')])

class ClothPlate:
    def __init__(self,path,shape,frames):
        self.shape=shape
        height,width=shape
        with Path(path).open('rb') as stream:
            if stream.read(8)!=b'CLOTH_01':
                raise ValueError('Unrecognized curtain pass.')
            w,h,length,n,poses=struct.unpack('<5I',stream.read(20))
            if (w,h,length)!=(width,height,frames) or not (0<n<=w*h and 2<=poses<=frames+1):
                raise ValueError('Curtain exposures do not match the camera.')
            self.pixels=np.fromfile(stream,'<u4',n)
            if len(self.pixels)!=n or self.pixels[-1]>=w*h or np.any(self.pixels[1:]<=self.pixels[:-1]):
                raise ValueError('Invalid curtain footprint.')
            self.rest=np.fromfile(stream,'<f4',n)
            self.keys=[]
            self.poses=[]
            for _ in range(poses):
                self.keys.append(struct.unpack('<I',stream.read(4))[0])
                data=np.fromfile(stream,SAMPLE,n)
                if len(data)!=n:
                    raise ValueError('Incomplete curtain pose.')
                self.poses.append(data)
            if stream.read(1) or self.keys[0]!=0 or self.keys[-1]!=frames or np.any(np.diff(self.keys)<=0):
                raise ValueError('Invalid curtain time sequence.')
            if not np.array_equal(self.poses[0],self.poses[-1]):
                raise ValueError('The curtain does not return to rest.')
        footprint=np.zeros(shape,bool)
        footprint.flat[self.pixels]=True
        self.footprint=binary_dilation(footprint,iterations=4)

    def expose(self,hdr,depth,material,roles,frame):
        right=min(np.searchsorted(self.keys,frame,side='right'),len(self.keys)-1)
        left=right-1
        f=(frame-self.keys[left])/(self.keys[right]-self.keys[left])
        a,b=self.poses[left],self.poses[right]
        delta=a['rgb']*(1-f)+b['rgb']*f
        if not np.any(delta):
            return None
        pix=self.pixels
        flat=hdr.reshape(-1,3)
        flat[pix]=np.maximum(0,flat[pix]+delta)
        depth.flat[pix]+=a['depth']*(1-f)+b['depth']*f
        # Between wholly exposed wall and wholly covered cloth, grade the weave
        # by subpixel coverage. Anchor the transfer exactly in the master pose.
        coverage=a['cotton']*(1-f)+b['cotton']*f
        original=roles[material.flat[pix]]==6
        keep_bias=np.minimum(1,np.minimum(coverage/np.maximum(self.rest,1e-6),
                                (1-coverage)/np.maximum(1-self.rest,1e-6)))
        keep_bias=np.where(coverage==self.rest,1,keep_bias)
        weight=np.clip(coverage+(original-self.rest)*keep_bias,0,1)
        measured=(b if f>=.5 else a)['mat']
        replace=(original!=(weight>.5))&((roles[measured]==6)==(weight>.5))
        material.flat[pix[replace]]=measured[replace]
        adjust=np.zeros(self.shape,np.float32)
        adjust.flat[pix]=weight-(roles[material.flat[pix]]==6)
        return adjust

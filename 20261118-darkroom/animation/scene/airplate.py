"""Sparse linear-light exposures of airborne fibres in the darkroom."""
from pathlib import Path
import struct
import numpy as np
from scipy.ndimage import binary_dilation

SAMPLE=np.dtype([('pixel','<u4'),('rgb','<f4',(3,))])

def read_exposure(stream,pixels):
    size=stream.read(4)
    if len(size)!=4:
        raise ValueError('Missing airborne exposure.')
    count=struct.unpack('<I',size)[0]
    samples=np.fromfile(stream,SAMPLE,count=count)
    if len(samples)!=count or (count and samples['pixel'].max()>=pixels):
        raise ValueError('Invalid airborne exposure.')
    return samples

class AirPlate:
    def __init__(self,path,shape,frames):
        h,w=shape
        with Path(path).open('rb') as stream:
            if stream.read(8)!=b'AIR_SE01' or struct.unpack('<III',stream.read(12))!=(w,h,frames+1):
                raise ValueError('The airborne exposures do not match the camera.')
            self.still_grains=read_exposure(stream,h*w)
            self.frames=[read_exposure(stream,h*w) for _ in range(frames+1)]
            if stream.read(1) or not np.array_equal(self.frames[0],self.frames[-1]):
                raise ValueError('The airborne loop does not close.')
        swept=np.zeros(shape,dtype=bool)
        for plate in (self.still_grains,*self.frames[:-1]):
            swept.flat[plate['pixel']]=True
        # Leave a few native pixels for the same halation and local contrast
        # used on the safelight, the sink and the rest of the still.
        self.footprint=binary_dilation(swept,iterations=4)

    def clear_grains(self,hdr):
        base=hdr.copy()
        flat=base.reshape(-1,3)
        ids=self.still_grains['pixel']
        flat[ids]=np.maximum(0,flat[ids]-self.still_grains['rgb'])
        return base

    def illuminate(self,hdr,frame):
        grains=self.frames[frame]
        hdr.reshape(-1,3)[grains['pixel']]+=grains['rgb']

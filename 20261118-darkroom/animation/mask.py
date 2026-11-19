from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt

def wet_weights(master):
    ids=np.fromfile(Path(master)/'final.id', np.uint8).reshape(304,528)
    yy,xx=np.indices(ids.shape)
    # Material IDs in the still render: bath, print, jet, and air film.
    moving=np.isin(ids,(18,48,74,113)) & (xx<260) & (yy>155)
    distance=distance_transform_edt(~moving)
    # The extended area includes the direct footprint of the wider stream,
    # glancing reflections in the inside rim and subpixel foreground occlusion.
    w=np.clip((6.4-distance)/3.5,0,1)
    return w.astype(np.float32)

if __name__=='__main__':
    import sys
    (wet_weights(sys.argv[1])>0).astype(np.uint8).tofile(Path(sys.argv[2])/'active.u8')

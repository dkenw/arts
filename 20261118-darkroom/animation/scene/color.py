"""Indexed, split-toned colour. Quantize light intensity before selecting a hue.
The four ink ramps meet in the darks, preventing mismatched-value colour speckles."""
import numpy as np
from PIL import Image,ImageFilter

SILVER='''080b15 101423 181e30 222a3d 2d394a 384c5a 466169 5a7a7c 74938c 91ab9c abc1a8 c5d0b3 dadebe e8e6c9 f2edd8 f8f3e0 fff8e9'''.split()
SMOKE='''090a15 111121 1b192d 282137 37283d 4b3045 633b4f 7b4a59 945b61 ab6e6a c18276 d49b83 e2b291 edc5a2 f5d7b6 fae5c8 fff1d8'''.split()
PAPER='''090a14 15101e 231322 36162a 501b2e 6c2536 8a323e a84345 c4574c da6d56 ea8663 f69f76 fab88a fdce9e ffddb2 ffe8c3 fff2d5'''.split()
RUBY='''080a13 130d1b 210e20 331024 4d122a 6b152f 8a1c32 a92632 c83530 e14832 f2643c fc804b ff9a5a ffb671 ffce8c ffe1a7 fff2c7'''.split()
ALL=list(dict.fromkeys(RUBY+SMOKE+SILVER+PAPER))
PAL=np.array([list(bytes.fromhex(c)) for c in ALL],np.uint8)
INDICES=np.array([[ALL.index(c) for c in row] for row in [SILVER,SMOKE,PAPER,RUBY]],np.uint8)
def blur(a,radius):
    return np.asarray(Image.fromarray(np.uint8(np.clip(a*255,0,255))).filter(ImageFilter.GaussianBlur(radius)),dtype=float)/255
def grade_arrays(hdr, ids, depth, role_table, lamp, lens, stock_adjust, cloth_adjust=None):
    h,w=ids.shape
    hdr=np.asarray(hdr,dtype=np.float32)
    # Suppress sub-pixel sampling noise only where depth, material and value agree.
    raw=hdr.copy();acc=raw*2.1;ws=np.full((h,w),2.1)
    for a,b in [(-1,0),(1,0),(0,-1),(0,1),(-1,1),(1,1),(-1,-1),(1,-1)]:
        adj=np.roll(raw,(a,b),(0,1));dz=abs(np.roll(depth,(a,b),(0,1))-depth)
        dd=np.max(np.abs(adj-raw)/(raw+.13),axis=-1)
        ok=(ids==np.roll(ids,(a,b),(0,1)))*np.exp(-(dd/.16)**2)*np.exp(-(dz/3.5)**2)
        ok*=.59 if a*b else .88
        acc+=adj*ok[:,:,None];ws+=ok
    hdr=acc/ws[:,:,None]
    mask=(ids==lamp).astype(float);halo=.51*blur(mask,4.8*w/528)+.245*blur(mask,15*w/528)
    hdr+=halo[:,:,None]*np.array([.80,.12,.038])
    hdr+=blur((ids==lens).astype(float),2.0*w/528)[:,:,None]*np.array([.09,.12,.105])
    # A little halation follows the actual bright water and nickel glints.
    # The narrow radius keeps an individual crest on the pixel grid.
    hot=np.clip((.46*hdr[:,:,0]+.39*hdr[:,:,1]+.15*hdr[:,:,2]-.42)/1.1,0,1)
    hdr+=blur(hot,1.55*w/528)[:,:,None]*np.array([.095,.041,.018])
    rr,gg,bb=hdr.transpose(2,0,1)
    Y=.43*rr+.41*gg+.16*bb
    # An S-shaped film response preserves the dense cabinet shadows and the
    # high shoulder of the exposed print, with a long range for ruby reflections.
    stops=np.array([.0005,.003,.008,.015,.027,.045,.076,.12,.185,.28,.41,.59,.83,1.12,1.50,2.15,3.20])
    yy,xx=np.indices((h,w))
    off_axis=((xx-w*.51)/(.77*w))**2+((yy-h*.50)/(.77*w))**2
    log_value=np.log2(np.maximum(Y,1e-7))
    near=16*blur((log_value+12)/16,6.2*w/528)-12
    # Light falloff at the field edges and modest local contrast retain the
    # narrow rims of metal and luminous paper without outlining every object.
    log_value+=np.clip(.34*(log_value-near),-.58,.64)-1.18*np.log2(1+off_axis)+.10
    levels=np.interp(log_value,np.log2(stops),np.arange(17))
    warmth=(rr-1.03*gg)/np.maximum(rr+.008,1e-6)
    # Mixed illumination occurs at the enlarger and on reflected stainless steel.
    roles=role_table[ids]
    # The paper and metal ramps retain the colour of mixed illumination.
    photograph=(roles==3)|(roles==7)
    warmth-=np.where(roles==1,.14,np.where(roles==2,.10,np.where(photograph,.145,0)))
    warmth-=.045*stock_adjust
    warmth-=np.where(roles==5,.125,0)
    warmth-=np.where(roles==6,.082,0)
    if cloth_adjust is not None:
        warmth-=.082*cloth_adjust
    family=np.where(warmth>.748,3,np.where(warmth>.57,2,np.where(warmth>.32,1,0)))
    levels=(levels-6.4)*1.13+6.4
    levels+=np.where(roles==1,.91,np.where(roles==2,.67,np.where(roles==3,1.38,0)))
    levels+=.71*stock_adjust
    levels+=np.where(roles==5,.48,0)
    # Wet stock reflects distinct highlights in the sink. The diffuse drying
    # sheets on the line sit lower in the print's exposure.
    levels+=np.where(roles==7,.72,0)
    bayer=np.array([[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]])/15-.5
    threshold=bayer[yy%4,xx%4]
    grain=threshold*np.where(roles==4,.37,.15)
    ix=np.clip(np.floor(levels+.5+grain),0,16).astype(np.uint8)
    sel=INDICES[family,ix]
    return sel

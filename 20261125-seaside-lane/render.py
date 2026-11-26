"""Low Gear — Edition VIII, B1 (Narrow Checker).

Draw the complete 250 × 350 painting from geometry and native-pixel strokes.
Running the script writes Low-Gear.png in the current directory.

    python -m pip install numpy Pillow
    python render.py
    python render.py --output Low-Gear.png --preview Low-Gear-4x.png

The optional preview uses 4× nearest-neighbour scaling.
"""
import argparse
import math
import random
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw

W, H = 250, 350
SCENE_SEED = 173
F = 251.
EYE = np.array([1.43,2.44,0.0])
YAW, PITCH = np.deg2rad([-13.4, -8.3])
CY = 171.
rng = random.Random(SCENE_SEED)
vec = lambda a: np.asarray(a, dtype=float)
def norm(a): return a / max(np.linalg.norm(a), 1.e-8)
def rgb(h): return np.array([int(h[i:i+2],16) for i in (0,2,4)],float)
def mix(a,b,t): return a*(1-t)+b*t
def grade(z):
    return float(np.interp(z,[-12,0,7,18,32,47,58], [2.65,0,-1.51,-4.26,-8.13,-10.91,-11.70]))
FORWARD=vec((math.sin(YAW)*math.cos(PITCH),math.sin(PITCH),math.cos(YAW)*math.cos(PITCH)))
RIGHT=vec((math.cos(YAW),0,-math.sin(YAW)))
UP=norm(np.cross(FORWARD,RIGHT))
CAM=np.stack((RIGHT,UP,FORWARD))
# The sun angle is measured from the downhill direction of the lane.
# A slight cross-street angle allows the houses to shelter the foreground.
SUN_AZIMUTH = 27.5
SUN_ELEVATION = 37.0
AZIMUTH, ELEVATION = np.deg2rad((SUN_AZIMUTH, SUN_ELEVATION))
SUN = vec((math.sin(AZIMUTH)*math.cos(ELEVATION), math.sin(ELEVATION),
           math.cos(AZIMUTH)*math.cos(ELEVATION)))
SR = norm(np.cross((0, 1, 0), SUN))
SU = norm(np.cross(SUN, SR))
LIGHT = np.stack((SR, SU, -SUN))
SZ = 2160
LP = 34.
LO = vec((0, 0))
HOUSE_MASSES = []
GROUND_POTS = []


def camera_rays(x, y):
    """World-space rays through the centres of native pixels."""
    across = ((x + .5 - W / 2) / F)[:, None]
    up = ((CY - y - .5) / F)[:, None]
    return across * RIGHT + up * UP + FORWARD


def fit_sun_map(depth, ids):
    """Fit an orthographic sun camera to every surface visible from the lane."""
    global LP, LO
    y, x = np.where(ids >= 0)
    receiver = EYE + depth[y, x, None] * camera_rays(x, y)
    projected = receiver @ LIGHT.T
    span = max(np.ptp(projected[:, 0]), np.ptp(projected[:, 1]))
    LP = min(65., (SZ - 30) / span)
    LO = vec((15 - projected[:, 0].min()*LP, 15 + projected[:, 1].max()*LP))


def open_sky(points, normals):
    """Integrate the unobstructed arc of sky above the neighboring rooflines."""
    px, py, pz = (points + normals*.055 + [0,.028,0]).T
    nx, ny, nz = normals.T
    norm_y = np.clip(ny, 0, 1)
    fraction = np.zeros(len(points))
    weights = np.zeros(len(points))
    seaward = np.zeros(len(points))
    seaward_weight = 0.
    for az in (np.arange(28) + .5) * (2*np.pi / 28):
        hx, hz = np.sin(az), np.cos(az)
        highest = np.zeros(len(points))
        for left, right, near, far, cornice in HOUSE_MASSES:
            tx0, tx1 = (left-px)/hx, (right-px)/hx
            tz0, tz1 = (near-pz)/hz, (far-pz)/hz
            entry = np.maximum(np.minimum(tx0, tx1), np.minimum(tz0, tz1))
            leave = np.minimum(np.maximum(tx0, tx1), np.maximum(tz0, tz1))
            crosses = (leave > np.maximum(entry, .025)) & (cornice > py)
            slope = (cornice - py) / np.maximum(.06, entry)
            highest = np.maximum(highest, np.where(crosses, slope, 0.))
        # A horizontal surface weights the zenith most. A vertical surface
        # weights the lower, opposite arc of sky, often screened by a house.
        up = 1. / (1. + highest*highest)
        side = 1. - (2/np.pi)*(np.arctan(highest) + highest*up)
        aperture = side + norm_y*(up-side)
        w = .07 + .65*norm_y + np.maximum(0., nx*hx+nz*hz)
        fraction += w*aperture
        weights += w
        # The bright marine layer occupies the lowest part of the seaward sky.
        # Its narrow arc is largely hidden from the upper part of the lane.
        toward_water = max(0., hz)**10
        seaward += toward_water*np.clip((.30-highest)/.27,0,1)
        seaward_weight += toward_water
    return fraction / weights, seaward / seaward_weight


# Each pigment has an occluded, a skylit, and a sunlit swatch.
MATS={}; M=[]
def mat(name,oc,sky,lit,tex='plain'):
    MATS[name]=len(M); M.append((rgb(oc),rgb(sky),rgb(lit),tex,name))
mat('asphalt','222944','586c91','c4cacb','road')
mat('roadpatch','1f2e47','546683','b9c2c5','road')
mat('stone','222f4b','5c748a','aebdc1','stone')
mat('stone2','24394f','6c8592','c2cdcb','stone')
mat('cutstone','2a3a52','748d99','d1d8d6','stone')
mat('mortar','223550','4e6277','929eab','stone')
mat('plaster','29364e','8f9cad','e0e4df','plaster')
mat('lime','2a374c','8499a2','d9e1dc','plaster')
mat('cream','3b3e54','929a9d','e6e4d8','plaster')
mat('mauve','35374f','8b929f','ddd6cc','plaster')
mat('umber','302b3a','784f4b','ae795b','wood')
mat('wood','342d40','8e6458','c7926d','wood')
mat('wood2','3d2d40','a16c55','dbab7e','wood')
mat('wood3','3c394c','957c71','d7b99e','wood')
mat('darkwood','19283c','485568','817a73','wood')
mat('soot','101b30','354555','68767d','metal')
mat('iron','17263e','475e76','93a7ad','metal')
mat('zinc','2a3a57','728998','c3d3d3','metal')
mat('edge','34445f','8f9fa6','e0e6df','metal')
mat('indigo','202c48','506789','9cabb8','metal')
mat('patina','193a48','467c80','98bbb1','metal')
mat('claytile','39354d','8c6a6b','c7947c','tile')
mat('slate','1d2e50','4b6b8c','97adc0','tile')
mat('roofrust','473f56','937977','b4a19a','sheet')
mat('slatehi','314158','69879e','b5c9d0','metal')
mat('render','24314a','667988','a9b5bc','plaster')
mat('glass','132a46','37566e','799bab','glass')
mat('glass2','23364e','546e81','9bb7bf','glass')
mat('glint','31435d','6e91a4','abcbd0','metal')
mat('blind','394055','758690','bbc8c5','metal')
mat('cloth','485574','a3b7c2','f2f0df','cloth')
mat('clothblue','2c486c','668ca5','bad4d9','cloth')
mat('petrol','163a46','48797b','8bafac','metal')
mat('signblue','1d304c','385a7a','7095a8','metal')
mat('signrim','405a70','96a9b4','c7d2d2','metal')
mat('paper','65575f','aca99f','ebdcb9','plain')
mat('ceramic','354b65','93a4ad','dce4e1','metal')
mat('pot','433142','9b664f','d19872','stone')
mat('ochre','423b4a','927357','cda779','wood')
mat('brick','583442','b76850','d88e69','stone')
mat('green0','0d2639','20504c','4c7565','leaf')
mat('green1','10323e','2e6b53','78a468','leaf')
mat('green2','153b47','387c5e','a2b76a','leaf')
mat('green3','26434a','77955e','bfc375','leaf')
mat('flower','364565','858eb3','b5bacd','plain')
mat('flowerlight','4c5a77','a2a5c4','d9d9e2','plain')
mat('grass','283e47','647f60','a2b682','leaf')
mat('rubber','0f1d30','323e51','596471','plain')
mat('wheel','25374a','788a97','c4cece','metal')
mat('van','485669','a8b5b2','e7e6d8','metal')
mat('vantrim','3f5263','789398','c4d1cd','metal')
mat('van_hi','607288','c4cdc4','f2f1e2','plain')
mat('cabin','15283c','35566d','749ca8','glass')
mat('cabin_hi','263e57','678596','abc2c5','glass')
mat('red','593346','be6157','e79073','plain')
mat('amber','88634b','d2a164','f2c582','plain')
mat('stripe','444c61','8e9d9e','cbd1c9','stone')
mat('wire','1b2b42','3a4b62','566b7d','plain')

@dataclass
class Face:
    p: np.ndarray
    m: int
    n: np.ndarray
    bias: float
    casts: bool

faces=[]; cables=[]
def face(points,m,n=None,bias=0.,casts=True):
    p=vec(points)
    if n is None:n=norm(np.cross(p[1]-p[0],p[2]-p[0]))
    faces.append(Face(p,MATS[m],vec(n),bias,casts))

def box(x0,y0,z0,x1,y1,z1,m,top=None,bias=0):
    x0,x1=sorted((x0,x1)); y0,y1=sorted((y0,y1)); z0,z1=sorted((z0,z1))
    a,b,c,d=(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)
    A,B,C,D=(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)
    for v,n,sw in [([a,b,B,A],(0,0,-1),m),([d,c,C,D],(0,0,1),m),([a,d,D,A],(-1,0,0),m),([b,c,C,B],(1,0,0),m),([A,B,C,D],(0,1,0),top or m),([a,b,c,d],(0,-1,0),m)]:
        face(v,sw,n,bias)

def rod(a,b,r,m,ends=True,nside=7,r2=None,bias=0):
    a,b=vec(a),vec(b); axis=norm(b-a)
    u=norm(np.cross(axis,[0,0,1] if abs(axis[2])<.88 else [1,0,0]))
    v=np.cross(axis,u)
    ring=np.array([u*math.cos(i*math.tau/nside)+v*math.sin(i*math.tau/nside) for i in range(nside)])
    A=a+r*ring;B=b+(r if r2 is None else r2)*ring
    for i in range(nside):
        j=(i+1)%nside;face([A[i],A[j],B[j],B[i]],m,norm(ring[i]+ring[j]),bias)
    if ends:face(A,m,-axis,bias);face(B,m,axis,bias)

def wire(a,b,sag,m='wire',width=.019):
    cables.append((vec(a),vec(b),sag,m,width))
def cam2(p):
    c=(vec(p)-EYE)@CAM.T
    return np.stack((W/2+F*c[...,0]/c[...,2],CY-F*c[...,1]/c[...,2],c[...,2]),axis=-1)

# Polygon rasterizer. The same geometry is seen by the camera and by the sun.
def clip_near(v,limit=.19):
    prev=v[-1];inside=prev[2]>=limit;out=[]
    for cur in v:
        now=cur[2]>=limit
        if now!=inside:out.append(prev+(cur-prev)*(limit-prev[2])/(cur[2]-prev[2]))
        if now:out.append(cur)
        inside=now;prev=cur
    return np.array(out)

def raster(shadow=False):
    h,w=(SZ,SZ) if shadow else (H,W)
    d=np.full((h,w),1e8); ids=None if shadow else np.full((h,w),-1,dtype=np.int32)
    for idx,fc in enumerate(faces):
        if shadow:
            if not fc.casts:continue
            v=fc.p@LIGHT.T
            sx=v[:,0]*LP+LO[0]; sy=-v[:,1]*LP+LO[1]; dep=v[:,2]
        else:
            v=(fc.p-EYE)@CAM.T
            if v[:,2].max()<.19:continue
            if v[:,2].min()<.19:v=clip_near(v)
            sx=W/2+F*v[:,0]/v[:,2];sy=CY-F*v[:,1]/v[:,2];dep=1/v[:,2]
        if sx.max()<0 or sx.min()>w or sy.max()<0 or sy.min()>h:continue
        for j in range(1,len(sx)-1):
            k=j+1
            xa,xb,xc=sx[0],sx[j],sx[k];ya,yb,yc=sy[0],sy[j],sy[k]
            x0=max(0,math.floor(min(xa,xb,xc)));x1=min(w-1,math.ceil(max(xa,xb,xc)))
            y0=max(0,math.floor(min(ya,yb,yc)));y1=min(h-1,math.ceil(max(ya,yb,yc)))
            if x1<x0 or y1<y0:continue
            den=(yb-yc)*(xa-xc)+(xc-xb)*(ya-yc)
            if abs(den)<.0001:continue
            yy,xx=np.ogrid[y0:y1+1,x0:x1+1];xx=xx+.5-xc;yy=yy+.5-yc
            u=((yb-yc)*xx+(xc-xb)*yy)/den; t=((yc-ya)*xx+(xa-xc)*yy)/den
            inside=(u>=-1e-7)&(t>=-1e-7)&(u+t<=1.0000001)
            if not np.any(inside):continue
            dd=dep[k]+u*(dep[0]-dep[k])+t*(dep[j]-dep[k])
            if not shadow:dd=1./np.maximum(dd,1e-9)
            sub=d[y0:y1+1,x0:x1+1];mask=inside&(dd<sub+1e-7);sub[mask]=dd[mask]
            if ids is not None:ids[y0:y1+1,x0:x1+1][mask]=idx
    return d,ids

class Wall:
    """Coordinates along a facade, up the wall, and toward the lane."""
    def __init__(self,base,along,out):
        self.o,self.u,self.n=vec(base),vec(along),vec(out)
    def pt(self,s,h,k=0):return self.o+s*self.u+vec((0,h,0))+k*self.n
    def patch(self,s,h,S,H,k,m,bias=0):
        self.shape([(s,h),(S,h),(S,H),(s,H)],k,m,bias)
    def shape(self,pts,k,m,bias=0):
        face([self.pt(s,h,k) for s,h in pts],m,self.n,bias,False)
    def solid(self,s,h,S,H,k,K,m,top=None,bias=0):
        a=self.pt(s,h,k);b=self.pt(S,H,K)
        box(*a,*b,m,top,bias)
    def beam(self,a,b,r,m):
        rod(self.pt(*a),self.pt(*b),r,m,nside=6)
    def pipe(self,s,h,H,k=.11,m='zinc',r=.047):
        p=self.pt(s,h,k);q=self.pt(s,H,k)
        rod(p,q,r,m,nside=7)
        for t in np.arange(h+.22,H-.06,1.15):rod(self.pt(s,t,k),self.pt(s,t+.045,k),r+.014,'iron',nside=6)
    def sign(self,s,h,w=.25):
        self.solid(s,h,s+w,h+w*1.4,.018,.05,'patina')
        self.patch(s+.033,h+.043,s+w-.027,h+w*1.4-.032,.052,'petrol')
        for a in [.25,.57]:
            self.patch(s+w*a,h+w*.52,s+w*(a+.10),h+w*.98,.057,'paper')
        self.patch(s+w*.20,h+w*.27,s+w*.8,h+w*.32,.057,'paper')

def window(w,s,h,width,height,frames=2,kind='glass',wood='darkwood',ledge=True):
    e=.07
    w.solid(s-.038,h-.04,s+width+.038,h+height+.045,.008,.06,wood,bias=-.03)
    w.patch(s,h,s+width,h+height,.066,'soot',-.10)
    dx=(width-e)/frames
    for i in range(frames):
        a=s+e+i*dx; b=s+(i+1)*dx
        if kind=='slats':
            w.patch(a,h+e,b,h+height-e,.068,'wood')
            for yy in np.arange(h+e+.04,h+height-e,.093):
                w.patch(a,yy,b,yy+.035,.072,'wood2',.02)
        elif kind=='screen':
            w.patch(a,h+e,b,h+height-e,.07,'blind',-.035)
            for t in range(1,7):
                y=h+height*t/7
                w.patch(a,y,b,y+.028,.076,wood)
            for xx in np.arange(a+.18,b-.06,.21):w.patch(xx,h+e,xx+.027,h+height-e,.076,wood)
        else:
            w.patch(a,h+e,b,h+height-e,.07,'glass' if i%3!=1 else 'glass2')
            # Reflected eaves break the sky in the upper panes.
            y=h+height*(.63+.06*math.sin(s+i*31))
            w.shape([(a,y+.05),(b,y-.09),(b,h+height-e),(a,h+height-e)],.073,'glass2' if i%3!=1 else 'glint',-.025)
            if (i+frames)%3==0:
                w.patch(a+.025,h+.09,a+.14,h+height-.1,.077,'blind',-.04)
            if height>1.2:
                w.patch(a,h+height*.32,b,h+height*.32+.04,.08,wood)
    w.patch(s+.016,h+.035,s+width-.016,h+.064,.083,'iron')
    if ledge:w.solid(s-.10,h-.09,s+width+.10,h-.025,0,.15,'zinc','edge')

def siding(w,s,h,width,height,vertical=False):
    w.patch(s,h,s+width,h+height,.009,'wood')
    if vertical:
        xx=s
        while xx<s+width:
            n=min(s+width,xx+rng.uniform(.15,.24))
            w.patch(xx+.009,h,n-.012,h+height,.014,rng.choice(['wood','wood2','wood','umber','darkwood']),rng.uniform(-.025,.03))
            xx=n
    else:
        yy=h+.08
        while yy<h+height:
            hh=min(h+height,yy+.16)
            w.patch(s,yy,s+width,hh,.016,rng.choice(['wood','wood','wood2','umber']))
            yy=hh+.014
    for x in [s,s+width-.080]:
        w.solid(x,h,x+.08,h+height,0,.062,'darkwood')

def awning(w,s,h,width,deep=.68,m='patina',drop=.18):
    a=w.pt(s,h,.01);b=w.pt(s+width,h,.01);c=w.pt(s+width,h-drop,deep);d=w.pt(s,h-drop,deep)
    n=norm(np.cross(b-a,d-a))
    if n[1]<0:n=-n
    face([a,b,c,d],m,n)
    face([a,b,c,d]-np.array([0,.057,0]),'darkwood',-n)
    face([d,c,c-vec((0,.084,0)),d-vec((0,.084,0))],'iron',w.n)
    for x in np.arange(s+.18,s+width-.1,.43):
        p=w.pt(x,h+.008,.012);q=w.pt(x,h-drop+.009,deep)
        face([p,p+w.u*.022,q+w.u*.022,q],m,n,.085)
    for x in [s+.12,s+width-.15]:w.beam((x,h-.43,.045),(x,h-drop-.05,deep-.08),.037,'iron')
    return d,c

def roof(x0,x1,z0,z1,base,loft,m='slate',axis='z',over=.32):
    # Roof ridge direction and two pitches. End fascias enclose both roof sections.
    if axis=='z':
        lo,hi=x0-over,x1+over;u0,u1=z0-over,z1+over
        def xyz(t,y,u):return vec((t,y,u))
    else:
        lo,hi=z0-over,z1+over;u0,u1=x0-over,x1+over
        def xyz(t,y,u):return vec((u,y,t))
    mid=(lo+hi)/2;rh=base+loft
    for a,b,y,Y in [(lo,mid,base,rh),(mid,hi,rh,base)]:
        q=np.array([xyz(a,y,u0),xyz(a,y,u1),xyz(b,Y,u1),xyz(b,Y,u0)])
        n=norm(np.cross(q[1]-q[0],q[3]-q[0]))
        if n[1]<0:n=-n
        face(q,m,n)
        face(q-vec((0,.105,0)),'darkwood',-n)
        for i,j in [(0,1),(2,3),(1,2),(3,0)]:
            a0,b0=q[i],q[j]
            N=norm(np.cross(b0-a0,vec((0,1,0))))
            face([a0,b0,b0-vec((0,.11,0)),a0-vec((0,.11,0))],'iron',N)
        for u in [u0+.02,u1-.02]:
            rod(xyz(a,y+.02,u),xyz(b,Y+.02,u),.052,'slatehi' if m=='slate' else m,nside=5)
    for u in [u0+over,u1-over]:
        mll='plaster' if m=='slate' else 'cream'
        face([xyz(lo+over,base-.01,u),xyz(hi-over,base-.01,u),xyz(mid,rh-.095,u)],mll,(0,0,-1 if u<u1-over else 1) if axis=='z' else (-1 if u<u1-over else 1,0,0))
    rod(xyz(mid,rh+.003,u0-.07),xyz(mid,rh+.003,u1+.07),.103,'slatehi' if m=='slate' else 'wood2',nside=7)
    for t in (lo,hi):
        rod(xyz(t,base-.08,u0),xyz(t,base-.08,u1),.065,'iron',nside=6)

def masonry(w,s,h,wd,ht,course=.35,stone='stone',seed=0):
    r=random.Random(seed+83)
    w.patch(s,h,s+wd,h+ht,.015,'mortar')
    y=h
    while y<h+ht-.035:
        Y=min(h+ht,y+r.uniform(.84,1.13)*course);x=s-r.uniform(.1,.7)
        while x<s+wd:
            xx=x+r.uniform(1.16,2.8)*course;a=max(s+.006,x+.012);b=min(s+wd-.006,xx-.014)
            if b>a+.04:
                # Chipped edges, a few discoloured courses, and recessed mortar.
                chip=min((b-a)*.17,r.uniform(.014,.065))
                w.shape([(a,y+.035),(a+chip,y+.014),(b-.024,y+.014),(b,y+.052),(b-.008,Y-.037),(b-chip,Y-.009),(a+.018,Y-.016),(a,Y-.053)],.023+r.uniform(0,.006),stone,r.uniform(-.057,.06))
            x=xx
        y=Y

def stairs(w,s,wd,base,n,rise,run):
    for i in range(n):
        near=(n-i)*run
        w.solid(s,base-.06,s+wd,base+(i+1)*rise,.01,near,'stone','stone2')
        w.patch(s+.02,base+(i+1)*rise-.043,s+wd-.02,base+(i+1)*rise-.015,near+.003,'cutstone')
def utility(w,s,h):
    w.solid(s-.02,h-.03,s+.36,h+.47,.015,.16,'iron','zinc')
    w.patch(s+.033,h+.045,s+.31,h+.43,.163,'zinc')
    w.patch(s+.085,h+.24,s+.258,h+.355,.166,'cabin')
    w.patch(s+.101,h+.27,s+.234,h+.32,.17,'glint')
    for t in [s+.08,s+.26]:w.pipe(t,.25,h,.075,'iron',.02)

def condenser(w,s,h,wd=.78):
    w.solid(s-.03,h-.07,s+wd+.03,h,.012,.34,'darkwood')
    w.solid(s,h,s+wd,h+.48,.023,.32,'zinc','ceramic')
    w.patch(s+.045,h+.045,s+wd*.70,h+.43,.323,'iron')
    for t in np.arange(h+.072,h+.44,.063):
        w.patch(s+.053,t,s+wd*.68,t+.022,.327,'glint')
    w.patch(s+wd*.82,h+.27,s+wd*.92,h+.32,.33,'ceramic')
    w.pipe(s+wd+.11,h-.53,h+.18,.10,'zinc',.031)

def balcony(w,s,h,wd):
    w.solid(s-.12,h-.15,s+wd+.12,h-.01,-.03,.79,'iron','zinc')
    w.solid(s-.13,h-.08,s+wd+.13,h-.014,.78,.84,'indigo')
    for x in np.arange(s,s+wd+.03,.43):
        w.solid(x,h-.01,x+.028,h+.79,.73,.76,'iron')
    for y,th in [(h+.77,.051),(h+.20,.04)]:
        w.solid(s-.03,y,s+wd+.06,y+th,.73,.78,'iron','zinc')
    for x in [s,s+wd]:
        w.solid(x-.025,h+.77,x+.03,h+.82,0,.77,'iron')
    for x in [s+.12,s+wd-.12]:
        w.beam((x,h-.56,.02),(x,h-.14,.70),.045,'darkwood')
def laundry(w,s,h,wd,colour='cloth'):
    # A folded sheet on a rod. Irregular lower edge and independent shaded folds.
    dep=.60
    w.beam((s-.34,h+.06,dep),(s+wd+.26,h+.06,dep),.031,'iron')
    for i in range(6):
        a=s+i*wd/6;b=a+wd/6
        heights=[.76,.79,.82,.80,.78,.75,.72]
        bumps=[-.015,.041,.055,.000,.046,.066,.005]
        p=[w.pt(a,h+.053,dep+bumps[i]),w.pt(b,h+.053,dep+bumps[i+1]),w.pt(b+.018,h-heights[i+1],dep+.03+bumps[i+1]),w.pt(a+.018,h-heights[i],dep+.03+bumps[i])]
        face(p,colour,norm(w.n*.93+w.u*(bumps[i]-bumps[i+1])*3+vec((0,.08,0))),[.025,-.04,.015,-.07,.03,-.025][i])
        if colour=='cloth':
            for level,thickness in [(.102,.026),(.17,.016)]:
                A=p[3]+vec((0,level,0))+.004*w.n
                B=p[2]+vec((0,level,0))+.004*w.n
                face([A,B,B+vec((0,thickness,0)),A+vec((0,thickness,0))],'clothblue',w.n,-.023,False)
    for x in [s+.07,s+wd-.08]:
        w.solid(x,h+.01,x+.038,h+.13,dep-.016,dep+.042,'ochre')

def groundp(x,z,lift=0):
    return (x,grade(z)+lift,z)
def ground_poly(xz,m,lift=.008,bias=0):
    face([groundp(x,z,lift) for x,z in xz],m,(0,.989,.15),bias,False)
def edges(z):
    # Surveyed separately so drain covers follow each setback at the pinch points.
    zz=[-12,0,7,10.5,11.9,13.65,16.7,18.8,21.8,24.9,29.0,32,36,44,49]
    left=[-2.65,-2.56,-2.58,-2.63,-2.56,-1.78,-1.77,-1.78,-1.44,-.05,.08,-.28,-.45,-1.04,-1.29]
    right=[2.07,2.12,2.22,2.30,2.40,2.56,2.68,3.02,3.18,3.85,4.06,3.51,3.59,3.70,3.0]
    return float(np.interp(z,zz,left)),float(np.interp(z,zz,right))
def terrain():
    # Sea-facing street changes grade twice and doglegs around the lower terrace.
    stops=sorted(set([-11,0,7,10.5,11.9,13.65,16.7,18,18.8,21.8,24.9,25,29.,32,33,36,44,47,49]+list(range(-9,50,3))))
    for a,b in zip(stops,stops[1:]):
        L,R=edges(a);l,r=edges(b)
        for x,X,u,U,m,y in [(-25,L,-25,l,'stone',-.04),(L,R,l,r,'asphalt',0),(R,27,r,27,'stone',-.04)]:
            ground_poly([(x,a),(X,a),(U,b),(u,b)],m,y)
    for side in (-1,1):
        t=-8.
        def edgeat(z):return edges(z)[int(side>0)]
        while t<47:
            s=t+rng.uniform(.65,1.13)
            e,E=edgeat(t),edgeat(s); width=.31 if side>0 else .25
            # Roadside precast drains, each slab seats against the next one.
            z=t+.014;S=s-.014
            ground_poly([(e,z),(e-side*width,z),(E-side*width,S),(E,S)],'stone2',.033,rng.uniform(-.055,.02))
            ground_poly([(e+.013*side,z),(e+side*.10,z),(E+side*.10,S),(E+.013*side,S)],'cutstone',.082,.01)
            if side>0 and (1.8<t<5.5 or 10.0<t<11.5 or 18<t<19):
                a=t+.12;b=s-.12
                A,B=edgeat(a),edgeat(b)
                ground_poly([(A-side*.025,a),(A-side*.27,a),(B-side*.27,b),(B-side*.025,b)],'iron',.047,-.05)
                for v in np.arange(a+.047,b-.025,.085):
                    G=edgeat(v)
                    ground_poly([(G-.043,v),(G-.248,v),(G-.248,v+.031),(G-.043,v+.031)],'soot',.050,-.14)
            else:
                z=t+(s-t)*.21;G=edgeat(z)
                ground_poly([(G-side*.065,z),(G-side*.18,z),(G-side*.18,z+.034),(G-side*.065,z+.034)],'iron',.042,-.035)
            t=s
    # Settled asphalt around a buried utility line.
    def seam(points,w=.011):
        for (x,z),(X,Z) in zip(points,points[1:]):
            ground_poly([(x-w,z),(x+w,z),(X+w,Z),(X-w,Z)],'iron',.014,-.02)
    seam([(-1.45,3),(-1.35,3.7),(-1.39,3.98),(-1.19,4.40),(-1.06,4.64),(-.97,5.35),(-.90,5.40),(-.93,6.03)])
    seam([(-1.33,4.13),(-1.53,4.34),(-1.82,4.47),(-1.90,4.66)],.009)
    # A cast-iron access cover, set into the incline.
    x,z=.72,5.04
    for rr,dh,ma in [(.325,.015,'roadpatch'),(.287,.020,'iron'),(.253,.024,'soot'),(.227,.028,'iron')]:
        ground_poly([(x+rr*math.cos(t*math.tau/28),z+rr*math.sin(t*math.tau/28)) for t in range(28)],ma,dh)
    for k in range(-2,3):
        for j in range(-2,3):
            X=x+k*.071+(.021 if j%2 else 0);Z=z+j*.067
            if (X-x)**2+(Z-z)**2<.18**2:
                ground_poly([(X-.024,Z),(X,Z+.015),(X+.024,Z),(X,Z-.014)],'soot',.031)
    # The protective roadside barrier follows the last terrace above the shore.
    for x0,x1 in [(-9,-2.8),(3,9)]:
        base=grade(44);box(x0,base,44,x1,base+.38,44.33,'stone','cutstone')
        for t in np.arange(x0+.24,x1,.92):rod((t,base+.38,44.13),(t,base+1.03,44.13),.03,'zinc')
        rod((x0,base+1.03,44.13),(x1,base+1.03,44.13),.032,'zinc')

def make_house(x0,x1,z0,z1,h,wall,axis,loft,roofmat,raised=.22):
    b=grade(z0)+raised
    HOUSE_MASSES.append((x0,x1,z0,z1,b+h+.32*loft))
    box(x0,grade(z1)-.37,z0,x1,b,z1,'render','cutstone')
    box(x0,b,z0,x1,b+h,z1,wall)
    roof(x0,x1,z0,z1,b+h,loft,roofmat,axis)
    side=1 if x1<.5 else -1
    w=Wall((x1 if side==1 else x0,b,z0),(0,0,1),(side,0,0))
    f=Wall((x0,b,z0),(1,0,0),(0,0,-1))
    return w,f,b

def buildings():
    # First left-hand house: cedar underneath lime plaster and an occupied upstairs.
    w,f,b=make_house(-8.40,-3.30,2.65,12.10,4.91,'plaster','x',1.52,'slate',.17)
    siding(w,.01,0,9.41,2.14,True)
    w.solid(.0,2.06,9.44,2.20,.01,.13,'darkwood')
    window(w,.54,.16,1.67,1.81,3,'screen')
    window(w,2.53,.74,1.71,1.13,3,'glass')
    window(w,4.79,.22,1.63,1.63,3,'slats')
    window(w,6.66,.59,1.68,1.30,2,'glass')
    awning(w,.20,2.39,8.92,.69,'indigo',.22)
    w.solid(.22,2.46,.31,4.85,0,.045,'wood')
    w.solid(9.17,2.37,9.28,4.85,0,.05,'wood2')
    for x,wd in [(1.0,2.3),(3.99,1.76),(6.26,2.26)]:
        window(w,x,2.87,wd,1.53,3,'glass',wood='wood')
    balcony(w,3.79,2.69,4.97)
    laundry(w,5.66,4.15,.46,'clothblue')
    w.pipe(8.99,-1.39,4.85,.105,'patina',.058)
    w.sign(8.54,1.53)
    utility(w,1.92,1.23)
    zbase=grade(8.4)
    ww=Wall((-2.65,zbase-1.02,7.5),(0,0,1),(1,0,0))
    masonry(ww,.0,0,4.58,1.29,.34)
    # A heavy near return, partly outside the frame.
    w0,f0,bb=make_house(-7.64,-2.31,-4.7,2.26,4.14,'mauve','x',.84,'slate',.09)
    siding(w0,0,0,6.94,2.22,False);window(w0,3.30,.42,2.5,1.52,4,'screen')
    awning(w0,2.1,2.39,4.82,.69,'patina')
    # Across the break: a narrower ochre timber house with a gabled end looking uphill.
    w,f,b=make_house(-7.37,-1.92,13.65,18.67,4.03,'cream','z',1.26,'slate',.08)
    siding(f,.0,.04,5.16,2.04,False)
    window(f,2.00,.18,1.38,1.72,3,'slats')
    window(f,3.66,.79,1.17,.92,2)
    awning(f,.28,2.18,4.74,.48,'patina')
    window(f,.75,2.68,1.62,1.04,3,'glass','wood')
    window(f,3.05,2.68,1.71,1.04,3,'glass','wood')
    siding(w,0,.02,5.60,1.76)
    window(w,.81,2.37,2.27,1.44,3)
    w.pipe(4.87,-.51,4.20,.09)
    condenser(w,.87,.80,.71)
    # The low plaster return and a stepped garden wall following the road.
    for a,d,x,h in [(19.1,22.5,-2.14,1.37),(22.5,25.6,-1.58,1.15),(26,29.3,-.87,.81)]:
        t=grade(a)+h
        box(x-3.2,grade(d)-.25,a,x,t,d,'render','stone2')
        box(x-3.26,t,a-.04,x+.038,t+.081,d+.04,'cutstone','stone2')
        wall=Wall((x,grade(d)-.12,a),(0,0,1),(1,0,0));masonry(wall,0,0,d-a,t-grade(d)+.12,.32,seed=int(a))
    w,f,b=make_house(-7.85,-3.51,20.0,25.5,2.75,'lime','x',1.12,'slate',.14)
    window(f,1.26,.66,2.4,1.27,3);window(w,1.16,.59,2.02,1.26,3)
    w,f,b=make_house(-9.3,-3.90,29.8,34.9,2.66,'plaster','z',1.01,'slate',.08)
    window(f,2.84,.84,1.92,1.09,3,'screen')
    # Right, a stone terrace holding a house back from the road.
    for a,d,h in [(-4.,2.25,1.32),(2.25,5.33,1.37),(5.33,8.32,1.27)]:
        x=2.19 if a<5 else 2.27;B=grade(a)+h
        box(x,grade(d)-.43,a,7.6,B,d,'stone','stone2')
        wa=Wall((x,grade(d)-.32,a),(0,0,1),(-1,0,0))
        masonry(wa,0,.0,d-a,B-grade(d)+.32,.43,'stone',int(d*3))
        box(x-.07,B-.03,a-.013,x+.38,B+.092,d+.008,'stone2','cutstone')
    w,f,b=make_house(3.84,9.15,-1.95,6.05,4.32,'lime','z',1.22,'slate',1.52)
    siding(w,.02,.04,7.96,1.29,True);window(w,3.92,1.45,2.8,1.52,4)
    awning(w,3.58,3.28,3.5,.64,'slate')
    # Recessed threshold at the next house has its own stoop.
    w,f,b=make_house(3.25,7.74,9.26,16.63,4.99,'lime','x',1.13,'slate',.47)
    w.solid(.0,.02,7.35,.51,.01,.045,'render')
    window(w,.84,.16,1.62,2.02,3,'screen','wood')
    stairs(w,.65,2.03,-.42,3,.15,.18)
    window(w,3.34,.91,1.58,1.16,2,'slats')
    awning(w,.47,2.41,2.52,.65,'patina')
    window(w,1.02,3.05,2.16,1.38,2,'glass','iron')
    window(w,4.19,3.06,1.83,1.39,2,'glass','iron')
    w.pipe(7.10,-.83,4.98,.105,'zinc',.057)
    utility(w,5.59,1.32);w.sign(.30,1.67)
    window(f,.50,3.02,1.76,1.44,3,'glass','wood')
    window(f,2.73,3.02,1.39,1.44,2,'slats','wood')
    window(f,2.36,.82,1.89,1.10,3,'glass')
    condenser(f,.75,1.02)
    # A low wall and a small corrugated lean-to on the seaward side.
    w,f,b=make_house(3.52,8.70,17.72,23.1,2.80,'mauve','z',1.14,'claytile',.08)
    window(f,.41,.73,1.8,1.11,3,'glass');window(w,1.41,.45,2.31,1.56,3,'slats')
    awning(f,.20,2.15,2.27,.58,'indigo')
    w,f,b=make_house(5.31,10.1,25.6,31.36,2.46,'cream','x',.80,'slate',.06)
    window(f,.55,.63,1.71,1.13,3,'glass')
    for a,d in [(19.36,23.15),(23.16,26.25),(27.1,32.45)]:
        x=edges(d)[1]+.32;B=grade(a)+.68
        box(x,grade(d)-.22,a,x+.29,B,d,'plaster','cutstone')
        box(x-.044,B,a-.04,x+.34,B+.07,d+.03,'slatehi')
    # A few lower roofs at the edge of the village, subordinate to the blue opening.
    for x,z,lenx,lenz in [(-8,37.8,4.3,4.2),(7.1,37.0,5.02,5.4),(-13.3,35,4,4)]:
        w,f,b=make_house(x,x+lenx,z,z+lenz,2.70,'lime','x' if x<0 else 'z',.91,'slate',.10)
        window(f,.54,.54,1.28,1.25,2)

def lived_in():
    """Small alterations accumulated over the lifetime of the buildings."""
    z0=2.65;left=-3.30;b=grade(z0)+.17
    w=Wall((left,b,z0),(0,0,1),(1,0,0))
    # Old gable boards, shaped fascias and the louvred attic vent.
    w.solid(.015,4.81,9.43,4.94,-.02,.125,'wood','wood2')
    for x,y,X,Y in [(.02,4.94,4.70,6.32),(4.70,6.32,9.41,4.94)]:
        w.shape([(x,y),(X,Y),(X,Y-.11),(x,y-.11)],.045,'wood')
    w.solid(4.66,4.91,4.75,6.23,0,.058,'wood2')
    w.solid(4.05,5.08,5.38,5.65,.022,.082,'wood2')
    w.patch(4.12,5.14,5.31,5.57,.085,'soot')
    for y in [5.19,5.29,5.39,5.49]:
        w.patch(4.11,y,5.31,y+.035,.089,'wood')
    # A light sheet, caught on the front of the upper gallery where it can dry.
    laundry(w,3.07,3.90,1.37,'cloth')
    for u in [3.0,4.57]:
        w.beam((u,3.1,.1),(u,3.97,.66),.026,'iron')
    # Blinds partly lowered on two upstairs panes, with actual rolled hems and cords.
    for u,v,wd,ht in [(1.08,4.37,1.18,.76),(6.35,4.36,.74,.53)]:
        w.patch(u,v-ht,u+wd,v,.117,'ochre')
        for y in np.arange(v-ht+.022,v-.035,.052):
            w.patch(u,y,u+wd,y+.018,.125,'wood2')
        for x in [u+.11,u+wd-.10]:
            w.patch(x,v-ht,x+.026,v,.13,'wood')
        w.beam((u-.024,v-ht,.127),(u+wd+.02,v-ht,.127),.032,'wood')
    # Ceramic pans wrap the edge of the long lower roof. Some ends catch the sky.
    de=.91
    awning(w,.03,2.49,9.27,de,'slate',.27)
    for u in np.arange(.08,9.28,.23):
        w.beam((u,2.498,.05),(u,2.23,de+.045),.056,'slate')
        p=w.pt(u,2.23,de+.047)
        w.shape([(u-.048,2.245),(u-.017,2.276),(u+.033,2.267),(u+.05,2.238),(u+.04,2.197),(u-.028,2.195)],de+.053,'slatehi',-.03)
    for u in [.24,1.62,3.11,4.61,6.08,7.61,9.05]:
        w.beam((u,2.31,.05),(u,2.15,.82),.050,'wood')
    # A glass sliding doorway, its partly drawn cotton curtain and red post box.
    window(w,2.48,.093,1.90,1.94,3,'glass','wood2')
    w.patch(2.562,.568,3.05,1.891,.091,'cabin')
    w.shape([(2.56,1.89),(3.04,1.89),(2.91,1.44),(2.79,1.14),(2.67,.69),(2.56,.67)],.099,'blind')
    w.solid(3.10,.67,3.132,1.04,.08,.121,'iron')
    for u in [2.58,3.19,3.78]:w.patch(u,.35,u+.50,.371,.098,'wood')
    w.solid(2.016,1.06,2.43,1.42,.05,.235,'brick','red')
    w.patch(2.052,1.30,2.39,1.345,.24,'darkwood')
    w.patch(2.126,1.15,2.27,1.195,.241,'paper')
    w.patch(.37,1.46,.63,1.76,.072,'patina')
    w.patch(.41,1.52,.590,1.55,.075,'paper')
    # Foundation is exposed at the downhill end. Retained earth carries the entry stoop.
    for u,U in [(0,1.85),(1.85,5.03),(5.03,7.37),(7.37,9.44)]:
        low=grade(z0+U)-b-.08
        masonry(w,u,low,U-u,-low-.005,.305,'stone',int(u*60)+55)
    for i in range(5):
        # These climb along the wall, leaving the gutter open.
        z=3.45+i*.32
        top=b+.025-i*.089
        box(-3.32,grade(z+.40)-.015,z,-2.66,top,z+.36,'stone','cutstone')
    # Simple shrine-like capped gate on the far side of the truck.
    w2=Wall((-1.94,grade(13.65)+.08,13.65),(0,0,1),(1,0,0))
    w2.sign(.19,1.47,.27)
    w2.solid(.64,.64,.98,1.16,.047,.18,'wood2')
    w2.patch(.685,.83,.94,.99,.185,'cabin')
    # Service entrance on the right, with a slatted wooden garden gate.
    y=grade(8.42)
    high=y+2.02
    for z in [8.39,9.12]:
        box(2.48,y-.12,z,2.59,high,z+.10,'darkwood','wood2')
    gw=Wall((2.51,y,8.40),(0,0,1),(-1,0,0))
    gw.patch(.10,.10,.71,1.73,.02,'darkwood')
    for u in np.arange(.105,.72,.105):
        gw.solid(u,.13,u+.077,1.77,0,.062,'wood2','wood3')
    gw.beam((.0,1.96,.04),(.82,1.96,.04),.058,'wood')
    # A foreground eave, so the lane opens between two layers of nearby shelter.
    rw=Wall((3.84,0,-1.95),(0,0,1),(-1,0,0))
    y=5.31
    awning(rw,2.80,y+.45,6.77,2.03,'slate',.59)
    rw.solid(2.73,y-.23,9.63,y-.098,1.93,2.06,'darkwood','zinc')
    for u in np.arange(2.87,9.64,.40):
        rw.beam((u,y+.31,.05),(u,y-.18,2.05),.068,'wood')
    # Capstones and a cast-iron water outlet interrupt the near stone face.
    wall=Wall((2.191,0,2.25),(0,0,1),(-1,0,0))
    B=grade(2.25)+1.37
    for u in np.arange(.05,3.08,.78):
        wall.solid(u,B+.058,min(3.08,u+.735),B+.107,-.35,.083,'stone2','cutstone')
    wall.pipe(2.50,grade(4.76)+.11,B-.19,.079,'iron',.046)
    wall.sign(2.76,B-.56,.18)
    # A low island of rooftops beyond the bend. The road turns at the quay.
    w,f,b=make_house(-3.86,-.18,24.9,29.25,2.95,'cream','x',.86,'roofrust',.06)
    window(f,1.58,.95,1.45,1.03,2,'screen')
    f.solid(.08,1.89,.71,2.30,.01,.23,'zinc')
    awning(f,1.37,2.17,1.95,.38,'indigo')
    w,f,b=make_house(3.72,7.71,32.0,35.80,2.38,'lime','z',.77,'slate',.04)
    window(f,.33,.76,1.32,1.01,2,'glass')
    for x in [-5.,-1.7,1.38,4.9]:
        z=46.7;y=grade(z)
        box(x,y,z,x+.15,y+.73,z+.16,'zinc','ceramic')
    a=grade(46.7)
    rod((-5.,a+.70,46.72),(5.05,a+.70,46.72),.035,'zinc')
    box(-7.8,a+.01,46.91,6.5,a+.29,47.53,'stone2','cutstone')
    # Roadside railing set into a low retaining terrace.
    for z in [21.3,23.0,24.7,26.4]:
        x=edges(z)[0]-.12;g=grade(z)
        rod((x,g,z),(x,g+.77,z),.035,'patina')
        if z<26.2:
            X=edges(z+1.7)[0]-.12
            rod((x,g+.77,z),(X,grade(z+1.7)+.77,z+1.7),.031,'zinc')


def finishing_details():
    w=Wall((-3.30,grade(2.65)+.17,2.65),(0,0,1),(1,0,0))
    # Recessed timber shopfronts were converted to glazed sliding panels.
    for u,wd in [(2.48,1.90),(6.66,1.68)]:
        s=u+.083;high=1.95 if u<4 else 1.82
        w.patch(s,1.47,s+wd-.15,1.51,.114,'darkwood')
        for j in range(1,6):
            x=s+(wd-.15)*j/6
            w.patch(x,1.50,x+.021,high,.112,'wood2')
    for u in np.arange(2.63,4.28,.163):
        w.patch(u,.098,u+.014,.34,.112,'darkwood')
    w.solid(4.52,.04,4.637,2.16,.01,.115,'wood2')
    w.solid(4.66,1.25,4.96,1.85,.04,.107,'signblue')
    w.patch(4.675,1.27,4.940,1.83,.109,'signrim')
    w.patch(4.687,1.29,4.925,1.81,.111,'signblue')
    # A ceramic street-number tile. The numerals are built in the facade plane.
    def stroke(pts):
        for (x,y),(X,Y) in zip(pts,pts[1:]):
            w.beam((x,y,.119),(X,Y,.119),.012,'paper')
    stroke([(4.713,1.59),(4.746,1.63),(4.746,1.46)])
    stroke([(4.79,1.61),(4.814,1.636),(4.851,1.636),(4.877,1.614),(4.873,1.572),(4.810,1.485),(4.885,1.485)])
    w.patch(4.71,1.353,4.89,1.374,.118,'paper')
    # Split knuckle, straps and splash shoe on a tarnished rainwater leader.
    w.pipe(4.32,.04,2.12,.19,'patina',.044)
    for p,q in [((4.32,2.12,.19),(4.32,2.21,.32)),((4.32,2.21,.32),(4.32,2.22,.83)),
                ((4.32,.11,.19),(4.32,-.04,.153)),((4.32,-.04,.153),(4.32,-.68,.153))]:
        w.beam(p,q,.043,'patina')
    # An exterior lamp, turned off in daylight, under the tiled canopy.
    w.beam((5.72,2.03,.08),(5.72,2.07,.35),.033,'iron')
    p=w.pt(5.72,2.06,.36)
    rod(p+vec((0,-.110,0)),p,.115,'iron',nside=10,r2=.043)
    rod(p+vec((0,-.173,0)),p+vec((0,-.112,0)),.072,'ceramic',nside=8,r2=.089)
    # Weathered patches are deliberately grouped along an exposed footing.
    for u,y,wd,h in [(5.80,-.49,.79,.13),(6.27,-.53,.51,.09),(8.01,-.31,.83,.16),
                       (8.80,-.41,.31,.09),(2.87,-.27,.43,.07)]:
        profile=[(0,.22),(.14,.34),(.19,.69),(.32,.60),(.38,1),(.53,.81),(.67,.86),
                 (.76,.49),(.92,.54),(1,.20),(.84,.06),(.63,.16),(.40,0),(.21,.11)]
        w.shape([(u+dx*wd,y+dy*h) for dx,dy in profile],.034,'render',.045)
    # A television aerial on the lower roof, visible in a gap underneath the wires.
    x,z=-1.54,26.84;y=grade(24.9)+3.88
    rod((x,y-.43,z),(x,y+1.02,z),.031,'iron',nside=6)
    a=(x-.62,y+.90,z-.32);b=(x+.58,y+.94,z+.44)
    rod(a,b,.023,'zinc',nside=6)
    for i in range(4):
        q=mix(vec(a),vec(b),.20+i*.21);v=vec((-.17+.022*i,0,.42-.050*i))
        rod(q-v,q+v,.017,'iron',nside=5)
    # Back edge of the quay. Two restrained bollards give the sea a near shore.
    # The service trench was resurfaced on the uphill side of the iron cover.
    # A worn edge pulls back into a fork just before the concrete gutter.
    ground_poly([(.76,4.73),(.89,4.73),(1.02,4.66),(1.38,4.66),(1.58,4.57),(1.90,4.58),(2.00,4.53),
                 (2.01,4.86),(1.64,4.88),(1.39,4.92),(1.11,4.92),(.97,4.97),(.85,4.97)],'asphalt',.006,-.026)
    for x,z in [(1.08,47.79),(4.24,47.79)]:
        y=grade(z)+.17
        rod((x,y,z),(x,y+.35,z),.090,'iron',nside=9)
        rod((x,y+.33,z),(x,y+.38,z),.135,'zinc',nside=9)


def vehicle_frame():
    # A long-wheelbase cab-over kei truck. Positive local Z is the nose.
    pos=vec((-1.56,grade(8.70),8.70));th=math.radians(6.3)
    longitudinal=norm(vec((math.sin(th),-.25,math.cos(th))))
    lateral=norm(vec((math.cos(th),0,-math.sin(th))))
    vertical=norm(np.cross(longitudinal,lateral))
    basis=np.array((lateral,vertical,longitudinal))
    def p(x,y,z):return pos+vec((x,y,z))@basis
    return p,basis,pos

def vehicle_shelter(receivers):
    """Fraction of the local skylight the truck hides from a road surface."""
    _, axes, origin = vehicle_frame()
    local = (receivers - origin) @ axes.T
    close = ((abs(local[:, 0]) < 4.5) & (abs(local[:, 2]) < 5.5)
             & (local[:, 1] < .37) & (local[:, 1] > -.30))
    result = np.zeros(len(receivers))
    contact = np.zeros(len(receivers))
    bounce = np.zeros(len(receivers))
    if not close.any():
        return result, contact, bounce

    x, y, z = local[close].T
    y = y + .012
    # Bed, chassis, cab below the glazing, and its narrower upper section.
    boxes = [(-.51,.263,-1.41,.51,.47,1.44), (-.727,.486,-1.643,.727,.93,.408),
             (-.726,.49,.335,.726,1.06,1.619), (-.663,1.06,.37,.663,1.69,1.39)]
    cover = np.zeros_like(x)
    total = 0.
    # A fixed cosine-weighted disk samples incident flux on the pitched road.
    # A direction that ends at a house still contributes weaker bounced light.
    samples = 256
    for i in range(samples):
        r = math.sqrt((i+.5)/samples)
        a = (i+.5)*math.pi*(3.-math.sqrt(5.))
        dx, dy, dz = r*math.cos(a), math.sqrt(1.-r*r), r*math.sin(a)
        direction = vec((dx,dy,dz)) @ axes
        wx, wy, wz = direction
        if wy <= 0.:
            continue
        visible = True
        for left, right, near, far, roof in HOUSE_MASSES:
            xa, xb = (left-origin[0])/wx, (right-origin[0])/wx
            za, zb = (near-origin[2])/wz, (far-origin[2])/wz
            enter = max(0., min(xa,xb), min(za,zb))
            leave = min(max(xa,xb),max(za,zb))
            if leave > enter and origin[1]+enter*wy < roof:
                visible = False
                break
        weight = (.24 if not visible else 1.) * (1. + 1.6*max(wz,0.)**3)
        total += weight
        blocked = np.zeros(len(x),dtype=bool)
        for x0,y0,z0,x1,y1,z1 in boxes:
            xa,xb = (x0-x)/dx,(x1-x)/dx
            za,zb = (z0-z)/dz,(z1-z)/dz
            enter = np.maximum(np.maximum(np.minimum(xa,xb),np.minimum(za,zb)),(y0-y)/dy)
            leave = np.minimum(np.minimum(np.maximum(xa,xb),np.maximum(za,zb)),(y1-y)/dy)
            blocked |= leave > np.maximum(enter,0.)
        # Intersect the actual circular tread, clipped between the two sidewalls.
        for axle in (-.988,1.035):
            oy,oz = y-.279,z-axle
            qa = dy*dy+dz*dz
            qb = oy*dy+oz*dz
            disc = qb*qb-qa*(oy*oy+oz*oz-.278**2)
            root = np.sqrt(np.maximum(disc,0.))
            first,last = (-qb-root)/qa,(-qb+root)/qa
            for side in (-.632,.632):
                xa,xb = (side-.083-x)/dx,(side+.083-x)/dx
                enter = np.maximum(np.minimum(xa,xb),first)
                leave = np.minimum(np.maximum(xa,xb),last)
                blocked |= (disc>=0.) & (leave>np.maximum(enter,0.))
        cover += weight*blocked
    cover /= total
    # A narrow seam survives at the tire contact even when a pixel straddles it.
    dx = np.maximum(abs(abs(x)-.632)-.074,0.)
    dz = np.minimum(abs(z+.988),abs(z-1.035))
    tread = np.exp(-(dx/.14)**2-(dz/.125)**2)
    # The bounding box skips negligible long-range sky occlusion.
    fade = np.clip((4.5-abs(x))/.8,0,1)*np.clip((5.5-abs(z))/1.,0,1)
    result[close] = cover*fade
    contact[close] = tread
    # Pavement outside the silhouette returns light through the gap below
    # the rear sill and the open span between the axles along either side.
    rear = np.exp(-((z+1.45)/.86)**2)*np.clip(1.-(x/.67)**4,0,1)
    side = np.exp(-((abs(x)-.64)/.43)**2)*np.clip((1.02-abs(z-.02))/.50,0,1)
    bounce[close] = np.maximum(rear,side)*cover*fade*(1.-tread)
    return result, contact, bounce


def pot_shelter(receivers):
    """Small clay and zinc pots interrupt the sky under their bellies."""
    result = np.zeros(len(receivers))
    for x0,z0,r,h in GROUND_POTS:
        # Projected solid angle of the pot belly seen from the paving below.
        x = receivers[:,0]-x0
        z = receivers[:,2]-z0
        up = grade(z0)+.050+h*.46-receivers[:,1]
        dist2 = np.maximum(x*x+z*z+up*up,.0001)
        belly = (r*.94)**2*np.maximum(0.,up)/dist2**1.5
        result = np.maximum(result,np.minimum(belly,1.))
    return result



def mini_truck():
    p,basis,pos=vehicle_frame()
    def panel(pts,m,n,bias=0):
        face([p(*v) for v in pts],m,vec(n)@basis,bias)
    def block(x,y,z,X,Y,Z,m,top=None,bias=0):
        a,b,c,d=(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)
        A,B,C,D=(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)
        for q,n,s in [([a,b,B,A],(0,0,-1),m),([d,c,C,D],(0,0,1),m),([a,d,D,A],(-1,0,0),m),([b,c,C,B],(1,0,0),m),([A,B,C,D],(0,1,0),top or m),([a,b,c,d],(0,-1,0),m)]:
            panel(q,s,n,bias)
    def tube(a,b,r,m,N=8):rod(p(*a),p(*b),r,m,nside=N)
    # Frame and tires. Both contact patches lie on the same declining street.
    block(-.51,.263,-1.41,.51,.47,1.44,'soot')
    for z in [-.988,1.035]:
        for side in [-1,1]:
            X=side*.632
            tube((X-side*.083,.279,z),(X+side*.083,.279,z),.278,'rubber',18)
            tube((X+side*.084,.279,z),(X+side*.095,.279,z),.146,'wheel',14)
            tube((X+side*.098,.279,z),(X+side*.102,.279,z),.061,'iron',10)
            for i in range(5):
                t=i*math.tau/5;u=.102*math.cos(t);v=.102*math.sin(t)
                panel([(X+side*.104,.279+u+.021,z+v),(X+side*.104,.279+u,z+v+.020),(X+side*.104,.279+u-.019,z+v),(X+side*.104,.279+u,z+v-.019)],'soot',(side,0,0))
    # Bed floor, drop sides, rim and opening tailgate.
    block(-.727,.486,-1.643,.727,.616,.408,'vantrim','van')
    for side in [-1,1]:
        X=side*.722
        block(min(X,X-side*.064),.614,-1.635,max(X,X-side*.064),.927,.41,'van')
        block(min(X+.010,X-side*.074),.913,-1.65,max(X+.010,X-side*.074),.951,.43,'van_hi')
        for y in [.733]:
            panel([(X+side*.003,y,-1.49),(X+side*.003,y,.32),(X+side*.003,y+.021,.32),(X+side*.003,y+.021,-1.49)],'vantrim',(side,0,0))
        block(X-.026,.238,-1.307,X+.026,.514,-1.266,'rubber')
    for x in np.arange(-.58,.61,.14):
        block(x,.616,-1.49,x+.021,.635,.23,'vantrim')
    block(-.72,.577,-1.67,.72,.921,-1.61,'van','van_hi')
    block(-.66,.883,-1.683,.66,.908,-1.668,'van_hi')
    for y in [.659,.778]:
        # Two shallow stiffening presses on the drop gate.
        panel([(-.505,y,-1.675),(.505,y,-1.675),(.472,y+.025,-1.675),(-.472,y+.025,-1.675)],'vantrim',(0,0,-1),-.055)
        panel([(-.470,y-.011,-1.677),(.470,y-.011,-1.677),(.505,y-.001,-1.677),(-.505,y-.001,-1.677)],'van_hi',(0,0,-1),-.025)
    for x in [-.62,.57]:
        block(x,.847,-1.688,x+.071,.935,-1.67,'iron')
        block(x-.03,.56,-1.692,x+.073,.595,-1.653,'wheel')
    block(-.69,.337,-1.662,.69,.478,-1.557,'soot','vantrim')
    for x in [-.634,.455]:
        block(x,.379,-1.673,x+.172,.458,-1.662,'red')
        block(x+.021,.381,-1.675,x+.061,.456,-1.671,'amber')
    block(-.171,.33,-1.686,.167,.480,-1.660,'amber')
    for x in [-.088,-.019,.043,.095]:
        block(x,.373,-1.690,x+.018,.416,-1.686,'soot')
    # The chamfered roof and pillars share an octagonal footprint.
    def ring(x,y,z,Z,b):
        return np.array([[-x+b,y,z],[x-b,y,z],[x,y,z+b],[x,y,Z-b],[x-b,y,Z],[-x+b,y,Z],[-x,y,Z-b],[-x,y,z+b]])
    rings=[ring(.726,.49,.335,1.619,.065),ring(.737,1.041,.329,1.638,.067),
           ring(.661,1.630,.373,1.383,.065),ring(.64,1.690,.395,1.368,.072)]
    for k in range(len(rings)-1):
        for i in range(8):
            j=(i+1)%8;o=rings[k];q=rings[k+1];s=[o[i],o[j],q[j],q[i]]
            no=norm(np.cross(q[i]-o[i],o[j]-o[i]))
            panel(s,'van' if k<2 else 'van_hi',no)
    panel(rings[-1],'van_hi',(0,1,0))
    for side in [-1,1]:
        X=side*.740
        for z in [.456,1.47]:
            panel([(X,.586,z),(X,.586,z+.013),(X,1.032,z+.013),(X,1.032,z)],'vantrim',(side,0,0),-.092)
        panel([(X,.583,.455),(X,.583,1.48),(X,.596,1.48),(X,.596,.455)],'vantrim',(side,0,0),-.086)
    # Rear cab glass, with its rubber gasket and a narrow highlight.
    def backwindow(x,y,X,Y,m,dist):
        def zval(v):return .329+(v-1.041)*.044/.589-dist
        panel([(x,y,zval(y)),(X,y,zval(y)),(X,Y,zval(Y)),(x,Y,zval(Y))],m,(0,0,-1))
    backwindow(-.515,1.107,.515,1.523,'rubber',.005)
    backwindow(-.481,1.14,.481,1.489,'cabin',.010)
    backwindow(-.473,1.393,.472,1.482,'cabin_hi',.014)
    def in_glass(x,y,offset):
        return (x,y,.329+(y-1.041)*.044/.589-offset)
    panel([in_glass(x,y,.016) for x,y in [(-.475,1.352),(-.475,1.445),(-.156,1.482),(.037,1.482),(-.198,1.414)]],'cabin_hi',(0,0,-1),.045)
    backwindow(.072,1.14,.094,1.491,'iron',.017)
    backwindow(-.430,1.145,-.204,1.230,'soot',.019)
    backwindow(.174,1.145,.375,1.211,'soot',.019)
    backwindow(-.448,1.398,-.302,1.451,'paper',.018)
    backwindow(-.432,1.41,-.35,1.436,'red',.020)
    for side in [-1,1]:
        def flank(y,z,e=.004):return (side*(.737-(y-1.041)*.076/.589+e),y,z)
        pts=[(1.098,.465),(1.101,1.50),(1.497,1.342),(1.574,1.275),(1.574,.482)]
        panel([flank(y,z) for y,z in pts],'rubber',(side,0,0))
        pts=[(1.132,.512),(1.135,1.432),(1.529,1.280),(1.533,.512)]
        panel([flank(y,z,.008) for y,z in pts],'cabin_hi',(side,0,0))
        panel([flank(y,z,.012) for y,z in [(1.133,.519),(1.135,.98),(1.528,1.193),(1.533,.512)]],'cabin',(side,0,0))
        block(min(side*.739,side*.752),.941,.535,max(side*.739,side*.752),.979,.70,'soot')
        tube((side*.716,1.061,1.35),(side*.851,1.087,1.33),.023,'iron')
        block(min(side*.815,side*.916),1.055,1.261,max(side*.815,side*.916),1.200,1.36,'iron')
    # Two shallow stackable produce crates, with openings and corner ribs.
    for x0,z0,width,depth,ma in [(-.59,-.34,.61,.60,'brick'),(-.50,-.93,.50,.45,'petrol')]:
        y=.64; top=.975 if ma=='brick' else .902
        block(x0,y,z0,x0+width,y+.048,z0+depth,'wood')
        for z in [z0,z0+depth-.04]:
            for h in [y+.06,y+.178,top-.04]:
                block(x0,h,z,x0+width,h+.037,z+.04,ma)
        for x in [x0,x0+width-.039]:
            for z in [z0,z0+depth-.045]:
                block(x,y,z,x+.04,top,z+.04,ma)
            block(x,top-.037,z0,x+.04,top,z0+depth,ma)

def leaf_lobe(p,r,ma):
    """An irregular volume of overlapping leaf sprays, with tips clustered at its edges."""
    p=vec(p);rx,ry,rz=r
    phases=[rng.uniform(-.3,.3) for _ in range(11)]
    rings=[]
    for level,scale in [(-.64,.55),(.03,1.0),(.57,.79)]:
        world=[]
        for j in range(11):
            angle=math.tau*j/11+phases[j]*.44+rng.uniform(-.075,.075)
            k=scale*rng.uniform(.80,1.16)
            world.append(p+vec((math.cos(angle)*k*rx,(level+rng.uniform(-.14,.13))*ry,math.sin(angle)*k*rz)))
        rings.append(world)
    for j in range(11):
        k=(j+1)%11
        for i in (0,1):
            a,b=rings[i],rings[i+1]
            n=norm((a[j]+b[k])*.5-p)
            face([a[j],a[k],b[k],b[j]],ma,n,rng.uniform(-.041,.022))
        face([rings[2][j],rings[2][k],p+vec((.02,ry*.91,.03))],ma,norm(vec((.3*math.cos(j*math.tau/11),.85,.3*math.sin(j*math.tau/11)))),.005)
        face([rings[0][j],rings[0][k],p-vec((0,ry*.80,0))],ma,(0,-.7,-.3),-.045)
    for j in range(int(21+max(rx,ry)*24)):
        t=rng.uniform(0,math.tau);f=rng.uniform(-.65,.84);k=math.sqrt(1-f*f)*rng.uniform(.83,1.11)
        v=p+vec((math.cos(t)*rx*k,ry*f,math.sin(t)*rz*k))
        # A branchlet ends in a small lance-shaped cluster.
        l=rng.uniform(.095,.235)*max(.42,min(1,rx+.20))
        d=vec((math.cos(t)*l,l*rng.uniform(-.62,.55),math.sin(t)*l))
        cross=vec((math.sin(t)*l*.46,l*rng.uniform(.14,.35),-math.cos(t)*l*.46))
        tone=rng.choice([ma,ma,'green2','green0' if f<0 else 'green3'])
        face([v-d*.26,v+cross*.76,v+d*1.15,v-cross*.49],tone,norm(vec((math.cos(t),rng.uniform(.22,.79),math.sin(t)))),rng.uniform(-.065,.025))

def branch(seq,radii,m='wood'):
    for a,b,r,R in zip(seq,seq[1:],radii,radii[1:]):rod(a,b,r,m,nside=7,r2=R)
def canopy():
    # The plants beyond this tree share V's deterministic random stream. Its
    # former crown consumed this many 32-bit words before those plants grew.
    for _ in range(120530):
        rng.getrandbits(32)
    # Less distinct trees across the lower terraces.
    for x,z,h,r in [(-3.35,18.7,2.57,.92),(-3.76,22.02,2.05,1.03),(4.08,21.6,2.27,.78),(-4.0,26.7,1.62,1.09),(5.7,31.9,1.78,1.23)]:
        y=grade(z)
        branch([(x,y,z),(x-.13,y+h*.69,z),(x+.13,y+h,z-.12)],[.115,.063,.025])
        for i in range(4):
            dx=rng.uniform(-.6,.60)*r;dz=rng.uniform(-.55,.6)*r
            leaf_lobe((x+dx,y+h+rng.uniform(-.17,.40),z+dz),(r*.68,r*.49,r*.66),rng.choice(['green1','green2','green3']))
def sprig(a,direction,length,width,tone,seed=None):
    """One leafy shoot. Paired blades bend about a central vein."""
    r=rng if seed is None else random.Random(seed);a=vec(a);d=norm(vec(direction));L=length
    across=norm(np.cross(d,[0,0,1.] if abs(d[2])<.85 else [0,1.,0]))
    sag=vec((.014,-.17*L,.018))
    def along(t):return a+d*t*L+sag*t*t
    tip=along(1)
    if L>.26:
        # Slender stem, visible wherever pairs of leaves part.
        face([a-across*.007,a+across*.007,along(.62)+across*.004,tip,along(.62)-across*.005],'green0',(.0,.6,-.3))
    for j in range(1,6):
        t=.14+j*.132
        for sign in [-1,1]:
            st=along(t+sign*.023)
            k=width*(1.30-.48*t)*r.uniform(.75,1.14)
            direction=norm(d*.53+across*(sign*r.uniform(.47,.94))+vec((r.uniform(-.12,.12),r.uniform(-.22,.12),r.uniform(-.29,.29))))
            end=st+direction*k; c=st+direction*k*.47
            side=norm(np.cross(direction,[0,0,1] if abs(direction[2])<.80 else [0,1,0]))*k*r.uniform(.18,.265)
            face([st,c+side,end,c-side*.74],tone,norm(vec((-.35+r.uniform(-.48,.4),.57+r.uniform(-.35,.60),-.30+r.uniform(-.28,.42)))),r.uniform(-.027,.052))

def flowering_pot():
    # Hydrangea heads grow on separate canes; individual florets share light in clumps.
    x,z=-2.33,5.49;b=grade(z)+.38
    for dx,dy,dz,rad in [(-.08,.60,-.03,.14),(.19,.67,.17,.15),(.03,.83,.24,.17),(.19,.47,-.07,.105)]:
        q=vec((x+dx,b+dy,z+dz));root=vec((x,b-.04,z))
        branch([root,(root+q)*.5+vec((.033,0,.06)),q],[.015,.012,.008],'green0')
        for j in range(4):
            a=mix(root,q,.20+j*.14)
            sprig(a,(rng.uniform(-1,1),rng.uniform(.11,.45),rng.uniform(-1,1)),.19,.14,'green2' if j%2 else 'green1')
        for j in range(36):
            t=rng.uniform(0,math.tau);u=rng.uniform(-.70,1);f=math.sqrt(1-u*u)
            v=vec((math.cos(t)*f,u,math.sin(t)*f));c=q+v*rad
            scale=rng.uniform(.026,.044)
            face([c+vec((-scale,0,0)),c+vec((-.45*scale,scale*.7,0)),c+vec((.46*scale,scale*.77,0)),c+vec((scale,-scale*.1,0)),c+vec((.1*scale,-scale*.66,0))],rng.choice(['flower','flower','flowerlight']),norm(v+vec((-.4,.42,0))),.018)

def climbing_plants():
    # The vine loops over the tiled pent roof before returning to the house.
    w=Wall((-3.30,grade(2.65)+.17,2.65),(0,0,1),(1,0,0))
    for pts in [[(1.92,-.52,.26),(1.94,.13,.22),(2.10,.63,.22),(1.95,1.08,.19),(2.12,1.32,.18),
                 (2.08,1.91,.17),(2.20,2.22,.41),(2.31,2.27,.91),(2.89,2.28,.93),(3.29,2.27,.94),(3.64,2.22,.90)],
                [(2.19,2.24,.44),(2.11,2.28,.79),(1.72,2.29,.89),(1.21,2.30,.91),(.85,2.22,.93)],
                [(2.55,2.26,.94),(2.42,2.10,.97),(2.50,1.89,1.0)]]:
        world=[w.pt(*p) for p in pts];branch(world,np.linspace(.027,.008,len(pts)),'wood')
        for i in range(1,len(pts)):
            if i<5 and pts[0][1]<0:continue
            a,b=world[i-1],world[i]
            for k in range(3):
                t=k/3+rng.uniform(0,.12);c=mix(a,b,t);v=vec((rng.uniform(.00,.25),rng.uniform(-.52,.44),rng.uniform(-.65,.65)))
                sprig(c,v,.32,rng.uniform(.12,.19),rng.choice(['green1','green2','green3']))
    # Ivy finding the joints between the cap and stone below the camera-side garden.
    for z,length in [(3.90,.65),(4.21,.84),(4.53,.55),(6.75,.57),(7.0,.49)]:
        x=2.15 if z<5.33 else 2.25;b=grade(2.25 if z<5.33 else 5.33)+(1.37 if z<5.33 else 1.27)
        path=[(x+.36,b+.12,z-.12),(x+.02,b+.14,z-.03),(x-.065,b-.07,z),(x-.082,b-length*.52,z+.07),(x-.09,b-length,z+.15)]
        branch(path,[.017,.013,.012,.009,.005],'green0')
        for j in range(1,5):
            for k in range(3):
                pos=mix(vec(path[j-1]),vec(path[j]),k/3+.08)
                sprig(pos,(-.07,rng.uniform(-.55,.04),rng.choice([-1,1])*rng.uniform(.4,1)),rng.uniform(.11,.25),rng.uniform(.070,.12),rng.choice(['green1','green2','green3']))



def garden_pot(x,z,r,ht,foliage='broad',base=None,ma='pot'):
    if base is None:
        GROUND_POTS.append((x,z,r,ht))
    y=grade(z)+.050 if base is None else base
    rod((x,y,z),(x,y+ht,z),r*.68,ma,nside=10,r2=r)
    rod((x,y+ht-.05,z),(x,y+ht+.012,z),r*1.065,ma,nside=10)
    rod((x,y+ht+.013,z),(x,y+ht+.018,z),r*.88,'darkwood',nside=10)
    for j in range(15 if foliage=='broad' else 23):
        th=rng.uniform(0,math.tau)
        u=vec((math.cos(th),0,math.sin(th)));v=vec((-math.sin(th),0,math.cos(th)))
        R=rng.uniform(.41,1.55)*r;h=r*rng.uniform(.94,2.29)*(1.27 if foliage!='broad' else 1)
        root=vec((x,y+ht,z))+u*rng.uniform(.03,.57)*r
        mid=root+u*R*.49+vec((0,h*.81,0));end=root+u*R+vec((0,h*(rng.uniform(.70,1.13)),0))
        side=r*(rng.uniform(.19,.33) if foliage=='broad' else .072)
        c=rng.choice(['green0','green1','green2','green3'])
        face([root,mid+v*side,end,mid],c,norm(u+vec((0,.38,0))))
        face([root,mid,end,mid-v*side],c,norm(u+vec((0,.88,0))),.032)

def flora():
    canopy()
    for x,z,r,h,v,m in [(-2.22,4.8,.20,.33,'broad','pot'),(-2.24,5.47,.27,.38,'broad','patina'),(-2.28,6.10,.16,.26,'grass','pot'),(-2.15,12.0,.19,.36,'broad','stone2'),(2.20,8.58,.22,.33,'broad','pot'),(2.41,12.5,.18,.29,'grass','pot'),(-1.86,19,.21,.29,'grass','ochre')]:
        garden_pot(x,z,r,h,v,ma=m)
    for x,z,h in [(2.65,6.77,1.27),(2.87,7.20,1.27),(2.73,3.1,1.37)]:
        B=grade(5.33 if z>5.33 else 2.25)+h+.01
        garden_pot(x,z,.23,.29,'broad',B,'patina')
    # A few escaped shoots at joints, kept in small, irregular clumps.
    for x,z in [(-2.32,3.89),(-2.26,6.88),(2.11,2.78),(2.15,3.05),(2.19,5.28),(2.22,5.41),(-2.42,14.5),(2.37,8.33)]:
        for j in range(rng.randint(4,10)):
            X=x+rng.uniform(-.063,.058);Z=z+rng.uniform(-.13,.14)
            p=vec(groundp(X,Z,.03));h=rng.uniform(.07,.24);end=p+vec((rng.uniform(-.10,.10),h,rng.uniform(-.09,.09)))
            face([p,p+vec((.017,0,.004)),end,p+vec((-.013,h*.38,0))],rng.choice(['grass','green2']),(.2,.8,-.2))

def poles():
    def pole(x,z,h,r,primary=True):
        B=grade(z);tip=vec((x+.075,B+h,z+.06));base=vec((x,B-.08,z))
        rod(base,tip,r,'render',nside=10,r2=r*.62)
        def anchor(y,s=0,d=0):
            t=(y-B)/(tip[1]-B)
            return vec((x+.075*t+s,y,z+.06*t+d))
        # Dark weather collars and an ochre identification strip.
        for y,th,m in [(B+.57,.28,'ochre'),(B+.91,.07,'soot'),(B+1.39,.07,'iron'),(B+h-2.15,.055,'iron'),(B+h-.48,.06,'iron')]:
            rod(anchor(y),anchor(y+th),r*(1-.37*(y-B)/h)+.009,m,nside=9)
        pins=[]
        for level in [h-.32,h-1.19]:
            y=B+level;span=.92 if primary else .57
            a=anchor(y,-span);b=anchor(y,span)
            rod(a,b,.049,'iron',nside=7)
            if primary:
                rod(anchor(y-.57,.04),anchor(y,span-.12),.028,'iron',nside=6)
            for s in [-span+.057,.035,span-.057]:
                p=anchor(y+.23,s);pins.append(p)
                rod(anchor(y,s),p,.037,'iron',nside=7)
                for dy in [.082,.144,.19]:
                    rod(anchor(y+dy,s),anchor(y+dy+.033,s),.090,'ceramic',nside=8)
        if primary:
            rod(anchor(B+h-2.11,.25,.05),anchor(B+h-1.49,.25,.05),.189,'iron',nside=12)
            rod(anchor(B+h-1.52,.25,.05),anchor(B+h-1.47,.25,.05),.210,'zinc',nside=12)
            for t in [-.065,.065]:
                rod(anchor(B+h-1.47,.25+t,.05),anchor(B+h-1.31,.25+t,.04),.046,'ceramic',nside=8)
            for i in range(6):
                y=B+h-2.5-i*.415
                rod(anchor(y,-.18 if i%2 else .02,-.009),anchor(y,-.02 if i%2 else .18,-.009),.017,'iron',nside=6)
            wire(anchor(B+h-1.11,.28),anchor(B+h-2.06,.34),.11,'soot',.02)
        return pins
    A=pole(-2.43,12.69,7.56,.159,True)
    B=pole(-1.20,25.71,5.92,.123,False)
    C=pole(-1.37,38.40,5.62,.102,False)
    # A street-side span, then three lines crossing diagonally down the lane.
    for i in [0,2,3]:
        a=A[i];k=[0,2,3].index(i)
        wire((3.29+[-.73,.80,.17][k],8.33+[.35,.41,-.76][k],1.97+[.17,-.16,.25][k]),a,.88+.05*k,'wire',.021 if k==0 else .016)
        wire(a,B[i],.76+.06*k,'wire',.020 if k==0 else .015)
        wire(B[i],C[i],.91,'wire',.017)
    # House drops follow separate paths to actual eave connections.
    for a,b,sag,rad in [
            (A[4],(3.23,grade(9.26)+4.77,10.2),.41,.016),
            (A[3],(-2.58,grade(2.65)+4.42,7.58),.34,.016),
            (A[5],(4.44,grade(4.7)+5.90,4.25),.46,.020),
            (B[3],(-3.55,grade(21)+2.99,20.55),.43,.016)]:
        wire(a,b,sag,'wire',rad)

def noise(x,y,seed):
    """Smooth value noise in material space. Used for shapes, not screen grain."""
    X=np.floor(x);Y=np.floor(y);u=x-X;v=y-Y
    u=u*u*(3-2*u);v=v*v*(3-2*v)
    def h(a,b):
        s=np.sin(a*127.1+b*311.7+seed*47.13)*43758.5453
        return s-np.floor(s)
    return mix(mix(h(X,Y),h(X+1,Y),u),mix(h(X,Y+1),h(X+1,Y+1),u),v)

# Swatches are shared between materials. The same lavender in a piece of zinc
# can turn up in a hydrangea, and the lightest enamel also edges the cloud.
INK_GROUPS = {
    'Ink and blue steel': (
        '0e1932 162543 203455 254362 2d5070 355f86 47799f 698fa8 '
        '8eacb8 adc7cc'),
    'Slate and daylight grey': (
        '2a3154 354367 374975 405381 485c89 526a93 69829c 8395a9 9aaab6 '
        'aab7bf b1bcc3 bcc5c4 c5cbc7 d5dbda e7eae5 f5f6ee'),
    'Foliage and glaze': (
        '082c3b 0b3943 0e4849 165b4d 227655 348b59 549760 '
        '80a761 9cb66c 306677 47858a'),
    'Cedar and clay': (
        '39293e 533145 743e45 90504a ac654e bd7f60 cd9a73 '
        'ac9391 b94946 d56846 e9975c e0b16d'),
    'Violet and zinc': '505576 696e91 8c8daf a8abc1 c2c7d3',
    'Coastal water': (
        '286796 2c83a6 389bb8 4ab3c9 6ac9d2 92d6d8 '
        'b5e4e0 d0efeb f5fbf3'),
    'Day sky': (
        '3a79b0 4384b6 508fbf 5b99c5 67a4ca 75afd0 82b8d5 92bfd8 '
        '9dc8dd a8d0e1 b3d8e5 bfe0e8 cbe6eb d5ecec dff1ee e7f5ef'),
}
BASE_PALETTE = tuple(bytes.fromhex(swatch)
                     for group in INK_GROUPS.values() for swatch in group.split())
INKS = np.frombuffer(b''.join(BASE_PALETTE), dtype=np.uint8).reshape(-1, 3)
SKY_BLUES = np.frombuffer(bytes.fromhex(INK_GROUPS['Day sky']), dtype=np.uint8).reshape(-1, 3)
MAX_INKS = 80


def perceptual_colors(values):
    """OKLab distances keep similar-value blues and greens distinguishable."""
    c = np.asarray(values,dtype=float)/255.
    lin = np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    lms = lin@np.array([[.41222147,.53633254,.05144599],
                        [.21190350,.68069955,.10739695],
                        [.08830246,.28171884,.62997870]]).T
    return (np.cbrt(lms)@np.array([[.21045426,.79361779,-.00407205],
                                   [1.9779985,-2.42859221,.45059371],
                                   [.02590404,.78277177,-.80867577]]).T)*[1.,1.45,1.38]


def indexed_image(indices, palette):
    """Attach ordered RGB swatches to native pixel indices."""
    if len(palette) > MAX_INKS or len(set(palette)) != len(palette):
        raise ValueError(f'The palette must contain at most {MAX_INKS} distinct inks')
    height, width = indices.shape
    image = Image.frombytes('P', (width, height), indices.astype(np.uint8, copy=False).tobytes())
    image.putpalette(b''.join(palette))
    return image


def indexed_art(image):
    pixels = np.asarray(image)
    colors, inverse = np.unique(pixels.reshape(-1, 3), axis=0, return_inverse=True)
    distances = perceptual_colors(colors)[:, None, :] - perceptual_colors(INKS)[None, :, :]
    nearest = np.argmin(np.sum(distances ** 2, axis=2), axis=1)
    return indexed_image(nearest[inverse].reshape(pixels.shape[:2]), BASE_PALETTE)


# Each contour has five guide heights and short lighter strokes along the edge.
SKY_COLUMNS = (0, 62, 124, 186, 249)
SKY_BANDS = (
    ((7, 5, 2, -1, -2), ((74, 83), (153, 158))),
    ((17, 15, 12, 9, 7), ((61, 68), (135, 143))),
    ((26, 24, 21, 19, 17), ((76, 91), (142, 148), (166, 175))),
    ((31, 29, 26, 25, 23), ((111, 124), (151, 155))),
    ((42, 40, 37, 34, 32), ((66, 73), (95, 112), (174, 181))),
    ((49, 47, 44, 43, 41), ((119, 129), (150, 156))),
    ((58, 57, 54, 52, 51), ((92, 105), (165, 173))),
    ((68, 66, 64, 62, 60), ()),
    ((74, 73, 71, 69, 68), ((159, 164),)),
    ((85, 84, 83, 82, 80), ()),
    ((94, 92, 90, 89, 88), ((129, 139), (174, 181))),
    ((102, 101, 100, 98, 97), ()),
    ((112, 111, 110, 109, 108), ((144, 151),)),
    ((121, 120, 120, 119, 118), ()),
    ((131, 131, 130, 130, 130), ()),
)
SKY_SCREEN = np.array(((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5)))


def daylight_sky():
    """Draw the sixteen blues and the narrow checker at their stepped boundaries."""
    y, x = np.indices((H, W))
    columns = np.arange(W)
    edges = []
    for heights, strokes in SKY_BANDS:
        edge = np.interp(columns, SKY_COLUMNS, heights)
        for start, end in strokes:
            taper = np.clip(np.minimum(columns - start + 1, end - columns) / 3., 0., 1.)
            edge -= .73 * taper
        edges.append(edge)
    edges = np.array(edges)
    preceding = np.vstack((2 * edges[0] - edges[1], edges[:-1]))
    following = np.vstack((edges[1:], 2 * edges[-1] - edges[-2]))
    widths = np.clip(.64 * (following - preceding), 6.5, 16.5)
    widths[0] = np.minimum(widths[0], 3.5)
    widths[1] = np.minimum(widths[1], 8.)
    widths = np.clip(.42 * widths, 2.4, 4.6)

    tone = np.zeros((H, W))
    for edge, width in zip(edges, widths):
        tone += np.clip((y - edge) / width + .5, 0, 1)
    dark = np.floor(tone).astype(np.uint8)
    coverage = np.clip((tone - dark - .09) / .82, 0, 1)
    threshold = (SKY_SCREEN[y % 4, x % 4] + .5) / 16.
    return Image.fromarray(SKY_BLUES[dark + (coverage > threshold)])


def backdrop():
    horizon=round(CY+F*math.tan(PITCH))
    pic = daylight_sky()
    d=ImageDraw.Draw(pic)
    def pg(p,c):d.polygon(p,fill=c)
    # An authored cloud profile. Sun catches its cauliflower shoulders, while the
    # undersides collect into one horizontal value and a few detached shreds drift east.
    def mark(points,offset,scale,col):
        x,y=offset;sx,sy=scale
        pg([(int(x+i*sx),int(y+j*sy)) for i,j in points],col)
    O=(58,52);S=(1.06,.88)
    crown=[(0,28),(6,28),(8,26),(12,26),(13,23),(15,22),(17,22),(17,19),(20,17),(22,17),
           (22,14),(24,13),(25,10),(29,9),(31,9),(32,7),(36,6),(38,7),(40,7),(42,9),
           (43,12),(46,13),(47,15),(50,15),(52,17),(53,20),(55,20),(57,18),(60,18),
           (61,16),(64,16),(65,14),(69,14),(72,15),(74,18),(75,20),(78,21),(79,23),
           (82,23),(84,24),(86,24),(89,26),(98,26),(100,27),(108,27),(108,28),
           (90,29),(86,30),(64,30),(57,31),(42,31),(38,30),(15,30),(14,29),(0,29)]
    mark(crown,O,S,'#f5fbf3')
    mark([(2,28),(15,27),(17,25),(24,25),(25,23),(29,23),(30,20),(34,19),(36,19),
          (38,16),(41,16),(44,18),(46,18),(47,20),(52,21),(53,23),(60,23),(61,21),
          (63,21),(66,18),(70,19),(73,21),(74,23),(79,24),(82,26),(87,27),(99,27),
          (99,28),(85,29),(64,29),(57,31),(41,31),(38,30),(17,30)],O,S,'#aacae0')
    mark([(5,27),(16,27),(19,26),(31,26),(34,24),(37,24),(38,23),(43,23),(45,25),
          (54,26),(72,26),(74,25),(81,26),(84,27),(93,27),(91,29),(61,29),(53,30),
          (37,29),(19,29)],O,S,'#c8e4e8')
    for p in [[(49,91),(58,90),(67,90),(68,89),(77,89),(77,90),(89,91),(74,92),(49,92)],
              [(146,91),(159,90),(168,90),(168,89),(178,90),(183,91),(166,92)],
              [(111,101),(123,100),(127,99),(140,100),(151,100),(152,101),(131,102)]]:
        pg(p,'#dbeef0')
    # Far island chain. Its overlapping ridges stay cooler than the sunlit sea.
    h=horizon
    pg([(0,h-5),(18,h-6),(25,h-9),(37,h-8),(47,h-12),(55,h-13),(62,h-15),(70,h-14),
        (78,h-10),(84,h-9),(93,h-12),(100,h-12),(105,h-10),(115,h-9),(122,h-6),
        (127,h-6),(136,h-3),(144,h-3),(150,h-1),(161,h),(161,h+1),(0,h+1)],'#94b1c2')
    pg([(0,h+1),(0,h-9),(24,h-13),(41,h-11),(54,h-8),(61,h-8),(75,h-10),
        (85,h-8),(98,h-5),(111,h-4),(121,h-2),(137,h-1),(140,h+1)],'#799eb4')
    pg([(158,h),(167,h-1),(174,h-3),(180,h-4),(185,h-6),(191,h-6),(202,h-10),
        (211,h-12),(214,h-11),(222,h-14),(229,h-17),(236,h-17),(249,h-24),(249,h+2),(158,h+2)],'#99b9c8')
    pg([(172,h+1),(184,h-1),(190,h-3),(196,h-3),(202,h-4),(209,h-7),(218,h-7),
        (226,h-11),(229,h-9),(234,h-10),(249,h-13),(249,h+2)],'#6695af')
    pg([(188,h),(192,h-2),(200,h-2),(206,h-4),(215,h-4),(220,h-5),
        (231,h-5),(234,h-8),(245,h-8),(249,h-10),(249,h+1)],'#547e9b')
    pg([(88,h),(91,h-6),(100,h-8),(107,h-8),(115,h-12),(120,h-11),
        (126,h-13),(131,h-15),(137,h-16),(142,h-15),(148,h-11),(154,h-9),
        (158,h-6),(164,h-5),(167,h-3),(175,h-2),(182,h),(185,h+1),(88,h+1)],'#8eabc3')
    pg([(90,h),(97,h-6),(106,h-7),(111,h-9),(117,h-9),(125,h-12),(132,h-12),
        (128,h-9),(133,h-9),(143,h-10),(148,h-9),(152,h-7),(156,h-6),(158,h-4),
        (166,h-3),(169,h-1),(179,h),(90,h+1)],'#789eb5')
    pg([(110,h),(118,h-3),(124,h-4),(130,h-4),(138,h-6),(142,h-7),(148,h-6),
        (152,h-5),(158,h-4),(163,h-2),(170,h-1),(170,h+1)],'#678ca4')
    d.line((124,h,164,h),fill='#b8d5d6')
    yy,xx=np.mgrid[:H,:W]
    dy=np.maximum(yy-h,0)
    # Grazing water reflects the pale horizon. Nearer facets see a deep blue
    # sky and the green body of the water. A band of silver lives near the ferry.
    coast=INK_GROUPS['Coastal water'].split()
    sea_ink=np.array([list(bytes.fromhex(c)) for c in coast],dtype=np.uint8)
    band=np.interp(dy,[0,2,5,10,19,35,52,70,110],
                         [4.9,6.1,6.8,5.85,4.6,3.50,2.75,1.9,1.2])
    drift=.33*np.sin(xx/36.+dy*.039)+.24*noise(xx/38.,dy/8.8,18)
    swell=.64*noise(xx/(25.+dy*.17)+dy*.021,dy*.246+drift,27)
    swell+=.36*noise(xx/(8.+dy*.08),dy*.61+xx*.013,41)
    water=band+(swell-.5)*(2.30+np.minimum(dy,60)*.010)
    # The pale cloud sits left of the opening. Little tilted facets borrow
    # its light in a broken strip to the port side of the departing ferry.
    reflected=np.exp(-((xx-(153.+dy*.23))/(9.+dy*.22))**2)*np.exp(-dy/60.)
    water+=reflected*.89+(noise(xx/51.,dy/10.,58)-.5)*.52
    lookup=np.clip(np.floor(water+.5).astype(int),0,7)
    pic.paste(Image.fromarray(sea_ink[lookup[h + 1:]]), (0, h + 1))
    # A wind line breaks into unequal, flat marks. Lines gather in runs and
    # are farther apart toward the foreground of the bay.
    wakes=[
        (3,148,5,7),(4,162,9,7),(5,173,3,8),(7,149,8,8),(7,160,3,7),
        (9,174,7,7),(13,142,5,7),(14,153,9,8),(14,166,2,7),
        (16,181,6,7),(18,170,4,6),(20,145,6,6),(20,156,3,7),
        (22,155,9,6),(22,167,2,7),(24,182,6,6),(26,161,7,4),(27,169,8,6),
        (30,148,5,5),(30,156,4,6),(32,187,7,5),(35,173,7,3),
        (36,182,3,5),(38,160,9,5),(39,187,9,5),(40,195,3,4),(43,169,5,2),
        (46,182,5,4),(48,174,8,4),(49,185,3,5),(51,194,7,3),
        (54,181,5,2),(56,189,10,4),(57,197,3,3),(61,172,7,3),(64,183,6,3),
        (68,194,8,2),
    ]
    for off,x,length,k in wakes:
        d.line((x,h+off,x+length-1,h+off),fill='#'+coast[k])
    # Crests occasionally turn over. One end goes silver for a pixel or two,
    # while the shaded lip ends earlier than the light above it.
    for x,off,width,tone in [(156,17,5,6),(168,29,6,4),(188,40,6,4),
                              (158,46,5,4),(179,54,7,3),(187,61,6,3)]:
        d.line((x+1,h+off+1,x+width-2,h+off+1),fill='#'+coast[max(1,tone-1)])
        d.line((x,h+off,x+width-1,h+off),fill='#'+coast[tone])
        d.point((x+width,h+off-1),fill='#'+coast[min(7,tone+1)])
    x,y=164,h+11
    # Hull, sunward cabin, one dark wheelhouse window and a broken wake.
    d.line((x+4,y+1,x+13,y+1),fill='#'+coast[8])
    d.line((x+16,y+1,x+19,y+1),fill='#'+coast[7])
    d.line((x+8,y+2,x+12,y+2),fill='#'+coast[6])
    pg([(x-7,y),(x+6,y),(x+4,y+1),(x-4,y+1)],'#547e9b')
    d.line((x-6,y-1,x+5,y-1),fill='#f5f6ee')
    d.line((x-3,y-2,x+3,y-2),fill='#e7eae5')
    d.line((x-2,y-1,x+1,y-1),fill='#6d91a6')
    d.point((x+2,y-3),fill='#a56751')
    return pic


def surface_texture(points, normals, material_ids, depth):
    """Return local brightness variation and warm plaster stains in material space."""
    world_x, world_y, world_z = points.T
    along_z = np.abs(normals[:, 0]) > np.abs(normals[:, 2])
    horizontal = np.where(along_z, world_z, world_x)
    vertical = np.where(np.abs(normals[:, 1]) > .88, world_z, world_y)
    variation = np.zeros(len(points))
    warmth = np.zeros(len(points))
    materials = [m[3] for m in M]
    simple_grain = {'metal': .031, 'cloth': .032, 'glass': .038}

    # Asphalt wear is painted in the pavement pass. Plain materials take
    # their colour directly from the light and the material swatches.
    for kind in sorted(set(materials) - {'road', 'plain'}):
        mask = np.array([name == kind for name in materials])[material_ids]
        if not mask.any():
            continue
        u, v = horizontal[mask], vertical[mask]
        x, y, z = points[mask].T
        broad = .5 - noise(u * 1.41, v * 1.48, 4)
        if kind in ('plaster', 'stone', 'wood'):
            fine = noise(u * 8.7, v * 8.3, 8)
        if kind in ('plaster', 'stone'):
            small = noise(u * 22, v * 23, 32)

        if kind == 'plaster':
            delta = .043 * broad + .012 * (fine - .5)
            above = y - np.interp(z, [0, 7, 18, 32, 47], [0, -1.51, -4.26, -8.13, -10.91])
            blot = noise(u * 2.6, v * 3.3, 88) * .54 + noise(u * .96, v * .75, 72) * .46
            chip = (blot > .70 + np.clip(above, 0, 4) * .014) & (small > .23)
            delta -= chip * .039
            warmth[mask] = chip * 5.
            streak = noise(u * 15.5, v * .67, 12)
            delta -= (streak > .78) * np.maximum(0, 1.45 - above) * .044
        elif kind == 'stone':
            delta = .065 * broad + .025 * (fine - .5) + .016 * (small - .5)
            delta -= (noise(u * 4, v * 2.85, 41) > .76) * .053
        elif kind == 'wood':
            grain = noise(u * 18, v * 1.5, 81)
            delta = .057 * broad + .051 * (grain - .5) + .028 * (fine - .5)
        elif kind == 'tile':
            across = np.where(along_z[mask], x, z)
            pan = (u / .225 + .025 * np.sin(across * 11)) % 1
            row = (across / .281) % 1
            lap = .054 * (pan > .73) - .043 * (pan < .16) - .072 * (row < .15) + .023 * (row > .90)
            delta = lap * (depth[mask] < 32) + .034 * broad
        elif kind == 'sheet':
            pan = (u / .46) % 1
            delta = .044 * (pan > .86) - .037 * (pan < .11) + .058 * broad
        elif kind == 'leaf':
            cluster = (noise(x * 10 + z * 5, y * 12 - z * 4, 51) * .67
                       + noise(x * 25 + z * 9, y * 27, 26) * .33)
            delta = (cluster > .58) * .094 - (cluster < .38) * .071 + .041 * broad
        else:
            delta = simple_grain.get(kind, 0.) * broad
        variation[mask] = delta
    return variation, warmth


def shade(zbuf,ids,sm):
    good=ids>=0; iy,ix=np.nonzero(good);di=zbuf[good]
    rays = camera_rays(ix, iy)
    P=EYE+rays*di[:,None];xx,yy,zz=P.T
    fi=ids[good]; normals=np.array([f.n for f in faces])[fi];nx,ny,nz=normals.T
    mi=np.array([f.m for f in faces])[fi];bias=np.array([f.bias for f in faces])[fi]
    ls=P@LIGHT.T;lx=ls[:,0]*LP+LO[0];ly=-ls[:,1]*LP+LO[1]
    # Compare the blocker with the actual receiving plane *at the shadow texel*.
    # This keeps grazing light on clothing and plaster clean at native resolution.
    pn=np.array([norm(np.cross(f.p[1]-f.p[0],f.p[2]-f.p[0])) for f in faces])[fi]
    sn=pn@SUN
    sn=np.where(abs(sn)>.012,sn,np.where(sn>=0,.012,-.012))
    slope_x=(pn@SR)/sn/LP
    slope_y=-(pn@SU)/sn/LP
    # A distant eave softens over the angular radius of the sun. The small
    # fixed footprint on each shadow texel keeps contact shadows compact.
    front=np.full(len(fi),1e8)
    for dx,dy in ((0,0),(-2,-2),(2,-2),(-2,2),(2,2)):
        sx=np.clip(np.floor(lx+dx).astype(int),0,SZ-1)
        sy=np.clip(np.floor(ly+dy).astype(int),0,SZ-1)
        test=sm[sy,sx]-np.clip((sx+.5-lx)*slope_x+(sy+.5-ly)*slope_y,-.60,.60)
        front=np.minimum(front,test)
    width=.61+np.clip(ls[:,2]-front,0,30)*LP*.0031
    visibility=np.zeros(len(fi))
    for dx,dy,weight in [(0,0,2),(-.81,-.23,1),(.82,.29,1),(-.28,.86,1),
                          (.32,-.82,1),(-.48,-.60,1),(.49,.61,1),(.71,-.49,1),(-.71,.48,1)]:
        sx=np.clip(np.floor(lx+width*dx).astype(int),0,SZ-1)
        sy=np.clip(np.floor(ly+width*dy).astype(int),0,SZ-1)
        plane=ls[:,2]+np.clip((sx+.5-lx)*slope_x+(sy+.5-ly)*slope_y,-.60,.60)
        visibility+=weight*(plane<=sm[sy,sx]+.012)
    visibility/=10.
    # Keep the ray-traced contour and compress fractional coverage on either
    # side of it. A small shadow has a clean edge when drawn one pixel wide.
    visibility=np.clip((visibility-.16)/.68,0.,1.)
    # Contact shadow at recesses and under objects, sampled in a short camera-space radius.
    ao=np.zeros(len(fi));den=np.zeros(len(fi))+.001
    for step,weight in [(1,1.5),(3,1.0),(7,.56),(13,.29)]:
        for dx,dy in [(step,0),(-step,0),(0,step),(0,-step),(step,step),(-step,-step)]:
            j=np.clip(ix+dx,0,W-1);i=np.clip(iy+dy,0,H-1);D=zbuf[i,j]
            delta=(D-di)[:,None]*rays+D[:,None]*((j-ix)[:,None]*RIGHT-(i-iy)[:,None]*UP)/F
            height=np.sum(delta*normals,axis=1)
            distance=np.sqrt(np.sum(delta*delta,axis=1))
            close=(ids[i,j]!=fi)&(distance<.81)&(height>.008)
            ao+=weight*close*(1-np.clip(distance/.81,0,1))*np.clip(height/(distance+.0001)*1.45,0,1)
            den+=weight
    ao/=den
    texture, warm = surface_texture(P, normals, mi, di)
    # Reflectance is resolved by material before quantization. The same
    # sunlight can make a sheet shine and leave a recessed window quite dark.
    direct=np.maximum(0.,normals@SUN)
    aperture,sea_window=open_sky(P,normals)
    amb=np.clip(.55+.19*ny+.054*nx-.035*nz+.20*aperture-.99*ao,.06,1.05)
    indirect=.437*amb
    beam=visibility*np.where(direct>.012,.19+.81*direct**.72,0.)
    leaf=np.array([m[3]=='leaf' for m in M])[mi]
    beam[leaf]=np.maximum(beam[leaf],visibility[leaf]*.18*np.maximum(0.,-(normals[leaf]@SUN)))
    restrained=np.isin(mi,[MATS[x] for x in ('plaster','lime','cream','wood','cloth','clothblue')])
    beam[restrained&(xx<0)&(di<16.)]*=.93
    K=np.clip(indirect+(1.-indirect)*beam+bias*.93+texture*.81,0.,1.)
    # Slots between the louvers stay purple-brown; the higher slat faces
    # carry a thin, warmer edge even where the gallery shades them.
    wood=np.isin(mi,[MATS[x] for x in ('wood','wood2','umber')])
    K[wood] += np.where(mi[wood]==MATS['wood2'],.022,-.009)
    # A continuous fold, gently widening away from the clothespin, and a
    # second turned-under hem. These marks follow positions on the sheet.
    cloth=mi==MATS['cloth']
    if cloth.any():
        drop=np.clip((grade(2.65)+.17+3.953-yy[cloth])/.86,0,1)
        s=(zz[cloth]-5.72-.018*drop)/1.37
        fold=(s>.68-.11*drop)&(s<.72-.035*drop)
        crease=(s>.16+.024*drop)&(s<.20+.09*drop)&(drop<.82)
        lip=(s>.80-.10*drop)&(s<.87-.085*drop)&(drop>.21)
        K[cloth]+=.045*crease-.103*fold+.041*lip
    # Lower tier of leaves groups into a single crown with a few broad sprigs
    # facing the water. Fine lobes do not have to describe every leaf.
    if leaf.any():
        mass=noise(xx[leaf]*1.55+zz[leaf]*.32,yy[leaf]*1.3+zz[leaf]*.66,94)
        K[leaf]+=(mass>.64)*.040-(mass<.40)*.037
    K=np.clip(K,0.,1.)
    oc=np.array([v[0] for v in M])[mi]
    sky=np.array([v[1] for v in M])[mi]
    sun=np.array([v[2] for v in M])[mi]
    c=oc+(sky-oc)*np.minimum(1.,K/.46)[:,None]
    c+=(sun-sky)*np.maximum(0.,(K-.46)/.54)[:,None]
    road = np.isin(mi, [MATS['asphalt'], MATS['roadpatch']])
    if road.any():
        X,Z=xx[road],zz[road]
        # Worn mineral aggregate breaks up the two large pavement values.
        # The grains sit on the slope and shorten naturally with distance.
        slab=(.57*noise(X*1.48+Z*.19,Z*1.04,85)+.24*noise(X*3.8,Z*2.45,113)
              +.19*noise(X*9.5,Z*6.4,31))
        fines=noise(X*18.4+Z*1.3,Z*11.8,49)
        low=np.clip((.43-slab)*8.,0.,1.)
        high=np.clip((slab-.59)*8.,0.,1.)
        broken=(slab>.62)&(fines>.65)
        worn=high*4.6-low*7.5+broken*2.
        # The concrete drains keep the edge darker where rain collects.
        # Only the thin rim of the channel catches reflected sky.
        right=np.interp(Z,[-12,0,7,11.9,18.8,24.9,32,44,49],
                          [2.07,2.12,2.22,2.4,3.02,3.85,3.51,3.70,3.0])
        damp=np.clip((.99-(right-X)+.22*(slab-.50))/.71,0.,1.)
        worn-=damp*(4.5+6.*(1.-beam[road]))
        fade=np.clip((24.-Z)/12.,0.,1.)
        # Asphalt has one dominant local colour in each light. Its polished
        # aggregate and binder occupy a small interval either side of that.
        light=visibility[road]*np.clip((.19+.81*direct[road]**.72)/.824,0.,1.)
        fill=np.array([80.,95.,128.])+((aperture[road]-.60)*6.-ao[road]*26.)[:,None]
        sun_road=np.array([187.,193.,189.])+((direct[road]-.71)*17.)[:,None]
        c[road]=mix(fill,sun_road,light[:,None])
        c[road]+=(worn*fade)[:,None]*[1.08,1.,.87]
        # A narrow, older trench has a slightly denser binder than the surrounding tar.
        repair=bias[road]<-.022
        c[road]-=(repair*fade)[:,None]*[8.,9.,9.]
    # The cast-iron cover has a raised lip. Only a few adjoining facets are
    # polished smooth, enough to describe the ellipse across the road grade.
    mx,mz=xx-.72,zz-5.04
    radius=np.hypot(mx,mz)
    cap=(mi==MATS['iron'])&(ny>.8)&(radius>.254)&(radius<.291)&(mx*.46+mz*.89>.135)
    c[cap]+=[13.,18.,24.]
    # Sheltered cedar under the balcony keeps its colour in reflected light.
    # The attic louvers have lost more of their red to the weather.
    attic=wood&(abs(xx+3.30)<.19)&(zz>2.65)&(zz<12.1)&(yy>grade(2.65)+4.88)
    c[attic]=c[attic]*[.89,.96,1.02]+[2.,2.,4.]
    wall= (mi==MATS['plaster']) & (abs(xx+3.3)<.16) & (zz>2.61) & (zz<12.16)
    if wall.any():
        s=zz[wall]-2.65
        height=yy[wall]-(grade(2.65)+.17)
        c[wall]+=beam[wall,None]*[9.,7.,0.]
        # Old limewash varies in a few large islands of colour. Broken
        # runnels are confined to the stucco below the upstairs sills.
        plaster=(.70*noise(s*2.12,height*2.30,7)
                 +.30*noise(s*5.3,height*4.65,10))
        under_sill=(height<2.81)&(height>2.54)&(s>1.)&(s<8.48)
        drip=under_sill & (noise(s*10.,height*.9,15)>.66)
        face_weather=(plaster>.66)*2.6-(plaster<.32)*3.8-drip*8.
        c[wall]+=face_weather[:,None]*[1.,.8,.55]
    # The sun sees the cab and part of the paving. Only the skylight is
    # intercepted by the truck, with the darkest patch at each tire.
    pave=(ny>.82)&(zz<21.)&np.isin(mi,[MATS[x] for x in
        ('asphalt','roadpatch','stone','cutstone','stone2','stripe','iron','mortar')])
    if pave.any():
        block,tread,bounce=vehicle_shelter(P[pave])
        pot=pot_shelter(P[pave])
        indirect_share=1.-.86*beam[pave]
        c[pave]-=(indirect_share*block**.9)[:,None]*[38.,44.,48.]
        c[pave]-=tread[:,None]*[13.,16.,19.]
        c[pave]+=bounce[:,None]*[11.,13.,15.]
        c[pave]-=(indirect_share*pot)[:,None]*[24.,28.,29.]
    # A short sky reflection catches the exposed rim of the uphill gutter,
    # the tiles and metal rails. Each surface still has to face the light.
    glaze=np.isin(mi,[MATS[x] for x in ('zinc','edge','slatehi','wheel')])
    sheen=np.maximum(0.,ny[glaze])*(.20+.80*visibility[glaze])*np.clip(.35+aperture[glaze],0.,1.)
    c[glaze]+=sheen[:,None]*[7.,11.,14.]
    # The lower facade sees colours from the road. Keep sheltered clay and
    # exposed foliage distinct from blue joinery at similar light levels.
    urn=np.isin(mi,[MATS['pot'],MATS['patina']])&(zz<16.)
    turn=np.clip(nx[urn]*np.where(xx[urn]<0,1.,-1.)*.52+.71*nz[urn]+.60*ny[urn],-.85,1.)
    c[urn]+=turn[:,None]*[11.,9.,5.]
    bloom=np.isin(mi,[MATS['flower'],MATS['flowerlight']])
    c[bloom]+=(ny[bloom]+.30*nx[bloom]>.52)[:,None]*[10.,4.,12.]
    if cloth.any():
        # Blue along the valley of a fold and a narrow neutral shoulder
        # give the pale fabric a distinct silhouette against the plaster.
        c[cloth]-=fold[:,None]*[11.,5.,-1.]
        c[cloth]+=crease[:,None]*[9.,7.,2.]
    fabric=np.isin(mi,[MATS['cloth'],MATS['clothblue']])
    towel=fabric&(zz>5.70)&(zz<7.15)&(xx>-2.78)&(xx<-2.53)
    if towel.any():
        width=np.clip((zz[towel]-5.738)/1.37,0.,1.)
        hem_height=np.interp(width,np.linspace(0,1,7),[.76,.79,.82,.80,.78,.75,.72])
        hem=yy[towel]-(grade(2.65)+.17+3.90-hem_height)
        stripe=((hem>.095)&(hem<.135))*.67+((hem>.165)&(hem<.187))*.41
        yarn=mix(np.array([66.,93.,126.]),np.array([114.,155.,179.]),beam[towel,None])
        c[towel]=mix(c[towel],yarn,stripe[:,None])
    # Only a few sheltered cedar ends have kept a bleached, exposed edge.
    # Their uneven runs interrupt the fine, regular cadence of the louvers.
    lip=(mi==MATS['wood2'])&(xx>-3.25)&(xx<-3.19)&(zz>7.44)&(zz<9.07)
    if lip.any():
        s=zz[lip]-7.44
        h=yy[lip]-(grade(2.65)+.17+.22)
        row=np.floor((h-.11)/.093).astype(int)
        across=(s-.07)%((1.63-.07)/3.)
        chip=((row==3)&(across>.28)&(across<.42)
              |(row==6)&(across>.06)&(across<.16)
              |(row==10)&(across>.36)&(across<.47))
        c[lip]+=chip[:,None]*[12.,10.,6.]
    facing_water=np.clip(.28+.6*ny+.33*nz,0.,1.)
    c+=(sea_window*facing_water*(1.-beam))[:,None]*[7.,12.,15.]

    # Small nicks where the slates curl under the tiled awning. Only a few
    # adjoining tiles expose fresh ceramic to the light.
    tile=(mi==MATS['slatehi'])&(abs(xx+2.34)<.16)&(zz>2.69)&(zz<11.99)
    if tile.any():
        end=np.floor((zz[tile]-2.73)/.23+.5).astype(int)
        pale=np.isin(end,[5,6,13,22,23,31]) & (yy[tile]>grade(2.65)+.17+2.23)
        c[tile]+=pale[:,None]*[11.,14.,13.]
    # Bright leaflets form little sprays on the outer, sun-facing branches.
    # In the interior the leaf masses keep their deep shared colour.
    needles=leaf&(xx>1.8)&(yy>2.0)&(zz>3.2)&(zz<15.)
    if needles.any():
        X,Y,Z=P[needles].T
        spray=(.73*noise(X*3.2+Z*.62,Y*2.7-Z*.28,57)
               +.27*noise(X*8.4-Z*.41,Y*5.+Z*.33,34))
        turn=np.maximum(0.,normals[needles]@SUN)
        tips=(spray>.61)*turn*(.26+.74*visibility[needles])
        c[needles]+=tips[:,None]*[15.,20.,5.]
    # A few periwinkle florets catch the sky; the lower petals retain violet.
    if bloom.any():
        c[bloom]+=((ny[bloom]>.25)&(nz[bloom]>.24))[:,None]*[6.,1.,12.]
    # The raised lip of the nearest drain grate sees a sliver of open sky.
    # The slots in the iron plate and the concrete beside it interrupt it.
    grate=(mi==MATS['iron'])&(ny>.90)&(xx>1.84)&(zz>3.5)&(zz<5.5)
    if grate.any():
        X,Z=xx[grate],zz[grate]
        by_curb=np.interp(Z,[0,7],[2.12,2.22])-X
        lip=(by_curb>.209)&(by_curb<.253)
        rub=((Z>3.69)&(Z<3.81))|((Z>4.57)&(Z<4.72))|((Z>5.00)&(Z<5.09))
        c[grate]+=(rub&lip)[:,None]*[12.,20.,22.]

    # Window glass catches the opposite row of houses. Test a handful of real
    # architectural volumes with reflected sightlines and keep the interiors visible.
    glazed=np.isin(mi,[MATS['glass'],MATS['glass2']])&(abs(ny)<.23)
    if np.any(glazed):
        src=P[glazed];nr=normals[glazed];look=rays[glazed]
        refl=look-2*np.sum(look*nr,axis=1)[:,None]*nr
        hit=np.zeros(len(src),bool)
        for lo,hi in [((3.25,grade(16.63),9.26),(7.74,grade(9.26)+5.44,16.63)),
                      ((3.52,grade(23.1),17.72),(8.7,grade(17.72)+3.49,23.1)),
                      ((-8.4,grade(12.10),2.65),(-3.30,grade(2.65)+5.30,12.1)),
                      ((-7.37,grade(18.67),13.65),(-1.92,grade(13.65)+4.68,18.67))]:
            inv=1./np.where(abs(refl)>.00001,refl,.00001);A=(vec(lo)-src)*inv;B=(vec(hi)-src)*inv
            st=np.min(np.maximum(A,B),axis=1);en=np.max(np.minimum(A,B),axis=1)
            hit|=(st>np.maximum(.05,en))
        gl=~hit&(refl[:,1]>-.08)
        c[glazed]+=np.where(gl[:,None],np.array([10.,18.,20.]),np.array([-3.,-3.,-1.]))
        # A pane reflecting open sky has one broad blue plane.
        inclination=np.maximum(0.,refl[:,1]/np.linalg.norm(refl,axis=1))
        reflection=gl*(.30+.70*np.clip(inclination*3.4,0.,1.))
        c[glazed]+=reflection[:,None]*[3.,10.,16.]
        # The sliding windows on the left reflect the houses across the street.
        # Intersect their actual facade planes so the reflected dado slopes
        # across several windowpanes and stops at each wooden mullion.
        lower=(src[:,0]<-2.9)&(src[:,2]<12.0)&(src[:,1]<2.)&(refl[:,0]>.08)
        for plane,z0,z1,base_y,wall_height in [
                (3.25,9.26,16.63,grade(9.26)+.47,4.99),
                (3.52,17.72,23.1,grade(17.72)+.08,2.80)]:
            t=(plane-src[:,0])/np.maximum(.05,refl[:,0])
            across=src[:,2]+t*refl[:,2]-z0
            height=src[:,1]+t*refl[:,1]-base_y
            facing=lower&(across>=0)&(across<=z1-z0)&(height>-.20)&(height<wall_height)
            if not facing.any():
                continue
            color=np.tile([93.,112.,123.],(len(src),1))
            color[height<.51]=[65.,82.,105.]
            color[(height>.43)&(height<.51)]=[121.,134.,139.]
            if z0<10.:
                openings=(((across>.84)&(across<2.46)&(height>.16)&(height<2.18))
                          |((across>3.34)&(across<4.92)&(height>.91)&(height<2.07)))
            else:
                openings=(across>1.41)&(across<3.72)&(height>.45)&(height<2.01)
            color[openings]=[42.,58.,72.]
            strength=facing*(.20+.16*(1.-np.clip(refl[:,0],0.,1.)))
            c[glazed]=mix(c[glazed],color,strength[:,None])

    c+=warm[:,None]*[.7,.1,-.35]
    value=c@np.array([.225,.68,.095])
    tone=np.interp(value,[0,27,46,65,90,115,144,174,203,229,255],
                           [6,22,36,52,78,108,144,178,213,240,252])
    dark=np.clip((112.-value)/96.,0.,1.)
    c=value[:,None]+(c-value[:,None])*1.29
    c+=((tone-value)*1.01)[:,None]+dark[:,None]*[-1.5,-.5,3.]
    air=(1.-np.exp(-np.maximum(di-12.,0.)*.0105))[:,None]
    c=mix(c,np.array([154.,188.,204.]),air)
    surface_rgb = np.rint(np.clip(c, 0., 255.)).astype(np.uint8)
    # A bright leaf deep in the lee of the next bough loses one ink of sun.
    # Use a finite separation from the blocker to leave the smaller painted
    # facets intact. Bark and open-sky reflections keep their own inks.
    visible_tree=fi>=GARDEN_FIRST
    tree_inks=GARDEN_PIGMENTS[fi[visible_tree]-GARDEN_FIRST]
    direct_x=np.clip(np.floor(lx[visible_tree]).astype(int),0,SZ-1)
    direct_y=np.clip(np.floor(ly[visible_tree]).astype(int),0,SZ-1)
    separation=ls[visible_tree,2]-sm[direct_y,direct_x]
    sheltered=(visibility[visible_tree]<.24)&(separation>.29)
    dim=np.arange(len(INKS))
    for step in range(4,9):
        dim[GREEN[step]-1]=GREEN[step-1]-1
    tree_inks=np.where(sheltered,dim[tree_inks],tree_inks)
    surface_rgb[visible_tree] = INKS[tree_inks]
    geometry_rgb = np.zeros((H, W, 3), dtype=np.uint8)
    geometry_rgb[good] = surface_rgb
    painting = backdrop()
    painting.paste(Image.fromarray(geometry_rgb), (0, 0), Image.fromarray(good))
    return painting

def ink_wires(im,d):
    r=ImageDraw.Draw(im)
    for a,b,sag,m,width in cables:
        dist=np.linalg.norm(a-b);ns=max(70,int(dist*16))
        T=np.linspace(0,1,ns);v=a[None,:]+T[:,None]*(b-a)
        v[:,1]-=4*sag*T*(1-T)
        v=v[((v-EYE)@FORWARD)>.29]
        if len(v)<2:continue
        s=cam2(v)
        for A,B in zip(s,s[1:]):
            x,y,Z=A;X,Y,D=B
            if max(x,X)<0 or min(x,X)>=W or max(y,Y)<0 or min(y,Y)>=H:continue
            # The screen line can be less than one pixel wide; keep a single, softer pixel.
            px=np.clip(int(round((x+X)/2)),0,W-1);py=np.clip(int(round((y+Y)/2)),0,H-1)
            if .5*(Z+D)>d[py,px]+.08:continue
            pt=F*width/max(Z,.2);fade=np.clip((1-pt)*.26+(Z-7)*.007,0,.47)
            c=mix(rgb('26354a'),rgb('aac6d2'),fade)
            w=max(1,min(3,round(pt)))
            r.line((round(x),round(y),round(X),round(Y)),fill=tuple(c.astype(int)),width=w)

def paint_truck(im,ids):
    """Place the last clusters on the enamel and the glass on the native grid.
    Every stroke is first positioned on its real panel, then clipped by the truck silhouette.
    """
    painted=im.copy();pen=ImageDraw.Draw(painted)
    p,_,_=vehicle_frame()
    def xy(x,y,z):
        q=cam2(p(x,y,z));return (int(round(q[0]-.5)),int(round(q[1]-.5)))
    def polygon(points,c):pen.polygon([xy(*q) for q in points],fill=c)
    def line(points,c):pen.line([xy(*q) for q in points],fill=c)
    def side(z,y,Z,Y,c,X=.726):
        polygon([(X,y,z),(X,y,Z),(X,Y,Z),(X,Y,z)],c)
    def gate(x,y,X,Y,c):
        polygon([(x,y,-1.673),(X,y,-1.673),(X,Y,-1.673),(x,Y,-1.673)],c)
    # A sun-faded side, with a single channel pressed into the steel.
    side(-1.61,.614,.36,.920,'#c6cfcb')
    side(-1.58,.638,.345,.688,'#b2bfbd')
    polygon([(.731,.778,-1.422),(.731,.780,.251),(.731,.816,.212),(.731,.818,-1.37)],'#9eafb2')
    line([(.735,.817,-1.359),(.735,.815,.202)],'#d9ddd8')
    line([(.735,.913,-1.61),(.735,.913,.38)],'#f2f2e4')
    for z in [-1.52,.228]:
        side(z,.855,z+.07,.931,'#688398',.738)
    line([(.728,.603,-1.575),(.728,.603,.32)],'#8097a0')
    # The drop gate faces uphill and holds a little sea-blue reflected light.
    gate(-.67,.607,.67,.890,'#98acb1')
    gate(-.62,.602,.61,.641,'#879ea6')
    for x,X in [(-.51,-.08),(.09,.51)]:
        line([(x,.756,-1.678),(x+.046,.727,-1.678),(X,.727,-1.678)],'#6f8797')
        line([(x+.048,.703,-1.68),(X-.016,.703,-1.68)],'#b4c3c4')
    line([(-.66,.901,-1.68),(.65,.901,-1.68)],'#cdd5d0')
    for x in [-.628,.550]:
        gate(x,.847,x+.058,.935,'#617a88')
        gate(x,.563,x+.105,.602,'#7891a0')
    # A tiny maker's badge, stop lights and a yellow plate with just enough lettering.
    line([(.27,.821,-1.68),(.48,.821,-1.68)],'#5f7f90')
    for x in [-.616,.474]:
        polygon([(x,.383,-1.68),(x+.143,.383,-1.68),(x+.143,.443,-1.68),(x,.443,-1.68)],'#b54b48')
        line([(x+.008,.445,-1.685),(x+.068,.445,-1.685)],'#db815a')
    polygon([(-.14,.340,-1.695),(.15,.340,-1.695),(.15,.463,-1.695),(-.14,.463,-1.695)],'#dcb075')
    for x in [-.08,.025,.084]:
        pen.point(xy(x,.392,-1.697),fill='#354052')
    # Rear-view glass. A broad reflection is cut by the two low head restraints.
    def gl(x,y):return (x,y,.329+(y-1.041)*.044/.589-.016)
    polygon([gl(x,y) for x,y in [(-.48,1.142),(.473,1.142),(.473,1.481),(-.48,1.481)]],'#243e59')
    polygon([gl(x,y) for x,y in [(-.47,1.327),(-.47,1.465),(.01,1.465),(.18,1.424),(-.21,1.364)]],'#44718b')
    polygon([gl(x,y) for x,y in [(.13,1.432),(.26,1.459),(.452,1.452),(.452,1.403)]],'#7797a6')
    line([gl(-.44,1.463),gl(-.09,1.463)],'#9bb6c2')
    for x,X in [(-.39,-.18),(.18,.37)]:
        polygon([gl(x,1.142),gl(x+.016,1.204),gl(X-.021,1.208),gl(X,1.142)],'#1a2d45')
    line([gl(.064,1.151),gl(.064,1.468)],'#2c4459')
    pen.point(xy(*gl(-.410,1.407)),fill='#c5c9bf')
    # Slotted, stackable harvest crate. Handle cutout and shadow under the rolled lip.
    x,z=-.59,-.34;X=x+.61;Z=z+.60;y=.643;Y=.975
    polygon([(x,y,z),(X,y,z),(X,Y,z),(x,Y,z)],'#aa6049')
    polygon([(X,y,z),(X,y,Z),(X,Y,Z),(X,Y,z)],'#c78259')
    polygon([(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],'#785752')
    line([(x,Y,Z),(X,Y,Z),(X,Y,z),(x,Y,z),(x,Y,Z)],'#e4a36b')
    line([(x+.17,Y-.085,z),(X-.15,Y-.085,z)],'#573845')
    for a in [.09,.23,.37,.51]:
        pen.point(xy(x+a,.75,z-.005),fill='#795049')
    # The second load is a folded tarpaulin with a turned-under sea-green edge.
    x,z=-.50,-.93;X=x+.50;Z=z+.45;Y=.902
    polygon([(x,Y-.15,z),(X,Y-.15,z),(X,Y,z),(x,Y,z)],'#2c5660')
    polygon([(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],'#4f8786')
    line([(x+.04,Y,z+.06),(x+.13,Y+.009,Z-.05),(x+.25,Y,Z-.01)],'#7ea597')
    line([(X-.17,Y,z+.04),(X-.04,Y,Z-.045)],'#406b73')
    # The nearby panels occlude background structures but can themselves be occluded.
    mask=(ids>=TRUCK_RANGE[0])&(ids<TRUCK_RANGE[1])
    im.paste(painted,(0,0),Image.fromarray(mask))

# The garden tree is painted at the resolution of the street. Its branches and
# foliage occupy different depths. The same painted silhouettes face the sun
# camera to cast their shadows on the ground below.
GARDEN_LEFT,GARDEN_TOP=133,-42
GARDEN_WIDTH,GARDEN_HEIGHT=222,292
_TREE_NAMES=('082c3b','0b3943','0e4849','165b4d','227655','348b59','549760','80a761','9cb66c')
_TREE_COLORS={bytes(c).hex():i+1 for i,c in enumerate(INKS)}
GREEN=[_TREE_COLORS[s] for s in _TREE_NAMES]


class Bough:
    """A small painted plane, positioned and slanted in camera space."""
    def __init__(self,anchor,depth,slope):
        self.anchor=anchor
        self.depth=depth
        self.slope=slope
        self.depth_curve=None
        self.image=Image.new('L',(GARDEN_WIDTH,GARDEN_HEIGHT))
        self.draw=ImageDraw.Draw(self.image)

    def pixel_points(self,points):
        return [(round(x)-GARDEN_LEFT,round(y)-GARDEN_TOP) for x,y in points]

    def polygon(self,points,color):
        self.draw.polygon(self.pixel_points(points),fill=int(color))

    def line(self,points,color):
        self.draw.line(self.pixel_points(points),fill=int(color),width=1)

    def distance(self,x,y):
        if self.depth_curve is not None:
            positions,inverse_depth=self.depth_curve
            return 1./np.interp(x,positions,inverse_depth)
        ax,ay=self.anchor
        sx,sy=self.slope
        return self.depth/(1.-(sx*(x-ax)+sy*(y-ay))/F)


def painted_limb(layers,coords,widths,depth,slope,warm=True):
    pts=np.asarray(coords,float)
    widths=np.asarray(widths,float)
    directions=np.diff(pts,axis=0)
    lengths=np.linalg.norm(directions,axis=1)
    d=directions/lengths[:,None]
    # Choose the visible upper face of a broken, tapered cylinder.
    n=np.stack((-d[:,1],d[:,0]),axis=1)
    if np.sum(n@np.array([.42,-.91])*lengths)<0.:
        n=-n
    perp=np.vstack((n[0],n[:-1]+n[1:],n[-1]))
    perp=perp/np.maximum(np.linalg.norm(perp,axis=1)[:,None],.15)
    layer=Bough(pts[0],depth,slope)
    lower,main,sun,glaze=('39293e','533145','90504a','ac9391') if warm else ('162543','2a3154','505576','8395a9')
    lower,main,sun,glaze=(_TREE_COLORS[v] for v in (lower,main,sun,glaze))
    w=perp*widths[:,None]*.5
    outline=list(pts+w)+list((pts-w)[::-1])
    layer.line(pts,lower)
    if max(widths)>=1.65:
        layer.polygon(outline,lower)
        edge=list(pts+w*.66)+list((pts-w*.34)[::-1])
        layer.polygon(edge,main)
    else:
        layer.line(pts,main)
    # Keep long runs of bark in one value and break the sky-facing edge
    # where the bough turns away. Fine twigs end in a single ink.
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        if widths[i]<2.8 or i%4==1:
            continue
        left=.09 if i%3==0 else .28
        right=(.67,.88,.83)[i%3]
        A=a+(b-a)*left
        B=a+(b-a)*right
        aw=w[i]*(1-left)+w[i+1]*left
        bw=w[i]*(1-right)+w[i+1]*right
        upper=sun if widths[i]>3.8 else main
        layer.polygon([A+aw*.62,B+bw*.62,B+bw*.17,A+aw*.22],upper)
        if widths[i]>5.2 and i%4==2:
            layer.line([A+aw*.66,A*.59+B*.41+(aw*.59+bw*.41)*.66],glaze)
    for a,b,w0 in zip(pts[:-1],pts[1:],widths[:-1]):
        if w0<1.6:
            layer.line([a,b],GREEN[1])
    layers.append(layer)
    return layer


def tree_scaffold(layers):
    # The unseen base stands in the raised garden behind the right wall.
    # The main crotch is visible against the distant roof.
    runs=[
    ([(285,245),(281,218),(278,189),(266,162),(254,149),(245,135),(239,120),(237,111),(240,100),(247,86),(252,65),(258,51),(264,20)],
      [15,13.5,12,10.8,9.0,7.0,6.1,5.4,4.3,3.6,3.1,2,.6],5.40,(-.21,-.09),1),
    ([(253,149),(246,138),(234,133),(224,126),(215,126),(205,131),(198,131),(190,128),(179,123)],
      [7.4,6.5,5.8,4.6,3.6,2.8,2.0,1.25,.5],5.18,(-.31,-.12),1),
    ([(228,129),(222,131),(217,139),(210,143),(205,146),(197,146),(186,147),(179,143)],
      [3.8,3.4,3.,2.5,2.2,1.7,1.,.5],5.48,(-.38,.14),0),
    ([(217,125),(212,119),(206,115),(200,115),(195,111),(182,108)],
      [3.1,2.65,2.05,1.7,1.3,.5],5.50,(-.20,-.46),1),
    ([(239,120),(236,114),(234,110),(229,105),(225,103),(221,100),(216,101),(211,99)],
      [4.8,4.1,3.5,2.6,2.1,1.55,.94,.5],5.57,(-.12,.36),0),
    ([(241,96),(236,88),(228,85),(220,79),(213,77),(207,78),(199,76),(190,73),(181,75),(177,73),(173,73)],
      [4.6,4.0,3.4,2.8,2.3,1.8,1.45,1.21,.95,.70,.40],5.09,(.39,-.25),1),
    ([(228,85),(223,88),(217,93),(212,94),(205,91),(198,90)],
      [2.55,2.12,1.6,1.25,.9,.45],5.01,(.18,.24),0),
    ([(248,85),(247,76),(239,68),(229,64),(220,63),(207,67),(196,64)],
      [3.3,2.85,2.25,1.95,1.5,.9,.55],5.04,(.19,.27),1),
    ([(252,66),(247,58),(236,54),(231,47),(228,43),(218,42),(211,43)],
      [3.3,2.7,2.3,1.8,1.4,.95,.5],4.94,(.36,.16),0),
    ([(251,75),(256,66),(261,61),(269,57),(280,58)],
      [3.2,2.8,2.2,1.1,.45],5.04,(-.33,.20),1),
    ([(248,140),(253,132),(255,120),(264,113),(275,111)],
      [4.3,3.8,3.,2.,1.],5.51,(-.30,-.24),0),
    ([(265,163),(269,151),(278,142),(298,130)],
      [5.2,3.9,2.9,.6],5.57,(.32,.1),1)]
    for pts,widths,dist,slope,hot in runs:
        pts=[wind_bend(p) for p in pts]
        painted_limb(layers,pts,widths,dist,slope,hot)


# Each row describes a leafy branchlet: its joint, its terminal bud, the
# width of the spray, the depth of its near surface and its exposure. The
# first entry fixes the small differences between leaves on that shoot.
GARDEN_SPRAYS=[
    # Upper crown under the eave.
    (1397, 265, 48, 274, 13, 14, 5.1, 2),
    (1480, 266, 39, 248, 16, 13, 4.86, 2),
    (1563, 265, 44, 294, 18, 18, 5.68, 3),
    (1646, 262, 52, 278, 29, 17, 5.42, 3),
    (1729, 254, 57, 251, 29, 13, 4.88, 2),
    (1812, 250, 52, 232, 30, 12, 5.19, 3),
    (1895, 242, 50, 221, 37, 9, 5.38, 2),
    (1978, 231, 45, 214, 40, 5, 5.43, 3),
    (2061, 244, 57, 228, 44, 12, 4.88, 2),
    (2144, 255, 65, 273, 41, 16, 5.16, 4),
    (2227, 263, 64, 294, 59, 18, 5.56, 2),
    (2310, 249, 65, 233, 53, 13, 4.69, 3),
    # The upper bough reaches into the sea breeze.
    (2393, 237, 67, 219, 53, 12, 5.11, 3),
    (2476, 230, 64, 210, 55, 11, 4.94, 3),
    (2559, 220, 65, 199, 60, 8, 5.3, 2),
    (2642, 210, 67, 191, 63, 4.8, 5.28, 3),
    (2725, 227, 75, 212, 64, 12, 4.91, 2),
    (2808, 215, 76, 196, 68, 11, 4.83, 2),
    (2891, 204, 76, 186, 69, 8, 5.14, 3),
    (2974, 194, 74, 179, 75, 5, 5.15, 3),
    (3057, 186, 74, 173, 70, 3, 5.16, 3),
    (3389, 213, 79, 194, 80, 8, 4.69, 1),
    (3472, 235, 84, 217, 79, 8, 4.75, 2),
    (3555, 218, 91, 204, 88, 4.8, 4.86, 2),
    (3638, 211, 92, 198, 94, 2.9, 5, 1),
    # Receding foliage inside the fork.
    (3721, 241, 79, 264, 68, 11, 4.64, 2),
    (3804, 259, 103, 277, 81, 14, 6.26, 3),
    (3887, 256, 94, 249, 78, 9, 5.91, 1),
    (3970, 249, 99, 260, 84, 9, 5.84, 2),
    (4053, 236, 110, 227, 98, 5.5, 5.78, 2),
    (4136, 229, 104, 216, 97, 4, 5.75, 2),
    (4219, 221, 100, 209, 101, 3.4, 5.7, 2),
    # The lower bough above the water.
    (4302, 238, 133, 224, 119, 7, 5.3, 1),
    (4385, 225, 127, 211, 111, 9, 5.17, 3),
    (4468, 215, 124, 205, 111, 7, 5.24, 3),
    (4551, 208, 118, 191, 109, 7, 5.22, 3),
    (4800, 220, 126, 211, 124, 5.4, 5, 1),
    (4883, 211, 129, 192, 121, 9, 4.95, 3),
    (4966, 199, 129, 183, 123, 7, 4.98, 2),
    (5049, 190, 127, 178, 125, 3.5, 5.12, 3),
    (5298, 230, 132, 219, 124, 6, 5.11, 1),
    (5381, 215, 140, 201, 137, 7, 5.62, 2),
    (5464, 205, 146, 190, 139, 6, 5.51, 2),
    (5547, 199, 145, 186, 142, 4.1, 5.6, 3),
    (5630, 193, 146, 181, 150, 2.7, 5.57, 2),
    (5713, 188, 144, 179, 143, 2, 5.65, 2),
    (5796, 259, 132, 272, 110, 13, 5.65, 3),
    (5879, 258, 123, 253, 103, 11, 5.42, 2),
    (5962, 256, 117, 245, 104, 8, 5.32, 2),
    (6045, 265, 136, 288, 125, 13, 5.64, 3),
    (6128, 276, 144, 296, 130, 10, 5.91, 1),
]


# Unequal openings to the high, right-hand sun. These areas carry the light
# on a few groups of blades rather than outlining every terminal twig.
GARDEN_LIGHT=[
    (218,42,18,6,-.28), (249,30,23,10,-.57), (230,54,17,8,-.30),
    (205,61,19,6,-.27), (188,70,13,4,-.10), (246,72,10,8,-.70),
    (224,80,9,4,.18), (203,89,7,3,-.35),
    (228,97,9,5,-.47), (198,110,17,5,.37), (214,114,12,6,.35),
    (190,123,15,5,.28), (175,123,7,3,-.20), (223,128,8,4,.17),
    (197,141,10,3,.30), (183,143,7,3,.06), (249,107,10,6,-.42),
    (267,109,14,8,-.70)]
def crown_light(p):
    x,y=p
    reach=0.
    for cx,cy,rx,ry,tilt in GARDEN_LIGHT:
        dx=x-cx
        q=(dx/rx)**2+((y-cy-tilt*dx)/ry)**2
        reach=max(reach,1.-q)
    return reach

def tufted_bough(layers,row,seed):
    ax,ay,tx,ty,span,depth,base_light=row
    r=random.Random(seed)
    start=np.array([ax,ay],float)
    finish=np.array([tx,ty],float)
    delta=finish-start
    axis=delta/np.linalg.norm(delta)
    up_axis=np.array([axis[1],-axis[0]])
    if up_axis[1]>0:
        up_axis=-up_axis
    span*=1.01
    layer=Bough(start,depth,(r.uniform(-.52,.51),r.uniform(-.80,.93)))
    layers.append(layer)
    ink=lambda k:GREEN[max(0,min(8,int(k)))]
    length=np.linalg.norm(delta)
    tip_bend=r.uniform(-.4,.24)*span
    def along(t):
        return start+delta*t+up_axis*tip_bend*4.*t*(1.-t)
    def branchlet(p,q,S):
        middle=p*.52+q*.48
        middle[1]+=.15*np.linalg.norm(q-p)
        layer.line([p,middle,q],S)
    # Each flared cluster grows from the end of an upturned shoot. The base
    # of the axis is left visible between shoots.
    def fan(base,heading,radius,level,bright):
        direction=heading/np.maximum(.001,np.linalg.norm(heading))
        cross=np.array([direction[1],-direction[0]])
        turn=r.uniform(-.14,.19)
        # An evergreen spray has a broad terminal leaf and lower, splayed
        # pairs. A lit upper blade is a single connected stroke.
        for j,angle in enumerate([-.98,.91,-.60,.47,-.05]):
            a=angle+turn+r.uniform(-.18,.18)
            d=direction*np.cos(a)+cross*np.sin(a)
            e=np.array([d[1],-d[0]])
            joint=base+direction*radius*(.36 if j==4 else .17 if j in (2,3) else 0)
            reach=radius*r.uniform(.68,1.21)
            w=reach*r.uniform(.27,.49)
            tip=joint+d*reach
            side1=joint+d*reach*.38+e*w*.55
            side2=joint+d*reach*.66+e*w*.42
            under=joint+d*reach*.47-e*w*.49
            top=(bright>.20 and j in (2,4)) or (j==3 and bright>.55)
            layer.polygon([joint,side1,side2,tip,under],ink(level+int(top)))
            if j==4 and reach>4 and bright>.69:
                layer.line([side2,tip],ink(min(7,level+2)))
    # Some lateral shoots extend well clear of the main crown. Older crowns
    # close up at the centre and keep the silhouettes of their younger tips.
    shoots=max(2,round(length/(7.8 if span>5 else 7.0)))
    spine=[along(t) for t in (0,.28,.53,.77,1)]
    branchlet(spine[0],spine[2],_TREE_COLORS['39293e'] if span>5 else ink(1))
    layer.line(spine[2:],ink(2))
    if span>6:
        ridge=[along(t)+up_axis*span*k for t,k in [(0,.05),(.22,.20),(.41,.38),(.48,.24),(.68,.31),(.77,.21),(.93,.12),(1,0)]]
        belly=[along(t)-up_axis*span*k for t,k in [(.88,.10),(.74,.26),(.59,.24),(.45,.41),(.31,.37),(.20,.18),(.09,.19)]]
        layer.polygon(ridge+belly,ink(max(1,base_light-1)))
    layout=[]
    for j,t in enumerate(np.linspace(.20,.83,shoots)):
        for sign in (-1.,1.):
            t2=np.clip(t+r.uniform(-.065,.075),.11,.93)
            p=along(t2)
            width=span*(.91-.51*t2+.20*np.sin(np.pi*t2))
            # The irregularity of the spacing creates gaps of several pixels
            # between some adjacent bunches.
            D=axis*r.uniform(.18,.83)+up_axis*sign*r.uniform(.79,1.06)
            q=p+D*width*r.uniform(.58,1.06)
            heading=D*.63+np.array([r.uniform(-.35,.12),-.76])
            size=(1.40+span*.25)*r.uniform(.79,1.24)
            layout.append((p,q,heading,size,sign,j))
    layout.append((along(.76),finish,axis*.77+np.array([-.18,-.67]),(1.30+span*.22)*r.uniform(.84,1.13),1.,shoots))
    # Paint the twigs first so their points of attachment disappear under
    # the terminal foliage, even when a neighbouring cluster overlaps them.
    for p,q,_,_,sign,j in layout:
        branchlet(p,q,ink(1 if sign<0 else 2))
    for p,q,heading,size,sign,j in layout:
        sunlight=crown_light(q+.63*heading)
        exposure=base_light-1+int(sign>0)+int(sunlight>.17)+int(sunlight>.57)
        exposure+=r.choice([0,0,0,0,1,-1])
        exposure=max(1,min(6,exposure))
        if span>=4.9:
            reach=q-p
            normal=np.array((heading[1],-heading[0]))
            normal=normal/max(.01,np.linalg.norm(normal))
            for off in (-1.,1.):
                middle=p+reach*r.uniform(.54,.78)
                end=middle+normal*size*r.uniform(.35,.76)*off
                layer.line((middle,end),ink(exposure-1))
                fan(end,heading*.80+normal*off*.79,size*r.uniform(.66,.99),
                    max(1,exposure-(off<0)),sunlight*.81)
        fan(q,heading,size,exposure,sunlight)



def wind_bend(point):
    # Unequal lengths give the two main arms their own curves. Past the last
    # fork the unsupported tips turn down in the breeze.
    x,y=point
    tip=float(np.clip((240-x)/57.,0,1))
    side=math.exp(-((y-69)/15.)**2)
    ledge=math.exp(-((y-124)/7.8)**2)
    low=math.exp(-((y-146)/6.)**2)
    return (x+tip*(4.2*side+2.1*ledge+5.9*low),
            y+tip*(-8.0*side+4.7*ledge+1.8*low+1.7*math.exp(-((x-173)/6.)**2)))


def finishing_twigs(layers):
    # Visible switches interrupt the solid crown. Leaf coordinates are local
    # to the stem and specify a tip, not the centre of a stamped leaf.
    # The side of a turned leaf can catch a sliver of the cooler sky.
    def twig(stem,leaves,depth,slope,shade):
        layer=Bough(stem[0],depth,slope)
        layers.append(layer)
        layer.line(stem,_TREE_COLORS['39293e'] if shade<4 else GREEN[2])
        for j,(along,dx,dy,width,tone) in enumerate(leaves):
            pos=min(len(stem)-2,int(along))
            t=along-pos
            a=np.array(stem[pos])*(1.-t)+np.array(stem[pos+1])*t
            v=np.array([dx,dy])
            tip=a+v
            n=np.array([-dy,dx])/max(1,np.linalg.norm(v))
            k=a+.41*v+n*width*.54
            g=a+.70*v+n*width*.29
            far=a+.42*v-n*width*.46
            layer.polygon([a,k,g,tip,far],GREEN[tone])
            if width>=2.4 and j%3!=2:
                if shade==2 and j%3==0:
                    mid=_TREE_COLORS['306677']
                elif shade==5 and j%3==1:
                    mid=_TREE_COLORS['47858a']
                else:
                    mid=GREEN[min(tone+1,7)]
                layer.polygon([a+v*.28,k,g,tip],mid)
    # Bent leading terminal against the pale sky. Short side shoots turn
    # independently, with a bare span before the last bud.
    twig([(200,68),(191,66),(185,65),(179,64),(174,65),(170,68),(167,68)],
         [(.50,-2,-5,2.5,3),(.76,-6,1,2.5,4),(1.1,-2,-5,2.0,4),(1.5,-4,4,2.3,3),
          (2.18,-5,-3,2.1,4),(2.64,-4,3,2.2,3),(3.32,-2,-5,1.8,4),(3.72,-4,2,1.7,3),
          (4.1,-3,-3,1.8,4),(4.47,.4,4,1.6,3),(5.45,-4,1,1.3,3)],5.00,(.24,-.43),3)
    # Two hanging twigs, separated by an opening in the fork.
    twig([(205,73),(201,74),(198,77),(196,81),(191,84),(188,84)],
         [(.29,-2,-4,2.2,3),(.74,-5,-1,2.4,3),(1.05,2,5,2.4,3),
          (1.56,-5,1,2.2,4),(2.24,2,4,2.0,3),(3.04,-5,0,2.0,3),
          (3.63,-1,4,1.6,2),(4.34,-4,1,1.5,3)],4.56,(.13,.43),2)
    twig([(224,84),(223,86),(222,90),(218,92)],
         [(.21,-4,-1,1.7,3),(.66,3,3,2.2,3),(1.10,-3,3,1.9,4),(2.10,1,4,1.6,3)],4.88,(.29,-.10),2)
    # A fine split on the front of the lower branch dips toward the sea.
    twig([(194,130),(187,129),(182,130),(178,132),(175,134),(171,136)],
         [(.22,-2,-5,2.5,3),(.56,-6,-1,2.6,3),(.89,-3,4,2.,2),(1.21,-4,-3,1.8,4),
          (1.54,-3,4,2.1,3),(2.13,-3,-4,1.6,4),(2.78,.6,4,1.5,3),(3.30,-3,-3,1.6,3),
          (4.14,1,4,1.4,2),(4.73,-4,1,1.4,3)],4.80,(-.25,.15),3)
    twig([(201,115),(198,112),(194,110),(190,108),(185,108)],
         [(.29,2,-4,2.0,4),(.56,-4,0,2.0,3),(.94,0,-4,2.0,4),(1.34,-4,1,1.8,3),
          (1.92,-1,-5,2.0,4),(2.28,-4,1,1.7,3),(2.69,1,-4,1.7,4),
          (3.21,-2,-3,1.8,4),(3.54,-4,1,1.4,3)],4.88,(.34,-.06),3)
    # Sunlit pairs on the broad planes that turn to the open sky.
    twig([(215,62),(212,59),(207,57),(203,58)],
         [(.16,4,-6,2.8,4),(.48,-2,-5,2.8,5),(.86,-5,1,2.6,4),(1.22,-1,-5,2.6,5),
          (1.64,-4,2,2.5,4),(2.13,-3,-4,2,5),(2.47,-5,0,2.3,4)],4.51,(.40,.14),5)
    twig([(244,51),(240,47),(236,45),(232,45)],
         [(.23,1,-6,2.6,4),(.55,-4,1,2.8,3),(.89,2,-5,2.7,4),(1.36,-3,-4,2.5,5),
          (1.64,-5,1,2.3,4),(2.18,-2,-4,1.9,4),(2.65,-5,-1,1.9,5)],4.46,(.31,.22),5)
    twig([(215,121),(211,117),(207,115),(202,114)],
         [(.26,3,-5,3.2,4),(.52,-5,2,2.9,3),(.98,-4,-5,2.8,4),(1.26,1,-6,2.3,5),
          (1.67,-5,2,2.6,4),(2.18,-2,-4,2.1,4),(2.57,-5,0,2.2,5)],4.70,(.16,-.17),5)
    twig([(210,126),(205,123),(202,121),(197,122)],
         [(.14,4,-3,2.5,3),(.51,0,-5,2.6,4),(1.13,-6,0,2.8,3),(1.49,1,-5,2.4,5),
          (1.91,-2,-4,2.3,5),(2.39,-5,2,2.5,4)],4.77,(.1,.08),5)
    twig([(235,56),(230,55),(227,52),(222,52)],
         [(.23,2,-5,2.7,4),(.65,-4,2,2.4,4),(1.1,-2,-4,2.7,5),
          (1.62,-4,1,2.4,4),(2.12,-1,-4,2.1,5),(2.44,-5,0,2.3,4)],4.59,(.33,-.21),5)
    twig([(242,40),(237,39),(235,36)],
         [(.20,1,-4,2.3,4),(.53,-2,-4,2.3,5),(.88,-5,0,2.6,4),
          (1.22,1,-4,2.5,5),(1.7,-4,-1,1.9,4)],4.57,(.18,.22),5)
    twig([(202,145),(199,145),(196,148),(192,151),(189,153)],
         [(.30,-4,-3,2.4,3),(.72,1,4,2.0,3),(1.31,-5,1,2.1,4),
          (1.65,1,4,2.0,3),(2.12,-4,1,1.8,3),(2.53,-1,4,1.7,2),(3.4,-4,1,1.5,2)],5.31,(.05,.33),2)


def garden_painting():
    layers=[]
    tree_scaffold(layers)
    for seed,ax,ay,tx,ty,span,depth,exposure in GARDEN_SPRAYS:
        root=wind_bend((ax,ay))
        tip=wind_bend((tx,ty))
        tufted_bough(layers,(*root,*tip,span,depth,exposure),seed)
    # A few short shoots connect the upper crown across its wide opening.
    for i,row in enumerate([(244,81,235,72,6.7,5.41,2),(239,78,231,69,6.2,5.32,2),
                            (248,83,243,93,5.7,5.56,1),(251,41,232,32,9.0,5.0,3),
                            (243,44,231,39,6.2,4.84,3),(220,57,211,49,6.2,5.18,2),
                            (200,70,192,78,4.8,5.05,2)]):
        tufted_bough(layers,row,5534+31*i)
    # The back of a mature crown is about a metre and a half behind its near
    # leaves. Parts peep between the front bunches; more of it is visible
    # to the sun, whose rays throw the lower bough's shadow into the lane.
    rear_limb=painted_limb(layers,[(277,182),(269,162),(261,151),(250,144),(240,135),(231,129),
                        (221,124),(210,120),(198,119)], [7.1,6.1,5.1,4.6,3.8,3.1,2.5,1.6,.6],
                        5.64,(-.64,-.48),False)
    # This bough first travels away from the viewer, then turns left across
    # the frame. Its fore-end and the attached branchlets share a depth.
    rear_limb.depth_curve=([198,210,221,231,240,250,261,269,277],
                          1./np.array([6.53,6.67,6.78,6.76,6.67,6.44,6.14,5.73,5.46]))
    fork=painted_limb(layers,[(243,137),(235,133),(230,128),(227,119),(217,115),(207,115)],
                        [3.6,3.0,2.35,1.7,1.2,.5],6.43,(-.28,-.36),False)
    fork.depth_curve=([207,217,227,230,235,243],1./np.array([6.64,6.76,6.85,6.78,6.65,6.56]))
    # Receding shoots, each at the depth of its place on the bough.
    rear=[
        (249, 143, 235, 129, 8.178, 6.26, 2),
        (243, 138, 229, 127, 6.225, 6.7, 1),
        (235, 132, 221, 125, 6.9, 6.46, 2),
        (227, 127, 212, 116, 9.118, 6.8, 2),
        (219, 123, 202, 116, 5.175, 6.5, 2),
        (211, 120, 195, 117, 4.982, 6.51, 2),
        (205, 119, 191, 115, 4.324, 6.52, 2),
        (230, 125, 224, 111, 6.225, 6.73, 2),
        (222, 116, 212, 110, 6.486, 6.72, 2),
        (240, 135, 241, 122, 9.494, 6.91, 2),
        (248, 144, 257, 127, 9, 6.47, 2),
        (256, 144, 268, 131, 11.28, 6.74, 2),
        (263, 164, 271, 148, 11.28, 6.31, 2),
        (274, 156, 295, 146, 13.16, 6.56, 2),
        (274, 104, 293, 81, 15.04, 5.98, 2),
        (284, 85, 305, 64, 16.92, 6.18, 2),
        (262, 62, 287, 49, 13.16, 5.78, 2),
        (272, 55, 298, 38, 15.04, 6.01, 2),
    ]
    for i,row in enumerate(rear):
        tufted_bough(layers,row,1119+53*i)
    for i,row in enumerate([(246,137,238,138,2.2,6.91,2),
                            (247,138,242,143,2.2,6.88,2),
                            (208,116,197,112,2.5,6.77,2)]):
        tufted_bough(layers,row,7294+i*93)
    finishing_twigs(layers)
    # Pieces of bark catch skylight on the two outward-facing elbows.
    bark=Bough((242,132),5.12,(.13,.26))
    bark.polygon([(249,140),(244,135),(241,133),(237,131),(234,128),(236,129),
                  (240,131),(243,132),(246,135)],_TREE_COLORS['533145'])
    bark.line([(245,135),(242,132),(240,132),(238,130)],_TREE_COLORS['90504a'])
    bark.line([(238,130),(236,129)],_TREE_COLORS['696e91'])
    bark.polygon([(239,114),(240,110),(243,106),(242,108),(241,112),(241,114)],
                 _TREE_COLORS['533145'])
    bark.line([(240,111),(242,108)],_TREE_COLORS['696e91'])
    layers.append(bark)
    return layers

def into_world(x,y,z):
    return EYE+z*((x-W*.5)*RIGHT/F+(CY-y)*UP/F+FORWARD)


def install_garden():
    """Fold each inked plane into the depth buffer and the daylight shadow map."""
    global GARDEN_FIRST,GARDEN_PIGMENTS
    GARDEN_FIRST=len(faces)
    pigments=[]
    for bough in garden_painting():
        data=np.asarray(bough.image)
        for row in np.where(np.any(data,axis=1))[0]:
            # Contiguous ink marks are coalesced horizontally. Their corners
            # lie exactly on pixel boundaries in the original composition.
            y=GARDEN_TOP+int(row)
            values=np.pad(data[row],(1,1))
            edges=np.flatnonzero(values[1:]!=values[:-1])
            for left,right in zip(edges,edges[1:]):
                color=int(data[row,left])
                if color==0:
                    continue
                x0=GARDEN_LEFT+int(left)
                x1=GARDEN_LEFT+int(right)
                corners=[(x0,y),(x1,y),(x1,y+1),(x0,y+1)]
                world=[into_world(a,b,bough.distance(a,b)) for a,b in corners]
                face(world,'green1')
                pigments.append(color-1)
    GARDEN_PIGMENTS=np.array(pigments,dtype=np.uint8)


def build():
    global TRUCK_RANGE
    faces.clear()
    cables.clear()
    rng.seed(SCENE_SEED)
    HOUSE_MASSES.clear()
    GROUND_POTS.clear()
    terrain()
    buildings()
    lived_in()
    finishing_details()
    first=len(faces)
    mini_truck()
    TRUCK_RANGE=(first,len(faces))
    flora()
    flowering_pot()
    climbing_plants()
    poles()
    install_garden()


def render(output, preview=None):
    """Draw B1 from scratch and write the native indexed PNG and optional 4× preview."""
    build()
    depth, ids = raster()
    fit_sun_map(depth, ids)
    shadow_depth, _ = raster(shadow=True)
    painting = shade(depth, ids, shadow_depth)
    paint_truck(painting, ids)
    ink_wires(painting, depth)
    art = indexed_art(painting)
    art.save(output, optimize=True)
    if preview:
        art.resize((W * 4, H * 4), Image.Resampling.NEAREST).save(preview, optimize=True)
    return art


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, default=Path('Low-Gear.png'),
                        help='destination for the native PNG')
    parser.add_argument('--preview', type=Path, help='optional 4× nearest-neighbour PNG')
    args = parser.parse_args()
    render(args.output, args.preview)


if __name__ == '__main__':
    main()

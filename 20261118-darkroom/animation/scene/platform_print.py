"""A miniature silver print of an empty railway platform, drawn in perspective."""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def platform():
    w, h = 302, 268
    rng = random.Random(7031)
    horizon, vanishing_x, focal = 118, 215, 184
    eye_height = 1.46

    def project(x, height, z):
        return vanishing_x + focal*x/z, horizon - focal*(height-eye_height)/z

    rows, cols = np.indices((h, w))
    fog = np.exp(-((cols-210)/74)**2 - ((rows-116)/57)**2)
    sky = 147 + 83*fog + 17*rows/h
    im = Image.fromarray(np.uint8(sky))
    d = ImageDraw.Draw(im)

    def area(points, value):
        d.polygon([project(*p) for p in points], fill=int(value))

    def line(points, value, width=1):
        d.line([project(*p) for p in points], fill=int(value), width=width)

    def at_x(x, low, high, near, far, value):
        area([(x,low,near),(x,high,near),(x,high,far),(x,low,far)], value)

    def plane(y, left, right, near, far, value):
        area([(left,y,near),(right,y,near),(right,y,far),(left,y,far)], value)

    # Across the tracks, the lit mist dissolves the tops of buildings.
    for x in range(0, w, 5):
        y = 95 + rng.randrange(-8, 11)
        val = 124 + round(58*math.exp(-((x-207)/61)**2)) + rng.randrange(-5, 5)
        d.rectangle((x,y,x+rng.randint(6,17),128), fill=val)
    d.line((0,99,302,112), fill=145)
    d.line((0,104,302,115), fill=157)
    background=np.asarray(im,dtype=float)
    veil=np.exp(-((cols-218)/37)**2-((rows-113)/28)**2)*.80
    im=Image.fromarray(np.uint8((1-veil)*background+veil*243));d=ImageDraw.Draw(im)
    plane(-.43,-5,12,.7,110,62)
    # Sleepers, railheads and the platform edge share the vanishing point.
    for z in np.arange(1.0,74,.59)[::-1]:
        plane(-.43,.70,3.35,z,z+.17,79 if z<12 else 107)
    for x in (1.00,2.44,4.16,5.60):
        plane(-.31,x-.037,x+.038,.68,110,202 if x<3 else 137)
        line([(x-.056,-.39,.70),(x-.056,-.39,110)],29)
    area([(.61,0,.72),(.61,0,79),(.61,-.43,79),(.61,-.43,.72)],35)
    plane(0,-4,.61,.72,89,117)
    # Wet flagstones are lighter toward the station exit. Short reflected
    # segments change width with distance and stop at the platform edge.
    floor = np.asarray(im).copy()
    for y in range(horizon+3, h):
        z = focal*eye_height/(y-horizon)
        edge = min(w, int(project(.61,0,z)[0]))
        if edge <= 0:
            continue
        x = (np.arange(edge)-vanishing_x)*z/focal
        stripe = np.exp(-((x+.55-.12*np.sin(z*.85))/(.22+.025*z))**2)
        broad = np.exp(-((x+1.55)/.65)**2)
        tint = 87+80*(1-np.exp(-.17*z))+41*stripe+32*broad+3*np.sin(z*2.2)
        tint += 31*np.exp(-((z-25)/19)**2)
        floor[y,:edge] = np.clip(tint,0,245)
    im=Image.fromarray(floor); d=ImageDraw.Draw(im)
    for i in range(490):
        z=1.55+13*rng.random()**2; x=rng.uniform(-3.1,.57)
        val=rng.choice((85,95,126,170,194,216))
        line([(x,0,z),(min(.59,x+rng.uniform(.013,.16)),0,z+.002)],val)
    for x in (-3,-2.19,-1.37,-.55,.26):
        line([(x,0,.7),(x,0,47)],96)
    for z in np.arange(1.2,42,1.28):
        line([(-3.2,0,z),(.60,0,z)],98)
    plane(.008,.45,.55,.72,90,206)
    plane(.010,.592,.61,.72,90,235)

    # Receding timber-and-glass waiting room. One broad lighted opening
    # supplies the light behind the iron bench.
    at_x(-2.72,0,2.94,1.1,81,46)
    for k in range(13,-1,-1):
        z=1.55+k*1.5
        light = max(41,min(241, round(63+171*math.exp(-((z-3.5)/2.3)**2)+46*math.exp(-((z-12)/5)**2))))
        at_x(-2.69,.80,2.52,z+.04,z+1.37,light)
        at_x(-2.684,.08,.74,z+.04,z+1.38,max(28,int(light*.48)))
        at_x(-2.68,1.83,1.87,z,z+1.40,54)
        line([(-2.67,.78,z),(-2.67,2.57,z)],33,2)
        line([(-2.66,.76,z),(-2.66,.76,z+1.48)],146,1)

    # Separate rafters and the scalloped fascia are silhouetted against sky.
    plane(3.19,-4.85,.38,.70,65,34)
    for x in (-3.0,-2.12,-1.49,-.88,-.22,.28):
        line([(x,3.17,.78),(x,3.17,65)],54,2)
    for z in np.arange(2.2,51,3.38)[::-1]:
        area([(-3.35,3.17,z),(.39,3.17,z),(.39,2.99,z),(-3.35,3.02,z)],24)
        line([(-3.30,3.03,z),(.38,2.99,z)],78,1)
        line([(-.60,3.01,z),(-.60,2.45,z)],34,max(1,int(6/z)))
        line([(-.60,2.46,z),(.28,3.13,z)],37,max(1,int(8/z)))
        for j in range(7):
            x=-2.70+j*.37
            line([(x,3.02,z),(x+.17,3.15,z),(x+.34,3.02,z)],83)
    for z in np.arange(1.1,45,.17):
        area([(.40,3.19,z),(.40,3.19,z+.17),(.40,3.06,z+.17),(.40,3.025,z+.09),(.4,3.06,z)],28)
    line([(.4,3.18,.8),(.4,3.18,65)],105,1)
    for z in (33,24,16.7,11.9,8.2,5.7):
        # Platform piers recede behind the bench, with a slender lit arris.
        line([(-.28,0,z),(-.28,3.04,z)],39,max(1,round(23/z)))
        line([(-.247,0,z),(-.247,3.04,z)],142,max(1,round(4/z)))
        line([(-.28,2.55,z),(.24,3.03,z)],55,max(1,round(9/z)))
        line([(-.28,2.61,z),(-.91,3.08,z)],51,max(1,round(9/z)))
        plane(3.00,-2.0,-1.88,z,z+1.08,207 if z<9 else 163)

    # A bench across the platform. Three splayed legs, three seat boards,
    # two back rails and curved end arms keep the little silhouette readable.
    def bench(x,y,z):
        a=math.radians(8)
        return -1.24+x*math.cos(a)-z*math.sin(a), y, 2.88+x*math.sin(a)+z*math.cos(a)
    def bl(points,t,wid):
        d.line([project(*bench(*p)) for p in points],fill=t,width=wid)
    for x in (-.82,.78):
        bl([(x,.04,-.31),(x,.42,-.21),(x,.44,.12),(x+.02,.05,.30)],24,3)
        bl([(x,.4,.13),(x,1.10,.25)],22,3)
    for j in range(3):
        z=-.22+j*.115
        area([bench(x,.45,zz) for x,zz in [(-.99,z),(.99,z),(.99,z+.087),(-.99,z+.087)]],52+j*7)
        bl([(-.99,.451,z),(.99,.451,z)],124,1)
    for y in (.73,.94):
        area([bench(x,yy,.20+(yy-.65)*.27) for x,yy in [(-.99,y),(.99,y),(.99,y+.16),(-.99,y+.16)]],28)
        bl([(-.99,y+.155,.21),(.99,y+.155,.21)],101,1)
    for x in (-.91,.91):
        bl([(x,.41,-.25),(x,.58,-.29),(x,.65,-.20),(x,.66,.15),(x,.54,.20)],28,2)

    # The face of the suspended clock sits in a plane perpendicular to the
    # tracks. Its apparent size and mounting rods come from the same camera.
    z=3.08; cx,cy=project(-1.98,2.48,z); radius=focal*.305/z
    for x in (-2.07,-1.89):
        line([(x,3.15,z),(x,2.76,z)],29,2)
    d.ellipse((cx-radius-3,cy-radius-3,cx+radius+3,cy+radius+3),fill=21)
    d.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=224,outline=102,width=1)
    for k in range(12):
        a=k*math.pi/6
        d.line([(cx+.79*radius*math.cos(a),cy+.79*radius*math.sin(a)),
                (cx+.93*radius*math.cos(a),cy+.93*radius*math.sin(a))],fill=72,width=2 if k%3==0 else 1)
    for angle,length in ((-98,.69),(165,.48)):
        a=math.radians(angle);d.line((cx,cy,cx+length*radius*math.cos(a),cy+length*radius*math.sin(a)),fill=8,width=4)
    d.ellipse((cx-2.1,cy-2.1,cx+2.1,cy+2.1),fill=23)
    # A little silver-halide flare where daylight meets the wet track.
    a=np.asarray(im,dtype=float)
    br=np.asarray(Image.fromarray(np.uint8(np.maximum(a-170,0)*2)).filter(ImageFilter.GaussianBlur(2.0)),dtype=float)
    a+=br*.075+np.random.default_rng(4048).normal(0,2.1,a.shape)
    return Image.fromarray(np.uint8(np.clip(a,0,255)))


def tests(photo):
    """Five consecutively exposed sections of one paper test strip."""
    w,h=100,310
    im=photo.convert('L').crop((66,18,143,253)).resize((w-14,h-24),Image.Resampling.LANCZOS)
    out=Image.new('L',(w,h),218)
    data=np.asarray(im,dtype=float)/255
    yy=np.indices(data.shape)[0];exposures=np.array([.46,.73,1.03,1.45,2.06])
    latent=np.exp(-exposures[np.minimum(4,5*yy//(h-24))]*(1-data)*2.18)
    out.paste(Image.fromarray(np.uint8(22+218*latent)),(7,9))
    # Pencil bracket at the selected exposure and two grease-pencil ticks.
    d=ImageDraw.Draw(out);d.line([(5,118),(2,121),(2,181),(5,184)],fill=53,width=2)
    d.line([(9,299),(12,303),(20,295)],fill=66,width=2)
    return out

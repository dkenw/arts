"""Original images used in the negatives, drying line and the projected exposure.
The spiral is a second, miniature perspective scene viewed from below."""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw
from platform_print import platform, tests
import numpy as np

rng=random.Random(432)
def film_grain(image,seed,amount=2.0):
    a=np.asarray(image,dtype=float)
    dy,dx=np.indices(a.shape)
    fall=np.maximum(0,(dx/a.shape[1]-.51)**2+(dy/a.shape[0]-.48)**2-.13)
    a+=np.random.default_rng(seed).normal(0,amount,a.shape)-23*fall
    return Image.fromarray(np.uint8(np.clip(a,0,255)))

def stair():
    w,h=240,287
    im=Image.new('L',(w,h),219)
    dr=ImageDraw.Draw(im)
    # All rails and treads follow one helix. Finite focal distance produces
    # the well of light at the top of the stair.
    o=(150,93)
    def xy(r,theta,z):
        gx=r*math.cos(theta)-.61
        gy=r*math.sin(theta)+.30
        d=1.55+z+.16*gx+.09*gy
        return (o[0]+264*(.91*gx+.29*gy)/d,
                o[1]+257*(-.29*gx+.91*gy)/d)
    dr.polygon([(0,0),(91,0),(150,92),(0,161)],fill=174)
    dr.polygon([(240,0),(174,45),(149,94),(240,74)],fill=244)
    # A glazed roof above the last turn gives the eye a scale for the helix.
    for i in (-1.25,-.40,.45,1.30):
        dr.line([xy(2.7,i,9.5),xy(2.7,math.pi-i,9.5)],fill=131,width=1)
    # Downward-facing soffit, tread edge, inner vertical fascia and ironwork.
    n=82;da=math.pi/12.0
    for i in range(n, -1,-1):
        a=i*da-.65;b=a+da;z=.099*i-.48;outer=2.68;inner=.79
        light=math.cos(a-2.2)
        near=1-i/n
        val=int(39+80*(light*.5+.5)+52*(1-near))
        dr.polygon([xy(inner,a,z),xy(outer,a,z),xy(outer,b,z),xy(inner,b,z)],fill=val)
        dr.line([xy(inner,a,z),xy(outer,a,z)],fill=max(28,val-29),width=1 if i>37 else 2)
        dr.polygon([xy(inner,a,z),xy(inner,b,z),xy(inner,b,z+.11),xy(inner,a,z+.11)],fill=int(42+48*(light*.5+.5)))
        dr.line([xy(inner,a,z+.11),xy(inner,b,z+.11)],fill=int(172+31*light),width=1 if i>40 else 2)
        if i%2==0:
            dr.line([xy(inner+.025,a,z+.13),xy(inner+.025,a,z+.74)],fill=int(46+53*(1-near)),width=1 if i>25 else 2)
        dr.line([xy(inner,a,z+.74),xy(inner,b,z+.839)],fill=int(22+49*(1-near)),width=1 if i>44 else 3)
    return film_grain(im,39,2.6)

def bridge():
    w,h=248,184
    a=np.zeros((h,w),float)
    y,x=np.indices(a.shape)
    a[:]=166+45*(1-y/h)+23*np.exp(-((x-183)/78)**2)
    im=Image.fromarray(np.uint8(a));d=ImageDraw.Draw(im)
    # Gaps between the bridge piers reveal the sawtooth roofs beyond.
    d.polygon([(0,107),(24,105),(30,97),(50,98),(60,92),(75,97),(98,96),(115,88),(132,91),(140,82),(166,89),(191,81),(220,85),(247,78),(248,184),(0,184)],fill=139)
    for j in range(25):
        x=j*12+rng.randrange(-3,4);y=106+rng.randrange(-5,4)
        d.rectangle((x,y,x+rng.randrange(5,14),127),fill=rng.randint(80,144))
    d.polygon([(0,130),(248,111),(248,184),(0,184)],fill=135)
    # Early-20th-century railway viaduct. Receding arches share a vanishing point.
    vp=(303,95)
    def pr(u,y):return (vp[0]+(-344)/(1+u*.46),vp[1]+(y-vp[1])/(1+u*.46))
    for i in range(7,-1,-1):
        a,b=i,i+1;p=[pr(a,3),pr(b,3),pr(b,172),pr(b-.11,172),pr(b-.11,113)]
        for j in range(19):
            t=j*math.pi/18
            p.append(pr(a+.5+.39*math.cos(t),113-58*math.sin(t)))
        p += [pr(a+.11,172),pr(a,172)]
        d.polygon(p,fill=42+min(60,i*9))
        edge=[pr(a+.5+.39*math.cos(j*math.pi/28),114-58*math.sin(j*math.pi/28)) for j in range(29)]
        d.line(edge,fill=107+i*6,width=2 if i<=1 else 1)
        for j in range(1,14):
            t=j*math.pi/14;d.line([pr(a+.5+.39*math.cos(t),112-58*math.sin(t)),pr(a+.5+.43*math.cos(t),112-66*math.sin(t))],fill=70+i*5,width=1)
        d.line([pr(a,10),pr(b,10)],fill=158-i*2,width=2)
        for k in range(5):
            u=a+k*.2;d.line([pr(u,4),pr(u,-6)],fill=63+i*7,width=1)
        d.line([pr(a,-6),pr(b,-6)],fill=62+i*7,width=1)
    for j in range(95):
        x=rng.randrange(w);y=rng.randrange(134,h);d.line((x,y,x+rng.randrange(1,13),y-1),fill=rng.randrange(92,169))
    return film_grain(im,40,3)
def tank():
    w,h=175,225;yy,xx=np.indices((h,w))
    a=207-35*yy/h+7*np.cos(xx/55);im=Image.fromarray(a.astype('uint8'));d=ImageDraw.Draw(im)
    d.polygon([(0,169),(28,155),(53,164),(73,156),(87,162),(114,153),(132,155),(147,144),(175,151),(175,225),(0,225)],fill=95)
    d.polygon([(0,182),(46,177),(75,184),(96,175),(133,179),(175,165),(175,225),(0,225)],fill=53)
    for x in (54,100):
        d.line([(x,101),(x-9 if x==54 else x+7,169)],fill=40,width=4)
    d.line((51,137,104,110),fill=57,width=2);d.line((52,112,104,139),fill=57,width=2)
    d.polygon([(45,55),(55,48),(76,46),(99,48),(109,53),(105,99),(100,104),(72,107),(48,101)],fill=61)
    for x in range(48,106,4):d.line((x,55,x-1,101),fill=int(60+37*(1-(x-65)**2/2000)),width=2)
    d.ellipse((44,48,109,60),fill=78);d.polygon([(42,54),(73,32),(80,30),(112,54),(89,56),(61,56)],fill=40)
    d.line((76,32,76,24),fill=36,width=2)
    for y in (63,75,88,99):d.arc((46,y-5,107,y+5),0,180,fill=40,width=2)
    for j in range(4):d.line((0,125+j*4,175,108+j*3),fill=100+j*4)
    return film_grain(im,41,2.5)
FONT={
 'A':'010101111101101','B':'110101110101110','C':'011100100100011','D':'110101101101110','E':'111100110100111','F':'111100110100100','G':'011100101101011','H':'101101111101101','I':'111010010010111','J':'001001001101010','K':'101101110101101','L':'100100100100111','M':'101111111101101','N':'101111111111101','O':'010101101101010','P':'110101110100100','Q':'010101101111011','R':'110101110101101','S':'011100010001110','T':'111010010010010','U':'101101101101111','V':'101101101101010','W':'101101111111101','X':'101101010101101','Y':'101101010010010','Z':'111001010100111','0':'111101101101111','1':'010110010010111','2':'110001010100111','3':'110001010001110','4':'101101111001001','5':'111100110001110','6':'011100110101010','7':'111001010010010','8':'010101010101010','9':'010101011001110','-':'000000111000000','/':'001001010100100','+':'000010111010000','.':'000000000000010',' ':'000000000000000'}
def typeface(draw,text,x,y,size=1,col=15,tracking=1):
    for ch in text:
        mask=FONT.get(ch,'0'*15)
        for i,v in enumerate(mask):
            if v=='1':
                xx=x+(i%3)*size;yy=y+(i//3)*size;draw.rectangle((xx,yy,xx+size-1,yy+size-1),fill=col)
        x+=3*size+tracking
def clock():
    n=216;im=Image.new('L',(n,n),25);d=ImageDraw.Draw(im);c=108
    d.ellipse((4,4,211,211),fill=46,outline=81,width=2)
    d.ellipse((11,11,205,205),fill=32)
    for j in range(60):
        a=math.radians(j*6-90);r=95;rr=81 if j%5==0 else 88
        d.line([(c+rr*math.cos(a),c+rr*math.sin(a)),(c+r*math.cos(a),c+r*math.sin(a))],fill=210 if j%5==0 else 155,width=3 if j%5==0 else 2)
    for k in (0,10,20,30,40,50):
        a=math.radians(k*6-90);s=str(k if k else 60);z=3;x=c+68*math.cos(a)-11;y=c+68*math.sin(a)-7;typeface(d,s,int(x),int(y),z,195,2)
    typeface(d,'INTERVAL',74,134,2,118,1)
    a=math.radians(-48);d.line((c-11*math.cos(a),c-11*math.sin(a),c+83*math.cos(a),c+83*math.sin(a)),fill=225,width=4)
    d.ellipse((102,102,114,114),fill=132)
    return im
def sticker(name,sub,style=0):
    im=Image.new('L',(170,80),200 if style!=1 else 53);d=ImageDraw.Draw(im)
    if style==1:
        typeface(d,name,10,16,5,220,3);d.line((9,49,157,49),fill=142,width=2);typeface(d,sub,11,56,2,173,2)
    else:
        d.rectangle((3,4,167,76),outline=104,width=2);typeface(d,name,10,12,6,35,3)
        d.line((10,48,157,48),fill=88,width=2);typeface(d,sub,12,56,2,61,2)
    return film_grain(im,22,2.0)
def proof_sheet(photos):
    im=Image.new('L',(263,202),213);d=ImageDraw.Draw(im)
    d.rectangle((6,6,256,179),fill=19)
    for row in range(4):
        for col in range(5):
            x=10+col*49;y=12+row*41;photo=photos[(col+row*2)%len(photos)]
            width,height=photo.size;cx=(.39+.16*math.sin(col*4+row))*width;cy=(.48+.12*math.cos(row*2+col))*height
            halfx=width*(.39+col%2*.08);halfy=halfx*28/43
            rect=(max(0,cx-halfx),max(0,cy-halfy),min(width,cx+halfx),min(height,cy+halfy))
            im.paste(photo.crop(rect).resize((43,28),Image.Resampling.LANCZOS),(x,y))
            typeface(d,str(1+col+row*5),x+2,y+30,1,161)
            for k in range(7):d.rectangle((x+5+k*5,y-3,x+7+k*5,y-2),fill=117)
    d.arc((104,47,154,83),-34,332,fill=226,width=2)
    typeface(d,'CONTACT    04 - 17',12,184,2,71,2)
    return film_grain(im,74,1.7)
def paper_brand():
    im=Image.new('L',(213,141),50);d=ImageDraw.Draw(im)
    d.polygon([(146,0),(185,0),(118,141),(78,141)],fill=119)
    d.polygon([(166,0),(177,0),(110,141),(99,141)],fill=178)
    typeface(d,'FIBRE',12,16,7,214,4);typeface(d,'PAPER',13,60,3,213,3)
    d.line((12,88,77,88),fill=171,width=2);typeface(d,'8 X 10',13,106,3,202,2)
    typeface(d,'02',170,103,4,222,2)
    return film_grain(im,24,1.9)
def build(folder):
    folder.mkdir(parents=True,exist_ok=True)
    images=[stair(),bridge(),tank(),clock(),sticker('FIXER','1 + 4'),sticker('DEV','PAPER  1 + 9'),sticker('STOP','BATH'),sticker('GRADE','2  /  FIBRE',1),sticker('M-67','CONDENSER',1),sticker('PAN','100 / 36',1)]
    station=platform()
    images.extend([proof_sheet([images[0],station,images[1],station,images[2]]),paper_brand(),station,tests(station)])
    for idx,img in enumerate(images):img.save(folder/f'plate{idx}.pgm')
if __name__=='__main__':build(Path(__file__).resolve().parent.parent/'work')

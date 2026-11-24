"""Draw the backlit blind and four small areas of aged concrete in metres."""

import math
from functools import lru_cache

import numpy as np

from casting_patina import SurfaceSheet, smooth
from concrete_wear import Site, pier_coordinates
from layout import BLIND_Y, blind_hem


def linen_coordinates(start, x, y, z):
    # The roller shares its material with the hanging web. Accept only the
    # 36 mesh strips of the web, at their actual piecewise-linear geometry.
    s = min(1., max(0., (y-start)/(BLIND_Y[1]-start)))
    j = min(int(36*s), 35)
    t = 36*s-j
    a, b = j/36, (j+1)/36
    hem = (1-t)*blind_hem(a)+t*blind_hem(b)
    drop = (6.28-z)/(6.28-hem)
    face_x = 10.32-drop*(.12+.045*((1-t)*math.cos(12*a)+t*math.cos(12*b)))
    if not (-.003 <= drop <= 1.004) or abs(face_x-x) > .004:
        return None
    return y-start, z-hem


def beam_face(station, x, y, z):
    return x, z-6.86-(y-station)


def soffit(station, x, y, z):
    return y-station, -3.75-x


FINISHES = (
    Site("linen", BLIND_Y[0], (10.10,4.839,5.27),(10.34,7.631,6.282),
         (-.009,2.803,-.015,1.0), (), 16531, ("linen sunshade",), linen_coordinates),
    Site("beam_plugs", -2.25, (-1.06,-2.252,6.868),(1.50,-2.233,7.49),
         (-1.07,1.51,-.01,.65), (), 51219, coordinates=beam_face),
    Site("soffit_seam", 2.37, (-4.52,.64,7.672),(-3.68,4.26,7.685),
         (-1.74,1.90,-.08,.78), (), 7772, ("sheltered soffit",), soffit),
    Site("pier_joint", -2.25, (6.105,-2.258,2.81),(6.805,-1.738,3.82),
         (-.52,.70,2.80,3.83), (), 23711, coordinates=pier_coordinates),
    Site("ring_heel", 5.05, (6.108,5.04,.151),(6.81,5.562,1.09),
         (-.52,.70,.15,1.10), (), 48523, coordinates=pier_coordinates),
)


def linen(sheet):
    u,v=sheet.u,sheet.v
    s=np.clip(u/(BLIND_Y[1]-BLIND_Y[0]),0,1)
    height=6.28-blind_hem(s, sine=np.sin)
    fall=np.clip(1-v/height,0,1)
    from_roll=np.maximum(height-v,0)
    # Sky transmits through the single layer. The doubled, turned hem and the
    # first centimetres below the roller absorb more of it.
    hem=.059+.005*np.sin(3*u)+.003*sheet.flake_grain
    doubled=(1-smooth(hem-.007,hem+.009,v))*(1-.64*smooth(2.14,2.39,u))
    edge=np.exp(-((v-hem-.007)/.010)**2)
    roll=np.exp(-from_roll/.088)
    selvedge=np.exp(-((u-.021)/.031)**2)+.6*np.exp(-((u-2.77)/.024)**2)
    # Shallow tension folds fan away from the end that has slipped off its rail.
    # Their light shoulders taper; the middle of the web retains open sky.
    shade=np.zeros((sheet.h,sheet.w),np.float32)
    for root,sweep,bend,radius,strength in (
        (.26,.28,.075,.105,12.0),(1.50,-.43,.086,.145,7.2),
        (2.67,-.58,.061,.080,17.0),(2.59,-.19,.037,.044,6.0),
    ):
        track=root+sweep*fall+bend*np.sin(np.pi*fall)
        dw=(u-track)/(radius*(.62+.72*fall))
        relief=2.8*np.exp(-((dw-1.08)/1.05)**2) - strength*np.exp(-(dw/.94)**2)
        shade+=relief*(.22+.78*np.sin(.45+1.48*fall)**2)
    thread=sheet.noise(.012,.160)
    nap=(.6*thread+.4*sheet.noise(.14,.022))*(1.05+.9*doubled)
    tone=(-5.4-9.8*roll-20.5*doubled+3.7*edge-4.7*selvedge+shade+nap+
          1.8*sheet.broad+.9*sheet.flake_grain)
    return tone,-1.05*doubled-.50*roll


def beam_plugs(sheet):
    # Two tie cones were packed flush after stripping the form. The faint
    # second repair and the irregular pores are all part of the same pour.
    u,v=sheet.u,sheet.v
    tone=np.zeros((sheet.h,sheet.w),np.float32)
    for x,y,r,contrast in ((-.52,.321,.064,1.0),(.68,.365,.048,.53)):
        rr=np.hypot((u-x)*.96,v-y)+.005*sheet.sand+.004*sheet.flake_grain
        fill=1-smooth(.79*r,1.07*r,rr)
        lip=np.exp(-((rr-.98*r)/(.009+.001*sheet.sand))**2)
        lower=np.clip((y-v)/r,-1,1)
        feather=np.exp(-(((u-x+.025)/(.17+.24*r))**2+((v-y)/.103)**2))
        rim=.37+.63*smooth(-.55,.44,.59*sheet.flake_grain+.35*sheet.sand)
        tone+=contrast*(fill*(6.8+5*sheet.flake_grain+3*sheet.sand)
                        +rim*lip*(-4-8*lower)+2.7*feather)
    strip=np.exp(-((u-.12)/.85)**4-((v-.192-.021*np.sin(5*u))/.077)**2)
    stone=.51*sheet.flake_grain+.29*sheet.sand+.20*sheet.broad
    pores=strip*smooth(.19,.57,stone)*smooth(.14,.64,sheet.fine)
    tone+=strip*(-1.8+2.7*sheet.flake_grain)-25*pores
    rubbed=sheet.islands((
      ((.01,.168),(.08,.145),(.13,.155),(.26,.142),(.36,.166),(.23,.185),(.13,.174),(.10,.188)),
      ((.40,.169),(.48,.155),(.53,.165),(.50,.180),(.45,.187)),
      ((-.82,.178),(-.75,.159),(-.65,.178),(-.70,.192),(-.78,.193)),
    ),.015)
    tone+=sheet.grain_relief(rubbed,5.0,5.0)
    return tone,.2*rubbed+.13*strip


def soffit_seam(sheet):
    # One old seep has dried against a form board, leaving an interrupted
    # scalloped margin. The centre is barely lighter than the dark soffit.
    u,v=sheet.u,sheet.v
    reach=np.exp(-((u-.80)/.85)**4)
    breadth=(.267+.11*np.exp(-((u-.62)/.49)**2)+.055*np.cos(3.3*(u-.45))
             +.032*sheet.flake_grain+.013*sheet.sand)
    front=v-breadth
    inside=(1-smooth(-.022,.035,front))*smooth(-.032,.024,v)
    threaded=.55*sheet.broad+.27*sheet.flake_grain+.18*sheet.sand
    lip=np.exp(-(front/.020)**2)*smooth(-.52,.40,threaded)
    ghost=np.exp(-((front-.050-.018*sheet.flake_grain)/.018)**2)*smooth(.0,.48,threaded)
    film=reach*inside
    friable=sheet.islands((
        ((.39,.310),(.46,.298),(.52,.320),(.53,.352),(.47,.342),(.43,.347)),
        ((.78,.385),(.82,.369),(.88,.365),(.86,.393),(.81,.404)),
        ((1.04,.289),(1.13,.273),(1.17,.278),(1.12,.296),(1.08,.301)),
    ),.011)
    tone=film*(2.5+3.2*sheet.broad+2.0*sheet.sand) + reach*(17.5*lip+5*ghost)
    tone+=sheet.grain_relief(friable,-5,7)
    stain=reach*np.exp(-((v-.044)/.043)**2)*(.5+.5*sheet.flake_grain)
    return tone-7.6*stain,.35*film+.80*reach*lip


def pier_joint(sheet):
    # Local delamination below one horizontal lift line. Some of the old
    # casting skin bridges the split and a narrow tongue turns the arris.
    u,v=sheet.u,sheet.v
    lost=sheet.islands((
        ((-.163,3.627),(-.095,3.612),(-.041,3.623),(.002,3.604),(.072,3.614),
         (.123,3.582),(.217,3.577),(.262,3.548),(.216,3.539),(.186,3.503),
         (.131,3.519),(.081,3.480),(.059,3.496),(.035,3.438),(-.003,3.433),
         (-.016,3.487),(-.050,3.481),(-.066,3.542),(-.120,3.552),(-.102,3.589),(-.163,3.583)),
        ((.287,3.598),(.367,3.585),(.389,3.563),(.335,3.568),(.321,3.544),(.290,3.555)),
        ((-.012,3.388),(.011,3.392),(.033,3.350),(.022,3.310),(-.004,3.328)),
    ),.020)
    join=np.exp(-((v-3.632-.010*sheet.flake_grain)/.023)**2)*np.exp(-((u-.08)/.32)**4)
    grit=smooth(.17,.60,.56*sheet.sand+.44*sheet.fine)
    track=np.interp(v,[2.89,3.08,3.25,3.39,3.55],[.028,-.008,.019,.002,.052])
    wash=np.exp(-((u-track)/(.033+.013*sheet.flake_grain))**2)*smooth(2.92,3.33,v)*(1-smooth(3.44,3.55,v))
    weather=sheet.grain_relief(lost,-7.6,13)-10*lost*grit
    return weather-8.0*join-6.0*wash, .61*lost+.39*wash


def ring_heel(sheet):
    u,v=sheet.u,sheet.v
    # Splashes and cleaning water collect on the lower exposed corner.
    # The line breaks across the return and dies before the far edge.
    reach=np.exp(-((u-.11)/.52)**4)
    irregular=.024*sheet.broad+.014*sheet.flake_grain+.005*sheet.sand
    level=.347+.10*np.exp(-((u-.01)/.21)**2)+.048*np.cos(6*u)+irregular
    above=v-level
    apron=(1-smooth(-.069,.105,above))*reach*smooth(.151,.181,v)
    scatter=.54*sheet.flake_grain+.26*sheet.sand+.20*sheet.broad
    dust=np.exp(-((above+.009)/.029)**2)*smooth(-.27,.48,scatter)
    remnants=np.exp(-((above-.081-.013*sheet.sand)/.022)**2)*smooth(.13,.52,scatter)
    dragged=sheet.stroke(((-.15,.331),(-.04,.341),(.05,.354),(.15,.349),(.21,.341)),.016,.42)
    rubbed=sheet.islands((
        ((-.080,.205),(-.046,.238),(-.055,.263),(-.007,.294),(.019,.277),(.062,.297),
         (.081,.269),(.141,.259),(.110,.221),(.085,.227),(.053,.189),(.002,.199),(-.022,.174)),
        ((.219,.313),(.251,.321),(.282,.312),(.301,.337),(.277,.351),(.224,.345)),
    ),.016)
    tone=apron*(-8.5+5*sheet.broad+3*sheet.flake_grain)+reach*(20*dust+6*remnants)
    tone+=sheet.grain_relief(rubbed,7.5,10)+5.0*dragged
    return tone,.85*reach*dust+.40*rubbed-.27*apron


@lru_cache(maxsize=len(FINISHES))
def material(site):
    painter={"linen":linen,"beam_plugs":beam_plugs,"soffit_seam":soffit_seam,
             "pier_joint":pier_joint,"ring_heel":ring_heel}[site.name]
    tone, colour=painter(SurfaceSheet(site))
    return np.asarray(tone,np.float32), np.asarray(colour,np.float32)

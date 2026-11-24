"""Broad areas of concrete wear in the hall. All dimensions are in metres."""

from functools import lru_cache

import numpy as np

from casting_patina import SurfaceSheet, smooth
from concrete_wear import Site, beam_coordinates
from layout import SILL_JOINT


def slab_coordinates(station, x, y, z):
    # The seam at x = 4.20 is the edge of a real strip of shuttering.
    return y-station, 4.20-x


def sill_coordinates(station, x, y, z):
    return y-station, 1.0-z


def board_coordinates(station, x, y, z):
    return y-station, x+3.74


OVERLAYS = ("clock face", "wicked moisture at the pier foot", "chalked paper boat",
            "water and mineral under the leaking sill")


SITES = (
    Site("stripped_beam", -2.25, (-3.47,-2.254,6.856),(2.40,-2.242,7.72),
         (-3.49,2.43,-.05,.94),(),7549,coordinates=beam_coordinates),
    Site("ceiling_seam", 1.65, (2.72,-1.70,7.674),(4.39,5.045,7.687),
         (-3.37,3.41,-.21,1.50),(),13559,("sheltered soffit",),slab_coordinates),
    Site("board_bed", 3.65, (-3.71,2.21,7.674),(-1.37,5.046,7.687),
         (-1.46,1.43,.015,2.39),(),49531,("sheltered soffit",),board_coordinates),
    Site("inner_beam", 5.05, (-7.63,5.043,6.87),(-3.81,5.557,7.64),
         (-7.65,-3.77,-.55,.82),(),31003,coordinates=beam_coordinates),
    Site("ring_pier", 5.05, (6.115,5.045,2.47),(6.795,5.556,5.53),
         (-.53,.70,2.45,5.55),(),19373),
    Site("landing_pier", -2.25, (6.113,-2.255,.22),(6.795,-1.745,2.65),
         (-.535,.70,.19,2.68),(),82147),
    Site("sill_face", SILL_JOINT, (10.412,.02,.02),(10.427,8.10,1.001),
         (-4.85,3.34,-.02,1.01),(),92941,
         ("old base render",),sill_coordinates),
)


def profile(u, knots):
    positions, heights = zip(*knots)
    return np.interp(u, positions, heights).astype(np.float32)


def stripped_beam(sh):
    """Broad shallow loss of the facing along the lower timber board of the near beam."""
    u, v = sh.u, sh.v
    # Map the broad contour by hand. Intact ends and a tongue of sound cement
    # separate the lifted skin from two remnants farther down the board.
    track = u + .095*sh.broad + .033*sh.flake_grain
    edge = (profile(track, ((-3.27,.065),(-3.05,.073),(-2.78,.178),(-2.51,.123),
                            (-2.18,.320),(-1.89,.285),(-1.61,.462),(-1.22,.426),
                            (-.89,.522),(-.72,.365),(-.39,.319),(-.17,.218),
                            (.13,.269),(.36,.176),(.55,.130),(.90,.115),
                            (1.18,.223),(1.42,.265),(1.66,.166),(2.16,.089)))
            + .084*sh.broad + .047*sh.flake_grain + .013*sh.sand)
    lower = (.09+.053*np.sin(3*u+.6)+.052*sh.broad+.035*sh.flake_grain
             +.085*np.exp(-((u+.19)/.39)**2))
    reach = smooth(-3.39,-2.94,track)*(1-smooth(1.64,2.20,track))
    field = np.minimum(edge-v, v-lower)
    # A sound strip cuts through the lifted edge; this keeps the long failure
    # from reading as one continuous painted line across the face.
    bridging = np.exp(-((u+1.84+.13*sh.broad)/.28)**4-((v-.24)/.18)**4)
    shape = reach*smooth(-.020,.024,field)*(1-.72*bridging)
    fibre = sh.noise(.56,.046)
    veil = .47*sh.broad+.36*fibre+.25*sh.flake_grain+.10*sh.sand
    scale = smooth(-.49,.15,veil)
    # Pockets of original dense skin remain interlocked with the more porous bed.
    exposed = shape*(.32+.68*scale)
    pores = smooth(.24,.68,.52*sh.sand+.26*sh.fine+.22*sh.flake_grain)
    rim = reach*np.exp(-((v-edge)/.025)**2)*smooth(-.42,.54,veil)
    under = reach*np.exp(-((v-edge-.032)/.043)**2)*smooth(-.33,.55,sh.flake_grain)
    halo = reach*np.exp(-((v-(edge+lower)*.5)/(.12+.50*(edge-lower).clip(0)))**2)
    # The face sits in shadow. A few pockets of old cement skin
    # catch light among the darker exposed pores.
    clock_end = 1-smooth(-2.84,-2.40,u+.040*sh.broad)
    pocket = (.62*np.exp(-((u+2.54+.07*sh.broad)/.24)**2-((v-.17)/.085)**2)
              + np.exp(-((u+1.05+.09*sh.broad)/.32)**2-((v-.31)/.13)**2)
              + .62*np.exp(-((u-1.26)/.22)**2-((v-.17)/.09)**2))
    paste = 2.6 + 4.7*pocket - 3.5*clock_end
    contour = 2.15*rim - 3.85*under
    surrounding = .40+.74*sh.broad
    tint = .16*exposed+.08*rim
    tone = (sh.grain_relief(exposed,paste,9) + 7*fibre*exposed - 12*pores*exposed
            + contour*(1-.75*bridging) + halo*surrounding)
    # Dry fibres and a darker open fault lie in the softer paste. Their ends feather away.
    for points,radius,contrast in (
        (((-2.69,.18),(-2.39,.20),(-2.16,.207),(-1.97,.186),(-1.60,.207),(-1.17,.210)),.016,-13),
        (((-1.79,.316),(-1.52,.326),(-1.37,.313),(-1.05,.327),(-.89,.318)),.010,11),
        (((-.93,.272),(-.63,.281),(-.34,.264),(-.15,.268),(.15,.249)),.019,-9.5),
        (((.94,.141),(1.15,.157),(1.41,.153),(1.60,.162)),.011,-13),
    ):
        tone += contrast*shape*sh.stroke(points,radius,.34)
    # Ease the surface relief into the intact strip of concrete just above the bevel.
    intact_edge = smooth(.022,.126,v+.019*sh.broad+.007*sh.sand)
    tone *= (.86-.18*clock_end)*intact_edge
    tint *= intact_edge
    return tone, tint


def ceiling_seam(sh):
    """A broad old damp front on just one side of the soffit joint."""
    u,v = sh.u,sh.v
    long_grain = sh.noise(.58,.16)
    along = u+.15*sh.broad+.06*sh.flake_grain
    extent = smooth(.47,.94,along)*(1-smooth(2.98,3.37,along))
    line = (profile(along, ((.64,.05),(.91,.14),(1.13,.34),(1.46,.39),(1.64,.61),
                            (1.85,.70),(2.03,.61),(2.29,.89),(2.45,.75),(2.69,.46),
                            (2.83,.26),(3.14,.13),(3.35,.04)))
            +.11*long_grain+.06*sh.flake_grain+.022*sh.sand)
    inlet = smooth(-.035,.047,v)
    distance = line-v
    field = extent*inlet*smooth(-.054,.08,distance)
    grains = .48*sh.broad+.35*sh.flake_grain+.17*sh.sand
    edge = np.exp(-(distance/(.048+.014*sh.sand))**2)
    inner = np.exp(-((distance-.18-.048*sh.broad)/.046)**2)
    lip = extent*inlet*edge*smooth(-.58,.51,grains)
    remnant = extent*inlet*inner*smooth(-.14,.61,grains)
    dark = extent*np.exp(-((v-.079)/.104)**2)*(.72+.34*sh.broad)
    tone = field*(-6.1+3.5*long_grain+2.1*sh.flake_grain)-7.2*dark + 24*lip+10*remnant
    return tone, 1.1*lip+.32*remnant-.40*field


def inner_beam(sh):
    """The patchy print of one board and several air voids in the beam behind the clock."""
    u,v=sh.u,sh.v
    along=u+.082*sh.broad+.034*sh.flake_grain
    width=profile(along,((-6.69,.028),(-6.42,.058),(-6.18,.104),(-5.88,.183),
                         (-5.56,.134),(-5.29,.237),(-5.08,.182),(-4.82,.240),
                         (-4.55,.169),(-4.34,.099),(-4.13,.081),(-3.94,.025)))
    outer=width+.046*sh.broad+.032*sh.flake_grain+.009*sh.sand
    root=.018+.032*sh.broad+.011*sh.flake_grain
    reach=smooth(-6.73,-6.27,along)*(1-smooth(-4.28,-3.94,along))
    skin=reach*smooth(-.02,.03,np.minimum(outer-v,v-root))
    splinter=sh.noise(.62,.041)
    weather=smooth(-.28,.48,.48*splinter+.38*sh.broad+.25*sh.flake_grain)
    face=skin*(.35+.65*weather)
    tone=sh.grain_relief(face,12.5,6) + (4.8*splinter+2.5*sh.sand)*face
    for x,z,ru,rv in ((-6.12,.094,.037,.013),(-5.83,.088,.025,.016),(-5.69,.125,.053,.021),
                        (-5.63,.146,.021,.010),(-5.27,.076,.034,.021),(-5.20,.089,.023,.012),
                        (-4.78,.145,.042,.012)):
        offset=u-x
        rho=np.hypot(offset/ru,(v-z-.11*offset)/rv)+.20*sh.flake_grain+.15*sh.sand
        cavity=1-smooth(.66,1.16,rho)
        rim=np.exp(-((rho-1.04)/.21)**2)*np.clip(.5-(v-z)/rv,0,1)
        tone+=skin*((-15+4*sh.sand)*cavity+7*rim)
    return tone,.43*face


def board_bed(sh):
    """A worn board impression at the clock end of the ceiling bay, mostly in shadow."""
    u,v=sh.u,sh.v
    u_warp=u+.10*sh.broad+.041*sh.flake_grain
    # Across the grain, ridges torn from two boards end at different stations.
    # The plan is broader here; perspective compresses it into the soffit.
    shoulder=profile(u_warp,((-1.37,.53),(-1.07,.73),(-.79,1.10),(-.50,1.24),
                              (-.26,1.20),(.10,1.45),(.36,1.58),(.68,1.34),
                              (.88,1.11),(1.12,1.20),(1.35,.96)))
    toe=profile(u_warp,((-1.37,.47),(-.95,.51),(-.69,.44),(-.39,.29),
                         (-.16,.33),(.06,.24),(.38,.37),(.69,.56),(1.09,.61),(1.36,.83)))
    fibre=sh.noise(.56,.053)
    grain=.40*sh.broad+.36*fibre+.24*sh.flake_grain
    upper=shoulder+.14*sh.broad+.074*sh.flake_grain+.020*sh.sand
    lower=toe+.10*sh.broad+.043*sh.flake_grain+.015*sh.sand
    reach=smooth(-1.38,-.93,u_warp)*(1-smooth(.86,1.37,u_warp))
    area=reach*smooth(-.046,.065,np.minimum(upper-v,v-lower))
    polished=area*(.52+.48*smooth(-.48,.45,grain))
    flat=area*smooth(-.10,.48,.46*sh.broad+.33*sh.flake_grain+.21*fibre)
    lip=reach*np.exp(-((v-upper)/.048)**2)*smooth(-.26,.52,grain)
    # This shutter left a darker, smoother bed. Three rough splinters stayed
    # in its edge; the brighter grains make the direction of the timber legible.
    tone=(-15*polished + flat*(5.3+6.4*fibre)
          + 13*lip + 4*area*grain)
    for path,radius,contrast in (
        (((-.95,.61),(-.74,.64),(-.45,.625),(-.31,.66),(-.07,.64),(.22,.667)),.029,16),
        (((-.66,.83),(-.41,.807),(-.18,.82),(.04,.803),(.18,.809)),.016,-14),
        (((-.27,1.07),(.02,1.055),(.33,1.073),(.58,1.046),(.76,1.061)),.021,13),
    ):
        tone+=contrast*area*sh.stroke(path,radius,.39)
    return tone,-.35*polished+.66*lip


def ring_pier(sh):
    """A damp fan starts at the upper lift joint, spreads, then divides into finer runs."""
    u,z = sh.u,sh.v
    drop=5.45-z
    top=smooth(-.063,.052,drop)
    # Gravity keeps the long runs upright. Only the width opens out as the
    # water finds the rougher pores in the front face and turns the corner.
    axis=profile(drop,((-.12,.15),(.0,.15),(.26,.18),(.52,.14),(.85,.17),
                       (1.11,.12),(1.41,.10),(1.94,.066),(2.46,.086),(3.06,.095)))
    axis=axis+.026*sh.broad+.010*sh.flake_grain
    width=profile(drop,((-.10,.31),(.13,.41),(.47,.385),(.75,.32),(.98,.38),
                        (1.32,.29),(1.68,.18),(2.09,.108),(2.44,.063),(3.03,.016)))
    margin=(u-axis)/(width+.018*sh.flake_grain)
    thread=sh.noise(.068,.401)
    end=(2.12+.36*np.cos((u-.12)*9)+.20*thread+.13*sh.broad+.03*sh.sand)
    body=top*(1-smooth(end-.28,end+.065,drop))*(1-smooth(.65,1.13,np.abs(margin)))
    density=.55+.41*smooth(-.64,.47,.53*thread+.29*sh.broad+.18*sh.flake_grain)
    front=smooth(-.16,.18,u)
    stain=body*density
    salt=top*np.exp(-((margin+.91+.09*thread)/.17)**2)*smooth(-.35,.51,.57*thread+.43*sh.flake_grain)
    salt*=1-smooth(1.35,2.24,drop)
    # A second tooth of the joint discharged later. It splits off and ends high.
    second_axis=.43-.08*smooth(.15,1.17,drop)+.026*sh.broad
    secondary=top*np.exp(-((u-second_axis)/(.045+.014*sh.flake_grain))**2)*(1-smooth(.76,1.49,drop))
    grain=sh.noise(.025,.24)
    # The irregular, blanched islands at the head of the fan are old washed paste.
    wash=sh.islands((
        ((-.15,5.42),(-.08,5.45),(.04,5.44),(.14,5.43),(.19,5.37),(.14,5.28),
         (.17,5.20),(.105,5.17),(.095,5.04),(.042,5.08),(-.004,4.94),
         (-.06,4.98),(-.04,5.14),(-.13,5.16),(-.09,5.29),(-.15,5.31)),
        ((.232,5.31),(.305,5.38),(.391,5.35),(.425,5.25),(.362,5.23),(.38,5.13),
         (.31,5.10),(.30,4.99),(.252,5.02),(.263,5.19),(.208,5.19)),
        ((-.075,4.88),(-.018,4.96),(.037,4.96),(.049,4.87),(-.006,4.78),(-.054,4.80)),
    ),.033)
    salt_skin=wash*(.40+.60*smooth(-.35,.62,.48*sh.broad+.32*sh.flake_grain+.26*sh.sand))
    tone=stain*(-13-8.5*front+6.3*thread+3.2*grain) - 11*secondary
    tone+=21*salt + sh.grain_relief(salt_skin,19,9)
    tone+=body*np.exp(-((np.abs(margin)-.74)/.37)**2)*4.5*grain
    return tone,.93*salt+.77*salt_skin-.74*stain


def landing_pier(sh):
    """A low dull scuff and a broken casting skin straddle the passenger-side corner."""
    u,z=sh.u,sh.v
    rise=z+.043*sh.broad+.018*sh.flake_grain
    wear_axis=profile(rise,((.26,-.068),(.65,-.09),(1.0,-.011),(1.27,.01),
                            (1.55,.087),(1.82,.12),(2.08,.034),(2.42,-.024),(2.57,-.024)))
    width=profile(rise,((.25,.12),(.53,.195),(.83,.22),(1.06,.29),(1.26,.24),
                        (1.48,.32),(1.77,.42),(1.94,.30),(2.14,.195),(2.40,.09),(2.58,.03)))
    lateral=(u-wear_axis+.047*sh.broad+.012*sh.sand)/width
    reach=smooth(.25,.63,rise)*(1-smooth(2.16,2.55,rise))
    halo=reach*np.exp(-np.abs(lateral)**3)
    face=smooth(-.06,.09,u)
    # Irregular ledges of loose paste change direction where they turn the arris.
    broken=sh.islands((
        ((-.34,1.75),(-.26,1.79),(-.23,1.87),(-.15,1.91),(-.18,1.99),(-.09,2.04),
         (-.03,1.99),(.03,2.08),(.14,2.06),(.13,1.99),(.24,2.01),(.31,1.96),
         (.265,1.91),(.44,1.87),(.48,1.80),(.38,1.79),(.37,1.70),(.29,1.69),
         (.20,1.62),(.16,1.64),(.14,1.52),(.07,1.56),(.032,1.48),(-.03,1.51),
         (-.062,1.61),(-.14,1.57),(-.135,1.66),(-.24,1.64),(-.26,1.72),(-.34,1.70)),
        ((-.15,1.30),(-.07,1.42),(.024,1.45),(.12,1.40),(.15,1.34),(.10,1.31),
         (.11,1.24),(.035,1.24),(.018,1.13),(-.048,1.16),(-.049,1.24),(-.13,1.22)),
        ((.245,1.62),(.32,1.68),(.43,1.65),(.46,1.60),(.377,1.59),(.31,1.51),(.25,1.54)),
        ((-.24,.81),(-.18,.87),(-.11,.85),(-.075,.90),(-.01,.86),(-.047,.79),
         (-.09,.79),(-.12,.70),(-.19,.71),(-.16,.755),(-.248,.75)),
        ((-.045,2.18),(.022,2.22),(.087,2.18),(.06,2.12),(-.021,2.115)),
    ),.044)
    mix=.49*sh.broad+.28*sh.flake_grain+.23*sh.sand
    exposed=broken*(.56+.44*smooth(-.40,.54,mix))
    pores=smooth(.17,.67,.54*sh.sand+.28*sh.flake_grain+.18*sh.fine)
    tone=halo*((15-23*face)+3.7*sh.broad+2.2*sh.sand)
    tone+=sh.grain_relief(exposed,14-27*face,12)-15*exposed*pores
    # Rubber transfer on the high spots, then the fainter return pass, both cut by rough grains.
    for path,radius,value in (
        (((-.39,.87),(-.23,.926),(-.12,.956),(.01,.962),(.145,1.018),(.28,1.022)),.038,-20),
        (((-.27,.858),(-.14,.889),(-.039,.903),(.053,.926)),.019,-15),
        (((.037,1.071),(.14,1.095),(.27,1.134),(.377,1.128)),.017,-12),
    ):
        tone+=value*sh.stroke(path,radius,.46)*(.51+.49*face)
    return tone,.51*exposed+.20*halo


def sill_face(sh):
    """A lifted skim under the window sill and older salt-washed channels below it."""
    u,down=sh.u,sh.v
    along=u+.083*sh.broad+.039*sh.flake_grain
    # One joint and one smaller pocket farther along the bay. A length of
    # unmarked concrete interrupts them where the coping still sheds rain.
    outer=profile(along,((-4.58,.05),(-4.10,.12),(-3.68,.25),(-3.37,.28),
                         (-3.16,.16),(-2.88,.12),(-2.48,.265),(-2.17,.34),
                         (-1.96,.47),(-1.67,.395),(-1.39,.24),(-1.08,.23),
                         (-.86,.34),(-.60,.48),(-.40,.56),(-.15,.47),
                         (.12,.55),(.39,.36),(.69,.23),(1.07,.20),
                         (1.41,.10),(1.77,.08),(2.15,.15),(2.37,.22),
                         (2.61,.145),(3.04,.052)))
    channels=sh.noise(.105,.31)
    rim=outer+.061*channels+.056*sh.broad+.032*sh.flake_grain+.011*sh.sand
    reach=smooth(-4.67,-4.01,along)*(1-smooth(2.57,3.08,along))
    reach*=1-.87*np.exp(-((along+2.97)/.31)**4)
    below=smooth(.012,.091,down)
    field=reach*below*(1-smooth(-.025,.054,down-rim))
    speckle=.51*sh.broad+.32*sh.flake_grain+.25*sh.sand
    lip=reach*below*np.exp(-((down-rim)/.025)**2)*smooth(-.51,.41,speckle)
    older=reach*below*np.exp(-((down-rim-.081-.03*sh.broad)/.031)**2)*smooth(.06,.55,speckle)
    powder=field*smooth(-.38,.46,.40*sh.broad+.38*channels+.24*sh.flake_grain)
    fray=powder*smooth(.12,.64,speckle)
    tone=field*(1+5.5*channels)-8.5*reach*np.exp(-((down-.087)/.072)**2)
    tone+=sh.grain_relief(fray,15,6)+11.0*powder+19*lip+8*older
    return tone,1.24*powder+.60*lip


PAINTERS = {
    "stripped_beam": stripped_beam, "ceiling_seam": ceiling_seam, "board_bed": board_bed,
    "inner_beam": inner_beam,
    "ring_pier": ring_pier, "landing_pier": landing_pier, "sill_face": sill_face,
}


@lru_cache(maxsize=len(SITES))
def material(site):
    sheet = SurfaceSheet(site)
    tone, tint = PAINTERS[site.name](sheet)
    return np.asarray(tone,np.float32), np.asarray(tint,np.float32)

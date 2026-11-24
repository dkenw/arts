"""Draw five local finishes on the ceiling, booth, boarding pier, arch and window wall in metres."""

import math
from bisect import bisect_right
import numpy as np


def booth_coordinates(centre_y, x, y, z):
    # Continue the straight lintel around the quarter-circle at the end of the booth.
    offset = x + 4.25
    if offset > 0:
        offset = 1.86 * math.atan2(offset, centre_y - y)
    return offset, z - 2.77


def ceiling_coordinates(station, x, y, z):
    return y - station, x + 1.10


def sill_coordinates(joint_y, x, y, z):
    return y - joint_y, z


# Stations on the harbour side of the cast haunch in terminal.py.
HAUNCH_X = (6.79, 7.12, 7.92, 8.72)
HAUNCH_Z = (5.64, 6.04, 6.58, 6.86)


def shoulder_coordinates(face_y, x, y, z):
    index = min(len(HAUNCH_X)-2, max(0, bisect_right(HAUNCH_X,x)-1))
    fraction = min(1,max(0,(x-HAUNCH_X[index])/(HAUNCH_X[index+1]-HAUNCH_X[index])))
    height = HAUNCH_Z[index]+fraction*(HAUNCH_Z[index+1]-HAUNCH_Z[index])
    return x-HAUNCH_X[0], z-height-(y-face_y)


def smooth(a, b, values):
    t = np.clip((values-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


class SurfaceSheet:
    """Metric drawing grid with correlated grains at the scale of sand, chips and patches."""

    def __init__(self, site):
        self.rng = np.random.default_rng(site.seed)
        self.left, self.right, self.bottom, self.top = site.sheet
        self.density = 300
        self.w = round((self.right-self.left)*self.density)+1
        self.h = round((self.top-self.bottom)*self.density)+1
        self.u = np.linspace(self.left, self.right, self.w, dtype=np.float32)[None, :]
        self.v = np.linspace(self.bottom, self.top, self.h, dtype=np.float32)[:, None]
        self.broad = self.noise(.31, .16)
        self.flake_grain = self.noise(.076, .064)
        self.sand = self.noise(.024, .019)
        self.fine = self.noise(.009, .010)

    def noise(self, du, dv):
        from PIL import Image

        size = (max(2, round((self.top-self.bottom)/dv)), max(2, round((self.right-self.left)/du)))
        cells = self.rng.uniform(-1, 1, size).astype(np.float32)
        return np.asarray(Image.fromarray(cells).resize((self.w, self.h), Image.Resampling.BICUBIC))

    def islands(self, contours, roughness):
        from PIL import Image, ImageDraw
        from scipy.ndimage import distance_transform_edt

        image = Image.new("L", (self.w, self.h))
        draw = ImageDraw.Draw(image)
        for contour in contours:
            draw.polygon([((u-self.left)*self.density, (v-self.bottom)*self.density)
                          for u,v in contour], fill=255)
        binary = np.asarray(image) > 0
        depth = (distance_transform_edt(binary) - distance_transform_edt(~binary))/self.density
        depth += roughness*(.66*self.flake_grain + .24*self.sand + .10*self.fine)
        return smooth(-.004, .005, depth).astype(np.float32)

    def stroke(self, points, radius, broken):
        """Distance to a short scratch on this surface, with an irregular, interrupted centre."""
        distance = np.full((self.h, self.w), 4.0, np.float32)
        for (u0,v0), (u1,v1) in zip(points,points[1:]):
            du,dv = u1-u0,v1-v0
            s = np.clip(((self.u-u0)*du + (self.v-v0)*dv)/(du*du+dv*dv), 0, 1)
            np.minimum(distance, np.hypot(self.u-u0-s*du,self.v-v0-s*dv), out=distance)
        width = radius*(1+.42*self.flake_grain+.24*self.sand)
        return (1-smooth(.26*width, width+.003, distance)) * np.clip(1-broken+broken*self.flake_grain*1.9,0,1)

    def grain_relief(self, loss, matrix, lip):
        from scipy.ndimage import shift

        dark_grains = smooth(.34,.91,.65*self.sand+.35*self.fine)
        light_grains = smooth(.24,.88,-.68*self.sand-.32*self.fine)
        # The shallow ledge catches light on one side of the flake.
        shifted = shift(loss, (-1.15,.85), order=1, mode="nearest", prefilter=False)
        return (loss*(matrix+4*self.broad+3*self.flake_grain+2*self.sand-18*dark_grains+14*light_grains)
                + lip*np.maximum(shifted-loss,0) - (lip+4)*np.maximum(loss-shifted,0))


def ceiling_board(sheet):
    # The torn skin follows a single plank. Long fibres parallel to its edge
    # disappear into intact cement at both ends. The underside stays dry.
    loss = sheet.islands((
        ((-1.84,.190),(-1.59,.165),(-1.54,.130),(-1.13,.124),(-.93,.084),(-.69,.108),
         (-.53,.064),(-.10,.069),(.14,.048),(.32,.081),(.74,.080),(1.01,.113),(1.58,.159),
         (1.23,.169),(1.09,.205),(.88,.199),(.68,.238),(.42,.217),(.49,.271),(.31,.298),
         (.58,.305),(.69,.330),(.35,.353),(.35,.422),(.11,.397),(-.07,.468),(-.28,.478),
         (-.23,.532),(-.54,.541),(-.68,.472),(-.93,.496),(-.85,.428),(-1.09,.404),
         (-1.39,.411),(-1.26,.331),(-1.63,.309),(-1.49,.267),(-1.74,.257)),
        ((-.49,.624),(-.46,.572),(-.21,.549),(-.07,.506),(.13,.516),(.00,.559),
         (.22,.566),(.07,.617),(-.18,.610),(-.27,.650)),
        ((.06,.421),(.25,.389),(.39,.428),(.56,.411),(.81,.443),(.94,.480),
         (.75,.494),(.63,.531),(.44,.522),(.26,.570),(.19,.554),(.01,.588),(-.10,.551)),
        ((1.20,.249),(1.40,.221),(1.70,.224),(1.55,.244),(1.31,.264)),
        ((-1.70,.096),(-1.38,.056),(-1.24,.058),(-1.48,.089)),
        ((-.99,-.076),(-.68,-.112),(-.17,-.097),(.02,-.086),(-.26,-.051),(-.69,-.060)),
    ), .043)
    u,v = sheet.u,sheet.v
    # Broader lime-grey rubbed skin around the torn boards, then sparse evidence of grain.
    backing = np.exp(-((u+.12)/1.16)**4-((v-.30)/.30)**4) * smooth(.035,.090,v)
    fibre = sheet.noise(.49,.033)
    intact = smooth(.12,.82,.48*fibre+.39*sheet.flake_grain+.13*sheet.sand)
    exposed = loss*(1-.65*intact)
    tone = sheet.grain_relief(exposed,10.0,7.0)+backing*(1.6+1.7*sheet.broad)+6*exposed*fibre
    for trail, r in (
        (((-1.36,.186),(-.86,.178),(-.38,.204),(.04,.172),(.39,.186)),.011),
        (((-.98,.318),(-.53,.306),(-.15,.322),(.09,.316)),.015),
        (((-.31,.362),(-.04,.349),(.41,.334),(.67,.343)),.009),
        (((.32,.133),(.67,.148),(1.17,.154)),.008),
    ):
        tone -= 10*exposed*sheet.stroke(trail,r,.37)
    return tone, .32*exposed


def ticket_fascia(sheet):
    # Small losses at the vulnerable lower edge of the cement skin. The longer
    # chip crosses the transition from the straight head to the rounded end.
    loss = sheet.islands((
        ((-2.38,-.018),(-2.32,.042),(-2.21,.054),(-2.15,.094),(-2.07,.080),(-2.02,.102),
         (-1.88,.094),(-1.85,.130),(-1.73,.120),(-1.63,.141),(-1.59,.095),(-1.48,.084),
         (-1.45,.043),(-1.37,.037),(-1.40,-.018)),
        ((-1.47,.143),(-1.39,.140),(-1.35,.166),(-1.33,.190),(-1.42,.175)),
        ((-.93,-.018),(-.89,.039),(-.77,.062),(-.68,.057),(-.56,.094),(-.48,.083),
         (-.44,.036),(-.34,.019),(-.32,-.018)),
        ((-.16,.052),(-.08,.043),(-.03,.081),(.07,.064),(.15,.046),(.28,.044),
         (.31,.084),(.43,.096),(.47,.133),(.58,.132),(.68,.179),(.76,.171),
         (.82,.232),(.90,.220),(.96,.252),(1.00,.231),(1.08,.234),(1.12,.178),
         (1.20,.166),(1.25,.115),(1.37,.107),(1.40,.068),(1.52,.058),(1.55,.014),
         (1.42,-.020),(.62,-.025),(.48,.037),(.40,.031),(.25,-.016),(-.17,-.015)),
        ((1.19,.223),(1.21,.205),(1.29,.195),(1.34,.211),(1.31,.243),(1.26,.250)),
        ((1.77,-.022),(1.80,.033),(1.89,.049),(1.93,.088),(2.04,.078),(2.12,.026),
         (2.22,.022),(2.18,-.018)),
    ), .027)
    u,v = sheet.u,sheet.v
    low = np.exp(-((v-.048)/.14)**2)
    pockets = .72*np.exp(-((u+1.70)/.63)**4) + np.exp(-((u-.81)/1.10)**4)
    fleck = sheet.noise(.052,.021)
    patches = loss*(.80+.20*smooth(-.65,.26,sheet.flake_grain))
    tone = sheet.grain_relief(patches,16,8) + low*pockets*(1.4+2*sheet.broad)
    from scipy.ndimage import shift
    exposed_edge = np.maximum(0,loss-shift(loss,(-3.6,1.5),order=1,prefilter=False))
    recess = sheet.islands((
        ((.68,.081),(.73,.112),(.86,.127),(.88,.142),(.96,.140),(.91,.112),
         (.84,.092),(.77,.093),(.72,.074)),
        ((-2.08,.046),(-2.02,.061),(-1.99,.081),(-1.92,.083),(-1.95,.065),(-2.01,.041)),
        ((1.16,.082),(1.20,.109),(1.29,.118),(1.25,.093),(1.19,.074)),
    ),.011)
    tone += patches*(6.3*fleck-5.3*smooth(.23,.76,sheet.broad))
    tone -= 12*exposed_edge+recess*(12+4*sheet.flake_grain)
    # The older face below the shutter is cooler; the newly exposed sand is slightly warmer.
    return tone, 1.05*patches


def boarding_pier(sheet):
    # Baggage clipped the inner corner on the way to the gangway. Two different
    # contact heights and a chipped heel keep this distinct from the nearest pillar.
    u,v = sheet.u,sheet.v
    dust = np.exp(-((u-.015)/.28)**4 - ((v-.60-.05*u)/.31)**4)
    dust *= .64+.28*sheet.broad
    flaked = sheet.islands((
        ((-.18,.235),(-.135,.261),(-.145,.314),(-.087,.366),(-.062,.399),
         (-.026,.397),(.019,.451),(.071,.440),(.083,.410),(.138,.405),(.160,.373),
         (.194,.367),(.175,.325),(.104,.331),(.062,.292),(.013,.303),(-.031,.271),
         (-.091,.275),(-.108,.239)),
        ((-.067,.509),(-.035,.546),(-.035,.578),(.018,.592),(.059,.574),
         (.076,.551),(.040,.532),(.013,.509),(-.020,.524)),
        ((.18,.643),(.204,.675),(.250,.686),(.260,.667),(.222,.648)),
    ), .016)
    face = smooth(-.055,.080,u)
    tone = dust*(8-10*face+2.5*sheet.sand)+sheet.grain_relief(flaked,7-18*face,8)
    rubs = (
        (((-.33,.459),(-.19,.500),(-.09,.535),(.012,.539),(.11,.561),(.20,.575)),.022,20),
        (((-.16,.554),(-.07,.563),(.005,.559)),.011,11),
        (((-.22,.743),(-.14,.762),(-.071,.759),(.011,.771),(.065,.782)),.016,13),
        (((.21,.746),(.264,.766),(.332,.805)),.012,11),
    )
    for path,radius,darkness in rubs:
        ink = sheet.stroke(path,radius,.28)
        tone -= darkness*ink*(.50+.50*face)
    return tone,.31*flaked


def window_base(sheet):
    # The old damp front descends on either side of the poorly drained sill joint.
    # Water has dissolved salts at the base, leaving a broken pale fringe as it dried.
    u,v = sheet.u,sheet.v
    left = smooth(-3.56,-2.64,u)
    right = 1-smooth(1.53,2.15,u)
    extent = left*right
    def bump(at,r):
        return np.exp(-((u-at)/r)**2)
    height = (.095+.32*bump(-.04,.91)+.135*bump(-1.83,.56)+.080*bump(1.17,.60)
            +.075*bump(.67,.27)+.10*bump(-.58,.30))
    waviness = sheet.noise(.29,.88)
    edge = height+.073*waviness+.035*sheet.flake_grain+.018*sheet.sand
    lower = 1-smooth(-.05,.056,v-edge)
    crust = np.exp(-((v-edge)/(.035+.015*(sheet.broad+1)))**2)
    # Broken horizontal tongues and vertical channels prevent a continuous tidemark.
    channels = sheet.noise(.073,.35)
    island = smooth(-.18,.52,.48*sheet.broad+.42*sheet.flake_grain+.27*sheet.sand)
    friable = sheet.islands((
        ((-2.29,.175),(-2.18,.230),(-2.03,.212),(-1.96,.263),(-1.81,.240),
         (-1.72,.220),(-1.69,.173),(-1.81,.152),(-1.91,.119),(-2.12,.118),(-2.19,.150)),
        ((-.98,.170),(-.83,.187),(-.81,.244),(-.68,.252),(-.63,.302),(-.48,.280),
         (-.39,.340),(-.31,.318),(-.34,.254),(-.20,.244),(-.24,.198),(-.45,.189),
         (-.53,.151),(-.74,.153),(-.82,.127)),
        ((.07,.274),(.14,.313),(.30,.326),(.36,.369),(.46,.358),(.52,.297),
         (.64,.284),(.60,.234),(.44,.217),(.27,.259),(.14,.244)),
        ((.88,.117),(.94,.154),(1.06,.146),(1.19,.188),(1.29,.154),(1.20,.124),(1.10,.114)),
    ), .042)
    moist = extent*lower*(.66+.35*sheet.broad)
    # Accumulation is heaviest just below the leaking bay. On the shoulders only
    # fragments of the old waterline survive.
    limescale = extent*crust*island*(.44+.77*bump(-.14,1.31)+.23*bump(-2.23,.44))
    softened = extent*friable*(.55+.45*island)
    tone = (-6.8*moist + 23*limescale + sheet.grain_relief(softened,13,6)
          + extent*lower*(2.7*channels+2.4*sheet.flake_grain))
    # A softly washed apron reaches higher than the crystallised lip at the seam.
    wash = extent*bump(.12,.66)*np.exp(-((v-.39)/.27)**2)*smooth(-.27,.57,channels)
    tone -= 5*wash
    salt_dust = extent*bump(-.13,1.20)*lower*island*smooth(.12,.64,sheet.sand)
    tone += 5.9*salt_dust
    # At the head of the fan a narrow run from the open joint still shows through.
    # The ragged mineral fringe follows just one side of an older, wider run.
    vein = np.interp(v,[.24,.32,.43,.52,.63,.73,.84,.95],
                     [-.06,-.028,-.077,-.052,-.056,-.023,-.014,-.010])
    width = np.interp(v,[.24,.46,.70,.95],[.21,.12,.078,.036])
    margin = (u-vein)/(width+.017*sheet.flake_grain+.008*sheet.sand)
    vertical = smooth(.26,.46,v)*(1-smooth(.84,.93,v))
    fringe = np.exp(-((margin+.85)/.46)**2)
    chalk = vertical*fringe*smooth(-.46,.56,.60*sheet.flake_grain+.27*sheet.sand+.13*sheet.broad)
    fan = vertical*np.exp(-(margin/.94)**2)
    tone += 16*chalk-4*fan
    # A shallow friable patch beside the seep has both coated grains and open pits.
    spalled = sheet.islands((
        ((-.77,.337),(-.71,.398),(-.61,.405),(-.58,.453),(-.45,.429),
         (-.40,.478),(-.31,.458),(-.35,.400),(-.42,.386),(-.49,.346),(-.62,.322)),
        ((.22,.430),(.25,.468),(.32,.481),(.34,.515),(.42,.498),
         (.41,.465),(.36,.435),(.29,.421)),
    ),.025)
    crusted = spalled*(.47+.53*island)
    tone += sheet.grain_relief(crusted,13,7)
    return tone,1.08*limescale+.57*softened+.29*salt_dust+.72*chalk+.4*crusted


def arch_repair(sheet):
    # A small area of the windowward haunch was faced with finer repair mortar.
    # Follow the rise of the timber former, feather out above it, and turn the
    # narrow lower margin onto the return. The trowel grazes are interrupted.
    u,v = sheet.u,sheet.v
    repair = sheet.islands((
        ((.06,.207),(.11,.165),(.15,.112),(.19,.110),(.24,.034),(.28,.018),
         (.32,-.016),(.40,-.014),(.43,.013),(.51,-.018),(.62,-.021),
         (.70,.010),(.82,.005),(.89,.041),(.99,.033),(1.02,.062),
         (1.14,.063),(1.19,.091),(1.32,.101),(1.37,.137),(1.50,.168),
         (1.36,.181),(1.30,.210),(1.16,.201),(1.10,.245),(1.01,.234),
         (.96,.282),(.83,.288),(.84,.347),(.73,.362),(.71,.433),(.64,.408),
         (.60,.492),(.52,.511),(.46,.555),(.37,.517),(.31,.539),(.27,.469),
         (.21,.453),(.255,.382),(.235,.352),
         (.20,.313),(.14,.320),(.11,.275),(.045,.260)),
        ((.56,.552),(.64,.524),(.69,.472),(.75,.474),(.82,.438),
         (.86,.453),(.80,.501),(.69,.536),(.66,.580)),
        ((.95,.300),(1.02,.328),(1.11,.323),(1.15,.281),(1.07,.288)),
        ((1.40,.104),(1.52,.070),(1.61,.081),(1.55,.106),(1.47,.123)),
    ), .045)
    weather = sheet.noise(.18,.10)
    mottled = smooth(-.33,.69,.52*sheet.broad+.37*sheet.flake_grain+.31*sheet.sand)
    feather = np.exp(-((u-.67)/.69)**4 - ((v-.22)/.30)**4)
    # The two mixes differ in reflectance by only a few values. The chipped
    # bottom margin carries the stronger variations.
    trowelled = repair*(.72+.28*mottled)
    # Fine mortar is paler along the lower return. A cooler, unpowdered sliver
    # in its upper face gives the repair an interior as well as a visible edge.
    fresh = 8.6-3.2*smooth(.19,.43,v)+2.5*weather
    tone = sheet.grain_relief(trowelled,fresh,8) + feather*(2.0+1.5*weather)
    face = sheet.islands((
        ((.24,.320),(.28,.361),(.36,.355),(.39,.403),(.47,.411),(.49,.447),
         (.57,.425),(.62,.387),(.71,.364),(.72,.338),(.60,.346),(.55,.321),
         (.46,.336),(.42,.313),(.32,.326)),
    ),.028)
    tone -= face*(5+4.5*mottled)
    grainy = repair*smooth(.27,.84,.54*sheet.flake_grain+.46*sheet.sand)
    opening = np.exp(-((v-.056)/.116)**2)
    tone -= grainy*(6+11*opening)
    # A few swept arcs from a steel float disappear where the mortar wore away.
    for path,radius,contrast in (
        (((.15,.218),(.30,.226),(.45,.241),(.59,.255),(.73,.250),(.82,.245)),.016,-11),
        (((.36,.297),(.51,.307),(.61,.310),(.71,.298)),.011,7),
        (((.74,.113),(.91,.126),(1.10,.139),(1.20,.130)),.009,-8),
    ):
        tone += contrast*trowelled*sheet.stroke(path,radius,.41)
    return tone, .74*trowelled+.18*feather


def draw_detail(site):
    sheets = {
        "ceiling_board": ceiling_board,
        "ticket_fascia": ticket_fascia,
        "boarding_pier": boarding_pier,
        "window_base": window_base,
        "arch_repair": arch_repair,
    }
    tone, dust = sheets[site.name](SurfaceSheet(site))
    return np.asarray(tone,np.float32), np.asarray(dust,np.float32)

"""The thinning western edge of the sheet of water beside the foreground drain, in metres."""

from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

# Only this part of the uneven slab drains back to a thin film.
BOUNDS = (.55, 3.02, -4.27, -1.58)


def ease(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def footprint(x, y):
    left, right, low, high = BOUNDS
    return (ease(left, left+.42, x)*(1-ease(right-.60, right, x)) *
            ease(low, low+.62, y)*(1-ease(high-.40, high, y)))


def thinning(x, y, wet, mid, fine):
    """An apron of damp stone crosses one slab joint and feathers into deep water."""
    reach = footprint(x, y)
    joint = np.exp(-((y+2.45)/.071)**2)
    bank = (1.52 - .29*(y+2.65) + .092*np.sin(3.1*(y+2.6)) +
            .077*np.tanh(mid) + .024*np.tanh(fine) - .14*joint)
    distance = x-bank
    graduated = ease(-.49, .66, distance)
    # The thin front breaks around high aggregate, with more depth in the joint.
    shallow = 4*graduated*(1-graduated)
    graduated = np.clip(graduated + shallow*(.040*np.tanh(fine)+.026*joint),0,1)
    return reach*(wet-graduated), reach*shallow


def record(scene, material, maps, target):
    """Measure the optical difference with two local Cycles exposures under identical light."""
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    from harbour_air import solid_surfaces

    camera = scene.camera
    width, height = scene.render.resolution_x, scene.render.resolution_y
    left, right, lo, hi = BOUNDS
    corners = [world_to_camera_view(scene, camera, Vector((x,y,0))) for x in (left,right) for y in (lo,hi)]
    x0 = max(0,int(np.floor(min(p.x for p in corners)*width))-4)
    x1 = min(width,int(np.ceil(max(p.x for p in corners)*width))+4)
    y0 = max(0,int(np.floor((1-max(p.y for p in corners))*height))-4)
    y1 = min(height,int(np.ceil((1-min(p.y for p in corners))*height))+4)
    r = scene.render
    attrs = ("filepath","use_border","use_crop_to_border","border_min_x","border_max_x","border_min_y","border_max_y")
    original_settings = {name:getattr(r,name) for name in attrs}
    samples = scene.cycles.samples
    adaptive = scene.cycles.use_adaptive_sampling
    textures = {Path(node.image.filepath).name:node for node in material.node_tree.nodes
                if node.type == "TEX_IMAGE" and node.image is not None}
    replacements = {"terrazzo.png":"floor-film-colour.png","floor-rough.png":"floor-film-rough.png",
                    "floor-relief.png":"floor-film-relief.png"}
    old_images = {name:textures[name].image for name in replacements}
    new_images = []

    def capture(path):
        r.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(str(path), check_existing=False)
        try:
            im.colorspace_settings.name = 'Non-Color'
            values = np.empty(int(im.size[0])*int(im.size[1])*4,np.float32)
            im.pixels.foreach_get(values)
            encoded = values.reshape(height,width,4)[::-1][y0:y1,x0:x1,:3]
            return np.rint(np.clip(encoded,0,1)*255).astype(np.int16)
        finally:
            bpy.data.images.remove(im)
    try:
        r.use_border, r.use_crop_to_border = True, False
        r.border_min_x, r.border_max_x = x0/width, x1/width
        r.border_min_y, r.border_max_y = 1-y1/height, 1-y0/height
        scene.cycles.samples = min(224,samples)
        scene.cycles.use_adaptive_sampling = False
        with TemporaryDirectory() as temp:
            control = capture(Path(temp)/"existing.png")
            for name, replacement in replacements.items():
                image = bpy.data.images.load(str(Path(maps)/replacement), check_existing=False)
                image.colorspace_settings.name = old_images[name].colorspace_settings.name
                new_images.append(image)
                textures[name].image = image
            revised = capture(Path(temp)/"thinner.png")
    finally:
        for name, original in old_images.items():
            textures[name].image = original
        for im in new_images:
            bpy.data.images.remove(im)
        for name,value in original_settings.items():
            setattr(r,name,value)
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = adaptive

    # The metal grate, paper and seat fastenings are held from the approved exposure.
    # Ray-test only floor samples in the region of the material change.
    solid, floor_faces = solid_surfaces(scene, {"suspended sea air","low air above the inlet"}, material.name)
    frame = camera.data.view_frame(scene=scene)
    xl,xr = min(v.x for v in frame),max(v.x for v in frame)
    yb,yt = min(v.y for v in frame),max(v.y for v in frame)
    basis = camera.matrix_world.to_3x3()
    dx=basis@Vector(((xr-xl)/width,0,0))
    dy=basis@Vector((0,(yb-yt)/height,0))
    first=basis@Vector((xl+(xr-xl)*(x0+.5)/width,yt+(yb-yt)*(y0+.5)/height,frame[0].z))
    eye = camera.location.copy()
    ys,xs=np.ogrid[:y1-y0,:x1-x0]
    def ray_axis(axis):
        return first[axis]+xs*dx[axis]+ys*dy[axis]
    depth = -eye.z/ray_axis(2)
    world_x,world_y=eye.x+depth*ray_axis(0),eye.y+depth*ray_axis(1)
    domain = footprint(world_x,world_y)
    cover = np.zeros(domain.shape,np.uint8)
    for yy,xx in zip(*np.nonzero(domain>.004)):
        direction = first + int(xx)*dx + int(yy)*dy
        _,_,face,_=solid.ray_cast(eye,direction.normalized(),camera.data.clip_end)
        if face in floor_faces:
            cover[yy,xx] = round(255*float(ease(.004,.20,domain[yy,xx])))
    dest = Path(target).with_suffix(".drawdown.npz")
    dest.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(dest,size=(width,height),origin=(x0,y0),delta=revised-control,coverage=cover)


def apply(rgb, source, *, large):
    """Develop a mix of shallow film and standing water from a matched pair of exposures."""
    from scipy.ndimage import gaussian_filter, median_filter

    from exposure_filter import luma

    with np.load(Path(source).with_suffix(".drawdown.npz")) as pass_:
        width,height=map(int,pass_["size"])
        x,y=map(int,pass_["origin"])
        coverage=pass_["coverage"].astype(np.float32)/255
        delta=pass_["delta"].astype(np.float32)
    if rgb.shape != (height,width,3):
        raise ValueError("The drain film and camera exposure must use the same grid.")
    h,w=coverage.shape
    # Suppress solitary path-tracing samples without blurring the stone or its reflection.
    lum = luma(delta)
    mid=median_filter(lum,3)
    sigma=max(.72,.0010*width)
    weight=gaussian_filter(coverage,sigma)
    value=gaussian_filter(mid*coverage,sigma)/np.maximum(weight,1e-5)
    value+=.23*np.clip(mid-value,-8,8)
    chroma=delta-lum[...,None]
    hue=gaussian_filter(chroma*coverage[...,None],(1.7*sigma,1.7*sigma,0))
    hue/=np.maximum(gaussian_filter(coverage,1.7*sigma)[...,None],1e-5)
    patch=rgb[y:y+h,x:x+w]
    # Standing water still catches the frames. Keep more of the dark silhouette
    # on the native grid, where one step in the fixed palette carries farther.
    film_fraction=.69 if large else .48
    patch+=film_fraction*coverage[...,None]*(value[...,None]+hue)
    np.clip(patch,0,255,out=patch)

"""Render a camera exposure and the geometry guides for enlarged prints."""

from pathlib import Path

from capture_passes import GUIDE_PASSES, require_passes
from output_files import staged_output


def expose(scene, target, *, large):
    import bpy

    target = Path(target).resolve().with_suffix(".png")
    suffixes = (".png", *GUIDE_PASSES) if large else (".png",)
    with staged_output(target.parent, last=target.name) as stage:
        pending = stage / target.name
        scene.render.filepath = str(pending)
        try:
            if large:
                _render_with_guides(bpy, scene, pending)
            else:
                bpy.ops.render.render(write_still=True)
            require_passes(pending, suffixes, "Blender render")
            for suffix in suffixes:
                _check_image(bpy, scene, pending.with_suffix(suffix))
        finally:
            scene.render.filepath = str(target)


def _check_image(bpy, scene, path):
    render = scene.render
    scale = render.resolution_percentage
    expected = (render.resolution_x * scale // 100, render.resolution_y * scale // 100)
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        if tuple(image.size) != expected:
            raise ValueError(f"{path.name} must use the {expected[0]} × {expected[1]} camera grid.")
    finally:
        bpy.data.images.remove(image)


def _render_with_guides(bpy, scene, target):
    view = scene.view_layers[0]
    view.use_pass_normal = True
    view.use_pass_diffuse_color = True
    tree = bpy.data.node_groups.new("Camera exposure and guides", "CompositorNodeTree")
    scene.compositing_node_group = tree
    try:
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        layers = tree.nodes.new("CompositorNodeRLayers")
        final = tree.nodes.new("NodeGroupOutput")
        tree.links.new(layers.outputs["Image"], final.inputs["Image"])

        # Map signed normal components from [-1, 1] into PNG's [0, 1] range.
        normal = tree.nodes.new("ShaderNodeVectorMath")
        normal.operation = "MULTIPLY_ADD"
        normal.inputs[1].default_value = (0.5, 0.5, 0.5)
        normal.inputs[2].default_value = (0.5, 0.5, 0.5)
        tree.links.new(layers.outputs["Normal"], normal.inputs[0])

        guides = (("normal", normal.outputs["Vector"]), ("albedo", layers.outputs["Diffuse Color"]))
        for channel, socket in guides:
            output = tree.nodes.new("CompositorNodeOutputFile")
            output.directory = str(target.parent)
            output.file_name = f"{target.stem}.{channel}"
            fmt = output.format
            fmt.media_type = "IMAGE"
            fmt.file_format = "PNG"
            fmt.color_mode = "RGB"
            fmt.color_depth = "8"
            fmt.color_management = "OVERRIDE"
            fmt.view_settings.view_transform = "Raw"
            output.file_output_items.new("RGBA", "")
            tree.links.new(socket, output.inputs[0])

        bpy.ops.render.render(write_still=True)
    finally:
        scene.compositing_node_group = None
        bpy.data.node_groups.remove(tree)
        view.use_pass_normal = False
        view.use_pass_diffuse_color = False

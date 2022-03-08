from __future__ import annotations
import gpu
from mathutils import Vector as V
from gpu.types import GPUBatch
from gpu_extras.batch import batch_for_shader
from .helpers import Rectangle, vec_divide, vec_lerp, vec_min, vec_max, vec_multiply
from bpy.types import Area, AddonPreferences
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shader_cache import ShaderCache, CacheContainer

sh_2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
sh_2d_uniform_float = sh_2d.uniform_float
sh_2d_bind = sh_2d.bind


# graciously stolen from the amazing code_editor addon
# https://github.com/K-410/blender-scripts/blob/master/2.8/code_editor.py
def draw_quads_2d(sequence, color):
    """Draw a rectangle from the given coordinates"""
    qseq, = [(x1, y1, y2, x1, y2, x2) for (x1, y1, y2, x2) in (sequence,)]
    batch = batch_for_shader(sh_2d, 'TRIS', {'pos': qseq})
    gpu.state.blend_set('ALPHA')
    sh_2d_bind()
    sh_2d_uniform_float("color", [*color])
    batch.draw(sh_2d)


def get_batch_from_quads_2d(sequence) -> GPUBatch:
    """Return the batch for a rectangle from the given coordinates"""
    qseq, = [(x1, y1, y2, x1, y2, x2) for (x1, y1, y2, x2) in (sequence,)]
    batch = batch_for_shader(sh_2d, 'TRIS', {'pos': qseq})
    return batch


def draw_quads_2d_batch(batch, color):
    """Draw a rectangle batch with the given color"""
    gpu.state.blend_set('ALPHA')
    sh_2d_bind()
    sh_2d_uniform_float("color", [*color])
    batch.draw(sh_2d)


def draw_lines_from_quad_2d(sequence, color, width=1):
    """Draw the outline of a rectangle from the given coordinates and width"""
    # top/bottom, left/right
    # drawn in pairs of 2
    qseq, = [(tl, bl, bl, br, br, tr, tr, tl) for (tl, tr, br, bl) in (sequence,)]
    batch = batch_for_shader(sh_2d, 'LINES', {'pos': qseq})
    gpu.state.line_width_set(width)
    sh_2d_bind()
    sh_2d_uniform_float("color", [*color])
    batch.draw(sh_2d)


def get_batch_lines_from_quad_2d(sequence) -> GPUBatch:
    """return the batch of the outline of a rectangle from the given coordinates"""
    # top/bottom, left/right
    # drawn in pairs of 2
    qseq, = [(tl, bl, bl, br, br, tr, tr, tl) for (tl, tr, br, bl) in (sequence,)]
    batch = batch_for_shader(sh_2d, 'LINES', {'pos': qseq})
    return batch


def draw_lines_from_quad_2d_batch(batch, color, width):
    """Draw a rectangle line batch with the given color and width"""
    gpu.state.line_width_set(width)
    sh_2d_bind()
    sh_2d_uniform_float("color", [*color])
    batch.draw(sh_2d)


def draw_line(coords, color):
    """Draw single line from given coords and color"""
    batch = batch_for_shader(sh_2d, 'LINES', {'pos': coords})
    sh_2d_bind()
    sh_2d_uniform_float("color", [*color])
    batch.draw(sh_2d)


def get_node_dims(node) -> V:
    """Returns the visual node dimensions"""
    dims = node.dimensions.copy()
    # node.width is more accurate
    dims.x = node.width
    # invert y so that bottom corner is drawn below the location rather than above
    dims.y *= -1
    # multiply by .8 to correct for node.dimensions being weird
    dims.y *= 0.8
    return dims


def get_node_loc(node) -> V:
    """Get's a nodes location taking frames into account"""
    loc = node.location.copy()
    # add the locations of all parent frames
    if node.parent:
        i = 0
        n = node
        # If you have nodes nested to more than 100 layers god help you...
        while i < 100:
            if not n.parent:
                break
            loc += n.parent.location
            n = n.parent
            i += 1

    # get the visual location of a frame based on the locations of it's child nodes
    if node.type == "FRAME":
        default = V((100000, -100000))
        frame_loc = default.copy()
        for n in node.id_data.nodes:
            if n.parent == node:
                # recursively get the visual location of all child nodes
                nloc = get_node_loc(n)
                frame_loc.x = min(frame_loc.x, nloc.x)
                frame_loc.y = max(frame_loc.y, nloc.y)
        offset = V((30, -30))
        if default == frame_loc:
            # unfortunately, there doesn't seem to be a good way to get the visual location of
            # a frame if it doesn't have any nodes in it :(
            frame_loc = loc
        else:
            frame_loc -= offset
        return frame_loc

    return loc


def get_node_color(context, node) -> list[float]:
    """There doesn't seem to be an easy way to get the header colors of nodes,
    so this is a slow and not perfect approximation"""
    theme = context.preferences.themes[0].node_editor
    ntype = node.bl_idname.lower()
    name = ""

    if any(i in ntype for i in {"math", "string", "switch", "range", "clamp"}):
        name = "converter_node"
    if node.outputs:
        outtype = node.outputs[0].type
        if outtype == "GEOMETRY":
            name = "geometry_node"
        if "VECTOR" in outtype:
            name = "vector_node"
        if outtype == "SHADER":
            name = "shader_node"
    if any(i in ntype for i in {"curve", "mesh", "instance"}):
        name = "geometry_node"
    if "tex" in ntype:
        name = "texture_node"
    if any(i in ntype for i in {"color", "rgb"}):
        name = "color_node"
    if "attribute" in ntype:
        name = "attribute_node"
    if "input" in ntype:
        name = "input_node"
    if any(i in ntype for i in {"viewer", "output"}):
        name = "output_node"
    if any(i in ntype for i in {"groupinput", "groupoutput"}):
        name = "group_socket_node"
    if node.type == "GROUP":
        name = "group_node"

    if name:
        color = getattr(theme, name)
    else:
        color = (
            0.5,
            0.5,
            0.5,
        )

    if node.use_custom_color:
        color = node.color

    color = list(color)
    if len(color) < 4:
        color.append(0.95)
    color[3] = 0.95
    return color


def pos_to_fac(coords, node_area) -> V:
    """Convert coordinates into a 2D vector representing the x and y factor in the give area"""
    coords = V(coords)
    relative = coords - node_area.min
    fac = vec_divide(relative, node_area.size)
    return fac


def get_node_area(node_tree) -> Rectangle:
    """Returns a rectangle that goes from the minimum x and y of the nodes in the tree to the maximum x and y"""
    node_area = Rectangle((10000, 10000), (-1000, -1000))
    if node_tree:
        for node in node_tree.nodes:
            dims = get_node_dims(node)
            loc = get_node_loc(node)
            node_area.min = vec_min(loc + V((0, dims.y)), node_area.min)
            node_area.max = vec_max(loc + V((dims.x, 0)), node_area.max)
    return node_area


def get_map_area(context, area, node_area) -> Rectangle:
    """Returns a rectangle representing the size, shape and position of the minimap box"""
    region = area.regions[0]
    region_width = region.width - area.regions[1].width
    prefs = get_prefs(context)
    padding = V((prefs.offset[0], prefs.offset[1]))
    x = y = min(region_width / (prefs.size + padding.x * 2), prefs.max_size)
    size = V((prefs.size * x, prefs.size * y))
    size.y *= (node_area.size.y / node_area.size.x)

    area_size = V([region_width, region.height])
    location = area_size - padding
    min_co = V((location.x - size.x, location.y))
    max_co = V((location.x, location.y + size.y))
    map_area = Rectangle(min_co=min_co, max_co=max_co)
    return map_area


def node_area_to_map_area(coords, node_area, map_area) -> V:
    """Converts the coords from local node space to minmap space"""
    fac = pos_to_fac(coords, node_area)
    loc = vec_lerp(fac, map_area.min, map_area.max)
    return loc


def get_node_rect(node, node_area, map_area, scale, loc) -> Rectangle:
    """Returns a rectangle representing the minimap version of this node"""
    dims = node.dimensions.copy()
    dims.x = node.width
    dims.y *= -1
    dims = get_node_dims(node)
    dims = vec_multiply(dims, scale)
    loc = node_area_to_map_area(loc, node_area, map_area)
    node_rect = Rectangle(loc, loc + dims)
    return node_rect


def draw_view_box(view_area, node_area, map_area, line_width=2):
    """Draw the box representing the 2D camera view"""
    view_area.min = node_area_to_map_area(view_area.min, node_area, map_area)
    view_area.max = node_area_to_map_area(view_area.max, node_area, map_area)
    view_box = Rectangle(view_area.min, view_area.max)
    view_box.crop(map_area)
    draw_lines_from_quad_2d(view_box.coords, (0.75, 0.75, 0.75, 1), width=line_width)


def get_area(self, context) -> Area:
    """The default operator context doesn't update when the mouse moves,
    so this works out the active area from scratch"""
    for area in context.screen.areas:
        if str(area) == self.area:
            return area
    return context.area


def get_prefs(context) -> AddonPreferences:
    """Return the addon preferences"""
    return context.preferences.addons[__package__].preferences


def get_minimap_cache(context) -> CacheContainer:
    """Returns the scene minimap cache"""
    return context.window_manager.minimap_cache


def get_shader_cache(context) -> ShaderCache:
    """Returns the scene shader cache"""
    return get_minimap_cache(context).shader_cache
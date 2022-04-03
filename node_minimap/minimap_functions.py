from __future__ import annotations
from mathutils import Vector as V
from ..shared.helpers import Rectangle, vec_lerp, vec_multiply
from ..shared.functions import get_prefs, pos_to_fac, get_node_dims, draw_lines_from_quad_2d

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shader_cache import ShaderCache, CacheContainer


def get_map_area(context, area, node_area) -> Rectangle:
    """Returns a rectangle representing the size, shape and position of the minimap box"""
    region = area.regions[3]
    # We need to take into account the size of the header
    region_height = region.height - (area.regions[0].height / 2)
    region_height = region.height

    prefs = get_prefs(context)
    size = min(max(region.width * prefs.size, prefs.min_size), prefs.max_size)
    size = V((size, size))
    size.y *= (node_area.size.y / node_area.size.x)

    padding = V(prefs.offset)

    area_size = V([region.width, region_height])
    corner = prefs.anchor_corner

    # If breadcrumbs are enabled, move the minimap down so they don't overlap
    if corner == "TL":
        show_path = area.spaces[0].overlay.show_context_path
        if show_path:
            padding.y += 30

    min_co = V((0, 0))
    max_co = V((0, 0))

    # corner is a string in ["BL", "TR", "TL", "BR"] for bottom-left, top-right, etc.
    if "B" in corner:
        min_co.y = padding.y
        max_co.y = min_co.y + size.y
    else:
        max_co.y = area_size.y - padding.y
        min_co.y = max_co.y - size.y

    if "L" in corner:
        min_co.x = padding.x
        max_co.x = min_co.x + size.x
    else:
        max_co.x = area_size.x - padding.x
        min_co.x = max_co.x - size.x

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


def draw_view_box(view_area, node_area, map_area, color, line_width=2):
    """Draw the box representing the 2D camera view"""
    view_area.min = node_area_to_map_area(view_area.min, node_area, map_area)
    view_area.max = node_area_to_map_area(view_area.max, node_area, map_area)
    view_box = Rectangle(view_area.min, view_area.max)
    view_box.crop(map_area)
    draw_lines_from_quad_2d(view_box.coords, color, width=line_width)


def get_minimap_cache(context) -> CacheContainer:
    """Returns the scene minimap cache"""
    return context.window_manager.minimap_cache


def get_shader_cache(context) -> ShaderCache:
    """Returns the scene shader cache"""
    return get_minimap_cache(context).shader_cache
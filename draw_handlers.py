import bpy
import blf
from mathutils import Vector as V
from .helpers import Rectangle, get_active_tree, vec_min, vec_max, vec_divide, vec_multiply
from .functions import get_node_dims, get_node_loc, draw_quads_2d, draw_lines_from_quad_2d, get_node_color, get_prefs,\
    node_area_to_map_area, draw_view_box, get_area
from time import perf_counter

times = []


def draw_callback_px(self, context: bpy.types.Context):
    """Called by every operator when there's a redraw"""
    area = get_area(self, context)
    # the operator context.area remains the same even when the actual context is updated
    if context.area != area:
        # This filters out calls from operators that arent in the correct area,
        # so that the draw function only runs once per area
        return
    
    # for measuring performance
    start = perf_counter()
    prefs = get_prefs(context)

    node_tree = context.space_data.node_tree
    if not node_tree:
        return
    node_tree = get_active_tree(context)

    theme = context.preferences.themes[0].node_editor
    color = list(theme.grid)
    color.append(0.9)

    node_area = Rectangle((10000, 10000), (-1000, -1000))
    if node_tree:
        for node in node_tree.nodes:
            dims = get_node_dims(node)
            loc = get_node_loc(node)
            node_area.min = vec_min(loc + V((0, dims.y)), node_area.min)
            node_area.max = vec_max(loc + V((dims.x, 0)), node_area.max)
    self.node_area = node_area

    padding = V((prefs.offset[0], prefs.offset[1]))
    x = y = min(area.width / (prefs.size + padding.x * 2), prefs.max_size)
    size = V((prefs.size * x, prefs.size * y))
    size.y *= (node_area.size.y / node_area.size.x)
    line_width = size.x / 100

    region = area.regions[0]
    area_size = V([region.width, region.height])
    # print(area_size)
    location = area_size - padding
    min_co = V((location.x - size.x, location.y))
    max_co = V((location.x, location.y + size.y))
    map_area = Rectangle(min_co=min_co, max_co=max_co)
    self.map_area = map_area
    draw_quads_2d(map_area.coords, color)

    scale = vec_divide(map_area.size, node_area.size)

    if node_tree:
        for node in node_tree.nodes:
            if node.type == "REROUTE":
                continue
            # Get the color. This is slow and needs to be cached
            color = get_node_color(context, node)
            loc = get_node_loc(node)

            # get dimensions of the node relative to the minimap
            dims = node.dimensions.copy()
            dims.x = node.width
            dims.y *= -1
            dims = get_node_dims(node)
            dims = vec_multiply(dims, scale)
            loc = node_area_to_map_area(loc, node_area, map_area)
            node_rect = Rectangle(loc, loc + dims)

            # draw the box for each node
            draw_quads_2d(node_rect.coords, color)
            # draw outlines
            if node == node_tree.nodes.active:
                color = list(theme.node_active)
                if len(color) < 4:
                    color.append(1)
                draw_lines_from_quad_2d(node_rect.coords, (1, 1, 1, 0.8), width=line_width)
            elif node.select:
                color = list(theme.node_selected)
                if len(color) < 4:
                    color.append(1)
                draw_lines_from_quad_2d(node_rect.coords, color, width=line_width)

    # Draw the box representing the viewport camera
    region_to_view = context.region.view2d.region_to_view
    view_min = region_to_view(0, 0)
    view_max = region_to_view(context.region.width, context.region.height)
    view_area = Rectangle(view_min, view_max)
    self.view_area = view_area
    draw_view_box(view_area, node_area, map_area)

    # Draw debug text in the bottom left
    font_id = 0  # XXX, need to find out how best to get this.
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)
    # blf.draw(font_id, "Hello Word " + str(len(self.mouse_path)))
    blf.draw(font_id, str(self.idx))

    global times
    times.append(perf_counter() - start)
    if len(times) > 20:
        # uncomment to get the averaged draw times
        # from statistics import mean
        # print(mean(times))
        times = []

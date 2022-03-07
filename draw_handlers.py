import bpy
from .helpers import Rectangle, get_active_tree
from .functions import draw_quads_2d, draw_view_box, get_area, get_prefs, get_shader_cache
from .shader_cache import NodeCache
from time import perf_counter
from statistics import mean

times = []
main_times = []
final = 0


def handler_create(self, context: bpy.types.Context):
    """Initialize an operator for every visible node tree area that doesn have one yet"""
    screen = context.screen
    start = perf_counter()
    for area in screen.areas:
        if area.type == "NODE_EDITOR" and str(area) not in self.areas:
            self.areas.append(str(area))
            bpy.ops.node.draw_area_minimap("INVOKE_DEFAULT", area=str(area), idx=len(self.areas) - 1)

    remove = []
    for area_name in self.areas:
        for area in screen.areas:
            if area_name == str(area):
                break
        else:
            remove.append(area_name)

    for area_name in remove:
        self.areas.remove(area_name)

    cache = get_shader_cache(context)
    cache.update(context)
    global main_times
    global final
    main_times.append(perf_counter() - start)
    if len(main_times) > 20:
        final = mean(main_times)
        main_times = []


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
    node_tree = context.space_data.node_tree
    if not node_tree:
        return
    node_tree = get_active_tree(context, area=area)

    theme = context.preferences.themes[0].node_editor
    color = list(theme.grid)
    color.append(0.9)

    cache = get_shader_cache(context)
    area_cache = cache.areas[str(area)]
    area_cache.update(context, node_tree)
    map_area = self.map_area = area_cache.map_area
    node_area = self.node_area = area_cache.node_area
    line_width = map_area.size.x / 250
    draw_quads_2d(map_area.coords, color)

    prefs = get_prefs(context)
    if node_tree:
        for node_cache in area_cache.all_nodes:
            node_cache: NodeCache
            if prefs.only_top_level:
                if not node_cache.parent and node_cache.draw:
                    node_cache.draw_node(context, line_width)
            else:
                if node_cache.draw:
                    node_cache.draw_node(context, line_width)

    # Draw the box representing the viewport camera
    region_to_view = context.region.view2d.region_to_view
    view_min = region_to_view(0, 0)
    view_max = region_to_view(context.region.width, context.region.height)
    view_area = Rectangle(view_min, view_max)
    self.view_area = view_area
    draw_view_box(view_area, node_area, map_area, line_width)

    # # Draw debug text in the bottom left
    # import blf
    # font_id = 0  # XXX, need to find out how best to get this.
    # blf.position(font_id, 15, 30, 0)
    # blf.size(font_id, 20, 72)
    # # blf.draw(font_id, "Hello Word " + str(len(self.mouse_path)))
    # blf.draw(font_id, str(self.idx))

    global times
    global final
    times.append(perf_counter() - start)
    if len(times) > 20:
        # uncomment to get the averaged draw times
        # print(mean(times))
        # print("Total: " + str(mean(times) + final))
        times = []

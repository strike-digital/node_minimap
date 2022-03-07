import bpy
from typing import Set
from mathutils import Vector as V
from .helpers import get_active_tree, vec_divide
from .functions import draw_lines_from_quad_2d_batch, draw_quads_2d_batch, get_batch_from_quads_2d,\
    get_batch_lines_from_quad_2d, get_map_area, get_node_area, get_node_color, get_node_loc, get_node_rect
"""
This is very much not finished,
and should eventually work to speed up drawing as it can be quite slow at the moment
"""


class CacheContainer():
    shader_cache = None


class ShaderCache():

    def __init__(self):
        self.areas = {}
        self.node_trees: Set[AreaCache]

    @property
    def area_ids(self):
        return {cache.area_name for cache in self.areas.values()}

    def update(self, context):
        area_names = set()
        for area in context.screen.areas:
            if area.type == "NODE_EDITOR" and area.spaces[0].node_tree:
                area_names.add(str(area))

                if str(area) not in self.area_ids:
                    self.areas[str(area)] = AreaCache(context, area)

        remove = set()
        for cache in self.areas.values():
            if cache.area_name not in area_names:
                remove.add(cache)

        for cache in remove:
            del self.areas[cache.area_name]


idx = 0


class AreaCache():

    def __init__(self, context, area):
        self.all_nodes = []
        self.area_name = str(area)
        self.region_size = V((area.regions[0].width - area.regions[1].width, area.regions[0].height))
        self.update_areas(context, force=True)
        self.current_node_tree_name = self.node_tree.name
        self.tag_update = False

    def update_areas(self, context, force=False):
        # current_size = V((self.area.width, self.area.height))
        current_size = V((self.area.regions[0].width - self.area.regions[1].width, self.area.regions[0].height))
        if force or self.region_size != current_size:
            self.node_area = get_node_area(self.node_tree)
            self.map_area = get_map_area(context, self.area, self.node_area)
            self.scale = vec_divide(self.map_area.size, self.node_area.size)
            for node_cache in self.all_nodes:
                node_cache.update_loc_dims(node_cache.node)
            self.region_size = current_size

        # if self.area_size != current_size:
        #     self.node_area = get_node_area(self.node_tree)
        #     self.map_area = get_map_area(context, self.area, self.node_area)
        #     self.scale = vec_divide(self.map_area.size, self.node_area.size)
        #     return

    @property
    def node_names(self):
        return {cache.node_name for cache in self.all_nodes}

    @property
    def area(self):
        for area in bpy.context.screen.areas:
            if str(area) == self.area_name:
                return area
        return None

    @property
    def node_tree(self):
        area = self.area
        tree = get_active_tree(bpy.context, area)
        return tree

    def update(self, context, node_tree):
        nt = node_tree
        if nt:
            if nt.name != self.current_node_tree_name:
                self.all_nodes.clear()
                self.update_areas(context, force=True)
                self.current_node_tree_name = nt.name
            # add missing nodes
            if len(nt.nodes) != len(self.all_nodes):
                for node in nt.nodes:
                    if node.name not in self.node_names:
                        self.all_nodes.append(NodeCache(node, self, nt))

            # delete removed nodes
            for cache in list(self.all_nodes):
                node = self.node_tree.nodes.get(cache.node_name)
                if node:
                    cache.update(context)
                else:
                    self.all_nodes.remove(cache)

        self.update_areas(context, force=self.tag_update)
        self.tag_update = False


class NodeCache():

    batch = None

    def __init__(self, node, area_cache, node_tree):
        self.draw = node.type != "REROUTE"
        self.node_name = node.name
        self.area_cache = area_cache

        self.color = node.color.copy()
        self.location = node.location.copy()
        self.dimensions = node.dimensions.copy()
        self.width = node.width
        self.is_frame = node.type == "FRAME"
        self.select = node.select
        self.use_custom_color = node.use_custom_color
        self.parent = node.parent
        self.node_tree = node_tree

        self.theme_color = get_node_color(bpy.context, node)
        self.visual_location = get_node_loc(node)
        self.node_rect = get_node_rect(
            node,
            area_cache.node_area,
            area_cache.map_area,
            area_cache.scale,
            self.visual_location,
        )
        self.batch = get_batch_from_quads_2d(self.node_rect.coords)
        self.outline_batch = get_batch_lines_from_quad_2d(self.node_rect.coords)
        theme = bpy.context.preferences.themes[0].node_editor
        self.active_color = list(theme.node_active) + [0.9]
        self.selected_color = list(theme.node_selected) + [0.9]

    @property
    def node(self):
        return self.node_tree.nodes.get(self.node_name)

    def draw_node(self, context, line_width):
        # Get the color. This is slow and needs to be cached
        node = self.node

        # draw the box for each node
        draw_quads_2d_batch(self.batch, self.theme_color)
        # draw outlines
        node_tree = node.id_data
        if node == node_tree.nodes.active:
            draw_lines_from_quad_2d_batch(self.outline_batch, self.active_color, line_width)
        elif node.select:
            draw_lines_from_quad_2d_batch(self.outline_batch, self.selected_color, line_width)

    def update_loc_dims(self, node=None):
        if not node:
            node = self.node
        self.visual_location = get_node_loc(node)
        self.node_rect = get_node_rect(
            node,
            self.area_cache.node_area,
            self.area_cache.map_area,
            self.area_cache.scale,
            self.visual_location,
        )
        self.batch = get_batch_from_quads_2d(self.node_rect.coords)
        self.outline_batch = get_batch_lines_from_quad_2d(self.node_rect.coords)
        self.parent = node.parent

    def update_color(self, node):
        if node.use_custom_color:
            self.theme_color = list(node.color) + [0.95]  # The alpha value
        else:
            self.theme_color = get_node_color(bpy.context, node)

    def update(self, context):
        node = self.node
        if node.location != self.location or node.width != self.width:
            self.location = node.location.copy()
            self.width = node.width
            self.area_cache.tag_update = True
        if node.use_custom_color != self.use_custom_color or node.color != self.color:
            self.update_color(node)
            self.use_custom_color = node.use_custom_color
            self.color = node.color.copy()


def register():
    bpy.types.WindowManager.minimap_cache = CacheContainer()
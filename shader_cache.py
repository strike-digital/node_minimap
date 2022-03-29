import bpy
import blf
from typing import Dict, List
from mathutils import Vector as V
from .helpers import get_active_tree, get_alt_node_tree_name, vec_divide
from .functions import draw_lines_from_quads_2d_batch, draw_quads_2d_batch, get_batch_from_quads_2d,\
    get_batch_lines_from_quads_2d, get_map_area, get_node_area, get_node_color, get_node_loc, get_node_rect, get_prefs
"""
The caching system makes understanding how the minimap drawing works quite a lot harder, so if you want to do that,
I'd advise getting the first release on GitHub, and looking at that first. It will be a lot slower though.

From some quite unscientific testing, I found that using the caching system increases drawing speed by:
- while panning:                                     8x faster
- while modifying nodes (location, color, etc.):     2x faster

It works simply by caching attributes such as shader batches, and only recaculating them when they area needed,
rather than every redraw like previously.
"""


class CacheContainer():
    """Only here because you can't modify top level attributes,
    and a new instance of ShaderCache is created every time the operator is run"""
    shader_cache = None


class ShaderCache():
    """
    The global cache for areas and nodes. The hierarchy is like this:
    Scene -> ShaderCache -> AreaCache -> NodeCache
    where '->' means 'parent of'.
    """

    def __init__(self):
        """This level doesn't cache anything, it just acts as a parent for the currently visible areas."""
        self.areas = {}
        self.areas: Dict[str, AreaCache]

    @property
    def area_ids(self):
        """Return a list of area ids (str(area))"""
        return {cache.area_name for cache in self.areas.values()}

    def update(self, context):
        """Called once per redraw
        This checks to see if there are any new areas, or if any have been removed,
        and adds/removes the respective AreaCache"""
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


class AreaCache():
    """Represents an area, and caches it's attributes (mainly size and node tree)"""

    def __init__(self, context, area):
        """Store initial cached attributes"""
        self.all_nodes = []
        self.all_nodes: List[NodeCache]
        self.area_name = str(area)
        # get size (regions[0]) minus the n-panel (regions[1])
        self.region_size = V((area.regions[0].width - area.regions[1].width, area.regions[0].height))
        self.update_areas(context, force=True)
        self.current_node_tree_name = self.node_tree.name
        self.tag_update = False
        self.quad_batch = get_batch_from_quads_2d(self.map_area.coords)
        self.outline_batch = get_batch_lines_from_quads_2d(self.map_area.coords)

    def update_areas(self, context, force=False):
        """Update cached node and map area
        (the rectangles representing local node space and minimap space respectively), along with region size and scale
        (The scale factor between the node and map areas)"""
        # get size (regions[0]) minus the n-panel (regions[1])
        current_size = V((self.area.regions[0].width - self.area.regions[1].width, self.area.regions[0].height))
        if force or self.region_size != current_size:
            self.node_area = get_node_area(self.node_tree)
            self.map_area = get_map_area(context, self.area, self.node_area)
            self.scale = vec_divide(self.map_area.size, self.node_area.size)
            self.quad_batch = get_batch_from_quads_2d(self.map_area.coords)
            self.outline_batch = get_batch_lines_from_quads_2d(self.map_area.coords)
            for node_cache in self.all_nodes:
                node_cache.update_loc_dims(node_cache.node)
            self.region_size = current_size

    @property
    def node_names(self):
        """Get the names of all cached nodes"""
        return {cache.node_name for cache in self.all_nodes}

    @property
    def area(self):
        """Return the area data block. Only the name is cached,
        as Blender can go funky when you keep direct references to data blocks for a long time"""
        for area in bpy.context.screen.areas:
            if str(area) == self.area_name:
                return area
        return None

    @property
    def node_tree(self):
        """Get the node tree for this area. Same as above"""
        area = self.area
        tree = get_active_tree(bpy.context, area)
        return tree

    def update(self, context, node_tree):
        """Called once per area per draw.
        Updates the node cache to include new nodes, and removes nodes that aren't in the tree anymore.
        A side effect of this system is that when the name of a node is changed, the cache for that node is removed,
        and then recreated in the next draw call, causing a slight jump. Not a big problem though."""
        nt = node_tree
        if nt:
            if nt.name != self.current_node_tree_name:
                self.all_nodes.clear()
                self.update_areas(context, force=True)
                self.current_node_tree_name = nt.name
            # add missing nodes
            if len(nt.nodes) != len(self.all_nodes):
                self.tag_update = True
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
    """Represents a single node, and caches it's attributes"""

    batch = None

    def __init__(self, node, area_cache, node_tree):
        """Initialize all cached variables for this node. The main, and slowest ones to calculate are:
        color, location, and the actual shader batch. These are updated only when needed to improve speed."""
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

        # check if it is ashader or compositor node tree that is bound to either a material or scene,
        # and doesn't show up in bpy.data.node_groups
        nt = bpy.data.node_groups.get(node_tree.name)
        if nt:
            self.node_tree_name = node_tree.name
        else:
            self.node_tree_name = get_alt_node_tree_name(node_tree)
        self.tree_type = node_tree.type

        self.update_loc_dims(node)
        self.update_color(bpy.context, node)
        theme = bpy.context.preferences.themes[0].node_editor
        self.active_color = list(theme.node_active) + [0.9]  # add alpha channel
        self.selected_color = list(theme.node_selected) + [0.9]  # add alpha channel

    @property
    def node_tree(self):
        """Get the node tree of this node. Direct references can't be kept because they are removed on undo,
        So only the name is cached, and the actual data block is got dynamically"""
        nt = bpy.data.node_groups.get(self.node_tree_name)
        # Check if nt is bound to material or scene (shader or compositing)
        if not nt:
            # Get node tree if it is a shader, compsitor or world nodetree,
            # as these don't show up in bpy.data.node_groups
            for tree_subtype in ["materials", "scenes", "worlds"]:
                data = getattr(bpy.data, tree_subtype)
                if self.node_tree_name in data.keys():
                    nt = data[self.node_tree_name].node_tree
        return nt

    @property
    def node(self):
        """Get the node data block for this cache. Same deal as above"""
        return self.node_tree.nodes.get(self.node_name)

    def get_is_frame_used(self):
        """Check if a frame has any children. If it doesn't and the setting in preferences is off, it won't be rendered
        This is because it doesn't seem to be possible to get the visual location of a frame if it doesn't have any
        child nodes..."""
        node = self.node
        for n in node.id_data.nodes:
            if n.parent == node:
                return True
        return False

    def update_loc_dims(self, node=None):
        """Update cached data relating to location and size"""
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
        self.outline_batch = get_batch_lines_from_quads_2d(self.node_rect.coords)
        self.is_frame_used = self.get_is_frame_used()
        self.can_draw = self.check_can_draw(bpy.context)
        self.parent = node.parent
        self.update_label(node)

    def update_color(self, context, node):
        """Update cached data relating to color"""
        prefs = get_prefs(context)
        if node.use_custom_color:
            self.theme_color = list(node.color) + [prefs.node_transparency]  # The alpha value
        else:
            self.theme_color = get_node_color(bpy.context, node)

    def update_label(self, node):
        self.label = node.label
        node_rect = self.node_rect
        dims = blf.dimensions(0, node.label)
        posx = (node_rect.minx + (node_rect.maxx - node_rect.minx) / 2) - dims[0] / 2
        posy = node_rect.miny - dims[1]
        self.label_pos = V((posx, posy))

    def check_can_draw(self, context):
        prefs = get_prefs(context)
        return not (not self.draw or\
        (prefs.only_top_level and self.parent) or\
        (not prefs.show_non_full_frames and self.is_frame and not self.is_frame_used) or\
        (not prefs.show_non_frames and not self.is_frame))  # noqa

    def draw_node(self, context, line_width):
        """Draw this node using it's cached data"""
        prefs = get_prefs(context)
        # Check if node should be drawn
        if not self.can_draw:
            return

        # Get the color. This is slow and needs to be cached
        node = self.node
        color = self.theme_color if prefs.use_node_colors or node.use_custom_color else prefs.node_color

        # draw the box for each node
        draw_quads_2d_batch(self.batch, color)
        # draw outlines
        node_tree = node.id_data
        if node.select:
            draw_lines_from_quads_2d_batch(self.outline_batch, self.selected_color, line_width)
            if node == node_tree.nodes.active:
                draw_lines_from_quads_2d_batch(self.outline_batch, self.active_color, line_width)

    def draw_label(self):
        prefs = get_prefs(bpy.context)
        if self.is_frame and self.label and (not prefs.show_non_frames or prefs.only_top_level):
            # self.update_label(self.node)
            node_size = self.node_rect.size
            size = min(node_size.x, abs(node_size.y) * 5)
            if size < prefs.min_frame_size:
                return

            minsize = 50
            size = max(size, minsize)
            # size = max(node_size.x, minsize)
            blf.size(0, size, 10)

            color = prefs.text_color
            blf.color(0, color[0], color[1], color[2], color[3])

            node = self.node

            dims = blf.dimensions(0, node.label)
            node_rect = self.node_rect
            posx = (node_rect.minx + (node_rect.maxx - node_rect.minx) / 2) - dims[0] / 2
            posy = node_rect.miny - dims[1]

            # words
            if prefs.text_wrap:
                words = node.label.split()
                string = ""
                prev_dims = (0, 0)
                lines = []
                for i, word in enumerate(words):
                    next_word = words[i + 1] if i != len(words) - 1 else ""
                    string = string + " " + word
                    dims = blf.dimensions(0, string)

                    # check if next word will overlap with sides
                    next_dims = blf.dimensions(0, string + next_word)
                    if next_dims[0] > size or i == len(words) - 1:
                        posy -= prev_dims[1] + dims[1] * 0.3
                        posx = (node_rect.minx + (node_rect.maxx - node_rect.minx) / 2) - dims[0] / 2
                        lines.append({"string": string, "posx": posx, "posy": posy, "dims": dims})
                        # blf.position(0, posx, posy, 0)
                        # blf.draw(0, string)
                        string = ""
                        prev_dims = dims

                total_height = sum([line["dims"][1] for line in lines])
                total_width = max([line["dims"][0] for line in lines])
                if total_height > node_size.y:
                    blf.size(0, max(int(abs(node_size.y)), minsize), 10)
                    # blf.size(0, max(size-abs(node_size.y), minsize), 10)
                if total_width > node_size.x:
                    blf.size(0, max(int(int(abs(node_size.x))), minsize), 10)

                for line in lines:
                    blf.position(0, line["posx"], line["posy"], 0)
                    blf.draw(0, line["string"])
            else:
                blf.position(0, posx, posy, 0)
                blf.draw(0, node.label)

    def update(self, context):
        """Called once per node per area per draw (a.k.a a lot). This is where the most optimisation has been done"""
        node = self.node
        if not self.area_cache.tag_update and node.location != self.location or node.width != self.width:
            self.location = node.location.copy()
            self.width = node.width
            self.area_cache.tag_update = True
        if node.use_custom_color != self.use_custom_color or node.color != self.color:
            self.update_color(context, node)
            self.use_custom_color = node.use_custom_color
            self.color = node.color.copy()
        # if node.label != self.label:
        #     self.update_label(node)


# register the top level cache
def register():
    bpy.types.WindowManager.minimap_cache = CacheContainer()
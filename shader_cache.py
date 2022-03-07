import bpy
from .functions import get_node_color
from typing import Set


"""
This is very much not finished,
and should eventually work to speed up drawing as it can be quite slow at the moment
"""


class CacheContainer():
    shader_cache = None


class ShaderCache():

    def __init__(self):
        self.node_trees = set()
        self.node_trees: Set[NodeTreeCache]

    @property
    def tree_names(self):
        return {cache.node_tree_name for cache in self.node_trees}

    def update(self, context):
        node_tree_names = set()
        for area in context.screen.areas:
            if area.type == "NODE_TREE" and area.spaces[0].node_tree:
                tree = area.spaces[0].node_tree
                node_tree_names.add(tree.name)

                if tree.name not in self.tree_names:
                    self.node_trees.add(NodeTreeCache(tree))

        for cache in list(self.node_trees):
            group = bpy.data.node_groups.get(cache.node_tree_name)
            if group:
                cache.update()
                break
            else:
                self.node_trees.remove(cache)


class NodeTreeCache():

    def __init__(self, node_tree):
        self.all_nodes = set()
        self.node_tree_name = node_tree.name

    @property
    def tree_names(self):
        return {cache.node_name for cache in self.all_nodes}

    @property
    def node_tree(self):
        return bpy.data.node_groups.get(self.node_tree_name)

    def update(self, context):
        nt = bpy.data.node_groups.get(self.node_tree_name)
        if nt:
            for node in nt.nodes:
                if node.name not in self.tree_names:
                    self.all_nodes.add(NodeCache(node))
            
        if len(nt.nodes) != len(self.all_nodes):
            for cache in list(self.all_nodes):
                node = self.node_tree.nodes.get(cache.node_name)
                if node:
                    break
                else:
                    self.all_nodes.remove(cache)


class NodeCache():

    batch = None

    def __init__(self, node):
        self.node_name = node.name
        self.color = node.color.copy()
        self.location = node.location.copy()
        self.dimensions = node.dimensions.copy()
        self.is_frame = node.type == "FRAME"
        self.select = node.select
    
        self.theme_color = get_node_color(bpy.context, node)


def register():
    bpy.types.WindowManager.minimap_cache = CacheContainer()
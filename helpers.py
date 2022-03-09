import bpy
from bpy.types import NodeTree, Area, Region
from mathutils import Vector as V


class Rectangle():
    """Helper class to represent a rectangle"""

    def __init__(self, min_co=(0, 0), max_co=(0, 0)):
        min_co = V(min_co)
        max_co = V(max_co)

        self.min = min_co
        self.max = max_co

    # alternate getter syntax
    minx = property(fget=lambda self: self.min.x)
    miny = property(fget=lambda self: self.min.y)
    maxx = property(fget=lambda self: self.max.x)
    maxy = property(fget=lambda self: self.max.y)

    @property
    def coords(self):
        """Return corrdinates for drawing"""
        coords = [
            (self.minx, self.miny),
            (self.maxx, self.miny),
            (self.maxx, self.maxy),
            (self.minx, self.maxy),
        ]
        return coords

    @property
    def size(self):
        return self.max - self.min

    @property
    def center(self):
        return self.min + vec_divide(self.max - self.min, V((2, 2)))

    # return the actual min/max values. Needed because the class does not check
    # if the min and max values given are actually min and max at init.
    # I could fix it, but a bunch of stuff is built on it already, and I can't really be bothered
    @property
    def true_min(self):
        return vec_min(self.min, self.max)

    @property
    def true_max(self):
        return vec_max(self.min, self.max)

    def __str__(self):
        return f"Rectangle(V({self.minx}, {self.miny}), V({self.maxx}, {self.maxy}))"

    def __repr__(self):
        return self.__str__()

    def __mul__(self, value):
        if not isinstance(value, V):
            value = V((value, value))
        return Rectangle(self.min * value, self.max * value)

    def __add__(self, value):
        if not isinstance(value, V):
            value = V((value, value))
        return Rectangle(self.min + value, self.max + value)

    def isinside(self, point) -> bool:
        """Check if a point is inside this rectangle"""
        point = V(point)
        min = self.true_min
        max = self.true_max
        for i in range(2):
            if (point[i] < min[i]) or (point[i] > max[i]):
                return False
        return True

    def crop(self, rectangle):
        self.min = vec_max(self.min, rectangle.min)
        self.max = vec_min(self.max, rectangle.max)
        # prevent min/max overspilling on other side
        self.min = vec_min(self.min, rectangle.max)
        self.max = vec_max(self.max, rectangle.min)


def lerp(fac, a, b) -> float:
    """Linear interpolation (mix) between two values"""
    return (fac * b) + ((1 - fac) * a)


def vec_lerp(fac, a, b) -> V:
    """Elementwise vector linear interpolation (mix) between two vectors"""
    return V(lerp(f, e1, e2) for f, e1, e2 in zip(fac, a, b))


def vec_divide(a, b) -> V:
    """Elementwise divide for two vectors"""
    return V(e1 / e2 if e2 != 0 else 0 for e1, e2 in zip(a, b))


def vec_multiply(a, b) -> V:
    """Elementwise multiply for two vectors"""
    return V(e1 * e2 for e1, e2 in zip(a, b))


def vec_min(a, b) -> V:
    """Elementwise minimum for two vectors"""
    return V(min(e) for e in zip(a, b))


def vec_max(a, b) -> V:
    """Elementwise maximum for two vectors"""
    return V(max(e) for e in zip(a, b))


def get_active_tree(context, area=None) -> NodeTree:
    """Get nodes from currently edited tree.
    If user is editing a group, space_data.node_tree is still the base level (outside group).
    context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    the same as context.active_node, the user is in a group.
    source: node_wrangler.py"""

    if not area:
        tree = context.space_data.node_tree
    else:
        tree = area.spaces[0].node_tree

    if tree.nodes.active:
        # Check recursively until we find the real active node_tree
        # This wont work if there are two editors open with the same node tree so that a node that is not the
        # correct group can be selected. In that case, simply the deepest node tree will be returned
        while (tree.nodes.active != context.active_node) and tree.nodes.active.type == "GROUP":
            tree = tree.nodes.active.node_tree
            continue

    return tree


def get_active_area(context: bpy.types.Context, mouse_pos: V) -> Area:
    """The area given by the context is locked to the area the operator is executed in,
    so this works it out from scratch"""
    screen = context.screen
    for area in screen.areas:
        rect = Rectangle(V((area.x, area.y)), V((area.x + area.width, area.y + area.height)))
        if rect.isinside(mouse_pos):
            return area
    return context.area


def get_active_region(context, mouse_pos) -> Region:
    """The region given by the context is locked to the area the operator is executed in,
    so this works it out from scratch"""
    area = get_active_area(context, mouse_pos)
    for region in area.regions:
        rect = Rectangle(V((region.x, region.y)), V((region.x + region.width, region.y + region.height)))
        if rect.isinside(mouse_pos):
            return region
    return context.region


def get_alt_node_tree_name(node_tree) -> str:
    """Get's the name of the parent data block for this node tree
    Only necessary if the tree is attached to a material or scene (shading or compositing)"""
    # "bpy.data.materials['Material'].node_tree"
    # returns 'Material'
    # Not a good way to do it, but I can't find a better one :(
    return repr(node_tree.id_data).split("'")[1]
import bpy
from math import pi
from statistics import mean
from mathutils import Vector as V
from mathutils.geometry import intersect_point_tri_2d, interpolate_bezier, area_tri
from bpy.types import NodeTree, Context
from time import perf_counter
from typing import List
from collections import deque

WHITE = '\033[37m'
RED = '\033[91m'
GREEN = '\033[92m'


class Timer():
    """Class that allows easier timing of sections of code"""

    def __init__(self, average_of=20):
        self.start_times = {}
        self.end_times = {}
        self.indeces = {}
        self.average_of = average_of

    def start(self, name):
        """Set the start time for this name"""
        self.start_times[name] = perf_counter()

    def stop(self, name):
        """Add an end time for this name"""
        time = perf_counter() - self.start_times[name]
        prev_times = self.end_times.get(name, deque(maxlen=self.average_of))

        prev_times.append(time)
        self.end_times[name] = prev_times
        self.indeces[name] = (self.indeces.get(name, 0) + 1) % self.average_of

    def get_time(self, name):
        return mean(self.end_times[name])

    def get_total(self):
        return sum([mean(self.end_times[name]) for name in self.end_times.keys()])

    def print_average(self, name):
        average = mean(self.end_times[name])
        if self.indeces[name] >= self.average_of - 2:
            print(f"{name}: {' ' * (20 - len(name))}{average:.20f}")
        return average

    def print_all(self, accuracy=6):
        """Print all active timers with formatting.
        Accuracy is the number of decimal places to display"""
        if self.indeces[list(self.indeces.keys())[0]] >= self.average_of - 2:
            string = ""
            items = sorted(self.end_times.items(), key=lambda i: mean(i[1]), reverse=True)
            for i, (k, v) in enumerate(items):
                if i == 0:
                    color = RED
                elif i == len(items) - 1:
                    color = GREEN
                else:
                    color = WHITE
                average = mean(v)
                string += f"{color}{k}: {' ' * (20 - len(k))}{average:.{accuracy}f}\n"
            string += WHITE
            print(string)


class Polygon():
    """Helper class to represent a polygon of n points"""

    def __init__(self, verts: list[V] = []):
        self.verts = verts

    @property
    def verts(self):
        return getattr(self, "_verts", [])

    @verts.setter
    def verts(self, points):
        if not points:
            return
        points = [V(p) for p in points]
        self._verts = points

    def center(self):
        verts = self.verts
        return vec_mean(verts) if verts else V((0, 0))

    def is_inside(self, point: V) -> bool:
        """Check if a point is inside this polygon"""
        center = self.center()
        for i, vert in enumerate(self.verts):
            if intersect_point_tri_2d(point, vert, self.verts[i - 1], center):
                return True
        return False

    def as_tris(self, individual=False):
        """Return the tris making up this polygon"""
        points = []
        add = points.append if individual else points.extend
        center = self.center()
        for i, vert in enumerate(self.verts):
            point = [vert, self.verts[i - 1], center]
            add(point)
        return points

    def as_lines(self, individual=False):
        """Return the lines making up the outline of this polygon as a single list"""
        points = []
        add = points.append if individual else points.extend
        for i, vert in enumerate(self.verts):
            add([vert, self.verts[i - 1]])
        return points

    def area(self):
        area = 0
        for tri in self.as_tris(individual=True):
            # area += area_tri(*tri)
            area += area_tri(tri[0], tri[1], tri[2])
        return area

    def distance_to_edges(self, point: V, edges: List[List[V]] = None) -> float:
        """Get the minimum distance of a point from a list of edges.
        Code adapted from from: https://www.fundza.com/vectors/point2line/index.html"""
        edges = edges if edges else self.as_lines(individual=True)
        distances = []
        for edge in edges:
            start = edge[0]
            end = edge[1]

            line_vec = start - end
            pnt_vec = start - point
            line_len = line_vec.length
            line_unitvec = line_vec.normalized()

            pnt_vec_scaled = pnt_vec * 1.0 / line_len
            t = line_unitvec.dot(pnt_vec_scaled)
            t = max(0, min(1, t))

            nearest = line_vec * t
            dist = (nearest - pnt_vec).length
            distances.append(dist)
        if distances:
            return min(distances)
        else:
            return 700000000

    def bevelled(self, radius=15):
        """Smooth the corners by using bezier interpolation between the last point,
        the current point and the next point."""
        bevelled = []
        verts = self.verts
        for i, vert in enumerate(verts):
            vert = V(vert)
            prev_vert = V(verts[i - 1])
            next_vert = V(verts[(i + 1) % len(verts)])

            to_prev = prev_vert - vert
            to_next = next_vert - vert

            # make prev and next vert a set distance away from the current vert
            # in effect, this controls the size of the smoothing
            prev_vert = to_prev.normalized() * min(radius, to_prev.length / radius) + vert
            next_vert = to_next.normalized() * min(radius, to_next.length / radius) + vert

            # Use fewer vertices on angles that need it less
            try:
                angle = to_prev.angle(to_next)
            except ValueError:
                # This happens very rarely when there is a zero length vector
                print("zero length")
                continue
            res = max(int((pi - angle) * 6), 2)

            # interpolate points
            points = interpolate_bezier(prev_vert, vert, vert, next_vert, res)
            bevelled.extend(points)

        return Polygon(bevelled)
        # self.verts = bevelled

    def __str__(self):
        return f"Polygon({self.verts})"

    def __repr__(self):
        return self.__str__()


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


def vec_mean(vectors: list[V]) -> V:
    """Elementwise mean for a list of vectors"""
    return V((mean(v.x for v in vectors), mean(v.y for v in vectors)))


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


def get_alt_node_tree_name(node_tree) -> str:
    """Get's the name of the parent data block for this node tree
    Only necessary if the tree is attached to a material or scene (shading or compositing)"""
    # "bpy.data.materials['Material'].node_tree"
    # returns 'Material'
    # Not a good way to do it, but I can't find a better one :(
    return repr(node_tree.id_data).split("'")[1]


def view_to_region(context: Context, coords: V, as_vector=True) -> V:
    """Convert 2d editor to screen space coordinates"""
    return V(context.area.regions[3].view2d.view_to_region(coords[0], coords[1], clip=False))
    coords = context.area.regions[3].view2d.view_to_region(coords[0], coords[1], clip=False)
    return V(coords) if as_vector else coords


def region_to_view(context: Context, coords: V, as_vector=True) -> V:
    """Convert screen space to 2d editor coordinates"""
    return V(context.area.regions[3].view2d.region_to_view(coords[0], coords[1]))
    coords = context.area.regions[3].view2d.region_to_view(coords[0], coords[1
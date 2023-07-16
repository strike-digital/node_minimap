import bpy
from mathutils import Vector as V
from ..shared.functions import get_area, get_prefs
from .minimap_functions import get_shader_cache
from .draw_handlers import draw_callback_px, handler_create
from .shader_cache import ShaderCache

handlers = []


# Data class for storing event info
class CustomEvent():

    def __init__(self, event: bpy.types.Event):
        self.type = event.type
        self.value = event.value


class MINIMAP_OT_InitDrawOperators(bpy.types.Operator):
    """Initialize an operator for every visible node tree area"""
    bl_idname = "node.enable_minimap"
    bl_label = "Show minimap"
    bl_description = "Show a minimap of this node tree"

    def invoke(self, context, event):
        prefs = get_prefs(context)
        if prefs.is_enabled:
            prefs.is_enabled = False
            return {'CANCELLED'}

        context.window_manager.minimap_cache.shader_cache = ShaderCache()

        handler = bpy.types.SpaceNodeEditor.draw_handler_add(handler_create, (self, context), 'WINDOW', 'POST_PIXEL')
        self.handler = handler
        global handlers
        handlers.append(handler)
        self.areas = []

        context.window_manager.modal_handler_add(self)
        prefs.is_enabled = True
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        prefs = get_prefs(context)
        if not prefs.is_enabled:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')
            handlers.remove(self.handler)
            prefs = get_prefs(context)
            prefs.is_enabled = False
            return {'CANCELLED'}
        return {'PASS_THROUGH'}


class MINIMAP_OT_DrawAreaMinimap(bpy.types.Operator):
    """Draw a minimap in the corner of the given area"""
    bl_idname = "node.draw_area_minimap"
    bl_label = "Draw a minimap in the corner of the given area"
    bl_options = set()

    area: bpy.props.StringProperty()

    idx: bpy.props.IntProperty()

    def cancel(self, context):
        handlers.remove(self.handler)
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')

    def modal(self, context, event: bpy.types.Event):

        prefs = get_prefs(context)
        area = get_area(self, context)
        if event.type in {'ESC'} or not prefs.is_enabled:
            context.window.cursor_modal_restore()
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')
            handlers.remove(self.handler)
            area.tag_redraw()
            prefs.is_enabled = False
            return {'CANCELLED'}

        if not area:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')
            handlers.remove(self.handler)
            return {'CANCELLED'}

        try:
            area.tag_redraw()
        except AttributeError:
            pass

        if event.type == 'MOUSEMOVE':
            # save the position relative to the area and relative to the window
            self.prev_mouse_pos = self.mouse_pos
            self.mouse_pos = V((event.mouse_region_x - area.x, event.mouse_region_y - area.y))
            self.mouse_pos_abs = V((event.mouse_region_x, event.mouse_region_y))

        on_minimap = False
        if self.map_area:
            on_minimap = self.map_area.isinside(self.mouse_pos_abs)

        self.prev_is_pannings.insert(0, self.is_panning)
        # 7 seems to be the number of events that occur between clicking down and then releasing
        if len(self.prev_is_pannings) > 7:
            del self.prev_is_pannings[-1]

        if event.type == "LEFTMOUSE":

            # The default operator context doesn't update with the mouse moving, so construct it manually
            # If the minimap is clicked center the view
            # I tried for ages to get dragging the minimap to move the view working,
            # but I couldn't figure out how to move the view predictably without using an operator,
            # If you know how please tell me :)
            if on_minimap and event.value != "RELEASE":
                # Check for a double click by seeing if there is another mouse click in the most recent events
                if event.type in self.prev_event_types:
                    with context.temp_override(area=area, space=area.spaces[0], region=area.regions[3]):
                        bpy.ops.node.view_all()
                context.window.cursor_modal_set("SCROLL_XY")
                self.is_panning = True

            try:
                area_cache = get_shader_cache(context).areas[str(area)]
            except KeyError:
                return {'PASS_THROUGH'}

            # Zoom to node only if single click and not panning
            # To get whether it is a single click we need to look at the past events to see
            # whether is_panning was True then.
            # This can be slow on heavy node trees as setting which nodes are selected seems to update the depsgraph...
            # If anyone knows a way to stop this, it would be greatly appreciated
            if prefs.zoom_to_nodes:
                if on_minimap and (self.prev_is_pannings[-1] is not True and "PRESS" in self.prev_event_values):
                    for node_cache in area_cache.all_nodes:
                        if not node_cache.parent and node_cache.node_rect.isinside(self.mouse_pos_abs):
                            node = node_cache.node
                            node.id_data.nodes.active = node
                            for n in node.id_data.nodes:
                                n.select = False
                            node.select = True
                            with context.temp_override(area=area, space=area.spaces[0], region=area.regions[3]):
                                bpy.ops.node.view_selected("EXEC_DEFAULT")
                            break

            if event.value == "RELEASE":
                context.window.cursor_modal_restore()
                self.is_panning = False

        if on_minimap:
            self.prev_events.insert(0, CustomEvent(event))
            if len(self.prev_events) > 4:
                del self.prev_events[-1]

        if self.is_panning:
            delta = self.mouse_pos - self.prev_mouse_pos
            multiplier = 1 + (1 - prefs.size)
            delta *= multiplier * (self.map_area.size.x / self.view_area.size.x)
            with context.temp_override(area=area, space=area.spaces[0], region=area.regions[3]):
                bpy.ops.view2d.pan(deltax=int(delta.x), deltay=int(delta.y))
            return {'RUNNING_MODAL'}
        else:
            if on_minimap:
                context.window.cursor_modal_set("SCROLL_XY")
                if event.type == 'MOUSEMOVE':
                    return {'RUNNING_MODAL'}
            else:
                context.window.cursor_modal_restore()

        return {'PASS_THROUGH'}

    @property
    def prev_event_types(self):
        return [event.type for event in self.prev_events]

    @property
    def prev_event_values(self):
        return [event.value for event in self.prev_events]

    def invoke(self, context, event):
        if context.area.type != 'NODE_EDITOR':
            self.report({'WARNING'}, "Node editor not found, cannot run operator")
            return {'CANCELLED'}

        # the arguments we pass the the callback
        args = (self, context)
        # Add the region OpenGL drawing callback
        # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
        handler = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        self.handler = handler
        global handlers
        handlers.append(handler)

        self.map_area = None
        self.prev_mouse_pos = V((0, 0))
        self.mouse_pos = V((0, 0))
        self.mouse_pos_abs = V((0, 0))
        self.is_panning = False
        self.prev_events = []
        self.prev_is_pannings = []
        self.times = set()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def unregister():
    # Removes handlers left over if the operator is not stopped before reloading the addon
    global handlers
    for handler in handlers:
        try:
            bpy.types.SpaceNodeEditor.draw_handler_remove(handler, 'WINDOW')
        except ValueError:
            pass
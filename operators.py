import bpy
from mathutils import Vector as V
from .functions import get_area, get_prefs
from .draw_handlers import draw_callback_px, handler_create
from .shader_cache import ShaderCache

handlers = []


class MINIMAP_OT_InitDrawOperators(bpy.types.Operator):
    """Initialize an operator for every visible node tree area"""
    bl_idname = "node.enable_minimap"
    bl_label = "Show minimap"
    bl_description = "Show a minimap of this node tree"

    def invoke(self, context, event):
        prefs = get_prefs(context)
        if context.area.type != 'NODE_EDITOR':
            self.report({'WARNING'}, "Node editor not found, cannot run operator")
            return {'CANCELLED'}
        if prefs.is_enabled:
            # Need to find a way to disable it from an operator once it's running
            # Curently only way to stop it is to press escape
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


class ModalDrawOperator(bpy.types.Operator):
    """Draw a minimap in the corner of the given area"""
    bl_idname = "node.draw_area_minimap"
    bl_label = "Draw a minimap in the corner of the given area"

    area: bpy.props.StringProperty()

    idx: bpy.props.IntProperty()

    def cancel(self, context):
        handlers.remove(self.handler)
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')

    def modal(self, context, event: bpy.types.Event):
        area = get_area(self, context)

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
            self.mouse_pos = V((event.mouse_region_x - area.x, event.mouse_region_y - area.y))
            self.mouse_pos_abs = V((event.mouse_region_x, event.mouse_region_y))

        prefs = get_prefs(context)
        if event.type == "LEFTMOUSE":
            # If the minimap is clicked center the view
            # I tried for ages to get dragging the minimap to move the view working,
            # but I couldn't figure out how to move the view predictably without using an operator,
            # If you know how please tell me :)
            if self.map_area:
                on_minimap = self.map_area.isinside(self.mouse_pos_abs)
                # print(self.map_area, self.mouse_pos, on_minimap)
                if on_minimap and event.value != "RELEASE":
                    # The default operator context doesn't update with the mouse moving, so construct it manually
                    override = bpy.context.copy()
                    override["area"] = area
                    override["space"] = area.spaces[0]
                    override["region"] = area.regions[3]
                    bpy.ops.node.view_all((override))

        elif event.type in {'ESC'} or not prefs.is_enabled:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handler, 'WINDOW')
            handlers.remove(self.handler)
            area.tag_redraw()
            prefs.is_enabled = False
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

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

        self.mouse_pos = V((0, 0))
        self.mouse_pos_abs = V((0, 0))

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
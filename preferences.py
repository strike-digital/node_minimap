import bpy
from .functions import get_prefs


class MinimapAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    size: bpy.props.IntProperty(default=300, min=0)

    max_size: bpy.props.FloatProperty(default=1, min=0)

    offset: bpy.props.IntVectorProperty(default=(20, 20), size=2)

    is_enabled: bpy.props.BoolProperty()

    def draw(self, context):
        layout = self.layout
        layout: bpy.types.UILayout
        prefs = get_prefs(context)

        layout.operator("node.enable_minimap", depress=prefs.is_enabled)
        layout.prop(prefs, "size")
        layout.prop(prefs, "max_size")
        layout.prop(prefs, "offset")
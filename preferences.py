import bpy
from .functions import get_prefs, get_shader_cache


class MinimapAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def update_minimap(self, context):
        shader_cache = get_shader_cache(context)
        if not shader_cache:
            return
        for area_cache in shader_cache.areas.values():
            area_cache.tag_update = True

    size: bpy.props.IntProperty(default=300, min=0, update=update_minimap)

    max_size: bpy.props.FloatProperty(default=1, min=0, update=update_minimap)

    offset: bpy.props.IntVectorProperty(default=(20, 20), size=2, update=update_minimap)

    only_top_level: bpy.props.BoolProperty(update=update_minimap)
    
    show_non_full_frames: bpy.props.BoolProperty(update=update_minimap)

    is_enabled: bpy.props.BoolProperty()

    def draw(self, context):
        layout = self.layout
        layout: bpy.types.UILayout
        prefs = get_prefs(context)

        layout.operator("node.enable_minimap", depress=prefs.is_enabled)
        layout.prop(prefs, "size")
        layout.prop(prefs, "max_size")
        layout.prop(prefs, "offset")
        layout.prop(prefs, "only_top_level")
        layout.prop(prefs, "show_non_full_frames")
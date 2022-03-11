import bpy
from .functions import get_prefs
from .preferences import MinimapAddonPrefs
from .icons import icon_collections

# We need two different panels because defining


class MINIMAP_PT_settings_panel(bpy.types.Panel):
    """Shows the minimap settings in the header"""
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Minimap"

    @classmethod
    def poll(cls, context):
        return context.space_data.node_tree

    draw = MinimapAddonPrefs.draw

    def draw_header(self, context):
        if context.region.type == "HEADER":
            return
        layout = self.layout
        icons = icon_collections["icons"]
        prefs = get_prefs(context)
        layout.operator(
            "node.enable_minimap",
            text="",
            emboss=False,
            depress=prefs.is_enabled,
            icon_value=icons["minimap.png"].icon_id,
        )


def draw_header_button(self, context):
    if not context.space_data.node_tree:
        return
    icons = icon_collections["icons"]
    icon = icons["minimap.png"]

    layout = self.layout
    layout: bpy.types.UILayout
    row = layout.row(align=True)
    prefs = get_prefs(context)
    row.operator("node.enable_minimap", text="", depress=prefs.is_enabled, icon_value=icon.icon_id)
    row.popover("MINIMAP_PT_settings_panel", text="")


# Add a button to the header
def register():
    bpy.types.NODE_HT_header.append(draw_header_button)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_header_button)

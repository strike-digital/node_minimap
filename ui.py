import bpy
from .preferences import MinimapAddonPrefs


class MINIMAP_PT_settings_panel(bpy.types.Panel):
    """Shows the minimap settings"""
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "HEADER"
    bl_label = "Minimap"

    def draw(self, context):
        # draw the preferences
        MinimapAddonPrefs.draw(self, context)


def draw_header_button(self, context):
    layout = self.layout
    layout: bpy.types.UILayout
    layout.popover("MINIMAP_PT_settings_panel")


# Add a button to the header
def register():
    bpy.types.NODE_HT_header.append(draw_header_button)


def unregister():
    bpy.types.NODE_HT_header.remove(draw_header_button)
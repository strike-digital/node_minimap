import bpy
from .functions import get_minimap_cache, get_prefs, get_shader_cache


def draw_section(layout: bpy.types.UILayout, title: str):
    main_col = layout.column(align=True)
    box = main_col.box()
    col = box.column(align=True)
    col.scale_y = 0.85
    row = col.row(align=True)
    box = main_col.box()
    row.alignment = "CENTER"
    row.label(text=title)
    col = box.column()
    return col


def draw_inline_prop(layout: bpy.types.UILayout,
                     data,
                     data_name,
                     text="",
                     prop_text="",
                     invert=False,
                     factor=0.48,
                     alignment="RIGHT"):
    """Draw a property with the label to the left of the value"""
    row = layout.row()
    split = row.split(factor=factor, align=True)
    split.use_property_split = False
    left = split.row(align=True)
    left.alignment = alignment
    if not text:
        text = data.bl_rna.properties[data_name].name
    left.label(text=text)
    col = split.column(align=True)
    col.prop(data, data_name, text=prop_text, invert_checkbox=invert)
    return col


class MinimapAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def update_minimap(self, context):
        shader_cache = get_shader_cache(context)
        if not shader_cache:
            return
        for area_cache in shader_cache.areas.values():
            area_cache.tag_update = True

    theme = bpy.context.preferences.themes[0].node_editor

    # size: bpy.props.IntProperty(default=300, min=0, update=update_minimap)
    size: bpy.props.FloatProperty(
        name="Size",
        description="The factor of the width of the area to take up",
        default=0.2,
        min=0,
        max=1,
        update=update_minimap,
        subtype="FACTOR",
    )

    max_size: bpy.props.IntProperty(
        name="Max size",
        description="The maximum size in pixels that the minimap can be",
        default=1000,
        min=0,
        update=update_minimap,
        subtype="PIXEL",
    )

    min_size: bpy.props.IntProperty(
        name="Min size",
        description="The minimum size in pixels that the minimap can be",
        default=200,
        min=0,
        update=update_minimap,
        subtype="PIXEL",
    )

    offset: bpy.props.IntVectorProperty(
        name="Offset",
        description="The number of pixels to offset the minimap from the corner",
        default=(20, 20),
        size=2,
        update=update_minimap,
        subtype="COORDINATES",
    )

    only_top_level: bpy.props.BoolProperty(
        name="Only top level nodes",
        description="Only draw nodes that arent in a frame",
        update=update_minimap,
    )

    show_non_frames: bpy.props.BoolProperty(
        name="Show non frames",
        description="Whether to show non frame nodes",
        default=True,
        update=update_minimap,
    )

    show_non_full_frames: bpy.props.BoolProperty(
        name="Show non full frames",
        description="""Whether to show frames that don't contain any nodes. There currently isn't a good way to get\
the location of these nodes from the python api, so if this is on, they may appear in the wrong position""",
        default=True,
        update=update_minimap,
    )

    outline_color: bpy.props.FloatVectorProperty(
        name="Outline color",
        description="The color of the minimap outline",
        size=4,
        subtype="COLOR",
        default=(0.45, 0.45, 0.45, 1),
        min=0,
        max=1,
        update=update_minimap,
    )

    background_color: bpy.props.FloatVectorProperty(
        name="Background color",
        description="The color of the minimap background",
        size=4,
        subtype="COLOR",
        default=list(theme.grid) + [0.8],
        min=0,
        max=1,
        update=update_minimap,
    )

    line_width: bpy.props.FloatProperty(
        name="Line width",
        description="The width of outlines of the nodes",
        default=1,
        min=0,
        update=update_minimap,
    )

    use_node_colors: bpy.props.BoolProperty(
        name="Use node colors",
        description="Whether to draw nodes with the colors of their categories",
        default=True,
        update=update_minimap,
    )

    node_color: bpy.props.FloatVectorProperty(
        name="Node color",
        description="The color of the nodes when use node colors is false",
        size=4,
        subtype="COLOR",
        # default=(0.45, 0.45, 0.45, 1),
        default=list(theme.node_backdrop),
        min=0,
        max=1,
        update=update_minimap,
    )

    is_enabled: bpy.props.BoolProperty()

    def draw(self, context):
        layout = self.layout
        layout: bpy.types.UILayout
        prefs = get_prefs(context)

        if not issubclass(self.__class__, bpy.types.AddonPreferences):
            icon = "CHECKMARK" if prefs.is_enabled else "BLANK1"
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.operator("node.enable_minimap", depress=prefs.is_enabled, icon=icon, text="Show minimap      ")
            layout.separator()

        col = draw_section(layout, title="Shape")
        factor = 0.3
        draw_inline_prop(col, prefs, "size", "Scale", factor=factor)
        sub = draw_inline_prop(col, prefs, "min_size", "Size", prop_text="Min", factor=factor)
        sub.prop(prefs, "max_size", text="Max")
        draw_inline_prop(col, prefs, "offset", "Offset", factor=factor)
        layout.separator()

        col = draw_section(layout, title="Look")
        draw_inline_prop(col, prefs, "line_width")
        draw_inline_prop(col, prefs, "outline_color")
        draw_inline_prop(col, prefs, "background_color", "Background")
        draw_inline_prop(col, prefs, "use_node_colors", "One node color", invert=True)
        if not prefs.use_node_colors:
            draw_inline_prop(col, prefs, "node_color")

        layout.separator()
        factor = 0.9
        col = draw_section(layout, title="Performance")
        draw_inline_prop(col, prefs, "only_top_level", factor=factor, alignment="LEFT")
        draw_inline_prop(col, prefs, "show_non_frames", factor=factor, alignment="LEFT")
        draw_inline_prop(col, prefs, "show_non_full_frames", factor=factor, alignment="LEFT")


@bpy.app.handlers.persistent
def on_load(_0, _1):
    minimap_cache = get_minimap_cache(bpy.context)
    minimap_cache.shader_cache = None


def register():
    bpy.app.handlers.load_post.append(on_load)


def unregister():
    bpy.app.handlers.load_post.remove(on_load)
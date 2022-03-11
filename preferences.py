import bpy
from . import operators
from .functions import get_minimap_cache, get_prefs, get_shader_cache
from .icons import icon_collections


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
    main_col.separator()
    return col


def draw_inline_prop(
    layout: bpy.types.UILayout,
    data,
    data_name,
    text="",
    prop_text="",
    invert=False,
    factor=0.48,
    alignment="RIGHT",
):
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

    def update_minimap_and_color(self, context):
        shader_cache = get_shader_cache(context)
        if not shader_cache:
            return
        for area_cache in shader_cache.areas.values():
            area_cache.tag_update = True
            for node in area_cache.all_nodes:
                node.update_color(context, node.node)

    # Make sure icons have been registered
    try:
        icons = icon_collections["icons"]
    except KeyError:
        from . import icons
        icons.register()
        icons = icon_collections["icons"]

    anchor_corner: bpy.props.EnumProperty(
        items=(
            (
                "BL",
                "Bottom-left",
                "Anchor the minimap to the bottom left hand side of the area",
                icons["anchor bl.png"].icon_id,
                0,
            ),
            (
                "BR",
                "Bottom-right",
                "Anchor the minimap to the bottom right hand side of the area",
                icons["anchor br.png"].icon_id,
                1,
            ),
            (
                "TL",
                "Top-left",
                "Anchor the minimap to the top left hand side of the area",
                icons["anchor tl.png"].icon_id,
                2,
            ),
            (
                "TR",
                "Top-right",
                "Anchor the minimap to the top right hand side of the area",
                icons["anchor tr.png"].icon_id,
                3,
            ),
        ),
        name="Corner",
        description="The corner to anchor the minimap to",
        default="BR",
        update=update_minimap,
    )

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

    zoom_to_nodes: bpy.props.BoolProperty(
        name="Zoom to nodes (can be slow)",
        description="""When a node is clicked in the minimap, focus on that node. Be aware that this causes a scene \
update, so it's best to turn this off when using node trees that take a long time to evaluate""",
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

    view_outline_color: bpy.props.FloatVectorProperty(
        name="View outline color",
        description="The color of the view box outline",
        size=4,
        subtype="COLOR",
        default=(0.8, 0.8, 0.8, 1),
        min=0,
        max=1,
        update=update_minimap,
    )

    theme = bpy.context.preferences.themes[0].node_editor
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

    node_transparency: bpy.props.FloatProperty(
        name="Node Alpha",
        description="How transparently the nodes will be drawn",
        default=1,
        min=0,
        max=1,
        subtype="FACTOR",
        update=update_minimap_and_color,
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

        # Grid flow allows the UI to adapt to areas of different widths.
        layout = layout.grid_flow(row_major=True, even_columns=True,)

        factor = 0.9
        col = draw_section(layout, title="Performance")
        draw_inline_prop(col, prefs, "only_top_level", factor=factor, alignment="LEFT")
        draw_inline_prop(col, prefs, "show_non_frames", factor=factor, alignment="LEFT")
        draw_inline_prop(col, prefs, "show_non_full_frames", factor=factor, alignment="LEFT")
        if context.area.type == "NODE_EDITOR" and len(context.space_data.node_tree.nodes) > 100 and prefs.zoom_to_nodes:
            row = col.row(align=True)
            box = col.box().column(align=True)
            row.alert = True
            box.label(text="This node tree has more than 100")
            box.label(text="nodes, evaluation may be slow")
        else:
            row = col.row(align=True)
        draw_inline_prop(row, prefs, "zoom_to_nodes", factor=factor, alignment="LEFT")

        col = draw_section(layout, title="Shape")
        factor = 0.3
        draw_inline_prop(col, prefs, "anchor_corner", factor=factor)
        draw_inline_prop(col, prefs, "size", "Scale", factor=factor)
        sub = draw_inline_prop(col, prefs, "min_size", "Size", prop_text="Min", factor=factor)
        sub.prop(prefs, "max_size", text="Max")
        draw_inline_prop(col, prefs, "offset", "Offset", factor=factor)

        col = draw_section(layout, title="Look")
        draw_inline_prop(col, prefs, "line_width")
        draw_inline_prop(col, prefs, "outline_color")
        draw_inline_prop(col, prefs, "view_outline_color")
        draw_inline_prop(col, prefs, "background_color", "Background")
        draw_inline_prop(col, prefs, "node_transparency")
        draw_inline_prop(col, prefs, "use_node_colors", "One node color", invert=True)
        if not prefs.use_node_colors:
            draw_inline_prop(col, prefs, "node_color")

        col = draw_section(layout, title="Controls")
        col.label(text="Click and drag to pan the view")
        col.label(text="Double click to view all")
        if prefs.zoom_to_nodes:
            col.label(text="Click on a node to zoom to it")


@bpy.app.handlers.persistent
def on_load(_0, _1):
    prefs = get_prefs(bpy.context)
    prefs.is_enabled = False
    minimap_cache = get_minimap_cache(bpy.context)
    minimap_cache.shader_cache = None
    operators.unregister()


def register():
    bpy.app.handlers.load_post.append(on_load)


def unregister():
    bpy.app.handlers.load_post.remove(on_load)
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, FloatProperty, IntProperty, IntVectorProperty
from . import operators
from ..shared.functions import get_prefs
from .minimap_functions import get_minimap_cache, get_shader_cache
from ..shared.ui import draw_enabled_button, draw_inline_prop, draw_section
from ..shared.icons import icon_collections


class MinimapAddonPrefs():
    """Node minimap"""

    icon = "minimap.png"

    # Trigger the cache to update when a property is changed
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

    def update_label(self, context):
        return

    def minimap_section_enabled_update(self, context):
        prefs = get_prefs(bpy.context)
        prefs.is_enabled = False
        minimap_cache = get_minimap_cache(bpy.context)
        minimap_cache.shader_cache = None

    icons = icon_collections["icons"]

    minimap_section_enabled: BoolProperty(
        name="Minimap enabled",
        description="Whether to enable the minimap section",
        default=True,
        update=minimap_section_enabled_update,
    )

    # GENERAL
    enable_on_load: BoolProperty(
        name="Enable on load",
        description="Automatically enable the minimap when you load a file",
        default=True,
    )

    only_top_level: BoolProperty(
        name="Only top level nodes",
        description="Only draw nodes that arent in a frame",
        update=update_minimap,
    )

    show_non_frames: BoolProperty(
        name="Show non frames",
        description="Whether to show non frame nodes",
        default=True,
        update=update_minimap,
    )

    zoom_to_nodes: BoolProperty(
        name="Zoom to nodes (can be slow)",
        description="""When a node is clicked in the minimap, focus on that node. Be aware that this causes a scene \
update, so it's best to turn this off when using node trees that take a long time to evaluate""",
        default=True,
        update=update_minimap,
    )

    show_non_full_frames: BoolProperty(
        name="Show non full frames",
        description="""Whether to show frames that don't contain any nodes. There currently isn't a good way to get\
the location of these nodes from the python api, so if this is on, they may appear in the wrong position""",
        default=True,
        update=update_minimap,
    )

    # SHAPE

    anchor_corner: EnumProperty(
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

    size: FloatProperty(
        name="Size",
        description="The factor of the width of the area to take up",
        default=0.2,
        min=0,
        max=1,
        update=update_minimap,
        subtype="FACTOR",
    )

    max_size: IntProperty(
        name="Max size",
        description="The maximum size in pixels that the minimap can be",
        default=250,
        min=0,
        update=update_minimap,
        subtype="PIXEL",
    )

    min_size: IntProperty(
        name="Min size",
        description="The minimum size in pixels that the minimap can be",
        default=200,
        min=0,
        update=update_minimap,
        subtype="PIXEL",
    )

    offset: IntVectorProperty(
        name="Offset",
        description="The number of pixels to offset the minimap from the corner",
        default=(20, 20),
        size=2,
        update=update_minimap,
        subtype="COORDINATES",
    )

    # LOOK

    node_theme = bpy.context.preferences.themes[0].node_editor

    outline_color: FloatVectorProperty(
        name="Outline color",
        description="The color of the minimap outline",
        size=4,
        subtype="COLOR",
        default=(0.45, 0.45, 0.45, 1),
        min=0,
        max=1,
        update=update_minimap,
    )

    view_outline_color: FloatVectorProperty(
        name="View outline color",
        description="The color of the view box outline",
        size=4,
        subtype="COLOR",
        default=(0.8, 0.8, 0.8, 1),
        min=0,
        max=1,
        update=update_minimap,
    )

    background_color: FloatVectorProperty(
        name="Background color",
        description="The color of the minimap background",
        size=4,
        subtype="COLOR",
        default=list(node_theme.grid) + [0.8],
        min=0,
        max=1,
        update=update_minimap,
    )

    node_transparency: FloatProperty(
        name="Node Alpha",
        description="How transparently the nodes will be drawn",
        default=1,
        min=0,
        max=1,
        subtype="FACTOR",
        update=update_minimap_and_color,
    )

    line_width: FloatProperty(
        name="Line width",
        description="The width of outlines of the nodes",
        default=1,
        min=0,
        update=update_minimap,
    )

    use_node_colors: BoolProperty(
        name="Use node colors",
        description="Whether to draw nodes with the colors of their categories",
        default=True,
        update=update_minimap,
    )

    node_color: FloatVectorProperty(
        name="Node color",
        description="The color of the nodes when use node colors is false",
        size=4,
        subtype="COLOR",
        default=list(node_theme.node_backdrop),
        min=0,
        max=1,
        update=update_minimap,
    )

    # TEXT
    text_theme = bpy.context.preferences.themes[0].user_interface.wcol_text

    show_labels: BoolProperty(
        name="Show labels",
        description="Whether to show the labels of frame nodes",
        default=True,
        update=update_label,
    )

    text_color: FloatVectorProperty(
        name="Text color",
        description="The color of the labels show inside frame nodes",
        size=4,
        subtype="COLOR",
        default=list(text_theme.text) + [1],
        min=0,
        max=1,
        update=update_label,
    )

    text_wrap: BoolProperty(
        name="Text wrap",
        description="Whether to split up long labels into multiple lines",
        default=True,
        update=update_label,
    )

    min_frame_size: IntProperty(
        name="Min frame size",
        description="The minimum size of a frame for it's label to be displayed",
        default=20,
        min=0,
        update=update_label,
        subtype="PIXEL",
    )

    # PAGES
    page: EnumProperty(items=(
        ("0", "1", "View page 1"),
        ("1", "2", "View page 2"),
        # ("2", "2", "View page 2"),
    ))

    # INTERNAL

    is_enabled: BoolProperty()

    def draw(self, context):
        layout = self.layout
        layout: bpy.types.UILayout
        is_prefs = issubclass(self.__class__, bpy.types.AddonPreferences)

        if is_prefs:
            layout = draw_enabled_button(layout, self, "minimap_section_enabled")
        prefs = get_prefs(context)  # can't use self because draw function is also used by a panel
        page = int(prefs.page)

        row = layout.row(align=True)
        icons = icon_collections["icons"]
        row.scale_y = 1.5
        icon = "CHECKMARK" if prefs.is_enabled else "BLANK1"
        factor = 0.1
        if not is_prefs:
            row.scale_x = 1.25
            row.operator("node.enable_minimap", depress=prefs.is_enabled, icon=icon, text="Show minimap      ")
            layout.separator(factor=factor)
            icon_value = icons["enable on load.png"].icon_id
            row.prop(prefs, "enable_on_load", text="", icon_value=icon_value, toggle=True)

            grid = layout.grid_flow(row_major=True, even_columns=True)
            box = grid.box()
            row = box.row(align=True)
            row.alignment = "CENTER"
            row.scale_x = 0.75
            row.prop(prefs, "page", expand=True)
            layout.separator(factor=factor)

        # Grid flow allows the UI to adapt to areas of different widths.
        layout = layout.grid_flow(row_major=True, even_columns=True)

        if page == 0 or is_prefs:
            factor = 0.9
            col = draw_section(layout, title="General")
            draw_inline_prop(col, prefs, "enable_on_load", "Auto enable", factor=factor, alignment="LEFT")
            draw_inline_prop(col, prefs, "only_top_level", factor=factor, alignment="LEFT")
            draw_inline_prop(col, prefs, "show_non_frames", factor=factor, alignment="LEFT")
            draw_inline_prop(col, prefs, "show_non_full_frames", factor=factor, alignment="LEFT")
            if context.area.type == "NODE_EDITOR" and len(context.space_data.node_tree.nodes) > 100\
                and prefs.zoom_to_nodes and context.space_data.node_tree.type == "GEOMETRY":
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

        if page == 1 or is_prefs:
            col = draw_section(layout, title="Labels")
            draw_inline_prop(col, prefs, "show_labels")
            if prefs.show_labels:
                draw_inline_prop(col, prefs, "text_wrap")
                draw_inline_prop(col, prefs, "text_color")
                draw_inline_prop(col, prefs, "min_frame_size")

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
    operators.unregister()  # remove handlers

    # Load new minimap if enabled
    if prefs.enable_on_load:
        bpy.ops.node.enable_minimap("INVOKE_DEFAULT")


def register():
    bpy.app.handlers.load_post.append(on_load)


def unregister():
    bpy.app.handlers.load_post.remove(on_load)
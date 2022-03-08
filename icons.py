from pathlib import Path
from bpy.utils import previews

icon_collections = {}


def register():
    # load icons
    icon_path = Path(__file__) / "icons"
    global icon_collections
    pcoll = previews.new()
    for file in list(icon_path.glob("./*.png")):
        pcoll.load(file.name, str(file), "IMAGE")
    icon_collections["icons"] = pcoll


def unregister():
    global icon_collections
    for pcoll in icon_collections.values():
        previews.remove(pcoll)
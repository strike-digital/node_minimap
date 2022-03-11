from pathlib import Path
from bpy.utils import previews

icon_collections = {}


# Add a button to the header
def register():
    global icon_collections
    if icon_collections:
        return

    # load icons
    icon_path = Path(__file__).parent / "icons"
    pcoll = previews.new()
    for file in list(icon_path.glob("*.png")):
        pcoll.load(file.name, str(file), "IMAGE")
    icon_collections["icons"] = pcoll
    global icons


def unregister():

    global icon_collections
    for pcoll in icon_collections.values():
        previews.remove(pcoll)
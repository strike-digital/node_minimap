from pathlib import Path
from bpy.utils import previews

icon_collections = {}
pcolls = []


# Add a button to the header
def register():
    global icon_collections

    # load icons
    icon_path = Path(__file__).parent / "icons"
    pcoll = previews.new()
    for file in list(icon_path.glob("*.png")):
        pcoll.load(file.name, str(file), "IMAGE")
    icon_collections["icons"] = pcoll
    pcolls.append(pcoll)


def unregister():

    global pcolls
    for pcoll in pcolls:
        try:
            previews.remove(pcoll)
        except KeyError:
            pass
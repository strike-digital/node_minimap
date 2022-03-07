# Node Minimap
This is a Blender addon that generates a minimap of the current node tree, allowing for easy navigation and readability

![Minimap demo](https://thumbs.gfycat.com/ColdMinorBoa-size_restricted.gif)


## Warning
This is a very early version, and almost certainly contains many bugs and problems, use at your own risk :)


## Installation
Download this repo as a zip, and install it as a normal Blender addon.

## Usage

![Minimap header](https://i.ibb.co/LJyvk85/image.png)

click the Minimap button in header of the node editor, and then click "Show minimap"

![Header contents](https://i.ibb.co/JtPT0Ks/image.png)

You can then play about with the values that control how the minimap is displayed.

## Limitations
* Currently, clicking the minimap will just center the view to fit all nodes. This is because I haven't been able to find a way to reliably set the view position from python without using an operator. If you know how to do this, please tell me :)
* I haven't implemented any optimisations yet, so on large node trees, it can slow down redraw speeds quite noticably
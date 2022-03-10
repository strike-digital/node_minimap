# Node Minimap
This is a Blender addon that generates a minimap of the current node tree, allowing for easy navigation and readability

![Minimap demo](https://thumbs.gfycat.com/ColdMinorBoa-size_restricted.gif)

## Installation
Download this repo as a zip, and install it as a normal Blender addon.

## Usage

![Minimap header](https://i.ibb.co/hZ4Tpyc/image.png)

click the Minimap button in the header of the node editor, and then click "Show minimap"

![Header contents](https://i.ibb.co/C62vKQd/image.png)

You can then play about with the values that control how the minimap is displayed.

Controls:
* Clicking and dragging on the minimap pans the view
* Double-clicking the minimap centers the view to fit all nodes in the tree
* Clicking on a single node will center on that node.

## Limitations
* If you have an absolutely massive node tree (800 nodes plus), the responsiveness of the viewport will slow down significantly. There are a few options to improve this, but it will still be a bit slow on very large trees. This isn't something most people need to worry about though.


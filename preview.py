"""Show the loaded images preview. 
"""
from . import VoxelGrid

def show_all_sides(images, width, height, depth):
    """Generates a grid showing the input images before any intersections.

    Args:
        images: Images that were loaded through the panel
        width (int): Set width
        height (int): Set height
        depth (int): Set depth

    Returns:
        _type_: _description_
    """
    voxel_grid = VoxelGrid.VoxelGrid(width, height, depth)

    for x in range (width):
        for z in range (height):
            for y in range (depth):

                #front view
                if(y == 0) and 'FRONT' in images:
                    voxel_grid.set_color(x, y, z, images['FRONT'][z, x])
                #back view
                elif(y == depth - 1) and 'BACK' in images:
                    voxel_grid.set_color(x, y, z, images['BACK'][z, width - 1 - x])
                #left view
                elif(x == 0) and 'LEFT' in images:
                    voxel_grid.set_color(x, y, z, images['LEFT'][z, depth - 1 - y])
                #right view
                elif(x == width - 1) and 'RIGHT' in images:
                    voxel_grid.set_color(x, y, z, images['RIGHT'][z, y])
                #top view
                elif(z == height - 1) and 'TOP' in images:
                    voxel_grid.set_color(x, y, z, images['TOP'][y, x])
                #bottom view
                elif(z == 0) and 'BOTTOM' in images:
                    voxel_grid.set_color(x, y, z, images['BOTTOM'][depth - 1 - y, x])

    return voxel_grid

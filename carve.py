"""
This module implements spatial carving using photometric consistency. 
"""
import numpy as np
from . import VoxelGrid

def spatial_carve(images,
                    width,
                    height,
                    depth,
                    merge_technique,
                    concavity_depth,
                    colors_threshold=6,
                    variance_threshold=0.5,
                    hollow_grid=False):
    """Apply spatial carving to generate the grid from the passed images.

    Args:
        images: Images that were loaded through the panel
        width (int): Set width
        height (int): Set height
        depth (int): Set depth
        merge_technique (String): Color merging technique
        concavity_depth (float): Concavity depth multiplier
        colors_threshold (int, optional): Number of colors that need to intersect at a point. 
        Defaults to 6.
        variance_threshold (float, optional): Amount of color variance allowed at a point. 
        Defaults to 0.5.
        hollow_grid (bool, optional): Choice for whether the model should be filled in at 
        non-visible voxel points. Defaults to False.

    Returns:
        The 3D grid of colors representing the model
    """
    voxel_grid = VoxelGrid.VoxelGrid(width, height, depth)
    colors = np.full((width, height, depth, 4), [0, 0, 0, 1], dtype=float)

    for x in range (width):
        for z in range (height):
            for y in range (depth):
                candidates = []
                available_projections = {}

                # front
                if 'FRONT' in images:
                    front_color = images['FRONT'][z, x]
                    if front_color[3] > 0:
                        candidates.append(front_color)
                        available_projections['front'] = front_color

                # back
                if 'BACK' in images:
                    back_color = images['BACK'][z, width - 1 - x]
                    if back_color[3] > 0:
                        candidates.append(back_color)
                        available_projections['back'] = back_color

                # left
                if 'LEFT' in images:
                    left_color = images['LEFT'][z, depth - 1 - y]
                    if left_color[3] > 0:
                        candidates.append(left_color)
                        available_projections['left'] = left_color

                # right
                if 'RIGHT' in images:
                    right_color = images['RIGHT'][z, y]
                    if right_color[3] > 0:
                        candidates.append(right_color)
                        available_projections['right'] = right_color

                # top
                if 'TOP' in images:
                    top_color = images['TOP'][y, x]
                    if top_color[3] > 0:
                        candidates.append(top_color)
                        available_projections['top'] = top_color

                # bottom
                if 'BOTTOM' in images:
                    bottom_color = images['BOTTOM'][depth - 1 - y, x]
                    if bottom_color[3] > 0:
                        candidates.append(bottom_color)
                        available_projections['bottom'] = bottom_color

                if len(candidates) < colors_threshold / 1.0:
                    colors[x, y, z] = [0, 0, 0, 0]
                    continue

                colors_array = np.array([c[:3] for c in candidates])
                variance = np.var(colors_array, axis=0)
                total_variance = np.sum(variance)

                in_concavity_zone = (
                    (x < (width-1) / 2 and x < (width-1) * concavity_depth) or    # Left
                    (x >= (width-1) / 2 and x > (width-1) * (1 - concavity_depth)) or  # Right
                    (y < (depth-1) / 2 and y < (depth-1) * concavity_depth) or    # Front
                    (y >= (depth-1) / 2 and y > (depth-1) * (1 - concavity_depth)) or  # Back
                    (z < (height-1) / 2 and z < (height-1) * concavity_depth) or  # Bottom
                    (z >= (height-1) / 2 and z > (height-1) * (1 - concavity_depth))   # Top
                )

                if total_variance > variance_threshold and in_concavity_zone:
                    colors[x, y, z] = [0, 0, 0, 0]
                    continue

                else:
                    # finally, assign color based on merge technique
                    final_color = []

                    if merge_technique == "MAJORITY_VOTE":
                        colors_np = np.array([c[:3] for c in candidates])
                        unique_colors, counts = np.unique(colors_np, axis=0, return_counts=True)
                        max_index = np.argmax(counts)
                        final_color = list(unique_colors[max_index]) + [1.0] 

                    else:
                        distances = {
                            'front': y,
                            'back': depth - 1 - y,
                            'left': x,
                            'right': width - 1 - x,
                            'top': height - 1 - z,
                            'bottom': z
                        }
                        closest_projection = min(
                            available_projections.keys(),
                            key=lambda k: distances[k]
                        )
                        final_color = available_projections[closest_projection]

                    colors[x, y, z] = final_color

    if hollow_grid:
        hollow_grid = voxel_grid.hollow_out_grid(colors)
        voxel_grid.colors = hollow_grid

    else:
        voxel_grid.colors = colors

    return voxel_grid

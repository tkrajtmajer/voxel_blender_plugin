"""
This module implements the silhouette intersection algorithm. 
"""
import numpy as np
from . import VoxelGrid, depth_map

def project_min_dist(images,
                        width,
                        height,
                        depth,
                        merge_technique,
                        threshold = 1.0,
                        use_depth_mapping=False,
                        intensity_threshold=0.3,
                        concavity_depth=0.5,
                        factor = 1,
                        min_region_size=5,
                        keep_concave_regions=True,
                        hollow_grid=False):
    """Apply silhouette intersection to generate the grid from the passed images.

    Args:
        images: Images that were loaded through the panel
        width (int): Set width
        height (int): Set height
        depth (int): Set depth
        merge_technique (String): Color merging technique
        threshold (float, optional): Number of colors that need to intersect at a point. 
        Defaults to 1.0.
        use_depth_mapping (bool, optional): Choice of whether to apply the hybrid algorithm. 
        Defaults to False.

        Depth map-specific parameteres: 
            intensity_threshold (float): Intensity cutoff threshold
            concavity_depth (float): Concavity depth multiplier
            factor (float): Factor multipler
            min_region_size (float): Minimum size of concave regions
            keep_concave_regions (bool): Choice of whether voxels in concave regions should 
            be in the final model

        hollow_grid (bool, optional): Choice for whether the model should be filled in at 
        non-visible voxel points. Defaults to False.

    Returns:
        The 3D grid of colors representing the model
    """
    voxel_grid = VoxelGrid.VoxelGrid(width, height, depth)
    colors = np.full((width, height, depth, 4), [0, 0, 0, 0], dtype=float)
    depth_maps = {}

    if use_depth_mapping:
        for view, image in images.items():
            other_images = [(v, img) for v, img in images.items() if v != view]

            curr_depth_map = depth_map.calculate_depth(view,
                                                        image,
                                                        other_images,
                                                        width,
                                                        height,
                                                        depth)

            final_depth_map = depth_map.estimate_using_gradients(view,
                                                                    image,
                                                                    curr_depth_map,
                                                                    width,
                                                                    height,
                                                                    depth,
                                                                    intensity_threshold,
                                                                    concavity_depth,
                                                                    factor,
                                                                    min_region_size,
                                                                    keep_concave_regions)

            depth_maps[view] = final_depth_map

    for x in range (width):
        for y in range (depth):
            for z in range (height):
                candidates = []
                available_projections = {}

                # front
                if 'FRONT' in images:
                    front_color = images['FRONT'][z, x]
                    if front_color[3] > 0:
                        if use_depth_mapping:
                            if(y >= depth_maps['FRONT'][z,x]):
                                candidates.append(front_color)
                                available_projections['front'] = front_color
                        else:
                            candidates.append(front_color)
                            available_projections['front'] = front_color

                # back
                if 'BACK' in images:
                    back_color = images['BACK'][z, width - 1 - x]
                    if back_color[3] > 0:
                        if use_depth_mapping:
                            if(y <= depth_maps['BACK'][z,width-1-x]):
                                candidates.append(back_color)
                                available_projections['back'] = back_color
                        else:
                            candidates.append(back_color)
                            available_projections['back'] = back_color

                # left
                if 'LEFT' in images:
                    left_color = images['LEFT'][z, depth - 1 - y]
                    if left_color[3] > 0:
                        if use_depth_mapping:
                            if(x >= depth_maps['LEFT'][z,depth-1-y]):
                                candidates.append(left_color)
                                available_projections['left'] = left_color
                        else:
                            candidates.append(left_color)
                            available_projections['left'] = left_color

                # right
                if 'RIGHT' in images:
                    right_color = images['RIGHT'][z, y]
                    if right_color[3] > 0:
                        if use_depth_mapping:
                            if(x <= depth_maps['RIGHT'][z,y]):
                                candidates.append(right_color)
                                available_projections['right'] = right_color
                        else:
                            candidates.append(right_color)
                            available_projections['right'] = right_color

                # top
                if 'TOP' in images:
                    top_color = images['TOP'][y, x]
                    if top_color[3] > 0:
                        if use_depth_mapping:
                            if(z <= depth_maps['TOP'][y,x]):
                                candidates.append(top_color)
                                available_projections['top'] = top_color
                        else:
                            candidates.append(top_color)
                            available_projections['top'] = top_color

                # bottom
                if 'BOTTOM' in images:
                    bottom_color = images['BOTTOM'][depth - 1 - y, x]
                    if bottom_color[3] > 0:
                        if use_depth_mapping:
                            if(z >= depth_maps['BOTTOM'][depth-1-y,x]):
                                candidates.append(bottom_color)
                                available_projections['top'] = bottom_color
                        else:
                            candidates.append(bottom_color)
                            available_projections['top'] = bottom_color

                if len(candidates) >= (threshold * len(images)) / 1.0:
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

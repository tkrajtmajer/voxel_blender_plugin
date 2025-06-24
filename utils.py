"""
Utility functions for displaying the grid in the Blender editor.
"""
import bpy
from bpy.props import (StringProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty, FloatProperty, BoolProperty)
from bpy.types import (Panel, Operator, PropertyGroup)
import numpy as np
from . import (preview,
            silhouette_intersect,
            carve,
            depth_map,
            generate_mesh,
            VoxelGrid)

def create_grid(context):
    """
    Create grid using User settings.
    """
    settings = context.scene.voxel_generator_settings

    grid = VoxelGrid.VoxelGrid(0, 0, 0)

    images_dict = {}
    for img in settings.images:
        if not img.image_path:
            continue

        img_name = bpy.path.basename(img.image_path)
        if img_name in bpy.data.images:
            bpy.data.images.remove(bpy.data.images[img_name])

        image = bpy.data.images.load(img.image_path)
        width, height = image.size
        pixels_np = np.array(image.pixels[:]).reshape((height, width, 4))
        pixels_np = np.round(pixels_np, 3)
        images_dict[img.orientation] = pixels_np

    if settings.selected_algorithm == 'IMAGE_PREVIEW':
        grid = preview.show_all_sides(images_dict,
                                        settings.width,
                                        settings.height,
                                        settings.depth)

    elif settings.selected_algorithm == 'SILHOUETTE_INTERSECT':
        grid = silhouette_intersect.project_min_dist(images_dict,
                                                        settings.width,
                                                        settings.height,
                                                        settings.depth,
                                                        settings.color_merging,
                                                        settings.threshold,
                                                        settings.use_depth_mapping,
                                                        settings.intensity_threshold,
                                                        settings.concavity_depth,
                                                        settings.depth_factor,
                                                        settings.min_region_size,
                                                        settings.keep_concave_regions,
                                                        settings.hollow_grid)

    elif settings.selected_algorithm == 'SPATIAL_CARVING':
        grid = carve.spatial_carve(images_dict,
                                    settings.width,
                                    settings.height,
                                    settings.depth,
                                    settings.color_merging,
                                    settings.concavity_depth,
                                    settings.color_threshold_carve,
                                    settings.dist_threshold_carve,
                                    settings.hollow_grid)
    
    elif settings.selected_algorithm == 'DEPTH_ESTIMATE':
        grid = depth_map.generate_final_grid(images_dict,
                                                settings.width,
                                                settings.height,
                                                settings.depth,
                                                settings.intensity_threshold,
                                                settings.concavity_depth,
                                                settings.depth_factor,
                                                settings.min_region_size,
                                                settings.keep_concave_regions)

    return grid

def generate_voxel_grid(context):
    """
    Generate Voxel object and mesh in the viewport.
    """
    settings = context.scene.voxel_generator_settings

    grid = create_grid(context)

    obj = generate_mesh.generate_mesh_from_grid(grid.get_colors(),
                                                voxel_size = settings.voxel_size,
                                                remove_gamma_correction=settings.remove_gamma_correction)

    settings.gen_object = obj

def update_grid(self, context):
    """
    Update grid. Triggered when values are changed in the editor.
    """
    generate_voxel_grid(context)

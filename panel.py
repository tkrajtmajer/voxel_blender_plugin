"""
This module implements the Main Menu panel.
"""

import bpy
from bpy.props import (StringProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty, FloatProperty, BoolProperty)
from bpy.types import (Panel, Operator, PropertyGroup)
from . import presets, utils

class ImageMenuItems(PropertyGroup):
    """
    Collection for Image menu settings.
    """
    orientation: EnumProperty(
        name="Orientation",
        items=presets.orientations,
        default='FRONT'
    ) # type: ignore

    image_path: StringProperty(
        name="Image Path",
        subtype='FILE_PATH',
        default='/home/tica/Downloads/assets/cup/front.png'
    ) # type: ignore

class PanelSettings(PropertyGroup):
    """
    All panel settings.
    """
    images: CollectionProperty(type=ImageMenuItems) # type: ignore

    selected_algorithm: EnumProperty(
        name="Method",
        items=presets.algorithms
    ) # type: ignore

    width: IntProperty(
        name="Width",
        min = 1,
        max = 256
    ) # type: ignore

    height: IntProperty(
        name="Height",
        min = 1,
        max = 256
    ) # type: ignore

    depth: IntProperty(
        name="Depth",
        min = 1,
        max = 256
    ) # type: ignore

    voxel_size: FloatProperty(
        name="Voxel Size",
        default = 1.0,
        min = 0.1
    ) # type: ignore

    # silhouette intersect
    threshold: FloatProperty(
        name="Threshold",
        default=1.0,
        min=0.0,
        max=1.0,
        update=utils.update_grid
    ) # type: ignore

    use_depth_mapping: BoolProperty(
        name="Use Depth Mapping",
        default=False,
        update=utils.update_grid
    )

    color_merging: EnumProperty(
        name="Color Merging",
        items=presets.merging_techniques,
        default="NEAREST_PROJ",
        update=utils.update_grid
    ) # type: ignore

    color_threshold_carve: IntProperty(
        name="Color Threshold",
        default=6,
        min=1,
        max=6,
        update=utils.update_grid
    ) # type: ignore

    dist_threshold_carve: FloatProperty(
        name="Variance Threshold",
        default=0.5,
        min=0,
        max=1,
        update=utils.update_grid
    ) # type: ignore

    concavity_depth: FloatProperty(
        name="Concavity Depth Threshold",
        default=0.5,
        min=0,
        max=1,
        update=utils.update_grid
    ) # type: ignore

    # depth maps
    intensity_threshold: FloatProperty(
        name="Intensity Threshold",
        default=1.0,
        min=0.0,
        max=1.0,
        update=utils.update_grid
    ) # type: ignore

    depth_factor: FloatProperty(
        name="Depth Factor",
        default=1,
        min=0,
        update=utils.update_grid
    ) # type: ignore

    min_region_size: FloatProperty(
        name="Minimum Region Size",
        default=5,
        min=0,
        update=utils.update_grid
    ) # type: ignore

    keep_concave_regions: BoolProperty(
        name="Keep Concave Regions",
        description="Toggle concavity regions on/off",
        default=True,
        update=utils.update_grid
    )

    active_image_index: IntProperty(default=0) # type: ignore

    gen_object: bpy.props.PointerProperty(
        name="Generated Object",
        type=bpy.types.Object,
        description="Voxel object"
    )

    remove_gamma_correction: BoolProperty(
        name="Remove Gamma Correction",
        description="Turns sRGB inputs into linear RGB values",
        default=True
    )

    show_iou_differences: BoolProperty(
        name="Show Read Grid",
        default=False
    )

    reference_grid_path: StringProperty(
        name="Reference Object Path",
        subtype='FILE_PATH'
    )

    hollow_grid: BoolProperty(
        name="Hollow Out Grid",
        default=False
    )

    camera_ref: bpy.props.PointerProperty(
        name="Render Camera",
        type=bpy.types.Object,
        description=""
    )

class MainMenu(Panel):
    """
    Draw main panel with all the settings presets.
    """
    bl_label = "Voxel Generator"
    bl_idname = "VOXELGENERATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Voxel Editor"

    def draw(self, context):
        """_summary_

        Args:
            context (_type_): _description_
        """
        layout = self.layout
        settings = context.scene.voxel_generator_settings

        box = layout.box()
        box.label(text="Images")
        for idx, img in enumerate(settings.images):
            row = box.row()
            row.prop(img, "orientation", text="")
            row.prop(img, "image_path", text="")

            remove_op = row.operator("voxelgenerator.remove_image", text="", icon='X')
            remove_op.index = idx

        box.operator("voxelgenerator.add_image", icon='ADD')

        box = layout.box()
        box.label(text="Settings")
        box.prop(settings, "width")
        box.prop(settings, "height")
        box.prop(settings, "depth")
        box.prop(settings, "voxel_size")

        box = layout.box()
        box.label(text="Method")
        box.prop(settings, "selected_algorithm")

        if settings.selected_algorithm != 'IMAGE_PREVIEW' and settings.selected_algorithm != 'DEPTH_ESTIMATE':
            box.prop(settings, "color_merging")

        if settings.selected_algorithm == 'SILHOUETTE_INTERSECT':
            box.prop(settings, "threshold")
            box.prop(settings, "use_depth_mapping")

            if settings.use_depth_mapping:
                box.prop(settings, "intensity_threshold")
                box.prop(settings, "concavity_depth")
                box.prop(settings, "depth_factor")
                box.prop(settings, "min_region_size")
                box.prop(settings, "keep_concave_regions")

            box.prop(settings, "hollow_grid")

        if settings.selected_algorithm == 'SPATIAL_CARVING':
            box.prop(settings, "color_threshold_carve")
            box.prop(settings, "dist_threshold_carve")
            box.prop(settings, "concavity_depth")

            box.prop(settings, "hollow_grid")

        if settings.selected_algorithm == 'DEPTH_ESTIMATE':
            box.prop(settings, "intensity_threshold")
            box.prop(settings, "concavity_depth")
            box.prop(settings, "depth_factor")
            box.prop(settings, "min_region_size")
            box.prop(settings, "keep_concave_regions")

        layout.operator("voxelgenerator.generate_grid", icon='MOD_BUILD')

        box = layout.box()
        box.label(text="Testing")
        box.prop(settings, "remove_gamma_correction")
        box.prop(settings, "show_iou_differences")
        box.prop(settings, "reference_grid_path")
        layout.operator("voxelgenerator.generate_comparison_grid", icon='MOD_BUILD')

        layout.operator("voxelgenerator.exp1", icon='FILE_TEXT')

        layout.prop(settings, "camera_ref")
        layout.operator("voxelgenerator.exp2setup", icon='FILE_TEXT')

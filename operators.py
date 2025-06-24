"""
This module implements all the main Operators for the Blender plugin.
"""

import bpy
from bpy.props import (StringProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty, FloatProperty, BoolProperty)
from bpy.types import (Panel, Operator, PropertyGroup)
from . import utils, generate_comparison_grid, experiment1parallelized, experiment2_setup

class AddImage(Operator):
    """
    Operator to add an Image in the panel.
    """
    bl_idname = "voxelgenerator.add_image"
    bl_label = "Add Image"

    def execute(self, context):
        """
        Callback when (add image) button is pressed.
        """
        settings = context.scene.voxel_generator_settings
        settings.images.add()

        return {'FINISHED'}

class RemoveImage(Operator):
    """
    Operator to remove an Image in the panel.
    """
    bl_idname = "voxelgenerator.remove_image"
    bl_label = "Remove Image"

    index: IntProperty() # type: ignore

    def execute(self, context):
        """
        Callback when (remove image) button is pressed.
        """
        settings = context.scene.voxel_generator_settings
        settings.images.remove(self.index)
        return {'FINISHED'}

class GenerateGrid(Operator):
    """
    Operator to generate the voxel grid.
    """
    bl_idname = "voxelgenerator.generate_grid"
    bl_label = "Generate Voxel Grid"

    def execute(self, context):
        """
        Callback when (generate grid) button is pressed.
        """
        settings = context.scene.voxel_generator_settings

        if len(settings.images) < 2:
            self.report({'ERROR'}, "At least two images required")
            return {'CANCELLED'}

        if not settings.selected_algorithm:
            self.report({'ERROR'}, "No algorithm selected")
            return {'CANCELLED'}

        utils.generate_voxel_grid(context)

        self.report({'INFO'}, 'Dids it')    
        return {'FINISHED'}

class GenerateComparison(Operator):
    """
    Operator to generate the comparison grid.
    """
    bl_idname = "voxelgenerator.generate_comparison_grid"
    bl_label = "Compare To GT Model"

    def execute(self, context):
        """
        Callback when (generate comparison) button is pressed.
        """
        settings = context.scene.voxel_generator_settings

        grid = utils.create_grid(context)
        iou, mse = generate_comparison_grid.generate_comp(settings.reference_grid_path,
                                                            grid,
                                                            settings.show_iou_differences)

        self.report({'INFO'}, f'Calculated iou as {iou} and color MSE as {mse}')

        return {'FINISHED'}

class RunExperiment1(Operator):
    """
    Operator to run the first experiment.
    """
    bl_idname = "voxelgenerator.exp1"
    bl_label = "Run Experiment 1"

    def execute(self, context):
        """
        Callback when (run experiment 1) button is pressed.
        """
        experiment1parallelized.run_experiment1_parallel()

        return {'FINISHED'}

class RunSetupExperiment2(Operator):
    """
    Operator to run the setup for the second experiment.
    """
    bl_idname = "voxelgenerator.exp2setup"
    bl_label = "Run Setup Experiment 2"

    def execute(self, context):
        """
        Callback when (run setup experiment 2) button is pressed.
        """
        settings = context.scene.voxel_generator_settings

        experiment2_setup.run_experiment2_setup(settings.camera_ref)

        return {'FINISHED'}

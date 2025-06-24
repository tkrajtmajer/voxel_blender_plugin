"""
Main file for the Blender plugin.
"""

import bpy
from bpy.props import (StringProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty, FloatProperty, BoolProperty)
from bpy.types import (Panel, Operator, PropertyGroup)
import numpy as np
from . import (presets,
            utils,
            operators,
            panel)

bl_info = {
    "name": "Voxel Generator",
    "blender": (3, 0, 0),
    "category": "3D View",
}

classes = (
    panel.ImageMenuItems,
    panel.PanelSettings,
    operators.AddImage,
    operators.RemoveImage,
    operators.GenerateGrid,
    panel.MainMenu,
    operators.GenerateComparison,
    operators.RunExperiment1,
    operators.RunSetupExperiment2
)

def register():
    """
    Register all classes (panels and operators) in the editor.
    """
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.voxel_generator_settings = PointerProperty(type=panel.PanelSettings)

def unregister():
    """
    Unregister all classes.
    """
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.voxel_generator_settings


if __name__ == "__main__":
    register()

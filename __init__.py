bl_info = {
    "name": "Voxel Mesh Generator",
    "blender": (3, 0, 0),
    "category": "3D View",
}

import bpy
from bpy.props import (StringProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty, FloatProperty, BoolProperty)
from bpy.types import (Panel, Operator, PropertyGroup)
import numpy as np
from . import preview, silhouette_intersect, carve, depth_map, generate_mesh, VoxelGrid, generate_comparison_grid
from .experiments import experiment1, experiment1parallelized, experiment2_setup

# preset values
orientations = [
    ('FRONT', "Front", ""),
    ('BACK', "Back", ""),
    ('LEFT', "Left", ""),
    ('RIGHT', "Right", ""),
    ('TOP', "Top", ""),
    ('BOTTOM', "Bottom", ""),
]

algorithms = [
    ('IMAGE_PREVIEW', "Image Preview", ""),
    ('SILHOUETTE_INTERSECT', "Silhouette Intersect", ""),
    ('SPATIAL_CARVING', "Spatial Carving", ""),
    ('DEPTH_ESTIMATE', "Depth Estimation", "")
]

merging_techniques = [
    ('NEAREST_PROJ', "Nearest Projection", ""),
    ('MAJORITY_VOTE', "Majority Vote", "")
]

def create_grid(context):
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
        print(f"Using {np.count_nonzero(pixels_np[..., 3] > 0.0)} pixels in image {img.orientation}")

    if settings.selected_algorithm == 'IMAGE_PREVIEW':
        grid = preview.show_all_sides(images_dict, settings.width, settings.height, settings.depth)
        print("showing preview")

    elif settings.selected_algorithm == 'SILHOUETTE_INTERSECT':
        grid = silhouette_intersect.project_min_dist(images_dict, settings.width, settings.height, settings.depth, settings.color_merging, settings.threshold, settings.use_depth_mapping, settings.intensity_threshold, settings.concavity_depth, settings.depth_factor, settings.min_region_size, settings.keep_concave_regions, settings.hollow_grid)
        print("showing silhouette")

    elif settings.selected_algorithm == 'SPATIAL_CARVING':
        grid = carve.spatial_carve(images_dict, settings.width, settings.height, settings.depth, settings.color_merging, settings.concavity_depth, settings.color_threshold_carve, settings.dist_threshold_carve, settings.hollow_grid)
        print("showing carving")
    
    elif settings.selected_algorithm == 'DEPTH_ESTIMATE':
        grid = depth_map.generate_final_grid(images_dict, settings.width, settings.height, settings.depth, settings.intensity_threshold, settings.concavity_depth, settings.depth_factor, settings.min_region_size, settings.keep_concave_regions)
        print("showing depth estimate")

    else:
        print('nothing happened')

    return grid

def generate_voxel_grid(context):
    settings = context.scene.voxel_generator_settings
    
    grid = create_grid(context)
    
    obj = generate_mesh.generate_mesh_from_grid(grid.getColors(), voxel_size = settings.voxel_size, remove_gamma_correction=settings.remove_gamma_correction)

    settings.gen_object = obj

def update_grid(self, context):
    generate_voxel_grid(context)

class ImageMenuItems(PropertyGroup):
    orientation: EnumProperty(
        name="Orientation",
        items=orientations,
        default='FRONT'
    ) # type: ignore
    
    image_path: StringProperty(
        name="Image Path",
        subtype='FILE_PATH',
        default='/home/tica/Downloads/assets/cup/front.png'
    ) # type: ignore

class PanelSettings(PropertyGroup):
    images: CollectionProperty(type=ImageMenuItems) # type: ignore
    
    selected_algorithm: EnumProperty(
        name="Method",
        items=algorithms
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
        update=update_grid
    ) # type: ignore

    use_depth_mapping: BoolProperty(
        name="Use Depth Mapping",
        default=False,
        update=update_grid
    )

    color_merging: EnumProperty(
        name="Color Merging",
        items=merging_techniques,
        update=update_grid
    ) # type: ignore

    color_threshold_carve: IntProperty(
        name="Color Threshold",
        default=6,
        min=1,
        max=6,
        update=update_grid
    ) # type: ignore

    dist_threshold_carve: FloatProperty(
        name="Variance Threshold",
        default=0.5, 
        min=0,
        max=1,
        update=update_grid
    ) # type: ignore

    concavity_depth: FloatProperty(
        name="Concavity Depth Threshold",
        default=0.5, 
        min=0,
        max=1,
        update=update_grid
    ) # type: ignore

    # depth maps
    intensity_threshold: FloatProperty(
        name="Intensity Threshold",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_grid
    ) # type: ignore

    depth_factor: FloatProperty(
        name="Depth Factor",
        default=1, 
        min=0,
        update=update_grid
    ) # type: ignore

    min_region_size: FloatProperty(
        name="Minimum Region Size",
        default=5, 
        min=0,
        update=update_grid
    ) # type: ignore

    keep_concave_regions: BoolProperty(
        name="Keep Concave Regions",
        description="Toggle concavity regions on/off",
        default=True,
        update=update_grid
    )

    active_image_index: IntProperty(default=0) # type: ignore

    ref_object: bpy.props.PointerProperty(
        name="Reference Object",
        type=bpy.types.Object,
        description="Reference object for ground-truth comparison"
    )

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

class AddImage(Operator):
    bl_idname = "voxelgenerator.add_image"
    bl_label = "Add Image"

    def execute(self, context):
        settings = context.scene.voxel_generator_settings
        settings.images.add()
        return {'FINISHED'}
    
class RemoveImage(Operator):
    bl_idname = "voxelgenerator.remove_image"
    bl_label = "Remove Image"

    index: IntProperty() # type: ignore

    def execute(self, context):
        settings = context.scene.voxel_generator_settings
        settings.images.remove(self.index)
        return {'FINISHED'}

class GenerateGrid(Operator):
    bl_idname = "voxelgenerator.generate_grid"
    bl_label = "Generate Voxel Grid"

    def execute(self, context):
        settings = context.scene.voxel_generator_settings

        if len(settings.images) < 2:
            self.report({'ERROR'}, "At least two images required")
            return {'CANCELLED'}

        if not settings.selected_algorithm:
            self.report({'ERROR'}, "No algorithm selected")
            return {'CANCELLED'}

        generate_voxel_grid(context)

        self.report({'INFO'}, 'Dids it')    
        return {'FINISHED'}

class GenerateComparison(Operator):
    bl_idname = "voxelgenerator.generate_comparison_grid"
    bl_label = "Compare To GT Model"

    def execute(self, context):
        settings = context.scene.voxel_generator_settings

        grid = create_grid(context)
        iou, mse = generate_comparison_grid.generate_comp(settings.reference_grid_path, grid, settings.show_iou_differences)

        self.report({'INFO'}, f'Calculated iou as {iou} and color MSE as {mse}')    

        return {'FINISHED'}

class RunExperiment1(Operator):
    bl_idname = "voxelgenerator.exp1"
    bl_label = "Run Experiment 1"

    def execute(self, context):
        settings = context.scene.voxel_generator_settings

        experiment1parallelized.run_experiment1_parallel()

        return {'FINISHED'}

class RunSetupExperiment2(Operator):
    bl_idname = "voxelgenerator.exp2setup"
    bl_label = "Run Setup Experiment 2"

    def execute(self, context):
        settings = context.scene.voxel_generator_settings

        experiment2_setup.run_experiment2_setup(settings.camera_ref)

        return {'FINISHED'}

class MainMenu(Panel):
    bl_label = "Voxel Generator"
    bl_idname = "VOXELGENERATOR_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Voxel Editor"

    def draw(self, context):
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
        layout.operator("voxelgenerator.im_preset", icon='IMAGE_DATA')

        box = layout.box()
        box.label(text="Testing")
        layout.prop(settings, "gen_object")
        layout.prop(settings, "ref_object")
        box.prop(settings, "remove_gamma_correction")
        box.prop(settings, "show_iou_differences")
        box.prop(settings, "reference_grid_path")
        layout.operator("voxelgenerator.generate_comparison_grid", icon='MOD_BUILD')

        layout.operator("voxelgenerator.exp1", icon='FILE_TEXT')

        layout.prop(settings, "camera_ref")
        layout.operator("voxelgenerator.exp2setup", icon='FILE_TEXT')

classes = (
    ImageMenuItems,
    PanelSettings,
    AddImage,
    RemoveImage,
    GenerateGrid,
    MainMenu,
    GenerateComparison,
    RunExperiment1,
    RunSetupExperiment2
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.voxel_generator_settings = PointerProperty(type=PanelSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.voxel_generator_settings


if __name__ == "__main__":
    register()
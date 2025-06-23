import os
import itertools
import csv
import numpy as np
import bpy
import math
from . import silhouette_intersect, carve, depth_map, generate_mesh

fullpath = "/home/tica/.config/blender/4.4/extensions/user_default/voxel_generator/exp2"
assets_path = fullpath + '/assets'
output_path = fullpath + '/rendered_out'

subset_to_render_views = {
    ("TOP", "LEFT"): ["BOTTOM", "RIGHT"],
    ("TOP", "FRONT"): ["BOTTOM", "BACK"],
    ("FRONT", "LEFT"): ["BACK", "RIGHT"],
    ("TOP", "FRONT", "LEFT"): ["BOTTOM", "BACK", "RIGHT"],
}

size_map = {
    "barrel": 16,
    "bear": 32,
    "chair": 32,
    "cup": 16,
    "donut": 8,
    "feesh": 32,
    "guy": 16,
    "left": 16,
    "mug": 32,
    "pillar": 16,
    "plant": 32,
    "shark": 32,
    "turtle": 32
}

# Different merge strategies to evaluate
merge_strategies = ["NEAREST_PROJ", "MAJORITY_VOTE"]

def load_subset_images(obj_folder, views):
    images = {}
    for view in views:
        img_path = os.path.join(obj_folder, view.lower() + ".png")
        image = bpy.data.images.load(img_path)
        w, h = image.size
        pixels_np = np.array(image.pixels[:]).reshape((h, w, 4))
        pixels_np = np.round(pixels_np, 3)
        images[view] = pixels_np
    return images

def render_from_view(obj, cam, view_name, save_path, ortho_scale=30):

    cam.data.ortho_scale = ortho_scale

    # Set rotation based on view
    view_rotations = {
        "FRONT": (0, 0, 0),
        "BACK": (0, 0, math.radians(180)),
        "LEFT": (0, 0, math.radians(90)),
        "RIGHT": (0, 0, math.radians(-90)),
        "TOP": (math.radians(90), 0, 0),
        "BOTTOM": (math.radians(-90), 0, 0),
    }
    
    obj.rotation_euler = view_rotations[view_name]
    cam.location = (0, -50, 0)  # You can refine based on grid size

    bpy.context.scene.camera = cam
    bpy.context.view_layer.update()

    bpy.context.scene.render.filepath = save_path

    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get().update()

    bpy.ops.render.render(write_still=True)

def run_experiment2_setup(camera_ref):
    for obj_name in os.listdir(assets_path):
        obj_dir = os.path.join(assets_path, obj_name)
        if not os.path.isdir(obj_dir) or obj_name not in size_map:
            continue

        # --- Determine which subset(s) to run ---
        available_views = {
            fname.split('.')[0].upper()
            for fname in os.listdir(obj_dir)
            if fname.endswith(".png")
        }

        chosen_subsets = []

        if available_views >= {"FRONT", "LEFT"}:
            chosen_subsets.append(("FRONT", "LEFT"))

        if len(available_views) >= 5:  # Use all options only for "fuller" objects
            for subset in subset_to_render_views:
                if set(subset).issubset(available_views):
                    chosen_subsets.append(subset)

        for view_subset in chosen_subsets:
            # --- Load subset images ---
            images = load_subset_images(obj_dir, view_subset)
            if len(images) != len(view_subset):
                print(f"Skipping {obj_name} - incomplete view subset {view_subset}")
                continue

            ctresh = len(images)
            cdepthtresh = 0.0

            if len(images) == 6:
                ctresh = 5
                cdepthtresh = 0.5

            w = h = d = size_map[obj_name]

            # --- Run algorithms ---
            results = []

            # SILHOUETTE INTERSECT variants
            for strat in merge_strategies:
                grid = silhouette_intersect.project_min_dist(
                    images, w, h, d,
                    merge_technique=strat,
                    threshold=1.0,
                    hollow_grid=True
                )
                results.append(("SILHOUETTE_INTERSECT", strat, grid))

            # SPATIAL CARVING variants
            for strat in merge_strategies:
                grid = carve.spatial_carve(
                    images, w, h, d,
                    merge_technique=strat,
                    color_sim_technique="NISTA",
                    concavity_depth=cdepthtresh,
                    colors_threshold=ctresh,
                    variance_threshold=0.25,
                    hollow_grid=True
                )
                results.append(("SPATIAL_CARVE", strat, grid))

            # DEPTH MAPPING baseline (doesn't use merge)
            grid = depth_map.generate_final_grid(
                images, w, h, d,
                intensity_threshold=1.0,
                concavity_depth=0.125,
                factor=0.25,
                min_region_size=4,
                keep_concave_regions=True
            )
            results.append(("DEPTH_MAPPING", "NONE", grid))

            # HYBRID methods
            for strat in merge_strategies:
                grid = silhouette_intersect.project_min_dist(
                    images, w, h, d,
                    merge_technique=strat,
                    threshold=1.0,
                    use_depth_mapping=True,
                    intensity_threshold=1.0,
                    concavity_depth=0.125,
                    factor=0.25,
                    min_region_size=4,
                    keep_concave_regions=True,
                    hollow_grid=True
                )
                results.append(("HYBRID_DEPTH", strat, grid))


            for algo_name, merge_strategy, grid in results:
                # Generate a unique mesh object
                obj = generate_mesh.generate_mesh_from_grid(grid.colors, obj_name=f"{obj_name}_{algo_name}_{merge_strategy}")

                if obj.name not in bpy.context.collection.objects:
                    bpy.context.collection.objects.link(obj)

                obj.hide_render = False
                obj.hide_viewport = False
                obj.location = (0, 0, 0)

                # Folder name includes object name
                save_dir = os.path.join(output_path, obj_name)
                os.makedirs(save_dir, exist_ok=True)

                # Views used to generate model
                used_views_str = "_".join([v.lower() for v in view_subset])

                # Views to render from
                render_views = subset_to_render_views.get(view_subset, [])
                for view in render_views:
                    current_view_str = view.lower()
                    filename = f"{current_view_str}_{algo_name}_{merge_strategy}_from_{used_views_str}.png"
                    out_path = os.path.join(save_dir, filename)

                    render_from_view(obj, camera_ref, view, out_path, ortho_scale=size_map[obj_name])

                bpy.data.objects.remove(obj, do_unlink=True)



import os
import itertools
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import bpy

from . import silhouette_intersect, carve, depth_map, generate_comparison_grid

# --- Configurations ---
plugin_root = os.path.dirname(os.path.abspath(__file__))
fullpath = os.path.join(plugin_root, 'voxel_generator', 'exp1')
ref_txt_dir = fullpath + '/ground_truth'
ref_img_root = fullpath + '/images_sub'

# silhouette 24 permutations per
thresholds = [0.6, 0.8, 1.0]
hollow_options = [True]
merge_techniques = ["MAJORITY_VOTE", "NEAREST_PROJ"]

# carving
color_thresholds = [4, 5, 6]
variance_range = np.linspace(0, 0.5, 5)
concavity_range = np.linspace(0, 0.5, 5)

# depth
concavity_depth_threshold = np.linspace(0, 0.5, 5)
depth_factor = [0.25, 0.5, 1.0, 1.25, 1.5, 2.0]
minimum_region_size = [1, 2, 4, 8]

# hybrid
# same as depth here
# just actually use it
thresholds_hybrid = [0.8, 1.0]


size_map = {
    "bone": 16,
    "box": 20,
    "box2": 20,
    "box3": 20,
    "box4": 20,
    "bush": 20,
    "cactuss": 30,
    "castle": 21,
    "chr_knight": 21,
    "chr_sword": 21,
    "coin": 12,
    "covjek": 20,
    "fence": 20,
    "rock": 20,
    "skull": 16,
    "smallguy": 8,
}

def load_reference_images(img_dir):
    images_dict = {}

    orientations = {
        "FRONT": img_dir + "/front.png",
        "BACK": img_dir + "/back.png",
        "LEFT": img_dir + "/left.png",
        "RIGHT": img_dir + "/right.png",
        "TOP": img_dir + "/top.png",
        "BOTTOM": img_dir + "/bottom.png",
    }

    for (ori, impath) in orientations.items():
        image = bpy.data.images.load(impath)
        width, height = image.size
        pixels_np = np.array(image.pixels[:]).reshape((height, width, 4))
        pixels_np = np.round(pixels_np, 3)
        images_dict[ori] = pixels_np

    return images_dict

def single_job(job):
    """
    Runs one (algo, obj, params...) job and returns a tuple:
    (obj_name, algo_name, merge, iou, mse, params_dict)
    """
    algo, obj_base, params = job
    ref_txt_path = os.path.join(ref_txt_dir, obj_base + '.txt')
    img_dir      = os.path.join(ref_img_root, obj_base)
    
    images = load_reference_images(img_dir)
    grid_size = size_map[obj_base]
    w = h = d = grid_size

    if algo == "SILHOUETTE_INTERSECT":
        model = silhouette_intersect.project_min_dist(
            images, w, h, d,
            merge_technique=params['merge'],
            threshold=params['threshold'],
            hollow_grid=params['hollow_grid']
        )
    elif algo == "SPATIAL_CARVE":  # SPATIAL_CARVE
        model = carve.spatial_carve(
            images, w, h, d,
            merge_technique=params['merge'],
            concavity_depth=params['concavity_depth'],
            colors_threshold=params['colors_threshold'],
            variance_threshold=params['variance_threshold'],
            hollow_grid=params['hollow_grid']
        )
    elif algo == "DEPTH_MAPPING":
        model = depth_map.generate_final_grid(
            images, w, h, d,
            intensity_threshold=1.0,
            concavity_depth=params['concavity_depth_threshold'],
            factor=params['depth_factor'],
            min_region_size=params['minimum_region_size'],
            keep_concave_regions=True
        )
    else:
        model = silhouette_intersect.project_min_dist(
            images, w, h, d,
            merge_technique=params['merge'],
            threshold=params['thresholds_hybrid'],
            use_depth_mapping=True,
            intensity_threshold=1.0,
            concavity_depth=params['concavity_depth_threshold'],
            factor=params['depth_factor'],
            min_region_size=params['minimum_region_size'],
            keep_concave_regions=True,
            hollow_grid=params['hollow_grid']
        )

    iou, mse = generate_comparison_grid.generate_comp(ref_txt_path, model)
    
    merge_val = params.get('merge', '')
    return obj_base, algo, merge_val, iou, mse, params

def run_experiment1_parallel(context=None):
    # 1) build job list
    jobs = []
    for obj_name in os.listdir(ref_txt_dir):
        if not obj_name.endswith('.txt'): continue
        obj = obj_name[:-4]
        if obj not in size_map: continue

        # Silhouette jobs
        for merge, thresh, hollow in itertools.product(merge_techniques, thresholds, hollow_options):
            jobs.append((
                "SILHOUETTE_INTERSECT", obj,
                {"merge": merge, "threshold": thresh, "hollow_grid": hollow}
            ))
        # Spatial carving jobs
        for merge, clrt, var, conc, hollow in itertools.product(
            merge_techniques, color_thresholds, variance_range, concavity_range, hollow_options
        ):
            jobs.append((
                "SPATIAL_CARVE", obj,
                {
                    "merge": merge,
                    "colors_threshold": clrt,
                    "variance_threshold": var,
                    "concavity_depth": conc,
                    "hollow_grid": hollow
                }
            ))
        for conc, factor, region_size in itertools.product(
            concavity_depth_threshold, depth_factor, minimum_region_size
        ):
            jobs.append((
                "DEPTH_MAPPING", obj,
                {
                    "concavity_depth_threshold": conc,
                    "depth_factor": factor,
                    "minimum_region_size": region_size
                }
            ))

        for merge, threshold, conc, factor, region_size, hollow in itertools.product(
            merge_techniques, thresholds,
            concavity_depth_threshold, depth_factor, minimum_region_size,
            hollow_options
        ):
            jobs.append((
                "HYBRID_DEPTH", obj,
                {
                    "merge": merge,
                    "thresholds_hybrid": threshold,
                    "concavity_depth_threshold": conc,
                    "depth_factor": factor,
                    "minimum_region_size": region_size,
                    "hollow_grid": hollow
                }
            ))

    # 2) dispatch in parallel
    results = []  # collect all (obj, algo, merge, iou, mse, params)
    with ProcessPoolExecutor() as pool:
        future_to_job = {pool.submit(single_job, job): job for job in jobs}
        for fut in as_completed(future_to_job):
            try:
                results.append(fut.result())
            except Exception as e:
                job = future_to_job[fut]
                print(f"Job {job} failed: {e}")

    # 3) pick best per object & algorithm
    best = {}
    for obj, algo, merge, iou, mse, params in results:
        key = (obj, algo, merge)
        prev = best.get(key)
        if prev is None or iou > prev[0]:
            best[key] = (iou, mse, params)

    # 4) write CSV
    out_path = os.path.join(fullpath, "results.csv")
    with open(out_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Model","Algorithm","Merge","IoU","MSE","Params"])
        writer.writerow(["==================================================================="])
        
        sorted_items = sorted(best.items(), key=lambda item: item[0][0])  # (obj, algo, merge) -> sort by obj
        current_obj = None

        for (obj, algo, merge), (iou, mse, params) in sorted_items:
            if obj != current_obj and current_obj is not None:
                writer.writerow(["-----------------------------------------------------------------"])

            current_obj = obj

            writer.writerow([
                obj,
                algo,
                merge,
                f"{iou:.4f}",
                f"{mse:.6f}",
                str(params)
            ])
            
    print("Results written to", out_path)

if __name__ == "__main__":
    run_experiment1_parallel()

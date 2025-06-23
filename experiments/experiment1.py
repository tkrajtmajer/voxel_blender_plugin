import os
import numpy as np
import re
import itertools
import bpy
from . import silhouette_intersect, carve, generate_comparison_grid
import csv

# --- Configurations ---
fullpath = "/home/tica/.config/blender/4.4/extensions/user_default/voxel_generator/exp1"
ref_txt_dir = fullpath + '/ground_truth'
ref_img_root = fullpath + '/images_sub'

# silhouette
thresholds = [0.6, 0.8, 1.0]
hollow_options = [True, False]
merge_techniques = ["MAJORITY_VOTE", "NEAREST_PROJ"]

# carving
concavity_range = np.linspace(0, 1, 3)
variance_range = np.linspace(0, 1, 5)
color_thresholds = [4, 5, 6]

# depth

# hybrid

# Model name -> grid size (assumes cube)
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

def export_results_to_csv_row_silhouette(writer, obj_name, best_results):
    for method, metrics in best_results.items():
        iou = metrics.get("iou", -1)
        mse = metrics.get("mse", -1)
        params = metrics.get("params", {})
        threshold = params.get("threshold", None)
        hollow = params.get("hollow_grid", None)

        writer.writerow([
            obj_name,
            method,
            f"{iou:.4f}",
            f"{mse:.6f}",
            threshold,
            hollow
        ])   

def export_results_to_csv_row_carving(writer, obj_name, best_results):
    for method, metrics in best_results.items():
        iou = metrics.get("iou", -1)
        mse = metrics.get("mse", -1)
        params = metrics.get("params", {})
        color_thresh = params.get("color_thresholds", None)
        var = params.get("variance_range", None)
        conc_range = params.get("concavity_range", None)
        hollow = params.get("hollow_grid", None)

        writer.writerow([
            obj_name,
            method,
            f"{iou:.4f}",
            f"{mse:.6f}",
            color_thresh,
            var,
            conc_range,
            hollow
        ])       

def run_experiment1():
    with open(fullpath + "/results.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Silhouette Intersect"])
        writer.writerow(["------------------------"])
        writer.writerow(["Model", "Merge Technique", "IoU", "MSE", "Threshold", "Hollow Grid"])
        writer.writerow(["==================================================================="])

        for obj_name in os.listdir(ref_txt_dir):
            if not obj_name.endswith('.txt'):
                continue

            obj_base = obj_name[:-4]
            ref_txt_path = os.path.join(ref_txt_dir, obj_name)
            img_dir = os.path.join(ref_img_root, obj_base)

            if not os.path.isdir(img_dir):
                print(f"Warning: Image folder for {obj_base} not found, skipping.")
                continue

            # print(f"\n=== Evaluating: {obj_base} ===")

            grid_size = size_map.get(obj_base)
            if not grid_size:
                print(f"Warning: No grid size for {obj_base}, skipping.")
                continue

            width = height = depth = grid_size
            images = load_reference_images(img_dir)

            best_results = {
                "MAJORITY_VOTE": {"iou": -1, "mse": float("inf"), "params": None},
                "NEAREST_PROJ": {"iou": -1, "mse": float("inf"), "params": None},
            }

            for threshold, hollow, merge in itertools.product(thresholds, hollow_options, merge_techniques):
                model = silhouette_intersect.project_min_dist(
                    images,
                    width,
                    height,
                    depth,
                    merge_technique=merge,
                    threshold=threshold,
                    hollow_grid=hollow
                )

                iou, mse = generate_comparison_grid.generate_comp(ref_txt_path, model)

                if iou > best_results[merge]["iou"]:
                    best_results[merge] = {
                        "iou": iou,
                        "mse": mse,
                        "params": {
                            "threshold": threshold,
                            "hollow_grid": hollow
                        }
                    }

            # for method in merge_techniques:
            #     print(f"\n>> Best result for {method} on {obj_base}:")
            #     print(f"    IoU = {best_results[method]['iou']:.4f}")
            #     print(f"    MSE = {best_results[method]['mse']:.6f}")
            #     print(f"    Params = {best_results[method]['params']}")

            # Append best results for current object to CSV
            export_results_to_csv_row_silhouette(writer, obj_base, best_results)

            writer.writerow(["--------------------------------------------------------------------"])
        writer.writerow([])
        writer.writerow([])

        # carving
        writer.writerow(["Spatial Carving"])
        writer.writerow(["------------------------"])
        writer.writerow(["Model", "Merge Technique", "IoU", "MSE", "Color Threshold", "Variance Threshold", "Concavity Depth"])
        writer.writerow(["==================================================================="])

        for obj_name in os.listdir(ref_txt_dir):
            if not obj_name.endswith('.txt'):
                continue

            obj_base = obj_name[:-4]
            ref_txt_path = os.path.join(ref_txt_dir, obj_name)
            img_dir = os.path.join(ref_img_root, obj_base)

            if not os.path.isdir(img_dir):
                print(f"Warning: Image folder for {obj_base} not found, skipping.")
                continue

            # print(f"\n=== Evaluating: {obj_base} ===")

            grid_size = size_map.get(obj_base)
            if not grid_size:
                print(f"Warning: No grid size for {obj_base}, skipping.")
                continue

            width = height = depth = grid_size
            images = load_reference_images(img_dir)

            best_results = {
                "MAJORITY_VOTE": {"iou": -1, "mse": float("inf"), "params": None},
                "NEAREST_PROJ": {"iou": -1, "mse": float("inf"), "params": None},
            }

            for clrt, variance, concrng, hollow, merge in itertools.product(color_thresholds, variance_range, concavity_range, hollow_options, merge_techniques):
                model = carve.spatial_carve(
                    images,
                    width,
                    height,
                    depth,
                    merge_technique=merge,
                    color_sim_technique="NISTA",
                    colors_threshold=clrt,
                    variance_threshold=variance,
                    concavity_depth=concrng,
                    hollow_grid=hollow
                )

                iou, mse = generate_comparison_grid.generate_comp(ref_txt_path, model)

                if iou > best_results[merge]["iou"]:
                    best_results[merge] = {
                        "iou": iou,
                        "mse": mse,
                        "params": {
                            "color_thresholds": clrt,
                            "variance_range": variance,
                            "concavity_range": concrng,
                            "hollow_grid": hollow
                        }
                    }

            # for method in merge_techniques:
            #     print(f"\n>> Best result for {method} on {obj_base}:")
            #     print(f"    IoU = {best_results[method]['iou']:.4f}")
            #     print(f"    MSE = {best_results[method]['mse']:.6f}")
            #     print(f"    Params = {best_results[method]['params']}")

            # Append best results for current object to CSV
            export_results_to_csv_row_carving(writer, obj_base, best_results)

            writer.writerow(["--------------------------------------------------------------------"])

        writer.writerow([])
        writer.writerow([])

# if __name__ == '__main__':
#     run_silhouette()
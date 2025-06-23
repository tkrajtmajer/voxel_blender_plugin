import os
import csv
from PIL import Image
import numpy as np
from collections import defaultdict

fullpath = "/home/tica/Documents/school/rp-master-folder/experiment/current/part_two/measure_overlap/exp2"
assets_path = fullpath + '/assets'
output_path = fullpath + '/rendered_out'

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

def downscale_to_grid(filepath, target_size):
    with Image.open(filepath) as img:
        img = img.convert("RGBA")
        return img.resize((target_size, target_size), Image.NEAREST)

def calculate_metrics(pred_img, gt_img):
    pred = np.array(pred_img)
    gt = np.array(gt_img)

    pred_mask = pred[..., 3] > 0
    gt_mask = gt[..., 3] > 0

    intersection = np.logical_and(pred_mask, gt_mask).sum()
    union = np.logical_or(pred_mask, gt_mask).sum()
    iou = intersection / union if union != 0 else 0

    overlap_mask = np.logical_and(pred_mask, gt_mask)
    overlap_indices = np.where(overlap_mask)

    if overlap_indices[0].size > 0:
        pred_rgb = pred[overlap_indices][:, :3] / 255.0
        gt_rgb = gt[overlap_indices][:, :3] / 255.0
        mse = np.mean((pred_rgb - gt_rgb) ** 2)
    else:
        mse = 0

    return iou, mse

def run_comparison():
    results = defaultdict(list)  # key: (View, Algo, Merge, Input_Views), value: list of (iou, mse)

    for objname in os.listdir(output_path):
        obj_folder = os.path.join(output_path, objname)
        if not os.path.isdir(obj_folder): continue

        grid_size = size_map.get(objname)
        if not grid_size:
            print(f"[!] Skipping unknown object: {objname}")
            continue

        asset_folder = os.path.join(assets_path, objname)
        if not os.path.exists(asset_folder):
            print(f"[!] Missing asset folder for {objname}")
            continue

        for fname in os.listdir(obj_folder):
            if not fname.endswith(".png"): continue

            try:
                parts = fname.replace(".png", "").split("_")
                current_view = parts[0]
                algo = parts[1]
                merge = parts[2]
                input_views = "_".join(parts[4:])

                pred_img = downscale_to_grid(os.path.join(obj_folder, fname), grid_size)
                gt_path = os.path.join(asset_folder, current_view.lower() + ".png")
                gt_img = downscale_to_grid(gt_path, grid_size)

                iou, mse = calculate_metrics(pred_img, gt_img)

                key = (current_view, algo, merge, input_views)
                results[key].append((iou, mse))

            except Exception as e:
                print(f"[!] Error processing {fname} in {objname}: {e}")

    # Now compute averages and write final CSV
    csv_path = os.path.join(fullpath, "averaged_comparison_results.csv")
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["View", "Algo", "Merge", "Input_Views", "Avg_IOU", "Avg_MSE"])

        for key, metrics in results.items():
            avg_iou = sum(m[0] for m in metrics) / len(metrics)
            avg_mse = sum(m[1] for m in metrics) / len(metrics)
            writer.writerow([*key, f"{avg_iou:.4f}", f"{avg_mse:.4f}"])

if __name__ == "__main__":
    run_comparison()

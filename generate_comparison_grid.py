import bpy
import bmesh
import numpy as np
import mathutils
import re
from . import generate_mesh

def srgb_to_linear(arr):
    arr = np.asarray(arr)

    rgb = arr[..., :3]
    alpha = arr[..., 3:]

    rgb_linear = np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4
    )

    return np.concatenate((rgb_linear, alpha), axis=-1)

def load_color_grid_from_txt(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    # Extract shape from first line
    shape_line = lines[0]
    shape_match = re.search(r'\((\d+),\s*(\d+),\s*(\d+)\)', shape_line)
    if not shape_match:
        raise ValueError("Could not parse shape line")

    x_size, y_size, z_size = map(int, shape_match.groups())
    grid = np.zeros((x_size, y_size, z_size, 4), dtype=np.float32)  # RGBA normalized to [0.0, 1.0]

    z = -1
    y = 0
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if line.startswith("# Layer z="):
            z = int(re.search(r'z=(\d+)', line).group(1))
            y = 0
            continue
        # Parse RGBA tuples as ints
        color_tuples = re.findall(r'\((\d+),(\d+),(\d+),(\d+)\)', line)
        for x, (r, g, b, a) in enumerate(color_tuples):
            rgba = np.array([int(r), int(g), int(b), int(a)], dtype=np.float32) / 255.0
            grid[x, y, z] = rgba
        y += 1

    return grid

def rotate_voxel_grid_for_blender(grid):
    grid = np.flip(grid, axis=0)
    grid = np.flip(grid, axis=1)  
    
    return grid

def hollow_out_grid(colors):
        width, height, depth, _ = colors.shape
        hollow_grid = np.copy(colors)

        for x in range(1, width - 1):
            for y in range(1, height - 1):
                for z in range(1, depth - 1):
                    if colors[x, y, z][3] == 0:
                        continue

                    fully_surrounded = True
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for dz in (-1, 0, 1):
                                if dx == dy == dz == 0:
                                    continue  # skip center
                                neighbor = colors[x + dx, y + dy, z + dz]
                                if neighbor[3] == 0:
                                    fully_surrounded = False
                                    break
                            if not fully_surrounded:
                                break
                        if not fully_surrounded:
                            break

                    if fully_surrounded:
                        hollow_grid[x, y, z] = [0, 0, 0, 0]  # mark as hollow (transparent)

        return hollow_grid

def compute_color_mse(grid1, grid2, ignore_transparent=True, tol=1e-2):
    flat1 = grid1.reshape(-1, 4)
    flat2 = grid2.reshape(-1, 4)

    if ignore_transparent:
        alpha1 = flat1[:, 3]
        alpha2 = flat2[:, 3]
        keep_mask = ~((alpha1 <= tol) & (alpha2 <= tol))
        flat1 = flat1[keep_mask]
        flat2 = flat2[keep_mask]

    mse = np.mean((flat1[:, :3] - flat2[:, :3]) ** 2)
    return mse

def generate_comp(ref_file, gen_model, draw_comp=False, tol=1e-3, remove_gamma_correction=True):
    """
    Compute IoU for float RGBA voxel grids in [0.0, 1.0],
    ignoring voxels where alpha == 0.0 in both grids.
    
    `tol` is the per-channel tolerance.
    """
    grid1 = rotate_voxel_grid_for_blender(load_color_grid_from_txt(ref_file))
    grid2 = gen_model.colors

    if remove_gamma_correction:
        grid2 = srgb_to_linear(grid2)

    # hollow out grid1 for a more fair comparison for depth tbh lowkey
    grid1 = hollow_out_grid(grid1)

    # print(grid1.shape)
    # print(grid2.shape)

    # ref_coords = np.argwhere(grid1[..., 3] > 0)
    # gen_coords = np.argwhere(grid2[..., 3] > 0)

    # print("Sample ref coords:", ref_coords[:5])
    # print("Sample gen coords:", gen_coords[:5])

    assert grid1.shape == grid2.shape, "Grid shapes must match"

    alpha1 = grid1[..., 3]
    alpha2 = grid2[..., 3]

    occupied1 = alpha1 == 1.0
    occupied2 = alpha2 == 1.0

    # print(occupied1.shape)
    # print(occupied2.shape)

    intersection = np.logical_and(occupied1, occupied2).sum()
    union = np.logical_or(occupied1, occupied2).sum()

    # print(f"occupied 1: {np.where(occupied1 == True)}")

    # for a in range (16):
    #     for b in range (16):
    #         for c in range (16):
    #             print(f"{a} {b} {c} is {grid1[a,b,c]}")

    # print(f"occupied 2: {np.where(occupied2 == True)}")

    # print(intersection)
    # print(union)

    iou = intersection / union if union > 0 else 0.0

    # print(f"Voxel IOU is {iou}")

    mse = compute_color_mse(grid1, grid2)
    # print(f"MSE: {mse:.6f}")

    # render the loaded grid idk what else man
    if (draw_comp):
        generate_mesh.generate_mesh_from_grid(grid1, obj_name="Ref obj", mesh_name="Ref mesh")

    return iou, mse

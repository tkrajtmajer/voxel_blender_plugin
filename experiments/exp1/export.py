import os
import numpy as np
from voxypy.models import Entity

def extract_from_file(path):
    # Load the .vox into a VoxyPy Entity
    entity = Entity().from_file(path)
    palette = entity.get_palette()  # list of RGB(A) tuples
    dense = entity.get_dense()      # shape: (X, Y, Z), values are color indices
    
    # Create RGB color grid
    X, Y, Z = dense.shape
    color_grid = np.zeros((X, Y, Z, 4), dtype=np.uint8)
    
    for idx in np.unique(dense):
        if idx == 0:
            continue  # index 0 is empty/blank
        rgb = palette[idx]
        color_grid[dense == idx] = rgb
    
    return color_grid

def save_color_grid(grid, out_path):
    with open(out_path, 'w') as f:
        x_size, y_size, z_size, _ = grid.shape
        f.write(f"# Shape: ({x_size}, {y_size}, {z_size})\n")
        for z in range(z_size):
            f.write(f"\n# Layer z={z}\n")
            for y in range(y_size):
                row = []
                for x in range(x_size):
                    r, g, b, a = grid[x, y, z] 
                    row.append(f"({r},{g},{b},{a})")
                f.write(" ".join(row) + "\n")

def main():
    input_dir = './models'
    output_dir = './out'
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.endswith('.vox'):
            input_path = os.path.join(input_dir, filename)
            model_name = os.path.splitext(filename)[0]
            print("model name " + model_name)
            output_path = os.path.join(output_dir, f"{model_name}.txt")

            print(f"Processing {filename}...")
            color_grid = extract_from_file(input_path)
            save_color_grid(color_grid, output_path)

    print("Done.")

if __name__ == '__main__':
    main()
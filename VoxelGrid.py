"""
Voxel Grid class, used to store the grid color information.
"""
import json
import numpy as np

class VoxelGrid:
    """
    Voxel Grid class.
    """
    def __init__(self, width, height, depth, channels=4):
        self.width = width
        self.height = height
        self.depth = depth
        self.colors = np.zeros(shape=(width, height, depth, channels), dtype=float)

    def get_colors(self):
        """
        Returns 3D array of colors
        """
        return self.colors

    def set_color(self, x, y, z, color):
        """
        Set color at (x,y,z) as specified
        """
        self.colors[x, y, z] = color

    # slice by slice
    def visualize_grid(self):
        """
        Print layers of the grid.
        """
        for z in range(self.depth):
            print(f"Layer {z + 1}:")
            for y in range(self.height):
                for x in range(self.width):
                    color = self.colors[x, y, z]
                    print(f"Voxel ({x}, {y}, {z}): {color}")
            print("\n") 

    def write_grid(self):
        """
        Write grid values to a JSON file.
        """
        voxel_data = []
        w, h, d, _ = self.colors.shape

        for x in range(w):
            for y in range(h):
                for z in range(d):
                    color = self.colors[x, y, z]
                    voxel_data.append({
                        "pos": [x, y, z],
                        "color": color.tolist()
                    })

        with open("./out.json", "w") as f:
            json.dump(voxel_data, f)

    def hollow_out_grid(self, colors):
        """
        Produce a hollow version of the grid to improve performance.
        """
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
                                    continue 
                                neighbor = colors[x + dx, y + dy, z + dz]
                                if neighbor[3] == 0:
                                    fully_surrounded = False
                                    break
                            if not fully_surrounded:
                                break
                        if not fully_surrounded:
                            break

                    if fully_surrounded:
                        hollow_grid[x, y, z] = [0, 0, 0, 0]

        return hollow_grid

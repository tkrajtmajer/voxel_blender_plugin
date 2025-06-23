import numpy as np
from . import VoxelGrid
from collections import deque

def calculate_depth(view, image, other_images, width, height, depth):

    depth_map = -np.ones((image.shape[0], image.shape[1]), dtype=int)
    
    if view == 'FRONT':
        for x in range (width):
            for z in range (height):

                if image[z, x, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for y in range (depth):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'BACK' and img[z, width - 1 - x, 3] != 0:
                                overlap += 1
                            if v == 'LEFT' and img[z, depth - 1 - y, 3] != 0:
                                overlap += 1
                            if v == 'RIGHT' and img[z,y,3] != 0:
                                overlap += 1
                            if v == 'TOP' and img[y, x,3] != 0:
                                overlap += 1
                            if v == 'BOTTOM' and img[depth - 1 - y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = y
                    
                    depth_map[z, x] = max_overlap_idx

                else:
                    depth_map[z, x] = -1

    elif view == 'BACK':
        for x in range (width):
            for z in range (height):

                if image[z, width - 1 - x, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for y in range (depth-1,0,-1):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'FRONT' and img[z,x,3] != 0:
                                overlap += 1
                            if v == 'LEFT' and img[z, depth - 1 - y, 3] != 0:
                                overlap += 1
                            if v == 'RIGHT' and img[z,y,3] != 0:
                                overlap += 1
                            if v == 'TOP' and img[y, x,3] != 0:
                                overlap += 1
                            if v == 'BOTTOM' and img[depth - 1 - y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = y
                    
                    depth_map[z, width - 1 - x] = max_overlap_idx

                else:
                    depth_map[z, width - 1 - x] = -1

    elif view == 'LEFT': #images['LEFT'][z, depth - 1 - y]
        for z in range (height):
            for y in range (depth):

                if image[z, depth-1-y, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for x in range (width):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'FRONT' and img[z,x,3] != 0:
                                overlap += 1
                            if v == 'BACK' and img[z, width - 1 - x, 3] != 0:
                                overlap += 1
                            if v == 'RIGHT' and img[z,y,3] != 0:
                                overlap += 1
                            if v == 'TOP' and img[y, x,3] != 0:
                                overlap += 1
                            if v == 'BOTTOM' and img[depth - 1 - y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = x
                    
                    depth_map[z, depth-1-y] = max_overlap_idx

                else:
                    depth_map[z, depth-1-y] = -1

    elif view == 'RIGHT':
        for z in range (height):
            for y in range (depth):

                if image[z, y, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for x in range (width-1,0,-1):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'FRONT' and img[z,x,3] != 0:
                                overlap += 1
                            if v == 'BACK' and img[z, width - 1 - x, 3] != 0:
                                overlap += 1
                            if v == 'LEFT' and img[z,depth-1-y,3] != 0:
                                overlap += 1
                            if v == 'TOP' and img[y, x,3] != 0:
                                overlap += 1
                            if v == 'BOTTOM' and img[depth - 1 - y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = x
                    
                    depth_map[z, y] = max_overlap_idx

                else:
                    depth_map[z, y] = -1

    elif view == 'TOP':
        # images['TOP'][y, x]
        for x in range (width):
            for y in range (depth):

                if image[y, x, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for z in range (height-1,0,-1):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'FRONT' and img[z,x,3] != 0:
                                overlap += 1
                            if v == 'BACK' and img[z, width - 1 - x, 3] != 0:
                                overlap += 1
                            if v == 'LEFT' and img[z, depth - 1 - y, 3] != 0:
                                overlap += 1
                            if v == 'RIGHT' and img[z,y,3] != 0:
                                overlap += 1
                            if v == 'BOTTOM' and img[depth - 1 - y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = z
                    
                    depth_map[y, x] = max_overlap_idx

                else:
                    depth_map[y, x] = -1 # transparent pixel, skip it when merging
    
    elif view == 'BOTTOM':
        # images['BOTTOM'][depth - 1 - y, x]
        for x in range (width):
            for y in range (depth):

                if image[depth - 1 - y, x, 3] != 0:

                    max_overlap = -1
                    max_overlap_idx = -1

                    # compare each pixel in the image to all heights 
                    for z in range (height):

                        overlap = 0

                        for v, img in other_images:
                            if v == 'FRONT' and img[z,x,3] != 0:
                                overlap += 1
                            if v == 'BACK' and img[z, width - 1 - x, 3] != 0:
                                overlap += 1
                            if v == 'LEFT' and img[z, depth - 1 - y, 3] != 0:
                                overlap += 1
                            if v == 'RIGHT' and img[z,y,3] != 0:
                                overlap += 1
                            if v == 'TOP' and img[y, x,3] != 0:
                                overlap += 1


                        if max_overlap < overlap:
                            max_overlap = overlap
                            max_overlap_idx = z
                    
                    depth_map[depth - 1 - y, x] = max_overlap_idx

                else:
                    depth_map[depth - 1 - y, x] = -1 # transparent pixel, skip it when merging

    return depth_map

def sobel(image):
    sobel_x = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ])

    sobel_y = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ])

    h, w = image.shape
    gx = np.zeros((h, w))
    gy = np.zeros((h, w))

    padded = np.pad(image, pad_width=1, mode='edge')

    for y in range(1, h + 1):
        for x in range(1, w + 1):
            region = padded[y-1:y+2, x-1:x+2]
            gx[y-1, x-1] = np.sum(region * sobel_x)
            gy[y-1, x-1] = np.sum(region * sobel_y)

    grad_mag = np.sqrt(gx**2 + gy**2)
    return grad_mag, gx, gy

def connected_components(mask, min_size=5):
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    output_mask = np.zeros_like(mask, dtype=bool)
    
    for y in range(h):
        for x in range(w):
            if mask[y, x] and not visited[y, x]:
                queue = deque()
                queue.append((y, x))
                region_pixels = []

                while queue:
                    cy, cx = queue.popleft()
                    if (0 <= cy < h and 0 <= cx < w and
                        mask[cy, cx] and not visited[cy, cx]):
                        visited[cy, cx] = True
                        region_pixels.append((cy, cx))
                        queue.extend([
                            (cy-1, cx), (cy+1, cx),
                            (cy, cx-1), (cy, cx+1)
                        ])
                
                if len(region_pixels) >= min_size:
                    for py, px in region_pixels:
                        output_mask[py, px] = True

    return output_mask

def estimate_using_gradients(view, image, curr_depth_map, width, height, depth, intensity_threshold=1.0, concavity_depth=0.5, factor = 1, min_region_size=5, keep_concave_regions=True):
    gray = np.mean(image[:, :, :3], axis=2)
    h, w = gray.shape
    grad_mag, gx, gy = sobel(gray)

    alpha = image[:, :, 3]
    object_mask = alpha > 0.1

    flipped_mags = np.zeros_like(grad_mag)
    flipped_mags[object_mask] = 1.0 - grad_mag[object_mask]

    concavity_candidates = (flipped_mags < intensity_threshold) & (flipped_mags > 0.0) & (object_mask)
    
    valid_regions = connected_components(concavity_candidates, min_size=min_region_size)
    
    depth_map = curr_depth_map.astype(np.float32)

    for y in range(h):
        for x in range(w):
            intensity = gray[y, x]
            if valid_regions[y, x]:
                if keep_concave_regions:
                    multiplier = (1 * concavity_depth * (1 - intensity * factor))

                    if view == 'FRONT':
                        depth_map[y, x] = curr_depth_map[y, x] + depth*multiplier
                    elif view == 'BACK':
                        depth_map[y, x] = curr_depth_map[y, x] - depth*multiplier
                    elif view == 'LEFT':
                        depth_map[y, x] = curr_depth_map[y, x] + width*multiplier
                    elif view == 'RIGHT':
                        depth_map[y, x] = curr_depth_map[y, x] - width*multiplier
                    elif view == 'TOP':
                        depth_map[y, x] = curr_depth_map[y, x] - height*multiplier
                    elif view == 'BOTTOM':
                        depth_map[y, x] = curr_depth_map[y, x] + height*multiplier

                else:
                    depth_map[y, x] = -1

    final = depth_map.astype(np.int32)
    return final

'''
    just join all the maps into the final grid, use the images for colors
'''
def intersect_maps(depth_maps, images, width, height, depth):
    voxel_grid = VoxelGrid.VoxelGrid(width, height, depth)
    colors = np.zeros((width, height, depth, 4), dtype=float)

    for x in range (width):
        for z in range (height):
            for y in range (depth):

                for view, dmap in depth_maps.items():

                    #front view
                    if view == 'FRONT' and dmap[z,x] != -1:
                        colors[x, dmap[z, x], z] = images['FRONT'][z, x]
                    #back view
                    elif view == 'BACK' and dmap[z,width-1-x] != -1:
                        colors[x, dmap[z, width - 1 - x], z] = images['BACK'][z, width - 1 - x]
                    #left view
                    elif view == 'LEFT' and dmap[z,depth-1-y] != -1:
                        colors[dmap[z, depth - 1 - y], y, z] = images['LEFT'][z, depth - 1 - y]
                    #right view
                    elif view == 'RIGHT' and dmap[z,y] != -1:
                        colors[dmap[z, y], y, z] = images['RIGHT'][z, y]
                    #top view
                    elif view == 'TOP' and dmap[y,x] != -1:
                        colors[x, y, dmap[y, x]] = images['TOP'][y, x]
                    #bottom view
                    elif view == 'BOTTOM' and dmap[depth-1-y,x] != -1:
                        colors[x, y, dmap[depth - 1 - y, x]] = images['BOTTOM'][depth - 1 - y, x]

    voxel_grid.colors = colors
    return voxel_grid

def generate_final_grid(images, width, height, depth, intensity_threshold, concavity_depth, factor, min_region_size, keep_concave_regions):

    depth_maps = {}

    for view, image in images.items():
        other_images = [(v, img) for v, img in images.items() if v != view]

        curr_depth_map = calculate_depth(view, image, other_images, width, height, depth)

        final_depth_map = estimate_using_gradients(view, image, curr_depth_map, width, height, depth, intensity_threshold, concavity_depth, factor, min_region_size, keep_concave_regions)

        depth_maps[view] = final_depth_map

    grid = intersect_maps(depth_maps, images, width, height, depth)

    return grid
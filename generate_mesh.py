import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

def linear_to_srgb(c):
    result = np.where(
        c <= 0.0031308,
        12.92 * c,
        1.055 * (c ** (1 / 2.4)) - 0.055
    )
    return tuple(result[:3])

def srgb_to_linear(c):
    c = c / 255.0 if c.max() > 1.0 else c  
    result = np.where(
        c <= 0.04045,
        c / 12.92,
        ((c + 0.055) / 1.055) ** 2.4
    )
    return tuple(result[:3])

def color_key(c):
    return tuple(np.round(c[:3], 4))

def add_cube(bm, location, size, material_index):
    before_faces = set(bm.faces)
    ret = bmesh.ops.create_cube(bm, size=size, matrix=Matrix.Translation(location))
    new_faces = set(bm.faces) - before_faces

    for face in new_faces:
        face.material_index = material_index

def center_object_to_grid(obj, grid_size):
    center = (grid_size - 1) / 2.0  
    offset = (-center, -center, -center)

    bpy.ops.object.mode_set(mode='OBJECT')
    
    for v in obj.data.vertices:
        v.co.x += offset[0]
        v.co.y += offset[1]
        v.co.z += offset[2]
    
    obj.location = (0, 0, 0)

def generate_mesh_from_grid(colors, voxel_size=1.0, remove_gamma_correction=True, obj_name="VoxelObject", mesh_name="VoxelMesh"):
    remove_existing_mesh(obj_name)
    
    width, height, depth, _ = colors.shape
    print("size of colors: " + str(width) + str(height) + str(depth))

    mesh = bpy.data.meshes.new(mesh_name)
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    bm = bmesh.new()

    obj.data.materials.clear()

    unique_colors = np.unique(colors.reshape(-1, 4), axis=0)
    color_to_index = {}
    materials = []

    for i, c in enumerate(unique_colors):
        color = c

        if remove_gamma_correction:
            color = srgb_to_linear(c[:3])

        r, g, b = color
        
        mat = bpy.data.materials.new(name=f"Mat_{i}")
        mat.use_nodes = False  
        mat.diffuse_color = (r, g, b, 1) 
        
        obj.data.materials.append(mat)
        color_to_index[color_key(color)] = i
        materials.append(mat)

    # add cube meshes to obj
    for x in range (width):
        for y in range (height):
            for z in range (depth):
                color = colors[x, y, z]
                if color[3] == 0:
                    continue

                material_index = color_to_index[color_key(srgb_to_linear(color))]
                add_cube(bm, Vector((x * 1.0 * voxel_size, y * 1.0 * voxel_size, z * 1.0 * voxel_size)), voxel_size, material_index)

    bm.to_mesh(mesh)
    bm.free()

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    center_object_to_grid(obj, width)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    print("obj type: ")
    print(obj.type)

    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def remove_existing_mesh(name="VoxelObject"):
    obj_name = name
    if obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        bpy.data.objects.remove(obj, do_unlink=True)
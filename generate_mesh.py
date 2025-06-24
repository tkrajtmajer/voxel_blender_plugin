"""
This module generates the voxel model as an object in the Blender viewport.
"""
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

def srgb_to_linear(c):
    """Convert sRGB values to linear RGB, important for displaying the right colors in Blender 
    for comparison.

    Args:
        c: converted color value
    """
    c = c / 255.0 if c.max() > 1.0 else c  
    result = np.where(
        c <= 0.04045,
        c / 12.92,
        ((c + 0.055) / 1.055) ** 2.4
    )
    return tuple(result[:3])

def add_cube(bm, location, size, material_index):
    """Add a voxel as a cube mesh at the specified location, with the given size and material that 
    determines the voxel color.

    Args:
        bm: Mesh to add cube geometry to (voxel object mesh)
        location: Location of cube placement
        size (float): Voxel size
        material_index: Index of material that is assigned to this cube; 
        unique materials are precomputed
    """
    before_faces = set(bm.faces)
    bmesh.ops.create_cube(bm, size=size, matrix=Matrix.Translation(location))
    new_faces = set(bm.faces) - before_faces

    for face in new_faces:
        face.material_index = material_index

def center_object_to_grid(obj, grid_size):
    """
    After computing the object mesh, center the object at position 0,0,0 in world space.
    """
    center = (grid_size - 1) / 2.0
    offset = (-center, -center, -center)

    bpy.ops.object.mode_set(mode='OBJECT')

    for v in obj.data.vertices:
        v.co.x += offset[0]
        v.co.y += offset[1]
        v.co.z += offset[2]

    obj.location = (0, 0, 0)

def generate_mesh_from_grid(colors,
                            voxel_size=1.0,
                            remove_gamma_correction=True,
                            obj_name="VoxelObject",
                            mesh_name="VoxelMesh"):

    """Generates the voxel mesh from the 3D colors array.

    Args:
        colors: Voxel grid
        voxel_size (float, optional): Size of voxels (cubes in the mesh). Defaults to 1.0.
        remove_gamma_correction (bool, optional): Use sRGB to RGB conversion. Defaults to True.
        obj_name (str, optional): Name of generated object. Defaults to "VoxelObject".
        mesh_name (str, optional): Name of generated mesh. Defaults to "VoxelMesh".

    Returns:
        Generated voxel object.
    """
    remove_existing_mesh(obj_name)

    width, height, depth, _ = colors.shape

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
        color_to_index[tuple(np.round(color[:3], 4))] = i
        materials.append(mat)

    # add cube meshes to obj
    for x in range (width):
        for y in range (height):
            for z in range (depth):
                color = colors[x, y, z]
                if color[3] == 0:
                    continue

                material_index = color_to_index[tuple(np.round((srgb_to_linear(color))[:3], 4))]
                add_cube(bm,
                        Vector((x * 1.0 * voxel_size, y * 1.0 * voxel_size, z * 1.0 * voxel_size)),
                        voxel_size,
                        material_index)

    bm.to_mesh(mesh)
    bm.free()

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    center_object_to_grid(obj, width)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')\

    # clean up
    bpy.ops.mesh.remove_doubles(threshold=0.001)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj

def remove_existing_mesh(name="VoxelObject"):
    """
    Remove object and mesh geometry.
    """
    obj_name = name
    if obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        bpy.data.objects.remove(obj, do_unlink=True)

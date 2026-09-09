import bpy
import bmesh
from mathutils import Vector, Euler

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['AnimalArmature']
mesh = bpy.data.objects['ShibaInu']

# Check materials
mat_black = bpy.data.materials.get("Black2")
mat_fur_light = bpy.data.materials.get("Main_Light2")
mat_fur = bpy.data.materials.get("Main2")

print("Materials found:", mat_black.name, mat_fur_light.name, mat_fur.name)

import bpy
import math
import mathutils

# Open the Shiba blend file
bpy.ops.wm.open_mainfile(filepath='blender_src/ShibaInu.blend')

arm = bpy.data.objects['AnimalArmature']
mesh = bpy.data.objects['ShibaInu']

# Switch to Happy_TongueWag action at frame 10 (celebration pose with head up)
action = bpy.data.actions.get('Happy_TongueWag')
arm.animation_data.action = action
bpy.context.scene.frame_set(10)
bpy.context.view_layer.update()

pb_jaw = arm.pose.bones['Jaw']
pb_head = arm.pose.bones['Head']

# In model space, where is the mouth cavity between snout and jaw?
# Snout bottom is at Z ~ 2.28, Jaw top is at Z ~ 2.18
# Center of ball: Y ~ -2.40, Z ~ 2.26, X ~ 0.0
# Radius of ball in blender units: ball radius in godot is 0.08m / 0.33 scale = 0.242 blender units!

# Create a test tennis ball in blender
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.242, location=(0, -2.40, 2.26))
ball = bpy.context.active_object
ball.name = "TestBall"

# Tennis ball yellow material
mat = bpy.data.materials.new(name="BallMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.85, 0.95, 0.15, 1.0)
bsdf.inputs["Roughness"].default_value = 0.4
ball.data.materials.append(mat)

# Setup camera for side view and 3/4 view
cam = bpy.data.objects.get('Camera')
if not cam:
    cam_data = bpy.data.cameras.new('Camera')
    cam = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Set render settings
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.film_transparent = False

# Light
light = bpy.data.objects.get('Light')
if not light:
    light_data = bpy.data.lights.new('Light', 'SUN')
    light = bpy.data.objects.new('Light', light_data)
    bpy.context.scene.collection.objects.link(light)
light.data.energy = 3.0

out_dir = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860"

# 1. Side profile view
cam.location = (2.2, -2.3, 2.2)
cam.rotation_euler = (math.radians(85), 0, math.radians(90))
bpy.context.scene.render.filepath = out_dir + "/test_mouth_ball_side.png"
bpy.ops.render.render(write_still=True)
print("Rendered test_mouth_ball_side.png")

# 2. 3/4 perspective view
cam.location = (1.6, -3.4, 2.7)
cam.rotation_euler = (math.radians(65), 0, math.radians(35))
bpy.context.scene.render.filepath = out_dir + "/test_mouth_ball_34.png"
bpy.ops.render.render(write_still=True)
print("Rendered test_mouth_ball_34.png")

# Now compute the exact local offset relative to pb_jaw:
jaw_world_mat = arm.matrix_world @ pb_jaw.matrix
local_offset_jaw = jaw_world_mat.inverted() @ mathutils.Vector((0, -2.40, 2.26))
print("Computed local offset in Jaw space:", local_offset_jaw)

# And relative to pb_head:
head_world_mat = arm.matrix_world @ pb_head.matrix
local_offset_head = head_world_mat.inverted() @ mathutils.Vector((0, -2.40, 2.26))
print("Computed local offset in Head space:", local_offset_head)

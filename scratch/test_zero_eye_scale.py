import bpy
from mathutils import Vector, Euler
import math

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['AnimalArmature']
bpy.context.view_layer.objects.active = arm

# Remove all actions keyframes on Eye.L and Eye.R, set scale to 0.0001
for act in bpy.data.actions:
    arm.animation_data.action = act
    bpy.ops.object.mode_set(mode='POSE')
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        if act.name == "Happy_TongueWag":
            arm.pose.bones["Eye.L"].scale = Vector((0.0001, 0.0001, 0.0001))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].scale = Vector((0.0001, 0.0001, 0.0001))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
    bpy.ops.object.mode_set(mode='OBJECT')

arm.animation_data.action = bpy.data.actions["Happy_TongueWag"]

# Setup lighting & camera
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 640

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.16, 0.18, 0.22, 1.0)

sun = bpy.data.lights.new(name="Sun", type='SUN')
sun.energy = 4.2
sun.color = (1.0, 0.98, 0.93)
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(45), math.radians(-25), math.radians(40)), 'XYZ')

fill = bpy.data.lights.new(name="Fill", type='POINT')
fill.energy = 400.0
fill.color = (0.75, 0.88, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-4.0, -4.0, 4.0))

cam = bpy.data.cameras.new("Cam")
cam.lens = 72
cam_obj = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = Vector((-1.6, -4.4, 2.6))
target_face = Vector((0.0, -2.3, 2.45))
cam_obj.rotation_euler = (target_face - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

scene.frame_set(10)
out_img = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_zero_eye_test.png"
scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print("Rendered:", out_img)

import bpy
import math
from mathutils import Vector, Euler

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("AnimalArmature")
act = bpy.data.actions.get("Happy_TongueWag")
if arm and act:
    arm.animation_data.action = act
    print("Set active action to Happy_TongueWag")

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 640

for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

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

cam = bpy.data.cameras.new("SquintCam")
cam.lens = 70
cam_obj = bpy.data.objects.new("SquintCam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Shot 1: Face Closeup
cam_obj.location = Vector((-1.6, -4.4, 2.6))
target_face = Vector((0.0, -2.3, 2.45))
cam_obj.rotation_euler = (target_face - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(10)
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_squint_smile_closeup.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_squint_smile_closeup.png")

# Shot 2: Full Body 3/4
cam.lens = 45
cam_obj.location = Vector((-4.8, -5.2, 3.2))
target_body = Vector((0.0, -1.0, 1.5))
cam_obj.rotation_euler = (target_body - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(10)
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_squint_smile_full.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_squint_smile_full.png")

for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

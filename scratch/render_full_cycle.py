import bpy
import math
from mathutils import Vector, Euler

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 640

# Setup studio lighting
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.15, 0.17, 0.20, 1.0)

sun = bpy.data.lights.new(name="Sun", type='SUN')
sun.energy = 4.0
sun.color = (1.0, 0.98, 0.92)
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(45), math.radians(-30), math.radians(35)), 'XYZ')

fill = bpy.data.lights.new(name="Fill", type='POINT')
fill.energy = 350.0
fill.color = (0.7, 0.85, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-2.5, -4.0, 3.5))

cam = bpy.data.cameras.new("CycleCam")
cam.lens = 50
cam_obj = bpy.data.objects.new("CycleCam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Full dog perspective: from front-left at a slight elevated angle so we see head, tongue, and wagging tail all together!
cam_obj.location = Vector((-4.0, -3.2, 3.2))
target = Vector((0.0, -0.6, 1.6))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

# Render 4 key frames across the 40-frame loop
frames = [0, 10, 20, 30]
for idx, f in enumerate(frames):
    scene.frame_set(f)
    out_path = f"/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_cycle_frame_{f}.png"
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered frame {f}")

# Also render from rear-right angle to show full tail wag sweep
cam_obj.location = Vector((3.5, 1.5, 3.2))
target_tail = Vector((0.0, -0.6, 1.8))
cam_obj.rotation_euler = (target_tail - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(10) # Max tail wag
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_tail_wag_full.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_tail_wag_full.png")

for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

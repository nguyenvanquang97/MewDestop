import bpy
import math
from mathutils import Vector, Euler
import os
from PIL import Image

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 640
scene.render.resolution_y = 480

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
fill.energy = 350.0
fill.color = (0.75, 0.88, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-4.0, -4.0, 4.0))

cam = bpy.data.cameras.new("GifCam")
cam.lens = 42
cam_obj = bpy.data.objects.new("GifCam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Position to see full dog, head, tongue and tail
cam_obj.location = Vector((-4.8, -4.8, 3.0))
target = Vector((0.0, -0.9, 1.6))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

tmp_dir = "/tmp/shiba_frames"
os.makedirs(tmp_dir, exist_ok=True)

images = []
# 20 frames for smooth animated loop
for f in range(0, 40, 2):
    scene.frame_set(f)
    frame_path = f"{tmp_dir}/frame_{f:02d}.png"
    scene.render.filepath = frame_path
    bpy.ops.render.render(write_still=True)
    images.append(Image.open(frame_path))

gif_path = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_animation.gif"
images[0].save(
    gif_path,
    save_all=True,
    append_images=images[1:],
    duration=65, # ~15 fps
    loop=0
)
print("Saved GIF successfully:", gif_path)

for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

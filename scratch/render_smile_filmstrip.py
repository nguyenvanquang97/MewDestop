import bpy
import math
from mathutils import Vector, Euler
import os

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
fill.energy = 380.0
fill.color = (0.75, 0.88, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-4.0, -4.0, 4.0))

cam = bpy.data.cameras.new("Cam")
cam.lens = 52
cam_obj = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = Vector((-3.2, -4.8, 2.9))
target = Vector((0.0, -1.8, 2.2))
cam_obj.rotation_euler = (target - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

tmp_dir = "/tmp/shiba_smile_frames"
os.makedirs(tmp_dir, exist_ok=True)

for f in [0, 10, 20, 30]:
    scene.frame_set(f)
    scene.render.filepath = f"{tmp_dir}/frame_{f:02d}.png"
    bpy.ops.render.render(write_still=True)

for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

import bpy
import math
from mathutils import Vector, Euler

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

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

# Studio Sun
sun = bpy.data.lights.new(name="Sun", type='SUN')
sun.energy = 4.2
sun.color = (1.0, 0.98, 0.93)
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(45), math.radians(-25), math.radians(40)), 'XYZ')

# Studio Fill
fill = bpy.data.lights.new(name="Fill", type='POINT')
fill.energy = 400.0
fill.color = (0.75, 0.88, 1.0)
fill_obj = bpy.data.objects.new("Fill", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-4.0, -4.0, 4.0))

cam = bpy.data.cameras.new("PerfectCam")
cam.lens = 45 # natural perspective, no extreme distortion
cam_obj = bpy.data.objects.new("PerfectCam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Shot 1: Full body 3/4 front view (Framed at distance 6.5m)
cam_obj.location = Vector((-4.8, -5.2, 3.2))
target_body = Vector((0.0, -1.0, 1.5))
cam_obj.rotation_euler = (target_body - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(10)
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_full_34.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_full_34.png")

# Shot 2: Full body side view showing wagging tail & tongue
cam_obj.location = Vector((5.2, -1.0, 3.2))
target_center = Vector((0.0, -1.0, 1.6))
cam_obj.rotation_euler = (target_center - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(7)
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_full_side.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_full_side.png")

# Shot 3: Expressive Face Close-up
cam.lens = 70
cam_obj.location = Vector((-1.6, -4.5, 2.6))
target_face = Vector((0.0, -2.4, 2.35))
cam_obj.rotation_euler = (target_face - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(10)
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_face_refined.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_face_refined.png")

for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

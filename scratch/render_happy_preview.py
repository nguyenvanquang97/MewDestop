import bpy
import math
from mathutils import Vector, Euler

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Clear existing cameras/lights
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.film_transparent = False

# Background color: clean neutral studio grey
world = scene.world or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.18, 0.20, 0.24, 1.0)
    bg.inputs["Strength"].default_value = 1.0

# Add Key Light (warm sunlight)
light_data = bpy.data.lights.new(name="SunLight", type='SUN')
light_data.energy = 3.5
light_data.color = (1.0, 0.96, 0.90)
sun_obj = bpy.data.objects.new("SunLight", light_data)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(50), math.radians(-25), math.radians(40)), 'XYZ')

# Add Fill Light (cool blueish)
fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
fill_data.energy = 250.0
fill_data.color = (0.75, 0.85, 1.0)
fill_obj = bpy.data.objects.new("FillLight", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.location = Vector((-3.0, -3.0, 4.0))

# Create Camera
cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 65
cam_obj = bpy.data.objects.new("PreviewCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Shot 1: Front 3/4 perspective (shows face, tongue, and body)
cam_obj.location = Vector((-2.8, -4.8, 3.2))
# Point camera towards head/chest (0, -1.5, 2.0)
target = Vector((0.0, -1.5, 2.0))
dir_vec = target - cam_obj.location
rot_quat = dir_vec.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

scene.frame_set(10) # Mid-wag & mid-pant
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_front_quarter.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_front_quarter.png")

# Shot 2: Close-up on cute face & tongue
cam_obj.location = Vector((-1.1, -3.8, 2.7))
target_head = Vector((0.0, -2.4, 2.4))
cam_obj.rotation_euler = (target_head - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_closeup_face.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_closeup_face.png")

# Shot 3: Side-rear perspective showing tail wagging!
cam_obj.location = Vector((3.5, 1.5, 3.0))
target_tail = Vector((0.0, -0.5, 1.8))
cam_obj.rotation_euler = (target_tail - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()
scene.frame_set(7) # Tail fully wagged
scene.render.filepath = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_happy_side_wag.png"
bpy.ops.render.render(write_still=True)
print("Rendered shiba_happy_side_wag.png")

# Remove temporary camera/lights before saving
for o in [sun_obj, fill_obj, cam_obj]:
    bpy.data.objects.remove(o, do_unlink=True)

import math
import bpy
import bmesh
from mathutils import Vector, Euler

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['AnimalArmature']
mesh = bpy.data.objects['ShibaInu']

# Check materials
mat_black = mesh.data.materials.get("Black2")
mat_light = mesh.data.materials.get("Main_Light2")

# Create a test object for the closed eye lines
for o in list(bpy.data.objects):
    if o.name == "Test_Smile_Eyes":
        bpy.data.objects.remove(o, do_unlink=True)

bm = bmesh.new()

# Create a clean, elegant smiling closed eyelid curve (⌒)
# A soft arc that follows the natural eye contour:
# Inner corner -> graceful smiling arc -> outer corner
def create_eye_crease(is_left=True):
    sign = -1.0 if is_left else 1.0
    
    # 7 points along a smooth, gentle smiling curve
    # Inner corner is at X=0.165, Z=2.685
    # Outer corner is at X=0.275, Z=2.705
    # Mid apex curves smoothly up to Z=2.725
    pts = [
        (sign * 0.165, -2.080, 2.685),
        (sign * 0.185, -2.095, 2.705),
        (sign * 0.205, -2.105, 2.720),
        (sign * 0.225, -2.110, 2.725), # center apex
        (sign * 0.245, -2.100, 2.722),
        (sign * 0.265, -2.080, 2.712),
        (sign * 0.280, -2.050, 2.695), # outer corner slightly downturned
    ]
    
    line_thickness = 0.012
    v_top = []
    v_bot = []
    
    for (x, y, z) in pts:
        # Offset slightly along surface normal (forward-outward)
        # Face normal in eye region is roughly (sign*0.5, -0.8, 0.3) normalized
        n = Vector((sign * 0.35, -0.85, 0.40)).normalized()
        offset_pos = Vector((x, y, z)) + n * 0.005
        
        # Tangent along curve, binormal perpendicular to line
        up_vec = Vector((0.0, -0.4, 0.9)).normalized()
        
        vt = bm.verts.new(offset_pos + up_vec * (line_thickness * 0.5))
        vb = bm.verts.new(offset_pos - up_vec * (line_thickness * 0.5))
        v_top.append(vt)
        v_bot.append(vb)
    
    for i in range(len(pts) - 1):
        f = bm.faces.new((v_bot[i], v_bot[i+1], v_top[i+1], v_top[i]))
        f.material_index = 0 # Black2

create_eye_crease(is_left=True)
create_eye_crease(is_left=False)

bm.normal_update()

test_mesh = bpy.data.meshes.new("Test_Smile_Eyes_Mesh")
bm.to_mesh(test_mesh)
bm.free()

test_obj = bpy.data.objects.new("Test_Smile_Eyes", test_mesh)
bpy.context.collection.objects.link(test_obj)
test_obj.data.materials.append(mat_black)

# Parent to Head bone
test_obj.parent = arm
test_obj.parent_type = 'BONE'
test_obj.parent_bone = 'Head'

# Also temporarily hide the open eyes on the mesh by scaling bone Eye.L / Eye.R to 0
arm.animation_data.action = bpy.data.actions["Happy_TongueWag"]
bpy.ops.object.mode_set(mode='POSE')
arm.pose.bones["Eye.L"].scale = Vector((0.001, 0.001, 0.001))
arm.pose.bones["Eye.R"].scale = Vector((0.001, 0.001, 0.001))
bpy.ops.object.mode_set(mode='OBJECT')

print("Created Test_Smile_Eyes and parented to Head bone")

# Setup Camera for quick closeup render
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'):
        bpy.data.objects.remove(o, do_unlink=True)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 960
scene.render.resolution_y = 640

sun = bpy.data.lights.new(name="Sun", type='SUN')
sun.energy = 4.2
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = Euler((math.radians(45), math.radians(-25), math.radians(40)), 'XYZ')

cam = bpy.data.cameras.new("Cam")
cam.lens = 72
cam_obj = bpy.data.objects.new("Cam", cam)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = Vector((-1.6, -4.4, 2.6))
target_face = Vector((0.0, -2.3, 2.45))
cam_obj.rotation_euler = (target_face - cam_obj.location).to_track_quat('-Z', 'Y').to_euler()

scene.frame_set(10)
out_img = "/Users/macbook/.gemini/antigravity-ide/brain/acb36d71-6448-4b9e-a262-8d051bcf2860/shiba_smiling_closed_eyes_test.png"
scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print("Rendered:", out_img)

import bpy
import bmesh
from mathutils import Vector, Quaternion, Euler
import math

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['AnimalArmature']
mesh = bpy.data.objects['ShibaInu']

# 1. Setup Armature Bones:
# Eye_Open.L, Eye_Open.R (controls normal open eyeball)
# Eye_Smile.L, Eye_Smile.R (controls closed smiling crescent eyes)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones

# Rename or recreate Eye.L / Eye.R
for old in ["Eye.L", "Eye.R", "Eye_Open.L", "Eye_Open.R", "Eye_Smile.L", "Eye_Smile.R"]:
    if old in eb:
        eb.remove(eb[old])

# Open eye bones (pivot at center of eyeball)
b_eol = eb.new("Eye_Open.L")
b_eol.head = Vector((-0.224, -2.083, 2.709))
b_eol.tail = Vector((-0.224, -2.183, 2.709))
b_eol.parent = eb["Head"]
b_eol.use_connect = False

b_eor = eb.new("Eye_Open.R")
b_eor.head = Vector((0.224, -2.083, 2.709))
b_eor.tail = Vector((0.224, -2.183, 2.709))
b_eor.parent = eb["Head"]
b_eor.use_connect = False

# Smile eye bones
b_esl = eb.new("Eye_Smile.L")
b_esl.head = Vector((-0.224, -2.083, 2.709))
b_esl.tail = Vector((-0.224, -2.183, 2.709))
b_esl.parent = eb["Head"]
b_esl.use_connect = False

b_esr = eb.new("Eye_Smile.R")
b_esr.head = Vector((0.224, -2.083, 2.709))
b_esr.tail = Vector((0.224, -2.183, 2.709))
b_esr.parent = eb["Head"]
b_esr.use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')

# 2. Re-assign open eye vertices to Eye_Open.L and Eye_Open.R
# Remove old vertex groups if any
for old_vg in ["Eye.L", "Eye.R", "Eye_Open.L", "Eye_Open.R", "Eye_Smile.L", "Eye_Smile.R"]:
    if old_vg in mesh.vertex_groups:
        mesh.vertex_groups.remove(mesh.vertex_groups[old_vg])

vg_eol = mesh.vertex_groups.new(name="Eye_Open.L")
vg_eor = mesh.vertex_groups.new(name="Eye_Open.R")
vg_esl = mesh.vertex_groups.new(name="Eye_Smile.L")
vg_esr = mesh.vertex_groups.new(name="Eye_Smile.R")

for p in mesh.data.polygons:
    if p.material_index in (3, 4, 5): # eye materials
        for vi in p.vertices:
            v = mesh.data.vertices[vi]
            if v.co.x < 0:
                vg_eol.add([vi], 1.0, 'REPLACE')
            else:
                vg_eor.add([vi], 1.0, 'REPLACE')

# 3. Model closed smiling crescent eye geometry (⌒  ⌒)
# Remove old Smiling_Eyes if present
for o in list(bpy.data.objects):
    if o.name.startswith("Smiling_Eyes"):
        bpy.data.objects.remove(o, do_unlink=True)

mat_black = mesh.data.materials.get("Black2")
mat_light = mesh.data.materials.get("Main_Light2")
mat_brown = mesh.data.materials.get("Main2")

bm = bmesh.new()

# Function to build an arched smiling eye crescent (⌒) with eyelid backing
def build_smile_eye(is_left=True):
    sign = -1.0 if is_left else 1.0
    
    # 5 points along the curved eyelid arch (from inner eye corner to outer eye corner)
    # real shiba smiling eye curves UP then drops slightly at outer corner
    arch_pts = [
        # (x, y, z)
        (sign * 0.165, -2.070, 2.685),  # 0: inner corner
        (sign * 0.195, -2.105, 2.725),  # 1: inner curve
        (sign * 0.225, -2.125, 2.740),  # 2: top apex of crescent
        (sign * 0.255, -2.100, 2.715),  # 3: outer curve
        (sign * 0.280, -2.050, 2.665),  # 4: outer corner (cute doge squint downturn!)
    ]
    
    # Create the thick dark smiling line (width along normal)
    # Inner and outer line vertices
    line_w = 0.016
    v_top = []
    v_bot = []
    
    for (x, y, z) in arch_pts:
        # normal roughly pointing forward-up
        v_t = bm.verts.new(Vector((x, y - 0.006, z + line_w * 0.6)))
        v_b = bm.verts.new(Vector((x, y - 0.004, z - line_w * 0.6)))
        v_top.append(v_t)
        v_bot.append(v_b)
    
    # Dark smiling line faces
    for i in range(len(arch_pts) - 1):
        f = bm.faces.new((v_bot[i], v_bot[i+1], v_top[i+1], v_top[i]))
        f.material_index = 0 # Black2
    
    # Eyelid backing underneath (fills the eye socket so it looks like soft closed eyelid fur)
    # Bottom eyelid rim
    v_eyelid_low = [
        bm.verts.new(Vector((sign * 0.180, -2.060, 2.665))),
        bm.verts.new(Vector((sign * 0.225, -2.080, 2.660))),
        bm.verts.new(Vector((sign * 0.265, -2.050, 2.655)))
    ]
    
    # Connect bottom of line to eyelid backing
    f_b1 = bm.faces.new((v_eyelid_low[0], v_bot[1], v_bot[0]))
    f_b2 = bm.faces.new((v_eyelid_low[0], v_eyelid_low[1], v_bot[2], v_bot[1]))
    f_b3 = bm.faces.new((v_eyelid_low[1], v_eyelid_low[2], v_bot[3], v_bot[2]))
    f_b4 = bm.faces.new((v_eyelid_low[2], v_bot[4], v_bot[3]))
    for f in [f_b1, f_b2, f_b3, f_b4]:
        f.material_index = 1 # Main_Light2 (white cheek fur)

build_smile_eye(is_left=True)
build_smile_eye(is_left=False)

bm.normal_update()

smile_mesh_data = bpy.data.meshes.new("Smiling_Eyes_Data")
bm.to_mesh(smile_mesh_data)
bm.free()

smile_obj = bpy.data.objects.new("Smiling_Eyes", smile_mesh_data)
bpy.context.collection.objects.link(smile_obj)
smile_obj.data.materials.append(mat_black)
smile_obj.data.materials.append(mat_light)

# Add Armature modifier and vertex groups to Smiling_Eyes
mod = smile_obj.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm

vg_s_l = smile_obj.vertex_groups.new(name="Eye_Smile.L")
vg_s_r = smile_obj.vertex_groups.new(name="Eye_Smile.R")

for v in smile_obj.data.vertices:
    if v.co.x < 0:
        vg_s_l.add([v.index], 1.0, 'REPLACE')
    else:
        vg_s_r.add([v.index], 1.0, 'REPLACE')

# Join Smiling_Eyes into ShibaInu mesh so it's 1 single clean skinned mesh!
bpy.ops.object.select_all(action='DESELECT')
smile_obj.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print("Joined Smiling_Eyes into ShibaInu mesh!")

# 4. Animate Eye_Open vs Eye_Smile across all actions:
# In Happy_TongueWag:
#   Eye_Open -> scale = (0.001, 0.001, 0.001) [DISAPPEARS]
#   Eye_Smile -> scale = (1.0, 1.0, 1.0) [APPEARS AS CLOSED HAPPY ARCS ^_^]
# In all other actions:
#   Eye_Open -> scale = (1.0, 1.0, 1.0) [NORMAL OPEN EYES]
#   Eye_Smile -> scale = (0.001, 0.001, 0.001) [HIDDEN]
bpy.context.view_layer.objects.active = arm

for act in bpy.data.actions:
    arm.animation_data.action = act
    bpy.ops.object.mode_set(mode='POSE')
    
    if act.name == "Happy_TongueWag":
        for f in range(41):
            # Open eyes hide completely
            arm.pose.bones["Eye_Open.L"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Eye_Open.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye_Open.R"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Eye_Open.R"].keyframe_insert(data_path="scale", frame=f)
            
            # Smiling closed eyes appear with subtle cute squinting bounce
            t = (f / 40.0) * math.tau
            squint_bounce = 1.0 + abs(math.sin(t * 4.0)) * 0.04
            arm.pose.bones["Eye_Smile.L"].scale = Vector((1.0, 1.0, squint_bounce))
            arm.pose.bones["Eye_Smile.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye_Smile.R"].scale = Vector((1.0, 1.0, squint_bounce))
            arm.pose.bones["Eye_Smile.R"].keyframe_insert(data_path="scale", frame=f)
    else:
        for f in [int(act.frame_range[0]), int(act.frame_range[1])]:
            # Open eyes normal
            arm.pose.bones["Eye_Open.L"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye_Open.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye_Open.R"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye_Open.R"].keyframe_insert(data_path="scale", frame=f)
            
            # Smiling eyes hidden
            arm.pose.bones["Eye_Smile.L"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Eye_Smile.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye_Smile.R"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Eye_Smile.R"].keyframe_insert(data_path="scale", frame=f)
            
    bpy.ops.object.mode_set(mode='OBJECT')

print("Configured closed smiling eyes animation!")

# Set default action
arm.animation_data.action = bpy.data.actions["Happy_TongueWag"]

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blend file successfully!")

# Export glTF GLB
out_glb = "assets/models/shiba/ShibaInu.glb"
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    export_animations=True,
    export_nla_strips=True,
    export_anim_single_armature=True,
    export_current_frame=False
)
print("Exported GLB successfully!")

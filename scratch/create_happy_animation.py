import bpy
import math
from mathutils import Vector, Quaternion, Euler, Matrix
import bmesh

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Clean up any previous test objects
for o in list(bpy.data.objects):
    if o.name.startswith("Icosphere") or o.name.startswith("Tongue_Mesh"):
        bpy.data.objects.remove(o, do_unlink=True)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")

bpy.context.view_layer.objects.active = arm

# 1. Setup Tongue bone in Armature
bpy.ops.object.mode_set(mode='EDIT')
edit_bones = arm.data.edit_bones

# Mouth opening is at Z=2.37, Y=-2.36
tongue_root = Vector((0.0, -2.32, 2.37))
tongue_tip = Vector((0.02, -2.56, 2.22)) # slightly playful right slant

if "Tongue" not in edit_bones:
    tb = edit_bones.new("Tongue")
    tb.head = tongue_root
    tb.tail = tongue_tip
    tb.parent = edit_bones["Head"]
    tb.use_connect = False
else:
    tb = edit_bones["Tongue"]
    tb.head = tongue_root
    tb.tail = tongue_tip

bpy.ops.object.mode_set(mode='OBJECT')

# 2. Setup Pink_Tongue material with cute shine
mat_name = "Pink_Tongue"
mat = bpy.data.materials.get(mat_name)
if not mat:
    mat = bpy.data.materials.new(name=mat_name)
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.96, 0.38, 0.50, 1.0) # warm lively pink
    bsdf.inputs["Roughness"].default_value = 0.18 # wet shine
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.6

# 3. Model stylized, smooth low-poly tongue
bm = bmesh.new()

# Cross sections along tongue length (from inside mouth to outside flopping down)
profiles = [
    # (y, z, width, thick, x_offset)
    (-2.30, 2.37, 0.07, 0.020, 0.000),  # inside mouth root
    (-2.36, 2.37, 0.10, 0.024, 0.005),  # at mouth slit
    (-2.43, 2.35, 0.13, 0.025, 0.012),  # extending out
    (-2.50, 2.30, 0.13, 0.023, 0.018),  # curving down
    (-2.56, 2.23, 0.10, 0.018, 0.022),  # lower scoop
    (-2.60, 2.16, 0.05, 0.010, 0.025),  # rounded soft tip
]

rings = []
for (y, z, w, th, xo) in profiles:
    # 4 vertices per ring: Top-Left, Top-Right, Bottom-Right, Bottom-Left
    v_tl = bm.verts.new(Vector((-w * 0.5 + xo, y, z + th * 0.5)))
    v_tr = bm.verts.new(Vector((w * 0.5 + xo, y, z + th * 0.5)))
    v_br = bm.verts.new(Vector((w * 0.42 + xo, y, z - th * 0.5)))
    v_bl = bm.verts.new(Vector((-w * 0.42 + xo, y, z - th * 0.5)))
    rings.append((v_tl, v_tr, v_br, v_bl))

# Connect quads between rings
for i in range(len(rings) - 1):
    r1 = rings[i]
    r2 = rings[i+1]
    # Top face
    bm.faces.new((r1[0], r2[0], r2[1], r1[1]))
    # Right face
    bm.faces.new((r1[1], r2[1], r2[2], r1[2]))
    # Bottom face
    bm.faces.new((r1[2], r2[2], r2[3], r1[3]))
    # Left face
    bm.faces.new((r1[3], r2[3], r2[0], r1[0]))

# Cap the tip
tip = rings[-1]
bm.faces.new((tip[0], tip[1], tip[2], tip[3]))

bm.normal_update()

tongue_data = bpy.data.meshes.new("Tongue_MeshData")
bm.to_mesh(tongue_data)
bm.free()

tongue_obj = bpy.data.objects.new("Tongue_Mesh", tongue_data)
bpy.context.collection.objects.link(tongue_obj)
tongue_obj.data.materials.append(mat)

# Bind tongue to Armature with bone Tongue
mod = tongue_obj.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm
vg = tongue_obj.vertex_groups.new(name="Tongue")
vg.add(list(range(len(tongue_obj.data.vertices))), 1.0, 'REPLACE')

if "Tongue" not in mesh.vertex_groups:
    mesh.vertex_groups.new(name="Tongue")

print("Created refined tongue mesh and parented to Armature")

# 4. Animate Happy_TongueWag Action
act_name = "Happy_TongueWag"
act = bpy.data.actions.get(act_name)
if act:
    bpy.data.actions.remove(act)
act = bpy.data.actions.new(name=act_name)
act.use_fake_user = True

arm.animation_data_create()
arm.animation_data.action = act

TOTAL_FRAMES = 40
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = TOTAL_FRAMES

bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones:
    pb.location = Vector((0, 0, 0))
    pb.rotation_quaternion = Quaternion((1, 0, 0, 0))

for f in range(TOTAL_FRAMES + 1):
    t = (f / TOTAL_FRAMES) * math.tau
    
    # 1. TAIL: 3 energetic wag cycles
    wag_phase = t * 3.0
    # Tail1: wags left-right (Z axis) + stands perkily up (X=-14 deg)
    wag1 = math.sin(wag_phase) * math.radians(26.0)
    arm.pose.bones["Tail1"].rotation_quaternion = Euler((math.radians(-14.0), 0.0, wag1), 'XYZ').to_quaternion()
    arm.pose.bones["Tail1"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Tail2: with 0.35 rad delay, wag angle +/-36 deg
    wag2 = math.sin(wag_phase - 0.35) * math.radians(36.0)
    arm.pose.bones["Tail2"].rotation_quaternion = Euler((math.radians(-16.0), 0.0, wag2), 'XYZ').to_quaternion()
    arm.pose.bones["Tail2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Tail3: whip tip with 0.7 rad delay, wag angle +/-48 deg
    wag3 = math.sin(wag_phase - 0.70) * math.radians(48.0)
    arm.pose.bones["Tail3"].rotation_quaternion = Euler((math.radians(-18.0), 0.0, wag3), 'XYZ').to_quaternion()
    arm.pose.bones["Tail3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 2. HEAD & PANTING: 4 quick cheerful breath cycles
    pant_phase = t * 4.0
    pant_bob = math.sin(pant_phase)
    # Head nods slightly up/down, tilted with happy curiosity
    head_pitch = math.radians(7.0) + pant_bob * math.radians(5.0)
    head_tilt = math.sin(t * 2.0) * math.radians(3.5) # cute sideways head tilt
    arm.pose.bones["Head"].rotation_quaternion = Euler((head_pitch, head_tilt, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Head"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    neck_pitch = pant_bob * math.radians(2.8)
    arm.pose.bones["Neck2"].rotation_quaternion = Euler((neck_pitch * 0.5, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Neck3"].rotation_quaternion = Euler((neck_pitch, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 3. TONGUE: playful flop responding to panting
    tongue_flop = math.sin(pant_phase - 0.45) * math.radians(10.0)
    tongue_wiggle = math.sin(wag_phase * 0.5) * math.radians(4.0)
    arm.pose.bones["Tongue"].rotation_quaternion = Euler((tongue_flop, 0.0, tongue_wiggle), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 4. EARS: lively bounce
    ear_twitch_l = math.sin(pant_phase + 0.3) * math.radians(3.5)
    ear_twitch_r = math.sin(pant_phase + 0.1) * math.radians(3.5)
    arm.pose.bones["Ear1.L"].rotation_quaternion = Euler((ear_twitch_l, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.L"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Ear1.R"].rotation_quaternion = Euler((ear_twitch_r, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.R"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 5. BODY: proud chest, cheerful breathing squash
    breath = abs(math.sin(pant_phase)) * 0.028
    arm.pose.bones["Body"].location = Vector((0.0, 0.0, breath))
    arm.pose.bones["Body"].keyframe_insert(data_path="location", frame=f)
    
    # Legs planted
    for leg in ["FrontUpperLeg.L", "FrontUpperLeg.R", "BackLeg.L", "BackLeg.R"]:
        if leg in arm.pose.bones:
            arm.pose.bones[leg].rotation_quaternion = Quaternion((1, 0, 0, 0))
            arm.pose.bones[leg].keyframe_insert(data_path="rotation_quaternion", frame=f)

bpy.ops.object.mode_set(mode='OBJECT')
print("Successfully generated refined Happy_TongueWag!")

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blend file successfully!")

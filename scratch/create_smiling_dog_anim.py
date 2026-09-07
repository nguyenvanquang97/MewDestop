import bpy
import math
from mathutils import Vector, Quaternion, Euler, Matrix
import bmesh

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Remove old tongue mesh/objects
for o in list(bpy.data.objects):
    if o.name.startswith("Tongue_Mesh") or o.name.startswith("Mouth_Cavity") or o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")

bpy.context.view_layer.objects.active = arm

# 1. Setup multi-bone Tongue chain for organic flexibility: Tongue1 -> Tongue2 -> Tongue3
bpy.ops.object.mode_set(mode='EDIT')
edit_bones = arm.data.edit_bones

# Remove single bone Tongue if exists
if "Tongue" in edit_bones:
    edit_bones.remove(edit_bones["Tongue"])

for b_name in ["Tongue1", "Tongue2", "Tongue3"]:
    if b_name not in edit_bones:
        edit_bones.new(b_name)

# Positions for 3-segment flexible tongue
t1 = edit_bones["Tongue1"]
t1.head = Vector((0.0, -2.26, 2.38))
t1.tail = Vector((0.0, -2.38, 2.38))
t1.parent = edit_bones["Head"]
t1.use_connect = False

t2 = edit_bones["Tongue2"]
t2.head = t1.tail
t2.tail = Vector((0.01, -2.48, 2.33))
t2.parent = t1
t2.use_connect = True

t3 = edit_bones["Tongue3"]
t3.head = t2.tail
t3.tail = Vector((0.02, -2.59, 2.22))
t3.parent = t2
t3.use_connect = True

bpy.ops.object.mode_set(mode='OBJECT')

# 2. Materials
# Pink Tongue
mat_tongue = bpy.data.materials.get("Pink_Tongue")
if not mat_tongue:
    mat_tongue = bpy.data.materials.new(name="Pink_Tongue")
bsdf_t = mat_tongue.node_tree.nodes.get("Principled BSDF")
if bsdf_t:
    bsdf_t.inputs["Base Color"].default_value = (0.97, 0.36, 0.48, 1.0)
    bsdf_t.inputs["Roughness"].default_value = 0.15

# Dark Open Mouth Cavity Material (gives the dog an open smiling mouth illusion)
mat_mouth = bpy.data.materials.get("Mouth_Dark")
if not mat_mouth:
    mat_mouth = bpy.data.materials.new(name="Mouth_Dark")
bsdf_m = mat_mouth.node_tree.nodes.get("Principled BSDF")
if bsdf_m:
    bsdf_m.inputs["Base Color"].default_value = (0.12, 0.03, 0.05, 1.0)
    bsdf_m.inputs["Roughness"].default_value = 0.5

# 3. Model stylized smiling open mouth + flexible spoon tongue
bm = bmesh.new()

# Create dark mouth backing / smile slit that sits in the mouth opening
# (gives depth under the tongue so the dog looks like its mouth is happily open)
v_m1 = bm.verts.new(Vector((-0.12, -2.38, 2.42)))
v_m2 = bm.verts.new(Vector((0.12, -2.38, 2.42)))
v_m3 = bm.verts.new(Vector((0.09, -2.35, 2.34)))
v_m4 = bm.verts.new(Vector((-0.09, -2.35, 2.34)))
f_mouth = bm.faces.new((v_m1, v_m2, v_m3, v_m4))
f_mouth.material_index = 1 # Mouth_Dark

# Now create the flexible tongue: 8 rings along length with cute spoon curve
# y, z, width, thickness, x_offset
tongue_profiles = [
    (-2.26, 2.38, 0.08, 0.018, 0.000),  # 0: deep root
    (-2.32, 2.38, 0.11, 0.022, 0.002),  # 1: inside mouth
    (-2.38, 2.38, 0.13, 0.025, 0.005),  # 2: mouth opening
    (-2.44, 2.36, 0.15, 0.025, 0.010),  # 3: broad smiling mid-tongue
    (-2.50, 2.31, 0.15, 0.022, 0.016),  # 4: arching down over lip
    (-2.55, 2.24, 0.13, 0.018, 0.020),  # 5: dangling down
    (-2.60, 2.16, 0.09, 0.013, 0.024),  # 6: tapered scoop
    (-2.63, 2.11, 0.03, 0.006, 0.025),  # 7: rounded tip
]

rings = []
for (y, z, w, th, xo) in tongue_profiles:
    v_tl = bm.verts.new(Vector((-w * 0.5 + xo, y, z + th * 0.5)))
    v_tr = bm.verts.new(Vector((w * 0.5 + xo, y, z + th * 0.5)))
    v_br = bm.verts.new(Vector((w * 0.42 + xo, y, z - th * 0.5)))
    v_bl = bm.verts.new(Vector((-w * 0.42 + xo, y, z - th * 0.5)))
    rings.append((v_tl, v_tr, v_br, v_bl))

for i in range(len(rings) - 1):
    r1 = rings[i]
    r2 = rings[i+1]
    f1 = bm.faces.new((r1[0], r2[0], r2[1], r1[1]))
    f2 = bm.faces.new((r1[1], r2[1], r2[2], r1[2]))
    f3 = bm.faces.new((r1[2], r2[2], r2[3], r1[3]))
    f4 = bm.faces.new((r1[3], r2[3], r2[0], r1[0]))
    for f in [f1, f2, f3, f4]:
        f.material_index = 0 # Pink_Tongue

tip = rings[-1]
f_tip = bm.faces.new((tip[0], tip[1], tip[2], tip[3]))
f_tip.material_index = 0

bm.normal_update()

tongue_data = bpy.data.meshes.new("Tongue_MeshData")
bm.to_mesh(tongue_data)
bm.free()

tongue_obj = bpy.data.objects.new("Tongue_Mesh", tongue_data)
bpy.context.collection.objects.link(tongue_obj)
tongue_obj.data.materials.append(mat_tongue)
tongue_obj.data.materials.append(mat_mouth)

# Armature modifier
mod = tongue_obj.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm

# Vertex weighting across the 3 bones: Tongue1, Tongue2, Tongue3
vg_head = tongue_obj.vertex_groups.new(name="Head")
vg_t1 = tongue_obj.vertex_groups.new(name="Tongue1")
vg_t2 = tongue_obj.vertex_groups.new(name="Tongue2")
vg_t3 = tongue_obj.vertex_groups.new(name="Tongue3")

# Assign weights based on Y coordinate along tongue
for v in tongue_obj.data.vertices:
    y = v.co.y
    if y > -2.35:
        # Mouth backing & root -> Head & Tongue1
        vg_head.add([v.index], max(0.0, min(1.0, (y - (-2.30)) / 0.05)), 'REPLACE')
        vg_t1.add([v.index], max(0.0, min(1.0, 1.0 - abs(y - (-2.35)) / 0.06)), 'REPLACE')
    elif -2.48 <= y <= -2.35:
        # Mid segment -> Tongue2
        factor = (y - (-2.48)) / (0.13) # 0 at -2.48, 1 at -2.35
        vg_t1.add([v.index], factor * 0.5, 'REPLACE')
        vg_t2.add([v.index], 1.0 - factor * 0.3, 'REPLACE')
    else:
        # Tip segment -> Tongue3
        factor = max(0.0, min(1.0, (y - (-2.63)) / (0.15)))
        vg_t2.add([v.index], factor * 0.6, 'REPLACE')
        vg_t3.add([v.index], 1.0 - factor * 0.4, 'REPLACE')

print("Rigged 3-bone flexible tongue mesh!")

# 4. Animate Happy_TongueWag with dynamic panting smile!
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
    
    # 1. TAIL WAGGING: energetic whip wave (3 cycles)
    wag_phase = t * 3.0
    wag1 = math.sin(wag_phase) * math.radians(28.0)
    arm.pose.bones["Tail1"].rotation_quaternion = Euler((math.radians(-16.0), 0.0, wag1), 'XYZ').to_quaternion()
    arm.pose.bones["Tail1"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    wag2 = math.sin(wag_phase - 0.35) * math.radians(38.0)
    arm.pose.bones["Tail2"].rotation_quaternion = Euler((math.radians(-18.0), 0.0, wag2), 'XYZ').to_quaternion()
    arm.pose.bones["Tail2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    wag3 = math.sin(wag_phase - 0.70) * math.radians(50.0)
    arm.pose.bones["Tail3"].rotation_quaternion = Euler((math.radians(-20.0), 0.0, wag3), 'XYZ').to_quaternion()
    arm.pose.bones["Tail3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 2. HEAD: Dog panting smile expression!
    # Panting frequency: 4 quick cheerful breath pulses
    pant_phase = t * 4.0
    pant_bob = math.sin(pant_phase)
    
    # Smiling head: held up proudly with rhythmic chin-up panting
    head_pitch = math.radians(8.0) + pant_bob * math.radians(4.5)
    # Playful curious head tilt: swaying gently across the loop
    head_tilt = math.sin(t) * math.radians(5.0)
    head_turn = math.sin(t * 2.0) * math.radians(3.0)
    arm.pose.bones["Head"].rotation_quaternion = Euler((head_pitch, head_tilt, head_turn), 'XYZ').to_quaternion()
    arm.pose.bones["Head"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    neck_pitch = pant_bob * math.radians(3.0)
    arm.pose.bones["Neck2"].rotation_quaternion = Euler((neck_pitch * 0.4, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Neck3"].rotation_quaternion = Euler((neck_pitch * 0.8, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 3. HIGHLY FLEXIBLE TONGUE WAVE:
    # Tongue1 (base): pushes forward and down on exhale
    t1_pitch = math.radians(4.0) + math.sin(pant_phase) * math.radians(5.0)
    t1_yaw = math.sin(wag_phase * 0.4) * math.radians(3.0)
    # Tongue stretch forward (simulate panting breath pushing tongue out)
    t1_y_stretch = math.sin(pant_phase) * 0.015
    arm.pose.bones["Tongue1"].location = Vector((0.0, t1_y_stretch, 0.0))
    arm.pose.bones["Tongue1"].keyframe_insert(data_path="location", frame=f)
    arm.pose.bones["Tongue1"].rotation_quaternion = Euler((t1_pitch, 0.0, t1_yaw), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue1"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Tongue2 (mid): curves over lower teeth with phase delay of 0.45 rad
    t2_pitch = math.radians(8.0) + math.sin(pant_phase - 0.45) * math.radians(9.0)
    t2_roll = math.sin(t * 2.0) * math.radians(6.0) # playful side droop
    arm.pose.bones["Tongue2"].rotation_quaternion = Euler((t2_pitch, t2_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Tongue3 (tip): flexible floppy tip with 0.90 rad wave lag!
    # Tip flips up slightly like a happy spoon and wiggles as dog pants
    t3_pitch = math.sin(pant_phase - 0.90) * math.radians(16.0)
    t3_sway = math.sin(pant_phase * 0.5 - 0.6) * math.radians(10.0) # sideways wiggle
    arm.pose.bones["Tongue3"].rotation_quaternion = Euler((t3_pitch, 0.0, t3_sway), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 4. EARS: Happy dog "airplane ears" (perked and tilted slightly back/out warmly)
    ear_base_pitch = math.radians(-8.0) # slightly back
    ear_base_roll = math.radians(12.0)  # relaxed perky angle
    ear_bounce_l = math.sin(pant_phase + 0.3) * math.radians(4.0)
    ear_bounce_r = math.sin(pant_phase + 0.1) * math.radians(4.0)
    arm.pose.bones["Ear1.L"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_l, ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.L"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Ear1.R"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_r, -ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.R"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 5. BODY BREATHING: happy bouncy chest
    breath = abs(math.sin(pant_phase)) * 0.03
    arm.pose.bones["Body"].location = Vector((0.0, 0.0, breath))
    arm.pose.bones["Body"].keyframe_insert(data_path="location", frame=f)
    
    # Legs planted firmly
    for leg in ["FrontUpperLeg.L", "FrontUpperLeg.R", "BackLeg.L", "BackLeg.R"]:
        if leg in arm.pose.bones:
            arm.pose.bones[leg].rotation_quaternion = Quaternion((1, 0, 0, 0))
            arm.pose.bones[leg].keyframe_insert(data_path="rotation_quaternion", frame=f)

bpy.ops.object.mode_set(mode='OBJECT')
print("Successfully animated realistic 3-bone smiling panting tongue!")

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved ShibaInu.blend with updated smiling dog animation!")

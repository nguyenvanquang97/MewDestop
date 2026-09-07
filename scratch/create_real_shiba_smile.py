import bpy
import math
from mathutils import Vector, Quaternion, Euler
import bmesh

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

# Remove old tongue/mouth objects
for o in list(bpy.data.objects):
    if o.name.startswith("Tongue_Mesh") or o.name.startswith("Mouth_Cavity") or o.name.startswith("Smiling_Mouth"):
        bpy.data.objects.remove(o, do_unlink=True)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")

bpy.context.view_layer.objects.active = arm

# 1. Armature bones
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones

for b in ["Tongue", "Tongue1", "Tongue2", "Tongue3", "Tongue_Base", "Tongue_Tip"]:
    if b in eb:
        eb.remove(eb[b])

tb_root = eb.new("Tongue_Base")
tb_root.head = Vector((0.0, -2.30, 2.37))
tb_root.tail = Vector((0.0, -2.41, 2.36))
tb_root.parent = eb["Head"]
tb_root.use_connect = False

tb_tip = eb.new("Tongue_Tip")
tb_tip.head = tb_root.tail
tb_tip.tail = Vector((0.01, -2.52, 2.30)) # Authentic short spoon tongue
tb_tip.parent = tb_root
tb_tip.use_connect = True

bpy.ops.object.mode_set(mode='OBJECT')

# 2. Materials
mat_tongue = bpy.data.materials.get("Pink_Tongue")
if not mat_tongue:
    mat_tongue = bpy.data.materials.new(name="Pink_Tongue")
bsdf_t = mat_tongue.node_tree.nodes.get("Principled BSDF")
if bsdf_t:
    bsdf_t.inputs["Base Color"].default_value = (0.97, 0.42, 0.54, 1.0) # healthy warm pink
    bsdf_t.inputs["Roughness"].default_value = 0.20

mat_mouth = bpy.data.materials.get("Mouth_Dark")
if not mat_mouth:
    mat_mouth = bpy.data.materials.new(name="Mouth_Dark")
bsdf_m = mat_mouth.node_tree.nodes.get("Principled BSDF")
if bsdf_m:
    bsdf_m.inputs["Base Color"].default_value = (0.08, 0.03, 0.04, 1.0) # clean dark mouth slit
    bsdf_m.inputs["Roughness"].default_value = 0.4

# 3. Model authentic U-shaped / spoon tongue with dark mouth backing
bm = bmesh.new()

# Clean dark mouth backing sitting right at the mouth slit (No z-fighting with cheeks!)
# Mouth opening coordinates: X in [-0.09, 0.09], Y=-2.37, Z from 2.35 to 2.43
vm_tl = bm.verts.new(Vector((-0.09, -2.38, 2.42)))
vm_tr = bm.verts.new(Vector((0.09, -2.38, 2.42)))
vm_br = bm.verts.new(Vector((0.08, -2.35, 2.35)))
vm_bl = bm.verts.new(Vector((-0.08, -2.35, 2.35)))
f_mouth = bm.faces.new((vm_tl, vm_tr, vm_br, vm_bl))
f_mouth.material_index = 1 # Mouth_Dark

# Authentic Shiba panting tongue:
# - Broad & spoon-shaped (edges raised like a taco)
# - Length: only extends to Y=-2.52 (5.5cm outside mouth, totally natural!)
# - Deep groove down center, chubby rounded tip
sections = [
    # (y, z, width, thickness, taco_curl)
    (-2.28, 2.38, 0.09, 0.018, 0.000),  # inside mouth
    (-2.34, 2.38, 0.13, 0.022, 0.003),  # mouth opening
    (-2.40, 2.37, 0.16, 0.024, 0.008),  # wide mid-tongue with taco curl
    (-2.46, 2.35, 0.16, 0.023, 0.009),  # arching over bottom lip
    (-2.50, 2.31, 0.13, 0.018, 0.006),  # downward curve
    (-2.53, 2.26, 0.08, 0.012, 0.002),  # rounded chubby scoop tip
]

rings = []
for (y, z, w, th, taco) in sections:
    # 5 vertices on top: edges curled up (+taco), center dipped (-taco)
    v0 = bm.verts.new(Vector((-w * 0.5, y, z + th * 0.5 + taco)))
    v1 = bm.verts.new(Vector((-w * 0.25, y, z + th * 0.5)))
    v2 = bm.verts.new(Vector((0.0, y, z + th * 0.5 - taco * 0.8))) # center groove
    v3 = bm.verts.new(Vector((w * 0.25, y, z + th * 0.5)))
    v4 = bm.verts.new(Vector((w * 0.5, y, z + th * 0.5 + taco)))
    
    # 3 vertices on bottom (rounded belly of tongue)
    b0 = bm.verts.new(Vector((-w * 0.42, y, z - th * 0.5)))
    b1 = bm.verts.new(Vector((0.0, y, z - th * 0.55)))
    b2 = bm.verts.new(Vector((w * 0.42, y, z - th * 0.5)))
    
    rings.append(((v0, v1, v2, v3, v4), (b0, b1, b2)))

for i in range(len(rings) - 1):
    top1, bot1 = rings[i]
    top2, bot2 = rings[i+1]
    
    f1 = bm.faces.new((top1[0], top2[0], top2[1], top1[1]))
    f2 = bm.faces.new((top1[1], top2[1], top2[2], top1[2]))
    f3 = bm.faces.new((top1[2], top2[2], top2[3], top1[3]))
    f4 = bm.faces.new((top1[3], top2[3], top2[4], top1[4]))
    
    f5 = bm.faces.new((bot1[1], bot2[1], bot2[0], bot1[0]))
    f6 = bm.faces.new((bot1[2], bot2[2], bot2[1], bot1[1]))
    
    f7 = bm.faces.new((bot1[0], bot2[0], top2[0], top1[0]))
    f8 = bm.faces.new((top1[4], top2[4], bot2[2], bot1[2]))
    
    for f in [f1, f2, f3, f4, f5, f6, f7, f8]:
        f.material_index = 0 # Pink_Tongue

# Cap tip
top_end, bot_end = rings[-1]
ft1 = bm.faces.new((top_end[0], top_end[1], top_end[2], bot_end[0]))
ft2 = bm.faces.new((top_end[2], top_end[3], top_end[4], bot_end[2]))
ft3 = bm.faces.new((top_end[2], bot_end[2], bot_end[1], bot_end[0]))
for f in [ft1, ft2, ft3]:
    f.material_index = 0

bm.normal_update()

tongue_data = bpy.data.meshes.new("Smiling_Tongue_Data")
bm.to_mesh(tongue_data)
bm.free()

tongue_obj = bpy.data.objects.new("Smiling_Mouth", tongue_data)
bpy.context.collection.objects.link(tongue_obj)
tongue_obj.data.materials.append(mat_tongue)
tongue_obj.data.materials.append(mat_mouth)

# Rigging to Armature
mod = tongue_obj.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm

vg_head = tongue_obj.vertex_groups.new(name="Head")
vg_tbase = tongue_obj.vertex_groups.new(name="Tongue_Base")
vg_ttip = tongue_obj.vertex_groups.new(name="Tongue_Tip")

for v in tongue_obj.data.vertices:
    if v.co.y > -2.33:
        vg_head.add([v.index], 1.0, 'REPLACE')
    elif -2.44 <= v.co.y <= -2.33:
        factor = (v.co.y - (-2.44)) / 0.11
        vg_head.add([v.index], factor * 0.25, 'REPLACE')
        vg_tbase.add([v.index], 1.0 - factor * 0.25, 'REPLACE')
    else:
        factor = max(0.0, min(1.0, (v.co.y - (-2.53)) / 0.09))
        vg_tbase.add([v.index], factor * 0.35, 'REPLACE')
        vg_ttip.add([v.index], 1.0 - factor * 0.15, 'REPLACE')

print("Created authentic spoon tongue mesh!")

# 4. Animate Happy_TongueWag (Natural Shiba Panting)
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
    
    # Tail Wag (3 full cycles)
    wag_phase = t * 3.0
    wag1 = math.sin(wag_phase) * math.radians(26.0)
    arm.pose.bones["Tail1"].rotation_quaternion = Euler((math.radians(-15.0), 0.0, wag1), 'XYZ').to_quaternion()
    arm.pose.bones["Tail1"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    wag2 = math.sin(wag_phase - 0.35) * math.radians(36.0)
    arm.pose.bones["Tail2"].rotation_quaternion = Euler((math.radians(-18.0), 0.0, wag2), 'XYZ').to_quaternion()
    arm.pose.bones["Tail2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    wag3 = math.sin(wag_phase - 0.70) * math.radians(48.0)
    arm.pose.bones["Tail3"].rotation_quaternion = Euler((math.radians(-20.0), 0.0, wag3), 'XYZ').to_quaternion()
    arm.pose.bones["Tail3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 4 Panting breaths per loop
    pant_phase = t * 4.0
    pant_bob = math.sin(pant_phase)
    
    # Happy head bob & playful curiosity tilt
    head_pitch = math.radians(8.0) + pant_bob * math.radians(3.5)
    head_tilt = math.sin(t) * math.radians(4.5)
    head_yaw = math.sin(t * 2.0) * math.radians(2.5)
    arm.pose.bones["Head"].rotation_quaternion = Euler((head_pitch, head_tilt, head_yaw), 'XYZ').to_quaternion()
    arm.pose.bones["Head"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    neck_pitch = pant_bob * math.radians(2.2)
    arm.pose.bones["Neck2"].rotation_quaternion = Euler((neck_pitch * 0.4, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Neck3"].rotation_quaternion = Euler((neck_pitch * 0.8, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Authentic Panting Tongue Motion:
    # 1. On exhale (pant_bob > 0): tongue stretches slightly forward
    t_push = math.sin(pant_phase) * 0.010
    arm.pose.bones["Tongue_Base"].location = Vector((0.0, t_push, 0.0))
    arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="location", frame=f)
    
    t_base_pitch = math.radians(2.5) + math.sin(pant_phase) * math.radians(3.5)
    arm.pose.bones["Tongue_Base"].rotation_quaternion = Euler((t_base_pitch, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 2. Tongue Tip: cute floppy spoon tip with natural springiness
    t_tip_pitch = math.sin(pant_phase - 0.45) * math.radians(9.0)
    # Subtle derp sideways lean (common in smiling Shibas!)
    t_tip_roll = math.radians(4.0) + math.sin(t * 2.0) * math.radians(3.0)
    arm.pose.bones["Tongue_Tip"].rotation_quaternion = Euler((t_tip_pitch, t_tip_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Relaxed smiling ears
    ear_base_pitch = math.radians(-6.0)
    ear_base_roll = math.radians(10.0)
    ear_bounce_l = math.sin(pant_phase + 0.3) * math.radians(3.0)
    ear_bounce_r = math.sin(pant_phase + 0.1) * math.radians(3.0)
    arm.pose.bones["Ear1.L"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_l, ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.L"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Ear1.R"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_r, -ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.R"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # Body breath bounce
    breath = abs(math.sin(pant_phase)) * 0.024
    arm.pose.bones["Body"].location = Vector((0.0, 0.0, breath))
    arm.pose.bones["Body"].keyframe_insert(data_path="location", frame=f)
    
    for leg in ["FrontUpperLeg.L", "FrontUpperLeg.R", "BackLeg.L", "BackLeg.R"]:
        if leg in arm.pose.bones:
            arm.pose.bones[leg].rotation_quaternion = Quaternion((1, 0, 0, 0))
            arm.pose.bones[leg].keyframe_insert(data_path="rotation_quaternion", frame=f)

bpy.ops.object.mode_set(mode='OBJECT')
print("Successfully saved authentic Shiba smile animation!")

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blend file successfully!")

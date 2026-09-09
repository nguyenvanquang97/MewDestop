import bpy
import math
from mathutils import Vector, Quaternion, Euler

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")

bpy.context.view_layer.objects.active = arm

# 1. Vibrant cute pink tongue material
mat_tongue = bpy.data.materials.get("Pink_Tongue")
if mat_tongue:
    bsdf = mat_tongue.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1.0, 0.20, 0.42, 1.0) # Bright sweet candy pink!
        bsdf.inputs["Roughness"].default_value = 0.18

# 2. Reset and animate Happy_TongueWag with firmly planted 4 paws + squinting eyes
act = bpy.data.actions.get("Happy_TongueWag")
arm.animation_data.action = act

TOTAL_FRAMES = 40
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = TOTAL_FRAMES

bpy.ops.object.mode_set(mode='POSE')

# Reset ALL pose bones to rest pose first
for pb in arm.pose.bones:
    pb.location = Vector((0, 0, 0))
    pb.rotation_quaternion = Quaternion((1, 0, 0, 0))
    pb.scale = Vector((1, 1, 1))

# Keyframe 4 legs planted firmly throughout the 40 frames
leg_bones = [
    "FrontShoulder.L", "FrontUpperLeg.L", "FrontLowerLeg.L", "IKFrontLeg.L", "FF.L",
    "FrontShoulder.R", "FrontUpperLeg.R", "FrontLowerLeg.R", "IKFrontLeg.R", "FF.R",
    "BackShoulder.L", "BackLeg.L", "BackUpperLeg.L", "BackLowerLeg.L", "IKBackLeg.L", "FFB.L",
    "BackShoulder.R", "BackLeg.R", "BackUpperLeg.R", "BackLowerLeg.R", "IKBackLeg.R", "FFB.R",
    "PoleTarget.L", "PoleTarget.R", "PoleTargetBack.L", "PoleTargetBack.R"
]

for leg in leg_bones:
    if leg in arm.pose.bones:
        for f in range(TOTAL_FRAMES + 1):
            arm.pose.bones[leg].location = Vector((0, 0, 0))
            arm.pose.bones[leg].rotation_quaternion = Quaternion((1, 0, 0, 0))
            arm.pose.bones[leg].scale = Vector((1, 1, 1))
            arm.pose.bones[leg].keyframe_insert(data_path="location", frame=f)
            arm.pose.bones[leg].keyframe_insert(data_path="rotation_quaternion", frame=f)
            arm.pose.bones[leg].keyframe_insert(data_path="scale", frame=f)

for f in range(TOTAL_FRAMES + 1):
    t = (f / TOTAL_FRAMES) * math.tau
    
    # 1. TAIL: 3 energetic whip-like wag cycles
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
    
    # 2. PANTING SMILE HEAD:
    pant_phase = t * 4.0
    pant_bob = math.sin(pant_phase)
    
    head_pitch = math.radians(8.0) + pant_bob * math.radians(3.5)
    head_tilt = math.sin(t) * math.radians(4.0)
    head_yaw = math.sin(t * 2.0) * math.radians(2.0)
    arm.pose.bones["Head"].rotation_quaternion = Euler((head_pitch, head_tilt, head_yaw), 'XYZ').to_quaternion()
    arm.pose.bones["Head"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    neck_pitch = pant_bob * math.radians(2.0)
    arm.pose.bones["Neck2"].rotation_quaternion = Euler((neck_pitch * 0.4, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck2"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Neck3"].rotation_quaternion = Euler((neck_pitch * 0.8, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Neck3"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 3. SQUINTING EARS & EYES (Iconic "Shiba Smile"):
    # Squint eyes tightly into happy crescents: scale.z = 0.05
    squint_z = 0.05 + abs(math.sin(pant_phase)) * 0.02
    arm.pose.bones["Eye.L"].scale = Vector((1.08, 1.0, squint_z))
    arm.pose.bones["Eye.L"].location = Vector((0.0, 0.0, -0.018))
    arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
    arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
    
    arm.pose.bones["Eye.R"].scale = Vector((1.08, 1.0, squint_z))
    arm.pose.bones["Eye.R"].location = Vector((0.0, 0.0, -0.018))
    arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
    arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
    
    # Airplane ears (relaxed happy ears tilted back and out)
    ear_base_pitch = math.radians(-7.0)
    ear_base_roll = math.radians(12.0)
    ear_bounce_l = math.sin(pant_phase + 0.3) * math.radians(3.0)
    ear_bounce_r = math.sin(pant_phase + 0.1) * math.radians(3.0)
    arm.pose.bones["Ear1.L"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_l, ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.L"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    arm.pose.bones["Ear1.R"].rotation_quaternion = Euler((ear_base_pitch + ear_bounce_r, -ear_base_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Ear1.R"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 4. CHUBBY PINK SPOON TONGUE:
    # Tongue scale = (1, 1, 1) in Happy_TongueWag
    arm.pose.bones["Tongue_Base"].scale = Vector((1.0, 1.0, 1.0))
    arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="scale", frame=f)
    arm.pose.bones["Tongue_Tip"].scale = Vector((1.0, 1.0, 1.0))
    arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="scale", frame=f)
    
    t_push = math.sin(pant_phase) * 0.010
    arm.pose.bones["Tongue_Base"].location = Vector((0.0, t_push, 0.0))
    arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="location", frame=f)
    t_base_pitch = math.radians(2.5) + math.sin(pant_phase) * math.radians(3.5)
    arm.pose.bones["Tongue_Base"].rotation_quaternion = Euler((t_base_pitch, 0.0, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    t_tip_pitch = math.sin(pant_phase - 0.45) * math.radians(9.0)
    t_tip_roll = math.radians(4.0) + math.sin(t * 2.0) * math.radians(3.0)
    arm.pose.bones["Tongue_Tip"].rotation_quaternion = Euler((t_tip_pitch, t_tip_roll, 0.0), 'XYZ').to_quaternion()
    arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="rotation_quaternion", frame=f)
    
    # 5. BODY BREATH:
    breath = abs(math.sin(pant_phase)) * 0.022
    arm.pose.bones["Body"].location = Vector((0.0, 0.0, breath))
    arm.pose.bones["Body"].keyframe_insert(data_path="location", frame=f)

bpy.ops.object.mode_set(mode='OBJECT')

# 3. For all other actions, hide tongue and un-squint eyes
for other_act in bpy.data.actions:
    if other_act.name != "Happy_TongueWag":
        arm.animation_data.action = other_act
        bpy.ops.object.mode_set(mode='POSE')
        for f in [int(other_act.frame_range[0]), int(other_act.frame_range[1])]:
            # Normal open eyes
            arm.pose.bones["Eye.L"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.L"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Eye.R"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.R"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
            
            # Hide tongue
            arm.pose.bones["Tongue_Base"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Tongue_Tip"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="scale", frame=f)
        bpy.ops.object.mode_set(mode='OBJECT')

# Set default active action to Happy_TongueWag so opening the blend file shows it immediately
arm.animation_data.action = act

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blend file with finalized smile animation!")

# Export glTF
out_glb = "assets/models/shiba/ShibaInu.glb"
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    export_animations=True,
    export_nla_strips=True,
    export_anim_single_armature=True,
    export_current_frame=False
)
print(f"Exported to {out_glb} successfully!")

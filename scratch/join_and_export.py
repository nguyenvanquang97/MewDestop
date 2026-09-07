import bpy
from mathutils import Vector, Quaternion, Euler

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")
mouth = bpy.data.objects.get("Smiling_Mouth")

print("Found Armature:", arm.name if arm else None)
print("Found Mesh:", mesh.name if mesh else None)
print("Found Mouth:", mouth.name if mouth else None)

# 1. Join Smiling_Mouth into ShibaInu mesh so there is 1 clean skinned mesh
if mouth:
    for vg_name in ["Tongue_Base", "Tongue_Tip"]:
        if vg_name not in mesh.vertex_groups:
            mesh.vertex_groups.new(name=vg_name)
    
    bpy.ops.object.select_all(action='DESELECT')
    mouth.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    print("Successfully joined Smiling_Mouth into ShibaInu mesh!")

# 2. For all actions, configure tongue scale:
# (1, 1, 1) in Happy_TongueWag, (0.001, 0.001, 0.001) in all others
bpy.context.view_layer.objects.active = arm

for act in bpy.data.actions:
    arm.animation_data.action = act
    bpy.ops.object.mode_set(mode='POSE')
    if act.name == "Happy_TongueWag":
        for f in range(41):
            arm.pose.bones["Tongue_Base"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Tongue_Tip"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="scale", frame=f)
    else:
        for f in [int(act.frame_range[0]), int(act.frame_range[1])]:
            arm.pose.bones["Tongue_Base"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Tongue_Base"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Tongue_Tip"].scale = Vector((0.001, 0.001, 0.001))
            arm.pose.bones["Tongue_Tip"].keyframe_insert(data_path="scale", frame=f)
    bpy.ops.object.mode_set(mode='OBJECT')

print("Configured tongue visibility across all actions!")

# 3. Setup NLA Tracks for all 13 actions
arm.animation_data_create()
while len(arm.animation_data.nla_tracks) > 0:
    arm.animation_data.nla_tracks.remove(arm.animation_data.nla_tracks[0])

for act in sorted(bpy.data.actions, key=lambda a: a.name):
    act.use_fake_user = True
    track = arm.animation_data.nla_tracks.new()
    track.name = act.name
    strip = track.strips.new(act.name, int(act.frame_range[0]), act)
    strip.name = act.name
    print(f"Added NLA track: {act.name} (frames {int(act.frame_range[0])}-{int(act.frame_range[1])})")

# Save updated blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blend file successfully!")

# 4. Export glTF 2.0 GLB
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

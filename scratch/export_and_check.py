import bpy

blend_path = "assets/models/shiba/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("AnimalArmature")
print("Armature children:", [c.name for c in arm.children])
print("All actions:", [a.name for a in bpy.data.actions])

# Push all actions to NLA tracks so glTF exporter includes all 13 animations!
arm.animation_data_create()
# Clear existing tracks
arm.animation_data.nla_tracks.clear()

for act in bpy.data.actions:
    act.use_fake_user = True
    track = arm.animation_data.nla_tracks.new()
    track.name = act.name
    strip = track.strips.new(act.name, int(act.frame_range[0]), act)
    strip.name = act.name
    print(f"Added NLA track: {act.name}")

# Now export to assets/models/shiba/ShibaInu.glb
out_glb = "assets/models/shiba/ShibaInu.glb"
bpy.ops.export_scene.gltf(
    filepath=out_glb,
    export_format='GLB',
    use_selection=False,
    export_apply=False,
    export_animations=True,
    export_nla_strips=True,
    export_anim_single_armature=True,
    export_current_frame=False
)
print(f"Exported to {out_glb} successfully!")

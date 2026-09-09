import bpy
from mathutils import Vector, Quaternion, Euler
import math

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects.get("AnimalArmature")
mesh = bpy.data.objects.get("ShibaInu")

bpy.context.view_layer.objects.active = arm

# 1. Update Pink_Tongue material to be bright, vibrant, unmistakable pink
mat_tongue = bpy.data.materials.get("Pink_Tongue")
if mat_tongue:
    bsdf = mat_tongue.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # High saturation, bright candy pink so it stands out against the cream/brown fur!
        bsdf.inputs["Base Color"].default_value = (1.0, 0.18, 0.38, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.15

# 2. Add Eye.L and Eye.R bones to Armature
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones

for b_name, head_pos, tail_pos in [
    ("Eye.L", Vector((-0.224, -2.083, 2.709)), Vector((-0.224, -2.183, 2.709))),
    ("Eye.R", Vector((0.224, -2.083, 2.709)), Vector((0.224, -2.183, 2.709)))
]:
    if b_name not in eb:
        b = eb.new(b_name)
    else:
        b = eb[b_name]
    b.head = head_pos
    b.tail = tail_pos
    b.parent = eb["Head"]
    b.use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')

# 3. Assign eye vertices to Eye.L and Eye.R vertex groups
vg_eye_l = mesh.vertex_groups.get("Eye.L") or mesh.vertex_groups.new(name="Eye.L")
vg_eye_r = mesh.vertex_groups.get("Eye.R") or mesh.vertex_groups.new(name="Eye.R")

# Remove from Head group and assign to Eye groups
vg_head = mesh.vertex_groups.get("Head")

eye_vert_indices_l = set()
eye_vert_indices_r = set()
for p in mesh.data.polygons:
    if p.material_index in (3, 4, 5):
        for vi in p.vertices:
            v = mesh.data.vertices[vi]
            if v.co.x < 0:
                eye_vert_indices_l.add(vi)
            else:
                eye_vert_indices_r.add(vi)

for vi in eye_vert_indices_l:
    if vg_head:
        vg_head.remove([vi])
    vg_eye_l.add([vi], 1.0, 'REPLACE')

for vi in eye_vert_indices_r:
    if vg_head:
        vg_head.remove([vi])
    vg_eye_r.add([vi], 1.0, 'REPLACE')

print(f"Assigned {len(eye_vert_indices_l)} verts to Eye.L and {len(eye_vert_indices_r)} to Eye.R")

# 4. Animate Eye.L and Eye.R across all actions:
# In Happy_TongueWag: scale.z = 0.06 (happy squinting eyes! ^_^)
# In other actions: scale.z = 1.0 (normal open eyes)
TOTAL_FRAMES = 40

for act in bpy.data.actions:
    arm.animation_data.action = act
    bpy.ops.object.mode_set(mode='POSE')
    
    if act.name == "Happy_TongueWag":
        for f in range(TOTAL_FRAMES + 1):
            t = (f / TOTAL_FRAMES) * math.tau
            pant_phase = t * 4.0
            
            # Subtle eye squint pulse with breathing: squints tightly on exhale!
            squint_z = 0.06 + abs(math.sin(pant_phase)) * 0.03
            
            arm.pose.bones["Eye.L"].scale = Vector((1.08, 1.0, squint_z))
            arm.pose.bones["Eye.L"].location = Vector((0.0, 0.0, -0.018))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Eye.R"].scale = Vector((1.08, 1.0, squint_z))
            arm.pose.bones["Eye.R"].location = Vector((0.0, 0.0, -0.018))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
    else:
        for f in [int(act.frame_range[0]), int(act.frame_range[1])]:
            arm.pose.bones["Eye.L"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.L"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Eye.R"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.R"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
            
    bpy.ops.object.mode_set(mode='OBJECT')

print("Configured eye squinting across all actions!")

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved blender_src/ShibaInu.blend!")

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

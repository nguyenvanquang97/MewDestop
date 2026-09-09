import bpy
from mathutils import Vector, Euler
import math

blend_path = "blender_src/ShibaInu.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

arm = bpy.data.objects['AnimalArmature']
mesh = bpy.data.objects['ShibaInu']

# 1. Clean open eye vertex weights
# Left eye: p[824..843] + mat 3,4,5 (x < 0)
# Right eye: p[795..814] + mat 3,4,5 (x > 0)
left_eye_polys = [p for p in mesh.data.polygons if p.index in range(824, 844) or (p.material_index in (3,4,5) and mesh.data.vertices[p.vertices[0]].co.x < 0)]
right_eye_polys = [p for p in mesh.data.polygons if p.index in range(795, 815) or (p.material_index in (3,4,5) and mesh.data.vertices[p.vertices[0]].co.x > 0)]

vg_eye_l = mesh.vertex_groups.get("Eye.L") or mesh.vertex_groups.new(name="Eye.L")
vg_eye_r = mesh.vertex_groups.get("Eye.R") or mesh.vertex_groups.new(name="Eye.R")

for p in left_eye_polys:
    for vi in p.vertices:
        for vg in mesh.vertex_groups:
            try: vg.remove([vi])
            except RuntimeError: pass
        vg_eye_l.add([vi], 1.0, 'REPLACE')

for p in right_eye_polys:
    for vi in p.vertices:
        for vg in mesh.vertex_groups:
            try: vg.remove([vi])
            except RuntimeError: pass
        vg_eye_r.add([vi], 1.0, 'REPLACE')

print(f"Cleaned open eyes: {len(left_eye_polys)} L polys, {len(right_eye_polys)} R polys")

# 2. Add Smile_Eyes bone to Armature
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones

if "Smile_Eyes" not in eb:
    b_smile = eb.new("Smile_Eyes")
else:
    b_smile = eb["Smile_Eyes"]

b_smile.head = Vector((0.0, -2.08, 2.71))
b_smile.tail = Vector((0.0, -2.18, 2.71))
b_smile.parent = eb["Head"]
b_smile.use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')

vg_smile = mesh.vertex_groups.get("Smile_Eyes") or mesh.vertex_groups.new(name="Smile_Eyes")

# 3. Build Smiling Eyes geometry
pts_left = [
    Vector((-0.155, -2.130, 2.700)),
    Vector((-0.185, -2.108, 2.716)),
    Vector((-0.220, -2.082, 2.726)),
    Vector((-0.255, -2.060, 2.718)),
    Vector((-0.290, -2.040, 2.705)),
    Vector((-0.312, -2.025, 2.712)),
]

widths = [0.005, 0.020, 0.028, 0.024, 0.015, 0.005]

def get_point_normal(pt, mirror_x=False):
    rad = math.atan2(abs(pt.x), -pt.y - 2.0)
    nx = -math.sin(rad) * (1.0 if not mirror_x else -1.0)
    ny = -math.cos(rad)
    nz = 0.35
    return Vector((nx, ny, nz)).normalized()

smile_verts = []
smile_faces = []

def build_smile(pts, widths, mirror_x=False):
    v_start = len(smile_verts)
    n = len(pts)
    for i in range(n):
        pt = pts[i]
        w = widths[i]
        pos = Vector((pt.x if not mirror_x else -pt.x, pt.y, pt.z))
        norm = get_point_normal(pt, mirror_x)
        up = Vector((0.0, -0.2, 0.98)).normalized()
        surface_pos = pos + norm * 0.007
        vt = surface_pos + up * (w * 0.5)
        vb = surface_pos - up * (w * 0.5)
        smile_verts.extend([vt, vb])
        
    for i in range(n - 1):
        i0 = v_start + i * 2
        i1 = v_start + i * 2 + 1
        i2 = v_start + (i + 1) * 2 + 1
        i3 = v_start + (i + 1) * 2
        if not mirror_x:
            smile_faces.append((i0, i1, i2, i3))
        else:
            smile_faces.append((i3, i2, i1, i0))

build_smile(pts_left, widths, False)
build_smile(pts_left, widths, True)

# Join smiling eyes geometry directly into mesh
black_mat_idx = 1  # Black2
for i, m in enumerate(mesh.data.materials):
    if m.name == "Black2":
        black_mat_idx = i
        break

start_vi = len(mesh.data.vertices)
# Using bmesh to add geometry to mesh
import bmesh
bm = bmesh.new()
bm.from_mesh(mesh.data)

# First ensure vertex group 'Smile_Eyes' index
bm.verts.layers.deform.verify()
dlayer = bm.verts.layers.deform.active
smile_vg_idx = mesh.vertex_groups['Smile_Eyes'].index

new_bm_verts = []
for vco in smile_verts:
    bm_v = bm.verts.new(vco)
    bm_v[dlayer][smile_vg_idx] = 1.0
    new_bm_verts.append(bm_v)

bm.verts.ensure_lookup_table()

for f_indices in smile_faces:
    fv = [new_bm_verts[idx] for idx in f_indices]
    f = bm.faces.new(fv)
    f.material_index = black_mat_idx

bm.to_mesh(mesh.data)
bm.free()
mesh.data.update()

print("Integrated Smile_Eyes geometry into ShibaInu mesh!")

# 4. Keyframe all actions
bpy.context.view_layer.objects.active = arm

for act in bpy.data.actions:
    arm.animation_data.action = act
    bpy.ops.object.mode_set(mode='POSE')
    
    if act.name == "Happy_TongueWag":
        total_frames = int(act.frame_range[1] - act.frame_range[0])
        for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
            # Open eyes hidden: scale = 0.0001, retract slightly
            arm.pose.bones["Eye.L"].scale = Vector((0.0001, 0.0001, 0.0001))
            arm.pose.bones["Eye.L"].location = Vector((0.0, 0.2, 0.0))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Eye.R"].scale = Vector((0.0001, 0.0001, 0.0001))
            arm.pose.bones["Eye.R"].location = Vector((0.0, 0.2, 0.0))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
            
            # Smiling eyes visible!
            arm.pose.bones["Smile_Eyes"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Smile_Eyes"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Smile_Eyes"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Smile_Eyes"].keyframe_insert(data_path="location", frame=f)
    else:
        # In all other 12 actions: open eyes normal, smiling eyes hidden
        for f in [int(act.frame_range[0]), int(act.frame_range[1])]:
            arm.pose.bones["Eye.L"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.L"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.L"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Eye.R"].scale = Vector((1.0, 1.0, 1.0))
            arm.pose.bones["Eye.R"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Eye.R"].keyframe_insert(data_path="location", frame=f)
            
            arm.pose.bones["Smile_Eyes"].scale = Vector((0.0001, 0.0001, 0.0001))
            arm.pose.bones["Smile_Eyes"].location = Vector((0.0, 0.0, 0.0))
            arm.pose.bones["Smile_Eyes"].keyframe_insert(data_path="scale", frame=f)
            arm.pose.bones["Smile_Eyes"].keyframe_insert(data_path="location", frame=f)
            
    bpy.ops.object.mode_set(mode='OBJECT')

print("All actions successfully keyframed with Smile_Eyes!")

# 5. Save blend file
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved {blend_path}")

# 6. Export GLB
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

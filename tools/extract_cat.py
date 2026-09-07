import struct, json, os

src_path = 'assets/models/raw/Meshy_AI_Bluebell_the_Kitten_0904032606_texture.glb'
dst_path = 'assets/models/cat/cat_textured.glb'
os.makedirs('assets/models/cat', exist_ok=True)

with open(src_path, 'rb') as f:
    magic, version, length = struct.unpack('<III', f.read(12))
    chunk_len, chunk_type = struct.unpack('<II', f.read(8))
    gltf = json.loads(f.read(chunk_len).decode('utf-8'))
    bin_len, bin_type = struct.unpack('<II', f.read(8))
    bin_data = f.read(bin_len)

prim = gltf['meshes'][0]['primitives'][0]
pos_acc = gltf['accessors'][prim['attributes']['POSITION']]
norm_acc = gltf['accessors'][prim['attributes']['NORMAL']]
tang_acc = gltf['accessors'][prim['attributes']['TANGENT']]
uv_acc = gltf['accessors'][prim['attributes']['TEXCOORD_0']]
ind_acc = gltf['accessors'][prim['indices']]

def get_offset(acc):
    bv = gltf['bufferViews'][acc['bufferView']]
    return bv.get('byteOffset', 0) + acc.get('byteOffset', 0)

pos_off = get_offset(pos_acc)
norm_off = get_offset(norm_acc)
tang_off = get_offset(tang_acc)
uv_off = get_offset(uv_acc)
ind_off = get_offset(ind_acc)

itype = ind_acc['componentType']
fmt = '<H' if itype == 5123 else '<I'
stride = 2 if itype == 5123 else 4
icount = ind_acc['count']
vcount = pos_acc['count']

xs = [struct.unpack_from('<fff', bin_data, pos_off + i*12)[0] for i in range(vcount)]

cat1_triangles = []
for i in range(0, icount, 3):
    i1 = struct.unpack_from(fmt, bin_data, ind_off + i*stride)[0]
    i2 = struct.unpack_from(fmt, bin_data, ind_off + (i+1)*stride)[0]
    i3 = struct.unpack_from(fmt, bin_data, ind_off + (i+2)*stride)[0]
    mid_x = (xs[i1] + xs[i2] + xs[i3]) / 3.0
    if mid_x < -0.59:
        cat1_triangles.append((i1, i2, i3))

used_verts = sorted(list({v for t in cat1_triangles for v in t}))
old_to_new = {old: new for new, old in enumerate(used_verts)}
new_vcount = len(used_verts)

# Compute center & min y
orig_positions = [struct.unpack_from('<fff', bin_data, pos_off + old*12) for old in used_verts]
min_x = min(p[0] for p in orig_positions)
max_x = max(p[0] for p in orig_positions)
min_y = min(p[1] for p in orig_positions)
max_y = max(p[1] for p in orig_positions)
min_z = min(p[2] for p in orig_positions)
max_z = max(p[2] for p in orig_positions)

center_x = (min_x + max_x) / 2.0
center_z = (min_z + max_z) / 2.0

new_positions = [(p[0] - center_x, p[1] - min_y, p[2] - center_z) for p in orig_positions]

new_pos_bytes = b''.join(struct.pack('<fff', *p) for p in new_positions)
new_norm_bytes = b''.join(bin_data[norm_off + old*12 : norm_off + (old+1)*12] for old in used_verts)
new_tang_bytes = b''.join(bin_data[tang_off + old*16 : tang_off + (old+1)*16] for old in used_verts)
new_uv_bytes = b''.join(bin_data[uv_off + old*8 : uv_off + (old+1)*8] for old in used_verts)
new_ind_bytes = b''.join(struct.pack('<I', old_to_new[old]) for t in cat1_triangles for old in t)

def pad4_bytes(b, pad_char=b'\x00'):
    pad = (4 - (len(b) % 4)) % 4
    return b + (pad_char * pad if pad > 0 else b'')

new_bin = bytearray()
new_bufferViews = []

def append_bv(data, target=None):
    offset = len(new_bin)
    padded = pad4_bytes(data, b'\x00')
    new_bin.extend(padded)
    bv = {'buffer': 0, 'byteOffset': offset, 'byteLength': len(data)}
    if target:
        bv['target'] = target
    idx = len(new_bufferViews)
    new_bufferViews.append(bv)
    return idx

# BV 0: positions (target 34962 = ARRAY_BUFFER)
idx_pos_bv = append_bv(new_pos_bytes, 34962)
idx_norm_bv = append_bv(new_norm_bytes, 34962)
idx_tang_bv = append_bv(new_tang_bytes, 34962)
idx_uv_bv = append_bv(new_uv_bytes, 34962)
idx_ind_bv = append_bv(new_ind_bytes, 34963)

# BV images
new_images = []
for img in gltf.get('images', []):
    bv = gltf['bufferViews'][img['bufferView']]
    start = bv.get('byteOffset', 0)
    length = bv['byteLength']
    img_data = bin_data[start:start+length]
    idx_img_bv = append_bv(img_data)
    new_img = dict(img)
    new_img['bufferView'] = idx_img_bv
    new_images.append(new_img)

new_accessors = [
    { # 0: POSITION
        'bufferView': idx_pos_bv,
        'byteOffset': 0,
        'componentType': 5126,
        'count': new_vcount,
        'type': 'VEC3',
        'min': [float(min(p[0] for p in new_positions)), 0.0, float(min(p[2] for p in new_positions))],
        'max': [float(max(p[0] for p in new_positions)), float(max_y - min_y), float(max(p[2] for p in new_positions))]
    },
    { # 1: NORMAL
        'bufferView': idx_norm_bv,
        'byteOffset': 0,
        'componentType': 5126,
        'count': new_vcount,
        'type': 'VEC3'
    },
    { # 2: TANGENT
        'bufferView': idx_tang_bv,
        'byteOffset': 0,
        'componentType': 5126,
        'count': new_vcount,
        'type': 'VEC4'
    },
    { # 3: TEXCOORD_0
        'bufferView': idx_uv_bv,
        'byteOffset': 0,
        'componentType': 5126,
        'count': new_vcount,
        'type': 'VEC2'
    },
    { # 4: indices
        'bufferView': idx_ind_bv,
        'byteOffset': 0,
        'componentType': 5125,
        'count': len(cat1_triangles) * 3,
        'type': 'SCALAR'
    }
]

new_gltf = {
    'asset': gltf['asset'],
    'scene': 0,
    'scenes': [{'nodes': [0]}],
    'nodes': [{'name': 'Cat_Mesh', 'mesh': 0}],
    'materials': gltf.get('materials', []),
    'textures': gltf.get('textures', []),
    'samplers': gltf.get('samplers', []),
    'images': new_images,
    'meshes': [{
        'name': 'Cat_Mesh',
        'primitives': [{
            'attributes': {
                'POSITION': 0,
                'NORMAL': 1,
                'TANGENT': 2,
                'TEXCOORD_0': 3
            },
            'indices': 4,
            'material': 0
        }]
    }],
    'accessors': new_accessors,
    'bufferViews': new_bufferViews,
    'buffers': [{'byteLength': len(new_bin)}]
}

json_str = json.dumps(new_gltf)
json_bytes = pad4_bytes(json_str.encode('utf-8'), b' ')
total_len = 12 + 8 + len(json_bytes) + 8 + len(new_bin)

with open(dst_path, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, total_len))
    f.write(struct.pack('<II', len(json_bytes), 0x4E4F534A))
    f.write(json_bytes)
    f.write(struct.pack('<II', len(new_bin), 0x004E4942))
    f.write(new_bin)

print('Success! Wrote:', dst_path, 'Size:', os.path.getsize(dst_path) / 1024 / 1024, 'MB')

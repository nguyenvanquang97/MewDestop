import math, struct, json, os

def generate_bowl():
    # Cute, perfectly proportioned 3D ceramic pet dish (diameter ~ 35cm, height ~ 10cm)
    profile = [
        (0.00, 0.000),  # 0 bottom center
        (0.09, 0.000),  # 1 base pedestal ring inner
        (0.105, 0.006), # 2 base pedestal outer bevel
        (0.115, 0.018), # 3 pedestal indent
        (0.135, 0.035), # 4 bowl lower flare
        (0.165, 0.065), # 5 bowl mid body
        (0.175, 0.092), # 6 rim outer crest
        (0.170, 0.100), # 7 rim top rounded crest
        (0.155, 0.097), # 8 rim inner rounded crest
        (0.140, 0.082), # 9 inner wall upper
        (0.120, 0.050), # 10 inner wall mid
        (0.095, 0.028), # 11 inner floor corner
        (0.00, 0.025),  # 12 inner floor center
    ]

    segments = 36
    num_p = len(profile)

    verts = []
    norms = []
    uvs = []
    indices = []

    # Generate vertices by revolving around Y axis
    for s in range(segments + 1):
        angle = (s / float(segments)) * math.pi * 2.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        u = s / float(segments)

        for p_idx, (r, y) in enumerate(profile):
            px = r * cos_a
            py = y
            pz = r * sin_a
            verts.append((px, py, pz))
            v = p_idx / float(num_p - 1)
            uvs.append((u, v))

    # Calculate smooth vertex normals from profile tangents + radial direction
    for s in range(segments + 1):
        angle = (s / float(segments)) * math.pi * 2.0
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for p_idx in range(num_p):
            # Tangent along profile
            if p_idx == 0:
                dy = profile[1][1] - profile[0][1]
                dr = profile[1][0] - profile[0][0]
            elif p_idx == num_p - 1:
                dy = profile[-1][1] - profile[-2][1]
                dr = profile[-1][0] - profile[-2][0]
            else:
                dy = profile[p_idx+1][1] - profile[p_idx-1][1]
                dr = profile[p_idx+1][0] - profile[p_idx-1][0]

            # Normal in 2D (r, y): (-dy, dr)
            nr = -dy
            ny = dr
            length = math.sqrt(nr * nr + ny * ny)
            if length > 1e-6:
                nr /= length
                ny /= length
            else:
                nr, ny = 0.0, 1.0

            nx = nr * cos_a
            nz = nr * sin_a
            norms.append((nx, ny, nz))

    # Generate quad indices
    for s in range(segments):
        for p in range(num_p - 1):
            i00 = s * num_p + p
            i01 = s * num_p + (p + 1)
            i10 = (s + 1) * num_p + p
            i11 = (s + 1) * num_p + (p + 1)

            # Two triangles with proper winding order
            indices.extend([i00, i10, i01])
            indices.extend([i01, i10, i11])

    # Milk mesh: brimming near the top rim (y = 0.085, r = 0.145)
    milk_verts = []
    milk_norms = []
    milk_uvs = []
    milk_indices = []

    milk_segments = 32
    milk_rings = 4
    milk_r_max = 0.145
    milk_y = 0.085

    for r_i in range(milk_rings + 1):
        frac = r_i / float(milk_rings)
        r = milk_r_max * frac
        # Slight dome / meniscus curve: edges slightly higher
        y = milk_y + (0.003 * (frac * frac))
        for s in range(milk_segments + 1):
            angle = (s / float(milk_segments)) * math.pi * 2.0
            x = r * math.cos(angle)
            z = r * math.sin(angle)
            milk_verts.append((x, y, z))
            milk_norms.append((0.0, 1.0, 0.0))
            milk_uvs.append((x / (2*milk_r_max) + 0.5, z / (2*milk_r_max) + 0.5))

    stride_m = milk_segments + 1
    for r_i in range(milk_rings):
        for s in range(milk_segments):
            m00 = r_i * stride_m + s
            m01 = (r_i + 1) * stride_m + s
            m10 = r_i * stride_m + (s + 1)
            m11 = (r_i + 1) * stride_m + (s + 1)

            milk_indices.extend([m00, m01, m10])
            milk_indices.extend([m10, m01, m11])

    # Paw decal motif geometry on front rim (outside)
    # Pack into GLB
    return {
        'bowl': {'verts': verts, 'norms': norms, 'uvs': uvs, 'indices': indices},
        'milk': {'verts': milk_verts, 'norms': milk_norms, 'uvs': milk_uvs, 'indices': milk_indices}
    }

def export_glb(data, out_path):
    bin_data = bytearray()
    buffer_views = []
    accessors = []

    def pad4(b):
        p = (4 - (len(b) % 4)) % 4
        return b + (b'\x00' * p)

    def add_buffer_view(b, target):
        off = len(bin_data)
        padded = pad4(b)
        bin_data.extend(padded)
        bv_idx = len(buffer_views)
        buffer_views.append({
            'buffer': 0,
            'byteOffset': off,
            'byteLength': len(b),
            'target': target
        })
        return bv_idx

    meshes = []
    nodes = []

    for name, part in [('CeramicBowl', data['bowl']), ('MilkSurface', data['milk'])]:
        verts = part['verts']
        norms = part['norms']
        uvs = part['uvs']
        indices = part['indices']

        v_bytes = b''.join(struct.pack('<fff', *v) for v in verts)
        n_bytes = b''.join(struct.pack('<fff', *n) for n in norms)
        uv_bytes = b''.join(struct.pack('<ff', *uv) for uv in uvs)
        i_bytes = b''.join(struct.pack('<I', i) for i in indices)

        bv_pos = add_buffer_view(v_bytes, 34962)
        bv_norm = add_buffer_view(n_bytes, 34962)
        bv_uv = add_buffer_view(uv_bytes, 34962)
        bv_ind = add_buffer_view(i_bytes, 34963)

        min_pos = [min(v[c] for v in verts) for c in range(3)]
        max_pos = [max(v[c] for v in verts) for c in range(3)]

        acc_pos = len(accessors)
        accessors.append({
            'bufferView': bv_pos,
            'byteOffset': 0,
            'componentType': 5126, # FLOAT
            'count': len(verts),
            'type': 'VEC3',
            'min': min_pos,
            'max': max_pos
        })

        acc_norm = len(accessors)
        accessors.append({
            'bufferView': bv_norm,
            'byteOffset': 0,
            'componentType': 5126,
            'count': len(norms),
            'type': 'VEC3'
        })

        acc_uv = len(accessors)
        accessors.append({
            'bufferView': bv_uv,
            'byteOffset': 0,
            'componentType': 5126,
            'count': len(uvs),
            'type': 'VEC2'
        })

        acc_ind = len(accessors)
        accessors.append({
            'bufferView': bv_ind,
            'byteOffset': 0,
            'componentType': 5125, # UNSIGNED_INT
            'count': len(indices),
            'type': 'SCALAR'
        })

        mat_idx = 0 if name == 'CeramicBowl' else 1
        mesh_idx = len(meshes)
        meshes.append({
            'name': name,
            'primitives': [{
                'attributes': {
                    'POSITION': acc_pos,
                    'NORMAL': acc_norm,
                    'TEXCOORD_0': acc_uv
                },
                'indices': acc_ind,
                'material': mat_idx
            }]
        })

        nodes.append({
            'name': name,
            'mesh': mesh_idx
        })

    materials = [
        {
            'name': 'CeramicPastelMat',
            'pbrMetallicRoughness': {
                'baseColorFactor': [1.0, 0.45, 0.58, 1.0], # Cute Pastel Strawberry Coral
                'roughnessFactor': 0.20,
                'metallicFactor': 0.05
            }
        },
        {
            'name': 'CreamyMilkMat',
            'pbrMetallicRoughness': {
                'baseColorFactor': [1.0, 0.98, 0.92, 1.0], # Creamy Warm White Milk
                'roughnessFactor': 0.12,
                'metallicFactor': 0.0
            }
        }
    ]

    gltf = {
        'asset': {'version': '2.0', 'generator': 'MewDesktop Custom'},
        'scene': 0,
        'scenes': [{'nodes': list(range(len(nodes)))}],
        'nodes': nodes,
        'meshes': meshes,
        'materials': materials,
        'accessors': accessors,
        'bufferViews': buffer_views,
        'buffers': [{'byteLength': len(bin_data)}]
    }

    json_raw = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    pad_len = (4 - (len(json_raw) % 4)) % 4
    json_bytes = json_raw + (b' ' * pad_len)

    total_len = 12 + 8 + len(json_bytes) + 8 + len(bin_data)
    header = struct.pack('<III', 0x46546C67, 2, total_len)
    chunk0_hdr = struct.pack('<II', len(json_bytes), 0x4E4F534A) # JSON
    chunk1_hdr = struct.pack('<II', len(bin_data), 0x004E4942)  # BIN

    with open(out_path, 'wb') as f:
        f.write(header)
        f.write(chunk0_hdr)
        f.write(json_bytes)
        f.write(chunk1_hdr)
        f.write(bin_data)

    print(f'Successfully exported {out_path} ({total_len} bytes)')

if __name__ == '__main__':
    data = generate_bowl()
    export_glb(data, 'assets/models/items/milk_dish.glb')

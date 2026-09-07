import math
import struct
import json
import os
from PIL import Image, ImageDraw

def generate_ceramic_texture():
    # 512x512 texture:
    # Left half (u: 0.0 -> 0.6): Ceramic body with glaze gradient & pottery rim
    # Right half (u: 0.6 -> 1.0): Creamy rich milk with soft milky gradient
    w, h = 512, 512
    img = Image.new('RGB', (w, h), (160, 175, 175))
    draw = ImageDraw.Draw(img)

    # Ceramic gradient (v: 0.0 = base bottom, 0.6 = rim, 1.0 = inner bottom)
    for y in range(h):
        v = y / float(h)
        # Glazed ceramic tone: Warm Celadon Slate
        # Base is slightly deeper slate (130, 145, 145), waist is smooth (165, 180, 180),
        # Rim has a classic hand-thrown darker glazed line (110, 125, 125)
        if v < 0.15: # Foot base
            t = v / 0.15
            r = int(120 + t * 40)
            g = int(135 + t * 40)
            b = int(138 + t * 40)
        elif v < 0.55: # Outer wall
            t = (v - 0.15) / 0.40
            r = int(160 + math.sin(t * math.pi) * 15)
            g = int(175 + math.sin(t * math.pi) * 15)
            b = int(178 + math.sin(t * math.pi) * 15)
        elif v < 0.65: # Rim line
            r, g, b = 115, 130, 132 # Darker glazed rim accent
        else: # Inner wall
            t = (v - 0.65) / 0.35
            r = int(150 - t * 20)
            g = int(165 - t * 20)
            b = int(168 - t * 20)
        draw.line([(0, y), (int(w * 0.6), y)], fill=(r, g, b))

    # Milk texture on right side (u: 0.6 -> 1.0)
    # Creamy rich white milk with soft radial depth
    cx = int(w * 0.8)
    cy = int(h * 0.5)
    max_rad = int(w * 0.20)
    for rad in range(max_rad, -1, -1):
        t = rad / float(max_rad)
        # Center is pure cream (255, 255, 252), edge has subtle liquid depth (235, 238, 238)
        r = int(255 - t * 20)
        g = int(255 - t * 18)
        b = int(250 - t * 15)
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(r, g, b))

    tex_bytes = bytearray()
    import io
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def create_textured_ceramic_bowl():
    profile = [
        (0.000, 0.000),  # 0: base center
        (0.120, 0.000),  # 1: base outer
        (0.125, 0.012),  # 2: foot rim
        (0.118, 0.025),  # 3: foot groove
        (0.092, 0.052),  # 4: pedestal waist
        (0.115, 0.072),  # 5: pedestal upper
        (0.150, 0.090),  # 6: bowl outer transition
        (0.182, 0.110),  # 7: bowl outer wall
        (0.195, 0.125),  # 8: rim outer
        (0.190, 0.130),  # 9: rim crest
        (0.180, 0.128),  # 10: rim inner
        (0.160, 0.110),  # 11: inner bowl wall
        (0.135, 0.090),  # 12: inner bowl mid
        (0.095, 0.072),  # 13: inner floor transition
        (0.000, 0.068),  # 14: inner center
    ]

    SECTORS = 36
    bowl_vertices = []
    bowl_normals = []
    bowl_uvs = []
    bowl_indices = []

    for p_idx, (r, y) in enumerate(profile):
        v = p_idx / float(len(profile) - 1)
        for s in range(SECTORS + 1):
            theta = 2.0 * math.pi * (s % SECTORS) / SECTORS
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            x = r * cos_t
            z = r * sin_t
            bowl_vertices.append((x, y, z))
            # u mapped within [0.0, 0.58] for ceramic glaze
            u = (s / float(SECTORS)) * 0.58
            bowl_uvs.append((u, v))

    num_p = len(profile)
    normals_acc = [[0.0, 0.0, 0.0] for _ in range(len(bowl_vertices))]

    for p in range(num_p - 1):
        for s in range(SECTORS):
            i0 = p * (SECTORS + 1) + s
            i1 = p * (SECTORS + 1) + (s + 1)
            i2 = (p + 1) * (SECTORS + 1) + s
            i3 = (p + 1) * (SECTORS + 1) + (s + 1)

            tris = [(i0, i2, i1), (i1, i2, i3)]
            for ta, tb, tc in tris:
                bowl_indices.extend([ta, tb, tc])
                va = bowl_vertices[ta]
                vb = bowl_vertices[tb]
                vc = bowl_vertices[tc]
                ab = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
                ac = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
                nx = ab[1] * ac[2] - ab[2] * ac[1]
                ny = ab[2] * ac[0] - ab[0] * ac[2]
                nz = ab[0] * ac[1] - ab[1] * ac[0]
                length = math.sqrt(nx*nx + ny*ny + nz*nz)
                if length > 1e-6:
                    nx /= length; ny /= length; nz /= length
                for idx in (ta, tb, tc):
                    normals_acc[idx][0] += nx
                    normals_acc[idx][1] += ny
                    normals_acc[idx][2] += nz

    for n in normals_acc:
        length = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
        if length > 1e-6:
            bowl_normals.append((n[0]/length, n[1]/length, n[2]/length))
        else:
            bowl_normals.append((0.0, 1.0, 0.0))

    # Milk Liquid Surface (at y = 0.096, radius r = 0.150)
    milk_vertices = []
    milk_normals = []
    milk_uvs = []
    milk_indices = []

    MILK_SECTORS = 32
    MILK_RINGS = 4
    milk_y = 0.096
    milk_r = 0.150

    milk_vertices.append((0.0, milk_y, 0.0))
    milk_normals.append((0.0, 1.0, 0.0))
    # Milk center mapped to u=0.8, v=0.5
    milk_uvs.append((0.8, 0.5))

    for ring in range(1, MILK_RINGS + 1):
        rr = milk_r * (ring / float(MILK_RINGS))
        yy = milk_y + (0.002 if ring == MILK_RINGS else 0.0)
        for s in range(MILK_SECTORS):
            theta = 2.0 * math.pi * s / MILK_SECTORS
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            x = rr * cos_t
            z = rr * sin_t
            milk_vertices.append((x, yy, z))
            milk_normals.append((0.0, 1.0, 0.0))
            # Milk UV mapped within [0.65, 0.95] in U and [0.2, 0.8] in V
            mu = 0.80 + 0.15 * (x / milk_r)
            mv = 0.50 + 0.15 * (z / milk_r)
            milk_uvs.append((mu, mv))

    for s in range(MILK_SECTORS):
        next_s = (s + 1) % MILK_SECTORS
        milk_indices.extend([0, 1 + s, 1 + next_s])

    for ring in range(1, MILK_RINGS):
        r0 = 1 + (ring - 1) * MILK_SECTORS
        r1 = 1 + ring * MILK_SECTORS
        for s in range(MILK_SECTORS):
            next_s = (s + 1) % MILK_SECTORS
            p0 = r0 + s; p1 = r0 + next_s; p2 = r1 + s; p3 = r1 + next_s
            milk_indices.extend([p0, p2, p1])
            milk_indices.extend([p1, p2, p3])

    def pack_mesh_data(verts, norms, uvs, indices):
        v_bytes = bytearray()
        for v in verts: v_bytes.extend(struct.pack('<fff', v[0], v[1], v[2]))
        n_bytes = bytearray()
        for n in norms: n_bytes.extend(struct.pack('<fff', n[0], n[1], n[2]))
        u_bytes = bytearray()
        for u in uvs: u_bytes.extend(struct.pack('<ff', u[0], u[1]))
        i_bytes = bytearray()
        for idx in indices: i_bytes.extend(struct.pack('<H', idx))
        return v_bytes, n_bytes, u_bytes, i_bytes

    b_v, b_n, b_u, b_i = pack_mesh_data(bowl_vertices, bowl_normals, bowl_uvs, bowl_indices)
    m_v, m_n, m_u, m_i = pack_mesh_data(milk_vertices, milk_normals, milk_uvs, milk_indices)
    png_data = generate_ceramic_texture()

    def get_min_max(verts):
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        zs = [v[2] for v in verts]
        return [min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]

    b_min, b_max = get_min_max(bowl_vertices)
    m_min, m_max = get_min_max(milk_vertices)

    buffer_data = bytearray()
    def align_4(b):
        while len(b) % 4 != 0: b.append(0)

    views = []
    accessors = []
    parts = [
        (b_i, 5123, 'SCALAR', len(bowl_indices), None, None, 34963),
        (b_v, 5126, 'VEC3', len(bowl_vertices), b_min, b_max, 34962),
        (b_n, 5126, 'VEC3', len(bowl_normals), None, None, 34962),
        (b_u, 5126, 'VEC2', len(bowl_uvs), None, None, 34962),
        (m_i, 5123, 'SCALAR', len(milk_indices), None, None, 34963),
        (m_v, 5126, 'VEC3', len(milk_vertices), m_min, m_max, 34962),
        (m_n, 5126, 'VEC3', len(milk_normals), None, None, 34962),
        (m_u, 5126, 'VEC2', len(milk_uvs), None, None, 34962),
    ]

    for data_bytes, comp_type, data_type, count, min_v, max_v, target in parts:
        align_4(buffer_data)
        offset = len(buffer_data)
        buffer_data.extend(data_bytes)
        length = len(data_bytes)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": length, "target": target})
        acc = {"bufferView": len(views) - 1, "byteOffset": 0, "componentType": comp_type, "count": count, "type": data_type}
        if min_v is not None and max_v is not None:
            acc["min"] = min_v; acc["max"] = max_v
        accessors.append(acc)

    # View 8: PNG image data
    align_4(buffer_data)
    img_offset = len(buffer_data)
    buffer_data.extend(png_data)
    img_length = len(png_data)
    views.append({"buffer": 0, "byteOffset": img_offset, "byteLength": img_length})
    align_4(buffer_data)

    gltf = {
        "asset": {"version": "2.0", "generator": "MewDesktop Textured Ceramic Bowl"},
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "CeramicPetBowl", "mesh": 0}],
        "meshes": [
            {
                "name": "CeramicBowlMesh",
                "primitives": [
                    {"attributes": {"POSITION": 1, "NORMAL": 2, "TEXCOORD_0": 3}, "indices": 0, "material": 0},
                    {"attributes": {"POSITION": 5, "NORMAL": 6, "TEXCOORD_0": 7}, "indices": 4, "material": 1}
                ]
            }
        ],
        "textures": [{"sampler": 0, "source": 0}],
        "images": [{"bufferView": 8, "mimeType": "image/png"}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "materials": [
            {
                "name": "PorcelainCeramic",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicFactor": 0.05,
                    "roughnessFactor": 0.35
                },
                "doubleSided": False
            },
            {
                "name": "CreamyMilk",
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0},
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.15
                },
                "doubleSided": False
            }
        ],
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(buffer_data)}]
    }

    json_bytes = json.dumps(gltf).encode('utf-8')
    while len(json_bytes) % 4 != 0: json_bytes += b' '

    total_len = 12 + 8 + len(json_bytes) + 8 + len(buffer_data)
    glb_header = struct.pack('<4sII', b'glTF', 2, total_len)
    json_chunk_header = struct.pack('<I4s', len(json_bytes), b'JSON')
    bin_chunk_header = struct.pack('<I4s', len(buffer_data), b'BIN\x00')

    out_path = '/Users/macbook/Desktop/work/MewDestop/assets/models/items/ceramic_bowl.glb'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(glb_header)
        f.write(json_chunk_header)
        f.write(json_bytes)
        f.write(bin_chunk_header)
        f.write(buffer_data)
    print(f"Generated Textured Celadon Bowl {out_path} ({total_len} bytes)")

if __name__ == '__main__':
    create_textured_ceramic_bowl()

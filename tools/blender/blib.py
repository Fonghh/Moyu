# Blender 腳本共用工具（用法：pip install bpy==5.3.0，然後 python3 tools/blender/temple.py）
# Blender 腳本共用工具：建模小零件、程序材質（磁磚、水泥污漬、浪板、木板）、烘焙（顏色×AO、發光）、匯出 glb
import bpy, bmesh, math, random, time
import numpy as np
from mathutils import Vector, Matrix

import os
OUT = os.environ.get('MOYU_OUT', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')) + '/'   # 產出的模型、貼圖；確認好再複製到 assets/
os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
PARTS = []

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PARTS.clear()

def lin(hexs):
    c = [int(hexs[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]

_MATS = {}
def mat(name, color, rough=.8, metal=0., kind=None, scale=1., color2=None, emit=None, emit_k=1., axis='X'):
    """kind：tile 二丁掛磁磚、concrete 水泥＋污漬、corr 浪板、plank 木板、stripe 條紋、None 素色"""
    if name in _MATS: return _MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Lk = nt.links
    b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    base = (*lin(color), 1)
    co = N.new('ShaderNodeTexCoord')
    # 牆面用的座標：（水平位置 x+y, 高度 z），直的牆上磁磚才會一排一排橫著
    sp = N.new('ShaderNodeSeparateXYZ'); Lk.new(co.outputs['Object'], sp.inputs['Vector'])
    ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; Lk.new(sp.outputs['X'], ad.inputs[0]); Lk.new(sp.outputs['Y'], ad.inputs[1])
    wc = N.new('ShaderNodeCombineXYZ'); Lk.new(ad.outputs['Value'], wc.inputs['X']); Lk.new(sp.outputs['Z'], wc.inputs['Y'])
    wall = wc.outputs['Vector']
    if kind == 'tile':
        t = N.new('ShaderNodeTexBrick'); t.offset = .5; t.inputs['Scale'].default_value = 1
        Lk.new(wall, t.inputs['Vector'])
        t.inputs['Brick Width'].default_value = .23 * scale; t.inputs['Row Height'].default_value = .065 * scale
        t.inputs['Mortar Size'].default_value = .006 * scale
        t.inputs['Color1'].default_value = base; c2 = lin(color2 or color); t.inputs['Color2'].default_value = (c2[0] * .93, c2[1] * .93, c2[2] * .93, 1)
        mo = lin('#c4beb2'); t.inputs['Mortar'].default_value = (*mo, 1)
        col_out = t.outputs['Color']
    elif kind == 'corr':
        t = N.new('ShaderNodeTexWave'); t.wave_type = 'BANDS'; t.bands_direction = axis; t.inputs['Scale'].default_value = 6 * scale
        Lk.new(wall, t.inputs['Vector'])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        mx.inputs['A'].default_value = base; d = lin(color2 or color); mx.inputs['B'].default_value = (d[0] * .7, d[1] * .7, d[2] * .7, 1)
        Lk.new(t.outputs['Fac'], mx.inputs['Factor']); col_out = mx.outputs['Result']
    elif kind == 'plank':
        t = N.new('ShaderNodeTexBrick'); t.offset = .37
        Lk.new(co.outputs['Object'], t.inputs['Vector'])
        t.inputs['Brick Width'].default_value = 1.8 * scale; t.inputs['Row Height'].default_value = .16 * scale; t.inputs['Mortar Size'].default_value = .008
        t.inputs['Color1'].default_value = base; c2 = lin(color2 or color); t.inputs['Color2'].default_value = (*c2, 1); t.inputs['Mortar'].default_value = (.05, .04, .03, 1)
        col_out = t.outputs['Color']
    elif kind == 'xstripe':   # 只沿 x 變化的條紋（屋瓦一壟一壟）
        t = N.new('ShaderNodeTexWave'); t.wave_type = 'BANDS'; t.bands_direction = 'X'; t.inputs['Scale'].default_value = 4 * scale
        Lk.new(co.outputs['Object'], t.inputs['Vector'])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = base; d = lin(color2 or color); mx.inputs['B'].default_value = (*d, 1)
        Lk.new(t.outputs['Fac'], mx.inputs['Factor']); col_out = mx.outputs['Result']
    elif kind == 'stripe':
        t = N.new('ShaderNodeTexWave'); t.wave_type = 'BANDS'; t.bands_direction = axis; t.inputs['Scale'].default_value = 4 * scale
        Lk.new(wall, t.inputs['Vector'])
        mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = base; d = lin(color2 or color); mx.inputs['B'].default_value = (*d, 1)
        Lk.new(t.outputs['Fac'], mx.inputs['Factor']); col_out = mx.outputs['Result']
    else:
        col_out = None
    # 污漬：雜訊讓顏色有深淺（水泥、舊牆）
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 8
    Lk.new(co.outputs['Object'], nz.inputs['Vector'])
    gm = N.new('ShaderNodeMix'); gm.data_type = 'RGBA'; gm.blend_type = 'MULTIPLY'
    gm.inputs['Factor'].default_value = .4 if kind == 'concrete' else .12
    if col_out: Lk.new(col_out, gm.inputs['A'])
    else: gm.inputs['A'].default_value = base
    ramp = N.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = .35; ramp.color_ramp.elements[0].color = (.68, .65, .6, 1); ramp.color_ramp.elements[1].position = .7; ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    Lk.new(nz.outputs['Fac'], ramp.inputs['Fac']); Lk.new(ramp.outputs['Color'], gm.inputs['B'])
    Lk.new(gm.outputs['Result'], b.inputs['Base Color'])
    if emit:
        b.inputs['Emission Color'].default_value = (*lin(emit), 1); b.inputs['Emission Strength'].default_value = emit_k
    m['emit'] = bool(emit)
    _MATS[name] = m
    return m

def _assign(o, m):
    o.data.materials.clear(); o.data.materials.append(m); PARTS.append(o); return o

def box(sx, sy, sz, x, y, z, m, rz=0., bevel=0.):
    """以底面中心為準：(x, y, z) 是底面中心，z 往上"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + sz / 2))
    o = bpy.context.object; o.scale = (sx, sy, sz); o.rotation_euler[2] = rz
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    if bevel:
        md = o.modifiers.new('bv', 'BEVEL'); md.width = bevel; md.segments = 2; md.limit_method = 'ANGLE'
        bpy.ops.object.modifier_apply(modifier='bv')
    return _assign(o, m)

def cyl(r, h, x, y, z, m, seg=16, r2=None, rx=0., ry=0., rz=0.):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=seg, location=(0, 0, 0))
    else: bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=h, vertices=seg, location=(0, 0, 0))
    o = bpy.context.object
    o.data.transform(Matrix.Translation((0, 0, h / 2)))
    o.rotation_euler = (rx, ry, rz); o.location = (x, y, z)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.shade_smooth()
    return _assign(o, m)

def sphere(r, x, y, z, m, seg=16, sz=1.):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=max(6, seg // 2), location=(x, y, z))
    o = bpy.context.object; o.scale = (1, 1, sz); bpy.ops.object.transform_apply(scale=True); bpy.ops.object.shade_smooth()
    return _assign(o, m)

def torus(R, r, x, y, z, m, rx=0., ry=0., rz=0.):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=16, minor_segments=8, location=(x, y, z), rotation=(rx, ry, rz))
    o = bpy.context.object; bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return _assign(o, m)

def tube(pts, r, m, res=6):
    """沿著一串點做一條圓管（屋脊、燕尾、欄杆扶手）"""
    cu = bpy.data.curves.new('c', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2; cu.resolution_u = res
    sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_endpoint_u = True; sp.order_u = min(4, len(pts))
    o = bpy.data.objects.new('tube', cu); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object; bpy.ops.object.shade_smooth()
    return _assign(o, m)

def text(s, size, x, y, z, m, rx=math.pi / 2, rz=0., depth=.02):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = s; cu.size = size; cu.extrude = depth; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    try: cu.font = bpy.data.fonts.load(FONT)
    except Exception as e: print('font fail', e)
    o = bpy.data.objects.new('txt', cu); bpy.context.scene.collection.objects.link(o)
    o.location = (x, y, z); o.rotation_euler = (rx, 0, rz)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target='MESH'); o = bpy.context.object
    bpy.ops.object.transform_apply(location=True, rotation=True)
    return _assign(o, m)

def mesh_from(verts, faces, m, smooth=False, name='m'):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    return _assign(o, m)

def solidify(o, t):
    bpy.context.view_layer.objects.active = o; md = o.modifiers.new('s', 'SOLIDIFY'); md.thickness = t; md.offset = 0
    bpy.ops.object.modifier_apply(modifier='s'); return o

# ---- 烘焙：全部合成一個網格、自動展 UV，烘出「顏色×環境遮蔽」和「發光」兩張貼圖，匯出 glb ----
def bake_export(name, res=1024, samples=48, ao_dist=1.2, ao_min=.28):
    t0 = time.time()
    sc = bpy.context.scene
    for o in list(sc.objects):
        if o.type != 'MESH': continue
        o.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.select_all(action='DESELECT')
    for o in PARTS: o.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    ob = bpy.context.object; ob.name = name
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=.004, area_weight=0)
    bpy.ops.uv.pack_islands(margin=.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    print(name, 'faces', len(ob.data.polygons), 'verts', len(ob.data.vertices))
    imgs = {k: bpy.data.images.new(f'{name}_{k}', res, res, float_buffer=True) for k in ('col', 'ao', 'emit')}
    def target(img):
        for m in ob.data.materials:
            N = m.node_tree.nodes
            n = N.get('BAKE') or N.new('ShaderNodeTexImage'); n.name = 'BAKE'; n.image = img
            N.active = n; n.select = True
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.render.bake.margin = 6
    target(imgs['col']); sc.cycles.samples = 1
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
    target(imgs['ao']); sc.cycles.samples = samples; bpy.context.scene.world = bpy.context.scene.world or bpy.data.worlds.new('w')
    sc.world.light_settings.distance = ao_dist
    bpy.ops.object.bake(type='AO')
    target(imgs['emit']); sc.cycles.samples = 1
    bpy.ops.object.bake(type='EMIT')
    col = np.array(imgs['col'].pixels[:]).reshape(res, res, 4)
    ao = np.array(imgs['ao'].pixels[:]).reshape(res, res, 4)[..., :1]
    em = np.array(imgs['emit'].pixels[:]).reshape(res, res, 4)
    out = col.copy(); out[..., :3] = col[..., :3] * (ao_min + (1 - ao_min) * ao)   # 角落、縫隙變暗
    fin = bpy.data.images.new(f'{name}_albedo', res, res); fin.pixels = out.ravel().tolist()
    emi = bpy.data.images.new(f'{name}_emissive', res, res); e2 = em.copy(); e2[..., 3] = 1; emi.pixels = e2.ravel().tolist()
    has_emit = em[..., :3].max() > .01
    # 換成一個材質：烘好的顏色貼圖（＋發光貼圖）
    m = bpy.data.materials.new(name + '_baked'); m.use_nodes = True; N = m.node_tree.nodes; b = N['Principled BSDF']
    b.inputs['Roughness'].default_value = .78
    tn = N.new('ShaderNodeTexImage'); tn.image = fin; m.node_tree.links.new(tn.outputs['Color'], b.inputs['Base Color'])
    if has_emit:
        te = N.new('ShaderNodeTexImage'); te.image = emi; m.node_tree.links.new(te.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1
    ob.data.materials.clear(); ob.data.materials.append(m)
    for p in ob.data.polygons: p.material_index = 0
    for img, nm in ((fin, 'albedo'), (emi, 'emissive')):
        img.filepath_raw = OUT + f'{name}_{nm}.png'; img.file_format = 'PNG'; img.save()
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT + f'{name}.glb', export_format='GLB', use_selection=True, export_image_format='JPEG', export_jpeg_quality=82, export_apply=True)
    print(name, 'baked+exported in', round(time.time() - t0, 1), 's, emissive', has_emit)
    return ob

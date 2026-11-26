# 機車：復古速克達（車頭朝 -Y，匯出成 glb 後車頭是 +Z）。圓潤的車殼、鉻合金、輪胎輪圈、後照鏡、儀表、車牌
# 用法：MOYU_OUT=輸出資料夾 PAINT='#8fd3bd' NAME=scooter python3 scooter.py [preview]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *
import blib

PAINT = os.environ.get('PAINT', '#8fd3bd'); NAME = os.environ.get('NAME', 'scooter')
reset(); random.seed(7)

def rbox(sx, sy, sz, x, y, z, m, rx=0., ry=0., rz=0., r=.03, seg=3, sub=0):
    """圓角方塊（先倒角、可再細分變更圓）：車殼的基本形狀；(x, y, z) 是中心"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    md = o.modifiers.new('bv', 'BEVEL'); md.width = min(r, min(sx, sy, sz) * .48); md.segments = seg; md.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier='bv')
    if sub:
        md = o.modifiers.new('ss', 'SUBSURF'); md.levels = sub; bpy.ops.object.modifier_apply(modifier='ss')
    o.rotation_euler = (rx, ry, rz); o.location = (x, y, z)
    bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)

def ell(rx_, ry_, rz_, x, y, z, m, rx=0., ry=0., rz=0., seg=20):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=seg, ring_count=seg // 2, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (rx_, ry_, rz_); bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = (rx, ry, rz); o.location = (x, y, z); bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)

def cylx(r, h, x, y, z, m, seg=24, ry=math.pi / 2, rx=0., rz=0.):
    """軸心朝 x 的圓柱（輪子、握把）"""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=seg, location=(x, y, z), rotation=(rx, ry, rz))
    o = bpy.context.object; bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)

def loft(secs, axis, m, R=28, caps=True, sub=0):
    """沿著 y（或 z）一段段放超橢圓的截面，連成一個圓滑的殼。
    axis y：每段 (y, 中心z, 半高, 半寬, 次方)；axis z：每段 (z, 中心y, 半深, 半寬, 次方)"""
    V, F = [], []
    for t, c, h, w, n in secs:
        for i in range(R):
            a = i / R * math.pi * 2; ca, sa = math.cos(a), math.sin(a)
            u = w * math.copysign(abs(ca) ** (2 / n), ca); v = h * math.copysign(abs(sa) ** (2 / n), sa)
            V.append((u, t, c + v) if axis == 'y' else (u, c + v, t))
    for k in range(len(secs) - 1):
        for i in range(R):
            a, b = k * R + i, k * R + (i + 1) % R; F.append((a, b, b + R, a + R))
    if caps:
        for k, rev in ((0, True), (len(secs) - 1, False)):
            t, c, h, w, n = secs[k]; ci = len(V); V.append((0, t, c) if axis == 'y' else (0, c, t))
            for i in range(R):
                a, b = k * R + i, k * R + (i + 1) % R; F.append((ci, b, a) if rev else (ci, a, b))
    o = mesh_from(V, F, m, smooth=True, name='loft')
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    if sub:
        md = o.modifiers.new('ss', 'SUBSURF'); md.levels = sub; bpy.ops.object.modifier_apply(modifier='ss')
    return o

paint = mat('paint', PAINT, .22, .0)
paint2 = mat('paint2', '#f4f1e8', .3)
chrome = mat('chrome', '#d9dde0', .12, 1.)
rubber = mat('rubber', '#1b1b1d', .85)
seatm = mat('seatm', '#3a2c26', .55)
dark = mat('dark', '#2a2c2f', .5, .3)
glass = mat('glass', '#26343c', .05)
lens = mat('lens', '#fff4cf', .1, emit='#fff1c2', emit_k=3.)
tail = mat('tail', '#d3201a', .2, emit='#ff2a1a', emit_k=1.2)
plate = mat('plate', '#f6f6f0', .4)
inkm = mat('inkm', '#1a1a1a', .5)
alu = mat('alu', '#b9bec3', .3, .8)
rimm = mat('rimm', '#c9cdd1', .2, .9)

FY, RY, WR = -.66, .6, .262   # 前輪、後輪軸的 y，輪子半徑

# ---- 輪子：胎、輪圈、輪輻（5 支）、煞車碟、輪軸蓋 ----
for ay in (FY, RY):
    cylx(.185, .1, 0, ay, WR, rimm, 32); cylx(.15, .115, 0, ay, WR, dark, 32)
    torus(.215, .055, 0, ay, WR, rubber, ry=math.pi / 2)
    bpy.context.object.scale = (1, 1, 1)
    for k in range(5):
        a = k * math.pi * 2 / 5
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, ay + math.sin(a) * .09, WR + math.cos(a) * .09))
        o = bpy.context.object; o.scale = (.035, .03, .17); o.rotation_euler = (-a, 0, 0); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        blib._assign(o, rimm)
    cylx(.045, .13, 0, ay, WR, chrome, 16)
    cylx(.1, .012, .06 if ay == FY else -.06, ay, WR, alu, 28)   # 煞車碟
# ---- 前叉（單邊）、避震 ----
tube([(-.13, FY, WR), (-.13, FY + .06, .55), (-.1, FY + .13, .95)], .024, chrome)
tube([(.13, FY, WR), (.13, FY + .06, .55), (.1, FY + .13, .95)], .024, chrome)
tube([(.0, FY, .52), (.0, FY + .1, .85)], .03, dark)
# ---- 前擋泥板：沿著輪子的弧形薄殼 ----
loft([(FY - .3, .33, .016, .085, 3), (FY - .2, .46, .016, .095, 3), (FY - .05, .54, .016, .1, 3), (FY + .12, .54, .016, .1, 3), (FY + .26, .45, .016, .095, 3), (FY + .3, .4, .016, .085, 3)], 'y', paint)
# ---- 擋腿板（往後傾的 S 形）、龍頭罩 ----
loft([(.27, -.27, .09, .24, 2.6), (.45, -.34, .075, .22, 2.6), (.7, -.45, .06, .2, 2.6), (.92, -.5, .07, .17, 2.6)], 'z', paint)
loft([(.9, -.5, .09, .15, 2.4), (.99, -.5, .15, .2, 2.2), (1.1, -.51, .14, .17, 2.2), (1.16, -.51, .09, .1, 2.2)], 'z', paint)
rbox(.05, .02, .55, 0, -.55, .62, chrome, rx=-.28, r=.008)   # 擋腿板前面的鉻條
# ---- 腳踏板：橡膠踏墊、兩邊鋁條 ----
loft([(-.3, .27, .035, .21, 3), (-.1, .26, .035, .25, 3), (.25, .26, .035, .25, 3), (.38, .28, .04, .22, 3)], 'y', paint)
rbox(.34, .5, .02, 0, 0.0, .31, rubber, r=.008)
for sx in (-.26, .26): rbox(.025, .6, .045, sx, 0.02, .28, alu, r=.01)
# ---- 車身：圓滑的殼蓋住後輪上半、側蓋、尾端 ----
loft([(.0, .3, .12, .19, 2.4), (.1, .38, .2, .23, 2.4), (.3, .46, .2, .245, 2.4), (.45, .52, .17, .245, 2.4), (.7, .56, .15, .23, 2.4), (.9, .58, .1, .19, 2.4), (1.02, .58, .06, .13, 2.4), (1.07, .58, .035, .07, 2.4)], 'y', paint)
loft([(-.02, .72, .06, .13, 2.5), (.15, .73, .07, .17, 2.5), (.5, .74, .08, .18, 2.5), (.8, .73, .08, .17, 2.5), (.96, .72, .065, .12, 2.5), (1.0, .72, .04, .08, 2.5)], 'y', seatm)   # 坐墊
# ---- 排氣管 ----
cylx(.05, .55, .2, .6, .17, chrome, 14, ry=0, rx=math.pi / 2); cylx(.06, .38, .2, .75, .17, chrome, 14, ry=0, rx=math.pi / 2)
cylx(.045, .06, .2, 1.0, .17, dark, 10, ry=0, rx=math.pi / 2)
# ---- 後避震（彈簧）、鏈蓋、引擎 ----
# ---- 尾燈、方向燈、車牌 ----
rbox(.22, .04, .08, 0, 1.065, .62, tail, r=.012)
for sx in (-.14, .14): ell(.028, .028, .028, sx, 1.045, .6, mat('amber', '#ff9a1a', .2, emit='#ff8a10', emit_k=1.2))
rbox(.3, .012, .14, 0, 1.06, .5, plate, r=.01)
text('TAO-8888', .045, 0, 1.068, .5, inkm, rx=math.pi / 2, rz=math.pi, depth=.003)
# ---- 龍頭：橫桿、握把、剎車桿、後照鏡 ----
tube([(-.33, -.5, 1.13), (-.18, -.52, 1.16), (.18, -.52, 1.16), (.33, -.5, 1.13)], .012, chrome)
for sx in (-.33, .33):
    cylx(.017, .13, sx * 1.07, -.5, 1.13, rubber, 12); rbox(.02, .12, .015, sx * .93, -.58, 1.115, chrome, rz=sx * -.5)
    tube([(sx * .95, -.52, 1.17), (sx * .97, -.5, 1.28), (sx * .98, -.47, 1.36)], .006, chrome)
    ell(.055, .01, .04, sx * .98, -.455, 1.39, chrome, rx=.25); ell(.048, .006, .033, sx * .98, -.446, 1.392, glass, rx=.25)
# ---- 大燈、儀表 ----
ell(.115, .06, .115, 0, -.62, 1.03, chrome, rx=math.pi / 2)
ell(.095, .04, .095, 0, -.65, 1.03, lens, rx=math.pi / 2)
torus(.1, .01, 0, -.655, 1.03, chrome, rx=math.pi / 2)
rbox(.2, .12, .035, 0, -.5, 1.2, dark, rx=-.35, r=.012)
cylx(.055, .02, 0, -.52, 1.22, glass, 20, ry=0, rx=1.2)

# ---- 腳架、前置物鉤 ----
tube([(-.17, .45, .3), (-.2, .5, .1), (-.2, .56, .035)], .012, dark)
tube([(0, -.64, .72), (0, -.72, .76), (0, -.7, .8)], .008, chrome)

if __name__ == '__main__':
    if 'preview' in sys.argv:
        sc = bpy.context.scene
        sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 80; sc.cycles.use_denoising = True
        sc.render.resolution_x, sc.render.resolution_y = 700, 520; sc.render.film_transparent = False
        sc.view_settings.view_transform = 'Filmic' if hasattr(sc.view_settings, 'view_transform') else 'Standard'
        w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (.72, .78, .85, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = .9
        bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0)); g = bpy.context.object; g.data.materials.append(mat('floor', '#8d8a84', .9))
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.lens = 50
        for loc, e, sz in (((2.5, -3, 3.5), 320, 3), ((-3, 2, 2.5), 160, 3)):
            L = bpy.data.objects.new('L', bpy.data.lights.new('L', 'AREA')); sc.collection.objects.link(L); L.data.energy = e; L.data.size = sz; L.location = loc
            L.rotation_euler = (Vector((0, 0, .6)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        for nm, loc in (('q34', (-2.6, -3.0, 1.5)), ('side', (-4.2, 0, .85)), ('rear', (2.0, 3.4, 1.7)), ('top', (-1.4, -1.8, 3.2))):
            cam.location = loc; cam.rotation_euler = (Vector((0, .1, .65)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = OUT + f'{NAME}_{nm}.png'; bpy.ops.render.render(write_still=True); print('rendered', nm)
    else:
            # PART=paint 只留車殼（遊戲裡依每台的顏色染）、PART=rest 其他零件（輪胎、坐墊、鉻、燈）
        part = os.environ.get('PART')
        if part:
            keep = [o for o in PARTS if (o.data.materials[0].name.startswith('paint') and o.data.materials[0].name != 'paint2') == (part == 'paint')]
            for o in PARTS:
                if o not in keep: bpy.data.objects.remove(o, do_unlink=True)
            PARTS[:] = keep
            if part == 'rest':   # 零件面數多的減面（遊戲裡停在路邊的也用這台）
                for o in keep:
                    if len(o.data.polygons) > 150:
                        bpy.context.view_layer.objects.active = o; md = o.modifiers.new('dc', 'DECIMATE'); md.ratio = .3 if len(o.data.polygons) > 600 else .5
                        bpy.ops.object.modifier_apply(modifier='dc')
        bake_export(NAME, res=int(os.environ.get('RES', 1024)), samples=40, ao_dist=.35, ao_min=.5)

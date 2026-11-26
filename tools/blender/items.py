# 奇物、雜物、特別生物的圖（取代 emoji）：每個東西蓋好、打光，渲染成 448×224 透明背景的 png
# 用法：MOYU_OUT=輸出資料夾 python3 items.py [id ...]
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *
import blib

def rbox(sx, sy, sz, x, y, z, m, rx=0., ry=0., rz=0., r=.03, seg=3, sub=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    md = o.modifiers.new('bv', 'BEVEL'); md.width = min(r, min(sx, sy, sz) * .48); md.segments = seg; md.limit_method = 'ANGLE'
    bpy.ops.object.modifier_apply(modifier='bv')
    if sub: md = o.modifiers.new('ss', 'SUBSURF'); md.levels = sub; bpy.ops.object.modifier_apply(modifier='ss')
    o.rotation_euler = (rx, ry, rz); o.location = (x, y, z)
    bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)
def ell(a, b, c, x, y, z, m, rx=0., ry=0., rz=0., seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=seg, ring_count=seg // 2, location=(0, 0, 0))
    o = bpy.context.object; o.scale = (a, b, c); bpy.ops.object.transform_apply(scale=True)
    o.rotation_euler = (rx, ry, rz); o.location = (x, y, z); bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)
def cyl2(r, h, x, y, z, m, seg=32, rx=0., ry=0., rz=0., r2=None):
    if r2 is None: bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=seg, location=(0, 0, 0))
    else: bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=h, vertices=seg, location=(0, 0, 0))
    o = bpy.context.object; o.rotation_euler = (rx, ry, rz); o.location = (x, y, z)
    bpy.ops.object.transform_apply(location=True, rotation=True); bpy.ops.object.shade_smooth()
    return blib._assign(o, m)
def loft(secs, axis, m, R=28, caps=True, sub=0):
    """axis y：(y, 中心z, 半高, 半寬, 次方)；axis z：(z, 中心y, 半深, 半寬, 次方)；axis x：(x, 中心z, 半高, 半寬(y), 次方)"""
    V, F = [], []
    for t, c, h, w, n in secs:
        for i in range(R):
            a = i / R * math.pi * 2; ca, sa = math.cos(a), math.sin(a)
            u = w * math.copysign(abs(ca) ** (2 / n), ca); v = h * math.copysign(abs(sa) ** (2 / n), sa)
            V.append((u, t, c + v) if axis == 'y' else (u, c + v, t) if axis == 'z' else (t, u, c + v))
    for k in range(len(secs) - 1):
        for i in range(R): a, b = k * R + i, k * R + (i + 1) % R; F.append((a, b, b + R, a + R))
    if caps:
        for k, rev in ((0, True), (len(secs) - 1, False)):
            t, c, h, w, n = secs[k]; ci = len(V); V.append((0, t, c) if axis == 'y' else (0, c, t) if axis == 'z' else (t, 0, c))
            for i in range(R): a, b = k * R + i, k * R + (i + 1) % R; F.append((ci, b, a) if rev else (ci, a, b))
    o = mesh_from(V, F, m, smooth=True, name='loft')
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    if sub: md = o.modifiers.new('ss', 'SUBSURF'); md.levels = sub; bpy.ops.object.modifier_apply(modifier='ss')
    return o
def chain(pts, r0, r1, m, step=.6):
    """一串越來越細的球（章魚腳、鱷魚尾巴的鱗片）"""
    n = len(pts)
    for i in range(n):
        t = i / max(1, n - 1); ell(*(3 * [r0 + (r1 - r0) * t]), *pts[i], m, seg=12)
def M(name, color, rough=.5, metal=0., alpha=1., emit=None, coat=0.):
    m = mat(name, color, rough, metal, emit=emit)
    b = m.node_tree.nodes['Principled BSDF']
    if alpha < 1: b.inputs['Alpha'].default_value = alpha; m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
    if coat: b.inputs['Coat Weight'].default_value = coat
    return m

# ---------- 每個東西 ----------
def boot():   # 破靴子：舊皮革、鞋底、破洞、泥巴
    lea = M('lea', '#6a4524', .62); sole = M('sole', '#2a2522', .8); mud = M('mud', '#4a3b28', .95)
    loft([(.0, .0, .2, .16, 2.4), (.25, -.02, .2, .15, 2.4), (.55, -.04, .2, .15, 2.3), (.75, -.03, .21, .155, 2.3)], 'z', lea)   # 靴筒
    loft([(-.12, .05, .09, .15, 2.4), (.05, .08, .16, .16, 2.3), (.3, .07, .13, .15, 2.3), (.45, .06, .08, .12, 2.6), (.52, .05, .04, .08, 2.8)], 'y', lea)   # 腳背
    rbox(.33, .72, .05, 0, .2, -.02, sole, r=.02); rbox(.32, .18, .12, 0, -.08, .02, sole, r=.03)
    ell(.06, .05, .03, .1, .35, .15, mud); ell(.08, .02, .05, -.12, .05, .3, mud); ell(.05, .02, .04, .13, -.02, .55, mud)
    torus(.165, .012, 0, -.03, .75, M('rim', '#4a2f18', .6))
def boba():   # 喝一半的珍奶：透明杯、奶茶、珍珠、封膜、粗吸管
    cup = M('cup', '#ffffff', .05, alpha=.18); tea = M('tea', '#c79a6a', .3, alpha=.55); pearl = M('pearl', '#1a1210', .15)
    cyl2(.3, .95, 0, 0, .475, cup, 48, r2=.36)
    cyl2(.288, .42, 0, 0, .23, tea, 48, r2=.31)
    random.seed(3)
    for k in range(34):
        a = random.uniform(0, 6.28); r = random.uniform(.12, .25); ell(.05, .05, .05, math.cos(a) * r, math.sin(a) * r, .06 + random.uniform(0, .1), pearl, seg=12)
    cyl2(.365, .02, 0, 0, .955, M('film', '#f2ecd8', .4, alpha=.85), 48)
    cyl2(.04, 1.3, .06, .02, .9, M('straw', '#e9608a', .3), 20, rx=.25, ry=.12)
def airpods():   # 充電盒：亮白圓角、蓋子縫、小燈
    w = M('w', '#f4f4f2', .2, coat=.6)
    rbox(.6, .26, .5, 0, 0, .25, w, r=.12, seg=6, sub=1)
    ell(.012, .006, .012, 0, -.133, .22, M('led', '#4ee06a', .2, emit='#3cff60'))
    cyl2(.035, .02, 0, 0, .0, M('steel', '#c8ccd0', .2, 1.), 24)
def ball():   # 足球：白色皮面＋紅藍綠的彎曲色帶（主辦三國的顏色）
    ell(.5, .5, .5, 0, 0, .5, M('bw', '#f5f4ef', .35, coat=.4), seg=40)
    for k, (c, rx, ry) in enumerate((('#d0312d', .4, .2), ('#1f5fbf', -.5, 1.1), ('#25a35a', 1.2, -.4))):
        torus(.5, .03, 0, 0, .5, M('band' + str(k), c, .4), rx=rx, ry=ry)
        bpy.context.object.scale = (1.008, 1.008, 1.008)
    for k in range(6):
        a = k * 1.05; ell(.09, .09, .02, math.cos(a) * .35, math.sin(a) * .35, .5 + .35 * (k % 2 - .5), M('dot', '#1c1c1c', .5), rx=.4 * k)
def card():   # 閃卡：黃框、彩虹雷射面、護貝套（沒有任何角色圖）
    holo = mat('holo', '#ffffff', .15, .8)
    nt = holo.node_tree; N = nt.nodes; co = N.new('ShaderNodeTexCoord'); wv = N.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 3; wv.inputs['Distortion'].default_value = 6
    nt.links.new(co.outputs['Object'], wv.inputs['Vector'])
    rp = N.new('ShaderNodeValToRGB'); es = rp.color_ramp.elements; es[0].color = (1, .3, .6, 1); es[1].color = (.3, .9, 1, 1); e = es.new(.5); e.color = (1, .95, .3, 1)
    nt.links.new(wv.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], N['Principled BSDF'].inputs['Base Color'])
    rbox(.66, .02, .92, 0, 0, .46, M('frame', '#f2c230', .4), r=.03)
    rbox(.56, .025, .5, 0, 0, .6, holo, r=.01)
    rbox(.56, .025, .24, 0, 0, .19, M('txt', '#fbf6e2', .6), r=.01)
    for k in range(3): rbox(.4 - k * .08, .03, .025, -.06, 0, .25 - k * .055, M('ln', '#6b5a3a', .5), r=.004)
    for k in range(5):   # 星星（簡單的五芒形）
        a = k * 1.2566; ell(.05, .03, .05, .17 + math.cos(a) * .0, -.016, .8, M('star', '#ffffff', .2, emit='#fffbe8'), rz=a) if k == 0 else None
    rbox(.72, .04, .98, 0, 0, .46, M('sleeve', '#ffffff', .02, alpha=.12), r=.02)
def plush():   # 怪物布偶（通用造型）：毛絨身體、小圓耳朵、鈕扣眼睛、縫線笑臉
    fur = M('fur', '#b98a5e', .95); belly = M('bel', '#efd9b6', .95); eye = M('eye', '#151515', .1); st = M('stitch', '#4a2c18', .7)
    ell(.36, .32, .38, 0, 0, .4, fur); ell(.26, .1, .26, 0, -.24, .4, belly)
    ell(.34, .32, .3, 0, 0, .98, fur)
    for sx in (-.26, .26): ell(.11, .07, .11, sx, .02, 1.25, fur); ell(.06, .03, .06, sx, -.03, 1.25, belly)
    for sx in (-.12, .12): ell(.06, .03, .06, sx, -.28, 1.02, eye); ell(.015, .01, .015, sx - .02, -.305, 1.04, M('hl', '#ffffff', .1))
    ell(.05, .03, .035, 0, -.31, .93, M('nose', '#5a3420', .3))
    for k in range(5): ell(.012, .01, .03, -.08 + k * .04, -.305, .86 + .02 * abs(k - 2), st)
    for sx in (-.38, .38): ell(.11, .1, .2, sx, -.05, .5, fur, ry=sx * -1.2)
    for sx in (-.18, .18): ell(.13, .16, .1, sx, -.08, .06, fur)
def switch2():   # 遊戲機：黑色主機、螢幕、左右手把（藍、紅）、搖桿、按鈕
    body = M('body', '#202226', .35); scr = M('scr', '#0d1622', .05, emit='#1c3a5c'); bl = M('bl', '#2f7fd9', .4); rd = M('rd', '#e2463b', .4)
    rbox(1.2, .1, .58, 0, 0, .29, body, r=.03); rbox(1.06, .105, .5, 0, -.005, .3, scr, r=.01)
    rbox(.28, .12, .58, -.74, 0, .29, bl, r=.1, seg=5); rbox(.28, .12, .58, .74, 0, .29, rd, r=.1, seg=5)
    for sx, sz in ((-.74, .38), (.74, .2)): cyl2(.06, .06, sx, -.07, sz, M('stick', '#1a1a1a', .6), 20, rx=1.5708); ell(.065, .03, .065, sx, -.1, sz, M('stick', '#1a1a1a', .6))
    for k, (dx, dz) in enumerate(((0, .08), (.07, 0), (0, -.08), (-.07, 0))):
        ell(.025, .015, .025, .74 + dx, -.07, .4 + dz, M('btn', '#111111', .3)); ell(.025, .015, .025, -.74 + dx, -.07, .18 + dz, M('btn', '#111111', .3))
def iphone():   # 手機背面：鈦金屬框、霧面玻璃、三鏡頭（沒有商標）
    fr = M('fr', '#a69d90', .25, 1.); back = M('back', '#4a5a6b', .45); lens = M('lens', '#0c0c10', .05); ring = M('ring', '#8e877c', .2, 1.)
    rbox(.5, .06, 1.02, 0, 0, .51, fr, r=.08, seg=6); rbox(.47, .065, .99, 0, 0, .51, back, r=.075, seg=6)
    rbox(.24, .08, .24, -.09, -.01, .85, M('bump', '#55657a', .3), r=.05, seg=5)
    for (dx, dz) in ((-.04, .04), (-.04, -.06), (.05, -.01)):
        cyl2(.045, .03, -.09 + dx, -.05, .85 + dz, ring, 32, rx=1.5708); cyl2(.035, .035, -.09 + dx, -.055, .85 + dz, lens, 32, rx=1.5708)
    ell(.02, .01, .02, .03, -.05, .93, M('flash', '#fff6d0', .2))
def rtx():   # 顯示卡：深灰外殼、銀色飾條、三顆風扇、背板、金手指
    sh = M('sh', '#2b2d31', .35, .6); ac = M('ac', '#c9cdd2', .25, 1.); fan = M('fan', '#141414', .5)
    rbox(1.5, .16, .5, 0, 0, .25, sh, r=.03); rbox(1.5, .04, .5, 0, .1, .25, M('bp', '#1d1e21', .4, .7), r=.01)
    for k in range(3):
        x = -.48 + k * .48; cyl2(.2, .03, x, -.09, .27, M('hub', '#1f1f1f', .4), 40, rx=1.5708)
        for b in range(9):
            a = b * .698; rbox(.17, .01, .05, x + math.cos(a) * .09, -.1, .27 + math.sin(a) * .09, fan, ry=-a + .3, r=.004)
        cyl2(.05, .04, x, -.11, .27, M('cap', '#2b2b2b', .3), 24, rx=1.5708)
        torus(.205, .01, x, -.095, .27, ac, rx=1.5708)
    rbox(1.5, .17, .03, 0, 0, .51, ac, r=.01)
    rbox(.6, .04, .06, -.2, 0, -.02, M('gold', '#d4a73a', .25, 1.), r=.004)
    rbox(.12, .08, .06, .55, 0, .53, M('pwr', '#111111', .5), r=.01)
def btc():   # 實體比特幣：金色硬幣、邊緣齒紋、B 字和兩條直線
    au = M('au', '#e6b23a', .22, 1.)
    cyl2(.5, .1, 0, 0, .5, au, 64, rx=1.5708)
    torus(.47, .02, 0, -.05, .5, au, rx=1.5708)
    for k in range(60): a = k * .1047; rbox(.014, .1, .03, math.cos(a) * .5, 0, .5 + math.sin(a) * .5, au, ry=-a, r=.003)
    au2 = M('au4', '#b8862a', .3, 1.)
    text('B', .62, 0, -.07, .5, au2, rx=1.5708, depth=.025)
    for dx in (-.07, .07): rbox(.04, .04, .14, dx, -.07, .82, au2, r=.006); rbox(.04, .04, .14, dx, -.07, .18, au2, r=.006)
def gold():   # 金條：梯形、壓印 999.9
    au = M('au2', '#f0bf3c', .18, 1.)
    V = [(-.6, -.3, 0), (.6, -.3, 0), (.6, .3, 0), (-.6, .3, 0), (-.48, -.2, .26), (.48, -.2, .26), (.48, .2, .26), (-.48, .2, .26)]
    mesh_from(V, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], au, name='bar')
    text('999.9', .13, 0, 0, .27, M('au3', '#c9951f', .3, 1.), rx=0, depth=.008)
def octopus():   # 八爪章魚：圓圓的頭、眼睛、八隻往外捲的腳（吸盤）
    sk = M('sk', '#c4553a', .45, coat=.3); sk2 = M('sk2', '#e9a08a', .5); eye = M('oeye', '#f2e6b8', .2); pup = M('pup', '#111111', .1)
    ell(.36, .32, .42, 0, .05, .75, sk); ell(.3, .28, .2, 0, 0, .4, sk)
    for sx in (-.2, .2): ell(.07, .05, .07, sx, -.24, .5, eye); ell(.03, .02, .03, sx, -.285, .5, pup)
    for k in range(8):
        a = k * .785 + .2; pts = []
        for i in range(18):
            t = i / 17; r = .2 + t * .75; cur = t * 2.2
            pts.append((math.cos(a + cur * .35) * r, math.sin(a + cur * .35) * r * .8 - .05, .3 - t * .28 + .12 * math.sin(t * 3.1) * (k % 2)))
        chain(pts, .1, .025, sk)
        for i in range(2, 16, 2): ell(.022, .022, .01, pts[i][0], pts[i][1], pts[i][2] - .07 + .045 * i / 16, sk2, seg=10)
def croc():   # 史前巨鱷：長吻、背上一排鱗甲、粗尾巴、四隻腳
    sk = M('csk', '#4b5a33', .6); bel = M('cbel', '#a7a17a', .7); sc = M('csc', '#38452a', .7)
    loft([(-1.6, .1, .05, .05, 2.2), (-1.1, .14, .08, .1, 2.2), (-.6, .18, .12, .17, 2.3), (-.1, .22, .16, .26, 2.3), (.4, .24, .17, .3, 2.3), (.8, .23, .15, .24, 2.3), (1.05, .22, .12, .16, 2.4), (1.25, .2, .09, .14, 2.4), (1.6, .16, .05, .07, 2.4), (1.75, .15, .03, .04, 2.4)], 'x', sk)
    for k in range(20): x = -1.3 + k * .13; cyl2(.03, .07, x, -.06, .22 + .12 * (1 - abs(x) / 1.6) + .04, sc, 6, r2=.0); cyl2(.03, .07, x, .06, .22 + .12 * (1 - abs(x) / 1.6) + .04, sc, 6, r2=.0)
    for sx in (-.08, .08): ell(.04, .035, .035, 1.0, sx, .34, M('ceye', '#c9a227', .2))
    for (x, y) in ((.5, -.28), (.5, .28), (-.4, -.32), (-.4, .32)):
        loft([(.24, y * .6, .06, .07, 2.2), (.12, y * .95, .05, .06, 2.2), (.02, y * 1.1, .03, .08, 2.2)], 'z', sk) if False else None
        ell(.08, .13, .06, x, y, .12, sk, rx=.5 if y > 0 else -.5); ell(.09, .07, .03, x + .05, y * 1.25, .03, sk)
    for k in range(9): rbox(.02, .02, .05, 1.2 + k * .055, -.07, .17, M('teeth', '#f2efe2', .4), r=.005); rbox(.02, .02, .05, 1.2 + k * .055, .07, .17, M('teeth', '#f2efe2', .4), r=.005)
    ell(.5, .26, .06, .3, 0, .1, bel)

ITEMS = {'boot': boot, 'boba': boba, 'airpods': airpods, 'ball': ball, 'card': card, 'labubu': plush, 'switch2': switch2, 'iphone': iphone, 'rtx': rtx, 'btc': btc, 'gold': gold, 'octopus': octopus, 'croc': croc}
VIEW = {'croc': (35, -28), 'octopus': (55, -20), 'gold': (35, -30), 'rtx': (20, -25), 'iphone': (15, -25), 'card': (12, -18), 'switch2': (14, -10), 'btc': (10, -15)}

def render_item(k):
    reset(); random.seed(5); blib._MATS.clear() if hasattr(blib, '_MATS') else None
    ITEMS[k]()
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 64; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 448, 224; sc.render.film_transparent = True
    try: sc.view_settings.view_transform = 'Filmic'
    except Exception: pass
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (.85, .88, .92, 1); bg.inputs['Strength'].default_value = .8
    # 外框：照所有東西的大小決定鏡頭
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in sc.objects:
        if o.type != 'MESH': continue
        for v in o.bound_box:
            p = o.matrix_world @ Vector(v); lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p))
    cen = (lo + hi) / 2; size = (hi - lo).length
    el_, az = VIEW.get(k, (22, -32))
    d = size * 3; e, a = math.radians(el_), math.radians(az)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.location = cen + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
    # 投影到鏡頭平面算需要多寬
    bpy.context.view_layer.update(); inv = cam.matrix_world.inverted(); xs, ys = [], []
    for o in sc.objects:
        if o.type != 'MESH': continue
        for v in o.bound_box: p = inv @ (o.matrix_world @ Vector(v)); xs.append(p.x); ys.append(p.y)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cam.location = cam.matrix_world @ Vector((cx, cy, 0))
    cam.data.ortho_scale = max(max(xs) - min(xs), (max(ys) - min(ys)) * 2) * 1.12
    for loc, en, sz in (((2, -3, 4), 500, 3), ((-3, -1, 2), 160, 4), ((0, 3, 3), 220, 3)):
        L = bpy.data.objects.new('L', bpy.data.lights.new('L', 'AREA')); sc.collection.objects.link(L); L.data.energy = en * size * size * .25; L.data.size = sz * size * .5
        L.location = cen + Vector(loc) * size * .9; L.rotation_euler = (cen - L.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = OUT + f'item_{k}.png'; bpy.ops.render.render(write_still=True); print('rendered', k)

for k in (sys.argv[1:] or list(ITEMS)):
    render_item(k)

# 街景地面 demo：柏油（碎石、裂縫、補丁、油漬）、路緣、排水溝、人字磚人行道、藍欄杆、擋車柱、落葉、雜草、積水＋新機車
# 用法：MOYU_OUT=輸出資料夾 python3 streetdemo.py
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scooter                       # 先把機車蓋好（不渲染）
from blib import *
import blib

random.seed(11)
sc = bpy.context.scene
objs_scooter = [o for o in bpy.data.objects if o.type in ('MESH',)]
em = bpy.data.objects.new('scooterRoot', None); sc.collection.objects.link(em)
for o in objs_scooter: o.parent = em
em.location = (2.3, 1.2, 0.0); em.rotation_euler = (0, 0, math.pi / 2 + .08)

# ---------- 材質小工具 ----------
def newmat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    b = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, b
def node(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k in n.inputs: n.inputs[k].default_value = v
        else: setattr(n, k, v)
    return n
def link(nt, a, b):
    if isinstance(a, (tuple, list)): b.default_value = a    # 常數色直接填進去
    else: nt.links.new(a, b)
def ramp(nt, src, stops):
    r = nt.nodes.new('ShaderNodeValToRGB'); link(nt, src, r.inputs['Fac'])
    es = r.color_ramp.elements
    while len(es) > len(stops): es.remove(es[-1])
    while len(es) < len(stops): es.new(.5)
    for e, (p, c) in zip(es, stops):
        e.position = p; e.color = c if len(c) == 4 else (*c, 1)
    return r
def noise(nt, co, scale, detail=6, rough=.55):
    n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=detail, Roughness=rough); link(nt, co, n.inputs['Vector']); return n
def mathn(nt, op, a, b=None, val=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    link(nt, a, n.inputs[0])
    if b is not None: link(nt, b, n.inputs[1])
    elif val is not None: n.inputs[1].default_value = val
    return n
def mixc(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'
    link(nt, fac, n.inputs['Factor']); link(nt, a, n.inputs['A']); link(nt, b, n.inputs['B']); return n.outputs['Result']
def lc(h, k=1.): c = lin(h); return (c[0] * k, c[1] * k, c[2] * k, 1)

# ---------- 柏油：碎石粒、裂縫、補丁、油漬、輪胎痕 ----------
def asphalt_mat():
    m, nt, b = newmat('asphalt'); co = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    wear = noise(nt, co, 1.6, 7).outputs['Fac']                       # 大面積的深淺
    fine = noise(nt, co, 900, 2, .6).outputs['Fac']                  # 碎石粒
    mid = noise(nt, co, 60, 3).outputs['Fac']
    base = ramp(nt, wear, [(.3, lc('#33343a')), (.7, lc('#4d4e54'))]).outputs['Color']
    grit = ramp(nt, fine, [(.42, (0, 0, 0, 1)), (.58, (1, 1, 1, 1))]).outputs['Color']
    col = mixc(nt, mathn(nt, 'MULTIPLY', ramp(nt, fine, [(.5, (0, 0, 0, 1)), (.62, (1, 1, 1, 1))]).outputs['Color'], val=.35).outputs[0], base, lc('#8c8d92'))
    # 裂縫（Voronoi 邊緣距離），只在某些區域出現
    vo = node(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', **{'Scale': .85}); link(nt, co, vo.inputs['Vector'])
    vo2 = node(nt, 'ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', **{'Scale': 5.5}); link(nt, co, vo2.inputs['Vector'])
    area = ramp(nt, noise(nt, co, .5, 3).outputs['Fac'], [(.48, (0, 0, 0, 1)), (.62, (1, 1, 1, 1))]).outputs['Color']
    crack1 = ramp(nt, vo.outputs['Distance'], [(0, (1, 1, 1, 1)), (.009, (0, 0, 0, 1))]).outputs['Color']
    crack2 = ramp(nt, vo2.outputs['Distance'], [(0, (1, 1, 1, 1)), (.012, (0, 0, 0, 1))]).outputs['Color']
    area2 = ramp(nt, noise(nt, co, .3, 3).outputs['Fac'], [(.55, (0, 0, 0, 1)), (.68, (1, 1, 1, 1))]).outputs['Color']
    crack = mathn(nt, 'MULTIPLY', mathn(nt, 'MAXIMUM', mathn(nt, 'MULTIPLY', crack1, area2).outputs[0], mathn(nt, 'MULTIPLY', crack2, area).outputs[0]).outputs[0], ramp(nt, noise(nt, co, 3, 2).outputs['Fac'], [(.35, (0, 0, 0, 1)), (.55, (1, 1, 1, 1))]).outputs['Color']).outputs[0]
    col = mixc(nt, crack, col, lc('#0e0e10'))
    # 補丁：比較深、比較平滑
    patch = ramp(nt, noise(nt, co, .22, 2, .4).outputs['Fac'], [(.58, (0, 0, 0, 1)), (.6, (1, 1, 1, 1))]).outputs['Color']
    col = mixc(nt, mathn(nt, 'MULTIPLY', patch, val=.8).outputs[0], col, lc('#26272b'))
    # 油漬、輪胎痕
    oil = ramp(nt, noise(nt, co, .9, 5).outputs['Fac'], [(.62, (0, 0, 0, 1)), (.72, (1, 1, 1, 1))]).outputs['Color']
    col = mixc(nt, mathn(nt, 'MULTIPLY', oil, val=.8).outputs[0], col, lc('#16161a'))
    link(nt, col, b.inputs['Base Color'])
    rough = mixc(nt, oil, ramp(nt, fine, [(.4, lc('#ffffff', .95) ), (.6, lc('#ffffff', .78))]).outputs['Color'], (.18, .18, .18, 1))
    link(nt, rough, b.inputs['Roughness'])
    h = mathn(nt, 'MULTIPLY', fine, val=1.0).outputs[0]
    bump = node(nt, 'ShaderNodeBump', Strength=.5, Distance=.01); link(nt, mathn(nt, 'SUBTRACT', mathn(nt, 'ADD', fine, mid).outputs[0], crack).outputs[0], bump.inputs['Height'])
    link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    return m
def concrete_mat(name, color, dirt=.5, scale=6):
    m, nt, b = newmat(name); co = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    big = noise(nt, co, scale * .6, 6).outputs['Fac']; fine = noise(nt, co, 500, 2).outputs['Fac']
    c = mixc(nt, mathn(nt, 'MULTIPLY', ramp(nt, big, [(.35, (0, 0, 0, 1)), (.7, (1, 1, 1, 1))]).outputs['Color'], val=dirt).outputs[0], lc(color), lc(color, .45))
    c = mixc(nt, mathn(nt, 'MULTIPLY', fine, val=.25).outputs[0], c, lc(color, .6))
    link(nt, c, b.inputs['Base Color']); b.inputs['Roughness'].default_value = .88
    bump = node(nt, 'ShaderNodeBump', Strength=.35, Distance=.004); link(nt, fine, bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    return m
def brick_mat(name, color, var=.12):
    m, nt, b = newmat(name); co = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    big = noise(nt, co, 8, 4).outputs['Fac']; fine = noise(nt, co, 700, 2).outputs['Fac']
    c = mixc(nt, ramp(nt, big, [(.3, (0, 0, 0, 1)), (.75, (1, 1, 1, 1))]).outputs['Color'], lc(color, 1 - var * 2), lc(color, 1 + var))
    c = mixc(nt, mathn(nt, 'MULTIPLY', fine, val=.22).outputs[0], c, lc(color, .55))
    # 髒污、苔綠（磚縫邊）
    moss = ramp(nt, noise(nt, co, 1.7, 4).outputs['Fac'], [(.6, (0, 0, 0, 1)), (.78, (1, 1, 1, 1))]).outputs['Color']
    c = mixc(nt, mathn(nt, 'MULTIPLY', moss, val=.45).outputs[0], c, lc('#3b4a2c'))
    link(nt, c, b.inputs['Base Color']); b.inputs['Roughness'].default_value = .84
    bump = node(nt, 'ShaderNodeBump', Strength=.4, Distance=.003); link(nt, fine, bump.inputs['Height']); link(nt, bump.outputs['Normal'], b.inputs['Normal'])
    return m
def paint_mat(name, color, rough=.5, metal=0., worn=.35):
    m, nt, b = newmat(name); co = node(nt, 'ShaderNodeTexCoord').outputs['Object']
    wm = ramp(nt, noise(nt, co, 14, 6).outputs['Fac'], [(.55, (0, 0, 0, 1)), (.75, (1, 1, 1, 1))]).outputs['Color']
    c = mixc(nt, mathn(nt, 'MULTIPLY', wm, val=worn).outputs[0], lc(color), lc('#6b4a2a'))
    link(nt, c, b.inputs['Base Color']); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m
def simple(name, color, rough=.7, metal=0.):
    m, nt, b = newmat(name); b.inputs['Base Color'].default_value = lc(color); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal; return m

ASPH = asphalt_mat(); CURB = concrete_mat('curb', '#a9a79f', .6); GUT = concrete_mat('gutter', '#9a9890', .8)
BR = [brick_mat('b1', '#8d8b86'), brick_mat('b2', '#7d7b77'), brick_mat('b3', '#9a9892'), brick_mat('b4', '#85837e')]
BRR = [brick_mat('r1', '#b9776a'), brick_mat('r2', '#a8665a')]
BLUE = paint_mat('blue', '#1d4f9c', .35, .4, .45); IRON = paint_mat('iron', '#2b2e33', .5, .6, .5)

def obj_from(V, F, m, name):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    if isinstance(m, (list, tuple)):
        for mm in m: me.materials.append(mm)
    else: me.materials.append(m)
    return o
def plane(x0, x1, y0, y1, z, m, name, sub=0):
    return obj_from([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(0, 1, 2, 3)], m, name)
def cubeo(sx, sy, sz, x, y, z, m, rz=0.):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z)); o = bpy.context.object
    o.scale = (sx, sy, sz); o.rotation_euler[2] = rz; bpy.ops.object.transform_apply(scale=True, rotation=True); o.data.materials.append(m); return o

# ---------- 尺寸（公尺）：馬路 x∈[-4.5,0]，路緣、排水溝、人行道、欄杆在 x≈4.6、後面是港池 ----------
Y0, Y1 = -14, 24
plane(-4.5, -.32, Y0, Y1, 0, ASPH, 'road')
plane(-80, -4.5, Y0 - 40, Y1 + 60, -.02, concrete_mat('lot', '#8f8b82', .7, 4), 'lot')   # 馬路另一邊的水泥地
# 排水溝（雨水溝蓋格柵）
cubeo(.3, Y1 - Y0, .02, -.17, (Y0 + Y1) / 2, 0, GUT)
for k in range(8):
    y = -9 + k * 4.4
    cubeo(.28, .6, .03, -.17, y, .005, IRON)
    for s in range(7): cubeo(.24, .022, .04, -.17, y - .24 + s * .08, .012, simple('d', '#101113', .9))
# 路緣石（一節節有縫、有角缺）
for k in range(int((Y1 - Y0) / 1.0)):
    y = Y0 + k * 1.0 + .5; h = .14 + random.uniform(-.006, .006)
    cubeo(.16, .985, h, .08, y, h / 2, CURB)
# 紅線（路邊）：褪色剝落的塗漆
m, nt, b = newmat('redline'); co = node(nt, 'ShaderNodeTexCoord').outputs['Object']
worn = ramp(nt, noise(nt, co, 9, 6).outputs['Fac'], [(.42, (1, 1, 1, 1)), (.58, (0, 0, 0, 1))]).outputs['Color']
b.inputs['Base Color'].default_value = lc('#c4372c'); b.inputs['Roughness'].default_value = .75
tr = node(nt, 'ShaderNodeBsdfTransparent'); mx = node(nt, 'ShaderNodeMixShader'); out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
link(nt, worn, mx.inputs['Fac']); link(nt, tr.outputs['BSDF'], mx.inputs[1]); link(nt, b.outputs['BSDF'], mx.inputs[2]); link(nt, mx.outputs['Shader'], out.inputs['Surface'])
plane(-.62, -.46, Y0, Y1, .003, m, 'redline')
# 中間分隔：白色虛線
mw, ntw, bw = newmat('whiteline'); cow = node(ntw, 'ShaderNodeTexCoord').outputs['Object']
ww = ramp(ntw, noise(ntw, cow, 11, 6).outputs['Fac'], [(.4, (1, 1, 1, 1)), (.6, (0, 0, 0, 1))]).outputs['Color']
bw.inputs['Base Color'].default_value = lc('#e9e8e1'); bw.inputs['Roughness'].default_value = .7
trw = node(ntw, 'ShaderNodeBsdfTransparent'); mxw = node(ntw, 'ShaderNodeMixShader'); outw = [n for n in ntw.nodes if n.type == 'OUTPUT_MATERIAL'][0]
link(ntw, ww, mxw.inputs['Fac']); link(ntw, trw.outputs['BSDF'], mxw.inputs[1]); link(ntw, bw.outputs['BSDF'], mxw.inputs[2]); link(ntw, mxw.outputs['Shader'], outw.inputs['Surface'])
for k in range(8): plane(-4.45, -4.3, Y0 + 1 + k * 5, Y0 + 4 + k * 5, .003, mw, 'dash')
# 人孔蓋（圓盤、放射紋）
mh, nth, bh = newmat('manhole'); coh = node(nth, 'ShaderNodeTexCoord').outputs['Object']
wv = node(nth, 'ShaderNodeTexWave', wave_type='RINGS', **{'Scale': 26, 'Distortion': 2, 'Detail': 2}); link(nth, coh, wv.inputs['Vector'])
bh.inputs['Base Color'].default_value = lc('#3a3a3c'); bh.inputs['Roughness'].default_value = .5; bh.inputs['Metallic'].default_value = .7
bph = node(nth, 'ShaderNodeBump', Strength=.9, Distance=.01); link(nth, wv.outputs['Fac'], bph.inputs['Height']); link(nth, bph.outputs['Normal'], bh.inputs['Normal'])
bpy.ops.mesh.primitive_cylinder_add(radius=.35, depth=.025, vertices=40, location=(-2.4, 3.4, .008)); mo = bpy.context.object; mo.data.materials.append(mh)
bpy.ops.mesh.primitive_torus_add(major_radius=.36, minor_radius=.016, location=(-2.4, 3.4, .014)); mt = bpy.context.object; mt.data.materials.append(simple('ring', '#1c1c1d', .8, .4))

# ---------- 人字磚人行道 ----------
A = .1   # 磚寬 10 公分、長 20 公分
V, Fc, mi = [], [], []
cs, sn = math.cos(math.pi / 4), math.sin(math.pi / 4)
def rot(x, y): return (x * cs - y * sn, x * sn + y * cs)
for gx in range(-120, 330):
    for gy in range(-330, 330):
        f = gx - gy
        if f % 4 == 1: cells = (gx, gy, 2, 1)
        elif f % 4 == 0: cells = (gx, gy, 1, 2)
        else: continue
        x0, y0, w, h = cells; g = .005
        pts = [(x0 * A + g, y0 * A + g), ((x0 + w) * A - g, y0 * A + g), ((x0 + w) * A - g, (y0 + h) * A - g), (x0 * A + g, (y0 + h) * A - g)]
        P = [rot(*p) for p in pts]; cx = sum(p[0] for p in P) / 4; cy = sum(p[1] for p in P) / 4
        X = cx + 4.0 - 2.0; Yv = cy
        if not (.2 < cx + 2.6 < 4.5 and Y0 < cy < Y1): continue
        ox = 2.6   # 把圖樣往 +x 搬到人行道上
        top = .0 + random.uniform(-.0015, .0015) + .02
        b0 = len(V)
        for (px, py) in P: V.append((px + ox, py, 0.0));
        for (px, py) in P: V.append((px + ox, py, top))
        Fc += [(b0 + 4, b0 + 5, b0 + 6, b0 + 7), (b0, b0 + 1, b0 + 5, b0 + 4), (b0 + 1, b0 + 2, b0 + 6, b0 + 5), (b0 + 2, b0 + 3, b0 + 7, b0 + 6), (b0 + 3, b0, b0 + 4, b0 + 7)]
        red = (cx + ox) > 3.55
        mi.append((random.randrange(2) if red else random.randrange(4)) + (4 if red else 0))
print('bricks', len(mi))
bk = obj_from(V, Fc, BR + BRR, 'bricks')
for p, k in zip(bk.data.polygons, [k for k in mi for _ in range(5)]): p.material_index = k
for p in bk.data.polygons: p.use_smooth = False
plane(.16, 4.6, Y0, Y1, -.005, simple('sand', '#5d584f', .95), 'bedding')

# ---------- 藍色欄杆、擋車柱、路燈 ----------
for k in range(0, int((Y1 - Y0) / 1.4)):
    y = Y0 + k * 1.4
    cubeo(.06, .06, 1.0, 4.7, y, .5, BLUE)
    for s in range(11): cubeo(.014, .014, .85, 4.7, y + .1 + s * .11, .5, BLUE)
    if k:
        cubeo(.045, 1.4, .045, 4.7, y - .7, 1.0, BLUE); cubeo(.045, 1.4, .045, 4.7, y - .7, .62, BLUE); cubeo(.04, 1.4, .04, 4.7, y - .7, .16, BLUE)
for k in range(5):   # 擋車柱：藍色造型圓柱＋鑄鐵花紋盤
    y = -4 + k * 4.2; bpy.ops.mesh.primitive_cylinder_add(radius=.07, depth=.8, vertices=16, location=(.55, y, .4)); o = bpy.context.object; o.data.materials.append(BLUE)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.08, location=(.55, y, .82)); o = bpy.context.object; o.data.materials.append(BLUE)
    bpy.ops.mesh.primitive_cylinder_add(radius=.12, depth=.02, vertices=16, location=(.55, y, .01)); o = bpy.context.object; o.data.materials.append(IRON)
# 路燈
bpy.ops.mesh.primitive_cylinder_add(radius=.055, depth=7.5, vertices=12, location=(.9, 14, 3.75)); o = bpy.context.object; o.data.materials.append(simple('pole', '#7b7e82', .5, .7))
cubeo(.6, .2, .12, .6, 14, 7.45, simple('lamp', '#c6c9cc', .4, .6))
bpy.ops.mesh.primitive_uv_sphere_add(radius=.07, location=(.45, 14, 7.36)); lampb = bpy.context.object
lm, lnt, lb = newmat('lampglow'); lb.inputs['Emission Color'].default_value = (1, .9, .7, 1); lb.inputs['Emission Strength'].default_value = 5; lampb.data.materials.append(lm)

# ---------- 小細節：落葉、雜草、積水、菸蒂、口香糖、貼紙 ----------
leafm = [simple('leaf1', '#8a6a2a', .8), simple('leaf2', '#a8823a', .8), simple('leaf3', '#5d6b2c', .8), simple('leaf4', '#6b4a22', .8)]
for k in range(110):
    x = random.choice([random.uniform(-.8, .0), random.uniform(.2, 1.8), random.uniform(-2.5, -.8)]); y = random.uniform(Y0 + 2, Y1 - 4)
    z = .03 if x > .15 else .004
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=8, ring_count=4, location=(x, y, z)); o = bpy.context.object
    o.scale = (random.uniform(.025, .05), random.uniform(.012, .03), .0015); o.rotation_euler[2] = random.uniform(0, 6.28); o.data.materials.append(random.choice(leafm))
tufts_V, tufts_F = [], []
grass = simple('grass', '#4f7a2a', .8)
for k in range(70):   # 路緣縫、磚縫長出來的雜草
    side = random.random()
    x, y = (.0 + random.uniform(-.1, .12), random.uniform(Y0 + 1, Y1 - 2)) if side < .6 else (random.uniform(.3, 4.5), random.uniform(Y0 + 1, Y1 - 2))
    z0 = .14 if side < .6 and x > .0 else (.02 if side >= .6 else .0)
    for bl in range(random.randint(5, 9)):
        a = random.uniform(0, 6.28); L = random.uniform(.08, .2); bend = random.uniform(.2, .6); b0 = len(tufts_V)
        for t in (0, .5, 1):
            r = L * t * bend; zz = z0 + L * t * (1 - .3 * t); wd = .006 * (1 - t) + .001
            tufts_V += [(x + math.cos(a) * r - math.sin(a) * wd, y + math.sin(a) * r + math.cos(a) * wd, zz), (x + math.cos(a) * r + math.sin(a) * wd, y + math.sin(a) * r - math.cos(a) * wd, zz)]
        tufts_F += [(b0, b0 + 1, b0 + 3, b0 + 2), (b0 + 2, b0 + 3, b0 + 5, b0 + 4)]
obj_from(tufts_V, tufts_F, grass, 'weeds')
# 積水：路邊低處的一灘，反射天空
mw2, ntw2, bw2 = newmat('puddle'); bw2.inputs['Base Color'].default_value = lc('#202428'); bw2.inputs['Roughness'].default_value = .03
cow2 = node(ntw2, 'ShaderNodeTexCoord').outputs['Object']
msk = ramp(ntw2, noise(ntw2, cow2, .8, 3).outputs['Fac'], [(.5, (1, 1, 1, 1)), (.58, (0, 0, 0, 1))]).outputs['Color']
trp = node(ntw2, 'ShaderNodeBsdfTransparent'); mxp = node(ntw2, 'ShaderNodeMixShader'); outp = [n for n in ntw2.nodes if n.type == 'OUTPUT_MATERIAL'][0]
link(ntw2, msk, mxp.inputs['Fac']); link(ntw2, bw2.outputs['BSDF'], mxp.inputs[1]); link(ntw2, trp.outputs['BSDF'], mxp.inputs[2]); link(ntw2, mxp.outputs['Shader'], outp.inputs['Surface'])
plane(-3.2, -.5, 5.5, 11, .006, mw2, 'puddle')
# 菸蒂、瓶蓋、口香糖斑
for k in range(26):
    x, y = random.uniform(.3, 3.6), random.uniform(-6, 18)
    if k % 3 == 0: bpy.ops.mesh.primitive_cylinder_add(radius=.004, depth=.03, vertices=6, location=(x, y, .026), rotation=(1.57, 0, random.uniform(0, 3))); o = bpy.context.object; o.data.materials.append(simple('butt', '#d8c9a3', .9))
    elif k % 3 == 1: bpy.ops.mesh.primitive_cylinder_add(radius=.013, depth=.004, vertices=12, location=(x, y, .022)); o = bpy.context.object; o.data.materials.append(simple('cap', random.choice(['#c9372c', '#2f6fc0', '#d9a21a']), .4, .7))
    else: bpy.ops.mesh.primitive_cylinder_add(radius=.014, depth=.002, vertices=10, location=(x, y, .0215)); o = bpy.context.object; o.data.materials.append(simple('gum', '#3b3a38', .5))

# ---------- 港池水面、遠景、天空 ----------
mwt, ntt, bt = newmat('sea'); bt.inputs['Base Color'].default_value = lc('#1f5a6e'); bt.inputs['Roughness'].default_value = .08
cot = node(ntt, 'ShaderNodeTexCoord').outputs['Object']; bm = node(ntt, 'ShaderNodeBump', Strength=.3, Distance=.2); link(ntt, noise(ntt, cot, 1.2, 4).outputs['Fac'], bm.inputs['Height']); link(ntt, bm.outputs['Normal'], bt.inputs['Normal'])
plane(5.0, 160, -60, 120, -1.2, mwt, 'sea'); plane(4.6, 5.0, Y0, Y1, -.35, simple('wall', '#8a867d', .9), 'wallface')
for (x, y, w, d, h, c) in ((-30, 30, 14, 10, 14, '#c9c2b2'), (-22, 48, 10, 8, 11, '#d9d1c0'), (-34, 55, 12, 9, 17, '#b9b3a6'), (-14, 60, 9, 9, 8, '#cfc7b6'), (-40, 12, 12, 9, 9, '#bdb5a5')): cubeo(w, d, h, x, y, h / 2, simple('bld', c, .85))
for (x, y, w, d, h) in ((40, 70, 10, 12, 5), (70, 45, 8, 6, 6)): cubeo(w, d, h, x, y, h / 2 - 1.2, simple('boat', '#e9e9e4', .5))   # 遠處的船
try:
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True; nt = wd.node_tree
    sk = nt.nodes.new('ShaderNodeTexSky'); sk.sky_type = 'MULTIPLE_SCATTERING'; sk.sun_elevation = math.radians(42); sk.sun_rotation = math.radians(150); sk.altitude = 0
    link(nt, sk.outputs['Color'], nt.nodes['Background'].inputs['Color']); nt.nodes['Background'].inputs['Strength'].default_value = .22
    sun_el, sun_rot = 42, 150
except Exception as e:
    print('sky fallback', e); wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs['Color'].default_value = (.5, .7, 1, 1); wd.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.2
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 2.3; sun.data.angle = math.radians(1.2)
sun.rotation_euler = (math.radians(48), 0, math.radians(-60))

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = int(os.environ.get('SAMPLES', 96)); sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.render.resolution_x, sc.render.resolution_y = 900, 760
try: sc.view_settings.view_transform = 'Filmic'
except Exception: sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'None'; sc.view_settings.exposure = -1.2
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
def shot(name, loc, tgt, lens=28):
    cam.data.lens = lens; cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = OUT + name + '.png'; bpy.ops.render.render(write_still=True); print('rendered', name)
shot('street_eye', (-1.3, -9.5, 1.65), (1.8, 4, .5), 26)
shot('street_low', (1.0, -3.2, .32), (1.0, 3, .05), 32)

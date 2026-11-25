# 台灣漁船（約 15 公尺的魷釣船）：V 型船身、船頭弧線、舷牆、木甲板、駕駛艙、桅杆、兩排集魚燈、輪胎碰墊、漁網、魚箱
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *
reset(); random.seed(9)
Lb, B = 15.0, 4.4
white = mat('white', '#f2f2ee', .45); blueS = mat('blueS', '#2a64a0', .45); redB = mat('redB', '#9a3127', .6)
deck = mat('deck', '#9b7a55', .75, kind='plank', color2='#8a6a48'); cab = mat('cab', '#f4f4f0', .4)
win = mat('win', '#1e2a33', .1, .3, emit='#ffe2a8', emit_k=.8); rail = mat('rail', '#e8e8e4', .4, .6)
steel = mat('steel', '#c9cdd0', .3, .8); tire = mat('tire', '#1c1c1c', .9); net = mat('net', '#2f6a4a', .9, kind='concrete')
crate = mat('crate', '#2f78c0', .5); bulb = mat('bulb', '#fffbe8', .2, emit='#fff4d0', emit_k=6.); rope = mat('rope', '#c8a86a', .8)
flagR = mat('flagR', '#d42a1e', .6); flagY = mat('flagY', '#f2c230', .6)
# ---- 船身：沿長度的斷面（舷頂→舷側→舭部→龍骨）做成一張網格，依高度分顏色 ----
n, rows = 36, [(0, 1, white), (-.55, .995, white), (-.62, .99, blueS), (-.9, .975, blueS), (-1.0, .96, redB), (-1.6, .8, redB), (-2.3, .35, redB), (-2.55, 0, redB)]
secs = []
for k in range(n + 1):
    t = k / n; x = -Lb / 2 + t * Lb
    hb = B / 2 * (.86 + .14 * math.sin(min(1, t / .62) * math.pi / 2) if t < .62 else math.cos((t - .62) / .38 * math.pi / 2) ** .8)
    sheer = 2.0 + (t ** 3) * 1.25 + (1 - t) * .2      # 舷弧：船頭高高翹起
    keel = 1 - (t > .8) * (t - .8) * 2.2                # 船頭底部往上收
    secs.append([(x, max(-hb * wk * 0, 0) if False else hb * wk, sheer + dy * (keel if dy < -1 else 1)) for dy, wk, _ in rows])
V, Fc, mats = [], [], []
for side in (1, -1):
    base = len(V)
    for k in range(n + 1):
        for r in range(len(rows)): x, w, z = secs[k][r]; V.append((x, side * w, z))
    for k in range(n):
        for r in range(len(rows) - 1):
            a = base + k * len(rows) + r; b = a + len(rows)
            Fc.append((a, b, b + 1, a + 1) if side > 0 else (a, a + 1, b + 1, b)); mats.append(rows[r][2])
hull = mesh_from(V, Fc, white, smooth=True, name='hull')
for mm in (blueS, redB): hull.data.materials.append(mm)
for p, mm in zip(hull.data.polygons, mats): p.material_index = [white, blueS, redB].index(mm)
# 船尾板
st = secs[0]
mesh_from([(st[r][0], s * st[r][1], st[r][2]) for s in (1, -1) for r in range(len(rows))], [tuple(range(len(rows))) + (), ], white, name='tr')
mesh_from([(st[r][0], s * st[r][1], st[r][2]) for r in range(len(rows)) for s in (1, -1)], [(2 * r, 2 * r + 1, 2 * r + 3, 2 * r + 2) for r in range(len(rows) - 1)], white, name='transom')
# 甲板（比舷頂低 0.8）、舷牆頂的扶手
dv, df = [], []
for k in range(n + 1):
    x, w, z = secs[k][0]; dv += [(x, w * .95, z - .8), (x, -w * .95, z - .8)]
for k in range(n): df.append((2 * k, 2 * k + 2, 2 * k + 3, 2 * k + 1))
mesh_from(dv, df, deck, name='deck')
for side in (1, -1):
    tube([(secs[k][0][0], side * secs[k][0][1], secs[k][0][2] + .03) for k in range(0, n + 1, 3)], .06, rail)
    # 輪胎碰墊
    for k in range(5, n - 6, 5):
        x, w, z = secs[k][2]; torus(.32, .13, x, side * (w + .12), z - .25, tire, rx=math.pi / 2)
# ---- 駕駛艙（偏船尾）：白色、一圈窗、屋頂、雷達、天線 ----
cx = -2.4; dz = secs[int(n * .35)][0][2] - .8
box(3.4, 3.0, 2.3, cx, 0, dz, cab, bevel=.08)
for s in (-1, 1): box(2.4, .06, .75, cx + .2, s * 1.52, dz + 1.2, win)
box(.06, 2.4, .75, cx + 1.72, 0, dz + 1.2, win)
box(3.8, 3.4, .14, cx, 0, dz + 2.3, cab)
for s in (-1, 1): tube([(cx - 1.8, s * 1.65, dz + 2.45), (cx + 1.8, s * 1.65, dz + 2.45)], .03, rail)
cyl(.32, .25, cx - .6, 0, dz + 2.44, white, seg=16); box(1.3, .12, .08, cx - .6, 0, dz + 2.75, steel)   # 雷達
cyl(.03, 2.2, cx + .9, .6, dz + 2.44, steel, seg=6); cyl(.03, 1.6, cx + .9, -.6, dz + 2.44, steel, seg=6)
# ---- 桅杆、橫桿、旗子 ----
mx = 2.2; mz = secs[int(n * .66)][0][2] - .8
cyl(.1, 7.5, mx, 0, mz, steel, seg=10); box(.12, 3.6, .12, mx, 0, mz + 5.6, steel)
cyl(.07, 4.5, -6.3, 0, secs[1][0][2] - .8, steel, seg=8)
box(.02, .9, .55, mx, .5, mz + 6.8, flagR); box(.02, .9, .55, -6.3, .5, secs[1][0][2] + 3.1, flagY)
# ---- 集魚燈：兩排大燈泡掛在船兩側的架子上 ----
for side in (1, -1):
    tube([(-5.5, side * 1.9, mz + 2.4), (0, side * 1.95, mz + 2.5), (5.0, side * 1.9, mz + 2.4)], .04, steel)
    for k in range(10):
        x = -5.2 + k * 1.1
        cyl(.012, .25, x, side * 1.92, mz + 2.15, steel, seg=4)
        sphere(.17, x, side * 1.92, mz + 2.0, bulb, seg=6, sz=1.3)
for x in (-5.5, 0, 5.0):
    for side in (1, -1): cyl(.05, 2.5, x, side * 1.9, secs[int((x + Lb / 2) / Lb * n)][0][2] - .8, steel, seg=6)
# ---- 甲板上的東西：漁網堆、魚箱、繩子 ----
bpy.ops.mesh.primitive_ico_sphere_add(radius=1, subdivisions=2, location=(3.8, .2, mz + .2)); o = bpy.context.object
o.scale = (1.4, 1.0, .45); bpy.ops.object.transform_apply(scale=True)
for v in o.data.vertices: v.co += v.normal * random.uniform(-.12, .12)
_ = PARTS.append(o) or o.data.materials.append(net)
for k in range(6): box(.7, .5, .35, 0.6 + (k % 3) * .75, -1.0 + (k // 3) * .55, mz + (k % 2) * .0, crate)
torus(.35, .06, -4.8, .9, secs[4][0][2] - .75, rope); torus(.28, .06, -4.8, .9, secs[4][0][2] - .69, rope)
bake_export('boat', res=1024, samples=48)

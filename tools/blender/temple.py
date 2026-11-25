# 港口大眾爺廟（小型宮廟）：石台基、紅牆、龍柱、門神門、彎曲的屋面、燕尾脊、剪黏雙龍搶珠、燈籠、天公爐
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *
reset(); random.seed(5)
L, Dd, WH = 9.0, 7.0, 4.3     # 殿身長、深、牆高
P0 = .6                       # 台基高度
stone = mat('stone', '#c8c3b8', .9, kind='concrete')
gran = mat('gran', '#aaa69e', .85, kind='tile', scale=3, color2='#7f7c76')
red = mat('red', '#c8412f', .6)
redC = mat('redC', '#d0402f', .45)
gold = mat('gold', '#d8a93a', .3, .8)
wood = mat('wood', '#8a3a22', .55)
roofT = mat('roofT', '#d98a2b', .45, kind='xstripe', scale=2.6, color2='#b86a1c')
green = mat('green', '#2f8f6a', .4)
blue = mat('blue', '#2f5fa8', .4)
beam = mat('beam', '#2a6a8a', .5, kind='stripe', scale=3, color2='#d8a93a', axis='X')
black = mat('black', '#1d1a18', .5)
goldT = mat('goldT', '#ffd34d', .3, .6, emit='#ffcf5a', emit_k=.4)
lantern = mat('lantern', '#d42a1e', .6, emit='#ff5533', emit_k=2.)
bronze = mat('bronze', '#5a4a32', .4, .7)
# ---- 台基、台階 ----
box(L + 1.6, Dd + 3.4, P0, 0, Dd / 2 - .9, 0, stone)
for k in range(3): box(3.6 - k * .2, .45, P0 * (k + 1) / 3, 0, -2.6 + k * .45 - .2, 0, stone)
# ---- 殿身：花崗石牆腳＋紅牆；正面往內退出前廊 ----
y0 = 1.6   # 正面牆的位置（前面是 1.6 公尺的廊）
box(L, Dd - y0, 1.0, 0, y0 + (Dd - y0) / 2, P0, gran)
box(L, Dd - y0, WH - 1.0, 0, y0 + (Dd - y0) / 2, P0 + 1.0, red)
for s in (-1, 1): box(.5, y0, WH, s * (L / 2 - .25), y0 / 2, P0, red)   # 前廊兩側的牆
# 門：中門大、兩邊小，深色木門＋金色門釘
for (cx, w, h) in ((0, 2.2, 3.1), (-2.9, 1.3, 2.6), (2.9, 1.3, 2.6)):
    box(w + .3, .12, h + .25, cx, y0 - .02, P0, gold)
    for s in (-1, 1):
        box(w / 2 - .04, .1, h, cx + s * w / 4, y0 - .08, P0, wood)
        for r in range(6):
            for c in range(3): sphere(.035, cx + s * w / 4 + (c - 1) * w / 8, y0 - .14, P0 + .35 + r * (h - .6) / 5, gold, seg=6)
# 匾額
box(3.2, .12, .8, 0, y0 - .12, P0 + 3.35, black)
text('港口大眾爺廟', .48, 0, y0 - .2, P0 + 3.75, goldT, depth=.015)
# ---- 前廊的柱子：中間兩根是龍柱 ----
for x in (-3.6, -1.2, 1.2, 3.6):
    box(.62, .62, .35, x, .25, P0, gran)
    cyl(.22, WH - .55, x, .25, P0 + .35, redC, seg=20)
    box(.6, .6, .2, x, .25, P0 + WH - .2, gold)
    if abs(x) < 2:   # 盤龍：一條綠色的龍沿著柱子繞上去
        pts = [(x + math.cos(a) * .3, .25 + math.sin(a) * .3, P0 + .5 + a / (5 * math.pi) * (WH - 1.2)) for a in [k * .5 for k in range(32)]]
        tube(pts, .085, green); sphere(.16, *pts[-1], green, seg=10)
# 彩繪的橫樑
box(L - .2, .35, .45, 0, .25, P0 + WH, beam)
# ---- 屋頂：屋面中間凹、屋角翹，正反兩面；兩端補山牆三角形 ----
oh, ey = 1.3, P0 + WH + .45          # 出簷、屋簷高度
top, yc = ey + 2.9, Dd / 2 - .9       # 屋脊高度、屋脊的位置（深度方向）
hx, hd = L / 2 + oh, (Dd + 1.2) / 2 + oh
def roof_side(sign):
    nx, nt = 28, 12; V = []; Fc = []
    for i in range(nx + 1):
        u = -1 + 2 * i / nx
        for j in range(nt + 1):
            t = j / nt
            z = top - (top - ey) * (1 - (1 - t) ** 2.1)                 # 凹的屋面：屋脊陡、屋簷緩
            z += .75 * abs(u) ** 5 * t ** 1.6                           # 屋角往上翹
            y = yc + sign * (t * hd + .45 * abs(u) ** 4 * t ** 2)      # 屋角往外伸
            V.append((u * (hx + .25 * abs(u) ** 4 * t), y, z))
    for i in range(nx):
        for j in range(nt):
            a = i * (nt + 1) + j; b = a + nt + 1
            Fc.append((a, b, b + 1, a + 1) if sign > 0 else (a, a + 1, b + 1, b))
    o = mesh_from(V, Fc, roofT, smooth=True, name='roof'); solidify(o, .18)
roof_side(1); roof_side(-1)
for s in (-1, 1):   # 山牆（紅）
    xg = s * (L / 2 + .05)
    mesh_from([(xg, yc - hd * .62, ey + .3), (xg, yc + hd * .62, ey + .3), (xg, yc, top - .1)], [(0, 1, 2)], red, name='gable'); solidify(bpy.context.object if False else PARTS[-1], .2)
# 正脊＋燕尾（兩端往上翹開分叉）
box(2 * (hx - 1.6), .4, .5, 0, yc, top - .1, green)
for s in (-1, 1):
    x0 = s * (hx - 1.6)
    for fy in (-.22, .22):
        tube([(x0, yc, top + .15), (x0 + s * .6, yc + fy * .3, top + .28), (x0 + s * 1.05, yc + fy * .8, top + .6), (x0 + s * 1.3, yc + fy * 1.3, top + 1.05)], .1, green)
# 垂脊（從屋脊兩端往屋角）
for s in (-1, 1):
    for sg in (-1, 1):
        pts = []
        for k in range(9):
            u0 = (hx - 1.6) / hx; t = k / 8; u = s * (u0 + (1 - u0) * t)   # 從正脊尾端往屋角
            z = top - (top - ey) * (1 - (1 - t) ** 2.1) + .75 * abs(u) ** 5 * t ** 1.6 + .22
            pts.append((u * hx, yc + sg * t * hd * .96, z))
        tube(pts, .09, green)
# 剪黏：雙龍搶珠
for s in (-1, 1):
    pts = [(s * (2.6 - k * .26), yc + math.sin(k * 1.1) * .15, top + .35 + .25 * math.sin(k * .9) + k * .02) for k in range(9)]
    tube(pts, .1, blue if s > 0 else green)
    sphere(.2, *pts[0], blue if s > 0 else green, seg=10)
    cyl(.03, .45, pts[0][0] - s * .05, yc, top + .5, gold, seg=6, ry=s * .6)   # 龍角
cyl(.12, .45, 0, yc, top + .15, gold, seg=8, r2=.02)   # 火焰
sphere(.24, 0, yc, top + .72, gold, seg=14)            # 寶珠
# ---- 燈籠、天公爐 ----
for x in (-2.4, 2.4):
    cyl(.012, .5, x, .25, P0 + WH - .6, black, seg=4)
    sphere(.38, x, .25, P0 + WH - 1.0, lantern, seg=14, sz=1.25)
    cyl(.24, .1, x, .25, P0 + WH - .62, gold, seg=12); cyl(.2, .1, x, .25, P0 + WH - 1.55, gold, seg=12)
    cyl(.02, .35, x, .25, P0 + WH - 1.95, lantern, seg=4)
cyl(.75, .9, 0, -4.4, .35, bronze, seg=20, r2=.62)
cyl(.82, .1, 0, -4.4, 1.25, bronze, seg=20); cyl(.5, .25, 0, -4.4, 1.3, bronze, seg=16, r2=.3)
for k in range(3):
    a = k * 2.094; cyl(.08, .45, math.cos(a) * .55, -4.4 + math.sin(a) * .55, 0, bronze, seg=6)
for s in (-1, 1): torus(.18, .04, s * .86, -4.4, 1.0, bronze, rx=math.pi / 2, rz=math.pi / 2)
bake_export('temple', res=2048, samples=64, ao_dist=.7, ao_min=.55)   # 前廊比較亮

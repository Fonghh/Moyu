# 台灣海邊的透天厝（四樓、面寬 5.6 公尺、深 14 公尺）：騎樓、鐵捲門、招牌、鐵窗、冷氣、雨遮、陽台、頂樓加蓋、水塔
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *
reset(); random.seed(3)
W, D, G, F, NF = 5.6, 14., 3.8, 3.4, 4
H = G + F * (NF - 1)
AR = 3.0   # 騎樓深度
tile = mat('tile', '#f1ebdd', .7, kind='tile', color2='#e6dcc8')
conc = mat('conc', '#a8a296', .9, kind='concrete')
concL = mat('concL', '#c9c2b4', .9, kind='concrete')
alu = mat('alu', '#c9cdd0', .35, .7)
glass = mat('glass', '#2c3a44', .1, .2, emit='#ffcf8a', emit_k=1.)
glassD = mat('glassD', '#26323a', .1, .2)   # 不亮的窗
iron = mat('iron', '#e6e6e0', .5, .5)
shut = mat('shut', '#9aa0a5', .5, .6, kind='corr', scale=2.5, color2='#8a9095', axis='Y')   # 鐵捲門：橫的條紋
sign = mat('sign', '#c0392b', .4, emit='#e04838', emit_k=.6)
signT = mat('signT', '#fff6d0', .4, emit='#fff6d0', emit_k=1.5)
floorT = mat('floorT', '#b8a58a', .7, kind='tile', scale=1.8, color2='#a8957a')
acm = mat('ac', '#eeeeea', .5)
grey = mat('grey', '#6e7378', .6, .4)
sheet = mat('sheet', '#5b7fa6', .5, .4, kind='corr', scale=1.5, color2='#4a6a8c')
steel = mat('steel', '#d8dbde', .25, .85)
dark = mat('dark', '#2a2c2e', .6)
plant = mat('plant', '#3f7a3a', .8)
pot = mat('pot', '#9a5a3a', .8)
# ---- 主體：樓上整個、一樓往內退出騎樓 ----
box(W, D, H - G, 0, D / 2, G, conc)                       # 二樓以上（側面、背面是水泥）
box(W + .04, .06, H - G + .02, 0, -.03, G - .01, tile)    # 正面貼二丁掛磁磚
box(W - .5, D - AR, G, 0, AR + (D - AR) / 2, 0, conc)    # 一樓（往內退）
for s in (-1, 1):                                          # 騎樓兩側的牆柱（跟鄰居共用）
    box(.25, AR, G, s * (W / 2 - .125), AR / 2, 0, concL)
box(W, AR, .08, 0, AR / 2, 0, floorT)                     # 騎樓地磚
box(W - .5, .1, .25, 0, AR + .05, G - .25, conc)          # 騎樓天花板下的樑
# ---- 一樓店面：鐵捲門、門框、招牌 ----
box(W - 1.6, .12, G - .9, -.35, AR - .06, 0, shut)       # 鐵捲門
box(W - 1.4, .4, .45, -.35, AR - .2, G - .9, grey)        # 捲門箱
box(.9, .06, 2.2, W / 2 - .9, AR - .03, 0, dark)          # 旁邊的小門
box(W, .35, .9, 0, -.17, G - .95, sign)                   # 招牌（掛在騎樓外）
text('海鮮快炒', .62, 0, -.36, G - .5, signT)
# ---- 樓上的正面：每層一大一小的窗、鐵窗、冷氣、雨遮、樓板線 ----
for f in range(NF - 1):
    z0 = G + f * F
    box(W + .06, .1, .14, 0, -.05, z0 - .07, conc)        # 樓板線
    for (cx, ww, hh) in ((-.9, 2.4, 1.6), (1.75, 1.2, 1.3)):
        zz = z0 + 1.0
        box(ww, .12, hh, cx, .05, zz, glass if (f + int(cx > 0)) % 2 == 0 else glassD)   # 玻璃（凹進去）
        # 鋁窗框
        box(ww + .12, .1, .07, cx, -.01, zz - .07, alu); box(ww + .12, .1, .07, cx, -.01, zz + hh, alu)
        for sx in (-1, 0, 1): box(.06, .1, hh, cx + sx * ww / 2, -.01, zz, alu)
        # 雨遮（往外斜）
        box(ww + .5, .55, .08, cx, -.27, zz + hh + .25, concL)
        if f == 0 and cx < 0:   # 二樓的大窗做成陽台
            box(ww + .5, .95, .12, cx, -.47, z0, concL)
            for k in range(13): box(.03, .03, 1.0, cx - (ww + .4) / 2 + k * (ww + .4) / 12, -.92, z0 + .12, iron)
            box(ww + .5, .05, .05, cx, -.92, z0 + 1.1, iron)
            for k in range(3): cyl(.16, .3, cx - .8 + k * .8, -.6, z0 + .12, pot); sphere(.26, cx - .8 + k * .8, -.6, z0 + .62, plant, seg=10)
        else:   # 鐵窗：凸出來的籠子
            d = .38; x0, x1 = cx - ww / 2 - .1, cx + ww / 2 + .1
            for zz2 in (zz - .1, zz + hh + .05): box(x1 - x0, .04, .04, cx, -d, zz2, iron)
            for k in range(int((x1 - x0) / .12) + 1): box(.025, .025, hh + .15, x0 + k * .12, -d, zz - .1, iron)
            for sx in (x0, x1):
                for zz2 in (zz - .1, zz + hh + .05): box(.025, d, .025, sx, -d / 2, zz2, iron)
            box(x1 - x0, d, .03, cx, -d / 2, zz + hh + .08, iron)
        if cx > 0:   # 小窗下面掛冷氣室外機
            box(.85, .3, .6, cx, -.2, z0 + .1, acm); cyl(.2, .02, cx - .1, -.355, z0 + .4, grey, seg=12, rx=math.pi / 2)
# 落水管
cyl(.05, H, W / 2 - .12, -.08, 0, grey, seg=8)
# ---- 頂樓：女兒牆、鐵皮加蓋、水塔、太陽能熱水器、天線 ----
for (sx, sy, x, y) in ((W, .2, 0, .1), (W, .2, 0, D - .1), (.2, D, -W / 2 + .1, D / 2), (.2, D, W / 2 - .1, D / 2)):
    box(sx, sy, .95, x, y, H, conc)
box(W - .6, 6.5, 2.5, 0, D - 4, H, sheet)                    # 加蓋的鐵皮屋
box(W - .2, 7.1, .1, 0, D - 4, H + 2.5, sheet)               # 浪板屋頂
box(.9, .06, 2.0, -.8, D - 7.25, H, dark)                    # 鐵門
cyl(.65, 1.3, 1.3, 2.4, H + 1.1, steel, seg=24)              # 不鏽鋼水塔
for sx in (-1, 1):
    for sy in (-1, 1): box(.08, .08, 1.1, 1.3 + sx * .45, 2.4 + sy * .45, H, grey)
box(1.1, 1.1, .08, 1.3, 2.4, H + 1.05, grey)
box(1.8, 1.0, .05, -1.2, 1.6, H + .9, dark, rz=0)            # 太陽能熱水器（斜板）
bpy.context.object.rotation_euler[0] = .6; bpy.ops.object.transform_apply(rotation=True)
cyl(.18, 1.6, -1.2, 2.3, H + .6, steel, seg=12, ry=math.pi / 2, rx=0); bpy.context.object.location.x -= .8
cyl(.025, 2.4, 2.2, 1.0, H, grey, seg=6)
box(.9, .03, .03, 2.2, 1.0, H + 2.2, grey)
# 背面、側面的小窗
for f in range(NF):
    box(1.0, .1, .9, 0, D + .02, (G if f else 0) + f * F + 1.2, glassD if f % 2 else glass)
bake_export('house', res=2048, samples=64)

# 料理照片：白瓷魚盤（烤魚、炸魚用，魚的照片在遊戲裡疊上去）、魚湯、生魚片拼盤；透明背景 512×256
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blib import *

def scene_setup(name):
    reset(); random.seed(4)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 512, 256; sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Filmic' if 'Filmic' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'AgX'; sc.view_settings.look = 'None'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.85, .82, .78, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.05
    cam.location = (0, -2.3, 1.75); cam.rotation_euler = (math.radians(52), 0, 0); sc.camera = cam
    for loc, e, sz in (((1.2, -1.2, 2.4), 110, 1.2), ((-1.6, -.6, 1.6), 30, 2.2)):
        L = bpy.data.objects.new('L', bpy.data.lights.new('L', 'AREA')); sc.collection.objects.link(L)
        L.data.energy = e; L.data.size = sz; L.location = loc
        L.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    # 陰影接收面（透明背景裡只留陰影）
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0)); pl = bpy.context.object; pl.is_shadow_catcher = True
    return sc

def render(sc, name):
    sc.render.filepath = OUT + name + '.png'; bpy.ops.render.render(write_still=True); print('rendered', name)

def plate(rx, ry, z=0, m=None):
    """橢圓白瓷盤：盤底＋往上翹的盤緣"""
    m = m or mat('porcelain', '#ecebe6', .18)
    V, Fc, R = [], [], 48
    rings = [(0, .0), (.72, .0), (.86, .03), (1.0, .085), (1.04, .095)]
    for k, (rr, zz) in enumerate(rings):
        for i in range(R):
            a = i / R * math.pi * 2; V.append((math.cos(a) * rx * rr, math.sin(a) * ry * rr, z + zz))
    for k in range(len(rings) - 1):
        for i in range(R):
            a, b = k * R + i, k * R + (i + 1) % R; Fc.append((a, b, b + R, a + R))
    o = mesh_from(V, Fc, m, smooth=True, name='plate'); solidify(o, .025)
    return o

# ---- 1. 魚盤（烤魚、炸魚的底）：白瓷橢圓盤＋檸檬片＋香菜 ----
sc = scene_setup('plate')
plate(.95, .42)
lemon = mat('lemon', '#e8c22a', .35); peel = mat('peel', '#e2b415', .4); herb = mat('herb', '#3f7f2c', .6)
bpy.ops.mesh.primitive_cylinder_add(radius=.13, depth=.05, vertices=24, location=(.68, -.1, .1)); o = bpy.context.object; o.rotation_euler = (1.1, 0, .3); o.data.materials.append(lemon); PARTS.append(o)
bpy.ops.mesh.primitive_cylinder_add(radius=.13, depth=.05, vertices=24, location=(.74, .02, .09)); o = bpy.context.object; o.rotation_euler = (1.2, 0, .5); o.data.materials.append(lemon); PARTS.append(o)
for k in range(7): sphere(.04, -.72 + random.uniform(-.06, .06), random.uniform(-.12, .1), .06, herb, seg=6, sz=.4)
render(sc, 'dish_plate')

# ---- 2. 魚湯：藍邊白瓷碗、奶白色湯、魚塊、薑絲、蔥花 ----
sc = scene_setup('soup')
bowl = mat('bowl', '#ecebe6', .2); rim = mat('rim', '#2f5fa8', .3)
V, Fc, R = [], [], 48
prof = [(0, -.25), (.26, -.25), (.3, -.23), (.43, -.13), (.51, .0), (.55, .1), (.56, .13)]
for k, (rr, zz) in enumerate(prof):
    for i in range(R): a = i / R * math.pi * 2; V.append((math.cos(a) * rr, math.sin(a) * rr, zz))
for k in range(len(prof) - 1):
    for i in range(R): a, b = k * R + i, k * R + (i + 1) % R; Fc.append((a, b, b + R, a + R))
o = mesh_from(V, Fc, bowl, smooth=True, name='bowl'); solidify(o, .03)
torus(.555, .012, 0, 0, .13, rim)
broth = mat('broth', '#e6cf98', .15)
bpy.ops.mesh.primitive_circle_add(radius=.53, vertices=48, fill_type='NGON', location=(0, 0, .07)); o = bpy.context.object; o.data.materials.append(broth); PARTS.append(o)
fishm = mat('fishm', '#efe4d2', .5); skin = mat('skin', '#5d6670', .3)
for k in range(5):
    a = k * 1.25 + .3; x, y = math.cos(a) * .25, math.sin(a) * .22
    box(.17, .11, .06, x, y, .06, fishm, rz=a, bevel=.025); box(.17, .015, .062, x, y - .06, .062, skin, rz=a)
ginger = mat('ginger', '#e9c977', .5); onion = mat('onion', '#5aa43a', .5)
for k in range(10): box(.12, .012, .01, random.uniform(-.3, .3), random.uniform(-.25, .25), .115, ginger, rz=random.uniform(0, 3))
for k in range(18): cyl(.018, .012, random.uniform(-.38, .38), random.uniform(-.33, .33), .118, onion, seg=8)
render(sc, 'dish_soup')

# ---- 3. 生魚片：木盤、碎冰、扇形排開的魚片、紫蘇葉、山葵、白蘿蔔絲 ----
sc = scene_setup('sashimi')
wood = mat('wood', '#a8743f', .6, kind='plank', scale=.4, color2='#8f5f30')
box(1.9, .78, .07, 0, 0, 0, wood, bevel=.02)
ice = mat('ice', '#e8f2f6', .08)
for k in range(40): sphere(random.uniform(.04, .07), random.uniform(-.85, .85), random.uniform(-.3, .3), .07, ice, seg=10, sz=.6)
radish = mat('radish', '#fbfbf7', .5)
for k in range(30): box(.25, .008, .008, random.uniform(-.75, -.35), random.uniform(-.2, .2), .1, radish, rz=random.uniform(-.4, .4))
shiso = mat('shiso', '#2f6f2a', .5)
bpy.ops.mesh.primitive_circle_add(radius=.2, vertices=24, fill_type='NGON', location=(-.48, .05, .14)); o = bpy.context.object; o.scale = (1, .6, 1); o.rotation_euler = (.25, 0, .4); o.data.materials.append(shiso); PARTS.append(o)
flesh = mat('flesh', '#ee7b4e', .25, kind='stripe', scale=14, color2='#f7c9a8'); flesh2 = mat('flesh2', '#b8222e', .25)
for k in range(7):   # 一片片斜靠著排開
    x = -.15 + k * .16
    box(.14, .36, .035, x, 0, .14, flesh if k % 2 == 0 else flesh2, rz=.12)
    bpy.context.object.rotation_euler[1] = -.55; bpy.ops.object.transform_apply(rotation=True)
wasabi = mat('wasabi', '#9cc85a', .7)
sphere(.08, .78, -.12, .14, wasabi, seg=10, sz=.7)
render(sc, 'dish_sashimi')

# 把 OpenStreetMap 資料轉成遊戲用的真實地圖（竹圍漁港試作）
# 用法：python3 -I realmap.py raw.json out.json preview.png
import json, math, sys, random
from shapely.geometry import Polygon, LineString, Point, box, MultiPolygon, MultiLineString
from shapely.ops import unary_union
from shapely.prepared import prep

raw = json.load(open(sys.argv[1]))
lat0, lon0 = raw['meta']['lat'], raw['meta']['lon']
kx = 111320 * math.cos(math.radians(lat0)); ky = 110574
X0, X1, Y0, Y1 = -400, 600, -500, 650          # 以漁港為原點：西 400、東 600、南 500、北 650（公尺）
TX, TZ = 5, 2
W, H = (X1 - X0) // TX, (Y1 - Y0) // TZ
NODES = {int(k): v for k, v in raw['nodes'].items()}
WAYS = {int(k): v for k, v in raw['ways'].items()}
FRAME = box(0, 0, X1 - X0, Y1 - Y0)
rnd = random.Random(7)

def gp(n):   # 遊戲座標：X 往東、Z 往南（公尺）
    la, lo, _ = NODES[n]
    return ((lo - lon0) * kx - X0, Y1 - (la - lat0) * ky)
def pts(refs): return [gp(r) for r in refs if r in NODES]
def poly(refs):
    p = pts(refs)
    if len(p) < 4: return None
    g = Polygon(p)
    if not g.is_valid: g = g.buffer(0)
    return g if not g.is_empty else None

# ---- 收集圖形 ----
coast, basin, ponds, rivers, quays, piers, woods, parks, sands, parking = [], [], [], [], [], [], [], [], [], []
roads, buildings, trees = [], [], []
RW = {'primary': 12, 'secondary': 10, 'tertiary': 8, 'tertiary_link': 6, 'unclassified': 6, 'residential': 6, 'living_street': 5,
      'service': 4, 'pedestrian': 5, 'footway': 2, 'path': 1.5, 'cycleway': 2.5, 'track': 3, 'steps': 2}
for wid, (refs, t) in WAYS.items():
    closed = refs[0] == refs[-1] and len(refs) > 3
    if t.get('natural') == 'coastline':
        p = pts(refs)
        if len(p) > 1: coast.append(LineString(p))
    elif t.get('natural') == 'water' or 'water' in t:
        g = poly(refs) if closed else None
        if g is None: continue
        if t.get('leisure') == 'marina' or t.get('water') == 'harbour' or 'harbour' in t.get('seamark:type', ''): basin.append(g)
        elif t.get('water') == 'river': rivers.append(g)
        else: ponds.append(g)
    elif t.get('waterway') in ('river', 'canal', 'stream') and t.get('tunnel') is None:
        p = pts(refs)
        if len(p) > 1: rivers.append(LineString(p).buffer(4 if t['waterway'] != 'stream' else 2, cap_style=2))
    elif t.get('man_made') in ('pier', 'breakwater', 'groyne'):
        if closed and t.get('area') == 'yes':
            g = poly(refs)
            if g is not None: quays.append(g)
        else:
            p = pts(refs)
            if len(p) > 1:
                ln = LineString(p)
                if ln.length > 60 or t.get('man_made') != 'pier': quays.append(ln.buffer(5, cap_style=2))   # 長的是防波堤（水泥）
                else: piers.append(ln.buffer(2, cap_style=2))   # 短的是木棧橋
    elif t.get('natural') == 'wood' or t.get('landuse') == 'forest':
        g = poly(refs) if closed else None
        if g is not None: woods.append(g)
    elif t.get('leisure') in ('park', 'garden', 'pitch') or t.get('landuse') in ('grass', 'cemetery', 'farmland'):
        g = poly(refs) if closed else None
        if g is not None: parks.append(g)
    elif t.get('natural') in ('sand', 'beach', 'mud'):
        g = poly(refs) if closed else None
        if g is not None: sands.append(g)
    elif t.get('amenity') == 'parking':
        g = poly(refs) if closed else None
        if g is not None: parking.append(g)
    if 'highway' in t and t['highway'] in RW and t.get('area') != 'yes':
        p = pts(refs)
        if len(p) > 1: roads.append((LineString(p), RW[t['highway']], t['highway'], t.get('bridge') == 'yes'))
    if 'building' in t:
        g = poly(refs) if closed else None
        if g is not None and g.area > 6:
            lv = t.get('building:levels'); hgt = t.get('height')
            buildings.append({'g': g, 'name': t.get('name'), 'kind': t.get('amenity') or t.get('shop') or t.get('building'),
                              'levels': float(lv) if lv and lv.replace('.', '').isdigit() else None,
                              'height': float(hgt) if hgt and hgt.replace('.', '').isdigit() else None, 'osm': True})
for nid, (la, lo, t) in NODES.items():
    if t and t.get('natural') == 'tree': trees.append(gp(nid))

clipF = lambda gs: [g.intersection(FRAME) for g in gs if g.intersects(FRAME)]
basin, ponds, rivers, quays, piers, woods, parks, sands, parking = map(clipF, (basin, ponds, rivers, quays, piers, woods, parks, sands, parking))
buildings = [b for b in buildings if b['g'].intersects(FRAME) and FRAME.contains(b['g'].centroid)]
roads = [(l.intersection(FRAME), w, k, br) for l, w, k, br in roads if l.intersects(FRAME)]

# ---- 海：海岸線當牆，從北邊往下淹 ----
grid = [[0] * W for _ in range(H)]   # 0 陸地
LAND, SEA, BASIN, POND, RIVER = 0, 1, 2, 3, 4
import numpy as np
# 每一格找最近的海岸線線段：OSM 的海岸線「左邊是陸地、右邊是海」
segs = []
for c in coast:
    cs = list(c.coords)
    for n in range(len(cs) - 1): segs.append((*cs[n], *cs[n + 1]))
S = np.array(segs)
ax, az, bx, bz = S[:, 0], S[:, 1], S[:, 2], S[:, 3]
ex, ez = bx - ax, bz - az; L2 = np.maximum(ex * ex + ez * ez, 1e-9)
for j in range(H):
    for i in range(W):
        px, pz = (i + .5) * TX, (j + .5) * TZ
        t = np.clip(((px - ax) * ex + (pz - az) * ez) / L2, 0, 1)
        qx, qz = ax + ex * t, az + ez * t
        d2 = (px - qx) ** 2 + (pz - qz) ** 2
        k = int(np.argmin(d2))
        cr = ex[k] * (pz - az[k]) - ez[k] * (px - ax[k])   # 遊戲座標 Z 往南（左右顛倒）：cr > 0 在線的左邊（地圖上的右邊＝海）
        grid[j][i] = SEA if cr > 0 else LAND
def stamp(geoms, val, cond=None):
    if not geoms: return
    u = prep(unary_union(geoms))
    for j in range(H):
        for i in range(W):
            if (cond is None or cond(grid[j][i])) and u.contains(Point((i + .5) * TX, (j + .5) * TZ)): grid[j][i] = val
stamp(basin, BASIN); stamp(ponds, POND, lambda v: v == LAND); stamp(rivers, RIVER, lambda v: v == LAND)
print('sea tiles', sum(r.count(SEA) for r in grid), 'basin', sum(r.count(BASIN) for r in grid), 'pond', sum(r.count(POND) for r in grid), 'river', sum(r.count(RIVER) for r in grid))

# ---- 離岸距離（公尺）：決定近海、深海、遠洋 ----
INF = 1e9
dist = [[0 if grid[j][i] != SEA else INF for i in range(W)] for j in range(H)]
for _ in range(2):
    for j in range(H):
        for i in range(W):
            d = dist[j][i]
            if j > 0: d = min(d, dist[j - 1][i] + TZ)
            if i > 0: d = min(d, dist[j][i - 1] + TX)
            if i > 0 and j > 0: d = min(d, dist[j - 1][i - 1] + 5.39)
            if i < W - 1 and j > 0: d = min(d, dist[j - 1][i + 1] + 5.39)
            dist[j][i] = d
    for j in range(H - 1, -1, -1):
        for i in range(W - 1, -1, -1):
            d = dist[j][i]
            if j < H - 1: d = min(d, dist[j + 1][i] + TZ)
            if i < W - 1: d = min(d, dist[j][i + 1] + TX)
            if i < W - 1 and j < H - 1: d = min(d, dist[j + 1][i + 1] + 5.39)
            if i > 0 and j < H - 1: d = min(d, dist[j + 1][i - 1] + 5.39)
            dist[j][i] = d

# ---- 補房子：漁港旁的村子，地圖上沒畫的透天厝沿著路排 ----
landmarks = [b for b in buildings if b['kind'] in ('restaurant', 'marketplace', 'place_of_worship')]
town = unary_union([b['g'].centroid.buffer(170) for b in landmarks]) if landmarks else None
waterU = unary_union(basin + ponds + rivers + quays + piers + [box(i * TX, j * TZ, (i + 1) * TX, (j + 1) * TZ) for j in range(H) for i in range(W) if grid[j][i] == SEA])
roadU = unary_union([l.buffer(w / 2 + .5, cap_style=2) for l, w, k, br in roads if not l.is_empty])
blocked = unary_union([waterU, roadU.buffer(.8), unary_union([b['g'].buffer(1.2) for b in buildings]), unary_union(parks + parking + woods)])
added = []
if town is not None:
    tp = prep(town)
    for l, w, k, br in roads:
        if k not in ('tertiary', 'unclassified', 'residential', 'service', 'living_street', 'tertiary_link') or l.is_empty: continue
        for seg in (l.geoms if hasattr(l, 'geoms') else [l]):
            L = seg.length; s = 3.0
            while s < L - 3:
                p0 = seg.interpolate(s); p1 = seg.interpolate(min(L, s + 1))
                dx, dz = p1.x - p0.x, p1.y - p0.y; n = math.hypot(dx, dz) or 1; dx /= n; dz /= n
                fw = rnd.choice([5.5, 6, 6.5, 7, 8])   # 透天厝面寬
                if tp.contains(p0):
                    for side in (1, -1):
                        if rnd.random() < .18: continue
                        dp = rnd.choice([11, 13, 15, 17]); off = w / 2 + 1.6
                        nx, nz = -dz * side, dx * side
                        cx, cz = p0.x + nx * (off + dp / 2), p0.y + nz * (off + dp / 2)
                        corners = [(cx + dx * a * fw / 2 + nx * b * dp / 2, cz + dz * a * fw / 2 + nz * b * dp / 2) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                        g = Polygon(corners)
                        if not FRAME.contains(g) or g.intersects(blocked): continue
                        lv = rnd.choices([2, 3, 4, 5], [2, 6, 5, 2])[0]
                        added.append({'g': g, 'name': None, 'kind': 'house', 'levels': lv, 'height': None, 'osm': False})
                        blocked = blocked.union(g.buffer(.6))
                s += fw + rnd.choice([0, 0, .5, 1, 3])
print('osm buildings', len(buildings), 'added', len(added))
buildings += added

# ---- 樓高 ----
FL = 3.4   # 每層樓高（一樓再挑高 0.4）
def bheight(b):
    if b['height']: return b['height']
    if b['levels']: return b['levels'] * FL + .4
    a = b['g'].area
    h = sum(ord(c) for c in str(round(b['g'].centroid.x)) + str(round(b['g'].centroid.y)))
    n = b['name'] or ''
    if '漁業綜合大樓' in n: return 4 * FL + .4   # 頂樓另外蓋旋轉餐廳
    if b['kind'] == 'marketplace': return 9
    if b['kind'] == 'place_of_worship': return 6.5
    if a < 40: return FL + .4
    if a > 1500: return 3 * FL + (h % 2) * FL + .4
    if a > 500: return 2 * FL + (h % 2) * FL + .4
    if b['kind'] == 'restaurant': return (3 + h % 2) * FL + .4   # 海鮮餐廳多是三、四樓
    return (3 + h % 3) * FL + .4
for b in buildings: b['h'] = round(bheight(b), 1)

# ---- 四間店：真實位置 ----
def find(name):
    for k, b in enumerate(buildings):
        if b['name'] and name in b['name']: return k
    return -1
shops = {'market': find('漁產品直銷中心'), 'restaurant': find('避風港海鮮館'), 'tackle': find('漁會漁業大樓')}
# 遊藝場：餐廳街附近一棟補上的房子
ref = buildings[shops['restaurant']]['g'].centroid
cand = sorted([k for k, b in enumerate(buildings) if not b['osm'] and b['g'].area > 60], key=lambda k: buildings[k]['g'].centroid.distance(ref))
shops['slot'] = cand[3] if len(cand) > 3 else cand[0]
SHOPNAME = {'market': '魚市場', 'restaurant': '海港餐廳', 'tackle': '釣具行', 'slot': '遊藝場'}
print('shops', {k: (buildings[v]['name'], round(buildings[v]['g'].centroid.x), round(buildings[v]['g'].centroid.y)) for k, v in shops.items()})

# ---- 格子：陸地細分 ----
G, F, S_, P, PO, RI, SE, DE, D, FA, Q, B = 0, 1, 2, 3, 4, 5, 6, 7, 8, 11, 14, 15
tiles = [[G] * W for _ in range(H)]
for j in range(H):
    for i in range(W):
        v = grid[j][i]
        if v == SEA: tiles[j][i] = SE if dist[j][i] < 45 else DE if dist[j][i] < 130 else FA
        elif v == BASIN: tiles[j][i] = SE
        elif v == POND: tiles[j][i] = PO
        elif v == RIVER: tiles[j][i] = RI
def landStamp(geoms, val, keepWater=True):
    if not geoms: return
    u = prep(unary_union(geoms))
    for j in range(H):
        for i in range(W):
            if keepWater and grid[j][i] != LAND: continue
            if u.contains(Point((i + .5) * TX, (j + .5) * TZ)): tiles[j][i] = val
# 村子裡的地面是水泥；沙灘：靠外海的陸地
pave = unary_union([b['g'].buffer(14) for b in buildings]) if buildings else None
landStamp([pave] if pave else [], P)
landStamp([unary_union(basin).buffer(12)] if basin else [], P)   # 港池旁邊是水泥地（漁港的碼頭面）
for j in range(H):
    for i in range(W):
        if grid[j][i] == LAND and tiles[j][i] == G:
            # 往北找外海
            for b in range(1, 18):
                if j - b >= 0 and grid[j - b][i] == SEA: tiles[j][i] = S_; break
landStamp(sands, S_); landStamp(woods, F); landStamp(parks, G); landStamp(parking, P)
landStamp([roadU], P)
landStamp(quays, Q, keepWater=False)
landStamp(piers, D, keepWater=False)
# 海岸線畫出來的細長陸地（防波堤）：兩邊都是水 → 堤防
isW = lambda i, j: 0 <= i < W and 0 <= j < H and (grid[j][i] in (SEA, BASIN) or tiles[j][i] in (D, Q))
for j in range(H):
    for i in range(W):
        if grid[j][i] == LAND and tiles[j][i] not in (D, Q) and ((any(isW(i - a, j) for a in (1, 2)) and any(isW(i + a, j) for a in (1, 2))) or (any(isW(i, j - b) for b in (1, 2, 3, 4)) and any(isW(i, j + b) for b in (1, 2, 3, 4)))):
            tiles[j][i] = Q
# 海岸線畫出來的細長陸地（防波堤）：兩邊都是水 → 堤防
isW = lambda i, j: 0 <= i < W and 0 <= j < H and (grid[j][i] in (SEA, BASIN) or tiles[j][i] in (D, Q))
for j in range(H):
    for i in range(W):
        if grid[j][i] == LAND and tiles[j][i] not in (D, Q) and ((any(isW(i - a, j) for a in (1, 2)) and any(isW(i + a, j) for a in (1, 2))) or (any(isW(i, j - b) for b in (1, 2, 3, 4)) and any(isW(i, j + b) for b in (1, 2, 3, 4)))):
            tiles[j][i] = Q
for b in buildings:
    u = prep(b['g'].buffer(-.3) if b['g'].area > 30 else b['g'])
    for j in range(max(0, int(b['g'].bounds[1] // TZ)), min(H, int(b['g'].bounds[3] // TZ) + 1)):
        for i in range(max(0, int(b['g'].bounds[0] // TX)), min(W, int(b['g'].bounds[2] // TX) + 1)):
            if grid[j][i] == LAND and u.contains(Point((i + .5) * TX, (j + .5) * TZ)): tiles[j][i] = B

# ---- 出生點：餐廳街前面、靠港池的空地，面向漁港 ----
rb = buildings[shops['restaurant']]['g'].centroid
bU = prep(unary_union([b['g'].buffer(6) for b in buildings]))
basinP = prep(unary_union(basin).buffer(7))
best = None
for j in range(H):
    for i in range(W):
        if tiles[j][i] in (P, G, Q):
            pt = Point((i + .5) * TX, (j + .5) * TZ)
            if bU.contains(pt) or not basinP.contains(pt) or unary_union(basin).contains(pt): continue
            d = pt.distance(rb)
            if best is None or d < best[0]: best = (d, i, j)
spawn = [best[1] + .5, best[2] + .5]
print('spawn', spawn, 'dist to restaurant', round(best[0]))
sp = Point(spawn[0] * TX, spawn[1] * TZ)
from shapely.ops import nearest_points
bc = nearest_points(unary_union(basin), sp)[0]
# 看向港池中間一點（最近的水面往港內再走 40 公尺）
cen = unary_union(basin).centroid
tx, tz = bc.x + (cen.x - bc.x) * .3, bc.y + (cen.y - bc.y) * .3
yaw = math.atan2(-(tx - sp.x), -(tz - sp.y))   # 遊戲的 yaw：前方 = (-sin yaw, -cos yaw)

# ---- 輸出 ----
def rle(rows):
    out, prev, n = [], None, 0
    for r in rows:
        for v in r:
            if v == prev: n += 1
            else:
                if prev is not None: out.append(chr(65 + prev) + (str(n) if n > 1 else ''))
                prev, n = v, 1
    out.append(chr(65 + prev) + (str(n) if n > 1 else ''))
    return ''.join(out)
def ring(g):
    g = g if isinstance(g, Polygon) else max(g.geoms, key=lambda x: x.area)
    g = g.simplify(.3)
    c = list(g.exterior.coords)[:-1]
    if Polygon(c).exterior.is_ccw: c.reverse()   # 統一順序（遊戲座標 Z 往南，外牆法線朝外）
    return [round(v, 1) for p in c for v in p]
def lines(l):
    gs = l.geoms if hasattr(l, 'geoms') else [l]
    return [[round(v, 1) for p in g.simplify(.4).coords for v in p] for g in gs if g.length > 1]
bld = []
for k, b in enumerate(buildings):
    shop = next((s for s, v in shops.items() if v == k), None)
    bld.append([b['h'], ring(b['g']), b['name'] if b['name'] and b['kind'] not in ('yes', 'house') or shop else (b['name'] if b['name'] else None), shop, b['kind'] if b['kind'] in ('restaurant', 'marketplace', 'place_of_worship') else None])
rd = []
for l, w, k, br in roads:
    if l.is_empty: continue
    for c in lines(l): rd.append([w, c])
qboxes = [box(i * TX, j * TZ, (i + 1) * TX, (j + 1) * TZ) for j in range(H) for i in range(W) if tiles[j][i] == Q]
qU = unary_union(qboxes + [g for g in quays if g.area > 20]).buffer(1.5, join_style=1).buffer(-2.2, join_style=1).simplify(.9)
quayRings = []
for g in (qU.geoms if hasattr(qU, 'geoms') else [qU]):
    if g.area < 30: continue
    quayRings.append([ring(Polygon(g.exterior))] + [ring(Polygon(h)) for h in g.interiors if Polygon(h).area > 20])
print('quay polygons', len(quayRings))
treeList = [[round(x, 1), round(z, 1)] for x, z in trees if 0 < x < X1 - X0 and 0 < z < Y1 - Y0]
for g in parks:   # 公園裡種一些樹
    pg = prep(g)
    for _ in range(int(g.area / 260)):
        x0, z0, x1, z1 = g.bounds; x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        if pg.contains(Point(x, z)) and not roadU.contains(Point(x, z)): treeList.append([round(x, 1), round(z, 1)])
basinRings = [ring(g) for g in (basin if basin else [])]
out = {'name': '竹圍漁港', 'W': W, 'H': H, 'tiles': rle(tiles), 'bld': bld, 'roads': rd, 'quays': quayRings, 'basin': basinRings,
       'trees': treeList, 'spawn': [round(spawn[0], 2), round(spawn[1], 2), round(yaw, 3)], 'shopName': SHOPNAME,
       'origin': [lat0, lon0, X0, Y1]}
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, separators=(',', ':'))
print('W H', W, H, 'bytes', len(json.dumps(out, ensure_ascii=False, separators=(',', ':'))), 'tiles rle', len(out['tiles']), 'roads', len(rd), 'trees', len(treeList))

# ---- 預覽圖 ----
from PIL import Image, ImageDraw
COL = {G: (134, 207, 78), F: (63, 143, 53), S_: (244, 220, 142), P: (170, 165, 155), PO: (76, 195, 182), RI: (58, 168, 220), SE: (42, 143, 214), DE: (26, 95, 174), FA: (14, 59, 132), D: (201, 162, 107), Q: (200, 200, 200), B: (160, 90, 70)}
im = Image.new('RGB', (W, H))
for j in range(H):
    for i in range(W): im.putpixel((i, j), COL[tiles[j][i]])
im = im.resize((W * 5 // 2, H * 2 // 2), Image.NEAREST)
dr = ImageDraw.Draw(im)
sc = .5
for k, b in enumerate(bld):
    r = b[1]; p = [(r[n] * sc, r[n + 1] * sc) for n in range(0, len(r), 2)]
    dr.polygon(p, outline=(255, 255, 0) if b[3] else (90, 40, 30), fill=(255, 0, 255) if b[3] else None)
dr.ellipse((spawn[0] * TX * sc - 4, spawn[1] * TZ * sc - 4, spawn[0] * TX * sc + 4, spawn[1] * TZ * sc + 4), fill=(255, 0, 0))
im.save(sys.argv[3])

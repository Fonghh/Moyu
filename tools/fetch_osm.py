# 從 OpenStreetMap 官方 API 分 16 塊抓竹圍漁港附近 2.6 公里的資料（Overpass 伺服器常常連不上）
# 地圖資料 © OpenStreetMap 貢獻者（ODbL）
import json, math, subprocess, time, os, sys
import xml.etree.ElementTree as ET
os.chdir(sys.argv[1])   # 用法：python3 -I fetch_osm.py 輸出資料夾（存 tile_*.xml 和 raw.json）
lat, lon, half = 25.1174502, 121.2420139, 1300
dlat = half/110574; dlon = half/(111320*math.cos(math.radians(lat)))
S, W, N, E = lat-dlat, lon-dlon, lat+dlat, lon+dlon
nodes, ways, rels = {}, {}, {}
K = 4
for qi in range(K):
  for qj in range(K):
    s = S+(N-S)*qi/K; n = S+(N-S)*(qi+1)/K; w = W+(E-W)*qj/K; e = W+(E-W)*(qj+1)/K
    fn = f'tile_{qi}{qj}.xml'
    if not (os.path.exists(fn) and os.path.getsize(fn) > 200):
      for att in range(3):
        r = subprocess.run(['curl', '-sS', '-f', '-m', '120', '-A', 'moyu-game-prototype/1.0', '-o', fn, f'https://api.openstreetmap.org/api/0.6/map?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}'], capture_output=True)
        if r.returncode == 0: break
        print('retry', qi, qj, r.stderr.decode()[:100], flush=True); time.sleep(4)
      time.sleep(1)
    root = ET.parse(fn).getroot()
    for el in root:
      tags = {t.get('k'): t.get('v') for t in el.findall('tag')}
      i = int(el.get('id', 0))
      if el.tag == 'node': nodes[i] = (float(el.get('lat')), float(el.get('lon')), tags or None)
      elif el.tag == 'way': ways[i] = ([int(nd.get('ref')) for nd in el.findall('nd')], tags)
      elif el.tag == 'relation': rels[i] = ([(m.get('type'), int(m.get('ref')), m.get('role')) for m in el.findall('member')], tags)
    print(qi, qj, os.path.getsize(fn), len(nodes), len(ways), flush=True)
json.dump({'meta': {'lat': lat, 'lon': lon, 'half': half}, 'nodes': {k: v for k, v in nodes.items()}, 'ways': ways, 'rels': rels}, open('raw.json', 'w'))
print('done', len(nodes), len(ways), len(rels))

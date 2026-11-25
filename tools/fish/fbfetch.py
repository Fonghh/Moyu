# 從 FishBase 抓每種魚的照片清單和照片（照片給遊戲非商業測試用、標示攝影者）
import re, os, sys, json, subprocess, time
OUT = sys.argv[1]
SP = {'mosq': 'Gambusia-affinis', 'tilapia': 'Oreochromis-mossambicus', 'crucian': 'Carassius-auratus', 'koi': 'Cyprinus-carpio',
      'zacco': 'Opsariichthys-evolans', 'ayu': 'Plecoglossus-altivelis', 'catfish': 'Silurus-asotus', 'salmon': 'Oncorhynchus-masou',
      'puffer': 'Takifugu-niphobles', 'mahi': 'Coryphaena-hippurus', 'tuna': 'Thunnus-orientalis', 'marlin': 'Istiophorus-platypterus',
      'oarfish': 'Regalecus-glesne', 'sunfish': 'Mola-mola', 'whaleshark': 'Rhincodon-typus', 'coelacanth': 'Latimeria-chalumnae',
      'piranha': 'Pygocentrus-nattereri', 'angler': 'Melanocetus-johnsonii'}
def get(url, fn):
    r = subprocess.run(['curl', '-sSL', '-m', '40', '-A', 'Mozilla/5.0', '-o', fn, url], capture_output=True)
    return r.returncode == 0 and os.path.exists(fn) and os.path.getsize(fn) > 300
meta = {}
for gid, name in SP.items():
    d = os.path.join(OUT, gid); os.makedirs(d, exist_ok=True)
    if not get(f'https://www.fishbase.se/summary/{name}.html', d + '/sum.html'): print('no summary', gid); continue
    s = open(d + '/sum.html', encoding='utf-8', errors='replace').read()
    ids = re.findall(r'ThumbnailsSummary\.php\?ID=(\d+)', s)
    if not ids: print('no id', gid); continue
    get(f'https://www.fishbase.se/photos/ThumbnailsSummary.php?ID={ids[0]}', d + '/th.html')
    t = open(d + '/th.html', encoding='utf-8', errors='replace').read()
    ents = re.findall(r"species/(\w+\.(?:jpg|gif|png))' alt='[^']+'>Photo by ([^<]+)</span></a><br>([^<]+)", t)
    meta[gid] = []
    for k, (pic, cr, loc) in enumerate(ents[:8]):
        if get(f'https://www.fishbase.se/images/species/{pic}', f'{d}/{k}_{pic}'): meta[gid].append([k, pic, cr.strip(), loc.strip(' ,by')])
    print(gid, ids[0], len(ents), 'photos;', [m[2][:20] + '/' + m[3][:14] for m in meta[gid]])
    time.sleep(.5)
json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w'), ensure_ascii=False, indent=1)

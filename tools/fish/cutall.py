import json, subprocess, glob, os
from PIL import Image
PICK = {   # 魚種: (資料夾, 編號, 門檻, 翻轉, 去鰭核)
 'mosq': ('mosq', 4, 35, 0, .12), 'tilapia': ('tilapia', 3, 35, 0, .12), 'crucian': ('crucian', 5, 35, 0, .12), 'koi': ('koi', 3, 40, 0, .12),
 'zacco': ('zacco', 2, 40, 0, .12), 'ayu': ('ayu', 0, 35, 0, .12), 'catfish': ('catfish', 4, 30, 0, .14), 'salmon': ('salmon', 0, 45, 0, .12, .12),
 'puffer': ('puffer', 3, 40, 0, .12), 'mahi': ('mahi', 7, 40, 0, .12, .08), 'tuna': ('tuna2', 2, 40, 0, .12), 'marlin': ('marlin', 5, 30, 0, .1, .5),
 'sunfish': ('sunfish', 2, 40, 0, .1),
 'coelacanth': ('coelacanth', 1, 35, 0, .12), 'piranha': ('piranha', 4, 35, 1, .12),
}
os.makedirs('cut2', exist_ok=True)
for gid, v in PICK.items():
    d, k, thr, flip, kern = v[:5]; trim = v[5] if len(v) > 5 else 0
    src = glob.glob(f'fb/{d}/{k}_*')[0]
    r = subprocess.run(['python3', '-I', 'cutfish.py', src, f'cut2/{gid}', str(thr), str(flip), str(kern), str(trim)], capture_output=True, text=True)
    print(gid, r.stdout.strip()[-60:], r.stderr.strip()[-200:])
ims = [(g, Image.open(f'cut2/{g}_check.png')) for g in PICK if os.path.exists(f'cut2/{g}_check.png')]
W = Image.new('RGB', (1500, ((len(ims) + 3) // 4) * 200), 'white')
for n, (g, im) in enumerate(ims):
    im.thumbnail((370, 190)); W.paste(im, ((n % 4) * 375, (n // 4) * 200))
W.save('cut2/check_all.jpg', quality=80)

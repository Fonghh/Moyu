# 把去背的魚照片打包成遊戲用的資料：assets/fish/<id>.webp（照片貼圖）＋ assets/fish/fish.json（身體輪廓、厚度、出處）
# 用法：python3 -I packfish.py 去背資料夾 輸出資料夾 FishBase資料夾
import json, sys, os, base64, io
import numpy as np, cv2
from PIL import Image, ImageEnhance
CUT, OUT, FB = sys.argv[1], sys.argv[2], sys.argv[3]
THICK = {'mosq': .5, 'tilapia': .45, 'crucian': .5, 'koi': .6, 'zacco': .5, 'ayu': .55, 'catfish': .9, 'salmon': .55, 'scad': .55, 'porgy': .42,
         'puffer': .85, 'grouper': .6, 'mahi': .4, 'tuna': .7, 'marlin': .45, 'sunfish': .25, 'coelacanth': .6, 'piranha': .45}
CREDIT = {'porgy': 'Shao, K.T.（臺灣魚類資料庫）', 'scad': 'Shao, K.T.（臺灣魚類資料庫）', 'grouper': 'Lai, N.-W.'}
meta = json.load(open(os.path.join(FB, 'meta.json'))); meta.update(json.load(open(os.path.join(FB, 'meta_tuna.json'))))
PICK = {'mosq': ('mosq', 4), 'tilapia': ('tilapia', 3), 'crucian': ('crucian', 5), 'koi': ('koi', 3), 'zacco': ('zacco', 2), 'ayu': ('ayu', 0), 'catfish': ('catfish', 4),
        'salmon': ('salmon', 0), 'puffer': ('puffer', 3), 'mahi': ('mahi', 7), 'tuna': ('tuna2', 2), 'marlin': ('marlin', 5), 'sunfish': ('sunfish', 2),
        'coelacanth': ('coelacanth', 1), 'piranha': ('piranha', 4)}
for gid, (d, k) in PICK.items():
    m = next(x for x in meta[d] if x[0] == k); CREDIT[gid] = m[2] + ('（臺灣魚類資料庫）' if 'Shao' in m[2] or 'Fish Database' in m[2] else '')
def pack(gid, src, hue=None):
    cut = Image.open(f'{CUT}/{src}_cut.png').convert('RGBA'); pr = json.load(open(f'{CUT}/{src}_prof.json'))
    w, h = pr['w'], pr['h']
    rgb = cut.convert('RGB'); rgb = ImageEnhance.Brightness(rgb).enhance(1.08); rgb = ImageEnhance.Color(rgb).enhance(1.15); rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    arr = np.asarray(rgb).copy(); al = np.asarray(cut.getchannel('A'))
    if hue == 'gold':   # 黃金錦鯉：整條變成金色
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 0] = 22; hsv[..., 1] = np.clip(hsv[..., 1] * .6 + 150, 0, 255); hsv[..., 2] = np.clip(hsv[..., 2] * 1.1 + 25, 0, 255)
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    if hue == 'glow':   # 輻射錦鯉：詭異的螢光綠
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 0] = 48; hsv[..., 1] = np.clip(hsv[..., 1] * .7 + 120, 0, 255); hsv[..., 2] = np.clip(hsv[..., 2] * 1.15 + 30, 0, 255)
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    if src == 'sunfish':   # 水裡拍的偏藍：去掉大部分的藍色，變回灰白
        hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 1] *= .22; hsv[..., 2] = np.clip(hsv[..., 2] * .95 + 10, 0, 255)
        arr = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    arr = cv2.inpaint(arr, ((al < 200) * 255).astype(np.uint8), 5, cv2.INPAINT_TELEA)   # 透明的地方填魚身的顏色，3D 邊緣才不透出背景色
    tex = Image.fromarray(arr); tex.putalpha(cut.getchannel('A'))
    tex = tex.resize((512, max(64, round(h * 512 / w))), Image.LANCZOS)
    tex.save(f'{OUT}/{gid}.webp', 'WEBP', quality=84, method=6)
    cols = [i for i, p in enumerate(pr['prof']) if p]; x0, x1 = cols[0], cols[-1]
    raw = []
    for kk in range(65):
        x = round(x0 + (x1 - x0) * kk / 64); p = pr['prof'][x] or pr['prof'][min(cols, key=lambda c: abs(c - x))]
        raw.append([p[0] / h, p[1] / h])
    # 身體太高的地方（旗魚的帆）當成鰭，身體最高到一般高度的 1.3 倍
    hh = np.array([b - t for t, b in raw]); cap = 1.3 * np.percentile(hh, 60)
    prof = [[round(max(t, b - cap), 4), round(b, 4)] for t, b in raw]
    return {'aspect': round(w / h, 4), 'bx': [round(x0 / w, 4), round(x1 / w, 4)], 'prof': prof, 'thick': THICK.get(src, .5), 'credit': CREDIT.get(src, '')}
out = {}
for gid in list(PICK) + ['porgy', 'scad', 'grouper']:
    out[gid] = pack(gid, gid); print(gid, os.path.getsize(f'{OUT}/{gid}.webp') // 1024, 'KB')
out['goldkoi'] = pack('goldkoi', 'koi', 'gold'); out['glowkoi'] = pack('glowkoi', 'koi', 'glow')
json.dump(out, open(f'{OUT}/fish.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('total', sum(os.path.getsize(f'{OUT}/{g}.webp') for g in out) // 1024, 'KB, json', os.path.getsize(f'{OUT}/fish.json') // 1024, 'KB')

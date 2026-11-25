# 魚的照片去背：從邊緣用顏色往內淹（背景大多是單色），再分出「身體」（去掉細的魚鰭）
# 用法：python3 -I cutfish.py 輸入.jpg 輸出前綴 [門檻] [翻轉 0/1]
import sys, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd

src, out = sys.argv[1], sys.argv[2]
thr = float(sys.argv[3]) if len(sys.argv) > 3 else 38
flip = len(sys.argv) > 4 and sys.argv[4] == '1'
im = Image.open(src).convert('RGB')
if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
a = np.asarray(im).astype(np.float32)
H, W, _ = a.shape
# GrabCut：先用「跟邊緣顏色很像＝可能是背景、中間＝可能是魚」當起點，讓演算法分
import cv2
bgr = cv2.cvtColor(a.astype(np.uint8), cv2.COLOR_RGB2BGR)
# 背景：用四邊的像素擬合一個平滑的二次曲面（處理漸層、暗角）
yy, xx = np.mgrid[0:H, 0:W]; yn, xn = yy / H - .5, xx / W - .5
bm = np.zeros((H, W), bool); bm[:10] = bm[-10:] = True; bm[:, :10] = bm[:, -10:] = True
A = np.stack([np.ones_like(xn), xn, yn, xn * xn, yn * yn, xn * yn, xn ** 4, yn ** 4], -1)
bgfit = np.zeros_like(a)
for ch in range(3):
    coef, *_ = np.linalg.lstsq(A[bm], a[..., ch][bm], rcond=None)
    bgfit[..., ch] = A @ coef
d = np.sqrt(((a - bgfit) ** 2).sum(-1))
mask = np.full((H, W), cv2.GC_PR_BGD, np.uint8)
mask[d > thr] = cv2.GC_PR_FGD
mask[d > thr * 2.2] = cv2.GC_FGD
mask[d < thr * .35] = cv2.GC_BGD
m = 6; mask[:m] = mask[-m:] = cv2.GC_BGD; mask[:, :m] = mask[:, -m:] = cv2.GC_BGD
bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
cv2.grabCut(bgr, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
fish = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)
fish = nd.binary_opening(fish, iterations=2)
fish = nd.binary_fill_holes(fish)
lbl, n = nd.label(fish)
if n > 1:
    sizes = nd.sum(fish, lbl, range(1, n + 1)); fish = lbl == (np.argmax(sizes) + 1)
ys, xs = np.where(fish)
y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
pad = 4
y0, x0 = max(0, y0 - pad), max(0, x0 - pad); y1, x1 = min(H - 1, y1 + pad), min(W - 1, x1 + pad)
fish = fish[y0:y1 + 1, x0:x1 + 1]; rgb = a[y0:y1 + 1, x0:x1 + 1]
h, w = fish.shape
# 身體：開運算去掉細的鰭（核大小跟魚的高度成比例）
k = max(3, int(h * float(sys.argv[5]) if len(sys.argv) > 5 else h * .11))
st = np.zeros((2 * k + 1, 2 * k + 1), bool); yy, xx = np.ogrid[-k:k + 1, -k:k + 1]; st[yy * yy + xx * xx <= k * k] = True
body = nd.binary_opening(fish, structure=st)
lbl, n = nd.label(body)
if n > 1:
    sizes = nd.sum(body, lbl, range(1, n + 1)); body = lbl == (np.argmax(sizes) + 1)
# 每一行（x）身體的上下緣（給 3D 用），從頭（左）到尾柄
trim = float(sys.argv[6]) if len(sys.argv) > 6 else 0
if trim:   # 離身體太遠的東西（樹枝、釣線）剪掉
    fish = fish & nd.binary_dilation(body, iterations=max(1, int(h * trim)))
prof = []
for x in range(w):
    col = np.where(body[:, x])[0]
    prof.append([int(col.min()), int(col.max())] if len(col) else None)
# 邊緣柔和的透明度
alpha = Image.fromarray((fish * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
img = Image.fromarray(rgb.astype(np.uint8)); img.putalpha(alpha)
img.save(out + '_cut.png')
Image.fromarray((body * 255).astype(np.uint8)).save(out + '_body.png')
json.dump({'w': w, 'h': h, 'prof': prof}, open(out + '_prof.json', 'w'))
# 檢查用：去背的結果放在棋盤格上，身體範圍描紅線
chk = Image.new('RGB', (w, h))
for y in range(0, h, 16):
    for x in range(0, w, 16):
        chk.paste((200, 200, 200) if (x // 16 + y // 16) % 2 else (150, 150, 150), (x, y, x + 16, y + 16))
chk.paste(img, (0, 0), img)
edge = body ^ nd.binary_erosion(body, iterations=2)
c = np.asarray(chk).copy(); c[edge] = [255, 0, 0]
Image.fromarray(c).save(out + '_check.png')
print(out, 'size', w, h, 'fish px', int(fish.sum()), 'body px', int(body.sum()))

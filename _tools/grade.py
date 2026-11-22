#!/usr/bin/env python3
"""全站相片調色（2026-11-22 Erica 定）：
- 相片保持原色；偏暗（中位亮度 <0.50）先提亮，gamma 最多 0.8。
- 偏黃（中間調 (R+G)/2−B > 0.10）先修走一半黃色，再提亮到中位亮度約 0.62。
- 黑毛狗特寫（KEEP）一律原相，提亮會偏藍。
用法：python3 _tools/grade.py <相片> [...]（原地覆蓋）。只可以對原相行一次。"""
import os, sys
import numpy as np
from PIL import Image

KEEP = {'parent-review-dog-3.jpg', 'parent-review-dog-hotel-1.jpg'}
YELLOW, DARK, BRIGHT = 0.10, 0.50, 0.62

def _lum(a): return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]

def _lift(a, target, floor):
    lum = _lum(a); med = float(np.median(lum))
    if med >= target: return a
    g = np.log(target) / np.log(max(med, 0.05)); g = max(1 + 0.75 * (g - 1), floor)
    new = np.clip(lum, 1e-4, 1) ** g
    return a * (new / np.clip(lum, 1e-4, 1))[..., None]

def grade(im):
    a = np.asarray(im.convert('RGB')).astype(np.float64) / 255
    l = _lum(a); m = (l > .2) & (l < .9)
    r, g, b = a[m].mean(0) if m.any() else a.reshape(-1, 3).mean(0)
    y = (r + g) / 2 - b
    if y > YELLOW:
        fix = (y - 0.06) / 2                      # 修走一半黃色
        a = a * np.array([1 - fix * .5, 1, 1 + fix * 1.2])
        a = _lift(np.clip(a, 0, 1), BRIGHT, 0.75)
    else:
        a = _lift(a, DARK, 0.8)
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))

def grade_file(path, quality=88):
    if os.path.basename(path) in KEEP: return False
    grade(Image.open(path)).save(path, quality=quality); return True

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(('已調色 ' if grade_file(p) else '保留原相 ') + p)

#!/usr/bin/env python3
"""全站相片統一色調（國際學校風格：微暖、柔和、米色霧面）。2026-11-20 定。
用法：python3 _tools/grade.py <相片> [<相片> ...]   （原地覆蓋）
photos.py 換相後會自動調用。已調過嘅相唔好重複調（會越調越淡）。"""
import sys
import numpy as np
from PIL import Image

def grade(im):
    a = np.asarray(im.convert('RGB')).astype(np.float64) / 255
    m = a.reshape(-1, 3).mean(0)
    tgt = np.array([m.mean() * 1.03, m.mean(), m.mean() * 0.95])      # 微暖
    a = a * (1 + 0.4 * (tgt / np.maximum(m, 1e-3) - 1))                 # 白平衡只修四成
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]; med = float(np.median(lum))
    g = np.log(0.58) / np.log(min(max(med, 0.05), 0.95)); g = 1 + 0.5 * (g - 1)
    a = np.clip(a, 0, 1) ** g                                          # 曝光拉近一半
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])[..., None]
    a = lum + (a - lum) * 0.88                                         # 飽和 0.88
    a = 0.035 + a * 0.93                                               # 黑位提升、高光略收
    a = a * np.array([1.0, 0.995, 0.975]) + np.array([0.012, 0.008, 0])  # 米色
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))

def grade_file(path, quality=85):
    grade(Image.open(path)).save(path, quality=quality)

if __name__ == '__main__':
    for p in sys.argv[1:]:
        grade_file(p); print('已調色', p)

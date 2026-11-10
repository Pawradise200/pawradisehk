#!/usr/bin/env python3
"""換相工具：讀《相片對照表》，把新相片壓縮後放入網站對應位置。

用法：python3 _tools/photos.py
- 對照表：~/Desktop/內部文件/網站重建/相片對照表.md（「檔名」欄填相片檔名）
- 相片：~/Desktop/內部文件/網站重建/新相片/（可有子資料夾）
- 輸出：assets/img/slots/<編號>.jpg（長邊 1800px）；之後行 build.py 即生效
"""
import os, re, subprocess, sys

HOME = os.path.expanduser('~')
TABLE = os.path.join(HOME, 'Desktop/內部文件/網站重建/相片對照表.md')
PHOTOS = os.path.join(HOME, 'Desktop/內部文件/網站重建/新相片')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets/img/slots')

def index_photos():
    found = {}
    for dp, _, fs in os.walk(PHOTOS):
        for f in fs:
            found.setdefault(f.lower(), os.path.join(dp, f))
            found.setdefault(os.path.splitext(f)[0].lower(), os.path.join(dp, f))
    return found

def main():
    os.makedirs(OUT, exist_ok=True)
    photos = index_photos()
    done, missing, empty = [], [], []
    for line in open(TABLE, encoding='utf-8'):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 5 or not re.match(r'^[a-z]+-[a-z]+-\d+$', cells[0]):
            continue
        slot, name = cells[0], cells[-1]
        if not name:
            empty.append(slot); continue
        src = photos.get(name.lower()) or photos.get(os.path.splitext(name)[0].lower())
        if not src:
            missing.append((slot, name)); continue
        dst = os.path.join(OUT, slot + '.jpg')
        subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '80',
                        '-Z', '1800', src, '--out', dst], check=True, capture_output=True)
        done.append((slot, name))
    print('✅ 已換 %d 張' % len(done))
    for s, n in done: print('   %s ← %s' % (s, n))
    if missing:
        print('⚠️ 找不到相片 %d 張（檢查檔名）' % len(missing))
        for s, n in missing: print('   %s：%s' % (s, n))
    print('⬜ 未填檔名 %d 個位置' % len(empty))
    return 1 if missing else 0

if __name__ == '__main__':
    sys.exit(main())

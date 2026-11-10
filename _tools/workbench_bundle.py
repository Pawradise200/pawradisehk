#!/usr/bin/env python3
"""把已 build 嘅頁面打包畀《網站工作台》做真實預覽。
用法：python3 _tools/workbench_bundle.py <輸出資料夾>
輸出：<out>/site/{home,academy,hotel}.html＋用到嘅 assets（路徑改為相對）。"""
import os, re, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(sys.argv[1], 'site')
shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
PAGES = {'home': 'index.html', 'academy': 'academy/index.html', 'hotel': 'hotel/index.html'}
used = set()
for key, rel in PAGES.items():
    s = open(os.path.join(ROOT, rel), encoding='utf-8').read()
    def asset(m):
        path = m.group(2).split('?')[0]
        used.add(path)
        return m.group(1) + path.lstrip('/')
    s = re.sub(r'((?:src|href)=")(/assets/[^"]+)', asset, s)
    s = re.sub(r'(url\()(/assets/[^)]+)', lambda m: asset(m) , s)
    s = re.sub(r'href="/[^"]*"', 'href="#"', s)           # 預覽內唔跳頁
    s = re.sub(r'<link rel="canonical"[^>]*>', '', s)
    open(os.path.join(out, key + '.html'), 'w', encoding='utf-8').write(s)
# CSS 入面引用嘅相
for css in [p for p in used if p.endswith('.css')]:
    t = open(os.path.join(ROOT, css.lstrip('/')), encoding='utf-8').read()
    for m in re.findall(r'url\((/assets/[^)]+)\)', t):
        used.add(m)
for p in used:
    src = os.path.join(ROOT, p.lstrip('/'))
    if not os.path.exists(src): continue
    dst = os.path.join(out, p.lstrip('/'))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if p.endswith('.css'):
        t = open(src, encoding='utf-8').read().replace('url(/assets/', 'url(../')
        open(dst, 'w', encoding='utf-8').write(t)
    else:
        shutil.copy(src, dst)
print(len(used), 'assets')

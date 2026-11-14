#!/usr/bin/env python3
"""把已 build 嘅頁面打包畀《網站工作台》做真實預覽。
用法：python3 _tools/workbench_bundle.py <輸出資料夾>
輸出：<out>/site/<各頁 key>.html＋用到嘅 assets（路徑改為相對）。"""
import os, re, sys, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = {'home': 'index.html', 'academy': 'academy/index.html', 'trial': 'academy/trial/index.html',
         'schoollife': 'academy/school-life/index.html', 'hotel': 'hotel/index.html', 'about': 'about/index.html',
         'faq': 'faq/index.html', 'parents': 'parents/index.html', 'tst': 'campus/tsim-sha-tsui/index.html',
         'skw': 'campus/shau-kei-wan/index.html', 'privacy': 'privacy/index.html', 'terms': 'terms/index.html'}
NAMES = {'home': '首頁', 'academy': '學院頁', 'trial': '體驗試堂', 'schoollife': '校園生活', 'hotel': '酒店頁',
         'about': '關於我們', 'faq': '常見問題', 'parents': '家長專區', 'tst': '尖沙咀校區', 'skw': '筲箕灣校區',
         'privacy': '私隱政策', 'terms': '網站條款'}
if __name__ == '__main__':
    out = os.path.join(sys.argv[1], 'site')
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
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

#!/usr/bin/env python3
"""由已 build 嘅頁面抽出《網站工作台》可改嘅字同相片位，寫入工作台 HTML 嘅 content JSON。
用法：python3 _tools/workbench_extract.py <工作台資料夾>
（工作台資料夾入面要有 網站工作台.html；相片縮圖用 macOS sips 縮到 560px）"""
import os, re, sys, json, base64, subprocess, tempfile
from html.parser import HTMLParser
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from workbench_bundle import PAGES, NAMES

TAGS = {'h1', 'h2', 'h3', 'p', 'cite', 'summary', 'figcaption', 'b', 'small', 'span'}
VOID = {'br', 'img', 'input', 'meta', 'link', 'hr', 'source', 'wbr'}

class N:
    def __init__(s, tag, attrs, parent):
        s.tag, s.a, s.parent, s.kids = tag, dict(attrs), parent, []
    def text(s):
        return ''.join(k if isinstance(k, str) else k.text() for k in s.kids)
    def walk(s):
        for k in s.kids:
            if isinstance(k, N):
                yield k; yield from k.walk()

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.root = N('root', [], None); s.cur = s.root
    def handle_starttag(s, t, a):
        n = N(t, a, s.cur); s.cur.kids.append(n)
        if t not in VOID: s.cur = n
    def handle_endtag(s, t):
        c = s.cur
        while c is not s.root and c.tag != t: c = c.parent
        if c is not s.root: s.cur = c.parent
    def handle_data(s, d): s.cur.kids.append(d)

def hidden(n):
    while n:
        if isinstance(n, N) and 'display:none' in (n.a.get('style') or ''): return True
        if isinstance(n, N) and n.tag in ('header', 'footer'): return True
        n = n.parent
    return False

def thumb(src):
    p = os.path.join(ROOT, src.lstrip('/').split('?')[0])
    if not os.path.exists(p): return ''
    with tempfile.TemporaryDirectory() as d:
        o = os.path.join(d, 't.jpg')
        subprocess.run(['sips', '-Z', '560', '-s', 'format', 'jpeg', '-s', 'formatOptions', '70', p, '--out', o], capture_output=True)
        return 'data:image/jpeg;base64,' + base64.b64encode(open(o, 'rb').read()).decode()

def norm(t): return re.sub(r'\s+', ' ', t).strip()

out = []
for key, rel in PAGES.items():
    pr = P(); pr.feed(open(os.path.join(ROOT, rel), encoding='utf-8').read())
    secs = []
    for s in pr.root.walk():
        if s.tag != 'section' or hidden(s): continue
        cls = (s.a.get('class') or '').split()
        sid = s.a.get('id') or ('hero' if cls and cls[0] in ('hc-hero', 'page-hero', 'hhero') else '')
        if not sid or any(x['id'] == sid for x in secs): continue
        fields, photos = [], []
        for e in s.walk():
            if hidden(e): continue
            if e.a.get('data-slot'):
                img = e.tag == 'img'
                photos.append({'slot': e.a['data-slot'], 'alt': e.a.get('alt', '') if img else '未有相',
                               'img': thumb(e.a.get('src', '')) if img else ''})
            if e.tag not in TAGS or (e.tag == 'span' and e.a.get('class')): continue
            if any(isinstance(k, N) and k.tag in TAGS - {'span'} for k in e.walk()): continue
            t = norm(e.text())
            if t: fields.append({'tag': e.tag, 'text': t, 'id': f'{key}.{sid}.{len(fields)}'})
        if fields or photos: secs.append({'id': sid, 'fields': fields, 'photos': photos})
    out.append({'key': key, 'name': NAMES[key], 'file': rel, 'sections': secs})
    print(key, len(secs), '節', sum(len(x['fields']) for x in secs), '字', sum(len(x['photos']) for x in secs), '相')

wb = os.path.join(sys.argv[1], '網站工作台.html')
h = open(wb, encoding='utf-8').read()
data = json.dumps(out, ensure_ascii=False).replace('</', '<\\/')
h2 = re.sub(r'(<script type="application/json" id="content">).*?(</script>)', lambda m: m.group(1) + data + m.group(2), h, count=1, flags=re.S)
open(wb, 'w', encoding='utf-8').write(h2)
print('已寫入', wb, len(h2) // 1024, 'KB')

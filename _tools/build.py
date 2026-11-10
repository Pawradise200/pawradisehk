#!/usr/bin/env python3
"""Pawradise 網站產生器。

用法：喺 repo 根目錄行  python3 _tools/build.py
- 讀 _src/pages/ 每一頁（第一行係 <!--meta {...} -->），套入 _src/layout.html
- 輸出到 repo 根目錄同樣路徑（例如 _src/pages/hotel/index.html → hotel/index.html）
- 產生 sitemap.xml、robots.txt、舊 .dc.html 轉址頁
- 最後自動檢查：內部連結、標題、描述、禁用字眼
唔使安裝任何嘢，只用 Python 內建功能。
"""
import json, os, re, sys, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '_src')
PAGES = os.path.join(SRC, 'pages')
SITE = 'https://pawradisehk.com'
WHATSAPP = 'https://wa.me/85294596420'

# 舊網址 → 新網址（GitHub Pages 做唔到伺服器轉址，所以用轉址頁）
REDIRECTS = {
    'index.dc.html': '/',
    'about.dc.html': '/about/',
    'academy.dc.html': '/academy/',
    'hotel.dc.html': '/hotel/',
}

NAV_ZH = [
    ('/academy/', '毛孩社交學院'),
    ('/academy/trial/', '體驗試堂'),
    ('/hotel/', '校園式寵物酒店'),
    ('/about/', '關於我們'),
    ('/parents/', '家長專區'),
]
NAV_EN = [
    ('/en/hotel/', 'Dog Hotel'),
    ('/en/academy/trial/', 'Trial Day'),
    ('/', '中文'),
]

# 禁用字眼（品牌規則）；另外會自動檢查價錢（收費唔放網站）
BANNED = ['主人', '你隻狗']

ORG = {
    '@type': 'Organization',
    '@id': SITE + '/#org',
    'name': 'Pawradise',
    'alternateName': ['Pawradise Limited', 'Pawradise 校園式寵物酒店及毛孩社交學院'],
    'url': SITE + '/',
    'logo': SITE + '/assets/img/crest.png',
    'foundingDate': '2021',
    'sameAs': ['https://www.instagram.com/pawradise_hk', 'https://linktr.ee/Pawradisehk'],
}
TST = {
    '@type': 'LocalBusiness',
    '@id': SITE + '/campus/tsim-sha-tsui/#place',
    'name': 'Pawradise 尖沙咀校區',
    'description': '校園式寵物酒店及毛孩社交學院',
    'parentOrganization': {'@id': SITE + '/#org'},
    'url': SITE + '/campus/tsim-sha-tsui/',
    'telephone': '+852 9459 6420',
    'image': SITE + '/assets/img/og-default.jpg',
    'address': {
        '@type': 'PostalAddress',
        'streetAddress': '彌敦道 200 號 16 至 17 樓及天台',
        'addressLocality': '尖沙咀',
        'addressRegion': '九龍',
        'addressCountry': 'HK',
    },
    'openingHoursSpecification': [{
        '@type': 'OpeningHoursSpecification',
        'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'opens': '09:00', 'closes': '20:00',
    }],
}
# 筲箕灣校區：開幕前唔加 LocalBusiness 標記


def read_page(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'\s*<!--meta\s*(\{.*?\})\s*-->\s*', raw, re.S)
    if not m:
        sys.exit('缺少 meta：' + path)
    return json.loads(m.group(1)), expand_includes(raw[m.end():])


def expand_includes(content):
    """<!--include 名--> 換成 _src/partials/名.html（多頁共用嘅區塊，只喺一個地方改）"""
    def sub(m):
        f = os.path.join(SRC, 'partials', m.group(1) + '.html')
        if not os.path.exists(f):
            sys.exit('搵唔到共用片段：' + f)
        return re.sub(r'<!--.*?-->', '', open(f, encoding='utf-8').read(), flags=re.S).strip()  # 註解唔輸出
    return re.sub(r'<!--include\s+([\w-]+)\s*-->', sub, content)


def url_of(rel):
    rel = rel.replace(os.sep, '/')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel


def nav_html(items, current):
    out = []
    for href, label in items:
        cur = ' aria-current="page"' if href == current else ''
        out.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return ''.join(out)


def faq_jsonld(content):
    qs = re.findall(r'<details[^>]*>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>', content, re.S)
    if not qs:
        return None
    strip = lambda s: re.sub(r'<[^>]+>', '', s).strip()
    return {
        '@type': 'FAQPage',
        'mainEntity': [{'@type': 'Question', 'name': strip(q),
                        'acceptedAnswer': {'@type': 'Answer', 'text': strip(a)}} for q, a in qs],
    }


def apply_slots(content):
    """相片位：assets/img/slots/<編號>.jpg 存在就用新相，否則保留現有相片或虛線框。"""
    def has(slot):
        return os.path.exists(os.path.join(ROOT, 'assets/img/slots', slot + '.jpg'))
    def img_sub(m):
        tag, slot = m.group(0), m.group(1)
        if has(slot):
            tag = re.sub(r'src="[^"]*"', 'src="/assets/img/slots/%s.jpg"' % slot, tag, 1)
        return tag
    content = re.sub(r'<img data-slot="([^"]+)"[^>]*>', img_sub, content)
    def ph_sub(m):
        slot = m.group(1)
        if has(slot):
            return '<img class="hc-ph-img" src="/assets/img/slots/%s.jpg" alt="" loading="lazy">' % slot
        return m.group(0)
    content = re.sub(r'<div class="hc-ph" data-slot="([^"]+)">.*?</div>', ph_sub, content, flags=re.S)
    def rv_sub(m):
        slot = m.group(1)
        if has(slot):
            return '<img class="hc-rv-img" src="/assets/img/slots/%s.jpg" alt="" loading="lazy">' % slot
        return m.group(0)
    content = re.sub(r'<div class="hc-rv-ph" data-slot="([^"]+)">.*?</div>', rv_sub, content, flags=re.S)
    return content

def render(layout, meta, content, url):
    lang = meta.get('lang', 'zh-HK')
    en = lang.startswith('en')
    graph = [ORG]
    if meta.get('localbusiness'):
        graph.append(TST)
    faq = faq_jsonld(content)
    if faq:
        graph.append(faq)
    jsonld = '<script type="application/ld+json">%s</script>' % json.dumps(
        {'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)
    hreflang = ''
    if meta.get('alt'):
        alt = meta['alt']
        pair = {lang: url, ('zh-HK' if en else 'en'): alt}
        hreflang = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">' % (k, SITE, v) for k, v in pair.items())
    vals = {
        'lang': lang,
        'title': html.escape(meta['title']),
        'description': html.escape(meta['description']),
        'robots': 'noindex,nofollow' if (meta.get('noindex') or meta.get('draft')) else 'index,follow',
        'canonical': SITE + url,
        'hreflang': hreflang,
        'og_image': SITE + meta.get('og_image', '/assets/img/og-default.jpg'),
        'og_locale': 'en_HK' if en else 'zh_HK',
        'jsonld': jsonld,
        'skip_text': 'Skip to content' if en else '跳到主要內容',
        'home': '/en/hotel/' if en else '/',
        'nav': nav_html(NAV_EN if en else NAV_ZH, meta.get('nav', url)),
        'content': content.strip(),
    }
    out = layout
    for k, v in vals.items():
        out = out.replace('{{%s}}' % k, v)
    return out


def redirect_page(target):
    t = SITE + target
    return ('<!doctype html><html lang="zh-HK"><head><meta charset="utf-8">'
            '<title>Pawradise</title><meta name="robots" content="noindex">'
            '<link rel="canonical" href="%s"><meta http-equiv="refresh" content="0; url=%s">'
            '<script>location.replace(%s)</script></head>'
            '<body><p>網頁已搬到 <a href="%s">%s</a></p></body></html>\n') % (t, target, json.dumps(target), target, t)


def main():
    layout = open(os.path.join(SRC, 'layout.html'), encoding='utf-8').read()
    # 樣式檔加版本號：內容一改，瀏覽器就會攞新版本（唔會用舊快取）
    import hashlib
    css_ver = hashlib.md5(open(os.path.join(ROOT, 'assets/css/site.css'), 'rb').read()).hexdigest()[:8]
    layout = layout.replace('/assets/css/site.css"', '/assets/css/site.css?v=%s"' % css_ver)
    c_ver = hashlib.md5(open(os.path.join(ROOT, 'assets/css/site-c.css'), 'rb').read()).hexdigest()[:8]
    layout = layout.replace('/assets/css/site-c.css"', '/assets/css/site-c.css?v=%s"' % c_ver)
    built, sitemap = [], []
    for dirpath, _, files in os.walk(PAGES):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, PAGES)
            meta, content = read_page(src)
            content = apply_slots(content)
            url = url_of(rel)
            dst = os.path.join(ROOT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, 'w', encoding='utf-8').write(render(layout, meta, content, url))
            built.append((rel, url, meta))
            if not meta.get('noindex') and not meta.get('draft'):
                sitemap.append(url)

    for old, target in REDIRECTS.items():
        open(os.path.join(ROOT, old), 'w', encoding='utf-8').write(redirect_page(target))

    today = date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in sorted(sitemap):
        sm.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (SITE, u, today))
    sm.append('</urlset>')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(sm) + '\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(
        'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % SITE)

    # ---------- 自動檢查 ----------
    problems = []
    for rel, url, meta in built:
        page = open(os.path.join(ROOT, rel), encoding='utf-8').read()
        if '{{' in page:
            problems.append('%s：有未填嘅 {{ }}' % rel)
        if not 10 <= len(meta['title']) <= 70:
            problems.append('%s：標題長度 %d（建議 10–70）' % (rel, len(meta['title'])))
        if not 40 <= len(meta['description']) <= 160:
            problems.append('%s：描述長度 %d（建議 40–160）' % (rel, len(meta['description'])))
        for w in BANNED:
            if w in page:
                problems.append('%s：出現禁用字眼「%s」' % (rel, w))
        # 收費唔放網站（2026-10-28 Erica 定）
        if re.search(r'(HK)?\$\s?\d|九五折|\d+\s?折優惠', page):
            problems.append('%s：出現價錢或折扣（收費唔放網站）' % rel)
        if re.search(r'\\u[0-9a-fA-F]{4}', page):
            problems.append('%s：有 \\uXXXX escape' % rel)
        for href in re.findall(r'(?:href|src)="(/[^"#?]*)', page):
            p = os.path.join(ROOT, href.lstrip('/'))
            if href.endswith('/'):
                p = os.path.join(p, 'index.html')
            if not os.path.exists(p):
                problems.append('%s：連結失效 %s' % (rel, href))
    print('已產生 %d 頁、%d 個轉址頁；sitemap 收錄 %d 頁' % (len(built), len(REDIRECTS), len(sitemap)))
    if problems:
        print('\n⚠️ 檢查發現 %d 個問題：' % len(problems))
        for p in sorted(set(problems)):
            print('  - ' + p)
        sys.exit(1)
    print('✅ 檢查全部通過')


if __name__ == '__main__':
    main()

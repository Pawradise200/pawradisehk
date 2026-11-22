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
    ('/hotel/', '校園式寵物酒店'),
    ('/faq/', '常見問題'),
    ('/about/', '關於我們'),
]
NAV_EN = [
    ('/en/', 'Home'),
    ('/en/academy/trial/', 'Trial Day'),
    ('/en/hotel/', 'Boarding House'),
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
    'url': SITE + '/',
    'telephone': '+852 9459 6420',
    'image': SITE + '/assets/img/pawradise-dog-hotel-academy-hong-kong.jpg',
    'address': {
        '@type': 'PostalAddress',
        'streetAddress': '彌敦道 200 號 16 至 17 樓及天台花園',
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

# ---------- 家長指南（/guide/）----------
# 每篇文章＝_src/pages/guide/<英文網址>/index.html，meta 加 "article": {category, date, cover, excerpt}
# build 會自動：套文章頁頭頁尾、排入 /guide/ 列表（新到舊）、加 Article＋麵包屑標記、檢查分類同日期
GUIDE_CATS = [('behaviour', '狗狗行為'), ('social', '狗狗社交'), ('boarding', '寵物寄宿'), ('care', '日常照顧')]
GUIDE_CTA = {
    'behaviour': ('想了解狗狗的情緒與社交狀態？', '學院新生由招生日體驗試堂開始，導師會先觀察及評估。', '/academy/trial/', '了解體驗試堂'),
    'social': ('想了解狗狗的情緒與社交狀態？', '學院新生由招生日體驗試堂開始，導師會先觀察及評估。', '/academy/trial/', '了解體驗試堂'),
    'boarding': ('準備為狗狗安排寄宿？', '入住前會先評估狗狗的性格及風險評級，再安排照顧。', '/hotel/', '了解校園式寵物酒店'),
    'care': ('有其他照顧上的疑問？', '歡迎透過 WhatsApp 與我們聯絡，導師樂意解答。', '/faq/', '查看常見問題'),
}


def fmt_date(d):
    y, m, dd = d.split('-')
    return '%s 年 %d 月 %d 日' % (y, int(m), int(dd))


def guide_card(a):
    cat = dict(GUIDE_CATS)[a['category']]
    img = '<img src="%s" alt="" loading="lazy">' % a['cover'] if a.get('cover') else '<div class="ph"></div>'
    return ('<a class="hc-gcard" href="%s" data-cat="%s">%s<div class="bd"><span class="caps">%s</span>'
            '<h3>%s</h3><p>%s</p><time datetime="%s">%s</time></div></a>') % (
        a['url'], a['category'], img, cat, html.escape(a['h1']), html.escape(a['excerpt']), a['date'], fmt_date(a['date']))


def guide_list_html(articles):
    if not articles:
        return '<p class="hc-gempty">第一篇文章即將推出。</p>'
    jump = '<nav class="hc-jump hc-gfilter" aria-label="文章分類"><a href="#all" data-f="all" class="on">全部</a>' + ''.join(
        '<a href="#%s" data-f="%s">%s</a>' % (k, k, v) for k, v in GUIDE_CATS if any(a['category'] == k for a in articles)) + '</nav>'
    script = ('<script>(function(){var n=document.querySelector(".hc-gfilter");if(!n)return;'
              'function go(f){n.querySelectorAll("a").forEach(function(a){a.classList.toggle("on",a.dataset.f===f)});'
              'document.querySelectorAll(".hc-gcard").forEach(function(c){c.hidden=!(f==="all"||c.dataset.cat===f)})}'
              'n.addEventListener("click",function(e){var a=e.target.closest("a");if(!a)return;e.preventDefault();go(a.dataset.f);history.replaceState(null,"","#"+a.dataset.f)});'
              'var h=location.hash.slice(1);if(h)go(h)})();</script>')
    return jump + '<div class="hc-glist">' + ''.join(guide_card(a) for a in articles) + '</div>' + script


def wrap_article(meta, content, url, articles):
    a = meta['article']; cat = dict(GUIDE_CATS)[a['category']]
    cover = ('<figure class="hc-acover"><img src="%s" alt="%s"></figure>' % (a['cover'], html.escape(a.get('cover_alt', meta['h1'])))) if a.get('cover') else ''
    head = ('<div class="hc hc-article"><section class="hc-sec hc-pagehead"><div class="wrap hc-aw">'
            '<nav class="hc-crumb" aria-label="麵包屑"><a href="/">首頁</a> › <a href="/guide/">家長指南</a> › <a href="/guide/#%s">%s</a></nav>'
            '<span class="caps">%s</span><h1>%s</h1><p class="hc-ameta">%s・%s</p></div></section>'
            '<section class="hc-sec hc-abody"><div class="wrap hc-aw">%s') % (
        a['category'], cat, cat, html.escape(meta['h1']), fmt_date(a['date']), html.escape(a.get('author', 'Pawradise 導師團隊')), cover)
    q, sub, href, label = GUIDE_CTA[a['category']]
    rel = [x for x in articles if x['url'] != url and x['category'] == a['category']][:3] or [x for x in articles if x['url'] != url][:3]
    tail = '</div></section>'
    tail += ('<section class="hc-sec hc-invite"><div class="wrap"><h2>%s</h2><p>%s</p>'
             '<a class="btn btn-navy" href="%s">%s</a> <a class="hc-alink" href="%s">WhatsApp 查詢</a></div></section>') % (q, sub, href, label, WHATSAPP)
    if rel:
        tail += '<section class="hc-sec hc-cream"><div class="wrap"><div class="hc-head"><div><span class="caps">Read more</span><h2>延伸閱讀</h2></div></div><div class="hc-glist">%s</div></div></section>' % ''.join(guide_card(x) for x in rel)
    return head + content.strip() + tail + '</div>'


def article_jsonld(meta, url):
    a = meta['article']; cat = dict(GUIDE_CATS)[a['category']]
    art = {'@type': 'Article', 'headline': meta['h1'], 'description': meta['description'],
           'datePublished': a['date'], 'dateModified': a.get('updated', a['date']),
           'author': {'@type': 'Organization', 'name': a.get('author', 'Pawradise 導師團隊'), '@id': SITE + '/#org'},
           'publisher': {'@id': SITE + '/#org'}, 'mainEntityOfPage': SITE + url, 'inLanguage': 'zh-HK',
           'articleSection': cat}
    if a.get('cover'):
        art['image'] = SITE + a['cover']
    crumbs = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': '首頁', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': '家長指南', 'item': SITE + '/guide/'},
        {'@type': 'ListItem', 'position': 3, 'name': meta['h1'], 'item': SITE + url}]}
    return [art, crumbs]



def is_draft(path):
    """睇 _src/pages/<path>/index.html 頂部 meta 有冇 draft。"""
    f = os.path.join(ROOT, '_src', 'pages', path.strip('/'), 'index.html') if path.strip('/') else os.path.join(ROOT, '_src', 'pages', 'index.html')
    if not os.path.exists(f): return True
    m = re.match(r'<!--meta (.*?) -->', open(f, encoding='utf-8').read(), re.S)
    return bool(m and json.loads(m.group(1)).get('draft'))

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


def apply_slots(content, en=False):
    """相片位：assets/img/slots/<編號>.jpg 存在就用新相，否則保留現有相片或虛線框。"""
    try:
        SLOTS = json.load(open(os.path.join(ROOT, '_tools/slots.json'), encoding='utf-8'))
    except OSError:
        SLOTS = {}
    def fname(slot):
        return SLOTS.get(slot, {}).get('file', slot + '.jpg')
    def alt(slot, en=False):
        s = SLOTS.get(slot, {})
        return html.escape(s.get('alt_en', '') if en else s.get('alt', ''))
    def has(slot):
        return os.path.exists(os.path.join(ROOT, 'assets/img/slots', fname(slot)))
    def img_sub(m):
        tag, slot = m.group(0), m.group(1)
        if has(slot):
            tag = re.sub(r'src="[^"]*"', 'src="/assets/img/slots/%s"' % fname(slot), tag, 1)
            if alt(slot, en):
                tag = re.sub(r'alt="[^"]*"', 'alt="%s"' % alt(slot, en), tag, 1)
        return tag
    content = re.sub(r'<img data-slot="([^"]+)"[^>]*>', img_sub, content)
    def ph_sub(m):
        extra, slot = m.group(1) or '', m.group(2)
        if has(slot):
            return '<img class="hc-ph-img%s" data-slot="%s" src="/assets/img/slots/%s" alt="%s" loading="lazy">' % (extra, slot, fname(slot), alt(slot, en))
        return m.group(0)
    content = re.sub(r'<div class="hc-ph( [a-z-]+)?" data-slot="([^"]+)">.*?</div>', ph_sub, content, flags=re.S)
    def rv_sub(m):
        slot = m.group(1)
        if has(slot):
            return '<img class="hc-rv-img" data-slot="%s" src="/assets/img/slots/%s" alt="%s" loading="lazy">' % (slot, fname(slot), alt(slot, en))
        return m.group(0)
    content = re.sub(r'<div class="hc-rv-ph" data-slot="([^"]+)">.*?</div>', rv_sub, content, flags=re.S)
    def logo_sub(m):
        key, label = m.group(1), m.group(2)
        for ext in ('png', 'svg', 'jpg'):
            if os.path.exists(os.path.join(ROOT, 'assets/img/logos', key + '.' + ext)):
                return '<span class="logo" data-logo="%s"><img src="/assets/img/logos/%s.%s" alt="%s"></span>' % (key, key, ext, label)
        return m.group(0)
    content = re.sub(r'<span class="logo" data-logo="([^"]+)">([^<]*)</span>', logo_sub, content)
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
    if meta.get('article'):
        graph += article_jsonld(meta, url)
    jsonld = '<script type="application/ld+json">%s</script>' % json.dumps(
        {'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)
    hreflang = ''
    if meta.get('alt') and not meta.get('draft') and not is_draft(meta['alt']):  # 對方係草稿就唔出 hreflang
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
        'og_image': SITE + meta.get('og_image', (meta.get('article') or {}).get('cover') or '/assets/img/pawradise-dog-hotel-academy-hong-kong.jpg'),
        'og_locale': 'en_HK' if en else 'zh_HK',
        'jsonld': jsonld,
        'skip_text': 'Skip to content' if en else '跳到主要內容',
        'footer': open(os.path.join(SRC, 'partials', 'footer-en.html' if en else 'footer-zh.html'), encoding='utf-8').read(),
        'wa_text': 'WhatsApp us' if en else 'WhatsApp 查詢',
        'menu_label': 'Main menu' if en else '主選單',
        'open_menu': 'Open menu' if en else '開啟選單',
        'crest_alt': 'Pawradise crest' if en else 'Pawradise 校徽',
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
    # 先收集家長指南文章（草稿唔入列表）
    articles, guide_problems = [], []
    for dirpath, _, files in os.walk(os.path.join(PAGES, 'guide')):
        if 'index.html' not in files or dirpath == os.path.join(PAGES, 'guide'):
            continue
        rel = os.path.relpath(os.path.join(dirpath, 'index.html'), PAGES)
        m, _c = read_page(os.path.join(dirpath, 'index.html'))
        a = m.get('article')
        if not a:
            guide_problems.append('%s：家長指南文章冇 article 設定' % rel); continue
        if a.get('category') not in dict(GUIDE_CATS):
            guide_problems.append('%s：分類要係 %s 其中一個' % (rel, '／'.join(k for k, _ in GUIDE_CATS))); continue
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(a.get('date', ''))):
            guide_problems.append('%s：日期格式要係 2026-12-01' % rel); continue
        if not m.get('h1'):
            guide_problems.append('%s：冇 h1（文章大標題）' % rel); continue
        if not m.get('draft') or os.environ.get('GUIDE_PREVIEW'):  # GUIDE_PREVIEW=1：本機預覽草稿文章（唔好咁樣 push）
            articles.append(dict(a, url=url_of(rel), h1=m['h1'], excerpt=a.get('excerpt') or m['description']))
    articles.sort(key=lambda x: x['date'], reverse=True)
    for dirpath, _, files in os.walk(PAGES):
        for f in sorted(files):
            if not f.endswith('.html'):
                continue
            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, PAGES)
            meta, content = read_page(src)
            content = apply_slots(content, str(meta.get('lang', '')).startswith('en'))
            url = url_of(rel)
            if meta.get('article') and meta['article'].get('category') in dict(GUIDE_CATS):
                content = wrap_article(meta, content, url, articles)
            content = content.replace('<!--guide-list-->', guide_list_html(articles))
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
    problems = list(guide_problems)
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

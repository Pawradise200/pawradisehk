#!/usr/bin/env python3
"""套用《網站工作台》嘅改字。

用法：python3 _tools/workbench_apply.py <匯出資料夾>
匯出資料夾＝ArtifactData list edits 用 out_dir 存低嘅 JSON（<dir>/edits/*.json）。
只處理 status=pending 嘅改字：喺 _src/pages/<file> 搵 original（要剛好出現一次）換成 text。
意見（notes）同次序（order）由 Claude 人手處理。完成後列出已套用嘅 doc id。
"""
import json, os, sys, glob, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = sys.argv[1]
done, fail = [], []
for f in sorted(glob.glob(os.path.join(d, 'edits', '*.json'))):
    j = json.load(open(f, encoding='utf-8'))
    doc = j.get('data', j)
    if doc.get('status') != 'pending' or doc.get('text') == doc.get('original'):
        continue
    p = os.path.join(ROOT, '_src/pages', doc['file'])
    s = open(p, encoding='utf-8').read()
    cands = [doc['original'], html.escape(doc['original'], quote=False)]
    hit = next((c for c in cands if s.count(c) == 1), None)
    if not hit:
        fail.append((os.path.basename(f), doc['original'][:30], '原文搵唔到或者出現多過一次'))
        continue
    new = doc['text'] if hit == doc['original'] else html.escape(doc['text'], quote=False)
    s = s.replace(hit, new.replace('\n', '<br>'), 1)
    open(p, 'w', encoding='utf-8').write(s)
    done.append(os.path.splitext(os.path.basename(f))[0])
print(json.dumps({'applied': done, 'failed': fail}, ensure_ascii=False, indent=1))

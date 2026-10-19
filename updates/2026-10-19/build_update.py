#!/usr/bin/env python3
"""Build only this dated supplement; never mutate the previous survey. Requires Markdown==3.9."""
import html
import json
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent
STYLE = """
:root{color-scheme:light dark;--bg:#f6f8f7;--fg:#172822;--muted:#53675e;--line:#ccd9d2;--accent:#096c51;--sheet:#fff}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--fg);font:18px/1.72 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}header,main,footer{max-width:880px;margin:auto;padding:26px 28px}header{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid var(--line);font-size:14px}main{padding-top:40px;padding-bottom:80px}h1{font-size:clamp(32px,6vw,54px);line-height:1.08;letter-spacing:-.04em;margin:0 0 30px}h2{font-size:29px;line-height:1.2;letter-spacing:-.025em;margin:70px 0 25px;padding-top:22px;border-top:1px solid var(--line)}p{margin:18px 0}a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}strong{font-weight:680}li{margin:15px 0}table{width:100%;border-collapse:collapse;margin:24px 0;font-size:16px;background:var(--sheet)}td,th{padding:14px;text-align:left;border-bottom:1px solid var(--line)}td:last-child,th:last-child{text-align:right;white-space:nowrap}footer{font-size:14px;color:var(--muted);border-top:1px solid var(--line)}a:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
@media(prefers-color-scheme:dark){:root{--bg:#0c1511;--fg:#edf5f0;--muted:#9fb7a9;--line:#30463a;--accent:#5ae8b2;--sheet:#15241c}}@media(max-width:480px){body{font-size:17px}header,main,footer{padding-left:20px;padding-right:20px}h2{font-size:25px}td,th{padding:10px;font-size:14px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{body{background:#fff;color:#000;font-size:11pt}header{display:none}h2{break-after:avoid}a{color:inherit}main{max-width:none;padding:0}table{break-inside:avoid}}
"""
for lang, other, label in [('ru','en','English'),('en','ru','Русский')]:
    source = (ROOT / f'{lang}.md').read_text(encoding='utf-8')
    body = markdown.markdown(source, extensions=['tables','toc'], output_format='html')
    title = source.splitlines()[0].lstrip('# ').strip()
    nav = f'<a href="{other}.html">{label}</a> · <a href="registry-delta.json">JSON</a> · <a href="references.bib">BibTeX</a>'
    doc = f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>{html.escape(title)}</title><style>{STYLE}</style></head><body><header><span>SWARM DYNAMICS / 19.10.2026</span><nav>{nav}</nav></header><main>{body}</main><footer>Anton Razzhigaev &amp; Ouroboros · <a href="{lang}.md">Markdown</a></footer></body></html>'
    (ROOT / f'{lang}.html').write_text(doc,encoding='utf-8')
records = json.loads((ROOT/'registry-delta.json').read_text(encoding='utf-8'))['records']
entries=[]
for record in records:
    if 'first_public' not in record:
        continue
    fields={'title': record['title'], 'author':' and '.join(record['authors']), 'year':record['first_public'][:4], 'url':record['url'], 'note':f"Version {record['version']}, {record['version_date']}; checked 2026-10-19"}
    if record.get('arxiv'):
        fields.update(eprint=record['arxiv'],archivePrefix='arXiv')
    entries.append('@misc{'+record['id']+',\n'+',\n'.join('  '+k+' = {'+v.replace('&',r'\&')+'}' for k,v in fields.items())+'\n}')
(ROOT/'references.bib').write_text('\n\n'.join(entries)+'\n',encoding='utf-8')
print(f'Built RU/EN supplement and {len(entries)} BibTeX records; previous survey untouched.')

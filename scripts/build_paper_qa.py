#!/usr/bin/env python3
"""Check a genuinely compiled report; optionally render pages/contact sheets.

Requires Poppler tools. --render additionally requires Pillow. This is build
verification, not independent scholarly review or a licensing determination.
"""
from pathlib import Path
from collections import Counter
import argparse, datetime, hashlib, json, re, subprocess, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / 'paper'
QA = PAPER / 'qa'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    QA.mkdir(exist_ok=True)
    pdf=PAPER/'swarm-dynamics.pdf'
    run(['pdftotext','-layout',str(pdf),str(QA/'swarm-dynamics.txt')])
    run(['pdftotext','-bbox-layout',str(pdf),str(QA/'text-bounds.html')])
    (QA/'fonts.txt').write_text(run(['pdffonts',str(pdf)]))
    (QA/'pdfinfo.txt').write_text(run(['pdfinfo',str(pdf)]))
    log=(PAPER/'build/main.log').read_text(errors='replace')
    blg=(PAPER/'build/main.blg').read_text(errors='replace')
    sources=[PAPER/'main.tex',*sorted((PAPER/'sections').glob('*.tex')),PAPER/'appendix-evidence.tex',PAPER/'appendix-figures.tex']
    source='\n'.join(p.read_text() for p in sources)
    keys=set(re.findall(r'@\w+\{([^,]+),',(PAPER/'references.bib').read_text()))
    cites=set()
    for match in re.finditer(r'\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}',source):
        cites.update(k.strip() for k in match[1].split(','))
    appendix=(PAPER/'appendix-evidence.tex').read_text()
    records=json.loads((PAPER/'evidence-matrix.json').read_text())['records']
    inventory=json.loads((PAPER/'corpus-inventory.json').read_text())
    manual_rendered=re.findall(r'^% Evidence unit: (.+)$',appendix,re.M)
    inventory_rendered=re.findall(r'^% Inventory record: (.+)$',appendix,re.M)
    rights=json.loads((PAPER/'figure-rights.json').read_text())
    failures=[]
    for row in rights['figures']:
        for path_key,hash_key in [('legacy_path','legacy_sha256'),('print_path','print_sha256')]:
            if sha(PAPER/row[path_key])!=row[hash_key]:failures.append(row[path_key])
    vendor=json.loads((PAPER/'vendor/upstream.json').read_text())
    vendor_bad=[name for name,data in vendor['files'].items() if sha(PAPER/'vendor'/name)!=data['sha256']]
    out_of_page=[]
    ns={'x':'http://www.w3.org/1999/xhtml'}
    tree=ET.parse(QA/'text-bounds.html')
    for number,page in enumerate(tree.findall('.//x:page',ns),1):
        w,h=float(page.attrib['width']),float(page.attrib['height'])
        for word in page.findall('.//x:word',ns):
            a=word.attrib
            if float(a['xMin']) < -0.5 or float(a['yMin']) < -0.5 or float(a['xMax'])>w+.5 or float(a['yMax'])>h+.5:
                out_of_page.append({'page':number,'word':word.text,'bounds':a})
    pages=int(re.search(r'^Pages:\s+(\d+)',(QA/'pdfinfo.txt').read_text(),re.M)[1])
    aux=(PAPER/'build/main.aux').read_text()
    labels={key:int(page) for key,page in re.findall(r'\\newlabel\{(app:[^}]+)\}\{\{[^}]*\}\{(\d+)\}',aux)}
    text=(QA/'swarm-dynamics.txt').read_text()
    refs=next(i for i,p in enumerate(text.split('\f'),1) if re.search(r'^References(?:\s|$)',p,re.M))
    warning_counts={
        'latex':log.count('LaTeX Warning:'),
        'natbib':log.count('Package natbib Warning:'),
        'bibtex':blg.count('Warning--'),
        'overfull_boxes':log.count('Overfull'),
        'underfull_boxes':log.count('Underfull'),
        'missing_characters':log.count('Missing character:')}
    font_rows=(QA/'fonts.txt').read_text().splitlines()[2:]
    fonts_embedded=all(re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$',line) for line in font_rows if line.strip())
    checks={
        'all_citations_resolve':not(cites-keys),
        'normal_build_has_no_archive_dependency':'.claude/sprints/' not in (PAPER/'build/main.fls').read_text(),
        'manual_records_render_once':Counter(manual_rendered)==Counter(r['id'] for r in records),
        'inventory_records_render_once':Counter(inventory_rendered)==Counter(r['id'] for r in inventory),
        'preserved_figure_hashes_match':not failures,
        'upstream_vendor_hashes_match':not vendor_bad,
        'text_within_page_bounds':not out_of_page,
        'all_fonts_embedded':fonts_embedded,
        'no_unresolved_reference_markers':'??' not in text,
        'no_overflow_or_citation_warnings':all(v==0 for k,v in warning_counts.items() if k!='underfull_boxes')}
    report={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'pdf':{'path':'paper/swarm-dynamics.pdf','sha256':sha(pdf),'bytes':pdf.stat().st_size,'pages':pages},
        'main_pages':f'1–{refs-1}','bibliography_pages':f'{refs}–{labels["app:evidence"]-1}',
        'appendix_starts':labels,'warning_counts':warning_counts,
        'bibliography_entries':len(keys),'cited_keys':len(cites),'missing_keys':sorted(cites-keys),
        'manual_evidence_records':len(records),'administrative_inventory_records':len(inventory),
        'preserved_logical_figures':len(rights['figures']),'original_vector_diagrams':len(rights['original_report_diagrams']),
        'checks':checks,'figure_hash_failures':failures,'vendor_hash_failures':vendor_bad,'out_of_page_text':out_of_page,
        'visual_check':'Recorded separately in visual-review.md; automated checks do not establish visual readability.'}
    (QA/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.render:
        from PIL import Image, ImageDraw
        dest=QA/'pages';dest.mkdir(exist_ok=True)
        # Only disposable previews produced by this script are replaced.
        for old in dest.glob('page-*.png'):old.unlink()
        for old in QA.glob('contact-*.jpg'):old.unlink()
        run(['pdftoppm','-scale-to','1400','-png',str(pdf),str(dest/'page')])
        imgs=sorted(dest.glob('page-*.png'))
        if len(imgs)!=pages:raise RuntimeError('Stale or missing rendered pages; inspect qa/pages before proceeding.')
        for start in range(0,len(imgs),4):
            sheet=Image.new('RGB',(1440,2100),'#dedede');draw=ImageDraw.Draw(sheet)
            for slot,path in enumerate(imgs[start:start+4]):
                im=Image.open(path).convert('RGB');im.thumbnail((700,1010))
                x=slot%2*720+10;y=slot//2*1050+28
                sheet.paste(im,(x,y));draw.text((x,y-20),f'PDF page {start+slot+1}',fill='black')
            sheet.save(QA/f'contact-{start//4+1:02}.jpg',quality=88)
    print(json.dumps(report,indent=2))
    if not all(checks.values()):raise SystemExit('Build verification failed; inspect verification.json')

if __name__=='__main__':main()

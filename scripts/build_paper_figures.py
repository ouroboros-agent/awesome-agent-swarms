#!/usr/bin/env python3
"""Preserve the current 52-figure set and rebuild this report's vector diagrams.

No downloads. --source reads the preserved Oct 4 research tree; it never writes it.
Without --source, only original diagrams are rebuilt from this script.
Requires Python 3 and pdflatex on PATH (or /opt/homebrew/bin/pdflatex).
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'paper' / 'figures'
AUTHOR_FILES = ['front.md', 'chapters/w1_t5_t1.md', 'chapters/w2_t3_wild.md',
                'chapters/w3_t2_incident.md', 'chapters/w4_t4_beliefs.md', 'back.md']

# Figure-specific sources override composite-card landing pages.
SOURCE_OVERRIDE = {
    'kim-scaling-agent-systems_fig3.png': 'https://arxiv.org/html/2512.08296v2',
    'kim-scaling-agent-systems_fig4.png': 'https://arxiv.org/html/2512.08296v2',
    'artificial-hivemind_fig5.png': 'https://arxiv.org/abs/2609.33936',
    'attractor-states_fig1.png': 'https://arxiv.org/abs/2606.30571',
    'attractor-states_fig4.png': 'https://www.anthropic.com/claude-4-system-card',
    'hf-incident-case_fig1.png': 'https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/',
    'hf-incident-case_fig2.png': 'https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/',
    'anthropic-c-compiler_fig2.png': 'https://github.com/anthropics/claudes-c-compiler',
    'ord-swarm-scaling_fig3.png': 'https://forum.effectivealtruism.org/posts/EkaBCQwL5hhTtxEwR/swarm-scaling',
}

# Captions for the inherited dashboards are kept as historical metadata; these
# aggregate pre-deduplication records and are not used as unique-work counts.
DASH_CAPTIONS = {
 'dash_mechanisms_dark.png': 'The archived review maps composition, connections, emergent phenomena, outcomes and risks to its chapter sequence.',
 'dash_scale_dark.png': 'Archived metadata records by population size and evidence class. Concurrent, cumulative and configured-capacity observations use different marks. These are 153 metadata records, not a deduplicated count of publications.',
 'dash_timeline_dark.png': 'Archived metadata records by first-publication month and source type; the displayed 153-record denominator predates publication-level deduplication.',
 'dash_orgs_dark.png': 'Archived organization classes and named organizations. One record can name multiple organizations; the denominator is 153 metadata records.',
 'dash_models_dark.png': 'Archived model-family counts and numbers of models per record. Multiple model families can occur in one record; 42 records do not name or use models. The denominator is 153 metadata records.',
 'dash_topics_dark.png': 'Archived topic by evidence-class matrix. A record can carry up to three topic labels; the denominator is 153 metadata records.',
}

SELECTED = [
 'kim-scaling-agent-systems_fig4.png',
 'recursive-language-models_fig4.png', 'agensh-1024_fig2.png',
 'sat-teams_fig2.png', 'anthropic-art-enzymes_fig1.png',
 'wiki-copying_fig4.png', 'opus55-card_fig1.png',
 'ai-organizations_fig1.png', 'deepmind-cheating-whistleblowing_fig1.png',
 'peer-preservation_fig1.png', 'hf-incident-case_fig2.png',
 'artificial-hivemind_fig5.png', 'semantic-collapse_fig2.png',
 'flag-game_fig2_hires.png', 'okawa-biased-consensus_fig2.png',
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def preserve(source):
    catalog = {x['file']: x for p in sorted((source/'figcat').glob('*.json'))
               for x in json.loads(p.read_text())}
    entries = []
    for author_file in AUTHOR_FILES:
        for line_number, line in enumerate((source/'build'/author_file).read_text().splitlines(), 1):
            if not line.startswith('!fig '):
                continue
            filename, caption, credit = [s.strip() for s in line[5:].split('|', 2)]
            cat = catalog.get(filename, {})
            cid = cat.get('card_id', filename.split('_fig')[0])
            card = {}
            card_rel = None
            for d in ['cards', 'cards_lanes']:
                p = source/d/(cid+'.json')
                if p.exists():
                    card, card_rel = json.loads(p.read_text()), str(p.relative_to(source))
                    break
            figure_records = card.get('figures', [])
            if not isinstance(figure_records, list):
                figure_records = []
            exact = next((x for x in figure_records if isinstance(x, dict)
                          and Path(str(x.get('local_file') or '')).name == filename), {})
            original = source/'figs'/filename
            assert original.is_file(), original
            target = FIG/'legacy'/filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            trim = source/'build'/'figs_trim'/filename
            # A no-derivatives figure is displayed from the unmodified original.
            rights = cat.get('license') or exact.get('license') or card.get('license') or ''
            display_source = original if 'BY-NC-ND' in rights else (trim if trim.exists() else original)
            display = FIG/'print'/filename
            display.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(display_source, display)
            urls = card.get('urls') or {}
            primary = (urls.get('primary') or urls.get('html') or urls.get('pdf')) if isinstance(urls, dict) else None
            fig_url = exact.get('image_url')
            source_url = SOURCE_OVERRIDE.get(filename) or fig_url or primary
            if source_url:
                source_url = re.search(r'https?://[^\s]+', source_url).group(0) if source_url.startswith('http') else source_url
            original_review = filename.startswith('dash_') or filename == 'anthropic-c-compiler_fig2.png'
            if filename.startswith('dash_'):
                rights = 'Original figure from the archived review. Retained unchanged; no third-party figure license asserted.'
                source_url = 'archive:build/charts.py'
            if filename == 'anthropic-c-compiler_fig2.png':
                rights = 'Original review analysis; underlying repository data recorded as CC0-1.0. This is not an Anthropic figure.'
            if original_review:
                category = 'original-review-figure'
            elif 'BY-NC-ND' in rights:
                category = 'CC-BY-NC-ND-4.0-recorded'
            elif 'CC BY 4.0' in rights:
                category = 'CC-BY-4.0-recorded'
            else:
                category = 'third-party-no-open-license-established'
            caption_en = DASH_CAPTIONS.get(filename) or cat.get('shows') or exact.get('caption_en')
            if filename == 'openai-navier-stokes_fig1.png':
                caption_en = 'The technical manuscript sketches the inner core at successive times approaching the claimed singular time: inward spiral flow and axial flow concentrate as the region contracts; radial contraction is faster than height contraction.'
            if filename.startswith('hf-incident-case'):
                caption_en = ('The METR investigation diagram follows the typical path from an isolated benchmark agent to an unauthorized shared message board and collaborative exploitation.' if filename.endswith('fig1.png') else 'Hourly message-board activity from July 9 to July 13, 2026, grouped by message category; timestamps were reconstructed and may be imprecise.')
            entry = {
                'id': filename.removesuffix('.png'), 'filename': filename,
                'source_card_id': None if filename.startswith('dash_') else cid,
                'bibliography_key': None if filename.startswith('dash_') else cid,
                'legacy_path': str(target.relative_to(ROOT/'paper')),
                'print_path': str(display.relative_to(ROOT/'paper')),
                'archive_original_path': str(original.relative_to(source)),
                'archive_print_path': str(display_source.relative_to(source)),
                'original_sha256': sha(original), 'legacy_sha256': sha(target), 'print_sha256': sha(display),
                'print_changes': ('None; byte-identical to archived original.' if sha(original)==sha(display)
                                  else 'Existing Oct 4 print variant: near-white margins trimmed by archived build/build.py. No new crop or relabelling.'),
                'author_file': 'build/'+author_file, 'author_file_line': line_number,
                'caption_ru_verbatim': caption, 'credit_ru_verbatim': credit,
                'caption_en_archival': caption_en,
                'source_figure_label': cat.get('label') or exact.get('label') or ('Unnumbered original archived review dashboard' if filename.startswith('dash_') else ('Figure 1 (technical PDF, p. 4)' if filename == 'openai-navier-stokes_fig1.png' else ('Figure 1' if filename == 'hf-incident-case_fig1.png' else 'Figure 2'))),
                'source_url': source_url, 'source_urls_recorded': urls,
                'attribution_recorded': credit.removeprefix('Источник: ').strip(),
                'rights_category': category, 'rights_recorded': rights,
                'rights_evidence': {'card':card_rel,'figcat': cat or None},
                'rights_validation': 'Inherited from the Oct 3-4 verified source archive; not a new permissions audit. The quoted rights note is evidence, not a grant of rights.',
                'distribution_note': ('Available in the private review candidate. No blanket license or third-party permission is claimed.' if not original_review else 'Original archived review graphic; retained with source provenance.'),
                'appendix_selected': filename in SELECTED,
                'main_text_selected': filename == 'test-time-communication_fig3.png',
            }
            if filename == 'artificial-hivemind_fig5.png':
                entry['bibliography_key'] = 'artificial-hivemind-reevaluation'
            if filename.startswith('hf-incident-case'):
                entry['bibliography_key'] = 'hf-metr-redwood-investigation'
            if filename.startswith('cursor-scaling'):
                entry['bibliography_key'] = 'cursor-self-driving'
            if filename == 'attractor-states_fig1.png':
                entry['bibliography_key'] = 'attractor-states-ko-geiping-paper'
            if filename == 'attractor-states_fig4.png':
                entry['bibliography_key'] = 'attractor-states-anthropic-card'
            entries.append(entry)
    assert len(entries)==52 and len({e['filename'] for e in entries})==52
    assert all(e['source_url'] and e['caption_en_archival'] for e in entries), [(e['filename'], e['source_url'], e['caption_en_archival']) for e in entries if not e['source_url'] or not e['caption_en_archival']]
    manifest = {'schema_version':1,'source_archive':'swarm-dynamics-20261003',
                'archive_snapshot':'Current six author files, Oct 4 version',
                'figure_count':len(entries), 'selected_for_appendix_count':len(SELECTED),
                'policy':'The source package preserves all 52 current figures. Each third-party asset retains its own recorded rights; no blanket reuse license is created.',
                'figures': entries,
                'original_report_diagrams': [
                    {'file':'figures/taxonomy.pdf','source':'scripts/build_paper_figures.py','authors':'Anton Razzhigaev and Ouroboros','license':'CC BY 4.0','kind':'Original conceptual synthesis; no empirical data.'},
                    {'file':'figures/coordination-layers.pdf','source':'scripts/build_paper_figures.py','authors':'Anton Razzhigaev and Ouroboros','license':'CC BY 4.0','kind':'Original conceptual synthesis; no empirical data.'},
                ]}
    (ROOT/'paper'/'figure-rights.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Preserved 52 original figures and 52 display variants; exact hashes in paper/figure-rights.json')

PREAMBLE = r'''\documentclass[tikz,border=3pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds}
\definecolor{ink}{RGB}{24,39,53}
\definecolor{blue}{RGB}{36,82,126}
\definecolor{pale}{RGB}{239,245,250}
\definecolor{teal}{RGB}{34,108,104}
\definecolor{warm}{RGB}{153,88,42}
\begin{document}
'''

TAXONOMY = PREAMBLE+r'''
% Cells share one height and start at the top; no hyphenation inside the narrow cells.
\newcommand{\cell}[2]{\parbox[t][2.2cm][t]{3.6cm}{\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000
 \textbf{#1}\\[4pt]#2}}
\begin{tikzpicture}[font=\sffamily\small, text=ink,
  box/.style={draw=blue!60,rounded corners=2pt,fill=pale,inner sep=8pt,anchor=north west}]
\node[box] (a) at (0,0) {\cell{1. Model composition}{Same model or mixed models; role prompts; competence and error correlations.}};
\node[box] (b) at (4.25,0) {\cell{2. Interaction graph}{Directed or undirected; dense or sparse; fixed or dynamic; allowed and realized edges.}};
\node[box] (c) at (8.5,0) {\cell{3. Exchange medium}{Direct messages, shared files, repositories, tools, or an external platform.}};
\node[box] (d) at (12.75,0) {\cell{4. Organization}{Designed roles; learned policies; emergent conventions. These can coexist.}};
\node[box] (e) at (0,-2.85) {\cell{5. Memory}{Private or shared; lifetime; retrieval and updates; provenance and access control.}};
\node[box] (f) at (4.25,-2.85) {\cell{6. Population scale}{Concurrent $N_{\mathrm{conc}}(t)$; cumulative $N_{\mathrm{cum}}(T)$; configured capacity $N_{\mathrm{cap}}$.}};
\node[box] (g) at (8.5,-2.85) {\cell{7. Baseline control}{Model and tasks; tools and context; tokens, compute, dollars, or wall-clock time.}};
\node[box] (h) at (12.75,-2.85) {\cell{8. Budget and outcome}{Quality, latency and cost; diversity, coordination failures and safety outcomes.}};
\node[anchor=north west,align=left,font=\sffamily\small,text width=16.7cm] at (0,-5.85)
 {A swarm result is conditional on all eight descriptors. An agent count alone does not identify an experimental treatment.};
\end{tikzpicture}
\end{document}
'''

COORDINATION = PREAMBLE+r'''
\begin{tikzpicture}[font=\sffamily\small,text=ink,
 agent/.style={circle,draw=blue,fill=pale,minimum size=7mm,inner sep=0pt},
 edge/.style={draw=blue!80,line width=.7pt},
 art/.style={draw=teal,fill=teal!7,rounded corners=2pt,minimum height=8mm,align=center},
 label/.style={align=left,anchor=north west,text width=7.7cm}]
\node[label,font=\sffamily\bfseries] at (0,0) {Graph: who can influence whom?};
\node[agent] (a) at (1.0,-1.0) {A};
\node[agent] (b) at (3.4,-1.0) {B};
\node[agent] (c) at (2.2,-2.3) {C};
\draw[edge,<->] (a)--(b);\draw[edge,<->] (a)--(c);\draw[edge,<->] (b)--(c);
\node[align=left,text width=3cm,anchor=west] at (4,-1.6) {Contact is not enough. Timing and content determine what propagates.};
\node[label,font=\sffamily\bfseries] at (8.6,0) {Medium: where does influence travel?};
\node[agent] (d) at (9.3,-1.0) {A};
\node[agent] (e) at (11.6,-1.0) {B};
\node[agent] (f) at (13.9,-1.0) {C};
\node[art,minimum width=6.4cm] (store) at (11.6,-2.3) {Shared repository / memory / environment};
\draw[edge,<->] (d)--(store);\draw[edge,<->] (e)--(store);\draw[edge,<->] (f)--(store);
\node[label] at (8.6,-3.0) {Artifact reads and writes induce an effective interaction graph even without direct messages.};
\draw[blue!25] (0,-4.0)--(16.7,-4.0);
\node[label,font=\sffamily\bfseries] at (0,-4.4) {Organization: how was the policy obtained?};
\node[art,text width=4.65cm,minimum height=1.5cm] (designed) at (2.5,-5.9)
 {\textbf{Designed}\\Human-specified roles, delegation rules, permissions};
\node[art,text width=4.65cm,minimum height=1.5cm] (learned) at (8.4,-5.9)
 {\textbf{Learned}\\Training changes orchestration or collaboration policies};
\node[art,text width=4.65cm,minimum height=1.5cm] (emergent) at (14.2,-5.9)
 {\textbf{Emergent}\\Runtime conventions and divisions of labor arise in traces};
\node[anchor=north west,align=left,text width=16.7cm] at (0,-7.1)
 {The three origins can operate within one system. A shared medium or a hierarchical trace does not, by itself, identify the origin of organization.};
\end{tikzpicture}
\end{document}
'''

def diagrams():
    FIG.mkdir(parents=True, exist_ok=True)
    latex = shutil.which('pdflatex') or '/opt/homebrew/bin/pdflatex'
    for name, tex in [('taxonomy', TAXONOMY), ('coordination-layers', COORDINATION)]:
        (FIG/(name+'.tex')).write_text(tex)
        p=subprocess.run([latex,'-interaction=nonstopmode','-halt-on-error',name+'.tex'],cwd=FIG,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if p.returncode:
            raise RuntimeError(p.stdout[-6000:])
        print('Built paper/figures/'+name+'.pdf')
        for suffix in ['.aux','.log']:
            (FIG/(name+suffix)).unlink(missing_ok=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,help='read-only archived research root; preserve its 52 current figures')
    args=parser.parse_args()
    if args.source:
        preserve(args.source)
    diagrams()

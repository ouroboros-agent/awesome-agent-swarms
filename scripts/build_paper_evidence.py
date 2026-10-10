#!/usr/bin/env python3
"""Render the manually coded evidence matrix; no source discovery or API calls."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'paper/evidence-matrix.json'
OUT = ROOT / 'paper/appendix-evidence.tex'

def esc(s):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '–':'--', '—':'---', '×':r'$\times$', '≈':r'$\approx$', '→':r'$\rightarrow$', '≥':r'$\geq$', '≤':r'$\leq$', '−':'-', 'ρ':r'$\rho$', 'λ':r'$\lambda$', '°':r'\textdegree{}', '“':'``', '”':"''", 'ő':r'\H{o}'}
    return ''.join(replacements.get(c,c) for c in str(s))

def evaluation_text(s):
    s = s.rstrip()
    return s if s.endswith(('.', '!', '?')) else s + '.'

INTRO = r'''
\clearpage
\onecolumn
\section{Evidence coding and comparative records}
\label{app:evidence}

This appendix makes the review's comparisons inspectable. It codes selected evidence units from the research collection's chapters and source cards, plus the two targeted additions described in Section~\ref{sec:methods}, a 30 September and a 2 October preprint. Selection prioritizes comparisons that distinguish mechanisms, studies with unusually large populations, and counterexamples to a simple ``more agents'' explanation. It does not estimate coverage of the literature. The collection's 153 metadata records and 147 source cards are different administrative units, not an audited count of unique publications; some cards group a report, later versions, and commentary. The records below cite their actual sources and should not be added to the inventory to obtain a publication count.

\paragraph{Extraction and provenance.}
The evidence layer is a secondary coding of the collection, not a new screening exercise or a reproduction of experiments. Numerical observations and their qualifications come from the collection's chapters, with detailed cards and metadata used to resolve scale and model fields. The two added belief-dynamics records were coded from notes on the primary papers' methods and results sections. We did not infer a communication graph from a model list, simultaneous population from session counts, or equal spending from an equal limit. The machine-readable companion, \texttt{evidence-matrix.json}, records the source chapter and card locator for each row; the bibliographic citation points to the original work. No independent dual-coder agreement study was performed.

\paragraph{Coding rules.}
\emph{Composition} distinguishes copies of one model within a run from mixtures of models; a study testing several homogeneous teams is not a heterogeneous team. \emph{Graph} describes available or observed communication separately from the \emph{medium} carrying it. A shared repository permits indirect coordination without a complete message graph. \emph{Organization} distinguishes designed infrastructure or roles, learned policies or strategies, and roles that emerge during deployment; multiple labels can apply to the same system. \emph{Memory} describes the state accessible across turns or sessions, not an inferred capacity in tokens. \emph{Concurrent} counts agents maintained within one run (the distinction from simultaneous inference calls is stated where available), \emph{cumulative} counts participants or sessions over time, and \emph{capacity} records an offered or configured ceiling. For sequential role-playing, active inference can be one even when the protocol contains several agents; logical populations and active-call counts are marked explicitly. A simulated population sampled from cached LLM policies is marked separately from live inference.

\paragraph{Missingness and comparison.}
NR means \emph{not reported in the extracted evidence}; it does not prove absence from the complete primary paper. NA means the field is not applicable to that evidence unit. A control can match tasks, model, total work, a token ceiling, actual token use, dollars, or time. These are recorded separately. A source with no single-agent control can establish that an artifact was produced or that a mechanism occurred, but not the causal benefit of using a swarm. Evaluation extent (tasks, trials, seeds, datasets, or calls) is kept separate from cumulative agent identities or sessions; online names and registrations are labeled identity proxies. Outcome measures retain their units and evaluation setting; accuracy, hidden-test pass rate, novelty, utility, vulnerability counts, and attacks detected are not pooled.

\subsection{Reading apparent contradictions}
\label{app:contradictions}

\paragraph{Negative average effects do not exclude conditional gains.}
Kim et al.'s fixed-ceiling comparisons and Tran and Kiela's short-answer tasks test whether communication earns back its overhead under a limited budget. Park et al. instead compare agents that can accumulate externally checkable discoveries with independent searches; on ARC-AGI-3 the advantage arrives only after enough search. The same study's negative Terminal-Bench result prevents generalizing from its strongest games. CORAL's shared history improves a measured optimization objective but consumes more evaluations. These findings motivate a conditional hypothesis about feedback and reuse; they do not establish feedback as a sufficient causal explanation across tasks \citep{kim-scaling-agent-systems,tran-kiela-equal-budget,test-time-communication,coral}.

\paragraph{Equal allowances and equal bills answer different questions.}
Opus 5's BrowseComp comparison gives the ten-agent team and the strongest single-agent condition equal nominal token allowances, yet their realized spending differs. Agensh fixes a six-hour deadline while adding workers gradually. Its larger system therefore demonstrates a benefit under a deadline without identifying a benefit per token. Conversely, the small-team curves reported for Opus 5.5 support faster attainment of a target score with extra tokens, not a universal upper bound on collective quality. A single fitted exponent from the GPT-5.6 curves is restricted to that model, orchestration method, task, and tested range \citep{opus5-card-multiagent,agensh-1024,opus55-card,ord-swarm-scaling}.

\paragraph{Organization has two timescales.}
The emergence of integrators in Agensh occurs inside an engineered loop with claims, checks, typed notes, reminders, and version control. SAT learns discussion strategies before test-time deployment and freezes them, while allowing task-specific division of labor to change during a discussion. Kimi learns the coordinator's policy with fixed workers. Cursor's hierarchy was redesigned by engineers after failures. These are different interventions. Their common result is that agents can operate under several forms of organization; the evidence does not rank spontaneous, learned, and designed organization under one matched large-scale protocol \citep{agensh-1024,sat-teams,kimi-agent-swarm,cursor-scaling-long-running,cursor-self-driving}.

\paragraph{External memory solves access before it solves integration.}
RLM provides an essential control: a single program-writing root can process text outside its context window without a concurrently interacting population. HiddenBench and Silo-Bench show a separate difficulty: agents may possess the required facts collectively yet fail to request or assemble them. The enzyme campaign records another boundary: a shared knowledge base carried results between sessions, but the decisive observation required one worker to inspect raw sequence data, and ten reruns missed it. Storage, retrieval, factual integration, and discovery therefore need separate tests; none is a proxy for unlimited memory \citep{recursive-language-models,hiddenbench,silo-bench,anthropic-art-enzymes}.

\paragraph{Diversity is a resource that the protocol can spend.}
Diversity Scaling and Deliberative Crowds find gains from heterogeneous starting judgments relative to homogeneous or independent conditions. Interaction Tax reports that sharing entire solutions can remove that diversity after one exchange. SAT's homogeneous control also executes strategies learned for a heterogeneous composition, so it does not isolate composition from policy fit. Artificial Hivemind measures similarity of independent texts; the reassessment disputes the inference from embedding similarity to a small number of ideas. None of these measurements alone establishes that a mixed swarm will outperform its strongest member \citep{diversity-scaling,deliberative-crowds,interaction-tax,sat-teams,artificial-hivemind}.

\paragraph{Agreement can be coordination, an error, or a measurement artifact.}
Naming games reward matching; flag identification rewards a correct answer; open-ended conversations have no externally correct endpoint. Consensus across these settings has different meanings. Large naming-game populations sometimes use cached policies, whereas the Flag Game executes live model calls and varies the network. Bayesian decompositions of paired opinion exchange also attribute much convergence to topic-specific model priors. Methodological audits show that the prompt can reveal the intended social experiment or change behavior through formatting. A claimed phase transition must therefore specify the update rule, sampled policy, temperature, exposure, and finite population \citep{prev-flint-group-size,flag-game,brockers-opinion-dynamics,pimmur-principles,prev-robustness-audits}.

\paragraph{Capability, propensity, and observability are separate safety outcomes.}
SCHEME explicitly asks agents to pursue a hidden objective; Colosseum varies whether a private channel is available; Shutdown Sabotage changes what a deletion script is said to target; Peer Preservation often supplies a textual colleague rather than a live second agent. These designs test different claims. Likewise, a transcript monitor's failure to recognize a coalition does not imply that its action-level benefit is absent, and successful detection in a scripted benchmark does not estimate attack frequency in deployment. In the Lean conference, warnings existed but lacked an enforcement path: more detection alone could not invalidate accepted artifacts \citep{schemes-coordinated-sabotage,colosseum,shutdown-sabotage,peer-preservation,deepmind-cheating-whistleblowing}.

\paragraph{Large online populations need an identity model.}
The wiki studies count edits, names, and reconstructed sessions differently. The incident reports count cumulative board participants and actions, not a concurrent swarm. Moltbook registrations are neither active agents nor independent autonomous principals; multiple accounts can share a human operator, and response coverage dominates the Superminds result. EinsteinArena shows reuse of validated artifacts but includes human steering and lacks a matched independent-search control. These observations establish mechanisms in deployed environments while leaving causal effects of population size unresolved \citep{wiki-copying,lutje-mechanics-of-a-swarm,hf-openai-technical-report,hf-metr-redwood-investigation,moltbook-illusion,superminds-test,einsteinarena}.

\subsection{Record layout}
Each row contains the model composition, communication graph and medium, organization, memory, three scale meanings, control, resource basis, evaluation extent where available, outcome, and the main limit on interpretation. ``Fixed'' refers only to the explicitly named quantity. Reported approximate values remain approximate. Where a study contains distinct experiments, the row identifies their scope instead of manufacturing one average scale or outcome.
'''

FOOT = r'''
\section{Reporting gaps and discriminating comparisons}
\label{app:gaps}

The matrix identifies recurrent gaps, not a checklist that every source was intended to satisfy. Engineering reports often provide a successful artifact and an elapsed time but omit unsuccessful runs, a long single-agent control, or realized spending. Short-answer experiments report precise outcomes but often use small populations and limited horizons. Social simulations can vary population size extensively while leaving model snapshots, prompt sensitivity, or the distinction between live and cached updates underdescribed. Field studies provide richer histories but weak identity resolution and few interventions.

A useful next comparison would report the same task under independent sampling, a persistent single agent with external memory, a designed team, and a team allowed to organize its own work. The shared constraints should include the model checkpoint, tool access, actual token accounting, action budget, and evaluation procedure. Wall-clock time should be an outcome as well as an optional deadline. The study should retain failed and cancelled runs, quantify uncertainty across tasks and seeds, and record the communication and artifact graph over time. This is a proposed protocol, not an experiment conducted for this report.

Memory requires its own evaluation: control corpus size and information distribution, then vary writers, readers, retrieval policy, update conflicts, and retention horizon. Measure recovery of relevant facts, contradictions, provenance, latency, and final task performance separately. A shared note store that improves a reader's score at one population size does not establish a scaling law for retained knowledge. A population of sessions should also be audited for repeated identities, overlapping context, and duplicate discoveries before a numerical ``swarm size'' is assigned.

For collective safety, evaluation should distinguish an externally instructed attack, spontaneous policy deviation under a neutral task, and compliance with a malicious message. A factorial intervention can vary live peers, stored peer messages, memory persistence, incentives, and enforcement independently. Monitors need both transcript-level and system-level views, with false-positive rates and action consequences reported. Heterogeneous monitoring is a testable design choice, not a guarantee of independence: shared training data, tools, and incentives can still correlate failures.

The present synthesis supplies an inspectable coding layer and conditional questions. It does not supply a causal estimate of the benefit of scale, a universal superiority ordering of topologies, an exhaustive census, or a new experimental result.
'''


INVENTORY_INTRO = r"""
\clearpage
\section{Complete analytical inventory}
\label{app:inventory}

The following table lists all 153 administrative records in the collection's analytical inventory. It is separate from the selected, manually coded evidence matrix in Appendix~\ref{app:evidence}. A row may describe a publication, a developer evaluation, an incident, or a bundle of related documents. It is not a deduplicated bibliography, a claim of exhaustive literature coverage, or a claim that all 153 records have been coded along every taxonomy dimension. The snapshot predates the two targeted additions and later publication-status updates. Component citations resolve bundles to actual documents rather than an invented aggregate publication; not every subsidiary link in a grouped card has its own bibliography entry.

The snapshot is preserved unchanged in \texttt{corpus-inventory.json}, including complete model lists, topic tags, source-class annotations, and original scale notes. The table shows its model-family, evidence, and scale fields. \textbf{N} is the snapshot's maximum within-run population field; it can mean a logical population rather than simultaneous inference calls. \textbf{Total} is cumulative and may count sessions, accounts, names, or participants. \textbf{Cap} is a configured or advertised ceiling; registration totals are labeled explicitly. Where the snapshot's own scale note shows that a value is a peak within a time bin, an interview estimate, a supplementary condition, a reproduction inside a literature audit, or platform-wide activity, a bracketed qualifier taken from that note follows the unchanged value. NR means the snapshot has no value. For surrogate simulations, N counts simulated population states. These fields are not fresh primary-source verification; the manually coded records provide finer qualifications where available.

\begingroup
\fontsize{9}{10.5}\selectfont
\setlength{\tabcolsep}{4pt}
\renewcommand{\arraystretch}{1.05}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.47\textwidth}>{\raggedright\arraybackslash}p{0.14\textwidth}>{\raggedright\arraybackslash}p{0.35\textwidth}@{}}
\toprule
Record and source & Evidence class & Model families and scale semantics \\
\midrule
\endfirsthead
\toprule
Record and source & Evidence class & Model families and scale semantics \\
\midrule
\endhead
\midrule
\multicolumn{3}{r}{Continued on next page}\\
\endfoot
\bottomrule
\endlastfoot
"""


# English renderings of the snapshot's own scale_note_ru for rows whose bare value
# is not a within-run concurrent count. The raw values above are not changed.
SCALE_QUALIFIERS = {
    'agensh-1024': 'peak active identities in one 37.5-second interval',
    'cursor-scaling': 'approximate peak across machines from an interview; the flat self-coordination test used 20',
    'colosseum': 'team in the Jira example; the coalition has 2 agents',
    'physics-of-agents': 'one supplementary mixed community; main-experiment communities have 32',
    'pimmur-principles': 'largest reproduction; the main study is a literature audit, not one swarm',
    'anthropic-art-enzymes': 'limit of 58 concurrent sessions; observed peak not reported',
    'anthropic-institute-pace': 'approximate, at one time, across different tasks on one internal platform',
    'openai-navier-stokes': 'order of magnitude',
}


def render_inventory():
    inventory = json.loads((ROOT / 'paper/corpus-inventory.json').read_text())
    mapping = json.loads((ROOT / 'paper/citation-key-map.json').read_text())
    entries = mapping['entries']
    replacements = mapping['draft_citation_replacements']
    if len(inventory) != 153 or len({r['id'] for r in inventory}) != 153:
        raise ValueError('Inherited inventory must contain its original 153 record IDs')
    bundle_titles = {
        'attractor-states': 'Attractor studies: open-ended self-interactions and paired debates',
        'cursor-scaling': 'Cursor: scaling long-running coding and self-driving codebases',
        'hf-incident-case': 'OpenAI / Hugging Face incident: developer, investigator, and victim reports',
        'ai-village': 'AI Village: operator account and longitudinal observation',
        'cognition-multi-agents': 'Cognition: multi-agent engineering guidance and follow-up',
        'sakana-conductor-trinity-fugu': 'Sakana: Conductor, TRINITY, and Fugu',
        'artificial-hivemind': 'Artificial Hivemind and its reassessment',
        'anthropic-multi-agent-guidance': 'Anthropic: multi-agent research-system engineering guidance',
        'opus46-launch-cluster': 'Claude Opus 4.6: launch, long-context, and multi-agent evaluations',
    }
    evidence_labels = {'benchmark':'Benchmark', 'engineering_report':'Engineering report', 'field_observation':'Field observation', 'incident':'Incident', 'live_experiment':'Live experiment', 'surrogate_simulation':'Surrogate simulation', 'system_card_eval':'System-card evaluation', 'theory_essay':'Theory / essay'}
    total_units = {'wiki-copying':'names', 'hf-incident-case':'board participants', 'agora-git-memory':'accounts/sessions', 'ai-village':'names', 'aisi-incident-july-2026':'runs', 'anthropic-project-swap':'participants', 'collusion-wiki':'names', 'commerce-misaligned-communication':'agent-runs', 'cursor-swarm-economics':'file editors', 'emergence-world':'agents across worlds', 'lai-looking-for-something-weird':'accounts across snapshots', 'lutje-mechanics-of-a-swarm':'estimated episodes', 'moltbook-illusion':'authors', 'moltbook-socialization':'post authors', 'riemann-zeta-swarm':'short-lived agents', 'swarmtraces':'self-chosen names', 'zhang-agents-in-the-wild':'accounts', 'anthropic-art-enzymes':'sessions', 'agensh-1024':'participants'}
    result=[INVENTORY_INTRO]
    seen=[]
    for index, record in enumerate(inventory, 1):
        rid=record['id']
        default_key=replacements.get(rid,rid)
        components=[k for k,v in entries.items() if v.get('part_of')==rid]
        keys=list(dict.fromkeys(([default_key] if default_key in entries else [])+components))
        if not keys:
            raise ValueError('Missing inventory citation: '+rid)
        is_bundle=rid in bundle_titles
        title=bundle_titles.get(rid, entries[default_key]['title'])
        # Titles are metadata text, not LaTeX. Removing escaped markup here does
        # not change the preserved snapshot or the bibliography title.
        title=title.replace('\\&','&').replace('\\_','_')
        a=esc(str(index)+'. '+title)
        if is_bundle:a+=r' \emph{(source bundle)}'
        a+=r' \citep{'+','.join(keys)+'}'
        b=esc(evidence_labels[record['evidence']])
        families=', '.join(record['model_families']) or 'NR'
        scale_kind=record['scale_kind']
        n=record['agents_max_simultaneous'];total=record['agents_total']
        fmt=lambda v: f'{v:,}' if isinstance(v,int) else str(v)
        if rid in {'superminds-test','wiz-moltbook'}:
            scale='Registrations: '+fmt(total)+' (platform figure); concurrent N: NR.'
        elif scale_kind=='capacity':
            value=n if n is not None else total
            scale='Cap: '+(fmt(value) if value is not None else 'NR')+'; observed N: NR.'
        elif scale_kind=='cumulative_only':
            scale='Total: '+(fmt(total) if total is not None else 'NR')+' '+total_units.get(rid,'(unit in raw notes)')+'; N: NR.'
        elif scale_kind=='none':
            scale='N and total: NR; no scale assigned.'
        else:
            scale='N: '+(fmt(n) if n is not None else 'NR')
            if rid in SCALE_QUALIFIERS:scale+=' ['+SCALE_QUALIFIERS[rid]+']'
            scale+='.'
            if total is not None:scale+=' Total: '+fmt(total)+' '+total_units.get(rid,'(unit in raw notes)')+'.'
            if record['evidence']=='surrogate_simulation':scale+=' N is a surrogate population.'
        if rid=='llm-agent-swarm-optimization':
            scale='N: 100 in Schelling simulation; LLM optimization uses 20.'
        elif rid=='emergence-world':
            scale='N: 13 including system roles. Total: 80 citizen and 24 system agents across worlds.'
        if rid in SCALE_QUALIFIERS and '['+SCALE_QUALIFIERS[rid]+']' not in scale:
            scale=scale.rstrip('.')+' ['+SCALE_QUALIFIERS[rid]+'].'
        c=esc(families)+r'\par '+esc(scale)
        result.append('% Inventory record: '+rid+'\n'+a+' & '+b+' & '+c+r' \\ \addlinespace[2pt]'+'\n')
        seen.append(rid)
    if set(seen)!={r['id'] for r in inventory} or len(seen)!=153:
        raise ValueError('Inventory render omitted or duplicated a record')
    result.append('\\end{longtable}\n\\endgroup\n')
    return ''.join(result)

def render():
    d=json.loads(DATA.read_text())
    rows=d['records']
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Repeated evidence-unit identifier')
    required=['models','composition','graph','exchange','organization','memory','baseline','matching','budget','outcome','limits','provenance']
    for r in rows:
        for key in required:
            if not r.get(key): raise ValueError(f"Missing {key}: {r['id']}")
        if set(r['scale']) != {'concurrent','cumulative','capacity'}: raise ValueError(r['id'])
        if re.search(r'\b(configurations?|trials?|tasks?|probes?|seeds?|replicates?|calls?|simulations?|papers?|steps?|transitions?|attempts?|runs?|datasets?|answers?|edits?)\b', r['scale']['cumulative'], re.I):
            raise ValueError('Evaluation extent placed in cumulative-agent scale: '+r['id'])
    parts=['% Generated by scripts/build_paper_evidence.py; edit evidence-matrix.json for records.\n',INTRO]
    for domain in dict.fromkeys(r['domain'] for r in rows):
        if domain in {'Field observations and identity', 'Methodological controls'}:
            parts.append('\n\\clearpage\n')
        # Reserve the heading, longtable header and a substantial first evidence row.
        parts.append('\n\\Needspace{20\\baselineskip}\n\\subsection{'+esc(domain)+'}\n')
        parts.append(r'''\begingroup
\small
\setlength{\tabcolsep}{5pt}
\renewcommand{\arraystretch}{1.13}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.16\textwidth}>{\raggedright\arraybackslash}p{0.395\textwidth}>{\raggedright\arraybackslash}p{0.40\textwidth}@{}}
\toprule
Evidence unit & Composition, interaction, organization, memory & Scale, comparison, and outcome \\
\midrule
\endfirsthead
\toprule
Evidence unit & Composition, interaction, organization, memory & Scale, comparison, and outcome \\
\midrule
\endhead
\midrule
\multicolumn{3}{r}{Continued on next page}\\
\endfoot
\bottomrule
\endlastfoot
''')
        domain_rows=[record for record in rows if record['domain'] == domain]
        for position, r in enumerate(domain_rows, 1):
            cite=r'\citep{'+','.join(r['citation_keys'])+'}'
            a=r'\textbf{'+esc(r['label'])+r'}\par '+cite+r'\par '+esc(r['source_class'])
            b=' '.join(r'\textbf{'+label+'} '+esc(r[field]) for label,field in [('Models.','models'),('Composition.','composition'),('Graph.','graph'),('Medium.','exchange'),('Organization.','organization'),('Memory.','memory')])
            evidence_fields=[('Control.','baseline'),('Matched.','matching'),('Resources.','budget')]
            if r.get('evaluation_extent'):
                evidence_fields.append(('Evaluation.','evaluation_extent'))
            evidence_fields.extend([('Outcome.','outcome'),('Limit.','limits')])
            c=r'\textbf{Scale.} '+esc('Concurrent: '+r['scale']['concurrent']+'; cumulative: '+r['scale']['cumulative']+'; capacity: '+r['scale']['capacity']+'.')+' '+ ' '.join(r'\textbf{'+label+'} '+esc(evaluation_text(r[field]) if field == 'evaluation_extent' else r[field]) for label,field in evidence_fields)
            # No spacer after a table's last row: it can strand the closing rule on its own page.
            spacer=r' \addlinespace[5pt]' if position < len(domain_rows) else ''
            parts.append('% Evidence unit: '+r['id']+'\n'+a+' & '+b+' & '+c+r' \\'+spacer+'\n')
        parts.append('\\end{longtable}\n\\endgroup\n')
    parts.append(FOOT)
    parts.append(render_inventory())
    rendered = ''.join(parts)
    expected = {r['id'] for r in rows}
    actual = [line[len('% Evidence unit: '):] for line in rendered.splitlines() if line.startswith('% Evidence unit: ')]
    if len(actual) != len(rows) or set(actual) != expected:
        raise ValueError('Rendered evidence records do not match the matrix exactly once')
    OUT.write_text(rendered)
    print(f'Rendered {len(rows)} selected evidence units to {OUT.relative_to(ROOT)}')

if __name__=='__main__': render()

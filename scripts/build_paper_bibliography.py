#!/usr/bin/env python3
"""Regenerate the bibliography from the preserved October cards (read-only).

This is an editorial conversion, not a metadata discovery or deduplication tool.
The checked-in .bib is sufficient to compile the report without the archive.
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path('research-archive')


def tex(text):
    replacements = {'&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#',
                    '$': r'\$', '–': '--', '—': '---', '’': "'", '‘': "'",
                    '“': '``', '”': "''", '…': '...', '×': r'$\times$',
                    '≠': r'$\ne$', 'λ': r'$\lambda$', '§': r'\S{}',
                    'ı': r'{\i}', 'ł': r'{\l}', 'Ł': r'{\L}',
                    'ø': r'{\o}', 'Ø': r'{\O}', 'ß': r'{\ss}',
                    'æ': r'{\ae}', 'œ': r'{\oe}'}
    accents = {'\u0301': "'", '\u0300': '`', '\u0302': '^', '\u0308': '"',
               '\u0303': '~', '\u0327': 'c', '\u030c': 'v', '\u0306': 'u',
               '\u030a': 'r', '\u0304': '='}
    out = ''
    for c in str(text):
        if c in replacements:
            out += replacements[c]
        elif ord(c) > 127:
            ds = unicodedata.normalize('NFD', c)
            if len(ds) == 2 and ds[1] in accents:
                out += '{\\' + accents[ds[1]] + '{' + ds[0] + '}}'
            elif c.isspace():
                out += ' '
            else:
                out += c
        else:
            out += c
    return out


CORPORATE = {'Anthropic', 'OpenAI', 'xAI', 'Kimi Team', 'Sakana AI',
             'UK AI Security Institute', 'Anthropic Frontier Red Team',
             'Anthropic Threat Intelligence', 'The Antigravity Team',
             'The Cognition Team', 'METR', 'Meta Superintelligence Labs',
             'Cursor Research', 'AI Village and Grove Research'}


# BibTeX reads a capitalized surname particle as part of the given name, which
# yields labels such as "Marzo et al."; give these recorded names in Last, First form.
SURNAME_PARTICLES = {'Giordano De Marzo': 'De Marzo, Giordano',
                     'Sydney Von Arx': 'Von Arx, Sydney',
                     'Cristiano De Nobili': 'De Nobili, Cristiano',
                     'Manlio De Domenico': 'De Domenico, Manlio'}


def clean_author(a):
    a = re.sub(r'\s*\([^)]*\)', '', a).strip()
    return a


def authors(d):
    raw = d.get('authors')
    incomplete = False
    if not raw:
        a = d.get('authors_short', '')
        n = re.search(r'(\d+)\s*(?:authors|автор|имён)', a)
        n = int(n.group(1)) if n else None
        a = re.split(r'\(|et al\.|и др\.|\+\d', a)[0].strip(' ,;')
        raw = a.split(', ')
        incomplete = bool(n and n > len(raw)) or bool(re.search(r'et al\.|и др\.|\+\d', d.get('authors_short', '')))
    result = []
    for a in raw:
        if re.match(r'et al\.', a):
            extra = re.search(r'\((?:also |7th: )(.+)\)', a)
            if extra:
                result.extend(x.strip() for x in extra.group(1).split(','))
            else:
                incomplete = True
        else:
            result.append(clean_author(a))
    n = d.get('n_authors')
    if isinstance(n, int) and n > len(result):
        incomplete = True
    result = [a for a in result if a]
    if incomplete:
        result.append('others')
    return result, incomplete


def source_url(d):
    value = d.get('url') or d.get('urls', {}).get('primary') or ''
    m = re.search(r'https?://[^\s<>]+', value)
    return m.group(0).rstrip('.,;)') if m else ''


def ordinary_record(key, d):
    a, partial = authors(d)
    date = str(d.get('date_first_public', ''))
    year = re.search(r'20\d\d', date)
    u = source_url(d)
    rec = {'entrytype': 'misc', 'author': a, 'title': d['title'],
           'year': year.group(0) if year else 'n.d.', 'url': u}
    arx = re.search(r'arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(v\d+)?', u)
    status = str(d.get('venue_status', d.get('status', d.get('type', ''))))
    if arx:
        rec.update(archivePrefix='arXiv', eprint=arx.group(1))
        rec['howpublished'] = 'arXiv preprint'
    elif 'system card' in d.get('title', '').lower():
        rec['howpublished'] = 'System card'
    elif 'doi.org/' in u:
        rec['doi'] = u.split('doi.org/', 1)[1]
    elif 'blog' in u or 'lesswrong.com' in u or 'substack.com' in u:
        rec['howpublished'] = 'Online article'
    if partial:
        rec['_partial_authors'] = True
    rec['_inherited_status'] = status
    return rec


def extra(title, author, year, url, **kw):
    return dict(entrytype='misc', title=title, author=author, year=str(year), url=url, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', type=Path, default=DEFAULT_ARCHIVE)
    args = ap.parse_args()
    records, provenance, raw = {}, {}, {}
    for folder in ['cards_c', 'cards_b', 'cards', 'cards_lanes']:
        for p in sorted((args.archive / folder).glob('*.json')):
            if '.pre_' in p.name:
                continue
            d = json.loads(p.read_text())
            key = p.stem
            raw[key] = d
            if key.startswith('prev-') and key.endswith('-cluster'):
                continue
            records[key] = ordinary_record(key, d)
            provenance[key] = {'source_card': str(p.relative_to(args.archive)),
                               'source_id': d['id'],
                               'source_sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def update(k, **kw):
        records[k].update(kw)
        records[k]['_editorial_normalization'] = True

    def add(k, source, **kw):
        records[k] = kw
        provenance[k] = {'source_card': source, 'editorial_component': True}

    # Bundle cards are split into citable documents; names are not merged across works.
    update('attractor-states', title='Models have some pretty funny attractor states',
           author=['Arya Jakkli', 'Senthooran Rajamanoharan', 'Neel Nanda'], year='2026',
           howpublished='LessWrong post')
    add('ko-geiping-attractors', 'cards/attractor-states.json',
        **extra('Attractor States Emerge in Multi-Turn LLM Conversations',
                ['Ting-Wen Ko', 'Jonas Geiping'], 2026, 'https://arxiv.org/abs/2606.30571',
                archivePrefix='arXiv', eprint='2606.30571', howpublished='arXiv preprint'))
    add('opus4-bliss-attractor', 'cards/attractor-states.json',
        **extra('System Card: Claude Opus 4 and Claude Sonnet 4', ['Anthropic'],
                2025, 'https://www.anthropic.com/claude-4-system-card', howpublished='System card'))
    update('cursor-scaling', title='Scaling long-running autonomous coding', year='2026')
    add('cursor-self-driving', 'cards/cursor-scaling.json',
        **extra('Towards self-driving codebases', ['Wilson Lin'], 2026,
                'https://cursor.com/blog/self-driving-codebases', howpublished='Cursor research blog'))
    update('ai-village', title='How the AI Village works', author=['Adam Binksmith'], year='2026')
    add('ai-village-longitudinal', 'cards_b/ai-village.json',
        **extra('Norms, Tools, and the Say/Do Gap: Seventeen Months of Autonomous Frontier-Model Agents in the AI Village',
                ['{Claude Fable 5.1}'], 2026, 'https://doi.org/10.5281/zenodo.23090815',
                doi='10.5281/zenodo.23090815', note='Agent-authored working paper, version 0.25'))
    update('cognition-multi-agents', title="Don't Build Multi-Agents", year='2025')
    add('cognition-multi-agents-working', 'cards_b/cognition-multi-agents.json',
        **extra("Multi-Agents: What's Actually Working", ['Walden Yan'], 2026,
                'https://cognition.com/blog/multi-agents-working', howpublished='Cognition engineering blog'))
    update('anthropic-multi-agent-guidance', title='How we built our multi-agent research system',
           author=['Jeremy Hadfield', 'Barry Zhang', 'Kenneth Lien', 'Florian Scholz', 'Jeremy Fox', 'Daniel Ford'], year='2025')
    update('anthropic-art-enzymes', title='Autonomous AI agents discover reverse transcriptases with tandem repeat arrays',
           url=raw['anthropic-art-enzymes']['urls']['pdf'], howpublished='Anthropic technical report')
    update('kim-scaling-agent-systems', title='Capable language models can outgrow the benefits of collaboration',
           entrytype='article', year='2026', journal='Nature Machine Intelligence', volume='8', number='7', pages='1157--1172',
           doi='10.1038/s42256-026-01268-y')
    update('kimi-agent-swarm', title='Kimi K2.5: Visual Agentic Intelligence', author=['Kimi Team'])
    update('kimi-k3-swarm-bench', author=['Kimi Team'])
    update('sakana-conductor-trinity-fugu', title='Sakana Fugu Technical Report', author=['Sakana AI'], year='2026')
    add('sakana-conductor', 'cards_b/sakana-conductor-trinity-fugu.json',
        **extra('Learning to Orchestrate Agents in Natural Language with the Conductor',
                ['Stefan Nielsen', 'Edoardo Cetin', 'Peter Schwendeman', 'Qi Sun', 'Jinglue Xu', 'Yujin Tang'],
                2026, 'https://openreview.net/forum?id=U23A2BUKYt', howpublished='ICLR 2026'))
    add('sakana-trinity', 'cards_b/sakana-conductor-trinity-fugu.json',
        **extra('Trinity: An Evolved LLM Coordinator',
                ['Jinglue Xu', 'Qi Sun', 'Peter Schwendeman', 'Stefan Nielsen', 'Edoardo Cetin', 'Yujin Tang'],
                2026, 'https://openreview.net/forum?id=5HaRjXai12', howpublished='ICLR 2026'))
    for k, title in {
        'mythos-preview-self-interactions': 'System Card: Claude Mythos Preview',
        'opus5-card-multiagent': 'System Card: Claude Opus 5',
        'opus55-card': 'System Card: Claude Opus 5.5',
        'fable51-card-multiagent': 'System Card: Claude Fable 5.1 and Claude Mythos 5.1',
        'opus46-launch-cluster': 'Claude Opus 4.6',
        'crypto-weaknesses': 'Discovering cryptographic weaknesses with Claude',
        'riemann-zeta-swarm': "Learning more about Claude's mathematical capabilities",
        'fermat-last-theorem': "Formalizing Fermat's Last Theorem",
    }.items():
        update(k, title=title, author=['Anthropic'])
    update('opus46-launch-cluster',howpublished='Anthropic launch post')
    update('gpt6-astra-card-a2a', title='GPT-6 Astra System Card')
    update('aisi-incident-july-2026', title='Incident Report: unsanctioned agent behaviour during cyber testing',
           author=['UK AI Security Institute'])
    update('hf-incident-case', title='OpenAI--Hugging Face Incident: Technical Report', author=['OpenAI'],
           url=raw['hf-incident-case']['urls']['pdf'], year='2026', howpublished='Technical report')
    add('hf-metr-investigation', 'cards_lanes/hf-incident-case.json',
        **extra('OpenAI Hugging Face Incident Investigation', ['Ryan Greenblatt', 'Ajeya Cotra', 'Hjalmar Wijk'],
                2026, 'https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/',
                howpublished='METR and Redwood Research investigation'))
    add('hf-technical-timeline', 'cards_lanes/hf-incident-case.json',
        **extra('Agent Intrusion: Technical Timeline', ['Hugo Larcher', 'Adrien Carreira', '{raphael g}', 'Christophe Rannou'],
                2026, 'https://huggingface.co/blog/agent-intrusion-technical-timeline', howpublished='Hugging Face incident report'))
    # Publication update to an existing work, checked at the publisher on 2026-10-09.
    add('piao-polarization', 'cards_c/prev-population-dynamics-cluster.json',
        **dict(entrytype='article', title='Emergence of polarization in networks of large language model agents',
               author=['Jinghua Piao', 'Zhihong Lu', 'Chen Gao', 'Fengli Xu', 'Qinghua Hu', 'Fernando P. Santos', 'Yong Li', 'James Evans'],
               year='2026', journal='Nature Communications', doi='10.1038/s41467-026-78228-y',
               url='https://www.nature.com/articles/s41467-026-78228-y',
               note='Published online 8 October 2026. Article in press; earlier preprint arXiv:2501.05171'))
    provenance['piao-polarization']['primary_update'] = 'https://www.nature.com/articles/s41467-026-78228-y'
    provenance['piao-polarization']['prior_arxiv_id'] = '2501.05171'
    # Corporate and short-card bylines: retain only actual recorded names.
    for k,a in {
        'ai-swarm-dynamics-hackathon':['AI Village and Grove Research'],
        'composer-2':['Cursor Research'], 'devin-fusion':['The Cognition Team'],
        'muse-spark':['Meta Superintelligence Labs'], 'effective-context-engineering':['Anthropic'],
        'eval-awareness-browsecomp':['Russell Coleman','others'],
        'claude-code-auto-mode-handoffs':['John Hughes','others'],
        'dwarkesh-agent-civilizations':['Dwarkesh Patel'],
        'ng-hao-peer-preservation-replication':['Yi Mei (Vanessa) Ng','Yixiong Hao'],
    }.items(): update(k,author=a)
    update('hiddenbench',title='Systematic Failures in Collective Reasoning under Distributed Information in Multi-Agent LLMs')
    update('sakana-ab-mcts',title='Wider or Deeper? Scaling LLM Inference-Time Compute with Adaptive Branching Tree Search')
    update('muse-spark',title="Introducing Muse Spark: Meta's Most Powerful Model Yet")
    update('science-agents-go-rogue',title="AI 'agents' go rogue in realistic simulations")
    update('openai-misalignment-reports',title='Misalignment reports')
    for k,fields in {
        'brockers-opinion-dynamics':dict(journal='Nature Communications',volume='17',pages='10077'),
        'co-scientist-nature':dict(journal='Nature',volume='655',number='8122',pages='487--496'),
        'evans-agentic-intelligence-explosion':dict(journal='Science',volume='391',number='6791',pages='eaeg1895',note='Editorial'),
        'llm-agent-swarm-optimization':dict(journal='npj Artificial Intelligence',volume='2',pages='36'),
        'nature-subliminal-learning':dict(journal='Nature',volume='652',number='8110',pages='615--621',doi='10.1038/s41586-026-10319-8'),
        'prev-demarzo-majority':dict(journal='Science Advances',volume='12',number='33',pages='eaea6091'),
        'prev-flint-group-size':dict(journal='Proceedings of the National Academy of Sciences',volume='123',number='34',pages='e2531697123'),
        'robin-futurehouse':dict(title='A multi-agent system for automating scientific discovery',
                               journal='Nature',volume='655',number='8122',pages='497--505'),
        'science-malicious-swarms':dict(journal='Science',volume='391',number='6783',pages='354--357',note='Policy Forum'),
        'science-invent-own-language':dict(journal='Science',volume='393',number='6818',pages='1286--1287',note='News article'),
    }.items():
        update(k,entrytype='article',year='2026',**fields)

    # Additional component records use only metadata explicitly preserved in the cards.
    components = [
        ('tanaka-memetic-drift','When Is Collective Intelligence a Lottery? Multi-Agent Scaling Laws for Memetic Drift in LLMs',['Hidenori Tanaka'],2026,'2603.24676','prev-population-dynamics-cluster'),
        ('naming-games','Microscopic dynamics of consensus formation in multi-agent LLM Naming Games',['De Nobili','Iyer','Codello','Burioni'],2026,'2608.02178','prev-population-dynamics-cluster'),
        ('structured-opinion-dynamics','Collective Opinion Dynamics in Structured LLM Populations',['Cau','Failla','Rossetti'],2026,'2604.11312','prev-population-dynamics-cluster'),
        ('attributing-emergence','Attributing Emergence in Million-Agent Systems',['Tang','Mei','Chen','others'],2026,'2605.11404','prev-population-dynamics-cluster'),
        ('conformity-no-speaker','Most LLM Conformity Needs No Speaker',['Hu','Qu'],2026,'2607.05545','prev-population-dynamics-cluster'),
        ('human-ai-consensus','AI agents reshape consensus formation in human groups',['Chen','Liu','Hu','others'],2026,'2609.02122','prev-population-dynamics-cluster'),
        ('zombie-agents','Zombie Agents: Persistent Control of Self-Evolving LLM Agents via Self-Reinforcing Injections',['Xianglin Yang','Yufei He','Shuo Ji','Hooi','Dong'],2026,'2602.15654','prev-contagion-cluster'),
        ('agentworm','AgentWorm: Self-Propagating Attacks Across LLM Agent Ecosystems',['Yihao Zhang','Zeming Wei','Xiaokun Luan','others'],2026,'2603.15727','prev-contagion-cluster'),
        ('multi-agent-security-tax','Multi-Agent Security Tax',['Pierre Peigné','Mikolaj Kniejski','Filip Sondej','others'],2025,'2502.19145','prev-contagion-cluster'),
        ('topological-collapse','Topological collapse of higher-order interactions bottlenecks collective intelligence in AI agent societies',['Lu Shuo','Meng Weicheng','Yu Aijing','others'],2026,'2608.15519','prev-moltbook-cluster'),
        ('moltbook-form-without-function','Form Without Function: Agent Social Behavior in the Moltbook Network',['Zerhoudi','Ghosh Dastidar','Klement','others'],2026,'2604.13052','prev-moltbook-cluster'),
        ('openclaw-norms','OpenClaw Agents on Moltbook: Risky Instruction Sharing and Norm Enforcement in an Agent-Only Social Network',['Manik','Wang'],2026,'2602.02625','prev-moltbook-cluster'),
        ('emergent-languages','Emergent Languages in Populations of Language Model Agents: From Token Efficiency to Oversight Evasion',['Beltoft','Brach','Torrielli','others'],2026,'2605.31170','prev-moltbook-cluster'),
        ('moltbook-observatory','The Moltbook Observatory Archive',['Gautam','Olstad','Pettersen','others'],2026,'2605.13860','prev-moltbook-cluster'),
    ]
    for k,title,a,y,arx,source in components:
        add(k,'cards_c/'+source+'.json',**extra(title,a,y,'https://arxiv.org/abs/'+arx,
             eprint=arx,archivePrefix='arXiv',howpublished='arXiv preprint'))
        records[k]['_partial_authors']=any(len(x.split())==1 for x in a)
    add('ashery-conventions','cards_c/prev-population-dynamics-cluster.json',
        **dict(entrytype='article',title='Emergent social conventions and collective bias in LLM populations',
               author=['Ashery','Aiello','Baronchelli'],year='2025',journal='Science Advances',
               doi='10.1126/sciadv.adu9368',url='https://doi.org/10.1126/sciadv.adu9368',_partial_authors=True))
    add('gasim','cards_c/prev-moltbook-cluster.json',
        **dict(entrytype='inproceedings',title='GASim: A Graph-Accelerated Hybrid Framework for Social Simulation',
               author=['Xuan Zhou','Yanhui Sun','Hantao Yao','Allen He','Yongdong Zhang','Wu Liu'],year='2026',
               booktitle='Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)',
               pages='12510--12528',doi='10.18653/v1/2026.acl-long.569',url='https://aclanthology.org/2026.acl-long.569/'))
    add('agentsociety','cards_c/prev-moltbook-cluster.json',
        **dict(entrytype='inproceedings',title='A Parallelized Framework for Simulating Large-Scale LLM Agents with Realistic Environments and Interactions',
               author=['Jun Zhang','Yuwei Yan','Junbo Yan','Zhiheng Zheng','Jinghua Piao','Depeng Jin','Yong Li'],year='2025',
               booktitle='Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 6: Industry Track)',pages='1339--1349',
               url='https://aclanthology.org/2025.acl-industry.94/',doi='10.18653/v1/2025.acl-industry.94'))
    provenance['agentsociety']['primary_metadata_checked']='https://aclanthology.org/2025.acl-industry.94/'
    provenance['agentsociety']['metadata_checked_date']='2026-10-09'
    # Parent-authorized bounded addition: a missed 2 October paper, not a new search.
    add('coherence-driven-contagion','parent freshness-notes.md (2026-10-09); arXiv primary metadata',
        **extra('Coherence-Driven Belief Formation and Population Dynamics of Contagion in LLM Agents',
                ['Tathagata Banerjee','Nima Moghaddas'],2026,'https://arxiv.org/abs/2610.02654',
                eprint='2610.02654',archivePrefix='arXiv',
                note='Accepted at the NeurIPS 2026 Workshop on Foundations of Agentic Systems Theory (FAST), per authors'))
    provenance['coherence-driven-contagion'].update(
        primary_metadata_checked='https://arxiv.org/abs/2610.02654',
        fulltext_url='https://arxiv.org/html/2610.02654v1',
        first_public='2026-10-02',metadata_checked_date='2026-10-09',
        proposed_canonical_id='coherence-driven-contagion',part_of=None,
        editorial_component=False,
        inclusion_status='Parent-authorized missed pre-cutoff work; not a post-cutoff discovery')
    # Recover a previously scouted lead after the parent's bounded qualification.
    add('rheon-consensus','discovery/sonnet_A8.md:154-156,222',
        **extra('Consensus and Factual Dynamics in Large Populations of Interacting Language Models',
                ['Emanuele Ricco','Elia Onofri','Vincenzo Sammartino','Roberto Di Pietro'],
                2026,'https://arxiv.org/abs/2609.39211',
                eprint='2609.39211',archivePrefix='arXiv'))
    provenance['rheon-consensus'].update(
        source_sha256=hashlib.sha256((args.archive/'discovery/sonnet_A8.md').read_bytes()).hexdigest(),
        fulltext_url='https://arxiv.org/html/2609.39211v1',
        first_public='2026-09-30',metadata_checked_date='2026-10-09',
        primary_metadata_checked_by='Parent; freshness-notes.md, RHEON lead qualified further by parent',
        proposed_canonical_id='rheon-consensus',part_of=None,editorial_component=False,
        license='CC BY-NC-SA 4.0 (parent primary-page check)',
        inclusion_status='Existing scout lead recovered after parent primary-source qualification; not a post-cutoff discovery')
    # The preserved arXiv metadata includes full lists for many light-card entries.
    meta_path=args.archive/'lanes/t_fable_triage/scratch/arxiv_meta.json'
    arxiv_meta=json.loads(meta_path.read_text())
    for k,d in records.items():
        m=arxiv_meta.get(d.get('eprint',''))
        if m and d.get('_partial_authors') and len(m.get('authors',[])) >= len(d['author']):
            d['author']=m['authors']
            d['_partial_authors']=False
            provenance[k]['author_metadata_source']=str(meta_path.relative_to(args.archive))
    update('ashery-conventions',author=['Ariel Flint Ashery','Luca Maria Aiello','Andrea Baronchelli'],
           volume='11',number='20',pages='eadu9368',_partial_authors=False)
    provenance['ashery-conventions']['author_metadata_source']='lanes/lc_g15/scratch/src/texsrc/main.bib:ashery2025emergent'

    # Complete bylines for the 18 entries left partial by the cards. Values were
    # read from primary arXiv, publisher, and journal pages on 2026-10-09 and are
    # recorded in swarm-recovery-20261009/metadata-18-bylines.md. Source date and
    # spelling conflicts are kept in the citation map, not resolved by guesswork.
    byline_source=('swarm-recovery-20261009/metadata-18-bylines.md '
                   '(primary arXiv, publisher and journal pages, checked 2026-10-09)')
    bylines={
        'agentworm':dict(author=['Yihao Zhang','Zeming Wei','Xiaokun Luan','Chengcan Wu','Zhixin Zhang','Jiangrong Wu','Haolin Wu','Huanran Chen','Jun Sun','Meng Sun'],
            _dates='arXiv v1 2026-03-16; v3 2026-07-16',
            _conflicts='An NDSS footer with a placeholder DOI is insufficient for proceedings metadata; kept as a preprint.'),
        'attributing-emergence':dict(author=['Ling Tang','Jilin Mei','Qian Chen','Qihan Ren','Linfeng Zhang','Quanshi Zhang','Jing Shao','Xia Hu','Dongrui Liu'],
            _dates='arXiv v1 2026-05-12; v2 2026-07-05'),
        'co-scientist-nature':dict(author=['Juraj Gottweis','Wei-Hung Weng','Alexander Daryin','Tao Tu','Petar Sirkovic','Artiom Myaskovsky','Grzegorz Glowaty','Felix Weissenberger','Alessio Orlandi','Dan Popovici','Anil Palepu','Keran Rong','Ryutaro Tanno','Khaled Saab','Fan Zhang','Jacob Blum','Andrew Carroll','Kavita Kulkarni','Nenad Tomašev','Dina Zverinski','Ivor Rendulic','Elahe Vedadi','Florian Hasler','Luka Rimanic','Marina Boia','Ivan Budiselic','Ben Feinstein','Mathias Bellaiche','Tom Sheffer','Jan Freyberg','Jeremy Ratcliff','Ottavia Bertolli','Katherine Chou','Avinatan Hassidim','Burak Gokturk','Amin Vahdat','Yuan Guan','Vikram Dhillon','Eeshit Dhaval Vaishnav','Byron Lee','Tiago R. D. Costa','José R. Penadés','Gary Peltz','Yossi Matias','James Manyika','Demis Hassabis','Yunhan Xu','Pushmeet Kohli','Annalisa Pawlosky','Alan Karthikesalingam','Vivek Natarajan'],
            _dates='Online 2026-05-19; version of record 2026-07-01; issue 2026-07-09'),
        'compass-kilo-flocks':dict(author=['Frederic Vatnsdal','Roshan Gopal','Garcia Camargo, Romina','Vijay Kumar','Alejandro Ribeiro'],
            _dates='arXiv v1 2026-09-23'),
        'conformity-no-speaker':dict(author=['Yibo Hu','Jiaming Qu'],
            title='Most LLM Conformity Needs No Speaker: Measuring the Speaker-Free Floor in Peer-Pressure Benchmarks',
            _dates='arXiv v1 2026-07-06'),
        'emergent-languages':dict(author=['Stine Lyngsø Beltoft','William Brach','Federico Torrielli','Jacob Nielsen','Annemette Brok Pirchert','Filippo Tonini','Peter Schneider-Kamp','Lukas Galke Poech'],
            _dates='arXiv v1 2026-05-29'),
        'human-ai-consensus':dict(author=['Lin Chen','Ziyi Liu','Xia Hu','Yong Li'],
            _dates='arXiv v1 2026-09-02'),
        'moltbook-form-without-function':dict(author=['Saber Zerhoudi','Kanishka {Ghosh Dastidar}','Felix Klement','Artur Romazanov','Andreas Einwiller','Dang H. Dang','Michael Dinzinger','Michael Granitzer','Annette Hautli-Janisz','Stefan Katzenbeisser','Florian Lemmerich','Jelena Mitrović'],
            _dates='Year only: arXiv submission history 2026-03-17; manuscript date 2026-04-16',
            _conflicts='Submission history and manuscript date disagree, so only the year is cited. The abstract page spells Mitrovic; the paper byline spells Mitrović and is followed.'),
        'moltbook-observatory':dict(author=['Sushant Gautam','Annika W. Olstad','Klas H. Pettersen','Michael A. Riegler'],
            title='The Moltbook Observatory Archive: an incremental dataset of agent-only social network activity',
            _dates='Year only: displayed submission 2026-04-16',
            _conflicts='The displayed April submission date conflicts with the 2605 identifier prefix; neither is silently corrected, so only the year is cited.'),
        'multi-agent-security-tax':dict(author=['Pierre Peigné','Mikolaj Kniejski','Filip Sondej','Matthieu David','Jason Hoelscher-Obermaier','{Schroeder de Witt}, Christian','Esben Kran'],
            title='Multi-Agent Security Tax: Trading Off Security and Collaboration Capabilities in Multi-Agent Systems',
            note='Accepted to AAAI 2025 (per arXiv comments)',
            _dates='arXiv v1 2025-02-26; v2 2025-06-04',
            _conflicts='First author: the paper byline reads Pierre Peigné, the abstract metadata Pierre Peigne-Lefebvre, and the uploader field Pierre Peigné-Lefebvre. The paper byline is followed; no expansion is inferred.'),
        'naming-games':dict(author=['De Nobili, Cristiano','Iyer, Vijayasri','Codello, Alessandro','Burioni, Raffaella'],
            _dates='arXiv v1 2026-08-03'),
        'openclaw-norms':dict(author=['Md Motaleb Hossen Manik','Ge Wang'],
            _dates='arXiv v1 2026-02-02'),
        'orchestra-o1':dict(author=['Fan Zhang','Vireo Zhang','Shengju Qian','Haoxuan Li','Hao Wu','Jinyang Wu','Donghao Zhou','Zhihong Zhu','Zheng Lian','Xin Wang','Pheng-Ann Heng'],
            doi='10.48550/arXiv.2606.13707',
            _dates='arXiv v1 2026-06-10'),
        'robin-futurehouse':dict(author=['Ali E. Ghareeb','Benjamin Chang','Ludovico Mitchener','Angela Yiu','Caralyn J. Szostkiewicz','Dmytro Shved','Gavin J. Gyimesi','Jon M. Laurent','Samantha M. Wright','Muhammed T. Razzak','Andrew D. White','Silvia C. Finnemann','Michaela M. Hinks','Samuel G. Rodriques'],
            _dates='Online 2026-05-19; version of record 2026-07-01; issue 2026-07-09',
            _conflicts='Journal title is used; the earlier "Robin:" preprint title belongs to another version.'),
        'science-malicious-swarms':dict(author=['Daniel Thilo Schroeder','Meeyoung Cha','Andrea Baronchelli','Nick Bostrom','Nicholas A. Christakis','David Garcia','Amit Goldenberg','Yara Kyrychenko','Kevin Leyton-Brown','Nina Lutz','Gary Marcus','Filippo Menczer','Gordon Pennycook','David G. Rand','Maria Ressa','Frank Schweitzer','Dawn Song','Christopher Summerfield','Audrey Tang','{Van Bavel}, Jay J.','van der Linden, Sander','Jonas R. Kunst'],
            _dates='Published 2026-01-22',
            _conflicts='The publisher page returned HTTP 403; the byline was read from the journal-formatted PDF hosted by HBS and corroborated by arXiv:2506.06299 author metadata.'),
        'structured-opinion-dynamics':dict(author=['Erica Cau','Andrea Failla','Giulio Rossetti'],
            _dates='arXiv v1 2026-04-13; v3 2026-09-28'),
        'topological-collapse':dict(author=['Shuo Lu','Weicheng Meng','Aijing Yu','Kun Shao','Jian Luan','Ran He','Jian Liang'],
            _dates='arXiv v1 2026-08-16',
            _conflicts='The inherited card reversed given and family names; the arXiv byline order is used.'),
        'zombie-agents':dict(author=['Xianglin Yang','Yufei He','Shuo Ji','Bryan Hooi','Jin Song Dong'],
            note='Published as a workshop paper in Lifelong Agent @ ICLR 2026 (per arXiv comments)',
            _dates='arXiv v1 2026-02-17; v2 2026-03-05',
            _conflicts='Workshop status only; not an ICLR main-conference publication.'),
    }
    for k,fields in bylines.items():
        dates=fields.pop('_dates')
        conflicts=fields.pop('_conflicts',None)
        update(k,_partial_authors=False,**fields)
        provenance[k]['author_metadata_source']=byline_source
        provenance[k]['primary_dates']=dates
        if conflicts:
            provenance[k]['metadata_conflicts']=conflicts

    paired=raw['artificial-hivemind']['paired_work']
    add('artificial-hivemind-reevaluation','cards/artificial-hivemind.json:paired_work',
        **extra(paired['title'],paired['authors'],2026,paired['urls']['abs'],
                eprint='2609.33936',archivePrefix='arXiv',howpublished='arXiv preprint'))
    # v0 reserves old aliases as corpus IDs. Propose fresh IDs for constituents,
    # keeping case/bundle identity separate from a citation to one document.
    component_renames={
        'hf-incident-case':'hf-openai-technical-report',
        'hf-metr-investigation':'hf-metr-redwood-investigation',
        'hf-technical-timeline':'hf-huggingface-technical-timeline',
        'attractor-states':'attractor-states-jakkli-post',
        'ko-geiping-attractors':'attractor-states-ko-geiping-paper',
        'opus4-bliss-attractor':'attractor-states-anthropic-card',
        'cursor-scaling':'cursor-scaling-long-running',
        'ai-village':'ai-village-how-it-works',
        'cognition-multi-agents':'cognition-dont-build-multi-agents',
        'anthropic-multi-agent-guidance':'anthropic-multi-agent-research-system',
        'sakana-conductor-trinity-fugu':'sakana-fugu-report',
        'opus46-launch-cluster':'opus46-launch-post',
    }
    part_of={
        'hf-openai-technical-report':'hf-incident-case',
        'hf-metr-redwood-investigation':'hf-incident-case',
        'hf-huggingface-technical-timeline':'hf-incident-case',
        'attractor-states-jakkli-post':'attractor-states',
        'attractor-states-ko-geiping-paper':'attractor-states',
        'attractor-states-anthropic-card':'attractor-states',
        'cursor-scaling-long-running':'cursor-scaling','cursor-self-driving':'cursor-scaling',
        'ai-village-how-it-works':'ai-village','ai-village-longitudinal':'ai-village',
        'cognition-dont-build-multi-agents':'cognition-multi-agents',
        'cognition-multi-agents-working':'cognition-multi-agents',
        'anthropic-multi-agent-research-system':'anthropic-multi-agent-guidance',
        'sakana-fugu-report':'sakana-conductor-trinity-fugu',
        'sakana-conductor':'sakana-conductor-trinity-fugu','sakana-trinity':'sakana-conductor-trinity-fugu',
        'opus46-launch-post':'opus46-launch-cluster',
        'artificial-hivemind-reevaluation':'artificial-hivemind',
        'piao-polarization':'prev-population-dynamics-cluster',
        'ashery-conventions':'prev-population-dynamics-cluster',
        'gasim':'prev-moltbook-cluster','agentsociety':'prev-moltbook-cluster',
    }
    for old,new in component_renames.items():
        records[new]=records.pop(old)
        provenance[new]=provenance.pop(old)
    for k,group in part_of.items():
        provenance[k]['part_of']=group
        provenance[k]['proposed_canonical_component_id']=k
    for k,*_,source in components:
        provenance[k]['part_of']=source
    for k in ['anthropic-multi-agent-research-system','crypto-weaknesses','kimi-k3-swarm-bench']:
        records[k]['_partial_authors']=False

    aliases = json.loads((args.archive/'build/card_alias.json').read_text())
    aliases.update({'openai-hf-incident-2026':'hf-incident-case',
                    'piao2025':'piao-polarization','piao2026':'piao-polarization',
                    '2501.05171':'piao-polarization'})

    lines=['% Generated from preserved October 2026 research cards.',
           '% Do not interpret entry count as a deduplicated count of research works.',
           '% Author lists ending in "and others" are incomplete in the inherited card.', '']
    for k,d in sorted(records.items()):
        if d.get('eprint') and d.get('howpublished')=='arXiv preprint':
            d.pop('howpublished')  # ACL's eprint formatter already prints Preprint.
        lines += [f'% source: {provenance[k]["source_card"]}', f'@{d["entrytype"]}{{{k},']
        for field,value in d.items():
            if field.startswith('_') or field=='entrytype' or value in [None,'']:continue
            if field=='author':
                value=' and '.join('{'+tex(a)+'}' if a in CORPORATE else tex(SURNAME_PARTICLES.get(a,a)) for a in value)
            elif field in ['url','doi','eprint','archivePrefix']:
                value=str(value).replace('%',r'\%') if field=='url' else str(value)
            else:value=tex(value)
            if field=='title':value='{'+value+'}'
            lines.append(f'  {field} = {{{value}}},')
        lines += ['}', '']
    # BibTeX cannot resolve aliases. Duplicate alias records are intentionally NOT emitted.
    (ROOT/'paper/references.bib').write_text('\n'.join(lines))
    mapping={'schema_version':1,'key_policy':'Source card filename stem; separate component documents receive explicit keys.',
             'source_cutoff':'2026-10-03','author_file_state':'2026-10-04','metadata_update':'2026-10-09','corpus_aliases':aliases,
             'draft_citation_replacements':component_renames,
             'nonpublication_bundles':{k:'Use the individual component entries, not this bundle key.' for k in raw if k.startswith('prev-') and k.endswith('-cluster')},
             'entries':{k:dict(provenance[k],title=d['title'],url=d.get('url',''),
                               partial_author_list=bool(d.get('_partial_authors')),
                               inherited_status=d.get('_inherited_status','')) for k,d in sorted(records.items())}}
    (ROOT/'paper/citation-key-map.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    print(f'Wrote {len(records)} citable records, {len(aliases)} aliases; no unique-work count implied.')
    remaining=[(k,d['author']) for k,d in records.items() if any(re.search('[\u0400-\u04ff]',a) for a in d['author'])]
    print('Cyrillic author strings requiring normalization:',remaining)


if __name__=='__main__':
    main()

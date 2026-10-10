#!/usr/bin/env python3
"""Build the canonical work registry data/works.json (+ data/stats.json, data/bib/works.bib).

  python scripts/build_registry.py <S>          # S = October sprint tree (read-only)

Identity rules (see data/interface.md):
  * a work with an October card keeps the card ID; synonyms from build/card_alias.json become `aliases`;
  * constituent documents of bundle cards get their own ID with `part_of` (data/registry_overrides.json);
  * every other URL in the text becomes a resource record with a deterministic ID derived from the URL;
  * URLs are merged into one work by normalized key: arXiv ID, DOI (incl. nature.com / science.org pages),
    ACL Anthology ID, else host+path without scheme, www, query or fragment.
The registry is generated once from the October tree and committed; later edits go to registry_overrides.json.
"""
import json, os, re, sys, unicodedata
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = sys.argv[1] if len(sys.argv) > 1 else "research-archive"
CARD_DIRS = ["cards", "cards_lanes", "cards_b", "cards_c"]
SYNONYMS = {"opus55-card-multiagent", "gpt56-ultra-launch", "anthropic-multiagent-patterns", "self-organizing-agent-teams", "cursor-scaling-agents"}

def key(url):
    if not url: return None
    u = url.strip().split()[0].rstrip(".,;)")
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", u)
    if m: return "arxiv:" + m.group(1)
    m = re.search(r"10\.48550/arXiv\.(\d{4}\.\d{4,5})", u, re.I)
    if m: return "arxiv:" + m.group(1)
    m = re.search(r"(?:dx\.)?doi\.org/(10\.\d{4,9}/[^\s?#]+)", u)
    if m: return "doi:" + m.group(1).lower().rstrip("/")
    m = re.search(r"nature\.com/articles/([a-z0-9.-]+?)(?:\.pdf)?(?:[?#]|$)", u)
    if m: return "doi:10.1038/" + m.group(1).lower()
    m = re.search(r"science\.org/doi/(?:full/|abs/|pdf/)?(10\.\d{4,9}/[^\s?#]+)", u)
    if m: return "doi:" + m.group(1).lower()
    m = re.search(r"pnas\.org/doi/(?:full/|abs/|pdf/)?(10\.\d{4,9}/[^\s?#]+)", u)
    if m: return "doi:" + m.group(1).lower()
    m = re.search(r"aclanthology\.org/([\w.-]+?)/?(?:\.pdf)?$", u)
    if m: return "doi:10.18653/v1/" + m.group(1).lower()   # ACL Anthology IDs are the suffix of their DOI
    m = re.search(r"openreview\.net/(?:forum|pdf)\?id=([\w-]+)", u)
    if m: return "openreview:" + m.group(1)
    u = re.sub(r"^https?://", "", u); u = re.sub(r"^www\.", "", u)
    u = u.split("#")[0].split("?")[0].rstrip("/")
    return "web:" + u.lower()

def first_url(s):
    if not s: return None
    if isinstance(s, list): s = s[0] if s else ""
    m = re.search(r"https?://\S+", str(s))
    return m.group(0).rstrip(".,;)") if m else None

def all_urls(s):
    return [u.rstrip(".,;)") for u in re.findall(r"https?://[^\s\"'<>]+", json.dumps(s, ensure_ascii=False) if not isinstance(s, str) else s)]

def slug(s, n=60):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:n].strip("-")

def date10(s):
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", str(s or ""))
    if not m: return None
    return m.group(0)

def load_cards():
    out = {}
    for d in CARD_DIRS:
        p = os.path.join(S, d)
        for f in sorted(os.listdir(p)):
            if f.endswith(".json") and ".pre_fix" not in f:
                c = json.load(open(os.path.join(p, f), encoding="utf-8"))
                c["_dir"] = d; c["_file_id"] = f[:-5]
                if c.get("id") != f[:-5]: c["_internal_id"] = c.get("id"); c["id"] = f[:-5]   # file name is the card ID used in the text
                out.setdefault(c["id"], c)
    return out

def import_text():
    import subprocess, tempfile
    tmp = tempfile.mkdtemp(prefix="aas-reg-")
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "import_source.py"), S, "--out", tmp], check=True, capture_output=True)
    pages = OrderedDict()
    for f in sorted(os.listdir(tmp)):
        pages[f[:-3]] = open(os.path.join(tmp, f), encoding="utf-8").read()
    return pages

KIND_FROM_META = {"peer_reviewed": "journal_or_conference", "preprint": "preprint", "system_card": "system_card", "lab_report": "lab_blog",
                  "incident_report": "incident_report", "essay_blog": "essay", "dataset_platform": "dataset"}

def kind_from_url(u, title=""):
    k = key(u) or ""
    if k.startswith("arxiv:"): return "preprint"
    if k.startswith("doi:10.1038/") or k.startswith("doi:10.1126/") or k.startswith("doi:10.1073/") or k.startswith("doi:10.1145/"): return "journal_or_conference"
    if k.startswith("acl:") or k.startswith("doi:10.18653/"): return "journal_or_conference"
    if k.startswith("openreview:"): return "preprint"
    if k.startswith("doi:10.5281/zenodo"): return "preprint"   # Zenodo record of a manuscript (data/code deposits are excluded from identities)
    if "github.com" in k: return "repo"
    if "huggingface.co/datasets" in k: return "dataset"
    if "biorxiv" in k: return "preprint"
    if any(h in k for h in ("lesswrong.com", "substack", "oneusefulthing", "dwarkesh", "darioamodei", "yegge.ai", "forethought")): return "essay"
    if any(h in k for h in ("anthropic.com", "openai.com", "cursor.com", "cognition", "claude.com", "x.ai", "metr.org", "huggingface.co/blog", "aisi.gov.uk", "research.google", "antigravity.google", "about.fb.com", "wiz.io", "theaidigest", "research.trychroma", "alignment.anthropic", "deploymentsafety.openai")): return "lab_blog"
    if any(h in k for h in ("science.org/content", "oag.ca.gov", "404media", "axios", "techcrunch")): return "news"
    return "web"

def kind_from_note(note):
    """Record type from the October card's own venue/status note (checked before the URL heuristic)."""
    n = str(note or "").lower()
    if not n: return None
    if re.search(r"новостн|\bnews\b|пресс-релиз|press release", n): return "news"
    if re.search(r"страница мероприятия|event page", n): return "web"
    if re.search(r"воркшоп|workshop", n) and not re.search(r"main conference|основн", n): return "workshop"
    if re.search(r"tmlr|icml|neurips|iclr|acl 20|emnlp|colm|sigdial|eacl|naacl|aaai|nature|science advances|pnas|journal", n) and not re.search(r"по комментарию|по словам|per the|according to|accepted per", n): return "journal_or_conference"
    if re.search(r"препринт|preprint|arxiv|biorxiv", n): return "preprint"
    if re.search(r"системн|system card|model card", n): return "system_card"
    if re.search(r"эссе|essay|lesswrong|интервью|interview|блог \(lesswrong", n): return "essay"
    if re.search(r"блог|blog|отчёт компании|company report|технический отчёт|technical report|threat intelligence", n): return "lab_blog"
    if re.search(r"датасет|dataset|набор данных", n): return "dataset"
    return None

def peer_from(meta_type, card):
    if card.get("peer_reviewed") is True: return "peer_reviewed"
    vs = str(card.get("venue_status") or card.get("status") or "")
    if re.search(r"workshop", vs, re.I): return "workshop"
    if meta_type == "peer_reviewed": return "peer_reviewed"
    if meta_type: return "none"
    return "unknown"

def authors_of(c):
    a = c.get("authors")
    if isinstance(a, list):
        return [re.sub(r"^\([A-Z]\)\s*", "", x if isinstance(x, str) else (x.get("name") or "")).split(" (")[0].strip() for x in a]
    if isinstance(a, str): return [a]
    if c.get("authors_short"): return [c["authors_short"]]
    return []

def identity_keys(c):
    keys = set()
    u = c.get("urls")
    prim = (u or {}).get("primary") if isinstance(u, dict) else (c.get("url") or first_url(u))
    pk = key(first_url(prim)) if prim else None
    if pk: keys.add(pk)
    if isinstance(u, dict):
        for f in ("pdf", "html"):
            k2 = key(first_url(u.get(f)))
            if k2 and pk and (k2 == pk or (k2.split(":")[0] == pk.split(":")[0] == "web" and k2.split("/")[0] == pk.split("/")[0] and c.get("_dir") != "cards_lanes")):
                keys.add(k2)
        other = u.get("other")
        txt = " ; ".join(other) if isinstance(other, list) else str(other or "")
        for m in re.finditer(r"(arXiv|preprint|Preprint|journal version|published version|Published version)[^h]{0,25}(https?://\S+)", txt):
            keys.add(key(m.group(2)))
    for f in ("date_first_public", "versions", "venue_status", "type", "status"):
        v = str(c.get(f) or "")
        for m in re.finditer(r"arXiv[:\s]*(\d{4}\.\d{4,5})", v): keys.add("arxiv:" + m.group(1))
        for m in re.finditer(r"\bDOI[:\s]*(10\.\d{4,9}/[^\s;,)]+)", v): keys.add("doi:" + m.group(1).lower().rstrip("."))
    return {k for k in keys if k}, (first_url(prim) if prim else None)

def main():
    cards = load_cards()
    meta = {m["id"]: m for m in json.load(open(os.path.join(S, "build/meta/corpus_meta.json"), encoding="utf-8"))}
    pru = json.load(open(os.path.join(S, "passports_ru.json"), encoding="utf-8"))
    alias = json.load(open(os.path.join(S, "build/card_alias.json"), encoding="utf-8"))
    ov_path = os.path.join(ROOT, "data", "registry_overrides.json")
    overrides = json.load(open(ov_path, encoding="utf-8")) if os.path.exists(ov_path) else {}
    pages = import_text()
    # where cards appear
    card_pages, level = defaultdict(list), {}
    for p, t in pages.items():
        for kind, cid in re.findall(r"(?m)^:::(card|short)\s+(\S+)", t):
            cid = alias.get(cid, cid); card_pages[cid].append(p); level[cid] = "full_card" if kind == "card" else "short_card"
    works = OrderedDict(); by_key = {}
    def reg(rec, keys):
        works[rec["id"]] = rec
        for k in keys:
            if k in by_key and by_key[k] != rec["id"]:
                rec.setdefault("_key_conflicts", []).append([k, by_key[k]])
                continue
            by_key[k] = rec["id"]
        rec["identity_keys"] = sorted(keys)
    CLUSTER = re.compile(r"\(кластер|\bcluster\b", re.I)
    clusters = OrderedDict((c, v) for c, v in cards.items() if v["_dir"] == "cards_c" and CLUSTER.search(v.get("title") or ""))
    ids = list(level) + [m for m in meta if m not in level] + [c for c, v in cards.items() if v["_dir"] == "cards_c" and c not in level and c not in meta and c not in clusters]
    for cid in ids:
        c = cards.get(cid) or {}
        m = meta.get(cid, {})
        o = pru.get(cid, {})
        keys, prim = identity_keys(c)
        excl = {k: v for k, v in (overrides.get("identity_exclusions") or {}).get(cid, {}).items()}
        excluded = [[k, excl[k]] for k in sorted(keys) if k in excl]
        keys = {k for k in keys if k not in excl}
        urls = c.get("urls") if isinstance(c.get("urls"), dict) else {}
        code = first_url(urls.get("code")) if urls else None
        rec = OrderedDict(
            id=cid, aliases=sorted(a for a, t in alias.items() if t == cid and a in SYNONYMS),
            kind=KIND_FROM_META.get(m.get("source_type")) or kind_from_note(c.get("venue_status") or c.get("status")) or kind_from_url(prim or "", c.get("title", "")),
            title=c.get("title"), title_ru_display=o.get("display_title"),
            authors=authors_of(c), n_authors=c.get("n_authors"),
            orgs=m.get("orgs") or ([c["institutions_short"]] if c.get("institutions_short") else []),
            institutions_note=c.get("institutions_short"),
            date_first_public=date10(c.get("date_first_public")) or (m.get("month") or None),
            venue_note=c.get("venue_status") or c.get("status"),
            peer_review=peer_from(m.get("source_type"), c),
            identifiers=OrderedDict(arxiv=next((k[6:] for k in sorted(keys) if k.startswith("arxiv:")), None),
                                    doi=next((k[4:] for k in sorted(keys) if k.startswith("doi:")), None)),
            urls=OrderedDict(primary=prim, code=code if code and code.startswith("http") else None,
                             code_note=(lambda t: ("listed in the paper; returned HTTP 404 at the October check" if re.search(r"\b404\b", t) else
                                                   "link taken from the paper, not opened at the October check" if re.search(r"not opened|not checked|не открыв", t) else None))(str(urls.get("code") or "")) if urls else None),
            level=level.get(cid) or ("mention_in_corpus" if cid in meta else "table_row"),
            in_analytic_corpus=cid in meta,
            source_pages=card_pages.get(cid, []),
            part_of=None,
            corpus=OrderedDict((k, m.get(k)) for k in ("month", "source_type", "org_class", "evidence", "topics", "scale_kind",
                         "agents_max_simultaneous", "agents_total", "scale_note_ru", "models", "model_families", "n_models", "mixed_swarm")) if m else None,
            card_file=f"{c['_dir']}/{cid}.json" if c else None,
            updates=[])
        if excluded: rec["excluded_keys"] = excluded
        reg(rec, keys)
    # constituent documents and manual records
    for rec in overrides.get("works", []):
        r = OrderedDict(rec); ks = {key(u) for u in r.pop("_urls", [])} | {key(r["urls"]["primary"])}
        claim = r.pop("claim_keys", False); r["provenance"] = r.pop("source", None)
        for f, v in (("updates", []), ("aliases", []), ("source_pages", []), ("n_authors", None), ("institutions_note", None),
                     ("venue_note", None), ("title_ru_display", None), ("corpus", None), ("card_file", None)):
            r.setdefault(f, v)
        r.setdefault("identifiers", OrderedDict(arxiv=None, doi=None))
        ks = {k for k in ks if k}
        if claim:
            for k in ks:
                old = by_key.get(k)
                if old and old != r["id"]:
                    works[old]["identity_keys"] = [x for x in works[old]["identity_keys"] if x != k]
                    by_key.pop(k)
        reg(r, ks)
    for b in overrides.get("bundle_cards", []):
        works[b]["kind"] = "bundle"
    # merges declared by hand: key -> id
    for k, wid in overrides.get("merge_keys", {}).items():
        by_key[k] = wid; works[wid]["identity_keys"] = sorted(set(works[wid]["identity_keys"]) | {k})
    # every URL in the text
    occ = defaultdict(list)
    for p, t in pages.items():
        in_rel = False
        for ln in t.split("\n"):
            if ln.startswith("## "): in_rel = bool(re.match(r"## (Ещё по теме|Для сравнения)", ln))
            for mm in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", ln):
                first_col = ln.lstrip().startswith("|") and ln.split("|")[1].find(mm.group(0)) >= 0
                occ[mm.group(2)].append((p, "table_row" if (in_rel and first_col) else "inline_link", mm.group(1)))
    text_links = OrderedDict()
    for u, places in occ.items():
        k = key(u); wid = by_key.get(k)
        if not wid:
            p0, lvl0, label = places[0]
            lvl = "table_row" if any(l == "table_row" for _, l, _ in places) else "inline_link"
            if lvl == "table_row" and label:
                stop = {"a", "an", "the", "of", "in", "for", "and", "on", "to", "via", "with", "is", "are", "llm", "multi", "agent"}
                words = [w for w in slug(re.sub(r"\(.*?\)", "", label), 200).split("-") if w and w not in stop]
                wid = "-".join(words[:4]) or slug(k, 40)
            elif k.startswith("arxiv:"): wid = "arxiv-" + k[6:].replace(".", "-")
            elif k.startswith("doi:"): wid = "doi-" + slug(k[4:], 50)
            elif k.startswith("acl:"): wid = "acl-" + slug(k[4:], 50)
            else: wid = slug(k[4:].replace("/", "-"), 70)
            base, n = wid, 2
            while wid in works: wid = f"{base}-{n}"; n += 1
            label_title = label if lvl == "table_row" else None
            rec = OrderedDict(id=wid, aliases=[], kind=kind_from_url(u), title=label_title, title_ru_display=None, authors=[], n_authors=None,
                              orgs=[], institutions_note=None, date_first_public=None, venue_note=None, peer_review="unknown",
                              identifiers=OrderedDict(arxiv=k[6:] if k.startswith("arxiv:") else None, doi=k[4:] if k.startswith("doi:") else None),
                              urls=OrderedDict(primary=u, code=None), level=lvl, in_analytic_corpus=False, source_pages=[], part_of=None,
                              corpus=None, card_file=None, updates=[])
            reg(rec, {k})
        w = works[wid]
        for p, lvl, label in places:
            if p not in w["source_pages"]: w["source_pages"].append(p)
        text_links[u] = wid
        if any(l == "table_row" for _, l, _ in places): w.setdefault("in_related_tables", True)
        if w["level"] == "inline_link" and any(l == "table_row" for _, l, _ in places): w["level"] = "table_row"
    for u in occ:
        pass
    # updates from overrides
    for wid, ups in overrides.get("updates", {}).items():
        works[wid]["updates"] = ups
    # ---- reconciliation with the integrated paper's citation keys (see scripts/reconcile_paper_keys.py)
    pr = {} if os.environ.get("AAS_NO_RECONCILE") else (overrides.get("paper_reconciliation") or {})
    for comp in pr.get("components", []):
        cid = comp["id"]
        if cid in works: continue
        k = key(comp.get("url"))
        rec = OrderedDict(id=cid, aliases=[], kind=kind_from_note(comp.get("inherited_status")) or kind_from_url(comp.get("url") or ""), title=comp.get("title"),
                          title_ru_display=None, authors=[], n_authors=None, orgs=[], institutions_note=None,
                          date_first_public=date10(comp.get("first_public")), venue_note=comp.get("inherited_status"), peer_review="unknown",
                          identifiers=OrderedDict(arxiv=k[6:] if k and k.startswith("arxiv:") else None, doi=k[4:] if k and k.startswith("doi:") else None),
                          urls=OrderedDict(primary=comp.get("url"), code=None, code_note=None), level="constituent", in_analytic_corpus=False,
                          source_pages=list((works.get(comp.get("part_of")) or {}).get("source_pages") or []), part_of=comp.get("part_of"),
                          corpus=None, card_file=None, updates=[], provenance="component key from the integrated paper's citation-key-map.json")
        if k:
            old = by_key.get(k)
            if old and old != cid:
                works[old]["identity_keys"] = [x for x in works[old]["identity_keys"] if x != k]
                if works[old].get("level") in ("full_card", "short_card") and works[old]["kind"] != "bundle": works[old]["kind_note"] = "multi-document card"
            by_key[k] = cid
        rec["identity_keys"] = [k] if k else []
        works[cid] = rec
        for u, wid in list(text_links.items()):
            if key(u) == k: text_links[u] = cid
    ren = pr.get("renames") or {}
    oct_alias = pr.get("october_aliases_to_bundles") or {}
    for old, new in ren.items():
        if old not in works or new in works: continue
        rec = works.pop(old); rec["id"] = new
        if old not in oct_alias: rec["aliases"] = sorted(set(rec.get("aliases") or []) | {old})
        works[new] = rec
        for k in rec.get("identity_keys") or []: by_key[k] = new
        for u, wid in list(text_links.items()):
            if wid == old: text_links[u] = new
        for w in works.values():
            if w.get("part_of") == old: w["part_of"] = new
    for a, t in oct_alias.items():
        if t in works and a not in works: works[t]["aliases"] = sorted(set(works[t].get("aliases") or []) | {a})
    cluster_ids = set(clusters)
    for wid, parent in (pr.get("part_of") or {}).items():
        if wid in works and not works[wid].get("part_of") and (parent in works or parent in cluster_ids):
            works[wid]["part_of"] = parent
    for w in works.values():   # a card whose documents are now separate components is a multi-document bundle
        if w.get("level") in ("full_card", "short_card") and any(x.get("part_of") == w["id"] for x in works.values()) and not w.get("identity_keys"):
            w["kind"] = "bundle"
    for w in works.values():   # components of a cluster without their own link: page of their siblings
        if w.get("part_of") in cluster_ids and not w.get("source_pages"):
            sib = sorted({p for x in works.values() if x.get("part_of") == w["part_of"] for p in (x.get("source_pages") or [])})
            w["source_pages"] = sib
    for c in clusters:
        pass
    # ---- source-grounded metadata corrections (bylines, titles, venues, date conflicts); see overrides "metadata_corrections"
    mc = overrides.get("metadata_corrections") or {}
    def split_bib_authors(b):
        parts, depth, cur = [], 0, ""
        for tok in re.split(r"(\{|\}|\s+and\s+)", b):
            if tok == "{": depth += 1
            elif tok == "}": depth -= 1
            if depth == 0 and re.fullmatch(r"\s+and\s+", tok or ""):
                parts.append(cur); cur = ""
            else: cur += tok or ""
        parts.append(cur)
        out = []
        for a in parts:
            a = a.strip(); top = re.sub(r"\{[^}]*\}", lambda m: "x" * len(m.group(0)), a)
            if "," in top:
                i = top.index(","); a = a[i + 1:].strip() + " " + a[:i].strip()
            out.append(a.replace("{", "").replace("}", ""))
        return out
    for wid, c in mc.items():
        if wid.startswith("_") or wid not in works: continue
        w = works[wid]
        w["authors"] = split_bib_authors(c["authors_bibtex"]); w["authors_bibtex"] = c["authors_bibtex"]; w["n_authors"] = len(w["authors"])
        if c.get("title") and c["title"] != w.get("title"):
            if w.get("title"): w.setdefault("title_variants", []).append(w["title"])
            w["title"] = c["title"]
        if c.get("date_first_public"): w["date_first_public"] = c["date_first_public"]
        if c.get("date_precision"): w["date_precision"] = c["date_precision"]
        if c.get("version_note"): w["version_note"] = c["version_note"]
        if c.get("venue"): w["venue"] = c["venue"]
        if c.get("arxiv_doi"): w["identifiers"]["arxiv_doi"] = c["arxiv_doi"]
        if c.get("note"): w["venue_status_note"] = c["note"]
        if c.get("status") == "workshop": w["peer_review"] = "workshop"
        if c.get("status") == "journal": w["peer_review"] = "peer_reviewed"
        if c.get("conflicts"): w["metadata_conflicts"] = c["conflicts"]
        w["metadata_corrected"] = "2026-10-09, metadata task 4aab7b90 (source-grounded byline/title check)"
    # stats
    from collections import Counter
    lv = Counter(w["level"] for w in works.values())
    rows = sum(1 for t in pages.values() for ln in t.split("\n") if re.match(r"^\|\s*\[", ln))
    related_rows = 0
    for t in pages.values():
        in_rel = False
        for ln in t.split("\n"):
            if ln.startswith("## "): in_rel = bool(re.match(r"## (Ещё по теме|Для сравнения)", ln))
            if in_rel and re.match(r"^\|(?!\s*-)", ln) and not re.match(r"^\|\s*Работа\s*\|", ln): related_rows += 1
    scholarly = sum(1 for w in works.values() if w["kind"] in ("preprint", "journal_or_conference", "system_card", "dataset", "workshop"))
    stats = OrderedDict(
        corpus=sum(1 for w in works.values() if w["in_analytic_corpus"]),
        cards_full=lv["full_card"], cards_short=lv["short_card"], mention_in_corpus=lv["mention_in_corpus"],
        cards_added_after_import=sum(1 for w in works.values() if w.get("added") and w.get("level") in ("short_card", "full_card")),
        retired_cluster_records=len(clusters),
        related_rows=related_rows,
        table_row_works=lv["table_row"], inline_link_resources=lv["inline_link"], constituent_documents=lv["constituent"],
        unique_works=len(works), unique_urls_in_text=len(occ), unique_url_keys_in_text=len({key(u) for u in occ}),
        fig_works=45, fig_own=7, orgs_in_passports=167,
        note="unique_works = all registry records after merging URL variants (arXiv abs/pdf/html/versions, DOI and publisher pages, synonyms) and card aliases; includes cards, related-work rows, constituent documents and every other linked resource (news, blog posts, documentation).")
    # bib
    os.makedirs(os.path.join(ROOT, "data", "bib"), exist_ok=True)
    def bibesc(s): return str(s or "").replace("&", r"\&").replace("%", r"\%").replace("#", r"\#").replace("_", r"\_")
    bib = []
    for w in works.values():
        if w["level"] == "inline_link" and w["kind"] in ("news", "web"): pass
        typ = {"journal_or_conference": "article", "preprint": "misc"}.get(w["kind"], "misc")
        f = OrderedDict()
        if w["title"]: f["title"] = "{" + bibesc(re.sub(r"\s+", " ", w["title"])) + "}"
        au = [a for a in w["authors"] if a and len(a) < 80]
        if w.get("authors_bibtex"): f["author"] = w["authors_bibtex"]     # source-grounded, BibTeX name form kept verbatim
        elif au: f["author"] = " and ".join(bibesc(a) for a in au)
        elif w.get("orgs"): f["author"] = "{" + bibesc(w["orgs"][0]) + "}"
        v = w.get("venue") or {}
        if v.get("journal"):
            typ = "article"; f["journal"] = v["journal"]
            for fk in ("volume", "number", "pages"):
                if v.get(fk): f[fk] = v[fk]
            f["year"] = (v.get("published_online") or w["date_first_public"] or "")[:4]
            if v.get("note"): f["note"] = v["note"]
        elif w["date_first_public"]: f["year"] = w["date_first_public"][:4]
        if w.get("venue_status_note"): f["note"] = bibesc(w["venue_status_note"])
        if w["identifiers"]["arxiv"]: f["eprint"] = w["identifiers"]["arxiv"]; f["archivePrefix"] = "arXiv"
        if w["identifiers"]["doi"]: f["doi"] = w["identifiers"]["doi"]
        if w["urls"]["primary"]: f["url"] = w["urls"]["primary"]
        if w["venue_note"] and typ != "misc" and "note" not in f and not v.get("journal"): f["note"] = bibesc(str(w["venue_note"])[:160])
        f["keywords"] = w["level"]
        bib.append(f"@{typ}{{{w['id']},\n" + ",\n".join(f"  {k} = {{{v}}}" if not v.startswith("{") else f"  {k} = {v}" for k, v in f.items()) + "\n}\n")
    open(os.path.join(ROOT, "data", "bib", "works.bib"), "w", encoding="utf-8").write(
        "% Generated by scripts/build_registry.py from data/works.json. Do not edit by hand.\n% Key = canonical work id.\n\n" + "\n".join(bib))
    conflicts = [(w["id"], w["_key_conflicts"]) for w in works.values() if w.get("_key_conflicts")]
    for w in works.values():
        for k, other in w.pop("_key_conflicts", []) or []:
            w["identity_keys"] = [x for x in w["identity_keys"] if x != k]
            w.setdefault("related_keys", []).append(k)
    cluster_out = []
    for cid, v in clusters.items():
        ks, prim = identity_keys(v)
        cluster_out.append(OrderedDict(id=cid, title=v.get("title"), status=v.get("status"), retired_as_work=True,
            reason="October scout record grouping several works into one table-row card; not itself a work. Each member row is its own record.",
            member_records=sorted({w["id"] for w in works.values() if w.get("part_of") == cid} | {by_key[k] for k in ks if k in by_key}), primary=prim))
    out = OrderedDict(version="v1", generated_by="scripts/build_registry.py", source_cutoff="2026-10-03", clusters=cluster_out, stats=stats,
                      text_url_map=text_links, works=list(works.values()))
    json.dump(out, open(os.path.join(ROOT, "data", "works.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(stats, open(os.path.join(ROOT, "data", "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1)); print("key conflicts:", conflicts)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Canonical identity audit of data/works.json -> data/provenance/IDENTITY_AUDIT.md (+ identity_audit.json).

Documents, for every record: which URLs/identifiers were merged into it and by which rule, where each
identifier came from (a URL in the text, a URL in the card JSON, a version/venue field of the card JSON, or a
hand-curated override verified against arXiv/publisher), records kept separate because of a key conflict,
possible duplicates by normalized title, and counts by record class (publications vs other resources).
  python scripts/identity_audit.py <S>
"""
import json, os, re, sys, unicodedata
from collections import Counter, defaultdict, OrderedDict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_registry import key, identity_keys, load_cards
import build_registry as BR
S = sys.argv[1] if len(sys.argv) > 1 else "research-archive"
BR.S = S
REG = json.load(open(os.path.join(ROOT, "data/works.json"), encoding="utf-8"))
OV = json.load(open(os.path.join(ROOT, "data/registry_overrides.json"), encoding="utf-8"))
OV_IDS = {w["id"]: w for w in OV["works"]}
cards = load_cards()
text_map = REG["text_url_map"]
urls_by_work = defaultdict(list)
for u, wid in text_map.items(): urls_by_work[wid].append(u)

CLASS = OrderedDict([
 ("paper", "Scholarly work (journal, conference, workshop, preprint)"),
 ("system_card", "Model system card"),
 ("report", "Lab / company / incident report or engineering post"),
 ("essay", "Essay, blog post, interview, forum post"),
 ("news", "News article / press release"),
 ("dataset", "Dataset, benchmark site or platform"),
 ("software", "Software repository"),
 ("event", "Event page / other web page"),
 ("bundle", "Case dossier grouping several documents (not itself a publication)"),
])
KIND2CLASS = {"journal_or_conference": "paper", "preprint": "paper", "workshop": "paper", "system_card": "system_card", "lab_blog": "report",
              "incident_report": "report", "essay": "essay", "news": "news", "dataset": "dataset", "repo": "software", "web": "event", "bundle": "bundle"}

def norm_title(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\(.*?\)", "", t); t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return " ".join(t.split()[:8])

def ident_sources(w):
    """Where each identity key of the record comes from."""
    out = OrderedDict()
    c = cards.get(w["id"])
    if w["id"] in OV_IDS:
        o = OV_IDS[w["id"]]
        for k in w.get("identity_keys") or []:
            out[k] = "override (" + (o.get("source") or "hand-curated") + ")"
        return out
    if c:
        u = c.get("urls")
        prim = (u or {}).get("primary") if isinstance(u, dict) else c.get("url")
        pk = key(prim) if prim else None
        for k in w.get("identity_keys") or []:
            if k == pk: out[k] = "card JSON primary URL"; continue
            src = None
            if isinstance(u, dict):
                for f in ("pdf", "html"):
                    if u.get(f) and key(str(u.get(f)).split()[0]) == k: src = f"card JSON urls.{f} (same work variant)"
                if not src and k in {key(x) for x in re.findall(r"https?://\S+", json.dumps(u.get("other"), ensure_ascii=False))}:
                    src = "card JSON urls.other, labelled as arXiv/preprint/journal version"
            if not src:
                for f in ("date_first_public", "versions", "venue_status", "type", "status"):
                    v = str(c.get(f) or "")
                    if (k.startswith("arxiv:") and k[6:] in v) or (k.startswith("doi:") and k[4:] in v.lower()): src = f"card JSON field '{f}' (free-text version/venue note)"; break
            out[k] = src or "text URL"
    else:
        for k in w.get("identity_keys") or []: out[k] = "URL in the survey text"
    return out

def main():
    rows, merges, conflicts, cls_count = [], [], [], Counter()
    for w in REG["works"]:
        cl = KIND2CLASS.get(w["kind"], "event")
        kb = "October corpus metadata (source_type)" if (w.get("corpus") or {}).get("source_type") else ("override" if w["id"] in OV_IDS else "URL-based heuristic")
        cls_count[cl] += 1
        srcs = ident_sources(w)
        text_urls = sorted(urls_by_work.get(w["id"], []))
        keys_from_text = {key(u) for u in text_urls}
        if len(set(srcs) | keys_from_text) > 1:
            merges.append((w["id"], cl, sorted(set(srcs) | keys_from_text), srcs))
        for k in w.get("related_keys") or []:
            conflicts.append((w["id"], k))
        rows.append(OrderedDict(id=w["id"], level=w["level"], kind=w["kind"], record_class=cl, class_basis=kb,
            arxiv=w["identifiers"].get("arxiv"), doi=w["identifiers"].get("doi"), identity_keys=w.get("identity_keys"), key_sources=srcs,
            text_urls=text_urls, aliases=w.get("aliases") or [], part_of=w.get("part_of"), related_keys=w.get("related_keys") or [],
            title=w.get("title"), uncertain=[x for x in [
                "title from link text only" if (w.get("level") in ("table_row", "inline_link") and not w.get("card_file") and w["id"] not in OV_IDS and not w.get("metadata_corrected")) else None,
                "record class from URL heuristic" if kb == "URL-based heuristic" else None,
                "identifier from a free-text card field" if any("free-text" in v for v in srcs.values()) else None,
                "no title recorded" if not w.get("title") else None] if x]))
    # duplicate candidates by normalized title
    by_t = defaultdict(list)
    for r in rows:
        if r["title"]: by_t[norm_title(r["title"])].append(r["id"])
    parent = {r["id"]: r["part_of"] for r in rows}
    dups = {t: ids for t, ids in by_t.items() if len(ids) > 1 and t
            and not (len(ids) == 2 and (parent.get(ids[0]) == ids[1] or parent.get(ids[1]) == ids[0]))}   # a card and its own component are not duplicates
    pubs = cls_count["paper"]
    json.dump(dict(class_counts=cls_count, records=rows, duplicate_title_candidates=dups, conflicts=conflicts),
              open(os.path.join(ROOT, "data/provenance/identity_audit.json"), "w"), ensure_ascii=False, indent=1)
    st = REG["stats"]
    md = ["# Canonical identity audit", "",
          f"Registry: `data/works.json` ({len(rows)} records), built by `scripts/build_registry.py` from the read-only October tree plus `data/registry_overrides.json`. Machine-readable version: `data/provenance/identity_audit.json`.", "",
          "## What the counts mean", "",
          f"- **{len(rows)} unique works and resources** = every distinct thing the survey links to, after merging versions of the same item. It is **not** a count of papers.",
          f"- **{pubs} records classified as scholarly works** (journal, conference, workshop, preprint). Other records: " + ", ".join(f"{CLASS[c].split(' (')[0].lower()}: {n}" for c, n in cls_count.items() if c != "paper") + ".",
          f"- **{st['corpus']}** of the records form the analytic corpus behind the Chapter 1 charts and atlas filters (October 2026 curation, unchanged).",
          "- Record class comes from the October corpus metadata where it exists; otherwise from the URL (arXiv/DOI → paper, company domains → report, etc.) or from a hand-curated override. Heuristic classes are flagged below as uncertain.", "",
          "| Class | Records |", "|---|---|"] + [f"| {CLASS[c]} | {cls_count[c]} |" for c in CLASS if cls_count[c]] + ["",
          "## Merge rules (applied in this order)", "",
          "1. **Card identity.** Every October card keeps its card ID. Its identity keys: the normalized primary URL; pdf/html URLs only when they normalize to the same key (arXiv ID or DOI); URLs in `urls.other` only when labelled as the arXiv/preprint/journal version; arXiv IDs or DOIs written in the card's own version/venue fields.",
          "2. **Normalization.** arXiv abs/pdf/html and vN → `arxiv:<id>`; `doi.org`, `nature.com/articles/…`, `science.org/doi/…`, `pnas.org/doi/…` → `doi:<doi>`; ACL Anthology → `acl:<id>`; anything else → host + path without scheme, `www`, query or fragment.",
          "3. **Synonyms.** Five October alias IDs that named the same card are kept as `aliases`.",
          "4. **Constituents.** Seven October alias IDs that named a specific document inside a bundle card become their own records with `part_of` (they claim their URL keys from the bundle).",
          "5. **Text URLs.** Every URL in the October text is mapped to the record holding its key; unmatched URLs become new records with deterministic IDs.",
          "6. **Conflicts.** If a second record would claim a key already held, the key is not moved; it stays on the first record and is listed on the second as `related_keys` (kept separate, not merged).",
          "7. **Hand-curated records** (`registry_overrides.json`) carry their verification source; identifiers there were read from the arXiv API or the publisher page on 2026-10-09. No identifier was constructed or guessed.", "",
          f"## Records with more than one identity key or text URL ({len(merges)})", "",
          "| Record | Class | Merged keys | Basis per key |", "|---|---|---|---|"]
    for wid, cl, ks, srcs in merges:
        md.append(f"| `{wid}` | {cl} | {'<br>'.join(f'`{k}`' for k in ks)} | {'<br>'.join(srcs.get(k, 'URL in the survey text') for k in ks)} |")
    md += ["", f"## Kept separate because of a key conflict ({len(conflicts)})", ""]
    md += [f"- `{wid}` mentions `{k}` in its own metadata, but that key belongs to another record (`{REG['text_url_map'].get(k) or next((w['id'] for w in REG['works'] if k in (w.get('identity_keys') or [])), '?')}`); the two stay separate (a reply/replication/news item about a paper is not the paper)." for wid, k in conflicts]
    excl = [(w["id"], k, why) for w in REG["works"] for k, why in (w.get("excluded_keys") or [])]
    md += ["", f"## Identifiers excluded from a record after review ({len(excl)})", "",
           "Found in a card's free-text fields or `urls.other`, but they identify a different document; kept as `excluded_keys` with the reason and not counted as part of the record.", ""]
    md += [f"- `{wid}`: `{k}` — {why}" for wid, k, why in excl]
    kept = {k: v for k, v in (OV.get("kept_merge_notes") or {}).items() if not k.startswith("_")}
    md += ["", f"## Multi-key records reviewed and kept merged ({len(kept)})", ""] + [f"- `{k}`: {v}" for k, v in kept.items()]
    cl = REG.get("clusters") or []
    md += ["", f"## Retired cluster records ({len(cl)})", "",
           "October scout records that grouped several works into one table-row card. They are not works; their IDs (announced in `canonical_ids.v0.json`) are retired, and each member row is now its own record.", ""]
    md += [f"- `{c['id']}` → {', '.join('`'+m+'`' for m in c['member_records'])}" for c in cl]
    md += ["", "## Constituent documents and aliases", ""]
    md += [f"- `{r['id']}` → part of `{r['part_of']}`" for r in rows if r["part_of"]]
    md += [f"- `{r['id']}` aliases: {', '.join('`'+a+'`' for a in r['aliases'])}" for r in rows if r["aliases"]]
    md += ["", f"## Possible duplicates by title (review; not merged automatically) ({len(dups)})", ""]
    md += [f"- “{t}”: {', '.join('`'+i+'`' for i in ids)}" for t, ids in sorted(dups.items())] or ["- none"]
    unc = [r for r in rows if r["uncertain"]]
    md += ["", f"## Records with uncertain metadata, retained ({len(unc)})", "",
           "These are kept in the registry and counts; the flag says what is weak.", "", "| Record | Class | Why uncertain |", "|---|---|---|"]
    md += [f"| `{r['id']}` | {r['record_class']} | {'; '.join(r['uncertain'])} |" for r in unc]
    corr = [w for w in REG["works"] if w.get("metadata_corrected")]
    prov = (OV.get("metadata_corrections") or {}).get("_provenance", {})
    md += ["", f"## Source-grounded metadata corrections ({len(corr)})", "",
           f"Complete ordered bylines, restored full titles, journal fields and date/spelling conflicts from metadata task {prov.get('task', '')}; original handoff `{prov.get('original_handoff', '')}` (SHA-256 `{prov.get('original_handoff_sha256', '')}`). These are corrections to existing records, **not new works**; identities and aliases are unchanged. BibTeX name forms are kept verbatim in `authors_bibtex`.", "",
           "| Record | Authors | Title / venue | Preserved conflicts and notes |", "|---|---|---|---|"]
    for w in corr:
        v = w.get("venue") or {}
        tv = f"{w['title']}" + (f" — {v['journal']} {v.get('volume', '')}({v.get('number', '')}): {v.get('pages', '').replace('--', '–')}" if v.get("journal") else "") + (" (date: year only)" if w.get("date_precision") == "year" else "")
        notes = "; ".join((w.get("metadata_conflicts") or []) + ([w["venue_status_note"]] if w.get("venue_status_note") else []) + ([f"earlier title: {t}" for t in w.get("title_variants") or []]))
        md.append(f"| `{w['id']}` | {w['n_authors']} | {tv} | {notes or '—'} |")
    md += ["", "## Post-cut-off identity update", "",
           "- `piao-polarization` (alias `piao-polarization-networks`): arXiv:2501.05171 and DOI 10.1038/s41467-026-78228-y (Nature Communications, 8 Oct 2026) are one record — same title and authors; publisher metadata read 2026-10-09. Counted once.", ""]
    open(os.path.join(ROOT, "data/provenance/IDENTITY_AUDIT.md"), "w", encoding="utf-8").write("\n".join(md))
    print(dict(cls_count), "merges", len(merges), "conflicts", len(conflicts), "dups", len(dups), "uncertain", len(unc))

if __name__ == "__main__":
    main()

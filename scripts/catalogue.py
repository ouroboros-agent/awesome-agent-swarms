#!/usr/bin/env python3
"""The survey's current catalogue: the historical registry plus its dated supplements.

data/works.json is the registry as of the 3 October 2026 cut-off (280 records, 153 of them in the analytic corpus that
the charts of Chapter 1 count). updates/2026-10-19/catalogue.json is that registry with the 19 October supplement
applied: eight added records, two updated, one identifier corrected, every existing id kept (288 records). This module
loads the supplement, checks that it was built on exactly these registry bytes, and gives the site builder:

  works()       the 288 records, in catalogue order, with identity keys for the added ones;
  SUP           what the supplement changed and when it was checked;
  PASSPORTS     bilingual display fields for the changed records (data/i18n/passports_2026-10-19.json).

The analytic corpus is not touched: added records stay outside it, so every chart and count of the 153 works is the
3 October one, and the pages say so where they print it.
"""
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "data", "works.json")
SUPPLEMENT = os.path.join(ROOT, "updates", "2026-10-19", "catalogue.json")
DELTA = os.path.join(ROOT, "updates", "2026-10-19", "registry-delta.json")
PASS_FILE = os.path.join(ROOT, "data", "i18n", "passports_2026-10-19.json")


def _load():
    base_bytes = open(REGISTRY, "rb").read()
    base = json.loads(base_bytes)
    if not os.path.exists(SUPPLEMENT):
        return base, None, {}
    sup = json.load(open(SUPPLEMENT, encoding="utf-8"))
    digest = hashlib.sha256(base_bytes).hexdigest()
    if sup.get("base_registry_sha256") != digest:
        raise SystemExit(f"catalogue: {os.path.relpath(SUPPLEMENT, ROOT)} was built on another registry "
                         f"({sup.get('base_registry_sha256')}), data/works.json is {digest}")
    delta = json.load(open(DELTA, encoding="utf-8"))
    passports = json.load(open(PASS_FILE, encoding="utf-8")) if os.path.exists(PASS_FILE) else {}
    return base, dict(sup=sup, delta=delta), passports


BASE, _SUP, PASSPORTS = _load()


def works():
    """Every record of the current catalogue. Added records get identity keys from their primary URL and arXiv id,
    normalised as the registry does it (scripts/build_registry.py), so links written in the chapters resolve to them."""
    if not _SUP:
        return BASE["works"]
    from build_registry import key as url_key
    out = []
    for w in _SUP["sup"]["works"]:
        if w["id"] in SUP["added"] and not w.get("identity_keys"):
            keys = []
            for k in (url_key((w.get("urls") or {}).get("primary")),
                      f"arxiv:{(w.get('identifiers') or {}).get('arxiv')}" if (w.get("identifiers") or {}).get("arxiv") else None):
                if k and k not in keys:
                    keys.append(k)
            w = dict(w, identity_keys=keys)
        out.append(w)
    return out


def _sup_meta():
    if not _SUP:
        return dict(added=[], updated=[], corrected=[], checked_at=None, total=len(BASE["works"]), base=len(BASE["works"]),
                    analytic=BASE["stats"]["corpus"], coverage="", leads=[], already=[])
    s, d = _SUP["sup"], _SUP["delta"]
    return dict(added=list(s["added_ids"]), updated=list(s["updated_ids"]), corrected=list(s["corrected_ids"]),
                checked_at=s["supplement_checked_at"], total=s["counts"]["total_records"], base=s["counts"]["base_records"],
                analytic=s["counts"]["historical_analytic_corpus"], coverage=s["coverage"],
                leads=[x["arxiv"] for x in d.get("unqualified_leads", [])], already=[x["id"] for x in d.get("already_present", [])],
                new_publications=sum(1 for r in d["records"] if r.get("new_publication")),
                kinds={r["id"]: r.get("kind") for r in d["records"]})


SUP = _sup_meta()


def changed(wid):
    """'added', 'updated', 'corrected' or None for a record id."""
    for k in ("added", "updated", "corrected"):
        if wid in SUP[k]:
            return k
    return None


def passport(wid, lang):
    """Display fields of a changed record in one language ({} for the others)."""
    p = (PASSPORTS.get("records") or {}).get(wid) or {}
    return p.get(lang) or {}


if __name__ == "__main__":
    ws = works()
    print(f"catalogue: {len(ws)} records; analytic corpus {SUP['analytic']} (3 October 2026); "
          f"supplement {SUP['checked_at']}: +{len(SUP['added'])} added, {len(SUP['updated'])} updated, {len(SUP['corrected'])} corrected")
    for wid in SUP["added"] + SUP["updated"] + SUP["corrected"]:
        missing = [l for l in ("ru", "en") if not passport(wid, l)]
        print(f"  {wid}: passports {'ok' if not missing else 'MISSING ' + ','.join(missing)}")

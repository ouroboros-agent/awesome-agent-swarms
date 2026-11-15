# Bibliography notes

The report cites from two BibTeX files. `references.bib` holds the 261 inherited entries derived from the October 2026 research collection; `references-2026-11.bib` holds the 35 entries added for the November 2026 edition. `main.tex` loads both, and `scripts/build_paper_qa.py` fails if a key appears in both files or a citation does not resolve. Compilation needs only these files and the vendored ACL style; it does not need the research archive.

## Keys and identities

Keys are the catalogue's canonical record IDs. A bundle of related documents in the collection is not cited as a single invented publication: each cited document has its own key, and `citation-key-map.json` records its `part_of` bundle, the source card it came from, and inherited metadata status. Bundle identifiers and old aliases remain corpus identities and are not reused as keys for different publications. Entry counts are bibliography sizes, not counts of independent studies.

## Inherited entries (`references.bib`)

`references.bib` is written by `scripts/build_paper_bibliography.py`, which reads the preserved October research cards and is not part of the portable build. The generator also applies the version notes of four entries listed below, so a regeneration keeps them. Published versions with an explicit journal record use their journal year and identifiers; arXiv-first dates are not substituted for known publication dates, and no proceedings metadata is guessed for preprints whose later venue is not fully specified.

Eighteen entries had incomplete bylines in the inherited cards. On 9 October 2026 their complete ordered bylines, exact titles and dates were read from primary arXiv, publisher and journal pages. Entries completed: `agentworm`, `attributing-emergence`, `co-scientist-nature`, `compass-kilo-flocks`, `conformity-no-speaker`, `emergent-languages`, `human-ai-consensus`, `moltbook-form-without-function`, `moltbook-observatory`, `multi-agent-security-tax`, `naming-games`, `openclaw-norms`, `orchestra-o1`, `robin-futurehouse`, `science-malicious-swarms`, `structured-opinion-dynamics`, `topological-collapse`, `zombie-agents`.

Titles restored to their full primary form: `conformity-no-speaker` (subtitle *Measuring the Speaker-Free Floor in Peer-Pressure Benchmarks*), `moltbook-observatory` (subtitle *an incremental dataset of agent-only social network activity*), `multi-agent-security-tax` (*Trading Off Security and Collaboration Capabilities in Multi-Agent Systems*). Status notes added only where the arXiv comments state them: Security Tax, `Accepted to AAAI 2025 (per arXiv comments)`; Zombie Agents, `Published as a workshop paper in Lifelong Agent @ ICLR 2026 (per arXiv comments)` — a workshop, not the ICLR main conference. Orchestra-o1 gains the DOI shown in its primary metadata, `10.48550/arXiv.2606.13707`. No proceedings or journal fields were invented.

Conflicts kept as recorded, not resolved by guesswork:

- `multi-agent-security-tax`: the paper byline reads *Pierre Peigné*; the abstract metadata reads *Pierre Peigne-Lefebvre* and the uploader field *Pierre Peigné-Lefebvre*. The paper byline is used.
- `moltbook-form-without-function`: arXiv submission history 2026-03-17 versus manuscript date 2026-04-16; year only is cited. The abstract page spells *Mitrovic*, the paper *Mitrović*; the paper is followed.
- `moltbook-observatory`: displayed submission 2026-04-16 conflicts with the `2605` identifier prefix; year only is cited.
- `agentworm`: an NDSS footer with a placeholder DOI is not sufficient for proceedings metadata; the entry stays a preprint.
- `science-malicious-swarms`: the publisher page returned HTTP 403; the byline was read from the journal-formatted PDF and corroborated by arXiv:2506.06299 author metadata.
- `robin-futurehouse`: the journal title is used; the earlier "Robin:" preprint title belongs to another version.
- `topological-collapse`: the inherited card had reversed given and family names; the arXiv order is used.

On 9 October 2026 the inherited bibliography was also reconciled, read-only, with the catalogue registry `data/works.json` and its identity audit:

- All **261** BibTeX keys exist as exact canonical record IDs; none needs an alias or identifier lookup.
- No arXiv identifier or DOI in `references.bib` disagrees with the registry's identifiers or identity keys (the arXiv-issued DOI `10.48550/arXiv.2606.13707` is treated as an arXiv identifier).
- Every `part_of` value in `citation-key-map.json` equals the registry's `part_of`. The registry has since retired the three `prev-*-cluster` bundles as works; the paper never cites them, and the map keeps them only as `part_of` provenance.
- The 18 entries completed above have the same author counts and exact titles in the registry.
- In `IDENTITY_AUDIT.md`, the "Multi-key records reviewed and kept merged" list in `IDENTITY_AUDIT.md` names `piao-polarization-networks`, which is not a record in `works.json`; the record is `piao-polarization`. The paper uses `piao-polarization`.

## November 2026 additions (`references-2026-11.bib`)

- Thirty-five entries, maintained by hand; the generator never writes this file. Thirty-four are works from the additions of 19 October and 7--12 November 2026; `worse-together-blog` is the 11 November blog version of an inherited preprint. Keys equal the record IDs in the site's BibTeX (`updates/2026-10-19/references.bib`, `updates/2026-11-12/references.bib`), so the PDF and the site cite the same identifiers.
- Author lists are complete as printed by each primary source: arXiv metadata, the Avalon-M1 title page, the byline of the Fable 5.2 post, and the COLLABMEM record of the ACL Anthology. The site's shortened author fields ("and others") are not used here.
- Four inherited entries name the version read: `multi-agent-transactive-memory` (v2, 15 October), `safety-of-latent-communication` (v3, 5 October; the cited result is present from v2), `worse-together` (v1, 30 September), and `voluntary-collusion-secret-tools` (v2, 5 October, whose Tables 2–3 give the framing comparison).
- De Marzo is written `De Marzo, Giordano` in both files, the form the generator uses, so natbib assigns consistent year suffixes to his four cited works.
- `collabmem-2026` uses DOI `10.18653/2026.emnlp-main.1194`, as listed in the Anthology's own BibTeX for the paper; on 15 November 2026 doi.org redirected this DOI to the Anthology page, while the same identifier with a `v1/` segment returned HTTP 404.
- `steering-information-networks` (arXiv:2611.11714) records a preprint withdrawn by its authors on 10 November 2026; the report cites it only to say that its results are not used.
- The November keys are not added to `citation-key-map.json`, which documents the inherited keys.

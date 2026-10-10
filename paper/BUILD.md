# Build and inspect the technical report

The editable entry point is `main.tex`; the delivered PDF is `swarm-dynamics.pdf`. `swarm-dynamics-source.zip` contains the portable project (including the PDF, all 52 figure assets in original and display form, and the vendored ACL files with their license notices); extract it and run the build from the directory containing `paper/` and `scripts/`. It excludes regenerable caches: `paper/build/`, page renders and contact sheets, `qa/text-bounds.html`, `qa/swarm-dynamics.txt`, figure contact sheets, and the `qa/pre-apply/` history. This is a self-published technical report by Anton Razzhigaev and Ouroboros, explicitly identified as a human–AI collaboration. The ACL layout does not imply submission, acceptance, or endorsement. No affiliation, ORCID, or email was inferred.

## Rebuild from the repository root

Install a current TeX Live or MacTeX distribution with `latexmk`, pdfLaTeX, BibTeX, and the packages used by `main.tex`. Then run:

```sh
./scripts/build_paper.sh
```

The script resolves the repository relative to itself, sets the official vendored style/bibliography search paths, compiles with fatal-error handling, and copies `paper/build/main.pdf` to `paper/swarm-dynamics.pdf`. The ordinary build is self-contained: no source archive, API credentials, network, external corpus checkout, or Overleaf project is required. `LATEXMK_BIN` can select another latexmk executable; the macOS Homebrew path is an automatic fallback.

The official ACL files are unchanged and pinned to upstream commit `d5adc823ff0f80f98c80405ca0ab66c68e684409`. Their URLs and SHA-256 hashes are in `vendor/upstream.json`; original license notices and the LPPL reference text are preserved. See `vendor/LICENSE-NOTES.md` for the precise file-level treatment. The official style sets `acl_natbib` itself, so do not add a second bibliography-style command.

## Delivered build

The final PDF contains **57 pages**: main synthesis **1–18**, references **19–25**, evidence coding and gaps **26–39**, complete analytical inventory **40–47**, and selected source figures **48–57**. It was compiled with latexmk 4.87, pdfTeX 1.40.29 (TeX Live 2026/Homebrew), and BibTeX 0.99e. Poppler produced the page renders.

The final log has zero LaTeX, natbib, or BibTeX warnings, zero missing characters, and zero overfull boxes. It retains **46 underfull-box spacing diagnostics**. All 171 cited keys resolve in the 261-entry local bibliography; all fonts are embedded. Original QA logs and visual-review records are retained outside the release export. Running the verifier below produces new local QA records.

## Files and regeneration

- `sections/*.tex`: the scholarly synthesis, taxonomy, comparisons, limitations, and authorship statement.
- `references.bib`: paper-local bibliography. `citation-key-map.json` preserves inherited keys, aliases, and proposed constituent-work IDs. `bibliography-notes.md` describes metadata gaps and reconciliation needed by the canonical corpus owner.
- `evidence-matrix.json`: manually coded analytical evidence units. `corpus-inventory.json`: the byte-identical 153-record administrative inventory; Appendix C shows its values unchanged, with bracketed qualifiers from its own scale notes where a value is not a within-run concurrent count. These are different units and must not be added into a publication count.
- `appendix-evidence.tex`: render with `python3 scripts/build_paper_evidence.py`; this needs only repository files and the Python standard library.
- `figures/legacy/` and `figures/print/`: all 52 logical inherited assets, each with an original and display copy. `figure-rights.json` records source, caption, rights, and hashes. Copies are not additional figures.
- `figures/taxonomy.tex` and `figures/coordination-layers.tex`: original vector diagrams. Rebuild with `python3 scripts/build_paper_figures.py`; it requires pdfLaTeX. The compiled vectors are already included for an ordinary paper build.
- `appendix-figures.tex`: selected source figures with explanatory English captions and individual attribution.
- `source-provenance.json`: archive-relative locators and observed hashes for the six author files; private editorial records are excluded.

Bibliography regeneration is optional and requires the preserved read-only research archive and the supplied corpus interface. It is not part of the portable compilation path. See `scripts/build_paper_bibliography.py --help` before using it. The bibliography is a local derived artifact, not a replacement for the catalogue builder's canonical `data/works.json`.

## Verification

After compilation, install Poppler (`pdftotext`, `pdffonts`, `pdfinfo`, `pdftoppm`) and run:

```sh
python3 scripts/build_paper_qa.py
```

To regenerate all page previews and four-page contact sheets, also install Pillow in that Python environment and run:

```sh
python3 scripts/build_paper_qa.py --render
```

The check records PDF identity, page boundaries, citations, warning counts, embedded fonts, text bounds, figure hashes, official-template hashes, and exact-once rendering of both evidence tables. It fails on unresolved citations, missing characters, overfull boxes, or a failed integrity check. Underfull-box spacing diagnostics are retained and reviewed visually. Automatic checks do not establish readability. The original page-inspection records and build receipts are retained with the authors outside this clean export; they are not bundled here. The verifier creates fresh machine-readable QA locally, but a new visual review must record its own coverage.

## Scope and remaining limits

This is a structured narrative synthesis of the existing October research, with explicit evidence coding. It is not a preregistered systematic review, a fresh broad search, an independent re-audit of every primary source, or a report of new experiments. Two targeted additions within the cutoff cover the RHEON paper (30 September) and the contagion-kernel paper (2 October); Piao's 8 October journal publication updates the existing work's metadata.

The 18 bylines previously left incomplete were completed from primary arXiv, publisher and journal pages on 9 October 2026; source-date and spelling conflicts are kept per key in `citation-key-map.json` and listed in `bibliography-notes.md`. Component-ID proposals still require integration by the canonical corpus owner. The 153 metadata records, 147 source cards, and bibliography-entry total are not verified unique-publication counts.

Third-party images retain their specific rights. All 52 are preserved in this private candidate as requested; an archived attribution note does not create a blanket redistribution license. Selected source panels retain their original labels; historical Russian dashboards remain available as archive assets. The two new conceptual diagrams and the report's original prose are distinct from these third-party materials. No publication, repository push, venue submission, or claim of independent acceptance is included in this delivery.

# Figure provenance and build notes

The paper's source package preserves all **52** unique `!fig` assets referenced by the current six author Markdown files: 7 in `front.md`, 12 in `w1_t5_t1.md`, 12 in `w2_t3_wild.md`, 9 in `w3_t2_incident.md`, and 12 in `w4_t4_beliefs.md`; none in `back.md`. Source: the preserved October 4 state of `swarm-dynamics-20261003`.

`figures/legacy/` contains byte-identical copies of the 52 source PNGs. `figures/print/` contains the current archived margin-trimmed variants when available, except the CC BY-NC-ND Kimi figure, for which the unmodified original is used. There are 52 logical assets, not 104 independent figures. Each original and display copy has a SHA-256 recorded in `figure-rights.json`, together with exact source-file locations, inherited captions, figure-specific URLs, English descriptions, and rights notes. No source image was newly recolored, translated, relabelled, or cropped in this task.

Rights information is inherited from the verified October source cards and figure catalog. It is not a new permission grant or a new independent licensing audit. “Attributed quotation” in an archived note is preserved as a historical rationale, not adopted as proof of unrestricted reuse. The owner authorized keeping all figures in the source package. Third-party figures retain their individual rights; no repository-wide license overrides them.

`appendix-figures.tex` contains seventeen explanatory source figures: fifteen inherited and two added in November 2026. Captions state the task, variables or controls, observation, and limits of interpretation. The selection, together with the main-text Park communication figure, covers fixed-budget scaling, communication overhead, externalized context, task variability, learned collaboration strategies, mixed organization origins, artifact-mediated conventions, realized organization, alignment tradeoffs, heterogeneous responses to misconduct, peer preservation, temporal incident activity, diversity measurement, semantic collapse, faction formation, and biased consensus. Unselected assets remain in the source package with their provenance records.

The six archived dashboards use **153 metadata records**, not a verified count of unique publications. The paper atlas does not reproduce their aggregate counts as coverage claims. Historical Russian labels remain in archived originals; the new conceptual diagrams and atlas captions are English.

## Original vector diagrams

- `figures/taxonomy.pdf` and `.tex`: the report's eight-dimensional taxonomy, including concurrent, cumulative, and configured-capacity scale.
- `figures/coordination-layers.pdf` and `.tex`: graph, exchange medium, and organization origin as distinct descriptors. Direct messaging and shared artifacts are conceptual examples, not measurements.

These two diagrams are original conceptual syntheses by Anton Razzhigaev and Ouroboros, licensed CC BY 4.0. Their light-background vector PDFs were compiled with `pdflatex` and rasterized with `pdftoppm` for visual inspection. No clipping, overlaps, or missing labels were observed in those previews. The PNG previews are convenience copies; the manuscript should embed the vector PDFs.

Rebuild the original diagrams from the repository root:

```sh
python3 scripts/build_paper_figures.py
```

The script needs Python 3.9+ and `pdflatex` (`/opt/homebrew/bin/pdflatex` is used as a fallback). To regenerate the archive-preservation step, supply `--source` with the read-only archive path. The normal repository build does not need that archive; all referenced image assets are already included.

## Source distinctions to retain

- `kim-scaling-agent-systems_fig3.png` and `_fig4.png` come from **arXiv v2**, recorded as CC BY 4.0, not the later journal image version.
- `artificial-hivemind_fig1.png` is Jiang et al., arXiv:2510.22954. `_fig5.png` is **Schaeffer et al.'s reevaluation**, arXiv:2609.33936. A combined source card must not erase this attribution difference.
- `attractor-states_fig1.png` is Ko and Geiping's arXiv paper; `_fig4.png` is an Anthropic system-card transcript.
- `hf-incident-case_fig1.png` and `_fig2.png` are from **METR and Redwood Research's investigation**, although the composite card's primary link is an OpenAI incident account.
- `cursor-scaling_fig1.png` and `_fig2.png` both come from **Towards self-driving codebases**, the second Cursor post; their bibliography key is `cursor-self-driving`.
- `anthropic-c-compiler_fig2.png` is an **original archived review calculation** from repository history, not a company-supplied figure. The underlying data are recorded as CC0-1.0.

Full-manuscript pagination and page-level visual checks are recorded with each build. The diagram previews alone do not establish readability of every source plot at its eventual printed size.

All 52 display variants were opened as contact sheets in October 2026; no missing, blank, or obviously corrupt image was observed. This checks asset completeness and gross rendering only. Dense source panels require full-width placement; the atlas gives additional height to SAT, Agensh task panels, and semantic-collapse interventions.

The main text uses `taxonomy.pdf`, `coordination-layers.pdf`, the paper variant of the survey scale chart (`figures/charts/dash_scale_en_light.png`, built by `scripts/build_paper_scale_chart.py` from the same data), and `test-time-communication_fig3.png`; the atlas omits the latter to avoid duplicate reproduction.

Correction pass, 9 October 2026: the taxonomy diagram's scale box now uses the main-text notation $N_{\mathrm{conc}}(t)$, $N_{\mathrm{cum}}(T)$ and $N_{\mathrm{cap}}$ instead of $N(t)$, $U$, $K$; the coordination diagram's narrow graph label was shortened to "Contact is not enough. Timing and content determine what propagates." Both PDFs and their preview PNGs were rebuilt with `python3 scripts/build_paper_figures.py`. No third-party image changed; the 52 asset hashes still match `figure-rights.json`. Reader-facing appendix text no longer refers to internal working states; this file and `RIGHTS.md` keep the rights record.

November 2026 edition: two open-licensed source figures were added to the atlas from works read at their primary sources, `figures/refresh/parallel-agent-teams_fig1.png` (arXiv:2611.09798v1, Figure 1) and `figures/refresh/scalemas-substrate_fig2.png` (arXiv:2610.16120v1, Figure 2). Both are CC BY 4.0 and byte-identical to the source PNGs. Their records are in `figure-rights-refresh.json`, kept apart from `figure-rights.json`, which `build_paper_figures.py --source` regenerates for the 52 inherited figures; `build_paper_qa.py` checks the hashes in both manifests. The atlas has 17 source-image floats; several share a page.


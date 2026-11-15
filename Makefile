PY ?= .venv/bin/python
S ?= research-archive

.PHONY: all site field check charts catalog registry preserve qa qa-features qa-regress qa-field coverage
all: charts site field catalog check

venv:
	python3 -m venv .venv && $(PY) -m pip install -r requirements.txt

registry:            ## rebuild data/works.json from the October tree (read-only)
	$(PY) scripts/build_registry.py $(S)
	$(PY) scripts/build_figures_registry.py $(S)
	$(PY) scripts/identity_audit.py $(S)
	$(PY) scripts/preservation_map.py $(S)

charts:              ## the survey's own corpus charts (assets/charts/) and the README's variant of the scale chart (assets/readme/)
	$(PY) scripts/build_charts.py
	$(PY) scripts/build_readme_scale_chart.py

site:                ## site/: the Field pages (index.html), the detailed survey of 19 October (survey-2026-10-19.html), former addresses, root page
	$(PY) scripts/build_site.py --check

field:               ## delivery/Swarm-Field-RU.html and -EN.html: the self-contained Field files (also rewrites site/<lang>/index.html)
	$(PY) scripts/build_field.py

catalog:
	$(PY) scripts/build_catalog.py
	$(PY) scripts/build_readme.py

check:               ## syntax + RU/EN parity; scene numbers against their cards and the consensus toy recomputed (needs the built site); Field parity, map and exports
	$(PY) scripts/check_content.py
	$(PY) scripts/check_scenes.py
	$(PY) scripts/check_field.py

coverage:            ## every card, figure, link, heading and block is on the single page (OLD=<dir>: a former multipage build; PREV=<dir>: the previous single-page edition)
	$(PY) scripts/check_coverage.py $(if $(OLD),--old $(OLD)) $(if $(PREV),--prev $(PREV))

preserve:            ## RU preservation against the October source (needs S)
	$(PY) scripts/check_content.py --source $(S) --no-parity

qa:                  ## real-browser checks of the single page (Chrome + WebKit; phone, desktop, wide; no-JS; former pages forward)
	$(PY) scripts/qa_browser.py

qa-features:         ## scenes move/stop/pause, reduced motion, language keeps the place, Back, viewer, atlas, README render
	$(PY) scripts/qa_features.py

qa-field:            ## the Field pages and exports from file:// in Chromium and WebKit (desktop, phone, no-JS, reduced motion, map, keyboard, language link); OUT=<dir>
	$(PY) scripts/qa_field.py $(OUT)

qa-regress:          ## the defects found in the final reviews stay fixed: atlas place after search/filter/reset, scenes settle in every layout, theme and skip focus keep the place, no-JS former-page entries, λ labels, phone legend
	$(PY) scripts/qa_regress.py

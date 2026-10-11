PY ?= .venv/bin/python
S ?= research-archive

.PHONY: all site check charts catalog registry preserve qa qa-features qa-regress coverage
all: charts site catalog check

venv:
	python3 -m venv .venv && $(PY) -m pip install -r requirements.txt

registry:            ## rebuild data/works.json from the October tree (read-only)
	$(PY) scripts/build_registry.py $(S)
	$(PY) scripts/build_figures_registry.py $(S)
	$(PY) scripts/identity_audit.py $(S)
	$(PY) scripts/preservation_map.py $(S)

charts:
	$(PY) scripts/build_charts.py

site:
	$(PY) scripts/build_site.py --check

catalog:
	$(PY) scripts/build_catalog.py
	$(PY) scripts/build_readme.py

check:               ## syntax + RU/EN parity; scene numbers against their cards and the consensus toy recomputed (needs the built site)
	$(PY) scripts/check_content.py
	$(PY) scripts/check_scenes.py

coverage:            ## every card, figure, link, heading and block is on the single page (add OLD=<dir> to compare with a former build)
	$(PY) scripts/check_coverage.py $(if $(OLD),--old $(OLD))

preserve:            ## RU preservation against the October source (needs S)
	$(PY) scripts/check_content.py --source $(S) --no-parity

qa:                  ## real-browser checks of the single page (Chrome + WebKit; phone, desktop, wide; no-JS; former pages forward)
	$(PY) scripts/qa_browser.py

qa-features:         ## scenes move/stop/pause, reduced motion, language keeps the place, Back, viewer, atlas, README render
	$(PY) scripts/qa_features.py

qa-regress:          ## the defects found in the final reviews stay fixed: atlas place after search/filter/reset, scenes settle in every layout, theme and skip focus keep the place, no-JS former-page entries, λ labels, phone legend
	$(PY) scripts/qa_regress.py

PY ?= .venv/bin/python
S ?= research-archive

.PHONY: all site check charts catalog registry preserve qa qa-features
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

check:               ## syntax + RU/EN parity
	$(PY) scripts/check_content.py

preserve:            ## RU preservation against the October source (needs S)
	$(PY) scripts/check_content.py --source $(S) --no-parity

qa:                  ## real-browser checks (Chromium via Chrome + WebKit), desktop and phone
	$(PY) scripts/qa_browser.py

qa-features:         ## scene movement, viewer, theme, language, parity, 52 figures, README render (Chromium + WebKit)
	$(PY) scripts/qa_features.py

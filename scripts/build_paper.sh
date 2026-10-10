#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT/paper"
LATEXMK_BIN=${LATEXMK_BIN:-latexmk}
if ! command -v "$LATEXMK_BIN" >/dev/null 2>&1; then
  if [[ -x /opt/homebrew/bin/latexmk ]]; then LATEXMK_BIN=/opt/homebrew/bin/latexmk; else
    echo 'latexmk is required (TeX Live or MacTeX).' >&2; exit 1
  fi
fi
export TEXINPUTS="$PWD/vendor:${TEXINPUTS:-}"
export BSTINPUTS="$PWD/vendor:${BSTINPUTS:-}"
mkdir -p build
"$LATEXMK_BIN" -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex
cp build/main.pdf swarm-dynamics.pdf

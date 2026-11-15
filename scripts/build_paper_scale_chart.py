#!/usr/bin/env python3
"""Build the paper's variant of the survey's scale chart (Figure 2 of the report).

Same data and plotting code as scripts/build_charts.py (the frozen 3 October inventory in
data/works.json); only the legend wording and one label offset differ, so the legend describes
the inventory's historical classes instead of measured simultaneous inference, and the
"C compiler" label clears a neighbouring marker. Writes paper/figures/charts/dash_scale_en_light.png.
Requires matplotlib (see requirements.txt); the survey's own charts are not touched.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_charts as C  # noqa: E402

PAPER_LEGEND = [["", "largest reported population in one run or system"],
                ["", "accumulated over the whole period"],
                ["", "stated platform capacity"]]


def main():
    out = os.path.join(C.ROOT, "paper", "figures", "charts")
    os.makedirs(out, exist_ok=True)
    C.SCALE_LEGEND = PAPER_LEGEND
    C.LABEL_POS = dict(C.LABEL_POS, **{"anthropic-c-compiler": (-6, -31, "right"), "openai-navier-stokes": (-8, 25, "right")})
    C.OUT = out
    T = C.THEMES["light"]
    C.setup(T)
    name = C.scale_map(T, "en", "light")
    print("wrote", os.path.join("paper", "figures", "charts", name))


if __name__ == "__main__":
    main()

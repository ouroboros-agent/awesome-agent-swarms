#!/usr/bin/env python3
"""Build the README's variant of the survey's scale chart: assets/readme/dash_scale_<lang>_<theme>.png.

Same data and plotting code as scripts/build_charts.py (the frozen 3 October inventory in data/works.json), with the
legend wording and label offsets of the report's Figure 2 (scripts/build_paper_scale_chart.py), in both languages
and themes. Filled points are the largest population a source reports for one run or system; that class mixes live
runs, simulations with surrogate models and whole platforms, so the legend does not call it simultaneous. The survey's
own charts in assets/charts/, which the dated survey of 19 October shows, are not touched.
Requires matplotlib and, for the committed bytes, the Inter font that build_charts.py looks for.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_charts as C  # noqa: E402

LEGEND = [["наибольшая указанная популяция в одном прогоне или системе", "largest reported population in one run or system"],
          ["накопленным итогом за всё время", "accumulated over the whole period"],
          ["заявленная ёмкость платформы", "stated platform capacity"]]
LABEL_POS = {"anthropic-c-compiler": (-6, -31, "right"), "openai-navier-stokes": (-8, 25, "right")}   # as in Figure 2


def main():
    out = os.path.join(C.ROOT, "assets", "readme")
    os.makedirs(out, exist_ok=True)
    C.SCALE_LEGEND = LEGEND
    C.LABEL_POS = dict(C.LABEL_POS, **LABEL_POS)
    C.OUT = out
    for th, T in C.THEMES.items():
        C.setup(T)
        for lang in ("en", "ru"):
            print("wrote", os.path.join("assets", "readme", C.scale_map(T, lang, th)))


if __name__ == "__main__":
    main()

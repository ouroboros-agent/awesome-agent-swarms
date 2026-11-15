#!/usr/bin/env python3
"""Photograph every state of the Field page at one window size: the first screen's four schemes, its second state, the
pull-out to 1,024 agents, and each of the 36 steps after its figure has settled.

  python scripts/showcase/survey.py OUT --page site/ru/index.html --size 432x768@2.5 --phone [--engine webkit]
         [--settle 2.6] [--name NAME] [--cap 2.5]

Each frame is taken on the deterministic clock (vclock.js) `--settle` seconds after arriving at the state, so the same
command gives the same pictures. Output: OUT/<name>/*.png, OUT/<name>/sheet.png (all frames on one sheet) and
OUT/<name>/survey.json (the scroll position of every frame and anything the browser complained about).
"""
import argparse
import json
import math
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage  # noqa: E402


def sheet(paths, out, cols, tw):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    w0, h0 = ims[0].size
    th = round(h0 * tw / w0)
    rows = math.ceil(len(ims) / cols)
    sh = Image.new("RGB", (cols * tw + (cols + 1) * 6, rows * th + (rows + 1) * 6), (40, 42, 44))
    for i, im in enumerate(ims):
        r, c = divmod(i, cols)
        sh.paste(im.resize((tw, th), Image.LANCZOS), (6 + c * (tw + 6), 6 + r * (th + 6)))
    sh.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--page", required=True)
    ap.add_argument("--size", required=True, help="WxH@DPR in CSS px, e.g. 432x768@2.5")
    ap.add_argument("--phone", action="store_true")
    ap.add_argument("--engine", default="chromium")
    ap.add_argument("--settle", type=float, default=2.6)
    ap.add_argument("--name")
    ap.add_argument("--cap", type=float, default=0, help="raise the canvas resolution cap to this (0: leave the page as it is)")
    a = ap.parse_args()
    wh, dpr = a.size.split("@")
    w, h = (int(v) for v in wh.split("x"))
    dpr = float(dpr)
    name = a.name or f"{a.engine}-{w}x{h}"
    out = os.path.join(os.path.abspath(a.out), name)
    os.makedirs(out, exist_ok=True)
    page = stage.capture_copy(a.page, out, a.cap) if a.cap else a.page
    n = round(a.settle * 60)
    shots, log = [], []
    with sync_playwright() as p:
        b, ctx, pg, problems = stage.open_page(p, a.engine, page, w, h, dpr, phone=a.phone)
        pg.evaluate("__vc.run(40)")
        f = stage.page_facts(pg)
        H, hx = f["H"], f["hx"]

        def take(key, y, pre=""):
            pg.evaluate(f"(() => {{ {pre} return __vc.run({n}, undefined, {y}); }})()")
            path = os.path.join(out, f"{len(shots):02d}-{key}.png")
            pg.screenshot(path=path)
            shots.append(path)
            log.append(dict(frame=os.path.basename(path), y=y))

        for m in range(4):
            take(f"scheme{m + 1}", 0, f"scrollTo(0, 0); document.querySelectorAll('.tab')[{m}].click();")
        take("delivered-vs-read", round(hx + H * 1.0))
        take("pull-out-mid", round(hx + H * 2.3))
        take("pull-out-end", round(hx + H * 2.9))
        for k, top, hh in f["steps"]:
            take(k, top)
            if hh > 1.8 * H:                      # a long step (the map, the finale): also its middle and end
                take(k + "-mid", round(top + (hh - H) * 0.5))
                take(k + "-end", round(top + (hh - H) * 0.95))
        json.dump(dict(page=a.page, engine=a.engine, version=b.version, size=a.size, phone=a.phone, facts={k: v for k, v in f.items() if k != "step"},
                       frames=log, problems=problems, clock_log=pg.evaluate("__vc.log")), open(os.path.join(out, "survey.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        b.close()
    sheet(shots, os.path.join(out, "sheet.png"), 8 if h > w else 5, 230 if h > w else 400)
    print(f"{name}: {len(shots)} frames -> {out}; problems: {len(problems)}")


if __name__ == "__main__":
    main()

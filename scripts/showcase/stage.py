"""Shared by the showcase scripts: open the Field page in a real browser engine on the deterministic clock.

The page is opened from its file (file://). Nothing is installed or fetched: the engines are the ones Playwright already
has (PLAYWRIGHT_BROWSERS_PATH), and any request other than file:, data:, about: or blob: is refused and recorded.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CAP = "Math.min(devicePixelRatio || 1, 2)"       # field.js: the canvas is drawn at no more than two device px per CSS px


def vclock():
    return open(os.path.join(HERE, "vclock.js"), encoding="utf-8").read()


def capture_copy(page, workdir, cap):
    """A copy of the page for capture, with one edit: the canvas resolution cap is raised from 2 to `cap`, so that the
    canvas is drawn at the capture resolution instead of being drawn at 2x and stretched. Geometry, timing and every
    drawing call stay the page's own. The copy is kept in `workdir`, next to the frames taken from it."""
    src = open(page, encoding="utf-8").read()
    if src.count(CAP) != 1:
        raise SystemExit(f"{page}: expected exactly one canvas resolution cap ({CAP}), found {src.count(CAP)}")
    out = os.path.join(workdir, "capture-" + os.path.basename(page))
    os.makedirs(workdir, exist_ok=True)
    open(out, "w", encoding="utf-8").write(src.replace(CAP, f"Math.min(devicePixelRatio || 1, {cap:g})"))
    return out


def open_page(p, engine, page, w, h, dpr, phone=False, reduced=False, clock=True, extra_init=()):
    """-> (browser, context, page, problems). `problems` collects console errors, page errors and refused requests."""
    b = getattr(p, engine).launch()
    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=dpr)
    if phone:
        kw["has_touch"] = True
        if engine == "chromium":
            kw["is_mobile"] = True
    if reduced:
        kw["reduced_motion"] = "reduce"
    ctx = b.new_context(**kw)
    ctx.set_default_timeout(120000)
    for s in extra_init:
        ctx.add_init_script(s)
    if clock:
        ctx.add_init_script(vclock())
    problems = []
    ctx.route("**/*", lambda route: (problems.append("request: " + route.request.url[:160]), route.abort()) if not route.request.url.startswith(("file:", "data:", "about:", "blob:")) else route.continue_())
    pg = ctx.new_page()
    pg.on("console", lambda m: problems.append("console: " + m.text[:240]) if m.type == "error" else None)
    pg.on("pageerror", lambda e: problems.append("pageerror: " + str(e)[:240]))
    pg.goto("file://" + os.path.abspath(page), wait_until="load")
    return b, ctx, pg, problems


STEPS = "[...document.querySelectorAll('.step')].map(e => [e.id, Math.round(e.getBoundingClientRect().top + scrollY), e.offsetHeight])"
# Where a reader arrives at a step. A card whose text is taller than its box keeps the box and moves the text inside with the
# page (field.js fitCards: class ov, the box's height in max-height); at the step's top that text is already past its first
# lines. The page's own arrival by address (field.js arrive) stands where the text is at its first line: the same place here.
ARRIVE = ("Object.fromEntries([...document.querySelectorAll('.step')].map(e => { const c = e.querySelector('.card'), top = e.getBoundingClientRect().top + scrollY;"
          " return [e.id, c.classList.contains('ov') ? Math.ceil(top - (innerHeight - 8 - parseFloat(c.style.maxHeight)) + 0.1 * innerHeight) + 1 : Math.round(top)]; }))")


def page_facts(pg):
    """Where things are on this page at this window size: the steps, the window, the first screen's excess."""
    f = pg.evaluate("({W: innerWidth, H: innerHeight, dpr: devicePixelRatio, doc: document.documentElement.scrollHeight,"
                    " hx: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--hx')) || 0,"
                    " steps: " + STEPS + ", arrive: " + ARRIVE + "})")
    f["step"] = {k: (top, hh) for k, top, hh in f["steps"]}
    return f


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

#!/usr/bin/env python3
"""Render a showcase video of the Field page from real browser frames.

  python scripts/showcase/render.py OUT --kind mobile            # 1080x1920, WebKit, phone layout (432x768 CSS px)
  python scripts/showcase/render.py OUT --kind desktop           # 1920x1080, Chromium, desktop layout (1280x720 CSS px)
         [--board tour|teaser] [--lang ru] [--page FILE] [--engine webkit|chromium] [--fps 60] [--preview] [--strip 15] [--crf 15]

Two storyboards (--board). `tour`, the default: every part of the page in under 25 s (the four schemes of the first
screen, delivered is not read, the pull-out to 1,024, then each of the six scenes that follow); the run fails if a part
is not on screen in the frames it took. `teaser`: the selection of 15 November 2026 (the first screen, the scale, the
Agensh curve, a self-spreading idea, the map), kept as it was.

How a video is made
  * The page is opened from its file in a real engine and driven by scripts/showcase/vclock.js: one call advances the
    page's own clock by one frame, the page draws that frame itself, and the frame is photographed. No frame is drawn or
    retouched outside the browser, and nothing is laid over the picture.
  * The "camera" is the reader's scroll position: eased moves inside one part of the page, and a jump (scrollTo) between
    distant parts, where the page itself re-forms its 1,024 dots into the next figure.
  * The page's clock may run faster than the video's (SPEED): a time-lapse of the page's own animation, the same for
    the canvas, the CSS transitions and the tab strip. The storyboard (board()) lists every move, jump and speed.
  * For the phone video the canvas resolution cap of the page (2 device px per CSS px) is raised to the capture scale
    (stage.capture_copy), so the canvas is drawn at 1080x1920 instead of being stretched. The desktop video needs no edit.

Output in OUT, with <name> = tour-<kind>-<lang> (teaser: <kind>-<lang>): swarm-dynamics-<name>.mp4 (H.264, yuv420p,
faststart), <name>.timeline.json (every frame: video time, page time, scroll position, scheme tab, active step; every
shot and every part of the page with the frames that show it), stills/ (full-size frames), <name>.strip.png.
The lossless master is written to the folder named by --work (default: OUT/work) and can be deleted.
"""
import argparse
import bisect
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stage  # noqa: E402

KINDS = {
    #          CSS window    scale  phone  engine      canvas cap
    "mobile": ((432, 768), 2.5, True, "webkit", 2.5),
    "desktop": ((1280, 720), 1.5, False, "chromium", 0),
}
SCHEME_END = (6.55, 4.0, 5.95, 4.3)     # seconds of page time by which each scheme has shown its whole action
SCHEME_DUR = (7.6, 6.6, 7.8, 7.0)       # field.js MODES[].dur: the page moves on to the next scheme by itself


def ease(u):
    """Smootherstep: starts and ends at rest."""
    u = 0.0 if u < 0 else 1.0 if u > 1 else u
    return u * u * u * (u * (6 * u - 15) + 10)


class Board:
    """A storyboard in video seconds: where the scroll position is, how fast the page's clock runs, what happens when."""

    def __init__(self):
        self.t = 0.0
        self.y = 0.0
        self.moves = []      # (t0, t1, y0, y1): eased; a jump has t0 == t1
        self.speeds = [(0.0, 1.0)]
        self.acts = []       # (t, javascript)
        self.marks = []      # (t, label): for the timeline and the stills
        self.parts = []      # (part of the page, test on a frame's log row): what a storyboard promises to show
        self.still_at_end = False   # a still at the last frame of each shot instead of half a second into it
        self.lead = 0.0      # seconds the page runs before the first frame is taken

    def speed(self, s):
        self.speeds.append((self.t, s))
        return self

    def hold(self, d, label=None):
        if label:
            self.marks.append((self.t, label))
        self.t += d
        return self

    def move(self, y, d, label=None):
        if label:
            self.marks.append((self.t, label))
        self.moves.append((self.t, self.t + d, self.y, y))
        self.t += d
        self.y = y
        return self

    def jump(self, y, label=None):
        if label:
            self.marks.append((self.t, label))
        self.moves.append((self.t, self.t, self.y, y))
        self.y = y
        return self

    def act(self, js, label=None):
        if label:
            self.marks.append((self.t, label))
        self.acts.append((self.t, js))
        return self

    def still(self, label):
        self.marks.append((self.t, label))
        return self

    def play(self, page_s, video_s, label=None):
        """Let the page run page_s seconds of its own time in video_s seconds of video."""
        return self.speed(page_s / video_s).hold(video_s, label)

    def shows(self, part, **need):
        """This storyboard shows `part` of the page: frames with that scheme tab on the first screen (tab=), that active
        step (step=) or that scroll range (y=(from, to)) must be in the video (checked against the frames taken)."""
        self.parts.append((part, need))
        return self

    def y_at(self, t):
        y = 0.0
        for t0, t1, y0, y1 in self.moves:
            if t < t0:
                break
            y = y1 if t >= t1 else y0 + (y1 - y0) * ease((t - t0) / (t1 - t0))
        return y

    def speed_at(self, t):
        return self.speeds[bisect.bisect_right([s[0] for s in self.speeds], t) - 1][1]


def teaser(kind, f):
    """The storyboard of 15 November 2026, the same for both videos. f: page facts at this window size (stage.page_facts).

    About 24 s. 0-11 s: the four schemes of the first screen, each to the end of its action, at twice the page's speed;
    the page moves on to the next scheme by itself, so the rest of a scheme's time, in which nothing moves, is passed in
    a quarter of a second. 11-15.5 s: the reader scrolls on: "delivered is not read", then the pull-out from six agents
    to 1,024. 15.5-24 s: the same 1,024 dots re-form into the scale of real swarms (scrolling on), then the page is
    jumped to three more parts: the Agensh curve, a self-spreading idea, the map of the sources."""
    H, hx, st = f["H"], f["hx"], f["step"]
    b = Board()
    for m in range(4):
        b.speed(2.0).hold(SCHEME_END[m] / 2.0, f"scheme {m + 1}")
        if m < 3:
            b.speed((SCHEME_DUR[m] - SCHEME_END[m] + 0.02) / 0.25).hold(0.25)
    b.speed(1.5).move(hx + 1.0 * H, 1.3, "delivered is not read").hold(0.6)
    b.speed(1.0).move(hx + 2.95 * H, 2.2, "pull-out to 1,024").hold(0.35)
    b.speed(1.25).move(st["s1-0"][0], 0.9, "01 scale").hold(1.1)
    b.speed(1.6).jump(st["s2-0"][0], "02 growth and price").hold(1.9)
    b.speed(2.2).jump(st["s5-1"][0], "05 beliefs").hold(2.2)
    b.speed(1.1).jump(st["s6-0"][0], "06 the map").hold(2.2)
    return b


def tour(kind, f):
    """Every part of the page in under 25 s, the same for both videos. f: page facts at this window size.

    The first frame is taken 1.05 s after the page has opened, when the six agents stand in their places and agent 3
    has found its solution: what a player shows before the video starts is the page's question with its picture.
    0-5.4 s, the first screen: its four schemes, each to the end of its action. A scheme is chosen by a click on its
    tab, as a reader chooses one, and the page's clock runs 2.8 to 3.8 times faster than the video's (the stretch of
    scheme 1 in which the other agents only keep working, 5.4 times). 5.4-10 s, the reader scrolls on: "delivered is not
    read", the pull-out from six agents to 1,024, the same dots as the scale of real swarms. 10-24.75 s: the page is
    jumped from part to part, and its 1,024 dots re-form into each figure: the Agensh curve and a hundred agents spent
    three ways; the board of claims, the steps 8, 128 and 1,024 with the integrators that appear, their merges into main
    (held until the page's counters reach 11,111 and 2,800); three kinds of memory when authors leave, a record
    published to the shared store, a record found after its author is gone; an idea that spreads through a chain (to its
    70%), the paragraph that stops it (to its 1%), a cascade of preferences, collusion compared across models; the map
    with its labels. A jump lands where a reader arrives at a step, with the card's text at its first line; from the
    step just before, it lands at the step's top, where the previous card has left the window.

    Each `shows` line is a promise checked against the frames taken (run): at least a fifth of a second of every part."""
    H, hx, st, at = f["H"], f["hx"], f["step"], f["arrive"]
    order = [k for k, _, _ in f["steps"]]
    tab = lambda m: f"document.querySelectorAll('.tab')[{m}].click()"
    top = (0, hx + 0.03 * H)                  # the first screen before its text starts to leave
    b = Board()
    b.still_at_end = True
    b.lead = 1.05
    # the first screen: four ways for a finding to reach the others
    b.play(3.25, 0.6, "scheme 1: independent").play(2.2, 0.75)
    b.act(tab(1)).play(3.8, 1.35, "scheme 2: through a coordinator")
    b.act(tab(2)).play(5.7, 1.5, "scheme 3: through shared memory")
    b.act(tab(3)).play(3.4, 1.2, "scheme 4: by a local rule")
    for m in range(4):
        b.shows(f"first screen, scheme {m + 1}", tab=m, y=top)
    # the reader scrolls on
    b.speed(2.0).move(hx + 1.0 * H, 0.9, "delivered is not read").speed(2.4).hold(0.55)
    b.speed(1.0).move(hx + 2.95 * H, 1.5, "pull-out to 1,024").hold(0.2)
    b.speed(1.6).move(st["s1-0"][0], 0.7, "01 scale").speed(2.4).hold(0.75)
    b.shows("delivered is not read", y=(hx + 0.6 * H, hx + 1.5 * H)).shows("pull-out to 1,024", y=(hx + 2.3 * H, hx + 3.0 * H)).shows("01 scale", step="s1-0")
    # from part to part: (step, seconds of the page, seconds of video, the shot, the part of the page it shows)
    last = "s1-0"
    for key, page_s, video_s, label, part in (
            ("s2-0", 3.1, 1.35, "02 growth: from 1 to 1,024 agents", "02 growth"),
            ("s2-3", 1.6, 0.85, "02 a hundred agents spent three ways", "02 budget"),
            ("s3-0", 1.5, 0.85, "03 self-organisation: the board of claims", "03 self-organisation"),
            ("s3-2", 5.9, 1.65, "03 steps 8, 128, 1,024: integrators appear", "03 emergent hierarchy"),
            ("s3-3", 4.7, 0.95, "03 integrators merge into main", "03 merges into main"),
            ("s4-0", 2.9, 1.2, "04 memory: three stores when authors leave", "04 durable memory"),
            ("s4-2", 3.4, 1.0, "04 a record is published to the shared store", "04 publishing to the shared store"),
            ("s4-3", 3.1, 1.05, "04 a record found after its author is gone", "04 search in the shared store"),
            ("s5-1", 4.9, 1.25, "05 an idea spreads through the chain", "05 self-spreading idea"),
            ("s5-2", 3.3, 0.95, "05 a warning paragraph stops it", "05 warning"),
            ("s5-3", 3.5, 0.95, "05 a cascade of preferences", "05 cascade"),
            ("s5-5", 2.4, 0.9, "05 collusion compared across models", "05 comparison"),
            ("s6-0", 2.5, 1.8, "06 the map of sources", "06 map")):
        b.jump(st[key][0] if order.index(key) - order.index(last) == 1 else at[key]).play(page_s, video_s, label).shows(part, step=key)
        last = key
    return b


BOARDS = {"tour": tour, "teaser": teaser}


def encode(master, final, fps, crf):
    """The delivery file from the lossless master: H.264 High at level 4.2 (four reference frames: any phone or TV of the
    last years decodes it), yuv420p, constant frame rate, the moov atom first (starts playing while it loads), no audio.
    Colour: BT.709 matrix and primaries, limited range, sRGB transfer, which is what a browser frame is."""
    cmd = [shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-i", master,
           "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=lanczos+accurate_rnd+full_chroma_int,format=yuv420p,"
                  "setparams=color_primaries=bt709:color_trc=iec61966-2-1:colorspace=bt709:range=tv",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level:v", "4.2", "-refs", "4", "-pix_fmt", "yuv420p", "-r", str(fps),
           "-x264-params", "aq-mode=3:keyint=%d" % (fps * 2), "-movflags", "+faststart", "-an", final]
    subprocess.run(cmd, check=True)
    probe = json.loads(subprocess.run([shutil.which("ffprobe"), "-v", "error", "-count_frames", "-show_entries",
                                       "stream=codec_name,profile,level,pix_fmt,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration,color_space,color_transfer,color_primaries,color_range:format=duration,size,format_name",
                                       "-of", "json", final], capture_output=True, text=True, check=True).stdout)
    return probe, hashlib.sha256(open(final, "rb").read()).hexdigest()


def run(a):
    (w, h), dpr, phone, engine, cap = KINDS[a.kind]
    engine = a.engine or engine
    if a.preview:
        dpr, cap = 1, 0
    out = os.path.abspath(a.out)
    work = os.path.abspath(a.work or os.path.join(out, "work"))
    stills = os.path.join(out, "stills")
    for d in (out, work, stills):
        os.makedirs(d, exist_ok=True)
    name = ("" if a.board == "teaser" else a.board + "-") + f"{a.kind}-{a.lang}" + ("-preview" if a.preview else "")
    src = os.path.abspath(a.page or os.path.join(stage.ROOT, "site", a.lang, "index.html"))
    page = stage.capture_copy(src, work, cap) if cap else src
    ow, oh = round(w * dpr), round(h * dpr)
    master = os.path.join(work, name + ".master.mkv")
    final = os.path.join(out, f"swarm-dynamics-{name}.mp4")
    ff = shutil.which("ffmpeg")
    if a.reencode:
        tl = os.path.join(out, name + ".timeline.json")
        d = json.load(open(tl, encoding="utf-8"))
        d["ffprobe"], d["sha256"] = encode(master, final, a.fps, a.crf)
        json.dump(d, open(tl, "w", encoding="utf-8"), ensure_ascii=False)
        st = d["ffprobe"]["streams"][0]
        print(f"{final}\n  re-encoded: {st['width']}x{st['height']} {st['codec_name']} {st['profile']}@{st['level']} {st['pix_fmt']} {st['r_frame_rate']} fps, {st['nb_read_frames']} frames, "
              f"{float(d['ffprobe']['format']['duration']):.2f} s, {int(d['ffprobe']['format']['size']) / 1e6:.1f} MB, sha256 {d['sha256']}")
        return
    log, marks_done, strip = [], set(), []
    with sync_playwright() as p:
        b, ctx, pg, problems = stage.open_page(p, engine, page, w, h, dpr, phone=phone)
        f = stage.page_facts(pg)
        bd = BOARDS[a.board](a.kind, f)
        if bd.lead:
            pg.evaluate(f"__vc.run({round(bd.lead * 60)})")
        clock0 = pg.evaluate("__vc.t") / 1000          # the page's time when the first frame's step begins
        n = round(bd.t * a.fps)
        if not 15 <= n / a.fps <= 25:
            raise SystemExit(f"the storyboard is {n / a.fps:.2f} s long: the video is to last 15 to 25 s")
        enc = subprocess.Popen([ff, "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-framerate", str(a.fps), "-c:v", "png", "-i", "-",
                                "-c:v", "libx264rgb", "-preset", "ultrafast", "-qp", "0", master], stdin=subprocess.PIPE)
        acts = sorted(bd.acts)
        marks = sorted(bd.marks)
        # the frame at which each shot's still is taken: half a second into it, or its last frame
        first = [min(n - 1, math.ceil(tt * a.fps - 1e-9)) for tt, _ in marks]
        still_i = {((first[k + 1] if k + 1 < len(marks) else n) - 1 if bd.still_at_end else None): marks[k] for k in range(len(marks))}
        FRAME = ("(o) => { const r = __vc.frame(o), tab = [...document.querySelectorAll('.tab')].findIndex(t => t.classList.contains('on')), s = document.querySelector('.step.on');"
                 " return [r.t, r.y, tab, s ? s.id : '', r.raf, r.anims]; }")
        for i in range(n):
            t = i / a.fps
            js = ";".join(j for tt, j in acts if t - 1 / a.fps < tt <= t) if i else ""
            o = dict(dt=1000.0 * bd.speed_at(t) / a.fps, y=round(bd.y_at(t), 2))
            o["n"] = max(1, math.ceil(o["dt"] / 40.0))     # a faster time-lapse is made of more page frames, not longer ones
            if js:
                o["run"] = js
            vt, y, tab, step, raf, anims = pg.evaluate(FRAME, o)
            png = pg.screenshot(type="png")
            if i == 0:
                from PIL import Image
                size = Image.open(io.BytesIO(png)).size
                if size != (ow, oh):
                    raise SystemExit(f"frame is {size}, expected {(ow, oh)}")
            enc.stdin.write(png)
            log.append([round(t, 4), round(vt / 1000, 4), round(y, 1), tab, step, raf, anims])
            if bd.still_at_end:
                if i in still_i:
                    open(os.path.join(stills, f"{name}-{t:05.2f}s-{stage.slug(still_i[i][1])}.png"), "wb").write(png)
            else:
                for tt, label in marks:      # a still half a second after each mark
                    if (tt, label) not in marks_done and t >= tt + 0.5:
                        marks_done.add((tt, label))
                        open(os.path.join(stills, f"{name}-{t:05.2f}s-{stage.slug(label)}.png"), "wb").write(png)
            if a.strip and i % a.strip == 0:
                strip.append(png)
            if i % 120 == 0:
                print(f"{name}: frame {i}/{n} t={t:.2f}s page={vt / 1000:.2f}s y={y:.0f} tab={tab + 1} step={step}", flush=True)
        if not bd.still_at_end:
            open(os.path.join(stills, f"{name}-{(n - 1) / a.fps:05.2f}s-last-frame.png"), "wb").write(png)
        enc.stdin.close()
        if enc.wait():
            raise SystemExit("ffmpeg (master) failed")
        clock_log = pg.evaluate("__vc.log")
        version = b.version
        b.close()
    # what the frames taken really show: every shot, and every part of the page the storyboard promises
    shots = []
    for k, (tt, label) in enumerate(marks):
        i0, i1 = first[k], (first[k + 1] if k + 1 < len(marks) else n)
        rows = log[i0:i1]
        page_s = rows[-1][1] - (log[i0 - 1][1] if i0 else clock0)
        shots.append(dict(label=label, start_s=round(i0 / a.fps, 3), end_s=round(i1 / a.fps, 3), frames=i1 - i0, page_s=round(page_s, 2),
                          page_speed=round(page_s / ((i1 - i0) / a.fps), 2), scroll_y=[rows[0][2], rows[-1][2]],
                          scheme_tabs=sorted({r[3] + 1 for r in rows if r[2] < f["hx"] + 0.03 * f["H"] + 1}), steps=sorted({r[4] for r in rows if r[4]})))

    def seen(r, need):
        return (("tab" not in need or r[3] == need["tab"]) and ("step" not in need or r[4] == need["step"])
                and ("y" not in need or need["y"][0] - 0.5 <= r[2] <= need["y"][1] + 0.5) and ("step" in need or not r[4]))

    parts = []
    for part, need in bd.parts:
        on = [r[0] for r in log if seen(r, need)]
        parts.append(dict(part=part, need=need, frames=len(on), seconds=round(len(on) / a.fps, 3), first_s=on[0] if on else None, last_s=on[-1] if on else None))
    missing = [x["part"] for x in parts if x["frames"] < a.fps / 5]
    if missing:
        raise SystemExit(f"{name}: the storyboard promises parts of the page that the frames do not show for a fifth of a second: {missing}")
    probe, sha = encode(master, final, a.fps, a.crf)
    schemes = sorted({r[3] + 1 for r in log if r[2] < f["hx"] + 0.03 * f["H"] + 1})
    steps = []
    for r in log:
        if r[4] and (not steps or steps[-1] != r[4]):
            steps.append(r[4])
    json.dump(dict(video=os.path.basename(final), sha256=sha, ffprobe=probe, board=a.board, kind=a.kind, lang=a.lang, page=os.path.relpath(src, stage.ROOT),
                   page_sha256=hashlib.sha256(open(src, "rb").read()).hexdigest(), canvas_cap=cap or 2, engine=engine, engine_version=version,
                   window=[w, h], scale=dpr, fps=a.fps, frames=len(log), seconds=len(log) / a.fps, facts={k: v for k, v in f.items() if k != "step"},
                   storyboard=dict(lead=bd.lead, moves=bd.moves, speeds=bd.speeds, acts=bd.acts, marks=bd.marks),
                   coverage=dict(schemes_on_first_screen=schemes, steps_shown=steps), shots=shots, parts=parts, problems=problems, clock_log=clock_log,
                   columns=["video_s", "page_s", "scroll_y", "scheme_tab", "active_step", "frame_requested", "css_animations"], frames_log=log),
              open(os.path.join(out, name + ".timeline.json"), "w", encoding="utf-8"), ensure_ascii=False)
    if strip:
        from PIL import Image
        ims = [Image.open(io.BytesIO(x)).convert("RGB") for x in strip]
        tw = 216 if oh > ow else 384
        th = round(ims[0].height * tw / ims[0].width)
        cols = 12 if oh > ow else 8
        rows = (len(ims) + cols - 1) // cols
        sh = Image.new("RGB", (cols * (tw + 4) + 4, rows * (th + 4) + 4), (40, 42, 44))
        for k, im in enumerate(ims):
            sh.paste(im.resize((tw, th), Image.LANCZOS), (4 + (k % cols) * (tw + 4), 4 + (k // cols) * (th + 4)))
        sh.save(os.path.join(out, name + ".strip.png"))
    st = probe["streams"][0]
    print(f"{final}\n  {st['width']}x{st['height']} {st['codec_name']} {st['pix_fmt']} {st['r_frame_rate']} fps, {st['nb_read_frames']} frames, {float(probe['format']['duration']):.2f} s, "
          f"{int(probe['format']['size']) / 1e6:.1f} MB, sha256 {sha}\n  schemes on the first screen: {schemes}; steps: {steps}; problems: {problems or 'none'}; clock log: {clock_log or 'empty'}")
    for x in parts:
        print(f"  {x['seconds']:5.2f} s  {x['part']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--board", default="tour", choices=sorted(BOARDS), help="the storyboard: every part of the page (tour) or the selection of 15 November 2026 (teaser)")
    ap.add_argument("--lang", default="ru")
    ap.add_argument("--page")
    ap.add_argument("--engine")
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--crf", type=int, default=15)
    ap.add_argument("--work")
    ap.add_argument("--preview", action="store_true", help="1x scale, for a quick look at the storyboard")
    ap.add_argument("--strip", type=int, default=0, help="also save every Nth frame on one sheet")
    ap.add_argument("--reencode", action="store_true", help="only encode the delivery file again from the master of an earlier run")
    run(ap.parse_args())

#!/usr/bin/env python3
"""Numbers and arithmetic of the mechanism scenes, checked against the cards they quote and recomputed independently.

  python scripts/check_scenes.py              # static checks (seconds)
  python scripts/check_scenes.py --browser    # also: the consensus readout in Chromium equals the Python numbers

Each scene in scripts/scenes_mech.py quotes numbers from a card in content/{en,ru}/*.md and draws the rest. This
script fails when a quoted number is missing from its card, when the arithmetic of a scene is off, or when the
consensus toy (curves, finite runs, the exact outcome bar) disagrees with an independent computation: a Newton
solve for the infinite group, the closed-form fold point, and an agent-level Monte Carlo of the finite group.
"""
import math, os, random, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import build_site   # noqa: F401  (binds the helpers the scenes need)
import scenes, scenes_mech as M

FAIL = []


def ok(cond, what):
    print(("ok   " if cond else "FAIL ") + what)
    if not cond: FAIL.append(what)


def card(lang, ch, cid):
    t = open(os.path.join(ROOT, "content", lang, f"{ch}.md"), encoding="utf-8").read()
    m = re.search(r":::(?:card|short) " + re.escape(cid) + r"\n(.*?)\n:::", t, re.S)
    return m.group(1) if m else ""


def html(lang):
    return open(os.path.join(ROOT, "site", lang, "index.html"), encoding="utf-8").read()


def scene_html(lang, sid):
    h = html(lang); i = h.index(f'id="{sid}"'); j = h.index("</figure>", i)
    return h[i:j]


# ---------------------------------------------------------------- λ: the rule's arithmetic, kept apart from measurements
ord_en = card("en", "ch04", "ord-swarm-scaling")
ok(all(x in ord_en for x in ("0.68 on BrowseComp", "0.57 on SEC-Bench Pro", "0.48 on Terminal-Bench 2.1", "16^0.57 ≈ 4.9", "2–2.8 times faster", "Only 1 and 4 agents")), "λ: the values the scene quotes are in Ord's card")
for N in (4, 16):
    for lam in (0.48, 0.5, 0.57, 0.68, 1.0):
        tt, cc, _ = M.lam_parts("en", N, lam)
        t, c = N ** -lam, N ** (1 - lam)
        ok(abs(float(tt[2:]) - 1 / t) < 0.051 and abs(float(cc[1:]) - c) < 0.051, f"λ: N={N}, λ={lam}: {tt} of the time, {cc} the tokens (N^−λ = {t:.4f}, N^(1−λ) = {c:.4f})")
ok(round(16 ** 0.57, 1) == 4.9 and round(16 ** 0.43, 1) == 3.3, "λ: 16 agents at λ = 0.57 → 1/4.9 of the time (a fifth) at 3.3× the tokens")
for lang in ("en", "ru"):
    T = M.LX[lang]
    ok(("fifth" if lang == "en" else "пятую") in T["beats"][1] and ("3.3" if lang == "en" else "3,3") in T["beats"][2] and ("2–2.8" if lang == "en" else "2–2,8") in T["beats"][2],
       f"λ {lang}: the beats give the formula's fifth and 3.3× and name the separate 2–2.8× latency estimate")
    ok(T["ext"].strip() in M.lam_readout(lang, 16, 0.48) and all(T["ext"].strip() not in M.lam_readout(lang, n_, l_) for n_, l_ in ((4, 0.48), (16, 0.57), (16, 0.68))),
       f"λ {lang}: the extrapolation note appears exactly for 16 agents at λ = 0.48")
ok(M.lam_who("ru", 4) == "4 агента" and M.lam_who("ru", 16) == "16 агентов", "λ ru: agreement of the number (4 агента, 16 агентов)")

# ---------------------------------------------------------------- HiddenBench: two interventions, two models
hb_en = card("en", "ch06", "hiddenbench")
ok(all(x in hb_en for x in ("30.1%", "80.7%", "92.6% for GPT-4.1", "98.2% for Gemini-2.5-Flash", "0.73–0.80", "65 tasks")), "HiddenBench: the numbers are in the card")
for lang in ("en", "ru"):
    T = M.HB[lang]
    vals = [(a, b) for _, a, b in T["bars"]]
    ok(vals == [(30.1, None), (73, 80), (80.7, None), (92.6, None), (98.2, None)], f"HiddenBench {lang}: five bars, the forced reveal split into its two models")
    ok(len(T["beats"]) == 5 and ("73–80" in T["beats"][3]) and ("92" in T["beats"][4] and "98" in T["beats"][4]), f"HiddenBench {lang}: Exchange-Decide and the forced reveal have separate beats")
    ok(not re.search(r"(every|all|все|каждый)", T["beats"][3], re.I), f"HiddenBench {lang}: the Exchange-Decide beat does not promise that every fact arrives")

# ---------------------------------------------------------------- Mind viruses: a schematic chain, a measured bar
mv_en = card("en", "ch07", "mind-viruses")
ok("DeepSeek 70%, Gemini 3 Flash 70%" in mv_en and "(1%)" in mv_en, "Mind viruses: 70% and 1% are in the card")
for lang in ("en", "ru"):
    sh = scene_html(lang, "sc-virus")
    bars = re.findall(r'<rect class="mv-tr" x="([\d.]+)" y="[\d.]+" width="([\d.]+)"[^>]*/><rect class="mv-bar r-(\w+)" x="[\d.]+" y="[\d.]+" width="([\d.]+)"', sh)
    good = len(bars) == 4 and all(abs(float(w) - max(2, float(tw) * {"plain": 70, "warned": 1}[r] / 100)) < 0.06 for _, tw, r, w in bars)
    ok(good, f"Mind viruses {lang}: each bar is the measured mean on a 0–100% track (70% and 1%), wide and narrow")
    seeds = len(re.findall(r'class="nd inf seed"', sh)); warned_inf = len(re.findall(r'class="nd inf[^"]*" data-i="\d" data-r="warned"', sh))
    ok(seeds == 4 and warned_inf == 2, f"Mind viruses {lang}: every chain starts at a marked seed; the warned chain has no other infected agent")

# ---------------------------------------------------------------- DeepMind loophole
dm_en = card("en", "ch07", "deepmind-cheating-whistleblowing")
ok(all(x in dm_en for x in ("57 minutes", "37 problems", "27 minutes", "34 problems", "9 agents cheated", "5 \"converted\"", "24 became whistleblowers", "62 noticed nothing", "nobody read the complaints channel in real time", "no way to reject a fake or sanction")),
   "Loophole: the numbers and the complaint semantics are in the card")
for lang in ("en", "ru"):
    leg = M.LH[lang]["legend"]
    ok(sum(c for _, _, c in leg) == 100 and 37 + 34 == 71, f"Loophole {lang}: 9 + 5 + 24 + 62 = 100 agents, 37 + 34 = 71 statements")
    ok(("proof store" if lang == "en" else "хранилище доказательств") in M.LH[lang]["title"], f"Loophole {lang}: the shared store is named as a proof store")

# ---------------------------------------------------------------- Echo
ec_en = card("en", "ch08", "ringelmann-effect")
ok(all(x in ec_en for x in ("1.12 on MMLU-Hard", "80% of items unanimous", "1.79 on GSM-Hard", "from 1.12 to 1.34")), "Echo: 1.12, 1.79, 1.34 and 80% are in the card")
for lang in ("en", "ru"):
    ok(not re.search(r"(each round|каждый раунд)", " ".join(M.EC[lang]["beats"]), re.I), f"Echo {lang}: no claim of a measured round-by-round pull")

# ---------------------------------------------------------------- Moltbook: two units, two glyphs
mb_en = card("en", "ch10", "wiz-moltbook")
ok("1.5 million registrations" in mb_en and "17,000 human owners" in mb_en and "88 agents per person" in mb_en, "Moltbook: 1.5 million registrations, 17,000 owners, 88 per person are in the card")
ok(M.MB_REG * M.MB_UNIT == 1_500_000 and M.MB_OWN * M.MB_UNIT == 17_000 and round(M.MB_REG / M.MB_OWN) == 88, "Moltbook: 1,500 squares × 1,000 = 1.5 million; 17 dots × 1,000 = 17,000; 1,500 / 17 ≈ 88")
for lang in ("en", "ru"):
    sh = scene_html(lang, "sc-moltbook")
    sq = sum(len(re.findall(r"M[\d.]+ [\d.]+h5v5h-5z", d)) for d in re.findall(r'<path class="mb-a"[^>]*d="([^"]+)"', sh))
    dots = len(re.findall(r'<circle cx="[\d.]+" cy="[\d.]+" r="7"/>', sh))
    ok(sq == 2 * M.MB_REG and dots == 2 * M.MB_OWN, f"Moltbook {lang}: {M.MB_REG} squares and {M.MB_OWN} dots in each layout (wide, narrow)")
    ok(all(re.search(p, sh) for p in (r'class="kg-a"', r'class="kg-b"')) and "agents" not in M.MB[lang]["title"] and "агент" not in M.MB[lang]["title"],
       f"Moltbook {lang}: one key per glyph; the title counts registrations, not agents")

# ---------------------------------------------------------------- Consensus: the toy, recomputed independently
h, N = M.CS_H, M.CS_N


def newton_roots(K):
    roots = []
    for m0 in [-0.999 + i * 0.0999 for i in range(21)]:
        m = m0
        for _ in range(200):
            f = math.tanh(K * m + h) - m; fp = K * (1 - math.tanh(K * m + h) ** 2) - 1
            if fp == 0: break
            m -= f / fp
            m = max(-1, min(1, m))
        if abs(math.tanh(K * m + h) - m) < 1e-10 and all(abs(m - r) > 1e-6 for r in roots): roots.append(m)
    return sorted(roots)


bad = []
for K, s in M.CS_UP:
    st = [r for r in newton_roots(K) if K * (1 - math.tanh(K * r + h) ** 2) < 1]
    if abs((1 + max(st)) / 2 - s) > 1e-6: bad.append(("up", K))
for K, s in M.CS_LO:
    st = [r for r in newton_roots(K) if K * (1 - math.tanh(K * r + h) ** 2) < 1]
    if len(st) < 2 or abs((1 + min(st)) / 2 - s) > 1e-6: bad.append(("lo", K))
ok(not bad, f"Consensus: {len(M.CS_UP)} upper and {len(M.CS_LO)} lower curve points are stable roots of m = tanh(K·m + h) (Newton) {bad[:3]}")
# the fold where the lower branch appears: m² = 1 − 1/K, h = atanh(|m|) − K·|m|
lo_k, hi_k = 1.0001, 3.0
for _ in range(100):
    mid = (lo_k + hi_k) / 2; a = math.sqrt(1 - 1 / mid)
    if math.atanh(a) - mid * a > -h: lo_k = mid
    else: hi_k = mid
ok(abs(M.CS_LO[0][0] - hi_k) <= 0.011, f"Consensus: the lower branch starts at K = {M.CS_LO[0][0]:.3f}; the closed-form fold is at {hi_k:.4f}")
ok(all(s > 0.5 for _, s in M.CS_UP) and all(s < 0.5 for _, s in M.CS_LO), "Consensus: the upper branch favours the biased answer, the lower one the other answer")
ok(M.CS_SEED == 3, "Consensus: the static runs keep the seed of the first version (3); their outcome is not chosen")
# finite runs: what the grids print is what they contain
for lang in ("en", "ru"):
    sh = scene_html(lang, "sc-consensus")
    shares = [int(x) for x in re.findall(r'<text class="sv2"[^>]*>(\d+)', sh)]
    exp = [round(M.CS_RUNS[K].count(1) / N * 100) for K in M.CS_K] * 2
    ok(shares == exp, f"Consensus {lang}: each grid prints its own share on the favoured answer ({exp[:3]})")
    ok(all(f">{p}{scenes.NB if lang == 'ru' else ''}%<" in sh for p in ("0", "50", "100")), f"Consensus {lang}: the y axis runs 0–100%, so a run against the bias is on the chart")
    printed = [int(x) for x in re.findall(r"<b>(\d+)(?: )?%</b>", sh[sh.index('class="cs-out"'):])]
    ok(printed == M.pct_round(M.cs_outcomes(M.CS_K[-1])) and sum(printed) == 100, f"Consensus {lang}: the outcome bar prints {printed}, summing to 100")
# the exact outcome distribution against an agent-level Monte Carlo (not the birth–death chain)
def mc(K, runs, seed):
    rnd = random.Random(seed); cnt = [0, 0, 0]
    for _ in range(runs):
        s = [rnd.choice((1, -1)) for _ in range(N)]; tot = sum(s)
        for _ in range(M.CS_ROUNDS * N):
            i = rnd.randrange(N); m = (tot - s[i]) / (N - 1)
            new = 1 if rnd.random() < 1 / (1 + math.exp(-2 * (K * m + h))) else -1
            tot += new - s[i]; s[i] = new
        k = s.count(1)
        cnt[0 if k >= M.CS_CUT else (2 if k <= N - M.CS_CUT else 1)] += 1
    return [c / runs for c in cnt]
runs = int(os.environ.get("CS_MC_RUNS", "1500"))
for K in (1.0, 1.6):
    ex = M.cs_outcomes(K); sim = mc(K, runs, 20261011)
    z = max(abs(a - b) / math.sqrt(max(a * (1 - a), 1e-4) / runs) for a, b in zip(ex, sim))
    ok(z < 4.5, f"Consensus: exact outcomes at K = {K} {[round(x, 3) for x in ex]} vs Monte Carlo of {runs} runs {[round(x, 3) for x in sim]} (max |z| = {z:.2f})")

# ---------------------------------------------------------------- optional: the browser readout equals the Python numbers
if "--browser" in sys.argv:
    import pwd
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(pwd.getpwuid(os.getuid()).pw_dir, "Library/Caches/ms-playwright"))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1240, "height": 800}, reduced_motion="reduce")
        pg.goto("file://" + os.path.join(ROOT, "site", "en", "index.html")); pg.wait_for_timeout(500)
        for K in (0.2, 0.6, 1.0, 1.2, 1.25, 1.6, 2.0):
            pg.evaluate("k => { const r = document.querySelector('#sc-consensus .cs-k'); r.value = k; r.dispatchEvent(new Event('input')); }", K); pg.wait_for_timeout(250)
            js = [int(x.rstrip('%').strip()) for x in pg.evaluate("[...document.querySelectorAll('#sc-consensus .cs-out-l b')].map(b => b.textContent)")]
            ok(js == M.pct_round(M.cs_outcomes(K)), f"Consensus: the page's bar at K = {K} prints {js}, Python {M.pct_round(M.cs_outcomes(K))}")
        b.close()

print(f"\n{len(FAIL)} failure(s)")
sys.exit(1 if FAIL else 0)

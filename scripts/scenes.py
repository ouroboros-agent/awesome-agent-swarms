#!/usr/bin/env python3
"""Native scenes of the longread: the survey's own charts and the mechanism explanations.

scripts/build_site.py places every scene where scripts/longread.py says (PLACE) and calls html(name, lang, ctx).
Each scene is complete without JavaScript: the static markup shows its end state, the narration is a numbered
list, and charts carry a data table. assets/js/scenes.js plays them when they are on screen.

Two kinds, and the badge on each says which:
  data       numbers computed here from data/works.json (Chapter 1 charts, the atlas map) or quoted from the
             card next to the scene, with the card's comparison conditions;
  schematic  the mechanism a card describes, drawn with the same six-agent grammar as the prologue. The motion is
             illustrative; only the numbers printed in the scene are measurements, and each comes from that card.
"""
import html as _html, json, math, os, random, re, statistics
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = " "
PINNED = {"fieldmap"}   # scenes that pin beside the text that follows them
H = {}            # helpers bound by build_site: card_href, card_title, scale_note, evid, topic, md_inline


def bind(**kw):
    H.update(kw)


def esc(s):
    return _html.escape(str(s if s is not None else ""), quote=True)


def fnum(v, lang, dec=0):
    s = f"{v:,.{dec}f}"
    return s.replace(",", NB).replace(".", ",") if lang == "ru" else s


def pct(v, lang, dec=1):
    return fnum(v, lang, dec) + (f"{NB}%" if lang == "ru" else "%")


def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


REG = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
CORPUS = [w for w in REG["works"] if w.get("in_analytic_corpus") and w.get("corpus")]

# ---------------------------------------------------------------- shared frame
UI = {
 "en": dict(sch="Schematic", dat="Survey data", card="Card data", pause="Pause", play="Play", replay="Replay",
            png="Static chart (PNG)", dark="dark", light="light", table="Data behind the chart", to_card="to the card",
            sch_note="The motion is illustrative; the numbers are the card’s."),
 "ru": dict(sch="Схема", dat="Данные обзора", card="Данные карточки", pause="Пауза", play="Продолжить", replay="Ещё раз",
            png="Статичный график (PNG)", dark="тёмный", light="светлый", table="Данные графика", to_card="к карточке",
            sch_note="Движение условное; числа — из карточки."),
}
I_PAUSE = ('<svg class="i-pause" viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="2" width="2.4" height="8" rx="1"/><rect x="7.1" y="2" width="2.4" height="8" rx="1"/></svg>'
           '<svg class="i-play" viewBox="0 0 12 12" aria-hidden="true"><path d="M3.5 2.2v7.6a.6.6 0 0 0 .9.5l6-3.8a.6.6 0 0 0 0-1l-6-3.8a.6.6 0 0 0-.9.5z"/></svg>'
           '<svg class="i-replay" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.2 6a3.8 3.8 0 1 0 1.1-2.7M2.2 1.8v2.4h2.4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def frame(name, lang, sid, art, title="", beats=None, badge="sch", note="", cls="", fig=None, after="", controls="", data_attrs=""):
    """<figure> with the art, a caption bar (badge, title, step dots, pause) and the numbered narration."""
    U = UI[lang]
    bl = beats or []
    dots = f'<span class="dots" aria-hidden="true">{"<i></i>" * len(bl)}</span>' if bl else ""
    pp = (f'<button class="sc-pp js-only" type="button" aria-label="{U["pause"]}" data-pause="{U["pause"]}" data-play="{U["play"]}" data-replay="{U["replay"]}">{I_PAUSE}</button>'
          if bl else "")
    blab = U["sch"] if badge == "sch" else (U["dat"] if badge == "dat" else U["card"])
    fnum_ = f'<span class="fnum">{fig["label"]}</span>' if fig else ""
    head = (f'<div class="sc-head"><span class="sc-badge b-{badge}">{blab}</span><span class="sc-title">{fnum_}{title}</span>{dots}{pp}</div>')
    beats_h = (f'<ol class="beats" data-beat="-1">' + "".join(f"<li>{b}</li>" for b in bl) + "</ol>") if bl else ""
    links = ""
    if fig and fig.get("pngs"):
        pl = " · ".join(f'<a href="{esc(h)}">{esc(t)}</a>' for h, t in fig["pngs"])
        if fig.get("native"):   # the static chart keeps its own legend
            cred = f' <span class="credit">{fig["credit"]}</span>' if fig.get("credit") else ""
            links = f'<details class="sc-orig"><summary>{U["png"]}</summary><p>{fig["caption"]}{cred}</p><p>{pl}</p></details>'
        else:
            links = f'<p class="sc-png">{U["png"]}: {pl}</p>'
    cap_note = ""
    if fig:
        main = fig.get("native") or fig["caption"]
        cap_note = f'<p class="sc-note">{main}' + (f'<span class="credit">{fig["credit"]}</span>' if fig.get("credit") else "") + "</p>"
    elif note:
        cap_note = f'<p class="sc-note">{note}</p>'
    return (f'<figure class="scene sc-{name}{" sc-fig" if fig else ""}{(" " + cls) if cls else ""}" id="{sid}" data-scene="{name}" data-sl{data_attrs}>'
            f'<figcaption class="sc-cap">{head}</figcaption>{controls}<div class="sc-stage">{art}</div>'
            + (f'<div class="sc-narr">{beats_h}</div>' if beats_h else "") + f'<div class="sc-foot">{cap_note}{links}{after}</div></figure>')


def sid_for(name, lang, ctx):
    return ctx.get("id") or f"sc-{name}"


# ---------------------------------------------------------------- Fig. 1.1: the logic of the field
FM = {
 "en": dict(
    title="The overall logic of the field",
    cols=[("What the swarm is built from", [("Models", "copies of one model (57 works) or a mix of different models (47)", []),
                                             ("Roles and rules", "drawn up by people, learned by an outer loop, or absent", []),
                                             ("Memory", "each agent’s own, shared files, wikis", [])]),
          ("How the agents are connected", [("Messaging", "chat, email, a message board", []),
                                             ("Shared artefacts", "git, wikis, notes, datasets", []),
                                             ("Markets and games", "prices, votes, competitions", [])]),
          ("What emerges", [("Self-organization", "roles, integrators, agreements", [5]),
                            ("Echo and attractors", "copies of a model converge on the same thing", [8]),
                            ("Consensus and cascades", "conformity, majority, split", [9]),
                            ("Contagion and collusion", "parasitic ideas and covert channels", [7])]),
          ("What it delivers and what it risks", [("Speed", "parallelism paid for in tokens", [4]),
                                                   ("Memory", "shared notes and facts distributed across agents", [6]),
                                                   ("Quality", "above the best single agent in specific measured settings", [4, 5]),
                                                   ("Failures", "from the Hugging Face incident to swarms in the wild", [3, 10])])],
    gain="delivers", risk="risks", ch="Ch.",
    beats=["A swarm is assembled from models, roles and rules, and memory.",
           "Its agents are connected by messages, shared artefacts, or markets and games.",
           "What emerges from the connection: self-organization, echo, consensus and cascades, contagion and collusion.",
           "What it delivers — speed, memory, quality in measured settings — and what it pays in failures."]),
 "ru": dict(
    title="Общая логика поля",
    cols=[("Из чего собран рой", [("Модели", "копии одной модели (57 работ) или смесь разных (47)", []),
                                   ("Роли и правила", "нарисованы людьми, выучены внешним циклом или их нет вовсе", []),
                                   ("Память", "своя у каждого агента, общие файлы, вики", [])]),
          ("Как связаны агенты", [("Переписка", "чат, почта, доска объявлений", []),
                                   ("Общие артефакты", "git, вики, заметки, датасеты", []),
                                   ("Рынки и игры", "цены, голосования, соревнования", [])]),
          ("Что возникает", [("Самоорганизация", "роли, интеграторы, договорённости", [5]),
                              ("Эхо и аттракторы", "копии модели сходятся к одному", [8]),
                              ("Согласие и каскады", "конформность, большинство, раскол", [9]),
                              ("Заражение и сговор", "идеи-паразиты и скрытые каналы", [7])]),
          ("Что рой даёт и чем грозит", [("Скорость", "параллельность, оплаченная токенами", [4]),
                                          ("Память", "общие заметки и факты, распределённые между агентами", [6]),
                                          ("Качество", "выше лучшего одиночки — в отдельных измеренных постановках", [4, 5]),
                                          ("Сбои", "от инцидента с Hugging Face до роёв в дикой природе", [3, 10])])],
    gain="даёт", risk="грозит", ch="гл.",
    beats=["Рой собирают из моделей, ролей, правил и памяти.",
           "Агентов связывают переписка, общие артефакты, рынки и игры.",
           "Из связи возникают самоорганизация, эхо, согласие и каскады, заражение и сговор.",
           "Что рой даёт — скорость, память, качество в измеренных постановках — и чем платит: сбоями."]),
}


def fieldmap(lang, ctx):
    T = FM[lang]
    cols = []
    for ci, (head, nodes) in enumerate(T["cols"], 1):
        items = []
        for ni, (t, sub, chs) in enumerate(nodes):
            risk = ci == 4 and ni == 3
            chips = "".join(f'<a class="fm-ch" href="#ch{c:02d}">{T["ch"]}{NB}{c}</a>' for c in chs)
            kind = " fm-risk" if risk else (" fm-gain" if ci == 4 else (" fm-emg" if ci == 3 else ""))
            items.append(f'<div class="fm-node{kind}" style="--j:{ni}"><b>{esc(t)}</b><span>{esc(sub)}</span>' + (f'<span class="fm-chs">{chips}</span>' if chips else "") + "</div>")
        cols.append(f'<div class="fm-col" data-c="{ci}"><p class="fm-h"><span class="fm-n">{ci}</span>{esc(head)}</p><div class="fm-nodes">{"".join(items)}</div></div>')
    art = f'<div class="fm" data-fm><svg class="fm-flow" aria-hidden="true"></svg>{"".join(cols)}</div>'
    return frame("fieldmap", lang, sid_for("fieldmap", lang, ctx), art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="dat", fig=ctx)


# ---------------------------------------------------------------- Fig. 1.2: how many agents (research dashboard)
EVID_ROWS = ["live_experiment", "engineering_report", "benchmark", "system_card_eval", "field_observation", "incident", "surrogate_simulation", "theory_essay"]
SK = {
 "en": dict(tabs=[("sim", "At the same time"), ("cum", "Over the whole period"), ("cap", "Capacity or stated limit"), ("none", "Not stated")],
            axis={"sim": "agents working at the same time in one run or system (log scale)", "cum": "distinct participants, names or sessions over the whole period (log scale)",
                  "cap": "registered accounts or a stated limit (log scale)"},
            lead={"sim": "{n} works state how many agents run at the same time. Median: {med}.",
                  "cum": "{n} works count participants over a whole period. These are not agents at one moment.",
                  "cap": "{n} works give a platform’s registrations or a system’s limit, not a run.",
                  "none": "{n} works give no agent count: theory and essays, or studies that do not disclose it."},
            med="median {v}", thr="≥{t}", works=("work", "works"), at_once="at the same time", total="over the whole period", cap_k="capacity or limit",
            ticks={1: "1", 10: "10", 100: "100", 1000: "1K", 10000: "10K", 100000: "100K", 1000000: "1M"},
            labels={"anthropic-c-compiler": "C compiler · 16", "opus55-card": "Opus 5.5 · 100", "agensh-1024": "Agensh · 1,020",
                    "openai-navier-stokes": "Navier–Stokes · ≈10,000", "anthropic-institute-pace": "Anthropic platform · ≈30,000",
                    "hf-incident-case": "Hugging Face incident · ≈1,200", "moltbook-illusion": "Moltbook authors, 14 days · 55,932",
                    "lai-looking-for-something-weird": "Moltbook, three snapshots · 181,585", "anthropic-art-enzymes": "Enzyme campaign · 949 sessions",
                    "wiz-moltbook": "Moltbook registrations · 1,494,823", "superminds-test": "Moltbook feed · >2 million", "kimi-agent-swarm": "Kimi K2.6 limit · 300",
                    "grok-420-multi-agent": "Grok 4.20 · 16"},
            tip_go="to the card", tip_atlas="to the atlas row",
            cap="Each dot is a work, placed by its number of agents (log scale) in the row of its evidence class. The tabs keep three different quantities apart — agents working at the same moment, participants counted over a whole period, and a platform’s registrations or a system’s stated limit — so they never share an axis; works that give no number are listed rather than placed at zero. Every dot links to the work’s card."),
 "ru": dict(tabs=[("sim", "Одновременно"), ("cum", "За всё время"), ("cap", "Ёмкость или предел"), ("none", "Не указано")],
            axis={"sim": "агентов одновременно в одном прогоне или системе (логарифмическая шкала)", "cum": "разных участников, имён или сессий за весь период (логарифмическая шкала)",
                  "cap": "зарегистрированных аккаунтов или заявленный предел (логарифмическая шкала)"},
            lead={"sim": "{n} работ называют число агентов, работающих одновременно. Медиана — {med}.",
                  "cum": "{n} работ считают участников за весь период. Это не агенты в один момент.",
                  "cap": "{n} работ приводят регистрации площадки или предел системы, а не прогон.",
                  "none": "{n} работ не называют числа агентов: теория и эссе или опыты, где число не раскрыто."},
            med="медиана {v}", thr="≥{t}", works=("работа", "работы", "работ"), at_once="одновременно", total="за всё время", cap_k="ёмкость или предел",
            ticks={1: "1", 10: "10", 100: "100", 1000: "1 тыс.", 10000: "10 тыс.", 100000: "100 тыс.", 1000000: "1 млн"},
            labels={"anthropic-c-compiler": "компилятор C · 16", "opus55-card": "Opus 5.5 · 100", "agensh-1024": "Agensh · 1 020",
                    "openai-navier-stokes": "Навье–Стокс · ≈10 000", "anthropic-institute-pace": "платформа Anthropic · ≈30 000",
                    "hf-incident-case": "инцидент с Hugging Face · ≈1 200", "moltbook-illusion": "авторы Moltbook, 14 дней · 55 932",
                    "lai-looking-for-something-weird": "Moltbook, три среза · 181 585", "anthropic-art-enzymes": "поиск ферментов · 949 сессий",
                    "wiz-moltbook": "регистрации Moltbook · 1 494 823", "superminds-test": "лента Moltbook · >2 млн", "kimi-agent-swarm": "предел Kimi K2.6 · 300",
                    "grok-420-multi-agent": "Grok 4.20 · 16"},
            tip_go="к карточке", tip_atlas="к строке атласа",
            cap="Каждая точка — работа: по горизонтали число агентов (логарифмическая шкала), строка — класс доказательств. Вкладки разводят три разные величины — агентов, работающих одновременно, участников, накопленных за весь период, и регистрации площадки или заявленный предел системы, — поэтому общей оси у них нет; работы без числа перечислены, а не поставлены в ноль. Каждая точка ведёт к карточке работы."),
}
LABEL_SET = {"w": {"sim": ["anthropic-c-compiler", "opus55-card", "agensh-1024", "openai-navier-stokes", "anthropic-institute-pace"],
                   "cum": ["anthropic-art-enzymes", "hf-incident-case", "moltbook-illusion", "lai-looking-for-something-weird"],
                   "cap": ["grok-420-multi-agent", "kimi-agent-swarm", "wiz-moltbook", "superminds-test"]},
             "n": {"sim": ["agensh-1024", "openai-navier-stokes", "anthropic-institute-pace"],
                   "cum": ["hf-incident-case", "lai-looking-for-something-weird"],
                   "cap": ["kimi-agent-swarm", "wiz-moltbook"]}}


def scale_layers():
    """The three quantities are kept apart: each work appears in a layer only with the number of that kind."""
    L = {"sim": [], "cum": [], "cap": [], "none": []}
    for w in CORPUS:
        c = w["corpus"]; k = c.get("scale_kind")
        if k == "simultaneous" and isinstance(c.get("agents_max_simultaneous"), (int, float)):
            L["sim"].append((w, c["agents_max_simultaneous"]))
            if isinstance(c.get("agents_total"), (int, float)): L["cum"].append((w, c["agents_total"]))
        elif k == "cumulative_only" and isinstance(c.get("agents_total"), (int, float)):
            L["cum"].append((w, c["agents_total"]))
        elif k == "capacity":
            v = c.get("agents_max_simultaneous") or c.get("agents_total")
            if isinstance(v, (int, float)): L["cap"].append((w, v))
        else:
            L["none"].append((w, None))
    return L


SCALE_L = scale_layers()
assert len(SCALE_L["sim"]) == 99 and len(SCALE_L["none"]) == 36, {k: len(v) for k, v in SCALE_L.items()}
SIM_VALUES = [v for _, v in SCALE_L["sim"]]
SIM_MEDIAN = statistics.median(SIM_VALUES)
THRESH = [(t, sum(1 for v in SIM_VALUES if v >= t)) for t in (10, 100, 1000, 10000)]
assert SIM_MEDIAN == 7 and THRESH == [(10, 42), (100, 15), (1000, 7), (10000, 4)], (SIM_MEDIAN, THRESH)

GEO = {"w": dict(W=1000, x0=26, x1=974, r=5.4, gap=1.6, row_pad=26, top=34, axis_h=58, lab_fs=13),
       "n": dict(W=360, x0=12, x1=348, r=4.1, gap=1.2, row_pad=24, top=30, axis_h=62, lab_fs=12)}
XMAX = {"sim": 4.75, "cum": 5.55, "cap": 6.55}


def swarm_rows(points, v, layer, roomy=()):
    """Beeswarm per evidence row on a log axis; returns rows [(evidence, [(w, value, x, y)])], total height.
    Rows in `roomy` get extra space between their name and their dots, for a direct label to sit there."""
    G = GEO[v]; r, step = G["r"], 2 * G["r"] + G["gap"]
    lo, hi = 0.0, XMAX[layer]
    def X(val): return G["x0"] + (math.log10(max(val, 1)) - lo) / (hi - lo) * (G["x1"] - G["x0"])
    by = OrderedDict((e, []) for e in EVID_ROWS)
    for w, val in points: by[w["corpus"]["evidence"]].append((w, val))
    rows, y = [], G["top"]
    for e, pts in by.items():
        if not pts: continue
        placed = []
        for w, val in sorted(pts, key=lambda p: (p[1], p[0]["id"])):
            x = X(val); k = 0; spot = None
            while spot is None:
                for s in ([0] if k == 0 else [k, -k]):
                    oy = s * step * 0.9
                    if all((x - px) ** 2 + (oy - py) ** 2 >= (step - .2) ** 2 for _, _, px, py in placed):
                        spot = oy; break
                k += 1
            placed.append((w, val, x, spot))
        lo_y = min(p[3] for p in placed); hi_y = max(p[3] for p in placed)
        extra = 16 if e in roomy else 0
        band = (hi_y - lo_y) + 2 * r + G["row_pad"] + 14 + extra
        cy = y + 18 + extra + (-lo_y) + r
        rows.append((e, [(w, val, x, cy + oy) for w, val, x, oy in placed], y, band))
        y += band
    return rows, y, X


def scale_svg(lang, v, layer):
    T = SK[lang]; G = GEO[v]
    pts = SCALE_L[layer]
    labset = set(LABEL_SET[v].get(layer, []))
    qty = {"sim": T["at_once"], "cum": T["total"], "cap": T["cap_k"]}[layer]
    roomy = {w["corpus"]["evidence"] for w, _ in pts if w["id"] in labset} if v == "n" else ()   # phones: room for the labels
    rows, y_end, X = swarm_rows(pts, v, layer, roomy)
    H_ = y_end + G["axis_h"]
    o = [f'<svg class="sk-svg sk-{v}" viewBox="0 0 {G["W"]} {n(H_)}" role="img" aria-label="{esc(T["axis"][layer])}">']
    # decade grid and axis
    ticks = [t for t in T["ticks"] if math.log10(t) <= XMAX[layer] + 1e-9]
    for t in ticks:
        x = X(t)
        o.append(f'<line class="grid" x1="{n(x)}" x2="{n(x)}" y1="{G["top"] - 6}" y2="{n(y_end)}"/>'
                 f'<text class="tk" x="{n(x)}" y="{n(y_end + 22)}" text-anchor="middle">{esc(T["ticks"][t])}</text>')
    o.append(f'<text class="axl" x="{G["x0"]}" y="{n(y_end + 46)}">{esc(T["axis"][layer])}</text>')
    if layer == "sim":
        xm = X(SIM_MEDIAN)
        o.append(f'<line class="med" x1="{n(xm)}" x2="{n(xm)}" y1="{G["top"] - 14}" y2="{n(y_end)}"/>'
                 f'<text class="medl" x="{n(xm + 6)}" y="{G["top"] - 4}">{esc(T["med"].format(v=fnum(SIM_MEDIAN, lang)))}</text>')
    for e, items, y0, band in rows:
        o.append(f'<text class="rowl" x="{G["x0"]}" y="{n(y0 + 12)}">{esc(H["evid"](e, lang))} · {len(items)}</text>')
        o.append(f'<line class="rowr" x1="{G["x0"]}" x2="{G["x1"]}" y1="{n(y0 + band)}" y2="{n(y0 + band)}"/>')
        for w, val, x, yy in items:
            href = H["card_href"](w["id"])
            title = H["card_title"](w, lang)
            note = H["scale_note"](w, lang)
            lab = T["labels"].get(w["id"]) if w["id"] in labset else None
            aria = f'{title}: {fnum(val, lang)}, {qty}; {H["evid"](e, lang)}' + (f'. {note}' if note else "")
            o.append(f'<a class="dot{" hl" if lab else ""}" href="{esc(href)}" aria-label="{esc(aria)}" data-w="{esc(w["id"])}" data-t="{esc(title)}" data-v="{esc(fnum(val, lang))}" '
                     f'data-e="{esc(H["evid"](e, lang))}" data-note="{esc(note)}"><circle class="hit" cx="{n(x)}" cy="{n(yy)}" r="{G["r"] + 5}"/><circle class="mk" cx="{n(x)}" cy="{n(yy)}" r="{G["r"]}"/></a>')
    # direct labels for a few works. Each hangs on a short vertical leader from its own dot, so a label that has to pass
    # over a neighbouring dot still points at the right one; where no leader fits, the label sits on the dot's own line
    # right beside it. Candidate spots above and below the dot, on either side of the leader, then beside it; the first
    # wins that clears the dots, the row names (13 px, bold) and earlier labels with both text and leader, and that does
    # not pass over another labelled dot; only if no spot does is passing over one allowed.
    placed = [(G["x0"], y0 + 12 - 13, G["x0"] + len(f'{H["evid"](e, lang)} · {len(items)}') * 13 * 0.6, y0 + 15) for e, items, y0, band in rows]
    dots_xy = [(x, yy) for _, items, _, _ in rows for _, _, x, yy in items]
    fs, r = G["lab_fs"], G["r"]
    marked = [(x, yy) for _, items, _, _ in rows for w, _, x, yy in items if w["id"] in labset and T["labels"].get(w["id"])]
    def free(bx0, by0, bx1, by1):
        if bx0 < 2 or bx1 > G["W"] - 2: return False
        if any(not (bx1 < a0 or bx0 > a1 or by1 < b0 or by0 > b1) for a0, b0, a1, b1 in placed): return False
        return not any(bx0 - r < dx < bx1 + r and by0 - r < dy < by1 + r for dx, dy in dots_xy)
    def leader_free(x, ya, yb):   # the vertical segment x, ya..yb (ya < yb) misses other dots and every placed box
        if any(abs(dx - x) < r + 1.5 and ya - r < dy < yb + r for dx, dy in dots_xy if (dx, dy) != (x, yy)): return False
        return not any(a0 - 1 <= x <= a1 + 1 and not (yb < b0 or ya > b1) for a0, b0, a1, b1 in placed)
    def over_marked(x, bx0, by0, bx1, by1):
        return any((mx, my) != (x, yy) and bx0 - r <= mx <= bx1 + r and by0 - 2 * fs <= my <= by1 + 2 * fs for mx, my in marked)
    for e, items, y0, band in rows:
        for w, val, x, yy in sorted(items, key=lambda it: -it[2]):
            lab = T["labels"].get(w["id"]) if w["id"] in labset else None
            if not lab: continue
            tw = len(lab) * fs * 0.56
            cands = []
            for k in range(3):   # tiers above and below: the leader ends level with the middle of the text
                up = r + 9 + k * (fs + 4)
                for side in (-1, 1):
                    end = yy + side * (up + .35 * fs)
                    lead = (min(yy + side * (r + 1.5), end), max(yy + side * (r + 1.5), end))
                    cands += [(x + 5, end + .35 * fs, "start", lead), (x - 5, end + .35 * fs, "end", lead)]
            cands += [(x + r + 4, yy + .35 * fs, "start", None), (x - r - 4, yy + .35 * fs, "end", None)]   # beside the dot
            spot = None
            for strict in (True, False):
                for lx, ly, anc, lead in cands:
                    bx0 = lx if anc == "start" else lx - tw
                    box = (bx0, ly - fs, bx0 + tw, ly + 3)
                    if free(*box) and (not lead or leader_free(x, *lead)) and not (strict and over_marked(x, *box)):
                        spot = (lx, ly, anc, lead, box); break
                if spot: break
            if not spot: continue
            lx, ly, anc, lead, box = spot
            placed.append(box)
            if lead:
                ya, yb = lead
                placed.append((x - 1, ya, x + 1, yb))
                o.append(f'<line class="dll" data-w="{esc(w["id"])}" x1="{n(x)}" x2="{n(x)}" y1="{n(ya if ly < yy else yb)}" y2="{n(yb if ly < yy else ya)}"/>')
            o.append(f'<text class="dl" data-w="{esc(w["id"])}" x="{n(lx)}" y="{n(ly)}" text-anchor="{anc}">{esc(lab)}</text>')
    o.append("</svg>")
    return "".join(o)


def plural(k, forms, lang):
    if lang == "en": return forms[0] if k == 1 else forms[1]
    n10, n100 = k % 10, k % 100
    if n10 == 1 and n100 != 11: return forms[0]
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14: return forms[1]
    return forms[2]


def scale(lang, ctx):
    T = SK[lang]; st = site_story_T(lang)
    sid = sid_for("scale", lang, ctx)
    radios, labels, layers = [], [], []
    for i, (k, lab) in enumerate(T["tabs"]):
        cnt = len(SCALE_L[k])
        radios.append(f'<input type="radio" class="sk-r" name="{sid}-m" id="{sid}-{k}" value="{k}"{" checked" if i == 0 else ""}>')
        labels.append(f'<label for="{sid}-{k}" class="sk-tab"><span>{esc(lab)}</span><b>{cnt}</b></label>')
    for k, _ in T["tabs"]:
        cnt = len(SCALE_L[k])
        lead = T["lead"][k].format(n=cnt, med=fnum(SIM_MEDIAN, lang))
        if k == "none":
            items = sorted(SCALE_L["none"], key=lambda p: H["card_title"](p[0], lang).lower())
            body = '<ul class="sk-none">' + "".join(f'<li><a href="{esc(H["card_href"](w["id"]))}">{esc(H["card_title"](w, lang))}</a> <span>{esc(H["evid"](w["corpus"]["evidence"], lang))}</span></li>' for w, _ in items) + "</ul>"
        else:
            body = scale_svg(lang, "w", k) + scale_svg(lang, "n", k)
        layers.append(f'<div class="sk-lay sk-lay-{k}" data-lay="{k}"><p class="sk-lead">{esc(lead)}</p>{body}</div>')
    # the threshold ladder (computed; the example rows are the approved prologue's, each linked to its card)
    lad = []
    for t, cnt in THRESH:
        text, wid = st["sc_rows"][t]
        lad.append(f'<li style="--v:{cnt};--of:{len(SIM_VALUES)}"><span class="th">≥{NB}{fnum(t, lang)}</span><span class="bar"><i></i></span><b class="v">{cnt}</b>'
                   f'<span class="ex">{text.replace("{nb}", NB)} <a class="exl" href="{esc(H["card_href"](wid))}" aria-label="{esc(st["sc_card"])}">→</a></span></li>')
    ladder = (f'<div class="sk-ladder" id="scale"><div class="hero-num"><b>{fnum(SIM_MEDIAN, lang)}</b><p>{esc(st["sc_unit"].format(known=len(SIM_VALUES), corpus=len(CORPUS), nb=NB))}</p></div>'
              f'<div class="ladder"><p class="fig-t">{esc(st["sc_fig"].format(known=len(SIM_VALUES), nb=NB))}</p><ol>{"".join(lad)}</ol>'
              f'<p class="src">{esc(LADDER_SRC[lang].format(known=len(SIM_VALUES), corpus=len(CORPUS)))}</p></div></div>')
    # data table: every work in its layer
    rows = []
    for k, lab in T["tabs"][:3]:
        for w, val in sorted(SCALE_L[k], key=lambda p: -p[1]):
            rows.append(f'<tr><td>{esc(lab)}</td><td class="num">{esc(fnum(val, lang))}</td><td><a href="{esc(H["card_href"](w["id"]))}">{esc(H["card_title"](w, lang))}</a></td>'
                        f'<td>{esc(H["evid"](w["corpus"]["evidence"], lang))}</td><td>{esc(H["scale_note"](w, lang))}</td></tr>')
    head = {"en": ("Quantity", "Number", "Work", "Evidence class", "What was counted"), "ru": ("Величина", "Число", "Работа", "Класс доказательств", "Что посчитано")}[lang]
    table = (f'<details class="sc-data"><summary>{UI[lang]["table"]}</summary><div class="table-wrap" data-cols="5" tabindex="0"><table><thead><tr>'
             + "".join(f"<th>{h}</th>" for h in head) + f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>')
    art = (f'<div class="sk" data-sk>{"".join(radios)}<div class="sk-tabs" role="group">{"".join(labels)}</div>'
           f'<div class="sk-plot">{"".join(layers)}<div class="sk-tip" aria-hidden="true"></div></div></div>')
    ctx["native"] = esc(T["cap"])
    return frame("scale", lang, sid, art, title={"en": "How many agents there really are", "ru": "Сколько агентов на самом деле"}[lang],
                 badge="dat", fig=ctx, after=ladder + table)


LADDER_SRC = {"en": "Bars show the share of the {known} works. The survey's count over {corpus} works, cut-off 3 October 2026.",
              "ru": "Полоса — доля от {known}\u00a0работ. Расчёт обзора по {corpus} работам, срез 3 октября 2026."}


def site_story_T(lang):
    import site_story
    return site_story.T[lang]


# ---------------------------------------------------------------- Fig. 1.3–1.6: publication rhythm, organizations, models, topics × evidence
MONTHS_SHORT = {"en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "ru": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]}
STYPE_GROUP = {"preprint": "pre", "peer_reviewed": "peer"}
STYPE_LAB = {"en": {"preprint": "preprints", "peer_reviewed": "peer-reviewed", "lab_report": "lab blogs and reports", "essay_blog": "essays and interviews",
                    "incident_report": "incident investigations", "system_card": "system cards", "dataset_platform": "dataset"},
             "ru": {"preprint": "препринты", "peer_reviewed": "рецензированные", "lab_report": "блоги и отчёты лабораторий", "essay_blog": "эссе и интервью",
                    "incident_report": "расследования инцидентов", "system_card": "системные карты", "dataset_platform": "датасет"}}
RH = {"en": dict(title="Works by month of first publication", groups=[("pre", "preprints"), ("peer", "peer-reviewed"), ("oth", "lab reports, essays, investigations, system cards, dataset")],
                 early="{n} more before 2025.", peak="September 2026: {n} works", aug="August: {n}", per="works per month", total="{n} works"),
      "ru": dict(title="Работы по месяцу первой публикации", groups=[("pre", "препринты"), ("peer", "рецензированные"), ("oth", "отчёты лабораторий, эссе, расследования, системные карты, датасет")],
                 early="Ещё {n} — раньше 2025 года.", peak="Сентябрь 2026: {n} работ", aug="август: {n}", per="работ в месяц", total="{n} работ")}


def rhythm(lang, ctx):
    T = RH[lang]
    months, y, m = [], 2025, 1
    while (y, m) <= (2026, 10):
        months.append(f"{y}-{m:02d}"); m += 1
        if m == 13: y, m = y + 1, 1
    cnt = {mm: Counter() for mm in months}
    early = 0
    for w in CORPUS:
        mo = w["corpus"].get("month") or ""
        if mo < "2025-01": early += 1; continue
        if mo in cnt: cnt[mo][w["corpus"]["source_type"]] += 1
    mx = max(sum(c.values()) for c in cnt.values())
    assert sum(cnt["2026-09"].values()) == 48 and sum(cnt["2026-08"].values()) == 15 and early == 1
    cols = []
    for i, mm in enumerate(months):
        c = cnt[mm]; tot = sum(c.values())
        g = Counter()
        for k, v in c.items(): g[STYPE_GROUP.get(k, "oth")] += v
        tip = " · ".join(f"{STYPE_LAB[lang][k]} {v}" for k, v in sorted(c.items(), key=lambda kv: -kv[1]))
        mon = MONTHS_SHORT[lang][int(mm[5:]) - 1] + (f" {mm[:4]}" if mm.endswith("-01") else "")
        segs = "".join(f'<i class="g-{k}" style="--h:{g[k] / mx:.4f}"></i>' for k, _ in T["groups"] if g[k])
        cls = " pk" if mm == "2026-09" else ""
        cols.append(f'<li class="rb{cls}" style="--k:{i}" data-tip="{esc(mon)}: {tot} — {esc(tip)}" tabindex="0"><span class="rb-bar" style="--t:{tot / mx:.4f}">{segs}</span>'
                    f'<span class="rb-v">{tot or ""}</span><span class="rb-m">{esc(mon)}</span></li>')
    legend = "".join(f'<li><i class="g-{k}"></i>{esc(lab)}</li>' for k, lab in T["groups"])
    art = (f'<div class="rh"><ul class="sc-legend">{legend}</ul><div class="rh-plot"><p class="rh-ann">{esc(T["peak"].format(n=48))} · {esc(T["aug"].format(n=15))}</p>'
           f'<ol class="rh-bars" style="--max:{mx}">{"".join(cols)}</ol></div><p class="rh-early">{esc(T["early"].format(n=early))}</p><div class="sc-tip" aria-hidden="true"></div></div>')
    return frame("rhythm", lang, sid_for("rhythm", lang, ctx), art, title=esc(T["title"]), badge="dat", fig=ctx)


ORG = {"en": dict(title="Who publishes", a="Organization class (one per work)", b="Most frequent organizations (a work may name several)",
                  cls={"academia": "Universities", "mixed": "Universities and industry jointly", "frontier_lab": "Frontier labs", "independent": "Independent researchers and non-profits", "industry": "Other companies"}),
       "ru": dict(title="Кто публикует", a="Класс организации (один на работу)", b="Самые частые организации (у работы их может быть несколько)",
                  cls={"academia": "Университеты", "mixed": "Университеты и индустрия вместе", "frontier_lab": "Фронтир-лаборатории", "independent": "Независимые исследователи и некоммерческие", "industry": "Другие компании"})}
ORG_RU = {"Stanford University": "Стэнфорд", "University of Oxford": "Оксфорд", "Carnegie Mellon University": "Карнеги-Меллон", "University of Chicago": "Чикагский университет",
          "UC Berkeley": "Беркли", "Harvard University": "Гарвард", "Tsinghua University": "Университет Цинхуа", "Princeton University": "Принстон"}


def bars(items, mx, cls=""):
    return (f'<ol class="hb{(" " + cls) if cls else ""}">' + "".join(
        f'<li style="--v:{v / mx:.4f};--k:{i}" tabindex="0" data-tip="{esc(lab)}: {v}"><span class="hb-l">{esc(lab)}</span><span class="hb-b"><i></i></span><b class="hb-v">{v}</b></li>'
        for i, (lab, v) in enumerate(items)) + "</ol>")


def orgs(lang, ctx):
    T = ORG[lang]
    c = Counter(w["corpus"].get("org_class") for w in CORPUS)
    order = ["academia", "mixed", "frontier_lab", "independent", "industry"]
    assert [c[k] for k in order] == [53, 41, 30, 19, 10]
    oc = Counter(o for w in CORPUS for o in set(w.get("orgs") or []))
    top = oc.most_common(14)
    assert top[0] == ("Anthropic", 25) and top[1] == ("Stanford University", 16)
    lab = (lambda o: ORG_RU.get(o, o)) if lang == "ru" else (lambda o: o)
    art = (f'<div class="two"><div><p class="sc-sub">{esc(T["a"])}</p>{bars([(T["cls"][k], c[k]) for k in order], max(c.values()))}</div>'
           f'<div><p class="sc-sub">{esc(T["b"])}</p>{bars([(lab(o), v) for o, v in top], top[0][1], "thin")}</div></div><div class="sc-tip" aria-hidden="true"></div>')
    return frame("orgs", lang, sid_for("orgs", lang, ctx), art, title=esc(T["title"]), badge="dat", fig=ctx)


MOD = {"en": dict(title="Which models are in the swarms", a="Works that involve each model family (a work may involve several)", b="Different models in one work",
                  fam={"OpenAI GPT": "OpenAI", "Anthropic Claude": "Claude", "Qwen": "Qwen", "Google Gemini": "Gemini", "DeepSeek": "DeepSeek", "Meta Llama": "Llama",
                       "other open": "other open models", "xAI Grok": "Grok", "Kimi": "Kimi", "Mistral": "Mistral", "GLM": "GLM", "other closed": "other closed models"},
                  bins=["1 model", "2–3", "4–9", "10 or more"], comp="Where the composition is known: copies of one model — {a} works, a mix of models — {b}. {c} works do not state the number of models or use none."),
       "ru": dict(title="Какие модели работают в роях", a="Работы с моделями каждого семейства (в работе их может быть несколько)", b="Разных моделей в одной работе",
                  fam={"OpenAI GPT": "OpenAI", "Anthropic Claude": "Claude", "Qwen": "Qwen", "Google Gemini": "Gemini", "DeepSeek": "DeepSeek", "Meta Llama": "Llama",
                       "other open": "другие открытые", "xAI Grok": "Grok", "Kimi": "Kimi", "Mistral": "Mistral", "GLM": "GLM", "other closed": "другие закрытые"},
                  bins=["1 модель", "2–3", "4–9", "10 и больше"], comp="Где состав известен: копии одной модели — {a} работ, смесь моделей — {b}. {c} работы не называют число моделей или обходятся без них.")}


def models(lang, ctx):
    T = MOD[lang]
    fc = Counter(f for w in CORPUS for f in set(w["corpus"].get("model_families") or []))
    fams = fc.most_common()
    assert fc["OpenAI GPT"] == 89 and fc["Anthropic Claude"] == 83
    ns = [w["corpus"].get("n_models") for w in CORPUS if isinstance(w["corpus"].get("n_models"), int) and w["corpus"]["n_models"] > 0]
    vals = [sum(1 for x in ns if x == 1), sum(1 for x in ns if 2 <= x <= 3), sum(1 for x in ns if 4 <= x <= 9), sum(1 for x in ns if x >= 10)]
    assert vals == [10, 22, 48, 31] and len(CORPUS) - len(ns) == 42
    mix = sum(1 for w in CORPUS if w["corpus"].get("mixed_swarm") is True); mono = sum(1 for w in CORPUS if w["corpus"].get("mixed_swarm") is False)
    cols = "".join(f'<li style="--v:{v / max(vals):.4f};--k:{i}" tabindex="0" data-tip="{esc(b)}: {v}"><span class="vb-b"><i></i></span><b class="vb-v">{v}</b><span class="vb-l">{esc(b)}</span></li>'
                   for i, (b, v) in enumerate(zip(T["bins"], vals)))
    art = (f'<div class="two"><div><p class="sc-sub">{esc(T["a"])}</p>{bars([(T["fam"].get(f, f), v) for f, v in fams], fams[0][1], "thin")}</div>'
           f'<div><p class="sc-sub">{esc(T["b"])}</p><ol class="vb">{cols}</ol><p class="sc-sub2">{esc(T["comp"].format(a=mono, b=mix, c=len(CORPUS) - len(ns)))}</p></div></div><div class="sc-tip" aria-hidden="true"></div>')
    return frame("models", lang, sid_for("models", lang, ctx), art, title=esc(T["title"]), badge="dat", fig=ctx)


TOPIC_ORDER = ["scaling_economics", "self_organization", "memory", "safety_alignment", "contagion_security", "echo_diversity", "social_dynamics", "wild_field", "infrastructure", "training_rl", "theory"]
EVID_COLS = ["live_experiment", "engineering_report", "benchmark", "field_observation", "incident", "system_card_eval", "theory_essay", "surrogate_simulation"]
TP = {"en": dict(title="Map of topics and evidence", go="Open these works in the atlas", cell="{t} × {e}: {v} works", none="none"),
      "ru": dict(title="Карта тем и доказательств", go="Открыть эти работы в атласе", cell="{t} × {e}: {v}", none="нет")}


def topic_grid():
    g = {t: {e: 0 for e in EVID_COLS} for t in TOPIC_ORDER}
    for w in CORPUS:
        e = w["corpus"].get("evidence")
        for t in w["corpus"].get("topics") or []:
            if t in g and e in g[t]: g[t][e] += 1
    return g


TOPIC_G = topic_grid()
assert sum(TOPIC_G["scaling_economics"].values()) == 69 and TOPIC_G["social_dynamics"]["live_experiment"] == 41
# Break points for the longest one-word row labels; they only take effect where the label cell is narrow (phones).
SOFT = {"Самоорганизация": "Само\u00adорганизация", "Безопасность": "Безопас\u00adность", "разнообразие": "разно\u00adобразие", "симуляторы": "симу\u00adляторы"}


def soft(label):
    for w, h in SOFT.items(): label = label.replace(w, h)
    return label


def topics(lang, ctx, compact=False):
    T = TP[lang]
    mx = max(max(r.values()) for r in TOPIC_G.values())
    head = '<div class="tm-c tm-corner"></div>' + "".join(f'<div class="tm-c tm-eh" title="{esc(H["evid"](e, lang))}"><span>{esc(H["evid"](e, lang))}</span></div>' for e in EVID_COLS)
    cells = []
    for t in TOPIC_ORDER:
        tot = sum(TOPIC_G[t].values())
        cells.append(f'<div class="tm-c tm-th"><span>{soft(esc(H["topic"](t, lang)))}</span><b>{tot}</b></div>')
        for e in EVID_COLS:
            v = TOPIC_G[t][e]
            if not v:
                cells.append('<div class="tm-c tm-0"></div>'); continue
            lab = T["cell"].format(t=H["topic"](t, lang), e=H["evid"](e, lang), v=v)
            sv = math.sqrt(v / mx)
            cells.append(f'<a class="tm-c tm-v{" out" if sv < 0.42 else ""}" href="#atlas" data-ft="{t}" data-fe="{e}" style="--s:{sv:.4f}" aria-label="{esc(lab)}" data-tip="{esc(lab)}">'
                         f'<i></i><span>{v}</span></a>')
    art = f'<div class="tm{" tm-compact" if compact else ""}" style="--cols:{len(EVID_COLS)}">{head}{"".join(cells)}</div><div class="sc-tip" aria-hidden="true"></div>'
    if compact:
        return art
    return frame("topics", lang, sid_for("topics", lang, ctx), art, title=esc(T["title"]), badge="dat", fig=ctx)


def atlasmap(lang, ctx):
    T = {"en": "Topic × evidence: pick a cell to filter the list", "ru": "Тема × доказательства: клетка фильтрует список"}[lang]
    return f'<div class="atlasmap js-only" data-scene="atlasmap"><p class="sc-sub">{T}</p>{topics(lang, ctx, compact=True)}</div>'


# ---------------------------------------------------------------- dispatch (mechanism scenes are defined in scenes_mech.py)
def html(name, lang, ctx):
    from scenes_mech import MECH
    fn = {"fieldmap": fieldmap, "scale": scale, "rhythm": rhythm, "orgs": orgs, "models": models, "topics": topics, "atlasmap": atlasmap}.get(name) or MECH.get(name)
    if not fn:
        raise KeyError(f"unknown scene {name}")
    return fn(lang, dict(ctx or {}))


def table(name, lang, table_html):
    from scenes_mech import TABLES
    return TABLES[name](lang, table_html)

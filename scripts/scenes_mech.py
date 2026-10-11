#!/usr/bin/env python3
"""Mechanism scenes of the longread, drawn with the prologue's grammar: agents as chips or dots, an emerald mark
for a finding or correct knowledge, coral for an error, a fake or an infection, blue for a shared store.

Every number printed in a scene is quoted from the card the scene follows (named in the caption) and keeps that
card's comparison condition. The motion between those numbers is schematic. Each scene's static markup is its
end state, so the page reads the same without JavaScript or with reduced motion.
"""
import json, math, random, re

import site_story
from scenes import frame, esc, fnum, pct, n, plural, NB, H, UI

# ---------------------------------------------------------------- λ: parallel work buys time with tokens (ch. 4)
# A calculator of the rule in the λ box: N agents finish N^λ times faster at N^(1−λ) times the tokens. The rule's
# numbers are not measurements; the one measured speed-up quoted (2–2.8× on SEC-Bench Pro) is said to be separate.
LX = {
 "en": dict(title="Parallel work: time against tokens", one="1 agent", many="{n} {w}", w=("agent", "agents"), time="time to the same result", tok="tokens for the same result",
            read="By the formula, at N = {n} and λ = {l}: {t} of the time, {c} the tokens.",
            ext=" Terminal-Bench 2.1 was measured only at 1 and 4 agents, so this is an extrapolation.",
            beats=["One agent works alone: the upper bar is its time to a result, the lower bar the tokens it spends.",
                   "For 16 agents at λ = 0.57, Ord’s estimate for SEC-Bench Pro, the scaling rule predicts about one fifth of the time…",
                   "…at about 3.3 times the tokens. That is the formula; from OpenAI’s simulated latencies we estimate a 2–2.8× speed-up on SEC-Bench Pro.",
                   "Across OpenAI’s three benchmarks λ was 0.48–0.68. At λ = 1 the work would divide without loss."],
            lam="λ", n_lab="agents", meas={0.48: "Terminal-Bench 2.1, measured at 1 and 4 agents", 0.57: "SEC-Bench Pro", 0.68: "BrowseComp", 0.5: "example in the box", 1.0: "ideal division"},
            chart_t="Speed-up and token cost against team size", speed="faster", cost="more tokens",
            src="λ: Toby Ord’s estimates from OpenAI’s GPT-5.6 Sol charts, one model, up to 16 agents (card below). Terminal-Bench 2.1 was measured only at 1 and 4 agents; beyond 4 its line is an extrapolation.",
            note="Calculated from the rule in the box above: N agents finish N^λ times faster at N^(1−λ) times the tokens."),
 "ru": dict(title="Параллельная работа: время против токенов", one="1 агент", many="{n} {w}", w=("агент", "агента", "агентов"), time="время до того же результата", tok="токены на тот же результат",
            read="По формуле при N = {n} и λ = {l}: {t} времени, {c} токенов.",
            ext=" Terminal-Bench 2.1 измеряли только на 1 и 4 агентах, так что это экстраполяция.",
            beats=["Один агент работает сам: верхняя полоса — его время до результата, нижняя — потраченные токены.",
                   "Для 16 агентов при λ = 0,57 — оценке Орда для SEC-Bench Pro — формула даёт примерно пятую часть времени…",
                   "…при расходе примерно в 3,3 раза больше токенов. Это расчёт по формуле; по смоделированным OpenAI задержкам мы оцениваем ускорение на SEC-Bench Pro в 2–2,8 раза.",
                   "На трёх бенчмарках OpenAI λ было 0,48–0,68. При λ = 1 работа делилась бы без потерь."],
            lam="λ", n_lab="агентов", meas={0.48: "Terminal-Bench 2.1, замеры на 1 и 4 агентах", 0.57: "SEC-Bench Pro", 0.68: "BrowseComp", 0.5: "пример из врезки", 1.0: "идеальное деление труда"},
            chart_t="Ускорение и расход токенов в зависимости от размера команды", speed="быстрее", cost="больше токенов",
            src="λ — оценки Тоби Орда по графикам OpenAI для GPT-5.6 Sol: одна модель, не больше 16 агентов (карточка ниже). Terminal-Bench 2.1 измеряли только на 1 и 4 агентах; дальше 4 его линия — экстраполяция.",
            note="Расчёт по правилу из врезки выше: N агентов справляются в N^λ раз быстрее при расходе в N^(1−λ) раз больше токенов."),
}
LX_EXTRA = (16, 0.48)      # the one choice the scene offers outside the measured range


def lam_parts(lang, N, lam):
    t = N ** (-lam); c = N ** (1 - lam)
    tt = "1/" + fnum(1 / t, lang, 1).rstrip("0").rstrip(".,")
    cc = "×" + (str(int(round(c))) if abs(c - round(c)) < 0.01 else fnum(c, lang, 2 if c < 10 else 1))
    lamv = fnum(lam, lang, 2).rstrip("0").rstrip(".,") if lam != 1 else "1"
    return tt, cc, lamv


def lam_readout(lang, N, lam):
    tt, cc, lamv = lam_parts(lang, N, lam)
    return LX[lang]["read"].format(n=N, l=lamv, t=tt, c=cc) + (LX[lang]["ext"] if (N, lam) == LX_EXTRA else "")


def lam_who(lang, N):
    T = LX[lang]
    return T["many"].format(n=N, w=plural(N, T["w"], lang))


def label_ys(a, b, gap=16):
    """The two curve labels sit at the ends of their curves; where the ends nearly meet (λ near 0.5) they move a line
    apart around the meeting point, the label of the higher curve on top. Only the labels move: curves and marks stay exact."""
    if abs(a - b) >= gap: return a, b
    m = (a + b) / 2
    return (m - gap / 2, m + gap / 2) if a <= b else (m + gap / 2, m - gap / 2)


def lam_chart(lang, lam=0.57, N=16):
    """Log-log: speed-up N^λ and token cost N^(1−λ) for N = 1…16, with the measured band 0.48–0.68."""
    T = LX[lang]
    W, Hh, x0, x1, y0, y1 = 340, 230, 40, 322, 196, 20
    def X(nn): return x0 + math.log2(nn) / 4 * (x1 - x0)
    def Y(f): return y0 - math.log2(f) / 4 * (y0 - y1)      # factor 1…16
    def path(fn): return "M" + " L".join(f"{n(X(nn))} {n(Y(fn(nn)))}" for nn in [1 + i * 15 / 60 for i in range(61)])
    band_s = path(lambda nn: nn ** 0.68) + " L" + " L".join(f"{n(X(nn))} {n(Y(nn ** 0.48))}" for nn in [16 - i * 15 / 60 for i in range(61)]) + " Z"
    band_c = path(lambda nn: nn ** 0.52) + " L" + " L".join(f"{n(X(nn))} {n(Y(nn ** 0.32))}" for nn in [16 - i * 15 / 60 for i in range(61)]) + " Z"
    o = [f'<svg class="lx-chart" viewBox="0 0 {W + 96} {Hh}" role="img" aria-label="{esc(T["chart_t"])}">']
    for f in (1, 2, 4, 8, 16):
        o.append(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{n(Y(f))}" y2="{n(Y(f))}"/><text class="tky" x="{x0 - 8}" y="{n(Y(f))}" dy=".35em">×{f}</text>')
    for nn in (1, 2, 4, 8, 16):
        o.append(f'<text class="tk" x="{n(X(nn))}" y="{y0 + 20}" text-anchor="middle">{nn}</text>')
    o.append(f'<text class="axl" x="{x1}" y="{y0 + 34}" text-anchor="end">{esc(T["n_lab"])}</text>')
    o.append(f'<path class="band b-s" d="{band_s}"/><path class="band b-c" d="{band_c}"/>')
    o.append(f'<path class="crv c-s" data-k="s" d="{path(lambda nn: nn ** lam)}"/><path class="crv c-c" data-k="c" d="{path(lambda nn: nn ** (1 - lam))}"/>')
    o.append(f'<circle class="mk m-s" cx="{n(X(N))}" cy="{n(Y(N ** lam))}" r="5"/><circle class="mk m-c" cx="{n(X(N))}" cy="{n(Y(N ** (1 - lam)))}" r="5"/>')
    ys, yc = label_ys(Y(16 ** lam), Y(16 ** (1 - lam)))
    o.append(f'<text class="cl cl-s" x="{x1 + 8}" y="{n(ys)}" dy=".35em">{esc(T["speed"])}</text>'
             f'<text class="cl cl-c" x="{x1 + 8}" y="{n(yc)}" dy=".35em">{esc(T["cost"])}</text>')
    o.append("</svg>")
    return "".join(o)


def lam(lang, ctx):
    T = LX[lang]
    N, l = 16, 0.57
    tt, cc, _ = lam_parts(lang, N, l)
    tracks = "".join(f'<i style="--k:{i}"></i>' for i in range(N))
    lanes = (f'<div class="lx" data-n="{N}" data-l="{l}" style="--t:{N ** -l:.4f};--c:{N ** (1 - l):.4f}">'
             f'<p class="lx-k">{esc(T["time"])}</p>'
             f'<div class="lx-row lx-one"><span class="lx-who">{esc(T["one"])}</span><span class="lx-tr"><i></i></span><b class="lx-v">1</b></div>'
             f'<div class="lx-row lx-many"><span class="lx-who" data-tpl="{esc(T["many"])}" data-w="{esc("|".join(T["w"]))}">{esc(lam_who(lang, N))}</span><span class="lx-trs">{tracks}</span><b class="lx-v lx-vt">{esc(tt)}</b></div>'
             f'<p class="lx-k">{esc(T["tok"])}</p>'
             f'<div class="lx-row lx-tk1"><span class="lx-who">{esc(T["one"])}</span><span class="lx-tb"><i style="--w:1"></i></span><b class="lx-v">×1</b></div>'
             f'<div class="lx-row lx-tkn"><span class="lx-who lx-who2">{esc(lam_who(lang, N))}</span><span class="lx-tb"><i style="--w:var(--c)"></i></span><b class="lx-v lx-vc">{esc(cc)}</b></div>'
             f'<p class="lx-read" aria-live="polite" data-tpl="{esc(T["read"])}" data-ext="{esc(T["ext"])}" data-extra="{LX_EXTRA[0]} {LX_EXTRA[1]}">{esc(lam_readout(lang, N, l))}</p></div>')
    opts_n = "".join(f'<button type="button" class="opt" data-n="{k}" aria-pressed="{"true" if k == N else "false"}">{k}</button>' for k in (4, 16))
    opts_l = "".join(f'<button type="button" class="opt" data-l="{k}" aria-pressed="{"true" if k == l else "false"}" title="{esc(T["meas"][k])}">{fnum(k, lang, 2).rstrip("0").rstrip(".,") if k != 1 else "1"}</button>'
                     for k in (0.48, 0.5, 0.57, 0.68, 1.0))
    controls = (f'<div class="sc-ctl js-only"><span class="ctl-g"><span class="ctl-l">{esc(T["n_lab"])}</span>{opts_n}</span>'
                f'<span class="ctl-g"><span class="ctl-l">λ</span>{opts_l}</span></div>')
    art = f'<div class="lx-wrap">{lanes}<div class="lx-side">{lam_chart(lang, l, N)}<p class="sc-sub2">{esc(T["src"])}</p></div></div>'
    return frame("lambda", lang, "sc-lambda", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", controls=controls,
                 note=esc(T["note"]))


# ---------------------------------------------------------------- the equalization ledger (ch. 4, first table)
LEDGER_G = ["tok", "lvl", "tok", "tok", "time", "ag", "price", "none", "ag", "tok"]
LG = {"en": dict(order="Order of the text", group="By what was held equal", tok="Matched token budgets or compute", lvl="The same result level; time and tokens compared",
                 time="Time held equal", ag="Number of agents (and actions) held equal", price="Price held equal", none="Nothing held equal"),
      "ru": dict(order="Порядок текста", group="По тому, что уравнено", tok="Сопоставлены бюджеты токенов или вычисления", lvl="Одинаковый уровень результата; сравнивают время и токены",
                 time="Уравнено время", ag="Уравнено число агентов (и действий)", price="Уравнена цена", none="Ничего не уравнено")}


def ledger(lang, table_html):
    T = LG[lang]
    rows = re.findall(r"<tr>", table_html)
    body = table_html.split("<tbody>", 1)
    if len(body) != 2: return table_html
    trs = re.findall(r"<tr>.*?</tr>", body[1], re.S)
    assert len(trs) == len(LEDGER_G), ("ledger rows changed", len(trs))
    new = body[1]
    for i, (tr, g) in enumerate(zip(trs, LEDGER_G)):
        new = new.replace(tr, tr.replace("<tr>", f'<tr data-g="{g}" data-i="{i}">', 1), 1)
    heads = "".join(f'<tr class="lg-h" data-g="{g}" hidden><th colspan="4">{esc(T[g])}</th></tr>' for g in ("tok", "lvl", "time", "ag", "price", "none"))
    new = new.replace("</tbody>", heads + "</tbody>", 1)
    tbl = body[0] + "<tbody>" + new
    tools = (f'<div class="lg-tools js-only" role="group"><button type="button" class="opt" data-mode="text" aria-pressed="true">{esc(T["order"])}</button>'
             f'<button type="button" class="opt" data-mode="group" aria-pressed="false">{esc(T["group"])}</button></div>')
    return f'<div class="ledger" data-scene="ledger" data-sl>{tools}{tbl}</div>'


# ---------------------------------------------------------------- Agensh: the board and the result (ch. 5, after the card)
def agensh(lang, ctx):
    L = site_story.T[lang]
    sub = lambda s: s.replace("{nb}", NB)
    o = ['<section class="scene sc-agensh" id="agensh" data-scene="agensh" aria-labelledby="agensh-t">',
         f'<div class="sc-cap"><p class="sc-kick">{esc(L["ag_eyebrow"])}</p><p class="sc-big" id="agensh-t">{esc(L["ag_h"])}</p></div>',
         '<div class="read">' + "".join(f"<p>{sub(p)}</p>" for p in L["ag_p1"][1:]) + '</div>',
         f'<figure class="chn-fig"><figcaption class="sc-head"><span class="sc-badge b-sch">{UI[lang]["sch"]}</span><span class="sc-title">{esc(L["ag_fig"])}</span></figcaption>'
         f'<div class="chn-art">{site_story.channels_svg(lang)}</div><ul class="fig-key">',
         f'<li><span class="k k-push"></span>{esc(L["ag_key"][0])}</li><li><span class="k k-pull"></span>{esc(L["ag_key"][1])}</li></ul>',
         f'<p class="fig-note">{sub(L["ag_note"])}</p></figure>',
         f'<div class="read"><p class="read-h">{esc(L["ag_h3"])}</p><p>{sub(L["ag_p2"][0])}</p></div>',
         '<div class="result"><figure class="lchart" id="line-chart">',
         f'<figcaption class="fig-t" id="li-t"><span class="sc-badge b-card">{UI[lang]["card"]}</span> {esc(sub(L["ag_chart"]))}</figcaption>', site_story.line_svg(lang),
         '<div class="tip" id="tip" aria-hidden="true"></div>', f'<ul class="rowvals" aria-label="{esc(L["ag_vals"])}">']
    for lab, (v, p) in zip(L["li_rows"], site_story.PANDOC):
        o.append(f'<li><span>{sub(lab)}</span> <b>{site_story.fnum(p, lang, 2)}</b></li>')
    o.append(f'</ul><p class="src">{L["ag_src"]}</p></figure>')
    o.append(f'<aside class="cond" aria-labelledby="h-cond"><h3 id="h-cond">{esc(L["ag_cond"])}</h3><dl>'
             + "".join(f"<dt>{esc(a)}</dt><dd>{sub(b)}</dd>" for a, b in L["ag_dl"]) + '</dl></aside></div></section>')
    return "".join(o)


# ---------------------------------------------------------------- HiddenBench: facts that do not add up (ch. 6)
# Two interventions of the card are kept apart: the Exchange-Decide protocol (73–80%) gets its own beat with open
# slots on the table, and only the separate forced reveal of all facts in round one is drawn as six facts arriving.
HB = {
 "en": dict(title="Distributed facts: the hidden profile", agent="agent {k}", board="the group’s table", wrong="wrong answer", right="right answer",
            beats=["In this schematic, each agent holds shared facts A and B and one unique fact. The right answer needs all six.",
                   "In free discussion the agents repeat what they all know; the unique facts stay with their owners.",
                   "The group settles on the answer the shared facts suggest, and it is wrong.",
                   "“Exchange facts, then decide” raises accuracy to 73–80%.",
                   "Revealing every fact in round one is a separate condition. With all six on the table, accuracy reaches 92.6% for GPT-4.1 and 98.2% for Gemini 2.5 Flash."],
            bars=[("groups of 3–4 agents, facts spread", 30.1, None), ("“exchange facts, then decide” protocol", 73, 80), ("one agent with all the facts", 80.7, None),
                  ("all facts revealed in round one: GPT-4.1", 92.6, None), ("all facts revealed in round one: Gemini 2.5 Flash", 98.2, None)],
            bars_t="Correct answers, HiddenBench (65 tasks)", src="Numbers: HiddenBench card below (Li, Naito, Shirado, ICML 2026)."),
 "ru": dict(title="Распределённые факты: скрытый профиль", agent="агент {k}", board="стол группы", wrong="неверный ответ", right="верный ответ",
            beats=["В этой схеме у каждого агента общие факты A и B и один уникальный. Для верного ответа нужны все шесть.",
                   "В свободном обсуждении агенты повторяют то, что знают все; уникальные факты остаются у владельцев.",
                   "Группа выбирает ответ, на который указывают общие факты, — и ошибается.",
                   "Протокол «сначала обменяться фактами, потом решать» поднимает точность до 73–80%.",
                   "Раскрытие всех фактов в первом раунде — отдельное условие. Когда на столе все шесть, точность доходит до 92,6% у GPT-4.1 и 98,2% у Gemini 2.5 Flash."],
            bars=[("группы из 3–4 агентов, факты разложены", 30.1, None), ("протокол «обменяться фактами, потом решать»", 73, 80), ("один агент со всеми фактами", 80.7, None),
                  ("все факты раскрыты в первом раунде: GPT-4.1", 92.6, None), ("все факты раскрыты в первом раунде: Gemini 2.5 Flash", 98.2, None)],
            bars_t="Верные ответы, HiddenBench (65 задач)", src="Числа — из карточки HiddenBench ниже (Ли, Найто, Сирадо, ICML 2026)."),
}
HB_POS = {"w": dict(W=560, H=380, board=(280, 190, 200, 112), ags={1: (90, 70), 2: (470, 70), 3: (470, 310), 4: (90, 310)}),
          "n": dict(W=360, H=420, board=(180, 210, 196, 120), ags={1: (82, 58), 2: (278, 58), 3: (278, 362), 4: (82, 362)})}


def tile(x, y, lab, cls):
    return f'<g class="tl {cls}" transform="translate({n(x)} {n(y)})"><rect x="-15" y="-12" width="30" height="24" rx="6"/><text dy=".35em" text-anchor="middle">{lab}</text></g>'


def hidden_svg(lang, v):
    T = HB[lang]; P = HB_POS[v]
    bx, by, bw, bh = P["board"]
    o = [f'<svg class="mx hb-svg hb-{v}" viewBox="0 0 {P["W"]} {P["H"]}" role="img" aria-label="{esc(T["title"])}">',
         f'<g class="board"><rect x="{n(bx - bw / 2)}" y="{n(by - bh / 2)}" width="{bw}" height="{bh}" rx="18"/><text class="bl" x="{n(bx - bw / 2 + 14)}" y="{n(by - bh / 2 + 22)}">{esc(T["board"])}</text>']
    slots = [("A", "sh"), ("B", "sh"), ("c1", "un"), ("c2", "un"), ("c3", "un"), ("c4", "un")]
    for j, (lab, cls) in enumerate(slots):
        sx = bx - bw / 2 + 30 + (j % 3) * 36 + (0 if j < 3 else 0); sy = by - 4 + (j // 3) * 30
        o.append(f'<g class="slot s-{lab}">' + tile(sx + (j // 3) * 0, sy, lab.upper() if cls == "sh" else lab, cls) + "</g>")
    o.append(f'<g class="verdict v-ok" transform="translate({n(bx + bw / 2 - 30)} {n(by + 8)})"><circle r="16"/><path d="M-7 0l5 5 9-10"/></g>'
             f'<g class="verdict v-no" transform="translate({n(bx + bw / 2 - 30)} {n(by + 8)})"><circle r="16"/><path d="M-6 -6l12 12M6 -6l-12 12"/></g></g>')
    for k, (x, y) in P["ags"].items():
        up = y < by
        o.append(f'<g class="ag ag-{k}" transform="translate({x} {y})"><rect class="chip" x="-58" y="-20" width="116" height="40" rx="20"/>'
                 f'<circle class="st" cx="-38" r="5"/><text class="al" x="-26" dy=".35em">{esc(T["agent"].format(k=k))}</text>'
                 f'<g class="hand" transform="translate(0 {(-44 if up else 44)})">' + tile(-34, 0, "A", "sh") + tile(0, 0, "B", "sh") + tile(34, 0, f"c{k}", "un") + "</g></g>")
    o.append('<g class="fx"></g></svg>')
    return "".join(o)


def hidden(lang, ctx):
    T = HB[lang]
    bars = []
    for lab, a, b in T["bars"]:
        val = pct(a, lang, 1) if b is None else (f"{fnum(a, lang)}–{fnum(b, lang)}{NB}%" if lang == "ru" else f"{fnum(a, lang)}–{fnum(b, lang)}%")
        bars.append(f'<li style="--a:{a / 100:.3f};--b:{(b or a) / 100:.3f}"><span class="pb-l">{esc(lab)}</span><span class="pb-b"><i></i><i class="r"></i></span><b>{val}</b></li>')
    art = (f'<div class="hb-wrap"><div class="hb-art">{hidden_svg(lang, "w")}{hidden_svg(lang, "n")}</div>'
           f'<div class="hb-side"><p class="sc-sub">{esc(T["bars_t"])}</p><ol class="pb">{"".join(bars)}</ol><p class="sc-sub2">{esc(T["src"])}</p></div></div>')
    return frame("hidden", lang, "sc-hidden", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", note=esc(UI[lang]["sch_note"]))


# ---------------------------------------------------------------- Mind viruses: an idea passed along a chain (ch. 7)
MV = {
 "en": dict(title="An idea passed along a chain of agents", plain="no warning", warned="one warning paragraph in the system prompt", soul="SOUL.md",
            beats=["Agents meet in pairs along a chain and keep only their own files between sessions.",
                   "An infected agent persuades the next one and writes the idea into its self-editable SOUL.md.",
                   "Without a warning, the mean infection in the chain reached 70% (DeepSeek, Gemini 3 Flash).",
                   "One warning paragraph in the system prompt cut it to 1%, even against viruses evolved to get past it."],
            res_plain="mean infection 70%", res_warn="mean infection 1%", val=(70, 1),
            key=[("seed", "seed agent, starts infected"), ("inf", "infected"), ("ref", "resisted"), ("off", "not reached")],
            note="The chains are a schematic; each bar is the card’s measured mean on a 0–100% scale.",
            src="Numbers: Mind Viruses card above (Papadopoulos et al., 2026). 88% of transmission attempts came from agents that had written the virus into SOUL.md."),
 "ru": dict(title="Идея, переданная по цепочке агентов", plain="без предупреждения", warned="один абзац-предупреждение в системном промпте", soul="SOUL.md",
            beats=["Агенты встречаются парами вдоль цепочки и между сессиями хранят только свои файлы.",
                   "Заражённый агент убеждает следующего и записывает идею в свой редактируемый SOUL.md.",
                   "Без предупреждения среднее заражение в цепочке доходило до 70% (DeepSeek, Gemini 3 Flash).",
                   "Один абзац-предупреждение в системном промпте снизил его до 1%, даже против вирусов, выведенных для обхода."],
            res_plain="среднее заражение 70%", res_warn="среднее заражение 1%", val=(70, 1),
            key=[("seed", "источник, заражён с начала"), ("inf", "заражён"), ("ref", "устоял"), ("off", "не затронут")],
            note="Цепочки — схема; каждая полоса — измеренное среднее из карточки на шкале 0–100%.",
            src="Числа — из карточки Mind Viruses выше (Пападопулос и др., 2026). 88% попыток передачи шли от агентов, записавших вирус в SOUL.md."),
}
# The chains are a mechanism, not a count: the seed is marked as such and the measured mean sits in its own bar
# (a share of 100), so ten circles are never read as the 70% or the 1%.
MV_ROWS = [("plain", ["seed", "inf", "inf", "inf", "inf", "inf", "inf", "ref", "off", "off"]),
           ("warned", ["seed", "ref"] + ["off"] * 8)]


def virus_svg(lang, v):
    T = MV[lang]
    wide = v == "w"
    W, Hh, gap, x0, r = (900, 268, 64, 40, 14) if wide else (360, 262, 33, 18, 11)
    o = [f'<svg class="mx mv-svg mv-{v}" viewBox="0 0 {W} {Hh}" role="img" aria-label="{esc(T["title"])}: {esc(T["res_plain"])}; {esc(T["res_warn"])}">']
    for ri, (key, sts) in enumerate(MV_ROWS):
        y = (78 + ri * 120) if wide else (72 + ri * 130)
        lab, res, val = (T["plain"], T["res_plain"], T["val"][0]) if key == "plain" else (T["warned"], T["res_warn"], T["val"][1])
        o.append(f'<text class="rowl" x="{x0 - 8 if wide else 6}" y="{y - (40 if wide else 36)}">{esc(lab)}</text>')
        o.append(f'<path class="chain" d="M{x0} {y}H{x0 + gap * 9}"/>')
        for i, st in enumerate(sts):
            cls = {"seed": "inf seed", "inf": "inf", "ref": "ref", "off": ""}[st]
            core = '<circle class="core" r="4"/>' if st == "seed" else ""
            o.append(f'<g class="nd {cls}" data-i="{i}" data-r="{key}" transform="translate({n(x0 + gap * i)} {y})"><circle r="{r}"/>{core}'
                     f'<rect class="soul" x="{8 if wide else 6}" y="{-22 if wide else -19}" width="12" height="15" rx="2"/></g>')
        # the measured mean: a bar of 100
        bx, bw, by, bh = (676, 204, y - 5, 10) if wide else (x0, W - 18 - x0, y + 24, 8)
        tx, ty, anc = (bx + bw, y - 16, "end") if wide else (x0, y + 50, "start")
        o.append(f'<g class="mv-m" data-r="{key}"><rect class="mv-tr" x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="{bh / 2:g}"/>'
                 f'<rect class="mv-bar r-{key}" x="{bx}" y="{by}" width="{n(max(2, bw * val / 100))}" height="{bh}" rx="{bh / 2:g}"/>'
                 f'<text class="res r-{key}" x="{tx}" y="{ty}" text-anchor="{anc}">{esc(res)}</text></g>')
    o.append('<g class="fx"></g></svg>')
    return "".join(o)


def virus(lang, ctx):
    T = MV[lang]
    key = "".join(f'<li><i class="k-{k}"></i>{esc(lab)}</li>' for k, lab in T["key"])
    art = (f'<div class="mv-art">{virus_svg(lang, "w")}{virus_svg(lang, "n")}</div><ul class="sc-legend mv-key">{key}</ul>'
           f'<p class="sc-sub2">{esc(T["src"])}</p>')
    return frame("virus", lang, "sc-virus", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", note=esc(T["note"]))


# ---------------------------------------------------------------- DeepMind: one loophole, a shared proof store, 27 minutes (ch. 7)
LH = {
 "en": dict(title="One loophole in a shared proof store", problems="71 statements to prove in Lean", agents="100 Gemini 3.1 Pro agents", clock="min",
            honest="honest proofs", fakes="fakes", legend=[("ex", "cheated at once", 9), ("cv", "converted under competitive pressure", 5), ("wb", "whistleblowers", 24), ("un", "noticed nothing", 62)],
            beats=["A hundred identical agents prove 71 statements in Lean; accepted proofs go automatically into a shared proof store. Gaming the checker is explicitly forbidden.",
                   "In the first 57 minutes the swarm honestly proves 37 statements.",
                   "One agent finds that a statement’s symbols can be redefined until it is trivially true. The trick reaches the store.",
                   "Within 27 minutes the other 34 statements are closed with fakes. The 24 whistleblowers cannot stop it: complaints go unread in real time, with no way to reject a fake or sanction a cheater."],
            src="Numbers: DeepMind card above (Paglieri et al., 2026), one run; the order of honest proofs within the first 57 minutes is schematic."),
 "ru": dict(title="Одна лазейка в общем хранилище доказательств", problems="71 утверждение для доказательства в Lean", agents="100 агентов Gemini 3.1 Pro", clock="мин",
            honest="честные доказательства", fakes="подделки", legend=[("ex", "сжульничали сразу", 9), ("cv", "начали жульничать под давлением конкуренции", 5), ("wb", "разоблачители", 24), ("un", "ничего не заметили", 62)],
            beats=["Сто одинаковых агентов доказывают в Lean 71 утверждение; принятые решения автоматически попадают в общее хранилище доказательств. Обходить проверку прямо запрещено.",
                   "За первые 57 минут рой честно доказывает 37 утверждений.",
                   "Один агент находит, что символы утверждения можно переопределить, пока оно не станет тривиально верным. Приём попадает в хранилище.",
                   "За 27 минут остальные 34 утверждения закрыты подделками. 24 разоблачителя не могут это остановить: жалобы не читают в реальном времени, а отклонить подделку или наказать нарушителя нельзя."],
            src="Числа — из карточки DeepMind выше (Пальери и др., 2026), один прогон; порядок честных доказательств внутри первых 57 минут условный."),
}


def wrap2(s, width):
    """One line, or two balanced lines at a word boundary when the text is longer than `width` characters."""
    if len(s) <= width: return [s]
    ws = s.split()
    return min(([" ".join(ws[:i]), " ".join(ws[i:])] for i in range(1, len(ws))), key=lambda ab: max(len(ab[0]), len(ab[1])))


def loophole_svg(lang, v):
    T = LH[lang]
    wide = v == "w"
    W, Hh = (900, 360) if wide else (360, 640)
    o = [f'<svg class="mx lh-svg lh-{v}" viewBox="0 0 {W} {Hh}" role="img" aria-label="{esc(T["title"])}">']
    # problem board: 71 cells, 37 honest then 34 fakes
    pc = 9 if wide else 10; ps = 28 if wide else 30
    px0, py0 = (24, 52) if wide else (30, 52)
    o.append(f'<text class="rowl" x="{px0}" y="{py0 - 18}">{esc(T["problems"])}</text>')
    for i in range(71):
        x = px0 + (i % pc) * ps; y = py0 + (i // pc) * ps
        st = "ok" if i < 37 else "fake"
        o.append(f'<rect class="pc {st}" data-i="{i}" x="{x}" y="{y}" width="{ps - 6}" height="{ps - 6}" rx="5"/>')
    # agents: 10 x 10
    ax0, ay0 = (370, 52) if wide else (30, 352)
    as_ = 25 if wide else 30
    o.append(f'<text class="rowl" x="{ax0}" y="{ay0 - 18}">{esc(T["agents"])}</text>')
    groups = ["ex"] * 9 + ["cv"] * 5 + ["wb"] * 24 + ["un"] * 62
    rnd = random.Random(7); order = list(range(100)); rnd.shuffle(order)
    for slot, gi in enumerate(order):
        g = groups[gi]
        x = ax0 + (slot % 10) * as_ + 10; y = ay0 + (slot // 10) * as_ + 10
        first = " first" if gi == 0 else ""
        o.append(f'<circle class="ad {g}{first}" data-g="{g}" cx="{x}" cy="{y}" r="{8 if wide else 9}"/>')
    # legend and clock
    lx0, ly0 = (650, 60) if wide else (30, 600)
    if wide:     # the legend column is 250 px: long labels take two lines
        y = ly0
        for g, lab, cnt in T["legend"]:
            ls = wrap2(lab, 22)
            rest = "".join(f'<tspan x="26" dy="17">{esc(x)}</tspan>' for x in ls[1:])
            o.append(f'<g class="lg" transform="translate({lx0} {y})"><circle class="ad {g}" r="8" cx="8" cy="0"/><text x="26" dy=".35em"><tspan class="lgv">{cnt}</tspan> {esc(ls[0])}{rest}</text></g>')
            y += 34 + 17 * (len(ls) - 1)
        o.append(f'<g class="lg" transform="translate({lx0} {y + 14})"><rect class="pc ok" x="0" y="-9" width="18" height="18" rx="4"/><text x="26" dy=".35em"><tspan class="lgv">37</tspan> {esc(T["honest"])}</text></g>'
                 f'<g class="lg" transform="translate({lx0} {y + 48})"><rect class="pc fake" x="0" y="-9" width="18" height="18" rx="4"/><text x="26" dy=".35em"><tspan class="lgv">34</tspan> {esc(T["fakes"])}</text></g>')
    tx0, tx1, ty = (24, 876, 330) if wide else (30, 330, 330)
    if wide:
        def TX(mn): return tx0 + mn / 84 * (tx1 - tx0)
        o.append(f'<line class="tl-ax" x1="{tx0}" x2="{tx1}" y1="{ty}" y2="{ty}"/><rect class="tl-fill" x="{tx0}" y="{ty - 3}" width="{tx1 - tx0}" height="6" rx="3"/>')
        for mn in (0, 57, 84):
            o.append(f'<line class="tl-tk" x1="{n(TX(mn))}" x2="{n(TX(mn))}" y1="{ty - 8}" y2="{ty + 8}"/><text class="tk" x="{n(TX(mn))}" y="{ty + 24}" text-anchor="middle">{mn}{NB}{esc(T["clock"])}</text>')
        o.append(f'<rect class="tl-ph" x="{tx1}" y="{ty - 10}" width="2" height="20" rx="1"/>')   # the end state: 84 minutes, as the fill
    o.append("</svg>")
    if not wide:
        leg = "".join(f'<li><i class="ad {g}"></i><b>{cnt}</b> {esc(lab)}</li>' for g, lab, cnt in T["legend"])
        leg += f'<li><i class="pcl ok"></i><b>37</b> {esc(T["honest"])}</li><li><i class="pcl fake"></i><b>34</b> {esc(T["fakes"])}</li>'
        return "".join(o) + f'<ul class="lh-leg lh-leg-n">{leg}</ul>'
    return "".join(o)


def loophole(lang, ctx):
    T = LH[lang]
    art = f'<div class="lh-art">{loophole_svg(lang, "w")}<div class="lh-n">{loophole_svg(lang, "n")}</div></div><p class="sc-sub2">{esc(T["src"])}</p>'
    return frame("loophole", lang, "sc-loophole", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", note=esc(UI[lang]["sch_note"]))


# ---------------------------------------------------------------- Echo: thirty copies, about one vote (ch. 8)
EC = {
 "en": dict(title="Thirty copies, about one independent vote", meter="effective independent votes", start="30 copies of Qwen2.5-7B",
            beats=["Thirty copies of Qwen2.5-7B answer the same question on their own.",
                   "They debate, but thirty copies do not provide thirty independent votes.",
                   "Afterwards thirty agents stand behind about 1.12 independent votes (MMLU-Hard; 80% of items unanimous).",
                   "A mix of three model families keeps a little more: 1.34 at the same size."],
            notes=[("MMLU-Hard, 30 copies", "1.12"), ("GSM-Hard, 30 copies", "1.79"), ("three model families, 30 agents", "1.34")],
            src="Numbers: Ringelmann-effect card above (Bertalanič and Fortuna, preprint, May 2026); open 7–32B models."),
 "ru": dict(title="Тридцать копий — примерно один независимый голос", meter="эффективных независимых голосов", start="30 копий Qwen2.5-7B",
            beats=["Тридцать копий Qwen2.5-7B отвечают на один вопрос сами по себе.",
                   "Они обсуждают ответ, но тридцать копий не дают тридцати независимых голосов.",
                   "После спора за тридцатью агентами стоит около 1,12 независимого голоса (MMLU-Hard; 80% вопросов — единогласно).",
                   "Смесь трёх семейств моделей сохраняет чуть больше: 1,34 при том же размере."],
            notes=[("MMLU-Hard, 30 копий", "1,12"), ("GSM-Hard, 30 копий", "1,79"), ("три семейства моделей, 30 агентов", "1,34")],
            src="Числа — из карточки об эффекте Рингельмана выше (Берталанич и Фортуна, препринт, май 2026); открытые модели 7–32B."),
}


def echo_points(k=30, seed=5):
    rnd = random.Random(seed); pts = []
    for i in range(k):
        a = rnd.uniform(0, 2 * math.pi); r = 40 + rnd.random() ** .6 * 120
        pts.append((math.cos(a) * r, math.sin(a) * r * .78))
    return pts


def echo(lang, ctx):
    T = EC[lang]
    pts = echo_points()
    rnd = random.Random(11)
    end = [(rnd.gauss(0, 9), rnd.gauss(0, 7)) for _ in pts]
    o = [f'<svg class="mx ec-svg" viewBox="-260 -180 520 360" role="img" aria-label="{esc(T["title"])}">',
         '<circle class="ring" r="168"/><circle class="ring r2" r="110"/><circle class="ring r3" r="52"/>', '<g class="trails"></g>']
    for i, ((x, y), (ex, ey)) in enumerate(zip(pts, end)):
        o.append(f'<circle class="ed" data-x="{n(x)}" data-y="{n(y)}" data-ex="{n(ex)}" data-ey="{n(ey)}" cx="{n(ex)}" cy="{n(ey)}" r="6"/>')
    o.append('<circle class="core" r="26"/></svg>')
    notes = "".join(f'<li><span>{esc(a)}</span><b>{esc(b)}</b></li>' for a, b in T["notes"])
    end1, end2 = ("1,12", "1,34") if lang == "ru" else ("1.12", "1.34")
    art = (f'<div class="ec-wrap"><div class="ec-art">{"".join(o)}</div><div class="ec-side"><p class="ec-meter" data-start="30" data-start-label="{esc(T["start"])}" '
           f'data-end="{end1}" data-mix="{end2}" data-label="{esc(T["meter"])}"><b>{end1}</b>'
           f'<span>{esc(T["meter"])}</span></p><ul class="ec-notes">{notes}</ul><p class="sc-sub2">{esc(T["src"])}</p></div></div>')
    return frame("echo", lang, "sc-echo", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", note=esc(UI[lang]["sch_note"]))


# ---------------------------------------------------------------- Consensus: the threshold λρN/T ≈ 1 (ch. 9), a toy model
# The toy: 64 agents hold +1 (the answer a weak shared bias h favours) or −1. At each step one agent reads the mean
# answer of all the others, m, and picks +1 with probability 1/(1 + e^(−2(K·m + h))), where K stands for λρN/T.
# Everything printed is about this toy and is computed here, in scripts/check_scenes.py and in scenes.js alike:
#   the curves   stable states of the same model in an infinite group, the stable roots of m = tanh(K·m + h);
#   the grids    one finite run per K (a fixed seed, kept from the first version; its outcome is not chosen);
#   the bar      the exact chance of each end state of a group of 64 after CS_ROUNDS rounds from a random start
#                (the number of agents on +1 is a birth–death chain, so its distribution is computed, not sampled).
# The y axis is the share on the favoured answer, 0–100 %, so a run that locks against the bias shows as such.
CS_N, CS_H, CS_ROUNDS, CS_CUT, CS_SEED = 64, 0.06, 50, 58, 3      # CS_CUT: "near-unanimous" = at least 58 of 64 (≥ 90 %)
CS_K = (0.6, 1.0, 1.6)
CS = {
 "en": dict(title="When a weak lean becomes near-unanimity: a toy model of the threshold", k="λρN / T", snap=["below the threshold", "near it", "above it"], snap_n=["below it", "near it", "above it"],
            fav="favoured answer", oth="other answer",
            beats=["Sixty-four copies hold one of two answers, and a weak shared bias slightly favours one. Each step, an agent reads the others’ answers and picks one, with sampling noise.",
                   "While conformity times the number of interlocutors is below the noise (λρN/T < 1), the answers stay mixed.",
                   "Above the threshold, one answer can dominate. A weak shared bias favours one side, but does not determine every finite run.",
                   "In finite groups the switch is smoothed into a crossover; it sharpens as the group grows."],
            yl="share on the favoured answer", curve="theory, infinite group", lo="other answer", thr="threshold without bias",
            out_t="Groups of 64 after {r} rounds, {k} = {v}:", out=["≥90% on the favoured answer", "mixed", "≥90% on the other answer"],
            toy="Toy model, not the paper’s simulation and no model outputs: each step one agent reads all the others’ answers and picks one by a logit rule with a weak bias; a round is 64 steps. "
                "Curves: the same model in an infinite group. Dots: the three groups, live. The bar is computed exactly for this toy.",
            note="The threshold and the crossover are from Okawa’s card above (ICML 2026): experiments used groups of 3–11 agents and pre-2026 models. Here λ measures conformity, not division of labour."),
 "ru": dict(title="Когда слабый перекос становится почти единогласием: игрушечная модель порога", k="λρN / T", snap=["ниже порога", "около порога", "выше порога"], snap_n=["ниже порога", "около", "выше"],
            fav="предпочтительный ответ", oth="другой ответ",
            beats=["Шестьдесят четыре копии держат один из двух ответов, и слабый общий перекос чуть склоняет к одному из них. На каждом шаге агент читает ответы остальных и выбирает свой с шумом выборки.",
                   "Пока конформность, умноженная на число собеседников, меньше шума (λρN/T < 1), ответы остаются смешанными.",
                   "Выше порога один ответ может стать преобладающим. Слабый общий перекос склоняет выбор в одну сторону, но не определяет каждый конечный прогон.",
                   "В конечных группах переход сглажен в кроссовер и становится резче с ростом группы."],
            yl="доля за предпочтительный ответ", curve="теория, бесконечная группа", lo="другой ответ", thr="порог без перекоса",
            out_t="Группы из 64 через {r} раундов, {k} = {v}:", out=["≥90% за предпочтительный ответ", "смесь", "≥90% за другой ответ"],
            toy="Игрушечная модель, не симуляция статьи и не выходы моделей: на каждом шаге один агент читает ответы всех остальных и выбирает свой по логит-правилу со слабым перекосом; раунд — 64 шага. "
                "Кривые — та же модель в бесконечной группе. Точки — три группы по ходу прогона. Полоса посчитана для этой модели точно.",
            note="Порог и кроссовер — из карточки Окавы выше (ICML 2026): опыты шли на группах из 3–11 агентов и моделях до 2026 года. Здесь λ обозначает конформность, а не эффективность разделения труда."),
}


def cs_p(K, m, h=CS_H):
    """Probability of picking the favoured answer given the others' mean answer m."""
    return 1 / (1 + math.exp(-2 * (K * m + h)))


def cs_sim(K, seed=CS_SEED, n_ag=CS_N, rounds=CS_ROUNDS, h=CS_H):
    """One finite run from a random start; returns the answers (+1 favoured, −1 other)."""
    rnd = random.Random(seed)
    s = [rnd.choice((1, -1)) for _ in range(n_ag)]
    tot = sum(s)
    for _ in range(rounds * n_ag):
        i = rnd.randrange(n_ag)
        new = 1 if rnd.random() < cs_p(K, (tot - s[i]) / (n_ag - 1), h) else -1
        tot += new - s[i]; s[i] = new
    return s


def cs_states(K, h=CS_H, grid=4000):
    """Stable states m of the infinite group: roots of tanh(K·m + h) − m where the map's slope K·sech² is below 1."""
    f = lambda m: math.tanh(K * m + h) - m
    out = []
    for i in range(grid):
        a, b = -1 + 2 * i / grid, -1 + 2 * (i + 1) / grid
        if f(a) == 0 or f(a) * f(b) < 0:
            for _ in range(80):
                c = (a + b) / 2
                if f(a) * f(c) <= 0: b = c
                else: a = c
            m = (a + b) / 2
            if K * (1 - math.tanh(K * m + h) ** 2) < 1: out.append(m)
    return out


def cs_branches(h=CS_H, k0=0.2, k1=2.0, steps=180):
    """The two stable branches as [(K, share)]: upper for every K, lower where it exists (from about K = 1.21)."""
    up, lo = [], []
    for i in range(steps + 1):
        K = k0 + (k1 - k0) * i / steps
        st = cs_states(K, h)
        up.append((K, (1 + max(st)) / 2))
        if len(st) > 1: lo.append((K, (1 + min(st)) / 2))
    return up, lo


def cs_outcomes(K, n_ag=CS_N, rounds=CS_ROUNDS, cut=CS_CUT, h=CS_H):
    """Exact chances (near-unanimous favoured, mixed, near-unanimous other) for a group of n_ag after `rounds` rounds
    from a random start. The count k of agents on +1 moves by at most one per step: up with probability
    (n−k)/n · p(others' mean seen by a −1 agent), down with probability k/n · (1 − p(mean seen by a +1 agent))."""
    N = n_ag
    v = [math.comb(N, k) / 2 ** N for k in range(N + 1)]
    up = [(N - k) / N * cs_p(K, (2 * k - N + 1) / (N - 1), h) for k in range(N + 1)]
    dn = [k / N * (1 - cs_p(K, (2 * k - N - 1) / (N - 1), h)) for k in range(N + 1)]
    for _ in range(rounds * N):
        v = [v[k] * (1 - up[k] - dn[k]) + (v[k - 1] * up[k - 1] if k else 0) + (v[k + 1] * dn[k + 1] if k < N else 0) for k in range(N + 1)]
    a, b = sum(v[cut:]), sum(v[:N - cut + 1])
    return a, 1 - a - b, b


def pct_round(ps):
    """Whole percentages that add up to 100 (largest remainder; ties go to the earlier item)."""
    raw = [p * 100 for p in ps]; fl = [math.floor(x) for x in raw]
    for i in sorted(range(len(ps)), key=lambda i: (-(raw[i] - fl[i]), i))[:100 - sum(fl)]: fl[i] += 1
    return fl


def cs_grid(s, ox, oy, sz=13):
    return "".join(f'<rect class="op {"a" if v > 0 else "b"}" x="{ox + (i % 8) * sz}" y="{oy + (i // 8) * sz}" width="{sz - 3}" height="{sz - 3}" rx="3"/>' for i, v in enumerate(s))


CS_GEO = {"w": dict(W=900, H=322, sz=13, gx=[24, 174, 324], gy=60, ly=40, vy=188, x0=560, x1=870, y0=270, y1=48, fs="sl"),
          "n": dict(W=360, H=490, sz=11, gx=[8, 132, 256], gy=52, ly=34, vy=160, x0=46, x1=340, y0=440, y1=240, fs="sl sl-n")}
CS_RUNS = {K: cs_sim(K) for K in CS_K}
CS_UP, CS_LO = cs_branches()


def cs_svg(lang, v):
    T = CS[lang]; G = CS_GEO[v]
    labs = T["snap"] if v == "w" else T["snap_n"]
    x0, x1, y0, y1 = G["x0"], G["x1"], G["y0"], G["y1"]
    def X(K): return x0 + (K - 0.2) / 1.8 * (x1 - x0)
    def Y(s): return y0 - s * (y0 - y1)
    o = [f'<svg class="mx cs-svg cs-{v}" viewBox="0 0 {G["W"]} {G["H"]}" role="img" aria-label="{esc(T["title"])}" '
         f'data-x0="{x0}" data-x1="{x1}" data-y0="{y0}" data-y1="{y1}" data-l="{esc("|".join(labs))}">']
    for j, K in enumerate(CS_K):
        st = CS_RUNS[K]; ox = G["gx"][j]
        o.append(f'<g class="snap" data-k="{K}"><g class="g8">{cs_grid(st, ox, G["gy"], G["sz"])}</g><text class="{G["fs"]}" x="{ox}" y="{G["ly"]}">{esc(labs[j])}</text>'
                 f'<text class="sv" x="{ox}" y="{G["vy"]}">{esc(T["k"])} = {fnum(K, lang, 1)}</text>'
                 f'<rect class="op a" x="{ox}" y="{G["vy"] + 9}" width="10" height="10" rx="3"/><text class="sv2" x="{ox + 16}" y="{G["vy"] + 19}">{pct(st.count(1) / len(st) * 100, lang, 0)}</text></g>')
    path = lambda pts: "M" + " L".join(f"{n(X(K))} {n(Y(s))}" for K, s in pts)
    cl = [T["curve"]] if v == "w" else T["curve"].split(" ", 1)
    curve_lab = esc(cl[0]) + "".join(f'<tspan x="{x1}" dy="15">{esc(x)}</tspan>' for x in cl[1:])
    lo_at = lambda K: min(CS_LO, key=lambda p: abs(p[0] - K))[1]
    o.append(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}"/><line class="grid" x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}"/>'
             f'<line class="grid mid" x1="{x0}" x2="{x1}" y1="{n(Y(.5))}" y2="{n(Y(.5))}"/>'
             f'<line class="thr" x1="{n(X(1))}" x2="{n(X(1))}" y1="{y1 - 10}" y2="{y0}"/><text class="cl thl" x="{n(X(1) - 6)}" y="{y1 + (16 if v == "w" else 20)}" text-anchor="end">{esc(T["thr"])}</text>'
             f'<text class="tk" x="{n(X(1))}" y="{y0 + 20}" text-anchor="middle">1</text>'
             f'<text class="tk" x="{x0}" y="{y0 + 20}" text-anchor="middle">{fnum(0.2, lang, 1)}</text><text class="tk" x="{x1}" y="{y0 + 20}" text-anchor="middle">2</text>'
             f'<text class="axl" x="{x1}" y="{y0 + 40}" text-anchor="end">{esc(T["k"])}</text>'
             + "".join(f'<text class="tky" x="{x0 - 8}" y="{n(Y(s))}" dy=".35em">{pct(s * 100, lang, 0)}</text>' for s in (0, .5, 1)) +
             f'<path class="crv" d="{path(CS_UP)}"/><path class="crv lo" d="{path(CS_LO)}"/>'
             f'<text class="cl" x="{x1}" y="{n(Y(.7 if v == "w" else .68))}" text-anchor="end">{curve_lab}</text>'
             f'<text class="cl" x="{n(X(1.45))}" y="{n(Y(lo_at(1.45)) - 12)}">{esc(T["lo"])}</text>'
             f'<text class="yl" x="{x0}" y="{y1 - 18}">{esc(T["yl"])}</text>')
    for j, K in enumerate(CS_K):
        st = CS_RUNS[K]
        o.append(f'<circle class="mk live" data-j="{j}" cx="{n(X(K))}" cy="{n(Y(st.count(1) / len(st)))}" r="6"/>')
    o.append("</svg>")
    return "".join(o)


def cs_out(lang, K=CS_K[-1]):
    T = CS[lang]
    ps = cs_outcomes(K); pc = pct_round(ps)
    seg = "".join(f'<i class="o-{c}" style="--w:{p:.4f}"></i>' for c, p in zip("amb", ps))
    lis = "".join(f'<li><i class="o-{c}"></i><span>{esc(lab)}</span> <b>{v}{NB if lang == "ru" else ""}%</b></li>' for c, lab, v in zip("amb", T["out"], pc))
    return (f'<div class="cs-out" data-n="{CS_N}" data-h="{CS_H}" data-r="{CS_ROUNDS}" data-cut="{CS_CUT}" data-tpl="{esc(T["out_t"].format(r=CS_ROUNDS, k=T["k"], v="{v}"))}">'
            f'<p class="cs-out-t">{esc(T["out_t"].format(r=CS_ROUNDS, k=T["k"], v=fnum(K, lang, 1)))}</p>'
            f'<div class="cs-bar" aria-hidden="true">{seg}</div><ul class="cs-out-l" aria-live="polite">{lis}</ul></div>')


def consensus(lang, ctx):
    T = CS[lang]
    controls = (f'<div class="sc-ctl js-only"><label class="ctl-g"><span class="ctl-l">{esc(T["k"])}</span>'
                f'<input type="range" class="cs-k" min="0.2" max="2" step="0.05" value="{CS_K[-1]}" aria-label="{esc(T["k"])}"><output class="cs-o">{fnum(CS_K[-1], lang, 1)}</output></label></div>')
    leg = f'<ul class="sc-legend cs-leg"><li><i class="o-a"></i>{esc(T["fav"])}</li><li><i class="o-b"></i>{esc(T["oth"])}</li></ul>'
    art = f'{leg}<div class="cs-wrap">{cs_svg(lang, "w")}{cs_svg(lang, "n")}</div>{cs_out(lang)}<p class="sc-sub2">{esc(T["toy"])}</p>'
    return frame("consensus", lang, "sc-consensus", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="sch", controls=controls, note=esc(T["note"]))


# ---------------------------------------------------------------- Moltbook: 1.5 million registrations, about 17 thousand owners (ch. 10)
# Two units, two glyphs, two keys: a small square is 1,000 registrations, a dot is 1,000 owners. 1,500 squares over
# 17 dots is ≈88 squares a dot, i.e. ≈88 registrations per owner. The canvas plays over the SVG and draws only the
# glyphs, so the labels and keys stay on screen while it moves.
MB = {
 "en": dict(title="1.5 million registrations, about 17 thousand owners", a="1.5 million registrations", b="≈17,000 human owners", ratio="≈88", ratio2="registrations per owner",
            key_a="= 1,000 registrations", key_b="= 1,000 owners",
            beats=["Moltbook’s database held 1.5 million registrations. Each square here represents a thousand registrations.",
                   "They belonged to about 17,000 human owners: roughly 88 registrations per person.",
                   "And the site did not check whether a model or a script was doing the posting."],
            src="Numbers: Wiz card above (Nagli, Wiz blog, 2026)."),
 "ru": dict(title="1,5 миллиона регистраций, около 17 тысяч владельцев", a="1,5 млн регистраций", b="≈17 000 владельцев-людей", ratio="≈88", ratio2="регистраций на владельца",
            key_a="= 1 000 регистраций", key_b="= 1 000 владельцев",
            beats=["В базе Moltbook было 1,5 миллиона регистраций. Каждый квадрат здесь — тысяча регистраций.",
                   "Они принадлежали примерно 17 тысячам владельцев: около 88 регистраций на человека.",
                   "А сайт не проверял, пишет ли модель или скрипт."],
            src="Числа — из карточки Wiz выше (Нагли, блог Wiz, 2026)."),
}
MB_REG, MB_OWN, MB_UNIT = 1500, 17, 1000      # glyphs; each stands for MB_UNIT registrations or owners


MB_GEO = {"w": dict(W=640, H=262, cols=50, cell=7, gx=0, gy=28, ox=446, oy=28, ocols=6, ostep=28, orad=7, ax="M372 120h44m-10-8l10 8-10 8",
                    la=(0, 14), lb=(446, 14), ka=(0, 254), kb=(446, 126), r1=(446, 174), r2=(446, 196)),
          "n": dict(W=360, H=508, cols=40, cell=7, gx=40, gy=28, ox=40, oy=384, ocols=9, ostep=28, orad=7, ax="M180 324v24m-8-10l8 10 8-10",
                    la=(40, 14), lb=(40, 372), ka=(40, 314), kb=(40, 446), r1=(40, 482), r2=(40, 502))}


def mb_owner_xy(G, j):
    return G["ox"] + G["orad"] + (j % G["ocols"]) * G["ostep"], G["oy"] + G["orad"] + (j // G["ocols"]) * G["ostep"]


def moltbook_svg(lang, v):
    T = MB[lang]; G = MB_GEO[v]
    c, cs = G["cols"], G["cell"]
    d = "".join(f"M{G['gx'] + (i % c) * cs} {(i // c) * cs}h5v5h-5z" for i in range(MB_REG))
    own = "".join(f'<circle cx="{x}" cy="{y}" r="{G["orad"]}"/>' for x, y in (mb_owner_xy(G, j) for j in range(MB_OWN)))
    attrs = " ".join(f'data-{k.lower()}="{G[k]}"' for k in ("W", "H", "cols", "cell", "gx", "gy", "ox", "oy", "ocols", "ostep", "orad"))
    (kax, kay), (kbx, kby) = G["ka"], G["kb"]
    return (f'<svg class="mx mb-svg mb-{v}" viewBox="0 0 {G["W"]} {G["H"]}" role="img" aria-label="{esc(T["a"])}; {esc(T["b"])}; {esc(T["ratio"])} {esc(T["ratio2"])}" {attrs}>'
            f'<text class="rowl" x="{G["la"][0]}" y="{G["la"][1]}">{esc(T["a"])}</text><path class="mb-a" transform="translate(0 {G["gy"]})" d="{d}"/>'
            f'<rect class="kg-a" x="{kax}" y="{kay - 8}" width="5" height="5"/><text class="mbk" x="{kax + 11}" y="{kay - 3}">{esc(T["key_a"])}</text>'
            f'<path class="arrow" d="{G["ax"]}"/>'
            f'<text class="rowl" x="{G["lb"][0]}" y="{G["lb"][1]}">{esc(T["b"])}</text><g class="mb-b">{own}</g>'
            f'<circle class="kg-b" cx="{kbx + 3.5}" cy="{kby - 5.5}" r="3.5"/><text class="mbk" x="{kbx + 11}" y="{kby - 3}">{esc(T["key_b"])}</text>'
            f'<text class="mbr" x="{G["r1"][0]}" y="{G["r1"][1]}">{esc(T["ratio"])}</text><text class="mbr2" x="{G["r2"][0]}" y="{G["r2"][1]}">{esc(T["ratio2"])}</text></svg>')


def moltbook(lang, ctx):
    T = MB[lang]
    art = f'<div class="mb-art">{moltbook_svg(lang, "w")}{moltbook_svg(lang, "n")}<canvas class="mb-cv" aria-hidden="true"></canvas></div><p class="sc-sub2">{esc(T["src"])}</p>'
    return frame("moltbook", lang, "sc-moltbook", art, title=esc(T["title"]), beats=[esc(b) for b in T["beats"]], badge="card")


MECH = {"lambda": lam, "agensh": agensh, "hidden": hidden, "virus": virus, "loophole": loophole, "echo": echo, "consensus": consensus, "moltbook": moltbook}
TABLES = {"ledger": ledger}

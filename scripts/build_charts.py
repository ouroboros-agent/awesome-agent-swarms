#!/usr/bin/env python3
"""The survey's own corpus charts («Поле сверху» / "The field from above"), RU+EN × dark+light.

  python scripts/build_charts.py        -> assets/charts/dash_<name>_<lang>_<theme>.png

Port of the October build/charts.py: same data (the analytic corpus in data/works.json, field `corpus`),
same chart forms. Changes: English labels, a light theme, and a categorical palette that passes the
colour-vision checks (the October dark palette did not separate violet/blue for deutan viewers).
The October RU dark files (dash_*_dark.png) are kept unchanged next to these.
"""
import collections, json, os, random, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "charts")
REG = json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))
META = []
for w in REG["works"]:
    if w.get("in_analytic_corpus") and w.get("corpus"):
        m = dict(w["corpus"]); m["id"] = w["id"]; m["orgs"] = w.get("orgs") or []; META.append(m)
assert len(META) == 153, len(META)
for f in ("Inter-Regular.otf", "Inter-Medium.otf", "Inter-SemiBold.otf", "Inter-Bold.otf"):
    p = os.path.expanduser("~/Library/Fonts/" + f)
    if os.path.exists(p): fm.fontManager.addfont(p)
FONT = "Inter" if any("Inter" in f.name for f in fm.fontManager.ttflist) else "DejaVu Sans"

THEMES = {
    "dark": dict(BG="#141017", BG2="#1a1520", LINE="#2a2530", INK="#e2e8f0", SOFT="#b4b8c0", FAINT="#8a8a93", ACC="#c93545", ACCL="#f07a86",
                 SLOTS=["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]),
    "light": dict(BG="#ffffff", BG2="#f6f3f0", LINE="#e3ddd8", INK="#1f1b24", SOFT="#3d3842", FAINT="#6b6570", ACC="#b52a3a", ACCL="#b52a3a",
                  SLOTS=["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]),
}
L = {  # labels: ru, en
 "evid": {"live_experiment": ("Эксперимент с живыми LLM-агентами", "Experiment with live LLM agents"), "field_observation": ("Наблюдение в дикой природе", "Field observation"),
          "incident": ("Реальный инцидент", "Real incident"), "engineering_report": ("Инженерный отчёт лаборатории", "Lab engineering report"),
          "system_card_eval": ("Системная карта модели", "Model system card"), "surrogate_simulation": ("Модель-суррогат / ABM", "Surrogate model / ABM"),
          "theory_essay": ("Теория / эссе", "Theory / essay"), "benchmark": ("Бенчмарк / датасет", "Benchmark / dataset")},
 "evid_short": {"live_experiment": ("Эксперимент\nс LLM-агентами", "Experiment\nwith LLM agents"), "field_observation": ("Наблюдение\nв дикой природе", "Field\nobservation"),
          "incident": ("Реальный\nинцидент", "Real\nincident"), "engineering_report": ("Инженерный\nотчёт", "Engineering\nreport"),
          "system_card_eval": ("Системная\nкарта", "System\ncard"), "surrogate_simulation": ("Суррогат\n/ ABM", "Surrogate\n/ ABM"),
          "theory_essay": ("Теория\n/ эссе", "Theory\n/ essay"), "benchmark": ("Бенчмарк\n/ датасет", "Benchmark\n/ dataset")},
 "type": {"peer_reviewed": ("Рецензированная статья", "Peer-reviewed paper"), "preprint": ("Препринт", "Preprint"), "system_card": ("Системная карта", "System card"),
          "lab_report": ("Блог / отчёт лаборатории", "Lab blog / report"), "incident_report": ("Расследование инцидента", "Incident investigation"),
          "essay_blog": ("Эссе, блог, интервью", "Essay, blog, interview"), "dataset_platform": ("Датасет / платформа", "Dataset / platform")},
 "org": {"frontier_lab": ("Фронтир-лаборатории", "Frontier labs"), "industry": ("Другие компании", "Other companies"), "mixed": ("Совместно: вузы + индустрия", "Academia + industry"),
         "academia": ("Университеты", "Universities"), "independent": ("Независимые и некоммерческие", "Independent & non-profit")},
 "topic": {"scaling_economics": ("Экономика и масштаб", "Economics & scale"), "self_organization": ("Самоорганизация", "Self-organization"), "memory": ("Память", "Memory"),
           "safety_alignment": ("Безопасность", "Safety"), "contagion_security": ("Заражение и атаки", "Contagion & attacks"), "echo_diversity": ("Эхо и разнообразие", "Echo & diversity"),
           "social_dynamics": ("Убеждения и согласие", "Beliefs & consensus"), "wild_field": ("Дикая природа", "In the wild"), "infrastructure": ("Платформы и симуляторы", "Platforms & simulators"),
           "training_rl": ("Обучение (RL)", "Training (RL)"), "theory": ("Теория", "Theory")},
 "fam": {"other open": ("Другие открытые", "Other open"), "other closed": ("Другие закрытые", "Other closed")},
}
EVID_ORDER = ["live_experiment", "engineering_report", "benchmark", "field_observation", "incident", "system_card_eval", "theory_essay", "surrogate_simulation"]
TYPE_ORDER = ["preprint", "peer_reviewed", "lab_report", "essay_blog", "incident_report", "system_card", "dataset_platform"]
ORG_ORDER = ["academia", "mixed", "frontier_lab", "independent", "industry"]
LABELS = {"openai-navier-stokes": ("OpenAI, задача Навье–Стокса", "OpenAI, Navier–Stokes problem"), "anthropic-institute-pace": ("Anthropic, внутренние агенты", "Anthropic, internal agents"),
    "zhang-agents-in-the-wild": ("Moltbook: 27 269 аккаунтов за 9 дней", "Moltbook: 27,269 accounts in 9 days"), "cursor-scaling": ("Cursor, сборка браузера", "Cursor, browser build"),
    "agensh-1024": ("Agensh (Microsoft Research)", "Agensh (Microsoft Research)"), "hf-incident-case": ("Инцидент OpenAI → Hugging Face, за 6 дней", "OpenAI → Hugging Face incident, 6 days"),
    "wiz-moltbook": ("Moltbook: 1,49 млн регистраций", "Moltbook: 1.49 M registrations"), "flag-game": ("Flag Game", "Flag Game"),
    "opus55-card": ("Claude Opus 5.5, системная карта", "Claude Opus 5.5, system card"), "deepmind-cheating-whistleblowing": ("DeepMind: 100 агентов Gemini", "DeepMind: 100 Gemini agents"),
    "prev-swarmworld": ("SwarmWorld", "SwarmWorld"), "anthropic-c-compiler": ("Компилятор C из 16 Claude", "C compiler by 16 Claudes"),
    "mind-viruses": ("Mind Viruses", "Mind Viruses"), "opus5-card-multiagent": ("Claude Opus 5", "Claude Opus 5"),
    "indirect-tipping": ("Суррогатные популяции", "Surrogate populations"), "silo-bench": ("Silo-Bench", "Silo-Bench")}
LABEL_POS = {"anthropic-c-compiler": (8, -17, "left"), "cursor-scaling": (8, -17, "left"), "openai-navier-stokes": (-8, 15, "right"),
    "anthropic-institute-pace": (8, 13, "left"), "zhang-agents-in-the-wild": (8, -17, "left"), "hf-incident-case": (8, -17, "left"),
    "wiz-moltbook": (-10, 12, "right"), "opus5-card-multiagent": (-8, -17, "right"), "opus55-card": (8, 12, "left"),
    "mind-viruses": (-6, -30, "right"), "deepmind-cheating-whistleblowing": (-40, 30, "right"), "flag-game": (6, -26, "left"),
    "prev-swarmworld": (14, 30, "left"), "agensh-1024": (8, -17, "left"), "indirect-tipping": (-8, 12, "right"), "silo-bench": (8, 10, "left")}
CITES_OTHER = {"noam-brown-dwarkesh", "bradshaw-swarm-exponent", "mollick-dot-and-swarm", "vidal-models-identify-as-swarm", "cotra-surprised", "metr-senate-testimony"}

def setup(T):
    plt.rcParams.update({"font.family": FONT, "font.size": 10, "text.color": T["INK"], "axes.labelcolor": T["SOFT"], "xtick.color": T["FAINT"],
        "ytick.color": T["SOFT"], "axes.edgecolor": T["LINE"], "figure.facecolor": T["BG"], "axes.facecolor": T["BG"], "savefig.facecolor": T["BG"],
        "axes.spines.top": False, "axes.spines.right": False})

def save(fig, name, lang, th):
    fn = f"dash_{name}_{lang}_{th}.png"
    fig.savefig(os.path.join(OUT, fn), dpi=200, bbox_inches="tight", pad_inches=0.18); plt.close(fig); return fn

def ecol(T, e): return T["SLOTS"][EVID_ORDER.index(e) % 8]

def fmt(n, lang): return f"{n:,}".replace(",", " ") if lang == "ru" else f"{n:,}"

# Legend of the scale map; scripts/build_paper_scale_chart.py substitutes wording for the paper's variant.
SCALE_LEGEND = [["одновременно в одном прогоне или системе", "simultaneous, in one run or system"], ["накопленным итогом за всё время", "accumulated over the whole period"],
                ["заявленная ёмкость платформы", "stated platform capacity"]]

def scale_map(T, lang, th):
    i = 0 if lang == "ru" else 1
    rows = ["incident", "engineering_report", "field_observation", "system_card_eval", "live_experiment", "benchmark", "surrogate_simulation"]
    pts = []
    for m in META:
        if m.get("evidence") not in rows or m["id"] in CITES_OTHER: continue
        k = m.get("scale_kind") or "simultaneous"; x = m.get("agents_max_simultaneous"); tot = m.get("agents_total")
        if k == "simultaneous" and isinstance(x, (int, float)) and x >= 1: pts.append((m, k, x))
        elif k == "capacity" and isinstance(x or tot, (int, float)): pts.append((m, k, x or tot))
        elif k == "cumulative_only" and isinstance(tot, (int, float)) and tot >= 1: pts.append((m, k, tot))
    order = {e: n for n, e in enumerate(rows)}
    fig, ax = plt.subplots(figsize=(10.5, 6.9)); rng = random.Random(11)
    for m, k, x in pts:
        e = m["evidence"]; y = order[e] + rng.uniform(-0.22, 0.22); col = ecol(T, e); lab = m["id"] in LABELS
        if k == "capacity": ax.scatter([x], [y], s=70, marker="D", facecolor="none", edgecolor=col, linewidth=1.4, zorder=3)
        elif k == "cumulative_only": ax.scatter([x], [y], s=54, facecolor="none", edgecolor=col, linewidth=1.4, zorder=3)
        else:
            ax.scatter([x], [y], s=58 if lab else 40, color=col, alpha=0.95 if lab else 0.7, edgecolor=T["BG"], linewidth=1.0, zorder=3)
            tot = m.get("agents_total")
            if isinstance(tot, (int, float)) and tot > x * 1.5:
                ax.plot([x, tot], [y, y], color=col, alpha=0.45, lw=1.2, zorder=2)
                ax.scatter([tot], [y], s=48, facecolor="none", edgecolor=col, linewidth=1.3, zorder=3)
        if lab:
            dx, dy, ha = LABEL_POS.get(m["id"], (7, 6, "left"))
            ax.annotate(LABELS[m["id"]][i], (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=7.6, color=T["INK"], ha=ha, va="center",
                        arrowprops=dict(arrowstyle="-", color=T["FAINT"], lw=0.6, shrinkA=0, shrinkB=3))
    ax.set_xscale("log"); ax.set_xlim(0.8, 6e6)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([L["evid"][e][i] for e in rows], fontsize=8.8); ax.set_ylim(len(rows) - 0.45, -0.55)
    ticks = [1, 10, 100, 1000, 10_000, 100_000, 1_000_000]
    names = {"ru": ["1", "10", "100", "1 тыс.", "10 тыс.", "100 тыс.", "1 млн"], "en": ["1", "10", "100", "1K", "10K", "100K", "1M"]}[lang]
    ax.set_xticks(ticks); ax.set_xticklabels(names); ax.minorticks_off()
    ax.grid(axis="x", color=T["LINE"], lw=0.6); ax.tick_params(axis="y", length=0); ax.set_axisbelow(True)
    ax.set_xlabel(["Число агентов, логарифмическая шкала", "Number of agents, log scale"][i], fontsize=9)
    leg = SCALE_LEGEND
    h = [Line2D([], [], marker="o", ls="", color=T["SOFT"], label=leg[0][i], markersize=6),
         Line2D([], [], marker="o", ls="", markerfacecolor="none", markeredgecolor=T["SOFT"], label=leg[1][i], markersize=6),
         Line2D([], [], marker="D", ls="", markerfacecolor="none", markeredgecolor=T["SOFT"], label=leg[2][i], markersize=6)]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, frameon=False, fontsize=8.2, labelcolor=T["SOFT"])
    return save(fig, "scale", lang, th)

def timeline(T, lang, th):
    i = 0 if lang == "ru" else 1
    months = []; y, mo = 2025, 1
    while (y, mo) <= (2026, 10):
        months.append(f"{y}-{mo:02d}"); mo += 1
        if mo == 13: y, mo = y + 1, 1
    types = [t for t in TYPE_ORDER if any(m.get("source_type") == t for m in META)]
    cnt = {t: collections.Counter(m["month"] for m in META if m.get("source_type") == t) for t in types}
    fig, ax = plt.subplots(figsize=(10.5, 3.9)); bottom = [0] * len(months)
    for n, t in enumerate(types):
        vals = [cnt[t].get(mm, 0) for mm in months]
        ax.bar(range(len(months)), vals, bottom=bottom, color=T["SLOTS"][n], width=0.74, label=L["type"][t][i], edgecolor=T["BG"], linewidth=1.0)
        bottom = [a + b for a, b in zip(bottom, vals)]
    early = sum(1 for m in META if m.get("month", "9") < "2025-01")
    mn = {"ru": ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"], "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}[lang]
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([mn[int(mm[5:]) - 1] + ("\n" + mm[:4] if mm.endswith("-01") else "") for mm in months], fontsize=7.6)
    ax.set_ylabel(["Работ в месяц", "Works per month"][i], fontsize=9); ax.grid(axis="y", color=T["LINE"], lw=0.6); ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=8.2, labelcolor=T["SOFT"], ncol=2)
    if early: ax.text(0.0, -0.2, [f"Ещё {early} — раньше 2025 года.", f"{early} more before 2025."][i], transform=ax.transAxes, ha="left", va="top", fontsize=7.6, color=T["FAINT"])
    return save(fig, "timeline", lang, th)

def orgs(T, lang, th):
    i = 0 if lang == "ru" else 1
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.8), gridspec_kw={"width_ratios": [1, 1.25]})
    c = collections.Counter(m.get("org_class") for m in META)
    keys = [k for k in ORG_ORDER if c.get(k)]
    a1.barh(range(len(keys)), [c[k] for k in keys], color=[T["SLOTS"][n] for n in range(len(keys))], height=0.62)
    a1.set_yticks(range(len(keys))); a1.set_yticklabels([L["org"][k][i] for k in keys], fontsize=8.6); a1.invert_yaxis()
    for n, k in enumerate(keys): a1.text(c[k] + 0.6, n, str(c[k]), va="center", fontsize=8.5, color=T["INK"])
    a1.set_title(["Кто публикует: классы организаций", "Who publishes: organization classes"][i], fontsize=10, color=T["INK"], loc="left"); a1.tick_params(axis="y", length=0); a1.set_xticks([])
    oc = collections.Counter()
    for m in META:
        for o in set(m.get("orgs") or []): oc[o] += 1
    top = oc.most_common(14)
    a2.barh(range(len(top)), [v for _, v in top], color=T["ACC"], height=0.62, alpha=0.9)
    a2.set_yticks(range(len(top))); a2.set_yticklabels([k for k, _ in top], fontsize=8.2); a2.invert_yaxis()
    for n, (_, v) in enumerate(top): a2.text(v + 0.2, n, str(v), va="center", fontsize=8.2, color=T["INK"])
    a2.set_title(["Самые частые организации в корпусе", "Most frequent organizations in the corpus"][i], fontsize=10, color=T["INK"], loc="left"); a2.tick_params(axis="y", length=0); a2.set_xticks([])
    for a in (a1, a2): a.spines["bottom"].set_visible(False); a.spines["left"].set_visible(False)
    fig.tight_layout(w_pad=3)
    return save(fig, "orgs", lang, th)

def models(T, lang, th):
    i = 0 if lang == "ru" else 1
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.9), gridspec_kw={"width_ratios": [1.35, 1]})
    fc = collections.Counter(f for m in META for f in set(m.get("model_families") or []))
    fams = [f for f, _ in fc.most_common()]
    a1.barh(range(len(fams)), [fc[f] for f in fams], color=T["SLOTS"][0], height=0.64)   # one series: the axis names the families
    a1.set_yticks(range(len(fams))); a1.set_yticklabels([L["fam"].get(f, (f, f))[i] for f in fams], fontsize=8.4); a1.invert_yaxis()
    for n, f in enumerate(fams): a1.text(fc[f] + 0.5, n, str(fc[f]), va="center", fontsize=8.2, color=T["INK"])
    a1.set_title(["Чьи модели работают в роях (работ на семейство)", "Whose models run in swarms (works per family)"][i], fontsize=10, color=T["INK"], loc="left")
    a1.set_xticks([]); a1.tick_params(axis="y", length=0)
    bins = [(["1 модель", "1 model"][i], lambda n: n == 1), ("2–3", lambda n: 2 <= n <= 3), ("4–9", lambda n: 4 <= n <= 9), (["10 и больше", "10 or more"][i], lambda n: n >= 10)]
    ns = [m.get("n_models") for m in META if isinstance(m.get("n_models"), int) and m["n_models"] > 0]
    vals = [sum(1 for n in ns if f(n)) for _, f in bins]
    a2.bar(range(len(bins)), vals, color=T["ACC"], width=0.62)
    for n, v in enumerate(vals): a2.text(n, v + 0.6, str(v), ha="center", fontsize=8.6, color=T["INK"])
    a2.set_xticks(range(len(bins))); a2.set_xticklabels([b for b, _ in bins], fontsize=8.4); a2.set_yticks([])
    mixed = sum(1 for m in META if m.get("mixed_swarm") is True); mono = sum(1 for m in META if m.get("mixed_swarm") is False)
    a2.set_title(["Сколько разных моделей в одной работе", "How many different models per work"][i], fontsize=10, color=T["INK"], loc="left", pad=22)
    a2.text(0, 1.02, [f"рои со смесью моделей: {mixed} работ · рои из одной модели: {mono}", f"mixed-model swarms: {mixed} works · single-model swarms: {mono}"][i],
            transform=a2.transAxes, ha="left", va="bottom", fontsize=8, color=T["SOFT"])
    for a in (a1, a2): a.spines["left"].set_visible(False)
    a1.spines["bottom"].set_visible(False); fig.tight_layout(w_pad=3)
    return save(fig, "models", lang, th)

def topics(T, lang, th):
    i = 0 if lang == "ru" else 1
    ts = [t for t in L["topic"] if any(t in (m.get("topics") or []) for m in META)]
    es = [e for e in EVID_ORDER if any(m.get("evidence") == e for m in META)]
    grid = [[sum(1 for m in META if t in (m.get("topics") or []) and m.get("evidence") == e) for e in es] for t in ts]
    fig, ax = plt.subplots(figsize=(10.5, 0.42 * len(ts) + 1.6)); mx = max(max(r) for r in grid) or 1
    for a, r in enumerate(grid):
        for b, v in enumerate(r):
            if v:
                ax.scatter(b, a, s=60 + 900 * v / mx, color=ecol(T, es[b]), alpha=0.9, edgecolor=T["BG"], linewidth=1.0)
                big = v / mx > 0.25
                ax.text(b, a, str(v), ha="center", va="center", fontsize=7.8, color=("#ffffff" if big else T["INK"]), fontweight="semibold" if big else "normal")
    tot = [sum(r) for r in grid]
    ax.set_yticks(range(len(ts))); ax.set_yticklabels([f"{L['topic'][t][i]}  ·  {n}" for t, n in zip(ts, tot)], fontsize=8.6)
    ax.set_xticks(range(len(es))); ax.set_xticklabels([L["evid_short"][e][i] for e in es], fontsize=7.8)
    ax.invert_yaxis(); ax.set_xlim(-0.6, len(es) - 0.4); ax.set_ylim(len(ts) - 0.4, -0.6)
    ax.tick_params(length=0); [s.set_visible(False) for s in ax.spines.values()]; ax.xaxis.tick_top()
    return save(fig, "topics", lang, th)

def mechanisms(T, lang, th):
    i = 0 if lang == "ru" else 1
    S1, S2, S3, S4 = T["SLOTS"][0], T["SLOTS"][6], T["SLOTS"][4], T["SLOTS"][3]
    cols = [
        (["Из чего собран рой", "What a swarm is made of"], S1, [(["Модели", "Models"], ["одна копия или смесь разных", "copies of one model or a mix"]),
            (["Роли и правила", "Roles and rules"], ["нарисованы людьми, выучены или без них", "drawn by people, learned, or none"]),
            (["Память", "Memory"], ["у каждого своя, общие файлы, вики", "per agent, shared files, wikis"])]),
        (["Как агенты связаны", "How agents are connected"], S2, [(["Переписка", "Messages"], ["чат, почта, доска объявлений", "chat, mail, message board"]),
            (["Общие артефакты", "Shared artifacts"], ["git, вики, заметки, датасеты", "git, wikis, notes, datasets"]),
            (["Рынки и игры", "Markets and games"], ["цены, голосования, соревнования", "prices, votes, competitions"])]),
        (["Что возникает в рое", "What emerges in a swarm"], S3, [(["Самоорганизация", "Self-organization"], ["роли, интеграторы, договорённости · гл. 5", "roles, integrators, agreements · Ch. 5"]),
            (["Эхо и аттракторы", "Echo and attractors"], ["копии модели сходятся к одному · гл. 8", "copies of a model converge · Ch. 8"]),
            (["Согласие и каскады", "Consensus and cascades"], ["конформность, большинство, раскол · гл. 9", "conformity, majority, splits · Ch. 9"]),
            (["Заражение и сговор", "Contagion and collusion"], ["идеи-паразиты, скрытые каналы · гл. 7", "parasitic ideas, covert channels · Ch. 7"])]),
        (["Что это даёт и чем грозит", "What it buys and what it risks"], S4, [(["Скорость", "Speed"], ["параллельность за токены · гл. 4", "parallelism paid in tokens · Ch. 4"]),
            (["Память", "Memory"], ["больше контекста на всех · гл. 6", "more context across agents · Ch. 6"]),
            (["Качество", "Quality"], ["выше лучшего одиночки в отдельных постановках · гл. 4", "above the best single agent in specific settings · Ch. 4"]),
            (["Сбои", "Failures"], ["инциденты, взлом Hugging Face · гл. 3, 10", "incidents, the Hugging Face breach · Ch. 3, 10"])]),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 5.4)); ax.set_xlim(0, 100); ax.set_ylim(0, 60); ax.axis("off")
    W, gap = 22.4, 2.9
    for ci, (title, col, boxes) in enumerate(cols):
        x0 = ci * (W + gap) + 0.6
        ax.text(x0, 57, title[i], fontsize=10, color=T["INK"], fontweight="semibold", va="top")
        n = len(boxes); h = (49 - (n - 1) * 2.2) / n
        for bi, (head, sub) in enumerate(boxes):
            y = 50 - (bi + 1) * h - bi * 2.2
            ax.add_patch(FancyBboxPatch((x0, y), W, h, boxstyle="round,pad=0.25,rounding_size=1.2", linewidth=1.2, edgecolor=col, facecolor=T["BG2"]))
            ax.add_patch(FancyBboxPatch((x0, y + h - 0.6), 1.2, 0.6, boxstyle="square,pad=0", linewidth=0, facecolor=col))
            ax.text(x0 + 1.4, y + h - 1.6, head[i], fontsize=9, color=T["INK"], fontweight="semibold", va="top")
            body, _, ch = sub[i].partition(" · ")
            if ch: ax.text(x0 + W - 1.2, y + h - 1.75, ch, fontsize=7.4, color=T["FAINT"], va="top", ha="right")
            ax.text(x0 + 1.4, y + h - 5.0, "\n".join(textwrap.wrap(body, 28)), fontsize=7.6, color=T["SOFT"], va="top", linespacing=1.35)
        if ci < len(cols) - 1:
            ax.add_patch(FancyArrowPatch((x0 + W + 0.35, 25), (x0 + W + gap - 0.35, 25), arrowstyle="-|>", mutation_scale=11, color=T["FAINT"], lw=1.2))
    return save(fig, "mechanisms", lang, th)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); made = []
    for th, T in THEMES.items():
        setup(T)
        for lang in ("ru", "en"):
            for f in (scale_map, timeline, orgs, models, topics, mechanisms): made.append(f(T, lang, th))
    print(len(made), "charts:", ", ".join(made))

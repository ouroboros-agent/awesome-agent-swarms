#!/usr/bin/env python3
"""Build the static bilingual site: content/{ru,en}/*.md + data/*.json + assets/ -> site/.

  python scripts/build_site.py            # build site/
  python scripts/build_site.py --check    # build, then fail on broken internal links / missing images

No JavaScript is needed to read or navigate: theme toggle, mobile table of contents, card disclosure,
image zoom (:target) and atlas filters (:has) are HTML+CSS. assets/js/enhance.js only adds niceties
(remembered theme, atlas text search and counts, scroll hints on overflowing tables).
"""
import html, json, os, re, shutil, sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import markdown  # pinned in requirements.txt

CONTENT, DATA, ASSETS, OUT = (os.path.join(ROOT, d) for d in ("content", "data", "assets", "site"))
LANGS = ("ru", "en")
PAGE_ORDER = ["index"] + [f"ch{n:02d}" for n in range(1, 12)] + ["atlas", "glossary", "sources", "about"]
SITE_TITLE = {"ru": "Динамика роёв LLM-агентов", "en": "On the Dynamics of LLM Agent Swarms"}
SITE_SUB = {"ru": "Масштабирование, координация и коллективное поведение", "en": "Scaling, Coordination, and Collective Behavior"}
AUTHORS = "Anton Razzhigaev, Ouroboros"
UI = {
 "ru": dict(toc="Содержание", on_page="На странице", chapter="Глава", details_full="Подробнее: метод, результаты, оговорки",
            details_short="Подробнее", authors="Авторы", orgs="Организации", published="Опубликовано", status="Статус", source="Источник",
            prev="Назад", next="Далее", theme="Светлая тема", lang_other="English", lang_other_code="en", skip="К тексту",
            zoom="Открыть крупно", close="Закрыть", original="оригинал", scroll="⟷ таблицу можно прокрутить", all="Все",
            f_topic="Тема", f_evid="Класс доказательств", f_scale="Масштаб (одновременно)", f_type="Тип источника", f_level="Где в обзоре", f_chapter="Глава",
            atlas_hint="Фильтры работают без JavaScript. Тема, класс доказательств и масштаб размечены для аналитического корпуса; у строк «Ещё по теме» тема — по главе, где они стоят; без класса и масштаба они видны при «Все».",
            to_card="к карточке", to_row="в таблицу", in_ch="гл.", full="Весь текст на одной странице", license="Текст и таблицы — CC BY 4.0, код — MIT; рисунки из работ — права их владельцев (подпись под рисунком).",
            cite="Как цитировать", cutoff="Срез: 3 октября 2026", search="Поиск по атласу", shown="Показано", updates="Обновление после среза",
            related="Ещё по теме", resources="Разделы", chapters="Главы", menu="Меню"),
 "en": dict(toc="Contents", on_page="On this page", chapter="Chapter", details_full="Details: method, results, caveats",
            details_short="Details", authors="Authors", orgs="Organizations", published="Published", status="Status", source="Source",
            prev="Previous", next="Next", theme="Light theme", lang_other="Русский", lang_other_code="ru", skip="Skip to text",
            zoom="Enlarge", close="Close", original="original", scroll="⟷ scroll the table sideways", all="All",
            f_topic="Topic", f_evid="Evidence class", f_scale="Scale (simultaneous)", f_type="Source type", f_level="Where in the survey", f_chapter="Chapter",
            atlas_hint="Filters work without JavaScript. Topic, evidence class and scale are labelled for the analytic corpus; related-work rows take the topic of the chapter they appear in and show under “All” for evidence class and scale.",
            to_card="to card", to_row="to table", in_ch="Ch.", full="Whole text on one page", license="Text and tables: CC BY 4.0; code: MIT; figures from the works keep their owners’ rights (see each caption).",
            cite="How to cite", cutoff="Cut-off: 3 October 2026", search="Search the atlas", shown="Shown", updates="Update after the cut-off",
            related="Related work", resources="Sections", chapters="Chapters", menu="Menu"),
}
MONTHS = {"ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
          "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
MONTHS_NOM = {"ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"],
              "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
TOPIC = OrderedDict([
 ("scaling_economics", ("экономика и масштаб", "economics & scale")), ("self_organization", ("самоорганизация", "self-organization")),
 ("memory", ("память", "memory")), ("safety_alignment", ("безопасность", "safety")), ("contagion_security", ("заражение и атаки", "contagion & attacks")),
 ("echo_diversity", ("эхо и разнообразие", "echo & diversity")), ("social_dynamics", ("убеждения и согласие", "beliefs & consensus")),
 ("wild_field", ("дикая природа", "in the wild")), ("infrastructure", ("платформы и симуляторы", "platforms & simulators")),
 ("training_rl", ("обучение (RL)", "training (RL)")), ("theory", ("теория", "theory"))])
EVID = OrderedDict([
 ("live_experiment", ("эксперимент с LLM-агентами", "experiment with LLM agents")), ("field_observation", ("наблюдение в дикой природе", "field observation")),
 ("incident", ("реальный инцидент", "real incident")), ("engineering_report", ("инженерный отчёт", "engineering report")),
 ("system_card_eval", ("системная карта", "system card")), ("surrogate_simulation", ("модель-суррогат", "surrogate model")),
 ("theory_essay", ("теория / эссе", "theory / essay")), ("benchmark", ("бенчмарк / датасет", "benchmark / dataset"))])
STYPE = OrderedDict([
 ("peer_reviewed", ("рецензированная статья", "peer-reviewed")), ("preprint", ("препринт", "preprint")), ("system_card", ("системная карта", "system card")),
 ("lab_report", ("блог / отчёт лаборатории", "lab blog / report")), ("incident_report", ("расследование инцидента", "incident report")),
 ("essay_blog", ("эссе, блог, интервью", "essay, blog, interview")), ("dataset_platform", ("датасет / платформа", "dataset / platform")),
 ("other", ("другое (новости, документация)", "other (news, docs)"))])
KIND2STYPE = {"journal_or_conference": "peer_reviewed", "preprint": "preprint", "system_card": "system_card", "lab_blog": "lab_report",
              "incident_report": "incident_report", "essay": "essay_blog", "dataset": "dataset_platform", "bundle": "incident_report",
              "repo": "other", "news": "other", "web": "other"}
SCALE = OrderedDict([("s1", ("1 агент", "1 agent")), ("s2", ("2–9", "2–9")), ("s10", ("10–99", "10–99")), ("s100", ("100–999", "100–999")),
                     ("s1000", ("1 000+", "1,000+")), ("sna", ("не указан / не применимо", "not stated / n.a."))])
LEVEL = OrderedDict([("card", ("карточка", "card")), ("related", ("строка «Ещё по теме»", "related-work row")), ("other", ("ссылка в тексте", "link in text"))])
CH_TOPICS = {"ch03": ["safety_alignment", "contagion_security"], "ch04": ["scaling_economics"], "ch05": ["self_organization"], "ch06": ["memory"],
             "ch07": ["safety_alignment"], "ch08": ["echo_diversity"], "ch09": ["social_dynamics"], "ch10": ["wild_field"]}

# ---------------------------------------------------------------- data
def jload(p, default=None):
    p = os.path.join(ROOT, p)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

REG = jload("data/works.json", {"works": [], "stats": {}, "text_url_map": {}})
WORKS = OrderedDict((w["id"], w) for w in REG["works"])
ALIAS = {a: w["id"] for w in REG["works"] for a in (w.get("aliases") or [])}
STATS = jload("data/stats.json", {}) or REG.get("stats", {})
PASS = jload("data/i18n/passports.json", {}) or {}
PASS_RU = jload("data/i18n/passports_ru.json", {}) or {}
FIGREG = {f["file"]: f for f in (jload("data/figures.json", {"figures": []})["figures"])}
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_registry import key as url_key  # same normalization as the registry
URLKEY2ID = {}
for w in REG["works"]:
    for k in w.get("identity_keys") or []: URLKEY2ID.setdefault(k, w["id"])
for u, wid in (REG.get("text_url_map") or {}).items(): URLKEY2ID.setdefault(url_key(u), wid)

def esc(s): return html.escape(str(s or ""), quote=True)

CYR_RX = re.compile(r"[А-Яа-яЁё]")
def lang_safe(s, lang):
    """Registry fields copied from October metadata are partly Russian; never show them on English pages."""
    return "" if (lang == "en" and s and CYR_RX.search(str(s))) else (s or "")

def fmt_int(n, lang):
    s = f"{int(n):,}"
    return s.replace(",", " ") if lang == "ru" else s

def fmt_date(s, lang, short=False):
    s = str(s or "")
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)
    if not m: return esc(s)
    y, mo, d = m.group(1), int(m.group(2)), m.group(3)
    if d: return f"{int(d)} {MONTHS[lang][mo-1]} {y}"
    return f"{MONTHS_NOM[lang][mo-1]} {y}"

def read_page(lang, page):
    p = os.path.join(CONTENT, lang, page + ".md")
    if not os.path.exists(p): return None
    text = open(p, encoding="utf-8").read()
    fm = OrderedDict()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).split("\n"):
            k, _, v = line.partition(":")
            if k.strip(): fm[k.strip()] = v.strip()
        text = text[m.end():]
    return fm, text

def blocks(body):
    out, buf = [], []
    lines = body.split("\n"); i = 0
    def flush():
        if buf: out.append(("md", "\n".join(buf))); buf.clear()
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^:::(\w+)\s*(.*)$", ln)
        if m:
            flush(); j = i + 1; inner = []
            while j < len(lines) and lines[j].strip() != ":::": inner.append(lines[j]); j += 1
            out.append((m.group(1), m.group(2).strip(), "\n".join(inner))); i = j + 1; continue
        if ln.strip().startswith("!fig "):
            flush(); out.append(("fig", ln.strip()[5:], "")); i += 1; continue
        buf.append(ln); i += 1
    flush()
    return out

# card location map (language-independent; taken from RU, checked against EN by check_content.py)
CARD_PAGE, ROW_PAGE = {}, {}
for page in PAGE_ORDER:
    r = read_page("ru", page)
    if not r: continue
    for kind, arg, txt in [b for b in blocks(r[1]) if b[0] in ("card", "short")]:
        cid = ALIAS.get(arg.split()[0], arg.split()[0]); CARD_PAGE[cid] = page
    for b in blocks(r[1]):
        if b[0] == "related":
            for u in re.findall(r"^\|\s*\[[^\]]*\]\((https?://[^)\s]+)\)", b[2], re.M):
                wid = URLKEY2ID.get(url_key(u))
                if wid: ROW_PAGE.setdefault(wid, page)
def work_anchor(wid):
    wid = ALIAS.get(wid, wid)
    w = WORKS.get(wid) or {}
    if wid in CARD_PAGE: return CARD_PAGE[wid], "w-" + wid
    if w.get("part_of") and w["part_of"] in CARD_PAGE: return CARD_PAGE[w["part_of"]], "w-" + w["part_of"]
    if wid in ROW_PAGE: return ROW_PAGE[wid], "w-" + wid
    return None, None

# ---------------------------------------------------------------- markdown helpers
MD = markdown.Markdown(extensions=["tables", "sane_lists", "attr_list"])
NBSP_NUM = re.compile(r"(?<=\d) (?=\d{3}(?!\d))")
SUP = re.compile(r"(?<=[A-Za-zА-Яа-я0-9λ)])\^\(([^)\s]{1,14})\)|(?<=[A-Za-zА-Яа-я0-9λ)])\^([0-9λ−-][0-9,.λ]{0,6})")

def stat_sub(text, lang):
    def r(m):
        v = STATS.get(m.group(1))
        return fmt_int(v, lang) if isinstance(v, int) else str(v if v is not None else "?")
    return re.sub(r"\{\{stat:(\w+)\}\}", r, text)

def md(text, lang):
    text = stat_sub(text or "", lang)
    if lang == "ru": text = NBSP_NUM.sub(" ", text)
    text = SUP.sub(lambda m: f"<sup>{m.group(1) or m.group(2)}</sup>", text)
    MD.reset()
    return MD.convert(text)

def md_inline(text, lang):
    h = md(text, lang).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)

def wrap_tables(h, lang):
    return re.sub(r"<table>(.*?)</table>", lambda m: (
        f'<div class="table-wrap" role="region" tabindex="0" aria-label="{esc(UI[lang]["scroll"])}"><table>{m.group(1)}</table></div>'
        f'<p class="scroll-hint" aria-hidden="true">{UI[lang]["scroll"]}</p>'), h, flags=re.S)

CHREF_RU = re.compile(r"(?<![\w-])(гл\.|главы|главе|главу|глава|главах|главам)(\s|&nbsp;| )+(\d{1,2}(?:(?:\s*,\s*|\s+и\s+|\s*[–-]\s*)\d{1,2})*)")
CHREF_EN = re.compile(r"(?<![\w-])(Ch\.|Chs\.|Chapter|Chapters|ch\.)(\s|&nbsp;| )+(\d{1,2}(?:(?:\s*,\s*|\s+and\s+|\s*[–-]\s*)\d{1,2})*)")
def link_chapters(h, lang, page_prefix=""):
    rx = CHREF_RU if lang == "ru" else CHREF_EN
    parts = re.split(r"(<[^>]+>)", h); depth = 0; out = []
    for p in parts:
        if p.startswith("<"):
            if re.match(r"<a[\s>]", p): depth += 1
            elif p.startswith("</a"): depth = max(0, depth - 1)
            out.append(p); continue
        if depth or not p: out.append(p); continue
        def rep(m):
            nums = re.sub(r"\d{1,2}", lambda n: (f'<a class="chref" href="{page_prefix}ch{int(n.group(0)):02d}.html">{n.group(0)}</a>'
                                                 if 1 <= int(n.group(0)) <= 11 else (f'<a class="chref" href="{page_prefix}atlas.html">12</a>' if n.group(0) == "12" else n.group(0))), m.group(3))
            return m.group(1) + m.group(2) + nums
        out.append(rx.sub(rep, p))
    return "".join(out)

def rewrite_internal(h, lang, single=False):
    def card_link(m):
        wid = m.group(1); pg, anc = work_anchor(wid)
        if not pg: return f'href="atlas.html#a-{esc(wid)}"' if not single else f'href="#a-{esc(wid)}"'
        return f'href="{"" if single else pg + ".html"}#{anc}"'
    h = re.sub(r'href="#w-([\w-]+)"', card_link, h)
    if single: h = re.sub(r'href="(ch\d\d|glossary|about|index)\.html(#[^"]*)?"', lambda m: f'href="{m.group(2) or "#p-" + m.group(1)}"', h)
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a class="ext" href="\1" rel="noopener"', h)
    return h

# ---------------------------------------------------------------- figures
FIG_COUNTER = [0]
def chart_variants(f, lang):
    m = re.match(r"(dash_[a-z]+)_dark\.png$", f)
    if not m: return None
    base = m.group(1); out = {}
    for th in ("dark", "light"):
        for cand in (f"{base}_{lang}_{th}.png",):
            if os.path.exists(os.path.join(ASSETS, "charts", cand)): out[th] = "charts/" + cand
    return out if len(out) == 2 else None

def figure(spec, lang, rel):
    parts = [p.strip() for p in spec.split("|")]
    f = parts[0]; cap = parts[1] if len(parts) > 1 else ""; credit = parts[2] if len(parts) > 2 else ""
    FIG_COUNTER[0] += 1; n = FIG_COUNTER[0]
    sub = "charts" if f.startswith("dash_") else "figures"
    var = chart_variants(f, lang)
    def src(p): return f"{rel}assets/{p}"
    if var:
        imgs = (f'<img class="theme-dark-only" loading="lazy" decoding="async" src="{src(var["dark"])}" alt="{esc(strip_tags(md_inline(cap, lang))[:180])}">'
                f'<img class="theme-light-only" loading="lazy" decoding="async" src="{src(var["light"])}" alt="{esc(strip_tags(md_inline(cap, lang))[:180])}">')
        big = src(var["dark"]); frame = "frame chart"
    else:
        web = f"{sub}/web/{f}" if os.path.exists(os.path.join(OUT, "assets", sub, "web", f)) else f"{sub}/{f}"
        imgs = f'<img loading="lazy" decoding="async" src="{src(web)}" alt="{esc(strip_tags(md_inline(cap, lang))[:180])}">'
        big = src(f"{sub}/{f}"); frame = "frame dark" if f.startswith("dash_") else "frame"
    capt = md_inline(cap, lang); cred = md_inline(credit, lang) if credit else ""
    return (f'<figure class="fig" id="fig-{n}"><a class="zoom" href="#zoom-{n}" aria-label="{UI[lang]["zoom"]}"><div class="{frame}">{imgs}</div></a>'
            f'<figcaption>{capt}' + (f'<span class="credit">{cred}</span>' if cred else "") +
            f' <a class="orig" href="{big}">{UI[lang]["original"]}</a></figcaption></figure>'
            f'<div class="lightbox" id="zoom-{n}" role="dialog" aria-label="{UI[lang]["zoom"]}"><a class="lb-close" href="#fig-{n}" aria-label="{UI[lang]["close"]}">×</a>'
            f'<div class="lb-tools"><input type="checkbox" id="actual-{n}" class="lb-actual">'
            f'<label for="actual-{n}">{"Размер 100% · прокрутка" if lang == "ru" else "Actual size · scroll to pan"}</label>'
            f'<a href="{big}" target="_blank" rel="noopener">{UI[lang]["original"]} ↗</a></div>'
            f'<div class="lb-img" tabindex="0" aria-label="{UI[lang]["zoom"]}"><img loading="lazy" src="{big}" alt="{esc(strip_tags(capt))}"></div></div>')

def strip_tags(h): return re.sub(r"<[^>]+>", "", h)

# ---------------------------------------------------------------- cards
RUNIN = {"ru": r"Что сделали|Что получилось|Почему это важно|Оговорки|Что показали|Главное", "en": r"What they did|Results|Why it matters|Caveats|What it shows"}
def passport(w, lang):
    P = PASS.get(w["id"], {}); R = PASS_RU.get(w["id"], {})
    if lang == "ru":
        au = (authors_line(w, lang) if w.get("metadata_corrected") else None) or R.get("authors") or authors_line(w, lang); orgs = R.get("institutions_short") or ", ".join(w.get("orgs") or [])
        st = P.get("status_ru") or R.get("venue_status") or ""
    else:
        au = (authors_line(w, lang) if w.get("metadata_corrected") else None) or P.get("authors_en") or lang_safe(authors_line(w, lang), lang); orgs = P.get("orgs_en") or lang_safe(", ".join(w.get("orgs") or []), lang)
        st = P.get("status_en") or ""
    date = fmt_date(R.get("date_first_public") or w.get("date_first_public"), lang)
    rows = [(UI[lang]["authors"], esc(au)), (UI[lang]["orgs"], esc(orgs)), (UI[lang]["published"], date), (UI[lang]["status"], esc(st))]
    u = (w.get("urls") or {}).get("primary")
    if u:
        su = re.sub(r"^https?://(www\.)?", "", u); su = su if len(su) < 80 else su[:78] + "…"
        rows.append((UI[lang]["source"], f'<a class="ext url" href="{esc(u)}" rel="noopener">{esc(su)}</a>'))
    if w.get("updates"):
        up = w["updates"][-1]
        txt = up["what"] if lang == "en" else ru_update(w["id"], up)
        rows.append((UI[lang]["updates"], f'{fmt_date(up["date"], lang)}: {esc(txt)} <a class="ext url" href="{esc(up["url"])}" rel="noopener">{esc(up.get("doi") or up["url"])}</a>'))
    return '<dl class="passport">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v) + "</dl>"

RU_UPDATES = {"piao-polarization": "опубликована в Nature Communications (поступила 14 апреля 2025, принята 21 сентября 2026); та же работа, что arXiv:2501.05171; CC BY 4.0."}
def ru_update(wid, up): return RU_UPDATES.get(wid, up["what"])

def authors_line(w, lang):
    a = [x for x in (w.get("authors") or []) if x]
    n = w.get("n_authors") or len(a)
    try: n = int(n)
    except (TypeError, ValueError): n = len(a)
    if not a: return ", ".join(w.get("orgs") or [])
    s = ", ".join(a[:6])
    if n and n > 6: s += (f" и др. (всего {n})" if lang == "ru" else f" et al. ({n} authors)")
    return s

def tags(w, lang):
    c = w.get("corpus") or {}; i = 0 if lang == "ru" else 1; out = []
    if c.get("evidence") in EVID: out.append(f'<span class="tag ev">{EVID[c["evidence"]][i]}</span>')
    for t in (c.get("topics") or [])[:3]:
        if t in TOPIC: out.append(f'<span class="tag t">{TOPIC[t][i]}</span>')
    sc = c.get("scale_note_ru") if lang == "ru" else (PASS.get(w["id"], {}).get("scale_en"))
    if sc: out.append(f'<span class="tag sc">{esc(sc)}</span>')
    return "".join(out)

def card_title(w, lang):
    if lang == "ru": return PASS_RU.get(w["id"], {}).get("display_title") or PASS.get(w["id"], {}).get("title_en") or w.get("title") or w["id"]
    if w.get("metadata_corrected") and w.get("title"): return w["title"]
    return PASS.get(w["id"], {}).get("title_en") or lang_safe(w.get("title"), lang) or w["id"]

LEADS = {"ru": {}, "en": {}}
def render_card(kind, arg, body, lang, rel, single):
    cid = ALIAS.get(arg.split()[0], arg.split()[0]); w = WORKS.get(cid) or {"id": cid, "urls": {}}
    lines = body.split("\n"); lead = ""
    while lines and not lines[0].strip(): lines.pop(0)
    if lines and re.match(r"^lead:\s*", lines[0]): lead = re.sub(r"^lead:\s*", "", lines.pop(0)).strip()
    LEADS[lang][cid] = lead
    figs, rest = [], []
    for ln in lines:
        (figs if ln.strip().startswith("!fig ") else rest).append(ln)
    text = "\n".join(rest).strip()
    text = re.sub(rf"(?<!\n\n)\s*(\*\*(?:{RUNIN[lang]})[^*]{{0,24}}\*\*)", lambda m: "\n\n" + m.group(1), text).strip()
    body_h = wrap_tables(md(text, lang), lang)
    body_h = re.sub(rf"<strong>((?:{RUNIN[lang]})[^<]{{0,24}})</strong>", r'<strong class="lab">\1</strong>', body_h)
    figs_h = "".join(figure(f.strip()[5:], lang, rel) for f in figs)
    u = (w.get("urls") or {}).get("primary"); title = esc(card_title(w, lang))
    tl = f'<a class="ext" href="{esc(u)}" rel="noopener">{title}</a>' if u else title
    full = kind == "card"; opn = " open" if single else ""
    head = (f'<header class="chead"><div class="tags">{tags(w, lang)}</div><h3 class="ctitle">{tl}</h3>'
            + (f'<p class="clead">{md_inline(lead, lang)}</p>' if lead else "") + "</header>")
    det = (f'<details class="more"{opn}><summary>{UI[lang]["details_full" if full else "details_short"]}</summary>'
           f'{passport(w, lang)}<div class="cbody">{body_h}</div></details>')
    cls = "card" if full else "card short"
    return f'<article class="{cls}" id="w-{esc(cid)}">{head}{figs_h if full else ""}{det}{"" if full else figs_h}</article>'

# ---------------------------------------------------------------- other blocks
def fmt_tl_date(d, lang):
    d = d.strip()
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", d)
    if m: return f"{int(m.group(1))} {MONTHS[lang][int(m.group(2))-1]} {m.group(3)}", f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return esc(d).replace("-", "–"), None

def render_timeline(body, lang):
    items = []
    for line in body.strip().split("\n"):
        if not line.strip(): continue
        d, _, e = line.partition("|"); dd, iso = fmt_tl_date(d, lang)
        t = f'<time datetime="{iso}">{dd}</time>' if iso else f'<span class="tdate">{dd}</span>'
        items.append(f'<li>{t}<div class="te">{md_inline(e.strip(), lang)}</div></li>')
    return '<ol class="timeline">' + "".join(items) + "</ol>"

def render_related(body, lang):
    rows = [r for r in body.strip().split("\n") if r.strip().startswith("|")]
    if len(rows) < 3: return wrap_tables(md(body, lang), lang)
    head = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    items = []
    for r in rows[2:]:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))]
        first = cells[0]; um = re.search(r"\((https?://[^)\s]+)\)", first)
        wid = URLKEY2ID.get(url_key(um.group(1))) if um else None
        aid = f' id="w-{esc(wid)}"' if wid and ROW_PAGE.get(wid) and work_anchor(wid)[1] == "w-" + wid else ""
        mid = cells[1] if len(cells) > 2 else ""
        rest = cells[2:] if len(cells) > 2 else cells[1:]
        extra = "".join(f'<p class="rabout">{md_inline(c, lang)}</p>' for c in rest)
        if len(head) > 3:  # e.g. physical swarms / comparison tables keep column labels
            extra = "".join(f'<p class="rabout"><span class="rlab">{esc(head[i+2])}:</span> {md_inline(c, lang)}</p>' for i, c in enumerate(rest))
        items.append(f'<li{aid}><div class="rtitle">{md_inline(first, lang)}</div>' + (f'<div class="rwho">{md_inline(mid, lang)}</div>' if mid else "") + extra + "</li>")
    return '<ul class="related">' + "".join(items) + "</ul>"

def render_cover(body, lang):
    kv = OrderedDict()
    for line in body.strip().split("\n"):
        k, _, v = line.partition(":"); kv[k.strip()] = v.strip()
    ring = ('<svg class="ring" width="54" height="54" viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="21" fill="none" stroke="currentColor" stroke-width="3"/>'
            '<circle cx="48" cy="27" r="4" fill="currentColor"/></svg>')
    return (f'<section class="cover"><div class="bar"></div><p class="kicker">{esc(kv.get("kicker", ""))}</p>'
            f'<h1>{kv.get("title", "")}</h1><p class="subtitle">{esc(kv.get("subtitle", ""))}</p>'
            f'<p class="byline">{esc(AUTHORS)}</p>'
            f'<div class="lede">{md(kv.get("lede", ""), lang)}</div><p class="meta">{md_inline(kv.get("meta", ""), lang)}</p>'
            f'<div class="brand">{ring}<div><b>Ouroboros</b><span>{"обзор исследований" if lang == "ru" else "research survey"}</span></div></div></section>')

# ---------------------------------------------------------------- atlas
def scale_bucket(c):
    n = c.get("agents_max_simultaneous")
    if not isinstance(n, (int, float)): return "sna"
    return "s1" if n <= 1 else "s2" if n < 10 else "s10" if n < 100 else "s100" if n < 1000 else "s1000"

ROW_TEXT = {"ru": {}, "en": {}}
LINK_TEXT = {"ru": {}, "en": {}}   # url -> the survey's own link text, used as a title fallback for untitled resources
_ov = jload("data/registry_overrides.json", {}) or {}
LABELS = {k: v for k, v in (_ov.get("labels") or {}).items() if not k.startswith("_")}
def label_of(wid, lang): return (LABELS.get(wid) or {}).get(lang)
def collect_row_text(lang):
    for page in PAGE_ORDER:
        r = read_page(lang, page)
        if not r: continue
        for txt, u in re.findall(r"\[([^\]]{3,})\]\((https?://[^)\s]+)\)", r[1]):
            wid = URLKEY2ID.get(url_key(u))
            if wid: LINK_TEXT[lang].setdefault(wid, re.sub(r"[*_«»“”\"]", "", txt).strip())
        for b in blocks(r[1]):
            if b[0] != "related": continue
            for row in b[2].split("\n"):
                if not row.strip().startswith("|"): continue
                cells = [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]
                um = re.search(r"\[([^\]]*)\]\((https?://[^)\s]+)\)", cells[0])
                if not um: continue
                wid = URLKEY2ID.get(url_key(um.group(2)))
                if wid: ROW_TEXT[lang].setdefault(wid, (um.group(1), cells[1] if len(cells) > 2 else "", cells[-1]))

def render_atlas(lang, rel):
    i = 0 if lang == "ru" else 1; ui = UI[lang]
    items, counts = [], defaultdict(lambda: defaultdict(int))
    def chapters_of(w):
        pg = [p for p in (w.get("source_pages") or []) if p.startswith("ch")]
        a = work_anchor(w["id"])[0]
        if a and a not in pg: pg.append(a)
        return sorted(set(pg))
    rows = []
    for w in WORKS.values():
        if w["level"] == "inline_link" and w["kind"] in ("news", "web"): lvl = "other"
        c = w.get("corpus") or {}
        lvl = "card" if w["level"] in ("full_card", "short_card", "mention_in_corpus", "constituent") else ("related" if w["level"] == "table_row" else "other")
        topics = [t for t in (c.get("topics") or []) if t in TOPIC]
        ev = c.get("evidence") if c.get("evidence") in EVID else ""
        filter_topics = topics or sorted({t for ch in chapters_of(w) for t in CH_TOPICS.get(ch, [])})   # non-corpus rows: topic of their chapter
        sb = scale_bucket(c) if c else "sna"
        st = c.get("source_type") if c.get("source_type") in STYPE else KIND2STYPE.get(w["kind"], "other")
        chs = chapters_of(w)
        for t in filter_topics: counts["t"][t] += 1
        if ev: counts["e"][ev] += 1
        counts["s"][sb] += 1; counts["k"][st] += 1; counts["l"][lvl] += 1
        for ch in chs: counts["c"][ch] += 1
        rt = ROW_TEXT[lang].get(w["id"])
        title = card_title(w, lang) if (w["id"] in CARD_PAGE or lvl == "card") else (rt[0] if rt else (lang_safe(w.get("title"), lang) or (w.get("urls") or {}).get("primary") or w["id"]))
        title = lang_safe(title, lang) if not re.match(r"https?://", str(title)) else ""
        title = label_of(w["id"], lang) or title or LINK_TEXT[lang].get(w["id"]) or (w.get("urls") or {}).get("primary") or w["id"]
        summary = LEADS[lang].get(w["id"]) or (rt[2] if rt else "")
        who = (PASS.get(w["id"], {}).get("orgs_en") if lang == "en" else PASS_RU.get(w["id"], {}).get("institutions_short")) or (rt[1] if rt else lang_safe(", ".join(w.get("orgs") or []), lang))
        date = (c.get("month") or w.get("date_first_public") or "")[:7]
        u = (w.get("urls") or {}).get("primary") or ""
        pg, anc = work_anchor(w["id"])
        go = f'<a class="go" href="{pg}.html#{anc}">{ui["in_ch"]} {int(pg[2:]) if pg and pg.startswith("ch") else ""} →</a>' if pg else ""
        tg = ""
        if ev: tg += f'<span class="tag ev">{EVID[ev][i]}</span>'
        for t in topics[:3]: tg += f'<span class="tag t">{TOPIC[t][i]}</span>'
        sc = c.get("scale_note_ru") if lang == "ru" else PASS.get(w["id"], {}).get("scale_en")
        if sc: tg += f'<span class="tag sc">{esc(sc)}</span>'
        mods = ", ".join((c.get("models") or [])[:4]) + (f" +{len(c['models'])-4}" if len(c.get("models") or []) > 4 else "")
        rows.append((date or "0000", f'<li class="w" id="a-{esc(w["id"])}" data-t="{" ".join(filter_topics)}" data-e="{ev}" data-s="{sb}" data-k="{st}" data-l="{lvl}" data-c="{" ".join(chs)}">'
                    f'<div class="wd">{esc(date[5:7] + "." + date[:4] if len(date) >= 7 else date)}</div><div class="wm">'
                    f'<div class="wt">' + (f'<a class="ext" href="{esc(u)}" rel="noopener">{md_inline(esc(title), lang) if False else esc(strip_tags(md_inline(title, lang)))}</a>' if u else esc(title)) + "</div>"
                    + (f'<div class="ww">{esc(strip_tags(md_inline(who, lang)))}</div>' if who else "")
                    + (f'<div class="ws">{md_inline(summary, lang)}</div>' if summary else "")
                    + (f'<div class="wg">{tg}</div>' if tg else "") + (f'<div class="wmod">{esc(mods)}</div>' if mods else "")
                    + f'</div><div class="wgo">{go}</div></li>'))
    rows.sort(key=lambda x: x[0], reverse=True)
    groups = [("t", ui["f_topic"], TOPIC), ("e", ui["f_evid"], EVID), ("s", ui["f_scale"], SCALE), ("k", ui["f_type"], STYPE), ("l", ui["f_level"], LEVEL),
              ("c", ui["f_chapter"], OrderedDict((f"ch{n:02d}", (f"гл. {n}", f"Ch. {n}")) for n in range(1, 12)))]
    fs, css = [], []
    for g, label, vals in groups:
        opts = [f'<input type="radio" name="f{g}" id="f{g}-all" checked><label for="f{g}-all">{ui["all"]}</label>']
        for v, names in vals.items():
            if not counts[g].get(v): continue
            opts.append(f'<input type="radio" name="f{g}" id="f{g}-{v}"><label for="f{g}-{v}">{esc(names[i])} <span class="n">{counts[g][v]}</span></label>')
            sel = f'[data-{g}~="{v}"]' if g in ("t", "c") else f'[data-{g}="{v}"]'
            css.append(f'.atlas:has(#f{g}-{v}:checked) .w:not({sel}){{display:none}}')
        fs.append(f'<fieldset><legend>{label}</legend><div class="opts">{"".join(opts)}</div></fieldset>')
    return (f'<style>{"".join(css)}</style><div class="atlas"><form class="filters" onsubmit="return false">{"".join(fs)}'
            f'<div class="search js-only"><label>{ui["search"]} <input type="search" id="atlas-q" autocomplete="off"></label> <span id="atlas-count" aria-live="polite"></span></div>'
            f'<p class="hint">{ui["atlas_hint"]}</p></form><ol class="worklist">{"".join(r for _, r in rows)}</ol></div>')

def render_sources(lang):
    by_page = OrderedDict()
    for w in WORKS.values():
        pg, _ = work_anchor(w["id"])
        if not pg and w["level"] == "inline_link": pg = (w.get("source_pages") or ["other"])[0]
        if not pg: continue
        by_page.setdefault(pg, []).append(w)
    out = []
    for page in PAGE_ORDER:
        ws = by_page.get(page)
        if not ws: continue
        fm, _ = read_page(lang, page) or ({}, "")
        out.append(f'<h2 id="src-{page}">{esc(fm.get("title", page))}</h2><ol class="srclist">')
        for w in ws:
            rt = ROW_TEXT[lang].get(w["id"]); u = (w.get("urls") or {}).get("primary")
            au = lang_safe((authors_line(w, lang) if w.get("metadata_corrected") else None) or (PASS.get(w["id"], {}).get("authors_en") if lang == "en" else PASS_RU.get(w["id"], {}).get("authors")) or authors_line(w, lang), lang) \
                 or (strip_tags(md_inline(rt[1], lang)) if rt else "")
            title = card_title(w, lang) if w["id"] in CARD_PAGE or w["level"] in ("constituent", "mention_in_corpus") else (strip_tags(md_inline(rt[0], lang)) if rt else lang_safe(w.get("title"), lang))
            title = label_of(w["id"], lang) or lang_safe(title, lang) or LINK_TEXT[lang].get(w["id"], "")
            st = lang_safe((PASS.get(w["id"], {}).get("status_en") if lang == "en" else (PASS.get(w["id"], {}).get("status_ru") or PASS_RU.get(w["id"], {}).get("venue_status"))) or "", lang)
            date = fmt_date(w.get("date_first_public"), lang) if w.get("date_first_public") else ""
            bits = [esc(au) if au else "", f"<em>{esc(title)}</em>" if title else "", esc(st), date]
            line = ". ".join(b for b in bits if b)
            if u:
                su = re.sub(r"^https?://(www[.])?", "", u)
                line += f'. <a class="ext url" href="{esc(u)}" rel="noopener">{esc(su)}</a>'
            if w.get("updates"): line += f' <span class="upd">{UI[lang]["updates"]}: {esc(w["updates"][-1]["what"] if lang == "en" else ru_update(w["id"], w["updates"][-1]))}</span>'
            out.append(f'<li id="s-{esc(w["id"])}">{line}</li>')
        out.append("</ol>")
    return "".join(out)

# ---------------------------------------------------------------- page assembly
def page_body(lang, page, rel="../", single=False):
    r = read_page(lang, page)
    if not r: return None, None
    fm, text = r
    parts, h2s = [], []
    for b in blocks(text):
        k = b[0]
        if k == "md": parts.append(wrap_tables(md(b[1], lang), lang))
        elif k == "fig": parts.append(figure(b[1], lang, rel))
        elif k in ("card", "short"): parts.append(render_card(k, b[1], b[2], lang, rel, single))
        elif k == "callout": parts.append(f'<aside class="callout"><p class="ctl">{esc(b[1])}</p>{wrap_tables(md(b[2], lang), lang)}</aside>')
        elif k == "timeline": parts.append(render_timeline(b[2], lang))
        elif k == "takeaways": parts.append(f'<aside class="takeaways"><p class="ctl">{"Главное в главе" if lang == "ru" else "Takeaways"}</p>{md(b[2], lang)}</aside>')
        elif k == "findings": parts.append(f'<section class="findings">{md(b[2], lang)}</section>')
        elif k == "related": parts.append(render_related(b[2], lang))
        elif k == "cover": parts.append(render_cover(b[2], lang))
        elif k == "corpus": parts.append("%%ATLAS%%")
        elif k == "sources": parts.append("%%SOURCES%%")
        else: parts.append(md(b[2], lang))
    h = "\n".join(parts)
    n = [0]
    def hid(m):
        lvl, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if "id=" in attrs: return m.group(0)
        n[0] += 1; sid = f"s-{n[0]}" if not single else f"{page}-s-{n[0]}"
        if lvl == "2": h2s.append((sid, strip_tags(inner)))
        return f'<h{lvl} id="{sid}"{attrs}>{inner}</h{lvl}>'
    h = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", hid, h)
    if "%%ATLAS%%" in h: h = h.replace("%%ATLAS%%", render_atlas(lang, rel))
    if "%%SOURCES%%" in h: h = h.replace("%%SOURCES%%", render_sources(lang))
    h = rewrite_internal(h, lang, single)
    h = link_chapters(h, lang, "" if not single else "#p-")
    if single: h = re.sub(r'href="#p-ch(\d\d)\.html"', r'href="#p-ch\1"', h)
    return fm, (h, h2s)

def nav_list(lang, current):
    items = []
    for p in PAGE_ORDER:
        r = read_page(lang, p)
        if not r: continue
        fm = r[0]; num = fm.get("num"); title = fm.get("nav") or fm.get("title") or p
        if p == "index": title = "Главная" if lang == "ru" else "Overview"
        cur = ' aria-current="page"' if p == current else ""
        lab = f'<span class="nn">{num}</span>' if num and p.startswith("ch") else '<span class="nn">·</span>'
        items.append(f'<li><a href="{p}.html"{cur}>{lab}{esc(title)}</a></li>')
    items.append(f'<li><a href="full.html"{" aria-current=page" if current == "full" else ""}><span class="nn">≡</span>{UI[lang]["full"]}</a></li>')
    return '<ol class="navlist">' + "".join(items) + "</ol>"

def shell(lang, page, title, content, h2s, desc=""):
    ui = UI[lang]; other = ui["lang_other_code"]
    onpage = ("".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in h2s))
    onpage_h = f'<div class="onpage"><p class="navh">{ui["on_page"]}</p><ol>{onpage}</ol></div>' if onpage else ""
    nav = nav_list(lang, page)
    idx = PAGE_ORDER.index(page) if page in PAGE_ORDER else -1
    pn = ""
    if idx >= 0:
        prev = PAGE_ORDER[idx - 1] if idx > 0 else None; nxt = PAGE_ORDER[idx + 1] if idx + 1 < len(PAGE_ORDER) else None
        def t(p):
            r = read_page(lang, p); return (r[0].get("nav") or r[0].get("title")) if r else p
        pn = ('<nav class="pager" aria-label="pager">' + (f'<a class="prev" href="{prev}.html">← {esc(t(prev))}</a>' if prev else "<span></span>")
              + (f'<a class="next" href="{nxt}.html">{esc(t(nxt))} →</a>' if nxt else "") + "</nav>")
    alt = f'<link rel="alternate" hreflang="{other}" href="../{other}/{page}.html"><link rel="alternate" hreflang="{lang}" href="{page}.html">'
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="dark light"><meta name="author" content="{AUTHORS}">{alt}
<link rel="stylesheet" href="../assets/css/site.css"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
</head><body>
<input type="checkbox" id="theme" class="theme-toggle" aria-label="{ui['theme']}">
<a class="skip" href="#main">{ui['skip']}</a>
<header class="topbar"><a class="brand" href="index.html"><svg width="22" height="22" viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="21" fill="none" stroke="currentColor" stroke-width="5"/><circle cx="48" cy="27" r="5" fill="currentColor"/></svg><span>{SITE_TITLE[lang]}</span></a>
<div class="tools"><label class="themebtn" for="theme" title="{ui['theme']}"><span class="i-sun" aria-hidden="true">☀</span><span class="i-moon" aria-hidden="true">☾</span><span class="sr">{ui['theme']}</span></label>
<a class="langbtn" href="../{other}/{page}.html" hreflang="{other}" lang="{other}">{ui['lang_other']}</a></div></header>
<details class="mtoc"><summary>{ui['menu']}</summary><nav aria-label="{ui['toc']}">{nav}{onpage_h}</nav></details>
<div class="layout"><nav class="sidenav" aria-label="{ui['toc']}"><p class="navh">{ui['toc']}</p>{nav}{onpage_h}</nav>
<main id="main" class="page">{content}{pn}</main></div>
<footer class="foot"><p>{esc(AUTHORS)} · {SITE_TITLE[lang]} · {ui['cutoff']}</p><p>{ui['license']} <a href="about.html">{ui['cite']}</a></p></footer>
<script src="../assets/js/enhance.js" defer></script>
</body></html>"""

def chapter_header(fm, lang):
    num = fm.get("num"); title = fm.get("title", "")
    if not num: return ""
    lead = fm.get("lead", "")
    lab = UI[lang]["chapter"] if str(num) != "12" else UI[lang]["chapter"]
    return (f'<header class="chapter-head"><p class="num">{lab} {num}</p><h1>{esc(title)}</h1>'
            + (f'<p class="chlead">{md_inline(lead, lang)}</p>' if lead else "") + '<div class="rule"></div></header>')

def chapter_map(lang):
    cards = []
    for p in PAGE_ORDER[1:]:
        r = read_page(lang, p)
        if not r or not p.startswith("ch") and p != "atlas": continue
        fm = r[0]
        cards.append(f'<li><a href="{p}.html"><span class="nn">{fm.get("num", "")}</span><b>{esc(fm.get("title", ""))}</b>'
                     + (f'<span class="cl">{md_inline(fm.get("lead", ""), lang)}</span>' if fm.get("lead") else "") + "</a></li>")
    head = "Главы" if lang == "ru" else "Chapters"
    return f'<section class="chmap"><h2 id="chapters">{head}</h2><ol>{"".join(cards)}</ol></section>'

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    # Downloadable scholarly candidate; paper/ is owned and built separately.
    # The parent replaces these copies with final paper bytes after integration.
    for name in ("swarm-dynamics.pdf", "swarm-dynamics-source.zip", "index.html"):
        source = os.path.join(ROOT, "paper", name)
        if os.path.isfile(source):
            os.makedirs(os.path.join(OUT, "paper"), exist_ok=True)
            shutil.copy2(source, os.path.join(OUT, "paper", name))
    # assets
    for sub in ("css", "js"):
        shutil.copytree(os.path.join(ASSETS, sub), os.path.join(OUT, "assets", sub))
    shutil.copy(os.path.join(ASSETS, "favicon.svg"), os.path.join(OUT, "assets", "favicon.svg"))
    from PIL import Image
    for sub in ("figures", "charts"):
        src = os.path.join(ASSETS, sub); dst = os.path.join(OUT, "assets", sub); os.makedirs(os.path.join(dst, "web"), exist_ok=True)
        for f in sorted(os.listdir(src)):
            if not f.lower().endswith(".png"): continue
            shutil.copy(os.path.join(src, f), os.path.join(dst, f))
            im = Image.open(os.path.join(src, f))
            if im.width > 1600:
                im2 = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
                im2.save(os.path.join(dst, "web", f), optimize=True)
    for lang in LANGS: collect_row_text(lang)
    # pre-pass to collect card leads for the atlas
    for lang in LANGS:
        for p in PAGE_ORDER:
            if p != "atlas": page_body(lang, p)
    built = []
    for lang in LANGS:
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        full_parts = []
        for p in PAGE_ORDER:
            FIG_COUNTER[0] = 0
            fm, res = page_body(lang, p)
            if fm is None: continue
            h, h2s = res
            head = chapter_header(fm, lang) if p not in ("index",) else ""
            if p not in ("index",) and not fm.get("num"):
                head = f'<header class="chapter-head"><h1>{esc(fm.get("title", p))}</h1><div class="rule"></div></header>'
            extra = chapter_map(lang) if p == "index" else ""
            if p == "index":
                h = h.replace('<section class="findings">', extra + '<section class="findings">', 1) if False else h + extra
            title = (SITE_TITLE[lang] if p == "index" else f'{fm.get("title", p)} — {SITE_TITLE[lang]}')
            doc = shell(lang, p, title, head + h, h2s, desc=re.sub(r"<[^>]+>", "", md_inline(fm.get("lead", "") or SITE_SUB[lang], lang)))
            open(os.path.join(OUT, lang, p + ".html"), "w", encoding="utf-8").write(doc); built.append(f"{lang}/{p}.html")
        # single page with everything expanded
        FIG_COUNTER[0] = 0; allh = []
        for p in PAGE_ORDER:
            if p in ("atlas", "sources"): continue
            fm, res = page_body(lang, p, single=True)
            if fm is None: continue
            h, _ = res
            head = chapter_header(fm, lang) if fm.get("num") else (f'<header class="chapter-head"><h1>{esc(fm.get("title", p))}</h1></header>' if p != "index" else "")
            allh.append(f'<section class="fullsec" id="p-{p}">{head}{h}</section>')
        doc = shell(lang, "full", f'{UI[lang]["full"]} — {SITE_TITLE[lang]}', "".join(allh), [], desc=SITE_SUB[lang])
        open(os.path.join(OUT, lang, "full.html"), "w", encoding="utf-8").write(doc); built.append(f"{lang}/full.html")
    # root chooser
    root = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{SITE_TITLE['en']} · {SITE_TITLE['ru']}</title><link rel="stylesheet" href="assets/css/site.css"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="en" href="en/index.html"><link rel="alternate" hreflang="ru" href="ru/index.html"></head>
<body class="root"><input type="checkbox" id="theme" class="theme-toggle" aria-label="Light theme"><main class="rootmain">
<svg width="54" height="54" viewBox="0 0 54 54" aria-hidden="true" class="ring"><circle cx="27" cy="27" r="21" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="48" cy="27" r="4" fill="currentColor"/></svg>
<h1>{SITE_TITLE['en']}</h1><p class="subtitle">{SITE_SUB['en']}</p><p class="byline">{AUTHORS}</p>
<p class="chooser"><a class="btn" href="en/index.html" hreflang="en">English</a> <a class="btn" href="ru/index.html" hreflang="ru" lang="ru">Русский</a></p>
<p class="rootnote" lang="ru">{SITE_TITLE['ru']}: {SITE_SUB['ru'].lower()}</p></main></body></html>"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(root)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(root.replace("<h1>", "<p>404</p><h1>"))
    return built

def check():
    errs = []
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith(".html"): continue
            p = os.path.join(dp, f); t = open(p, encoding="utf-8").read()
            ids = set(re.findall(r'\sid="([^"]+)"', t))
            for href in re.findall(r'(?:href|src)="([^"]+)"', t):
                if href.startswith(("http://", "https://", "mailto:", "data:")): continue
                target, _, frag = href.partition("#")
                if target:
                    tp = os.path.normpath(os.path.join(dp, target))
                    if not os.path.exists(tp): errs.append(f"{os.path.relpath(p, OUT)}: missing {href}"); continue
                    if frag and tp.endswith(".html"):
                        tt = open(tp, encoding="utf-8").read()
                        if f'id="{frag}"' not in tt: errs.append(f"{os.path.relpath(p, OUT)}: missing anchor {href}")
                elif frag and frag not in ids:
                    errs.append(f"{os.path.relpath(p, OUT)}: missing local anchor #{frag}")
    return errs

if __name__ == "__main__":
    built = build()
    print("built", len(built), "pages")
    if "--check" in sys.argv:
        e = check()
        for x in e[:80]: print("LINK", x)
        print("link errors:", len(e))
        sys.exit(1 if e else 0)

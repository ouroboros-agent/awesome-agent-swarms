#!/usr/bin/env python3
"""Build the static bilingual site: content/{ru,en}/*.md + data/*.json + assets/ -> site/.

  python scripts/build_site.py            # build site/
  python scripts/build_site.py --check    # build, then fail on broken internal links / missing images

Reading and navigation need no JavaScript: the theme switch, the contents sheet, card disclosure, the figure
lightbox (:target), the index scene's mode switch and the atlas filters (:has) are HTML and CSS.
assets/js/site.js adds the figure viewer, the remembered theme, section highlighting, atlas search and
expand-all; assets/js/story.js plays the index scene (scripts/site_story.py builds its markup).
"""
import html, json, os, re, shutil, sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import markdown  # pinned in requirements.txt
import site_story

CONTENT, DATA, ASSETS, OUT = (os.path.join(ROOT, d) for d in ("content", "data", "assets", "site"))
LANGS = ("ru", "en")
CHAPTERS = [f"ch{n:02d}" for n in range(1, 12)]
PAGE_ORDER = ["index"] + CHAPTERS + ["atlas", "glossary", "sources", "about"]
SITE_TITLE = {"ru": "Динамика роёв LLM-агентов", "en": "On the Dynamics of LLM Agent Swarms"}
SITE_SHORT = {"ru": "Динамика роёв", "en": "Swarm Dynamics"}
SITE_SUB = {"ru": "Масштабирование, координация и коллективное поведение", "en": "Scaling, Coordination, and Collective Behavior"}
AUTHORS = "Anton Razzhigaev, Ouroboros"
UI = {
 "ru": dict(toc="Содержание", on_page="На странице", chapter="Глава", of="из", details_full="Подробнее о работе",
            details_short="Подробнее", authors="Авторы", orgs="Организации", published="Опубликовано", status="Статус", source="Источник",
            prev="Назад", next="Далее", theme="Светлая тема", lang_other="English", lang_short="EN", lang_other_code="en", skip="К тексту",
            zoom="Открыть рисунок", close="Закрыть", original="оригинал", actual="Размер 100 % · прокрутка", scroll="⟷ таблицу можно прокрутить", all="Все",
            f_topic="Тема", f_evid="Класс доказательств", f_scale="Масштаб (одновременно)", f_type="Тип источника", f_level="Где в обзоре", f_chapter="Глава",
            atlas_hint="Фильтры работают и без JavaScript. Тема, класс доказательств и масштаб размечены для аналитического корпуса; у строк «Ещё по теме» тема — по главе, где они стоят, а класс и масштаб не размечены: такие строки видны при «Все».",
            in_ch="гл.", full="Весь текст на одной странице", license="Текст, таблицы и данные — CC BY 4.0, код сборки — MIT. Рисунки из работ остаются под правами их владельцев: условия — в подписи к каждому.",
            cite="Как цитировать", cutoff="срез 3 октября 2026", search="Поиск по атласу", shown="Показано", updates="Обновление после среза",
            menu="Содержание", fig="Рис.", expand="Развернуть все карточки", collapse="Свернуть карточки", home="Главное",
            cards_full=("подробная карточка", "подробные карточки", "подробных карточек"), cards_short=("краткая", "краткие", "кратких"),
            cards=("карточка", "карточки", "карточек"), figs=("рисунок", "рисунка", "рисунков"), minutes="≈{nb}{n}{nb}мин чтения",
            findings_eb="Выводы", findings_h="Что показывают работы", findings_note="Каждый вывод сформулирован для корпуса на 3 октября 2026 и ведёт в главу с доказательствами и условиями сравнения.",
            chapters_eb="Главы", chapters_h="Одиннадцать глав и атлас работ",
            start="Начать с главы 1", atlas="Атлас работ", atlas_s="Атлас", report="Технический отчёт", pdf="PDF", zip="LaTeX и рисунки (ZIP)", bib="BibTeX всех работ", data="Реестр работ (JSON)",
            materials="Материалы", survey="Обзор", rights="Права и цитирование", about_l="Об обзоре", glossary="Словарик", sources="Источники",
            n_corpus="работ в аналитическом корпусе", n_unique="уникальных работ и ресурсов", n_cards="карточек: {f} подробных и {s} кратких", n_figs="рисунков: {w} из работ, {o} собственных",
            filters="Фильтры", reset="Сбросить", empty="Под эти условия не подходит ни одна работа.", sources_ch="Источники главы", top="Наверх",
            atlas_eb="Атлас · {n} работ и ресурсов", ref_eb="Справка",
            idx=[("how", "Три схемы связи"), ("survey", "Об обзоре"), ("scale", "Масштаб"), ("findings", "Выводы"), ("agensh", "Разбор: Agensh"), ("chapters", "Главы")],
            v_close="Закрыть", v_prev="Предыдущий рисунок", v_next="Следующий рисунок", v_zoom="Увеличить", v_fit="Вписать", v_orig="Оригинал",
            v_title="Просмотр рисунков", v_hint="Двойной щелчок или касание — увеличить", v_count="{i} из {n}"),
 "en": dict(toc="Contents", on_page="On this page", chapter="Chapter", of="of", details_full="More about this work",
            details_short="More", authors="Authors", orgs="Organizations", published="Published", status="Status", source="Source",
            prev="Previous", next="Next", theme="Light theme", lang_other="Русский", lang_short="RU", lang_other_code="ru", skip="Skip to text",
            zoom="Open figure", close="Close", original="original", actual="Actual size · scroll to pan", scroll="⟷ scroll the table sideways", all="All",
            f_topic="Topic", f_evid="Evidence class", f_scale="Scale (simultaneous)", f_type="Source type", f_level="Where in the survey", f_chapter="Chapter",
            atlas_hint="The filters work without JavaScript too. Topic, evidence class and scale are labelled for the analytic corpus; related-work rows take the topic of the chapter they appear in and carry no class or scale, so they show under “All”.",
            in_ch="Ch.", full="Whole text on one page", license="Text, tables and data: CC BY 4.0; build code: MIT. Figures from the works keep their owners’ rights; the terms are under each figure.",
            cite="How to cite", cutoff="cut-off 3 October 2026", search="Search the atlas", shown="Shown", updates="Update after the cut-off",
            menu="Contents", fig="Fig.", expand="Expand all cards", collapse="Collapse cards", home="Overview",
            cards_full=("full card", "full cards"), cards_short=("short card", "short cards"), cards=("card", "cards"), figs=("figure", "figures"), minutes="≈{nb}{n}{nb}min read",
            findings_eb="Findings", findings_h="What the studies show", findings_note="Each finding is stated for the corpus as of 3 October 2026 and leads to the chapter with its evidence and comparison conditions.",
            chapters_eb="Chapters", chapters_h="Eleven chapters and an atlas of works",
            start="Start with Chapter 1", atlas="Atlas of works", atlas_s="Atlas", report="Technical report", pdf="PDF", zip="LaTeX and figures (ZIP)", bib="BibTeX for all works", data="Registry of works (JSON)",
            materials="Materials", survey="Survey", rights="Rights and citation", about_l="About the survey", glossary="Glossary", sources="Sources",
            n_corpus="works in the analytic corpus", n_unique="unique works and resources", n_cards="cards: {f} full and {s} short", n_figs="figures: {w} from the works, {o} our own",
            filters="Filters", reset="Reset", empty="No work matches these filters.", sources_ch="Sources for this chapter", top="Back to top",
            atlas_eb="Atlas · {n} works and resources", ref_eb="Reference",
            idx=[("how", "Three ways to connect"), ("survey", "About the survey"), ("scale", "Scale"), ("findings", "Findings"), ("agensh", "Case study: Agensh"), ("chapters", "Chapters")],
            v_close="Close", v_prev="Previous figure", v_next="Next figure", v_zoom="Zoom in", v_fit="Fit", v_orig="Original",
            v_title="Figure viewer", v_hint="Double-click or double-tap to zoom", v_count="{i} of {n}"),
}
NB = " "
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

# small inline icons (stroke = currentColor)
RING = ('<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="15" cy="16" r="9" fill="none" stroke="#22a876" stroke-width="3.4"/>'
        '<circle cx="24" cy="16" r="3.4" fill="#5fe3b3"/></svg>')
I_LIST = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>'
I_SUN = '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>'
I_MOON = '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
I_EXPAND = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>'
HEAD_JS = ("<script>(function(d){d.classList.add('js');try{if(localStorage.getItem('aas-theme')==='light')d.classList.add('light')}catch(e){}"
           "try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)d.classList.add('static')}catch(e){}})(document.documentElement)</script>")

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
LADDER = site_story.ladder(REG["works"])
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
    return s.replace(",", NB) if lang == "ru" else s

def plural(n, forms, lang):
    if lang == "en": return forms[0] if n == 1 else forms[1]
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11: return forms[0]
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14: return forms[1]
    return forms[2]

def fmt_date(s, lang, short=False):
    s = str(s or "")
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d{2}))?", s)
    if not m: return esc(s)
    y, mo, d = m.group(1), int(m.group(2)), m.group(3)
    if d and not short: return f"{int(d)} {MONTHS[lang][mo-1]} {y}"
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

def card_href(wid):
    pg, anc = work_anchor(wid)
    return f"{pg}.html#{anc}" if pg else f"atlas.html#a-{esc(wid)}"

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
    if lang == "ru": text = NBSP_NUM.sub(NB, text)
    text = SUP.sub(lambda m: f"<sup>{m.group(1) or m.group(2)}</sup>", text)
    MD.reset()
    return MD.convert(text)

def md_inline(text, lang):
    h = md(text, lang).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", h, flags=re.S)

def wrap_tables(h, lang):
    def rep(m):
        head = re.search(r"<tr>(.*?)</tr>", m.group(1), re.S)
        cols = len(re.findall(r"<th[\s>]", head.group(1))) if head else 0
        return (f'<div class="table-wrap" data-cols="{cols}" role="region" tabindex="0" aria-label="{esc(UI[lang]["scroll"])}"><table>{m.group(1)}</table></div>'
                f'<p class="scroll-hint" aria-hidden="true">{UI[lang]["scroll"]}</p>')
    return re.sub(r"<table>(.*?)</table>", rep, h, flags=re.S)

CHREF_RU = re.compile(r"(?<![\w-])(гл\.|главы|главе|главу|глава|главах|главам)(\s|&nbsp;| | )+(\d{1,2}(?:(?:\s*,\s*|\s+и\s+|\s*[–-]\s*)\d{1,2})*)")
CHREF_EN = re.compile(r"(?<![\w-])(Ch\.|Chs\.|Chapter|Chapters|ch\.)(\s|&nbsp;| | )+(\d{1,2}(?:(?:\s*,\s*|\s+and\s+|\s*[–-]\s*)\d{1,2})*)")
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
FIG = {"n": 0, "k": 0, "ch": None}   # n: unique id on the page; k: number within the chapter; ch: chapter number for labels
def chart_variants(f, lang):
    m = re.match(r"(dash_[a-z]+)_dark\.png$", f)
    if not m: return None
    base = m.group(1); out = {}
    for th in ("dark", "light"):
        cand = f"{base}_{lang}_{th}.png"
        if os.path.exists(os.path.join(ASSETS, "charts", cand)): out[th] = "charts/" + cand
    return out if len(out) == 2 else None

def strip_tags(h): return re.sub(r"<[^>]+>", "", h)

_DIMS = {}
def dims(rel_path):
    """width/height attributes for an image under site/assets, so lazy figures do not shift the text while they load."""
    if rel_path not in _DIMS:
        from PIL import Image
        p = os.path.join(OUT, "assets", rel_path)
        if not os.path.exists(p): p = os.path.join(ASSETS, rel_path.replace("/web/", "/"))
        try:
            with Image.open(p) as im: _DIMS[rel_path] = f' width="{im.width}" height="{im.height}"'
        except OSError:
            _DIMS[rel_path] = ""
    return _DIMS[rel_path]

def figure(spec, lang, rel):
    parts = [p.strip() for p in spec.split("|")]
    f = parts[0]; cap = parts[1] if len(parts) > 1 else ""; credit = parts[2] if len(parts) > 2 else ""
    FIG["n"] += 1; FIG["k"] += 1; n = FIG["n"]
    lab = f'{UI[lang]["fig"]}{NB}{FIG["ch"]}.{FIG["k"]}' if FIG["ch"] else f'{UI[lang]["fig"]}{NB}{FIG["k"]}'
    sub = "charts" if f.startswith("dash_") else "figures"
    var = chart_variants(f, lang)
    def src(p): return f"{rel}assets/{p}"
    capt = md_inline(cap, lang); cred = md_inline(credit, lang) if credit else ""
    alt = esc(strip_tags(capt)[:180])
    if var:
        imgs = (f'<img class="theme-dark-only" loading="lazy" decoding="async" src="{src(var["dark"])}"{dims(var["dark"])} alt="{alt}">'
                f'<img class="theme-light-only" loading="lazy" decoding="async" src="{src(var["light"])}"{dims(var["light"])} alt="{alt}">')
        big, big_light, frame, big_dims = src(var["dark"]), src(var["light"]), "frame chart", dims(var["dark"])
    else:
        web = f"{sub}/web/{f}" if os.path.exists(os.path.join(OUT, "assets", sub, "web", f)) else f"{sub}/{f}"
        imgs = f'<img loading="lazy" decoding="async" src="{src(web)}"{dims(web)} alt="{alt}">'
        big, big_light, frame, big_dims = src(f"{sub}/{f}"), "", ("frame dark" if f.startswith("dash_") else "frame"), dims(f"{sub}/{f}")
    dl = f' data-full-light="{big_light}"' if big_light else ""
    return (f'<figure class="fig" id="fig-{n}"><a class="zoom" href="#zoom-{n}" data-full="{big}"{dl} aria-label="{UI[lang]["zoom"]}: {esc(lab)}">'
            f'<div class="{frame}">{imgs}</div><span class="zi" aria-hidden="true">{I_EXPAND}</span></a>'
            f'<figcaption><span class="fnum">{lab}</span>{capt}' + (f'<span class="credit">{cred}</span>' if cred else "") +
            f' <a class="orig" href="{big}">{UI[lang]["original"]}</a></figcaption></figure>'
            f'<div class="lightbox" id="zoom-{n}" role="dialog" aria-label="{esc(lab)}"><a class="lb-close" href="#fig-{n}" aria-label="{UI[lang]["close"]}">×</a>'
            f'<div class="lb-tools"><span>{lab}</span><input type="checkbox" id="actual-{n}" class="lb-actual">'
            f'<label for="actual-{n}">{UI[lang]["actual"]}</label>'
            f'<a href="{big}" target="_blank" rel="noopener">{UI[lang]["original"]} ↗</a></div>'
            f'<div class="lb-img" tabindex="0" aria-label="{UI[lang]["zoom"]}"><img loading="lazy" src="{big}"{big_dims} alt="{alt}"></div></div>')

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

def byline(w, lang):
    """Organizations and month of the first public version, shown under the card title."""
    P = PASS.get(w["id"], {}); R = PASS_RU.get(w["id"], {})
    orgs = (R.get("institutions_short") or ", ".join(w.get("orgs") or [])) if lang == "ru" else (P.get("orgs_en") or lang_safe(", ".join(w.get("orgs") or []), lang))
    d = R.get("date_first_public") or w.get("date_first_public")
    bits = [esc(orgs)] if orgs else []
    if d and re.match(r"\d{4}-\d{2}", str(d)): bits.append(fmt_date(d, lang, short=True))
    return " · ".join(bits)

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
    # optional run-in labels («**Что сделали.**») start their own paragraph; flowing prose without labels renders as is
    text = re.sub(rf"(?<!\n\n)\s*(\*\*(?:{RUNIN[lang]})[^*]{{0,24}}\*\*)", lambda m: "\n\n" + m.group(1), text).strip()
    body_h = wrap_tables(md(text, lang), lang)
    body_h = re.sub(rf"<strong>((?:{RUNIN[lang]})[^<]{{0,24}})</strong>", r'<strong class="lab">\1</strong>', body_h)
    figs_h = "".join(figure(f.strip()[5:], lang, rel) for f in figs)
    u = (w.get("urls") or {}).get("primary"); title = esc(card_title(w, lang))
    tl = f'<a class="ext" href="{esc(u)}" rel="noopener">{title}</a>' if u else title
    full = kind == "card"; opn = " open" if single else ""
    by = byline(w, lang)
    head = (f'<header class="chead"><div class="tags">{tags(w, lang)}</div><h3 class="ctitle">{tl}</h3>'
            + (f'<p class="cmeta">{by}</p>' if by else "")
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

def cover_kv(body):
    kv = OrderedDict()
    for line in body.strip().split("\n"):
        k, _, v = line.partition(":"); kv[k.strip()] = v.strip()
    return kv

def render_intro(kv, lang):
    """The cover block of index.md, set as the section right under the scene: title, lede, counts, entry points."""
    ui = UI[lang]; st = STATS
    meta = [p.strip() for p in kv.get("meta", "").split(" · ") if p.strip() and "{{stat:" not in p]
    nums = [(fmt_int(st.get("corpus", 0), lang), ui["n_corpus"]), (fmt_int(st.get("unique_works", 0), lang), ui["n_unique"]),
            (fmt_int(st.get("cards_full", 0) + st.get("cards_short", 0), lang), ui["n_cards"].format(f=st.get("cards_full", 0), s=st.get("cards_short", 0))),
            (fmt_int(st.get("fig_works", 0) + st.get("fig_own", 0), lang), ui["n_figs"].format(w=st.get("fig_works", 0), o=st.get("fig_own", 0)))]
    return (f'<section class="intro" id="survey" aria-labelledby="h-survey"><div class="intro-in"><div>'
            f'<p class="eyebrow">{esc(kv.get("kicker", ""))}</p><h2 id="h-survey">{md_inline(kv.get("title", ""), lang)}</h2>'
            f'<p class="subtitle">{esc(kv.get("subtitle", ""))}</p><div class="lede">{md(kv.get("lede", ""), lang)}</div>'
            f'<p class="cta"><a class="btn primary" href="ch01.html">{ui["start"]} →</a><a class="btn" href="atlas.html">{ui["atlas"]}</a>'
            f'<a class="btn" href="../paper/index.html">{ui["report"]}</a></p></div>'
            '<dl class="numbers">' + "".join(f"<div><dt>{esc(l)}</dt><dd>{v}</dd></div>" for v, l in nums) + "</dl>"
            + ('<p class="meta">' + "".join(f"<span>{md_inline(p, lang)}</span>" for p in meta) + "</p>" if meta else "")
            + "</div></section>")

def findings_list(body, lang):
    """Numbered findings; each item is wrapped so the first bold sentence (if any) can be set as its headline."""
    return re.sub(r"<li>(.*?)</li>", lambda m: f'<li><div class="fb">{m.group(1)}</div></li>', md(body, lang), flags=re.S)

def render_cover_simple(kv, lang):
    return (f'<header class="chapter-head cover"><p class="eyebrow">{esc(kv.get("kicker", ""))}</p><h1>{md_inline(kv.get("title", ""), lang)}</h1>'
            f'<div class="chlead"><p>{esc(kv.get("subtitle", ""))}</p></div><p class="byline">{AUTHORS}</p></header>'
            f'<div class="lede">{md(kv.get("lede", ""), lang)}</div><p class="meta">{md_inline(kv.get("meta", ""), lang)}</p>')

def render_findings(body, lang):
    ui = UI[lang]
    h = findings_list(body, lang)
    return (f'<section class="sec findings" id="findings" aria-labelledby="h-findings"><header class="sec-head"><p class="eyebrow">{ui["findings_eb"]}</p>'
            f'<h2 id="h-findings">{ui["findings_h"]}</h2><p class="lede">{ui["findings_note"]}</p></header>{h}</section>')

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
    counts = defaultdict(lambda: defaultdict(int))
    def chapters_of(w):
        pg = [p for p in (w.get("source_pages") or []) if p.startswith("ch")]
        a = work_anchor(w["id"])[0]
        if a and a not in pg: pg.append(a)
        return sorted(set(pg))
    rows = []
    for w in WORKS.values():
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
        go = f'<a class="go" href="{pg}.html#{anc}">{ui["in_ch"]}{NB}{int(pg[2:]) if pg and pg.startswith("ch") else ""} →</a>' if pg else ""
        tg = ""
        if ev: tg += f'<span class="tag ev">{EVID[ev][i]}</span>'
        for t in topics[:3]: tg += f'<span class="tag t">{TOPIC[t][i]}</span>'
        sc = c.get("scale_note_ru") if lang == "ru" else PASS.get(w["id"], {}).get("scale_en")
        if sc: tg += f'<span class="tag sc">{esc(sc)}</span>'
        mods = ", ".join((c.get("models") or [])[:4]) + (f" +{len(c['models'])-4}" if len(c.get("models") or []) > 4 else "")
        ttl = esc(strip_tags(md_inline(title, lang)))
        rows.append((date or "0000", f'<li class="w" id="a-{esc(w["id"])}" data-t="{" ".join(filter_topics)}" data-e="{ev}" data-s="{sb}" data-k="{st}" data-l="{lvl}" data-c="{" ".join(chs)}">'
                    f'<div class="wd">{esc(date[5:7] + "." + date[:4] if len(date) >= 7 else date)}</div><div class="wm">'
                    f'<div class="wt">' + (f'<a class="ext" href="{esc(u)}" rel="noopener">{ttl}</a>' if u else esc(title)) + "</div>"
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
    return (f'<!--atlas-start--><style>{"".join(css)}</style><div class="atlas">'
            f'<div class="search js-only"><label><span class="sr">{ui["search"]}</span><input type="search" id="atlas-q" autocomplete="off" placeholder="{ui["search"]}"></label>'
            f'<span id="atlas-count" aria-live="polite"></span><button class="reset" type="button" id="atlas-reset">{ui["reset"]}</button></div>'
            f'<details class="fpanel" open><summary>{ui["filters"]}</summary><form class="filters" onsubmit="return false">{"".join(fs)}'
            f'<p class="hint">{ui["atlas_hint"]}</p></form></details><ol class="worklist">{"".join(r for _, r in rows)}</ol>'
            f'<p class="empty" id="atlas-empty">{ui["empty"]}</p></div><!--atlas-end-->')

def sources_by_page():
    by_page = OrderedDict()
    for w in WORKS.values():
        pg, _ = work_anchor(w["id"])
        if not pg and w["level"] == "inline_link": pg = (w.get("source_pages") or ["other"])[0]
        if not pg: continue
        by_page.setdefault(pg, []).append(w)
    return by_page

def render_sources(lang):
    by_page = sources_by_page()
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
        elif k == "findings": parts.append(f'<section class="findings">{findings_list(b[2], lang)}</section>')
        elif k == "related": parts.append(render_related(b[2], lang))
        elif k == "cover": parts.append(render_cover_simple(cover_kv(b[2]), lang) if single else render_intro(cover_kv(b[2]), lang))
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

def nav_title(lang, p):
    if p == "index": return UI[lang]["home"]
    if p == "full": return UI[lang]["full"]
    r = read_page(lang, p)
    return (r[0].get("nav") or r[0].get("title") or p) if r else p

def nav_list(lang, current, toc=None, href=None):
    """All pages; the current page carries its own sections underneath. href(p) overrides page links (single page)."""
    items = []
    for p in PAGE_ORDER + ["full"]:
        r = read_page(lang, p) if p != "full" else ({}, "")
        if not r: continue
        num = r[0].get("num") if p != "full" else None
        lab = f'<span class="nn">{num}</span>' if num and p.startswith("ch") else f'<span class="nn">{"≡" if p == "full" else "·"}</span>'
        cur = ' aria-current="page"' if p == current else ""
        sub = ""
        if p == current and toc:
            sub = '<ol class="onpage">' + "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in toc) + "</ol>"
        link = href(p) if href else f"{p}.html"
        items.append(f'<li><a href="{link}"{cur}>{lab}{esc(nav_title(lang, p))}</a>{sub}</li>')
    return '<ol class="navlist">' + "".join(items) + "</ol>"

def materials_links(lang):
    ui = UI[lang]
    return [("../paper/index.html", ui["report"]), ("../paper/swarm-dynamics.pdf", ui["pdf"]), ("../paper/swarm-dynamics-source.zip", ui["zip"]),
            ("../data/works.bib", ui["bib"]), ("../data/works.json", ui["data"])]

CITE_ANCHOR = {}
def footer(lang):
    ui = UI[lang]
    survey = [("index.html#findings", ui["findings_h"]), ("index.html#chapters", ui["chapters_eb"]), ("atlas.html", ui["atlas"]), ("glossary.html", ui["glossary"]),
              ("sources.html", ui["sources"]), ("full.html", ui["full"])]
    li = lambda xs: "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in xs)
    return (f'<footer class="foot"><div class="foot-in"><div><p class="fb-t">{RING}{SITE_TITLE[lang]}</p><p>{SITE_SUB[lang]}</p>'
            f'<p>{AUTHORS} · {ui["cutoff"]}</p></div>'
            f'<nav aria-label="{ui["survey"]}"><h2>{ui["survey"]}</h2><ul>{li(survey)}</ul></nav>'
            f'<nav aria-label="{ui["materials"]}"><h2>{ui["materials"]}</h2><ul>{li(materials_links(lang))}</ul></nav>'
            f'<div><h2>{ui["rights"]}</h2><p>{ui["license"]}</p><p><a href="about.html{CITE_ANCHOR.get(lang, "")}">{ui["cite"]}</a> · <a href="about.html">{ui["about_l"]}</a></p></div>'
            f'</div></footer>')

def viewer_i18n(lang):
    ui = UI[lang]
    return json.dumps({k: ui[k] for k in ("v_title", "v_close", "v_prev", "v_next", "v_zoom", "v_fit", "v_orig", "v_hint", "v_count", "expand", "collapse", "shown")}, ensure_ascii=False)

def shell(lang, page, title, content, toc=None, desc="", layout="doc", head_extra="", scripts=("site",), nav_href=None, link_page=None):
    """layout: 'doc' (sidebar + reading column), 'wide' (full-width container), 'index' (story sections)."""
    ui = UI[lang]; other = ui["lang_other_code"]; link_page = link_page or page
    nav = nav_list(lang, page, toc, nav_href)
    extra = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in materials_links(lang)[:3])
    mtoc = (f'<details class="mtoc"><summary title="{ui["toc"]}" aria-label="{ui["toc"]}">{I_LIST}<span class="lab">{ui["toc"]}</span></summary>'
            f'<nav aria-label="{ui["toc"]}">{nav}<div class="extra">{extra}</div></nav></details>')
    tnav = (f'<nav class="tnav" aria-label="{ui["survey"]}"><a href="index.html#findings">{ui["findings_eb"]}</a><a href="index.html#chapters">{ui["chapters_eb"]}</a>'
            f'<a href="atlas.html"{" aria-current=page" if page == "atlas" else ""}>{ui["atlas_s"]}</a><a href="../paper/swarm-dynamics.pdf">{ui["pdf"]}</a></nav>')
    top = (f'<header class="topbar"><div class="topbar-in"><a class="brand" href="index.html">{RING}<span class="bt">{SITE_TITLE[lang]}</span><span class="bt-s">{SITE_SHORT[lang]}</span></a>'
           f'{tnav}<div class="tools">{mtoc}<a class="langbtn" href="../{other}/{link_page}.html" hreflang="{other}" lang="{other}"><span class="long">{ui["lang_other"]}</span><span class="short">{ui["lang_short"]}</span></a>'
           f'<label class="themebtn" for="theme" title="{ui["theme"]}">{I_SUN}{I_MOON}<span class="sr">{ui["theme"]}</span></label></div>'
           + '</div>' + ('<span class="progress" aria-hidden="true"></span>' if layout == "doc" else "") + '</header>')
    if layout == "doc":
        body = (f'<div class="layout"><nav class="sidenav" aria-label="{ui["toc"]}"><p class="navh">{ui["toc"]}</p>{nav}</nav>'
                f'<main id="main" class="page p-{page}">{content}</main></div>')
    elif layout == "wide":
        body = f'<main id="main" class="wide-page p-{page}">{content}</main>'
    else:
        body = f'<main id="main" class="p-{page}">{content}</main>'
    alt = f'<link rel="alternate" hreflang="{other}" href="../{other}/{link_page}.html"><link rel="alternate" hreflang="{lang}" href="{link_page}.html">'
    js = "".join(f'<script src="../assets/js/{s}.js" defer></script>' for s in scripts)
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="dark light"><meta name="theme-color" content="#0a0c0d"><meta name="author" content="{AUTHORS}">{alt}
{HEAD_JS}
<link rel="stylesheet" href="../assets/css/site.css"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">{head_extra}
</head><body>
<input type="checkbox" id="theme" class="theme-toggle" aria-label="{ui['theme']}">
<a class="skip" href="#main">{ui['skip']}</a>
{top}
{body}
{footer(lang)}
<script type="application/json" id="ui-i18n">{viewer_i18n(lang)}</script>
{js}
</body></html>"""

def count_reading(h, lang):
    words = len(re.findall(r"\w+", strip_tags(re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S))))
    return max(5, int(round(words / (170 if lang == "ru" else 210) / 5.0)) * 5)

def chapter_header(fm, lang, page, h=""):
    ui = UI[lang]; num = fm.get("num"); title = fm.get("title", "")
    lead = fm.get("lead", "")
    if page.startswith("ch"):
        eb = f'{ui["chapter"]} {num} <span class="of">{ui["of"]} 11</span>'
    elif page == "atlas":
        eb = ui["atlas_eb"].format(n=fmt_int(STATS.get("unique_works", 0), lang))
    else:
        eb = ui["ref_eb"]
    meta = ""
    if page.startswith("ch") and h:
        nf, ns = h.count('<article class="card"'), h.count('<article class="card short"')
        nfig = h.count('<figure class="fig"')
        bits = []
        if nf: bits.append(f'{nf} {plural(nf, ui["cards_full"], lang)}')
        if ns: bits.append(f'{ns} {plural(ns, ui["cards_short"], lang)}')
        if nfig: bits.append(f'{nfig} {plural(nfig, ui["figs"], lang)}')
        bits.append(ui["minutes"].format(n=count_reading(h, lang), nb=NB))
        xall = f'<li class="js-only xli"><button class="xall" type="button" aria-pressed="false">{ui["expand"]}</button></li>' if (nf + ns) else ""
        meta = '<ul class="chmeta">' + "".join(f"<li>{b}</li>" for b in bits) + xall + "</ul>"
    return (f'<header class="chapter-head"><p class="eyebrow">{eb}</p><h1>{esc(title)}</h1>'
            + (f'<div class="chlead">{md_inline(lead, lang)}</div>' if lead else "") + meta + "</header>")

def pager(lang, page):
    ui = UI[lang]
    if page not in PAGE_ORDER: return ""
    idx = PAGE_ORDER.index(page)
    prev = PAGE_ORDER[idx - 1] if idx > 0 else None; nxt = PAGE_ORDER[idx + 1] if idx + 1 < len(PAGE_ORDER) else None
    def lab(p):
        r = read_page(lang, p); num = r[0].get("num") if r else None
        k = f'{ui["chapter"]} {num}' if num and p.startswith("ch") else (ui["home"] if p == "index" else "")
        return k
    out = '<nav class="pager" aria-label="pager">'
    out += (f'<a class="prev" href="{prev}.html"><span class="k">← {lab(prev) or ui["prev"]}</span><b>{esc(nav_title(lang, prev))}</b></a>' if prev else "<span></span>")
    if nxt: out += f'<a class="next" href="{nxt}.html"><span class="k">{lab(nxt) or ui["next"]} →</span><b>{esc(nav_title(lang, nxt))}</b></a>'
    return out + "</nav>"

def chapter_map(lang, counts):
    ui = UI[lang]; cards = []
    for p in CHAPTERS + ["atlas"]:
        r = read_page(lang, p)
        if not r: continue
        fm = r[0]
        if p == "atlas":
            cm = ui["atlas_eb"].split(" · ")[1].format(n=fmt_int(STATS.get("unique_works", 0), lang))
            cards.append(f'<li class="atl"><a href="atlas.html"><span class="nn">{fm.get("num", "")}</span><b>{esc(fm.get("title", ""))}</b>'
                         f'<span class="cl">{md_inline(fm.get("lead", ""), lang)}</span><span class="cm">{cm}</span></a></li>')
            continue
        nc, nfig = counts.get(p, (0, 0))
        cm = " · ".join(x for x in (f'{nc} {plural(nc, ui["cards"], lang)}' if nc else "", f'{nfig} {plural(nfig, ui["figs"], lang)}' if nfig else "") if x)
        cards.append(f'<li><a href="{p}.html"><span class="nn">{fm.get("num", "")}</span><b>{esc(fm.get("title", ""))}</b>'
                     + (f'<span class="cl">{strip_tags(md_inline(fm.get("lead", ""), lang))}</span>' if fm.get("lead") else "")
                     + (f'<span class="cm">{cm}</span>' if cm else "") + "</a></li>")
    return (f'<section class="sec chmap" id="chapters" aria-labelledby="h-chapters"><header class="sec-head"><p class="eyebrow">{ui["chapters_eb"]}</p>'
            f'<h2 id="h-chapters">{ui["chapters_h"]}</h2></header><ol>{"".join(cards)}</ol></section>')

def index_content(lang, counts):
    """index.md: cover -> intro, findings -> findings section, the rest -> «how to read»; the story sections come from site_story."""
    fm, text = read_page(lang, "index")
    intro, findings, rest = "", "", []
    for b in blocks(text):
        if b[0] == "cover": intro = render_intro(cover_kv(b[2]), lang)
        elif b[0] == "findings": findings = render_findings(b[2], lang)
        elif b[0] == "md": rest.append(wrap_tables(md(b[1], lang), lang))
        elif b[0] == "fig": rest.append(figure(b[1], lang, "../"))
        elif b[0] == "callout": rest.append(f'<aside class="callout"><p class="ctl">{esc(b[1])}</p>{md(b[2], lang)}</aside>')
        else: rest.append(md(b[2], lang))
    howto = "".join(rest).strip()
    howto = f'<section class="sec howto" id="howto">{howto}</section>' if howto else ""
    tail = intro + findings + howto
    n = [0]
    def hid(m):
        lvl, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if "id=" in attrs: return m.group(0)
        n[0] += 1; return f'<h{lvl} id="s-{n[0]}"{attrs}>{inner}</h{lvl}>'
    def finish(h): return link_chapters(rewrite_internal(re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", hid, h), lang), lang)
    intro, findings, howto = finish(intro), finish(findings), finish(howto)
    ch1 = read_page(lang, "ch01"); ch5 = read_page(lang, "ch05")
    ch1_title = ch1[0].get("title", "") if ch1 else ""; ch5_title = ch5[0].get("title", "") if ch5 else ""
    ch1_href = "ch01.html" + (f"#{H2_ANCHOR[lang]['ch01_scale']}" if H2_ANCHOR[lang].get("ch01_scale") else "")
    parts = [site_story.hero_html(lang, LADDER, card_href), intro, site_story.scale_html(lang, LADDER, card_href, ch1_title, ch1_href),
             findings, site_story.agensh_html(lang, card_href, ch5_title), chapter_map(lang, counts), howto]
    return fm, "\n".join(p for p in parts if p)

H2_ANCHOR = {"ru": {}, "en": {}}

def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    # Downloadable scholarly candidate; paper/ is owned and built separately.
    # The parent replaces these copies with final paper bytes after integration.
    for name in ("swarm-dynamics.pdf", "swarm-dynamics-source.zip", "index.html", "cite-this-report.bib"):
        source = os.path.join(ROOT, "paper", name)
        if os.path.isfile(source):
            os.makedirs(os.path.join(OUT, "paper"), exist_ok=True)
            shutil.copy2(source, os.path.join(OUT, "paper", name))
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    for src, name in (("data/works.json", "works.json"), ("data/bib/works.bib", "works.bib")):
        if os.path.isfile(os.path.join(ROOT, src)): shutil.copy2(os.path.join(ROOT, src), os.path.join(OUT, "data", name))
    # assets
    for sub in ("css", "js"):
        shutil.copytree(os.path.join(ASSETS, sub), os.path.join(OUT, "assets", sub))
    shutil.copy(os.path.join(ASSETS, "favicon.svg"), os.path.join(OUT, "assets", "favicon.svg"))
    site_story.write_illustrations()   # README posters and charts; the root page shows the poster too
    shutil.copytree(os.path.join(ASSETS, "illustrations"), os.path.join(OUT, "assets", "illustrations"))
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
    # pre-pass: card leads for the atlas, section anchors, per-chapter counts for the chapter map
    counts = {l: {} for l in LANGS}
    for lang in LANGS:
        for p in PAGE_ORDER:
            if p in ("atlas", "index"): continue
            FIG.update(n=0, k=0, ch=None)
            fm, res = page_body(lang, p)
            if fm is None: continue
            h, h2s = res
            counts[lang][p] = (h.count('<article class="card'), h.count('<figure class="fig"'))
            if p == "ch01":
                hit = next((a for a, t in h2s if re.search(r"агент|agent", t, re.I)), None)
                if hit: H2_ANCHOR[lang]["ch01_scale"] = hit
            if p == "about":
                hit = next((a for a, t in h2s if re.search(r"цитир|cite", t, re.I)), None)
                if hit: CITE_ANCHOR[lang] = "#" + hit
    built = []
    for lang in LANGS:
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        for p in PAGE_ORDER:
            FIG.update(n=0, k=0, ch=None)
            if p == "index":
                fm, h = index_content(lang, counts[lang])
                title = f'{SITE_TITLE[lang]}: {SITE_SUB[lang]}'
                doc = shell(lang, p, title, h, toc=UI[lang]["idx"], desc=strip_tags(md_inline(fm.get("lead", "") or SITE_SUB[lang], lang)),
                            layout="index", head_extra=f"<style>{site_story.mode_css()}</style>", scripts=("site", "story"))
                open(os.path.join(OUT, lang, "index.html"), "w", encoding="utf-8").write(doc); built.append(f"{lang}/index.html")
                continue
            r = read_page(lang, p)
            if r is None: continue
            num = r[0].get("num")
            FIG["ch"] = num if p.startswith("ch") else None
            fm, res = page_body(lang, p)
            h, h2s = res
            head = chapter_header(fm, lang, p, h)
            data_ch = f' data-ch style="--chn:\'{num}\'"' if p.startswith("ch") and num else ""
            if p == "atlas":
                a0, a1 = h.find("<!--atlas-start-->"), h.find("<!--atlas-end-->")
                intro_h, atlas_h, after_h = (h[:a0], h[a0:a1], h[a1 + 16:]) if a0 >= 0 and a1 > a0 else (h, "", "")
                content = (head + f'<div class="prose atlas-intro">{intro_h}</div>' + atlas_h
                           + (f'<div class="prose">{after_h}</div>' if after_h.strip() else "") + pager(lang, p))
                layout = "wide"
            else:
                tail = ""
                if p.startswith("ch"):
                    src = f'<a href="sources.html#src-{p}">{UI[lang]["sources_ch"]} →</a>' if p in sources_by_page() else ""
                    tail = f'<p class="chend">{src}<a href="#main">{UI[lang]["top"]} ↑</a></p>'
                content = head + f'<div class="prose"{data_ch}>{h}</div>' + tail + pager(lang, p)
                layout = "doc"
            title = f'{fm.get("title", p)} — {SITE_TITLE[lang]}'
            doc = shell(lang, p, title, content, toc=h2s, desc=strip_tags(md_inline(fm.get("lead", "") or SITE_SUB[lang], lang)), layout=layout)
            open(os.path.join(OUT, lang, p + ".html"), "w", encoding="utf-8").write(doc); built.append(f"{lang}/{p}.html")
        # single page with everything expanded
        FIG.update(n=0, k=0, ch=None); allh = []; toc = []
        for p in PAGE_ORDER:
            if p in ("atlas", "sources"): continue
            r = read_page(lang, p)
            if r is None: continue
            num = r[0].get("num")
            FIG.update(k=0, ch=num if p.startswith("ch") else None)
            fm, res = page_body(lang, p, single=True)
            h, _ = res
            if p == "index":
                head = ""
            else:
                head = chapter_header(fm, lang, p)
            data_ch = f' data-ch style="--chn:\'{num}\'"' if p.startswith("ch") and num else ""
            allh.append(f'<section class="fullsec" id="p-{p}">{head}<div class="prose"{data_ch}>{h}</div></section>')
            toc.append((f"p-{p}", (f"{num}. " if p.startswith("ch") else "") + nav_title(lang, p)))
        doc = shell(lang, "full", f'{UI[lang]["full"]} — {SITE_TITLE[lang]}', "".join(allh), toc=toc, desc=SITE_SUB[lang])
        open(os.path.join(OUT, lang, "full.html"), "w", encoding="utf-8").write(doc); built.append(f"{lang}/full.html")
    root = root_page()
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(root)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(root.replace('<main class="rootmain">', '<main class="rootmain"><p class="eyebrow">404</p>', 1))
    return built

def root_page():
    ui_en, ui_ru = UI["en"], UI["ru"]
    poster = ('<figure class="rootposter" aria-hidden="true">'
              '<img class="theme-dark-only" src="assets/illustrations/topologies-en-dark.svg" alt="" width="1600" height="900">'
              '<img class="theme-light-only" src="assets/illustrations/topologies-en-light.svg" alt="" width="1600" height="900"></figure>') \
        if os.path.isdir(os.path.join(ASSETS, "illustrations")) else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{SITE_TITLE['en']} · {SITE_TITLE['ru']}</title><meta name="description" content="{esc(SITE_SUB['en'])}. {AUTHORS}.">
<meta name="color-scheme" content="dark light"><meta name="theme-color" content="#0a0c0d">{HEAD_JS}
<link rel="stylesheet" href="assets/css/site.css"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="en" href="en/index.html"><link rel="alternate" hreflang="ru" href="ru/index.html"></head>
<body class="root"><main class="rootmain">
<header>{RING.replace('<svg ', '<svg class="ring" ', 1)}<h1>{SITE_TITLE['en']}</h1><p class="subtitle">{SITE_SUB['en']}</p><p class="byline">{AUTHORS} · {ui_en['cutoff']}</p></header>
<nav class="choose" aria-label="Language"><a href="en/index.html" hreflang="en" data-lang="en"><b>English</b><span>Eleven chapters, an atlas of works, the whole text on one page.</span></a>
<a href="ru/index.html" hreflang="ru" lang="ru" data-lang="ru"><b>Русский</b><span>{SITE_TITLE['ru']}: одиннадцать глав, атлас работ, весь текст на одной странице.</span></a></nav>
{poster}
</main><script>(function(){{try{{var l=(navigator.language||'').slice(0,2)==='ru'?'ru':'en';var a=document.querySelector('.choose a[data-lang="'+l+'"]');if(a)a.classList.add('pref');}}catch(e){{}}}})();</script></body></html>"""

def check():
    errs = []
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith(".html"): continue
            p = os.path.join(dp, f); t = open(p, encoding="utf-8").read()
            ids = set(re.findall(r'\sid="([^"]+)"', t))
            for href in re.findall(r'(?:href|src|data-full|data-full-light)="([^"]+)"', t):
                if href.startswith(("http://", "https://", "mailto:", "data:")): continue
                target, _, frag = href.partition("#")
                if target:
                    tp = os.path.normpath(os.path.join(dp, target))
                    if not tp.startswith(OUT): errs.append(f"{os.path.relpath(p, OUT)}: points outside site/: {href}"); continue
                    if not os.path.exists(tp): errs.append(f"{os.path.relpath(p, OUT)}: missing {href}"); continue
                    if frag and tp.endswith(".html"):
                        tt = open(tp, encoding="utf-8").read()
                        if f'id="{frag}"' not in tt: errs.append(f"{os.path.relpath(p, OUT)}: missing anchor {href}")
                elif frag and frag not in ids:
                    errs.append(f"{os.path.relpath(p, OUT)}: missing local anchor #{frag}")
            if re.search(r"\{\{|%%ATLAS%%|%%SOURCES%%", t): errs.append(f"{os.path.relpath(p, OUT)}: unfilled template mark")
    return errs

if __name__ == "__main__":
    built = build()
    print("built", len(built), "pages")
    if "--check" in sys.argv:
        e = check()
        for x in e[:80]: print("LINK", x)
        print("link errors:", len(e))
        sys.exit(1 if e else 0)

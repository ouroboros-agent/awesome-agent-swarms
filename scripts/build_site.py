#!/usr/bin/env python3
"""Build the static bilingual site: content/{ru,en}/*.md + data/*.json + assets/ -> site/.

  python scripts/build_site.py            # build site/
  python scripts/build_site.py --check    # build, then fail on broken links, missing images or duplicate ids

Since the Field edition of 12 November 2026, site/{ru,en}/index.html is the Field page (scripts/build_field.py, called at
the end of the build). This detailed survey stays whole at its dated address, site/{ru,en}/survey-2026-10-19.html
(longread.PAGE). Each language is one continuous page: the topology prologue, the survey's intro,
four parts with chapters 1–11, the findings, the atlas and the reference appendix (glossary, cards and
labels, sources, about). scripts/longread.py holds the order of parts and their bridge copy; scripts/scenes.py
and scripts/site_story.py build the native scenes. The former page addresses (ch01.html … full.html) stay as
small pages that forward every old fragment to its place on the survey page and, without JavaScript, list
those places as links.

Reading needs no JavaScript: the theme switch, the contents sheet, the figure lightbox (:target), the
prologue's scheme switch and the atlas filters (:has) are HTML and CSS, and every scene has a complete static
state. assets/js/site.js adds the remembered theme, progress and place-keeping, the figure viewer and atlas
search; assets/js/story.js plays the prologue and the Agensh scene; assets/js/scenes.js plays the others.
"""
import html, json, os, re, shutil, sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import markdown  # pinned in requirements.txt
import catalogue
import site_story
import longread
import scenes
import build_field
PAGE = longread.PAGE   # the detailed survey's page in site/<lang>/

CONTENT, DATA, ASSETS, OUT = (os.path.join(ROOT, d) for d in ("content", "data", "assets", "site"))
LANGS = ("ru", "en")
CHAPTERS = [f"ch{n:02d}" for n in range(1, 12)]
PAGE_ORDER = ["index"] + CHAPTERS + ["atlas", "glossary", "sources", "about"]
SITE_TITLE = {"ru": "Динамика роёв LLM-агентов", "en": "On the Dynamics of LLM Agent Swarms"}
SITE_SHORT = {"ru": "Динамика роёв", "en": "Swarm Dynamics"}
SITE_SUB = {"ru": "Масштабирование, координация и коллективное поведение", "en": "Scaling, Coordination, and Collective Behavior"}
AUTHORS = "Anton Razzhigaev, Ouroboros"
UI = {
 "ru": dict(toc="Содержание", chapter="Глава", of="из", authors="Авторы", orgs="Организации", published="Опубликовано", status="Статус", source="Источник",
            theme="Светлая тема", lang_other="English", lang_short="EN", lang_other_code="en", skip="К тексту",
            zoom="Открыть рисунок", close="Закрыть", original="оригинал", actual="Размер 100 % · прокрутка", scroll="⟷ таблицу можно прокрутить", all="Все",
            f_topic="Тема", f_evid="Класс доказательств", f_scale="Масштаб (одновременно)", f_type="Тип источника", f_level="Где в обзоре", f_chapter="Глава",
            atlas_hint="Фильтры работают и без JavaScript. Тема, класс доказательств и масштаб размечены для аналитического корпуса; у строк «Ещё по теме» тема — по главе, где они стоят, а класс и масштаб не размечены: такие строки видны при «Все».",
            in_ch="гл.", license="Текст, таблицы и данные — CC BY 4.0, код сборки — MIT. Рисунки из работ остаются под правами их владельцев: условия — в подписи к каждому.",
            cite="Как цитировать", cutoff="срез 3 октября 2026", edition="срез 3 октября 2026 · дополнение 19 октября 2026", search="Поиск по атласу", shown="Показано", updates="Обновление после среза",
            code="Код", in_survey="В обзоре", added_tag="добавлено 19 октября 2026", intro_h="О чём обзор",
            sup_note="Дополнение 19 октября 2026 года: {n} работ в главах 4–6, 9 и 10 и поправки к выводам о памяти роя (глава 6 и вопрос 4 главы 11).",
            fig="Рис.", pass_s="Авторы и источник", cards_full=("подробная карточка", "подробные карточки", "подробных карточек"), cards_short=("краткая", "краткие", "кратких"),
            figs=("рисунок", "рисунка", "рисунков"), scenes_n=("схема", "схемы", "схем"), minutes="≈{nb}{n}{nb}мин чтения",
            findings_h="Что показывают работы", findings_note="Каждый вывод сформулирован для корпуса на 3 октября 2026 и ведёт в главу с доказательствами и условиями сравнения; где работы дополнения 19 октября уточняют вывод, это сказано в нём отдельно.",
            report_d="Технический отчёт · 15 ноября", pdf="PDF · 15 ноября", zip="LaTeX и рисунки (ZIP) · 15 ноября", bib="BibTeX реестра · 3 октября", data="Реестр работ (JSON) · 3 октября",
            cat="Каталог с дополнением (JSON) · 19 октября", sup_bib="BibTeX каталога · 19 октября",
            materials="Материалы", survey="Обзор", rights="Права и цитирование", about_l="Об обзоре", glossary="Словарик", sources="Источники", atlas="Атлас работ",
            n_corpus="работ, по которым посчитаны графики обзора (на 3 октября)", n_unique="работ и ресурсов в каталоге (на 19 октября)", n_cards="карточек: {f} подробных и {s} кратких", n_figs="рисунков: {w} из работ, {o} собственных",
            filters="Фильтры", reset="Сбросить", empty="Под эти условия не подходит ни одна работа.", atlas_eb="Атлас · {n} работ и ресурсов",
            v_close="Закрыть", v_prev="Предыдущий рисунок", v_next="Следующий рисунок", v_zoom="Увеличить", v_fit="Вписать", v_orig="Оригинал",
            v_title="Просмотр рисунков", v_hint="Двойной щелчок или касание — увеличить", v_count="{i} из {n}", prologue="Пролог"),
 "en": dict(toc="Contents", chapter="Chapter", of="of", authors="Authors", orgs="Organizations", published="Published", status="Status", source="Source",
            theme="Light theme", lang_other="Русский", lang_short="RU", lang_other_code="ru", skip="Skip to text",
            zoom="Open figure", close="Close", original="original", actual="Actual size · scroll to pan", scroll="⟷ scroll the table sideways", all="All",
            f_topic="Topic", f_evid="Evidence class", f_scale="Scale (simultaneous)", f_type="Source type", f_level="Where in the survey", f_chapter="Chapter",
            atlas_hint="The filters work without JavaScript too. Topic, evidence class and scale are labelled for the analytic corpus; related-work rows take the topic of the chapter they appear in and carry no class or scale, so they show under “All”.",
            in_ch="Ch.", license="Text, tables and data: CC BY 4.0; build code: MIT. Figures from the works keep their owners’ rights; the terms are under each figure.",
            cite="How to cite", cutoff="cut-off 3 October 2026", edition="cut-off 3 October 2026 · supplement of 19 October 2026", search="Search the atlas", shown="Shown", updates="Update after the cut-off",
            code="Code", in_survey="In the survey", added_tag="added 19 October 2026", intro_h="What the survey covers",
            sup_note="Supplement of 19 October 2026: {n} works in Chapters 4–6, 9 and 10, and corrections to the conclusions on swarm memory (Chapter 6 and question 4 of Chapter 11).",
            fig="Fig.", pass_s="Authors and source", cards_full=("full card", "full cards"), cards_short=("short card", "short cards"),
            figs=("figure", "figures"), scenes_n=("scene", "scenes"), minutes="≈{nb}{n}{nb}min read",
            findings_h="What the studies show", findings_note="Each finding is stated for the corpus as of 3 October 2026 and leads to the chapter with its evidence and comparison conditions; where works of the 19 October supplement refine a finding, it says so separately.",
            report_d="Technical report · 15 November", pdf="PDF · 15 November", zip="LaTeX and figures (ZIP) · 15 November", bib="Registry BibTeX · 3 October", data="Registry of works (JSON) · 3 October",
            cat="Catalogue with the supplement (JSON) · 19 October", sup_bib="Catalogue BibTeX · 19 October",
            materials="Materials", survey="Survey", rights="Rights and citation", about_l="About the survey", glossary="Glossary", sources="Sources", atlas="Atlas of works",
            n_corpus="works behind the survey's charts (as of 3 October)", n_unique="works and resources in the catalogue (as of 19 October)", n_cards="cards: {f} full and {s} short", n_figs="figures: {w} from the works, {o} our own",
            filters="Filters", reset="Reset", empty="No work matches these filters.", atlas_eb="Atlas · {n} works and resources",
            v_close="Close", v_prev="Previous figure", v_next="Next figure", v_zoom="Zoom in", v_fit="Fit", v_orig="Original",
            v_title="Figure viewer", v_hint="Double-click or double-tap to zoom", v_count="{i} of {n}", prologue="Prologue"),
}
for _l in LANGS: UI[_l].update(longread.UI[_l])
NB = " "
MONTHS = {"ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
          "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
MONTHS_NOM = {"ru": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"],
              "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
DATED = re.compile(r"\b\d{1,2} (?:%s)" % "|".join(MONTHS["ru"] + MONTHS["en"]))
def keep_dates(s):
    """A label line of segments joined by « · » (the title screen's kicker and byline, the intro, the footer) breaks only
    between segments: inside a dated one («срез 3 октября 2026», "cut-off 3 October 2026") every space is non-breaking,
    so is the hyphen (U+2011), and the « ·» stays at the end of the line with the segment before it. The line still wraps."""
    return f"{NB}· ".join(x.replace(" ", NB).replace("-", "‑") if DATED.search(x) else x for x in s.split(" · "))

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
RING = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="3" y="2.5" width="10" height="27" rx="2" fill="none" stroke="currentColor" stroke-opacity=".45"/>'
        '<rect x="5.5" y="21" width="5" height="5" rx="1" fill="currentColor" fill-opacity=".55"/><rect x="5.5" y="14.5" width="5" height="5" rx="1" fill="#C8F542"/>'
        '<rect x="19" y="2.5" width="10" height="27" rx="2" fill="none" stroke="currentColor" stroke-opacity=".45"/>'
        '<rect x="21.5" y="21" width="5" height="5" rx="1" fill="currentColor" fill-opacity=".55"/><rect x="21.5" y="14.5" width="5" height="5" rx="1" fill="none" stroke="#C8F542" stroke-width="1.4"/></svg>')   # two context windows; a finding and its copy
I_LIST = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>'
I_MOTION = '<span class="mtg-i" aria-hidden="true"></span>'
I_SUN = '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>'
I_MOON = '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
I_EXPAND = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>'
HEAD_JS = ("<script>(function(d){d.classList.add('js');try{if(localStorage.getItem('aas-theme')==='light')d.classList.add('light')}catch(e){}"
           "try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)d.classList.add('static')}catch(e){}})(document.documentElement)</script>")

# ---------------------------------------------------------------- data
def jload(p, default=None):
    p = os.path.join(ROOT, p)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

REG = jload("data/works.json", {"works": [], "stats": {}, "text_url_map": {}})   # the registry as of 3 October 2026
# The atlas, cards and sources show the current catalogue (the registry plus the 19 October supplement, see
# scripts/catalogue.py); the analytic corpus behind the charts stays the registry's 153 works.
WORKS = OrderedDict((w["id"], w) for w in catalogue.works())
ALIAS = {a: w["id"] for w in WORKS.values() for a in (w.get("aliases") or [])}
STATS = dict(jload("data/stats.json", {}) or REG.get("stats", {}))
STATS.update(catalogue=len(WORKS), supplement_added=len(catalogue.SUP["added"]), supplement_updated=len(catalogue.SUP["updated"]),
             supplement_corrected=len(catalogue.SUP["corrected"]), supplement_new=catalogue.SUP.get("new_publications", 0))
SUP_DATE = catalogue.SUP["checked_at"]           # "2026-10-19"
PASS = jload("data/i18n/passports.json", {}) or {}
PASS_RU = jload("data/i18n/passports_ru.json", {}) or {}
FIGREG = {f["file"]: f for f in (jload("data/figures.json", {"figures": []})["figures"])}
LADDER = site_story.ladder(REG["works"])
from build_registry import key as url_key  # same normalization as the registry
URLKEY2ID = {}
for w in WORKS.values():
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
CARD_COUNT = {"card": 0, "short": 0}
for page in PAGE_ORDER:
    r = read_page("ru", page)
    if r:
        for b in blocks(r[1]):
            if b[0] in CARD_COUNT: CARD_COUNT[b[0]] += 1

def work_anchor(wid):
    wid = ALIAS.get(wid, wid)
    w = WORKS.get(wid) or {}
    if wid in CARD_PAGE: return CARD_PAGE[wid], "w-" + wid
    if w.get("part_of") and w["part_of"] in CARD_PAGE: return CARD_PAGE[w["part_of"]], "w-" + w["part_of"]
    if wid in ROW_PAGE: return ROW_PAGE[wid], "w-" + wid
    return None, None

def card_href(wid):
    """In-page link to a work: its card or related-work row, else its atlas row."""
    pg, anc = work_anchor(wid)
    return f"#{anc}" if pg else f"#a-{esc(wid)}"

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
def link_chapters(h, lang):
    """Chapter references in running text («гл. 4», "Chapters 3–10") become links to the chapter on the page."""
    rx = CHREF_RU if lang == "ru" else CHREF_EN
    parts = re.split(r"(<[^>]+>)", h); depth = 0; skip = 0; out = []
    for p in parts:
        if p.startswith("<"):
            if re.match(r"<a[\s>]", p): depth += 1
            elif p.startswith("</a"): depth = max(0, depth - 1)
            elif re.match(r"<(svg|script|style)[\s>]", p): skip += 1
            elif re.match(r"</(svg|script|style)>", p): skip = max(0, skip - 1)
            out.append(p); continue
        if depth or skip or not p: out.append(p); continue
        def rep(m):
            nums = re.sub(r"\d{1,2}", lambda n: (f'<a class="chref" href="#ch{int(n.group(0)):02d}">{n.group(0)}</a>'
                                                 if 1 <= int(n.group(0)) <= 11 else (f'<a class="chref" href="#atlas">12</a>' if n.group(0) == "12" else n.group(0))), m.group(3))
            return m.group(1) + m.group(2) + nums
        out.append(rx.sub(rep, p))
    return "".join(out)

PAGE_ANCHOR = {"index": "top", "atlas": "atlas", "glossary": "glossary", "sources": "sources", "about": "about", "full": "top"}
def rewrite_internal(h, lang):
    """Links written for the former pages point to places on the single page."""
    h = re.sub(r'href="#w-([\w-]+)"', lambda m: f'href="{card_href(m.group(1))}"', h)
    def page_link(m):
        page, frag = m.group(1), (m.group(2) or "")[1:]
        if not frag: return f'href="#{PAGE_ANCHOR.get(page, page)}"'
        if re.match(r"s-\d+$", frag) and page not in ("index",): return f'href="#{page}-{frag}"'
        return f'href="#{frag}"'
    h = re.sub(r'href="(ch\d\d|atlas|glossary|sources|about|index|full)\.html(#[^"]*)?"', page_link, h)
    h = re.sub(r'<a href="(https?://[^"]+)"', r'<a class="ext" href="\1" rel="noopener"', h)
    return h

# ---------------------------------------------------------------- figures
FIG = {"k": 0, "ch": None, "page": None, "list": []}   # k: number within the chapter; ch: chapter number for labels
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

def fig_label(lang):
    return f'{UI[lang]["fig"]}{NB}{FIG["ch"]}.{FIG["k"]}' if FIG["ch"] else f'{UI[lang]["fig"]}{NB}{FIG["k"]}'

def fig_ids():
    p = FIG["page"] or "x"
    return f"{p}-fig-{FIG['k']}", f"{p}-zoom-{FIG['k']}"

def figure(spec, lang, rel="../"):
    parts = [p.strip() for p in spec.split("|")]
    f = parts[0]; cap = parts[1] if len(parts) > 1 else ""; credit = parts[2] if len(parts) > 2 else ""
    FIG["k"] += 1
    lab = fig_label(lang); fid, zid = fig_ids()
    FIG["list"].append((fid, lab, f))
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
    return (f'<figure class="fig" id="{fid}"><a class="zoom" href="#{zid}" data-full="{big}"{dl} aria-label="{UI[lang]["zoom"]}: {esc(lab)}">'
            f'<div class="{frame}">{imgs}</div><span class="zi" aria-hidden="true">{I_EXPAND}</span></a>'
            f'<figcaption><span class="fnum">{lab}</span>{capt}' + (f'<span class="credit">{cred}</span>' if cred else "") +
            f' <a class="orig" href="{big}">{UI[lang]["original"]}</a></figcaption></figure>'
            f'<div class="lightbox" id="{zid}" role="dialog" aria-label="{esc(lab)}"><a class="lb-close" href="#{fid}" aria-label="{UI[lang]["close"]}">×</a>'
            f'<div class="lb-tools"><span>{lab}</span><input type="checkbox" id="{zid}-actual" class="lb-actual">'
            f'<label for="{zid}-actual">{UI[lang]["actual"]}</label>'
            f'<a href="{big}" target="_blank" rel="noopener">{UI[lang]["original"]} ↗</a></div>'
            f'<div class="lb-img" tabindex="0" aria-label="{UI[lang]["zoom"]}"><img loading="lazy" src="{big}"{big_dims} alt="{alt}"></div></div>')

def scene_figure(spec, name, lang):
    """A native scene that takes the place (number, caption, credit) of one of the survey's own charts."""
    parts = [p.strip() for p in spec.split("|")]
    f = parts[0]; cap = parts[1] if len(parts) > 1 else ""; credit = parts[2] if len(parts) > 2 else ""
    FIG["k"] += 1
    lab = fig_label(lang); fid, _ = fig_ids()
    FIG["list"].append((fid, lab, f))
    var = chart_variants(f, lang) or {}
    pngs = [(f"../assets/{var[t]}", UI[lang]["png_" + t]) for t in ("dark", "light") if t in var]
    ctx = dict(id=fid, label=lab, caption=md_inline(cap, lang), credit=md_inline(credit, lang) if credit else "", pngs=pngs, file=f)
    return scenes.html(name, lang, ctx)

# ---------------------------------------------------------------- cards
RUNIN = {"ru": r"Что сделали|Что получилось|Почему это важно|Оговорки|Что показали|Главное", "en": r"What they did|Results|Why it matters|Caveats|What it shows"}
def sup_pass(w, lang):
    """Display fields of a record changed by the 19 October supplement (empty for the others)."""
    return catalogue.passport(w["id"], lang)

def update_line(w, lang):
    """The last dated change of a record, in the page's language: the supplement's own phrasing for the records it
    changed, the registry's (with its Russian version) for the earlier one."""
    sp = sup_pass(w, lang)
    if sp.get("note") and catalogue.changed(w["id"]) in ("updated", "corrected"):
        up = w["updates"][-1]
        return fmt_date(up["date"] if catalogue.changed(w["id"]) == "updated" else SUP_DATE, lang), sp["note"], up["url"]
    if w.get("updates") and not catalogue.changed(w["id"]):
        up = w["updates"][-1]
        return fmt_date(up["date"], lang), (up["what"] if lang == "en" else ru_update(w["id"], up)), up.get("doi") and up["url"] or up["url"]
    return None

def passport(w, lang):
    P = PASS.get(w["id"], {}); R = PASS_RU.get(w["id"], {}); sp = sup_pass(w, lang)
    if lang == "ru":
        au = (authors_line(w, lang) if w.get("metadata_corrected") else None) or sp.get("authors") or R.get("authors") or authors_line(w, lang)
        orgs = sp.get("orgs") or R.get("institutions_short") or ", ".join(w.get("orgs") or [])
        st = sp.get("status") or P.get("status_ru") or R.get("venue_status") or ""
    else:
        au = (authors_line(w, lang) if w.get("metadata_corrected") else None) or sp.get("authors") or P.get("authors_en") or lang_safe(authors_line(w, lang), lang)
        orgs = sp.get("orgs") or P.get("orgs_en") or lang_safe(", ".join(w.get("orgs") or []), lang)
        st = sp.get("status") or P.get("status_en") or ""
    date = sp.get("date_note") or fmt_date(R.get("date_first_public") or w.get("date_first_public"), lang)
    rows = [(UI[lang]["authors"], esc(au)), (UI[lang]["orgs"], esc(orgs)), (UI[lang]["published"], esc(date)), (UI[lang]["status"], esc(st))]
    u = (w.get("urls") or {}).get("primary")
    if u:
        su = re.sub(r"^https?://(www\.)?", "", u); su = su if len(su) < 80 else su[:78] + "…"
        rows.append((UI[lang]["source"], f'<a class="ext url" href="{esc(u)}" rel="noopener">{esc(su)}</a>'))
    code = (w.get("urls") or {}).get("code")
    if code and catalogue.changed(w["id"]) == "added":
        rows.append((UI[lang]["code"], f'<a class="ext url" href="{esc(code)}" rel="noopener">{esc(re.sub(r"^https?://(www[.])?", "", code))}</a>'))
    if catalogue.changed(w["id"]) == "added":
        rows.append((UI[lang]["in_survey"], esc(sp.get("note") or "")))
    ul = update_line(w, lang)
    if ul:
        d, txt, url = ul
        rows.append((UI[lang]["updates"], f'{d}: {esc(txt)} <a class="ext url" href="{esc(url)}" rel="noopener">{esc(url)}</a>'))
    return '<dl class="passport">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v) + "</dl>"

def byline(w, lang):
    """Organizations and month of the first public version, shown under the card title."""
    P = PASS.get(w["id"], {}); R = PASS_RU.get(w["id"], {}); sp = sup_pass(w, lang)
    orgs = sp.get("orgs") or ((R.get("institutions_short") or ", ".join(w.get("orgs") or [])) if lang == "ru" else (P.get("orgs_en") or lang_safe(", ".join(w.get("orgs") or []), lang)))
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
    if catalogue.changed(w["id"]) == "added":   # outside the analytic corpus: no evidence class or topics, only what it is and when it came in
        sp = sup_pass(w, lang)
        out.append(f'<span class="tag new">{UI[lang]["added_tag"]}</span>')
        if sp.get("kind"): out.append(f'<span class="tag t">{esc(sp["kind"])}</span>')
        return "".join(out)
    if c.get("evidence") in EVID: out.append(f'<span class="tag ev">{EVID[c["evidence"]][i]}</span>')
    for t in (c.get("topics") or [])[:3]:
        if t in TOPIC: out.append(f'<span class="tag t">{TOPIC[t][i]}</span>')
    sc = c.get("scale_note_ru") if lang == "ru" else (PASS.get(w["id"], {}).get("scale_en"))
    if sc: out.append(f'<span class="tag sc">{esc(sc)}</span>')
    return "".join(out)

def card_title(w, lang):
    sp = sup_pass(w, lang)
    if sp.get("title"): return sp["title"]
    if lang == "ru": return PASS_RU.get(w["id"], {}).get("display_title") or PASS.get(w["id"], {}).get("title_en") or w.get("title") or w["id"]
    if w.get("metadata_corrected") and w.get("title"): return w["title"]
    return PASS.get(w["id"], {}).get("title_en") or lang_safe(w.get("title"), lang) or w["id"]

LEADS = {"ru": {}, "en": {}}
def render_card(kind, arg, body, lang):
    """A full card is a case study with its figures; a short card is an attributed note in the running text.
    Both keep the whole body visible; authors, status and the source link sit in a small disclosure."""
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
    figs_h = "".join(figure(f.strip()[5:], lang) for f in figs)
    u = (w.get("urls") or {}).get("primary"); title = esc(card_title(w, lang))
    tl = f'<a class="ext" href="{esc(u)}" rel="noopener">{title}</a>' if u else title
    by = byline(w, lang)
    new_attr = " data-new" if catalogue.changed(cid) == "added" else ""   # a card the 19 October supplement added: no former address
    pas = f'<details class="pass"><summary>{UI[lang]["pass_s"]}</summary>{passport(w, lang)}</details>'
    if kind == "card":
        head = (f'<header class="chead"><div class="tags">{tags(w, lang)}</div><h3 class="ctitle"{new_attr}>{tl}</h3>'
                + (f'<p class="cmeta">{by}</p>' if by else "") + (f'<p class="clead">{md_inline(lead, lang)}</p>' if lead else "") + "</header>")
        return f'<article class="case" id="w-{esc(cid)}">{head}<div class="cbody">{body_h}</div>{figs_h}{pas}</article>'
    head = (f'<header class="nhead"><h3 class="ctitle"{new_attr}>{tl}</h3>' + (f'<p class="cmeta">{by}</p>' if by else "")
            + f'<div class="tags">{tags(w, lang)}</div></header>')
    return (f'<section class="note" id="w-{esc(cid)}">{head}' + (f'<p class="nlead">{md_inline(lead, lang)}</p>' if lead else "")
            + f'<div class="cbody">{body_h}</div>{figs_h}{pas}</section>')

def _cap(s): return s[:1].upper() + s[1:] if s else s
scenes.bind(card_href=card_href, card_title=lambda w, lang: strip_tags(md_inline(card_title(w, lang), lang)),
            scale_note=lambda w, lang: ((w.get("corpus") or {}).get("scale_note_ru") if lang == "ru" else PASS.get(w["id"], {}).get("scale_en")) or "",
            evid=lambda e, lang: _cap(EVID[e][0 if lang == "ru" else 1]) if e in EVID else e,
            topic=lambda t, lang: _cap(TOPIC[t][0 if lang == "ru" else 1]) if t in TOPIC else t)

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

def render_related(body, lang, page):
    rows = [r for r in body.strip().split("\n") if r.strip().startswith("|")]
    if len(rows) < 3: return wrap_tables(md(body, lang), lang)
    head = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    items = []
    for r in rows[2:]:
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))]
        first = cells[0]; um = re.search(r"\((https?://[^)\s]+)\)", first)
        wid = URLKEY2ID.get(url_key(um.group(1))) if um else None
        own = wid and ROW_PAGE.get(wid) == page and work_anchor(wid)[1] == "w-" + wid
        aid = f' id="w-{esc(wid)}"' if own else ""
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

def findings_list(body, lang):
    """Numbered findings; each item is wrapped so the first bold sentence (if any) can be set as its headline."""
    return re.sub(r"<li>(.*?)</li>", lambda m: f'<li><div class="fb">{m.group(1)}</div></li>', md(body, lang), flags=re.S)

# ---------------------------------------------------------------- atlas
def scale_bucket(c):
    """The atlas facet "Scale (simultaneous)": only a stated simultaneous count has a bucket; a capacity or limit
    (Grok 4.20, Kimi, Orbit, Agent Swarms as Researchers) or a cumulative count is not one, as in the charts of Ch. 1."""
    n = c.get("agents_max_simultaneous")
    if c.get("scale_kind") != "simultaneous" or not isinstance(n, (int, float)): return "sna"
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

def atlas_level(w):
    if w["level"] in ("full_card", "short_card", "mention_in_corpus", "constituent") or w["id"] in CARD_PAGE: return "card"
    return "related" if w["level"] == "table_row" else "other"

def atlas_title(w, lang):
    c = w.get("corpus") or {}
    lvl = atlas_level(w)
    rt = ROW_TEXT[lang].get(w["id"])
    title = card_title(w, lang) if (w["id"] in CARD_PAGE or lvl == "card") else (rt[0] if rt else (lang_safe(w.get("title"), lang) or (w.get("urls") or {}).get("primary") or w["id"]))
    title = lang_safe(title, lang) if not re.match(r"https?://", str(title)) else ""
    return label_of(w["id"], lang) or title or LINK_TEXT[lang].get(w["id"]) or (w.get("urls") or {}).get("primary") or w["id"]

def render_atlas(lang):
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
        lvl = atlas_level(w)
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
        title = atlas_title(w, lang)
        summary = LEADS[lang].get(w["id"]) or (rt[2] if rt else "")
        who = sup_pass(w, lang).get("orgs") or (PASS.get(w["id"], {}).get("orgs_en") if lang == "en" else PASS_RU.get(w["id"], {}).get("institutions_short")) or (rt[1] if rt else lang_safe(", ".join(w.get("orgs") or []), lang))
        date = (c.get("month") or w.get("date_first_public") or "")[:7]
        u = (w.get("urls") or {}).get("primary") or ""
        pg, anc = work_anchor(w["id"])
        go = f'<a class="go" href="#{anc}">{ui["in_ch"]}{NB}{int(pg[2:]) if pg and pg.startswith("ch") else ""} →</a>' if pg else ""
        tg = f'<span class="tag new">{ui["added_tag"]}</span>' if catalogue.changed(w["id"]) == "added" else ""
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
    return (f'<!--atlas-start--><style>{"".join(css)}</style><div class="atlas">' + scenes.html("atlasmap", lang, {}) +
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
SOURCES_BY_PAGE = sources_by_page()

def render_sources(lang):
    out = []
    for page in PAGE_ORDER:
        ws = SOURCES_BY_PAGE.get(page)
        if not ws: continue
        fm, _ = read_page(lang, page) or ({}, "")
        num = fm.get("num")
        lab = (f'{UI[lang]["chapter"]} {num}. ' if page.startswith("ch") and num else "") + fm.get("title", page)
        out.append(f'<h2 id="src-{page}">{esc(lab)}</h2><ol class="srclist">')
        for w in ws:
            rt = ROW_TEXT[lang].get(w["id"]); u = (w.get("urls") or {}).get("primary")
            au = lang_safe((authors_line(w, lang) if w.get("metadata_corrected") else None) or sup_pass(w, lang).get("authors") or (PASS.get(w["id"], {}).get("authors_en") if lang == "en" else PASS_RU.get(w["id"], {}).get("authors")) or authors_line(w, lang), lang) \
                 or (strip_tags(md_inline(rt[1], lang)) if rt else "")
            title = card_title(w, lang) if w["id"] in CARD_PAGE or w["level"] in ("constituent", "mention_in_corpus") else (strip_tags(md_inline(rt[0], lang)) if rt else lang_safe(w.get("title"), lang))
            title = label_of(w["id"], lang) or lang_safe(title, lang) or LINK_TEXT[lang].get(w["id"], "")
            st = sup_pass(w, lang).get("status") or lang_safe((PASS.get(w["id"], {}).get("status_en") if lang == "en" else (PASS.get(w["id"], {}).get("status_ru") or PASS_RU.get(w["id"], {}).get("venue_status"))) or "", lang)
            date = fmt_date(w.get("date_first_public"), lang) if w.get("date_first_public") else ""
            bits = [esc(au) if au else "", f"<em>{esc(title)}</em>" if title else "", esc(st), date]
            line = ". ".join(b for b in bits if b)
            if u:
                su = re.sub(r"^https?://(www[.])?", "", u)
                line += f'. <a class="ext url" href="{esc(u)}" rel="noopener">{esc(su)}</a>'
            if catalogue.changed(w["id"]): line += f' <span class="upd">{esc(sup_pass(w, lang).get("note") or "")}</span>'   # the 19 October changes, dated in their own words
            elif w.get("updates"): line += f' <span class="upd">{UI[lang]["updates"]}: {esc(w["updates"][-1]["what"] if lang == "en" else ru_update(w["id"], w["updates"][-1]))}</span>'
            out.append(f'<li id="s-{esc(w["id"])}">{line}</li>')
        out.append("</ol>")
    return "".join(out)

# ---------------------------------------------------------------- one page: chapter bodies
ANCHORS = {l: defaultdict(list) for l in LANGS}    # page -> [(old fragment, new fragment, label)] for the former pages
HEADS = {l: defaultdict(list) for l in LANGS}      # page -> [(id, text)] of its section headings (h2 in the Markdown)
MOVED = {l: {} for l in LANGS}                     # page -> html of sections moved to the reference appendix
SCENE_N = {l: defaultdict(int) for l in LANGS}

def number_heads(h, page, lang):
    """Section ids keep the counter of the former page: every h2/h3 (card titles included) in document order.
    Headings the 19 October supplement added (a section heading marked {: .upd } in the Markdown, the title of an
    added card) had no former address: they take ids of their own (#chNN-u-K) and leave the old counter untouched."""
    n = [0]; u = [0]
    def hid(m):
        lvl, attrs, inner = m.group(1), m.group(2) or "", m.group(3)
        if "id=" in attrs: return m.group(0)
        if "data-new" in attrs or re.search(r'class="[^"]*\bupd\b', attrs):
            u[0] += 1; sid = f"{page}-u-{u[0]}"
            if lvl == "2": HEADS[lang][page].append((sid, strip_tags(inner).strip()))
            return f'<h{lvl} id="{sid}"{attrs}>{inner}</h{lvl}>'
        n[0] += 1; sid = f"{page}-s-{n[0]}"
        text = strip_tags(inner).strip()
        if lvl == "2": HEADS[lang][page].append((sid, text))
        ANCHORS[lang][page].append((f"s-{n[0]}", sid, text))
        return f'<h{lvl} id="{sid}"{attrs}>{inner}</h{lvl}>'
    return re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", hid, h)

def shift_heads(h):
    """On the single page a chapter title is h2, so the chapter's own headings move one level down."""
    h = re.sub(r"<(/?)h4([\s>])", r"<\1h5\2", h)
    h = re.sub(r"<(/?)h3([\s>])", r"<\1h4\2", h)
    return re.sub(r"<(/?)h2([\s>])", r"<\1h3\2", h)

def page_flow(lang, page):
    """Render one content page for the single page: blocks in order, scenes at their hooks, ids from the former page."""
    fm, text = read_page(lang, page)
    num = fm.get("num")
    FIG.update(k=0, ch=num if page.startswith("ch") else None, page=page)
    place = longread.PLACE.get(page, {})
    parts, scene_html = [], {}
    ncall = ntab = 0
    def put_scene(name):
        key = f"%%SCENE{len(scene_html)}%%"
        scene_html[key] = scenes.html(name, lang, {"page": page}); SCENE_N[lang][page] += 1
        parts.append(key)
    pin = None   # a pinned scene takes the text that follows it (up to the next section) as its companion column
    for b in blocks(text):
        k = b[0]
        if k == "md":
            h = wrap_tables(md(b[1], lang), lang)
            if pin is not None:
                cut = h.find("<h2")
                lead, h = (h, "") if cut < 0 else (h[:cut], h[cut:])
                n_li = [0]
                def tag_li(m):
                    n_li[0] += 1
                    return f'<li data-fm-col="{n_li[0]}">'
                lead = re.sub(r"<li>", tag_li, lead, count=4)
                parts[pin] = f'<div class="pin-pair">{parts[pin]}<div class="pin-text">{lead}</div></div>'
                pin = None
            def tab(m):
                nonlocal ntab
                ntab += 1
                name = place.get(f"table:{ntab}")
                if not name: return m.group(0)
                SCENE_N[lang][page] += 1
                return scenes.table(name, lang, m.group(0))
            parts.append(re.sub(r'<div class="table-wrap".*?</table></div>', tab, h, flags=re.S))
        elif k == "fig":
            f = b[1].split("|")[0].strip()
            name = place.get(f"fig:{f}")
            if name:
                SCENE_N[lang][page] += 1; parts.append(scene_figure(b[1], name, lang))
                if name in scenes.PINNED: pin = len(parts) - 1
            else: parts.append(figure(b[1], lang))
        elif k in ("card", "short"):
            cid = b[1].split()[0]
            if place.get(f"before:{cid}"): put_scene(place[f"before:{cid}"])
            parts.append(render_card(k, b[1], b[2], lang))
            ANCHORS[lang][page].append((f"w-{cid}", f"w-{cid}", strip_tags(card_title(WORKS.get(cid) or {"id": cid}, lang))))
            if place.get(f"after:{cid}"): put_scene(place[f"after:{cid}"])
        elif k == "callout":
            ncall += 1
            parts.append(f'<aside class="callout"><p class="ctl">{esc(b[1])}</p>{wrap_tables(md(b[2], lang), lang)}</aside>')
            if place.get(f"callout:{ncall}"): put_scene(place[f"callout:{ncall}"])
        elif k == "timeline": parts.append(render_timeline(b[2], lang))
        elif k == "takeaways": parts.append(f'<aside class="takeaways"><p class="ctl">{"Главное в главе" if lang == "ru" else "Takeaways"}</p>{md(b[2], lang)}</aside>')
        elif k == "related": parts.append(render_related(b[2], lang, page))
        elif k == "corpus": parts.append("%%ATLAS%%")
        elif k == "sources": parts.append("%%SOURCES%%")
        elif k in ("cover", "findings"): continue
        else: parts.append(md(b[2], lang))
    h = number_heads("\n".join(parts), page, lang)
    for key, v in scene_html.items(): h = h.replace(key, v)
    if "%%ATLAS%%" in h: h = h.replace("%%ATLAS%%", render_atlas(lang))
    if "%%SOURCES%%" in h: h = h.replace("%%SOURCES%%", render_sources(lang))
    for fid, lab, f in FIG["list"]:
        ANCHORS[lang][page].append((fid.split("-", 1)[1], fid, lab))
        ANCHORS[lang][page].append(("zoom-" + fid.rsplit("-", 1)[1], fid, None))
    FIG["list"] = []
    # sections that leave the reading flow (kept whole, with their ids)
    for title in longread.MOVE_TO_HOWTO.get(page, []):
        m = re.search(rf'<h2 id="[^"]+">{re.escape(title)}</h2>', h)
        if not m: continue
        nxt = re.search(r"<h2 id=", h[m.end():])
        end = m.end() + nxt.start() if nxt else len(h)
        MOVED[lang][page] = h[m.start():end]; h = h[:m.start()] + h[end:]
        HEADS[lang][page] = [x for x in HEADS[lang][page] if x[1] != title]
    h = link_chapters(rewrite_internal(h, lang), lang)
    return fm, shift_heads(h)

# ---------------------------------------------------------------- one page: frame
def materials_links(lang):
    ui = UI[lang]
    return [("../paper/index.html", ui["report_d"]), ("../paper/swarm-dynamics.pdf", ui["pdf"]), ("../paper/swarm-dynamics-source.zip", ui["zip"]),
            ("../data/catalogue-2026-10-19.json", ui["cat"]), ("../data/references-2026-10-19.bib", ui["sup_bib"]),
            ("../data/works.bib", ui["bib"]), ("../data/works.json", ui["data"])]

CITE_ANCHOR = {}
def footer(lang):
    ui = UI[lang]
    survey = [("#findings", ui["findings_h"]), ("#chapters", ui["contents"]), ("#atlas", ui["atlas"]), ("#glossary", ui["glossary"]),
              ("#sources", ui["sources"]), ("#about", ui["about_l"])]
    li = lambda xs: "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in xs)
    byline = keep_dates(f'{AUTHORS} · {ui["edition"]}')
    return (f'<footer class="foot"><div class="foot-in"><div><p class="fb-t">{RING}<span>{SITE_SHORT[lang]}</span></p><p class="fb-s">{SITE_TITLE[lang]}. {SITE_SUB[lang]}</p>'
            f'<p>{byline}</p></div>'
            f'<nav aria-label="{ui["survey"]}"><h2>{ui["survey"]}</h2><ul>{li(survey)}</ul></nav>'
            f'<nav aria-label="{ui["materials"]}"><h2>{ui["materials"]}</h2><ul>{li(materials_links(lang))}</ul></nav>'
            f'<div><h2>{ui["rights"]}</h2><p>{ui["license"]}</p><p><a href="{CITE_ANCHOR.get(lang, "#about")}">{ui["cite"]}</a> · <a href="#about">{ui["about_l"]}</a></p></div>'
            f'</div></footer>')

def viewer_i18n(lang):
    ui = UI[lang]
    keys = ("v_title", "v_close", "v_prev", "v_next", "v_zoom", "v_fit", "v_orig", "v_hint", "v_count", "shown", "here_top", "pause", "play", "replay")
    return json.dumps({k: ui[k] for k in keys}, ensure_ascii=False)

def nav_title(lang, p):
    if p == "findings": return UI[lang]["findings_h"]
    if p == "howto": return UI[lang]["howto_t"]
    r = read_page(lang, p)
    return (r[0].get("nav") or r[0].get("title") or p) if r else p

def num_of(lang, p):
    r = read_page(lang, p)
    return (r[0].get("num") if r else None) or ""

def part_label(lang, part):
    return f'{UI[lang]["part"]} {part["key"]}' if part["key"] else UI[lang]["epilogue"]

def outline(lang):
    """The contents sheet: prologue, the four parts with their chapters and sections, the reference appendix."""
    ui = UI[lang]
    def sec_list(p):
        hs = HEADS[lang].get(p) or []
        return ('<ol class="secs">' + "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in hs) + "</ol>") if hs else ""
    def item(p):
        n = num_of(lang, p) if p.startswith("ch") or p == "atlas" else ""
        lab = f'<span class="nn">{n or "·"}</span>'
        anchor = "findings" if p == "findings" else p
        return f'<li data-k="{anchor}"><a href="#{anchor}">{lab}{esc(nav_title(lang, p))}</a>{sec_list(p)}</li>'
    out = [f'<ol class="outline"><li class="og"><p class="ogt">{ui["prologue"]}</p><ol>'
           f'<li data-k="how"><a href="#how"><span class="nn">·</span>{esc(site_story.T[lang]["stage_t"])}</a></li>'
           f'<li data-k="survey"><a href="#survey"><span class="nn">·</span>{esc(SITE_TITLE[lang])}</a></li></ol></li>']
    for part in longread.PARTS:
        out.append(f'<li class="og"><p class="ogt">{esc(part_label(lang, part))} · {esc(part["title"][lang])}</p><ol>' + "".join(item(p) for p in part["pages"]) + "</ol></li>")
    out.append(f'<li class="og"><p class="ogt">{ui["appendix"]}</p><ol>' + "".join(item(p) for p in longread.REFERENCE) + "</ol></li></ol>")
    return "".join(out)

def rail(lang):
    """Wide screens: a column of small context windows at the left edge, one per chapter; read chapters fill with blocks."""
    items = []
    for p in CHAPTERS + ["atlas"]:
        n = num_of(lang, p)
        items.append(f'<li><a href="#{p}" data-k="{p}"><i aria-hidden="true"><b></b><b></b><b></b></i><span class="rt"><b>{n}</b> {esc(nav_title(lang, p))}</span></a></li>')
    return f'<nav class="rail" aria-label="{UI[lang]["toc"]}"><ol>{"".join(items)}</ol></nav>'

def shell(lang, title, content, desc=""):
    ui = UI[lang]; other = ui["lang_other_code"]
    extra = "".join(f'<a href="{h}">{esc(t)}</a>' for h, t in materials_links(lang)[:3])
    mtoc = (f'<details class="mtoc"><summary title="{ui["toc"]}" aria-label="{ui["toc"]}">{I_LIST}<span class="lab">{ui["toc"]}</span></summary>'
            f'<nav aria-label="{ui["toc"]}">{outline(lang)}<div class="extra">{extra}</div></nav></details>')
    motion = (f'<button class="mtg js-only" type="button" aria-pressed="false" data-off="{esc(ui["motion_off"])}" data-on="{esc(ui["motion_on"])}" data-sys="{esc(ui["motion_sys"])}">'
              f'{I_MOTION}<span class="lab">{esc(ui["motion_off"])}</span></button>')
    top = (f'<header class="topbar"><div class="topbar-in"><a class="brand" href="#top">{RING}<span class="bt">{SITE_SHORT[lang]}</span><span class="bt-s">{SITE_SHORT[lang]}</span></a>'
           f'<a class="here" href="#chapters" tabindex="-1" aria-hidden="true"><span class="here-n"></span><span class="here-t"></span></a>'
           f'<div class="tools">{motion}{mtoc}<a class="langbtn" href="../{other}/{PAGE}" hreflang="{other}" lang="{other}"><span class="long">{ui["lang_other"]}</span><span class="short">{ui["lang_short"]}</span></a>'
           f'<span class="themesw"><input type="checkbox" id="theme" class="theme-toggle" aria-label="{ui["theme"]}">'
           f'<label class="themebtn" for="theme" title="{ui["theme"]}">{I_SUN}{I_MOON}<span class="sr">{ui["theme"]}</span></label></span></div>'
           '</div><span class="progress" aria-hidden="true"></span></header>')
    alt = f'<link rel="alternate" hreflang="{other}" href="../{other}/{PAGE}"><link rel="alternate" hreflang="{lang}" href="{PAGE}">'
    js = "".join(f'<script src="../assets/js/{s}.js" defer></script>' for s in ("site", "story", "scenes"))
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="dark light"><meta name="theme-color" content="#050507"><meta name="author" content="{AUTHORS}">{alt}
{HEAD_JS}
<link rel="stylesheet" href="../assets/css/site.css"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
<style>{site_story.state_css()}</style>
</head><body id="top">
<a class="skip" href="#main">{ui['skip']}</a>
{top}
{rail(lang)}
<main id="main" class="lr">{content}</main>
{footer(lang)}
<script type="application/json" id="ui-i18n">{viewer_i18n(lang)}</script>
{js}
</body></html>"""

def count_reading(h, lang):
    words = len(re.findall(r"\w+", strip_tags(re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", h, flags=re.S))))
    return max(5, int(round(words / (170 if lang == "ru" else 210) / 5.0)) * 5)

def split_lead(lead):
    """«Question? Answer.» -> (question, answer); a lead without a leading question stays whole."""
    m = re.match(r"^([^.!?]{8,220}\?)\s+(.*)$", lead.strip(), re.S)
    return (m.group(1), m.group(2)) if m else ("", lead)

def chapter_meta(lang, h, page):
    ui = UI[lang]
    nf, ns = h.count('<article class="case"'), h.count('<section class="note"')
    nchart = len(re.findall(r'class="scene sc-\w+ sc-fig"', h))          # the survey's own charts, now native, keep their figure numbers
    nfig = h.count('<figure class="fig"') + nchart
    nsc = SCENE_N[lang].get(page, 0) - nchart
    bits = []
    if nf: bits.append(f'{nf} {plural(nf, ui["cards_full"], lang)}')
    if ns: bits.append(f'{ns} {plural(ns, ui["cards_short"], lang)}')
    if nfig: bits.append(f'{nfig} {plural(nfig, ui["figs"], lang)}')
    if nsc: bits.append(f'{nsc} {plural(nsc, ui["scenes_n"], lang)}')
    if page != "atlas":     # the atlas is a table to search, not a text to read through
        bits.append(ui["minutes"].format(n=count_reading(h, lang), nb=NB))
    return ('<ul class="plate-meta">' + "".join(f"<li>{b}</li>" for b in bits) + "</ul>") if bits else ""

def plate(lang, page, fm, h, part, kicker=None, numeral=None):
    ui = UI[lang]; num = fm.get("num")
    q, a = split_lead(fm.get("lead", ""))
    if kicker is None:
        kicker = f'{ui["chapter"]} {num} <span class="of">{ui["of"]} 11</span>' if page.startswith("ch") else ui["atlas_eb"].format(n=fmt_int(STATS.get("catalogue", 0), lang))
    numeral = numeral if numeral is not None else (f"{int(num):02d}" if num else "")
    pk = f'<span class="pk-part">{esc(part_label(lang, part))} · {esc(part["title"][lang])}</span>' if part else ""
    return (f'<header class="plate" data-sl><div class="plate-bg" aria-hidden="true"></div><div class="plate-in" data-sl>'
            + (f'<span class="plate-num" aria-hidden="true">{numeral}</span>' if numeral else "")
            + f'<p class="plate-k"><span class="pk-ch">{kicker}</span>{pk}</p>'
            + f'<h2 class="plate-t" id="{page}-t">{esc(fm.get("title", ""))}</h2>'
            + (f'<p class="plate-q">{md_inline(q, lang)}</p>' if q else "")
            + (f'<p class="plate-a">{link_chapters(md_inline(a, lang), lang)}</p>' if a else "")
            + chapter_meta(lang, h, page) + "</div></header>")

def words(text):
    """Bridge statements are set word by word so the reading highlight can follow the scroll."""
    ws = text.split()
    return f'<p class="part-say" style="--n:{len(ws)}">' + " ".join(f'<span class="sw" style="--i:{i}">{esc(w)}</span>' for i, w in enumerate(ws)) + "</p>"

CH_CARDS = {}
for _p in CHAPTERS:
    _r = read_page("ru", _p)
    _bl = [x for x in blocks(_r[1]) if x[0] in ("card", "short")] if _r else []
    CH_CARDS[_p] = dict(full=sum(1 for x in _bl if x[0] == "card" and catalogue.changed(x[1].split()[0]) != "added"),
                        short=sum(1 for x in _bl if x[0] == "short" and catalogue.changed(x[1].split()[0]) != "added"),
                        added=sum(1 for x in _bl if catalogue.changed(x[1].split()[0]) == "added"))

def part_towers(lang, part):
    """Each chapter of the part as a context window; one block per card: full, short, and those the 19 October supplement added."""
    chs = [p for p in part["pages"] if p.startswith("ch")]
    if sum(1 for p in chs if sum(CH_CARDS[p].values())) < 2: return ""
    ui = UI[lang]; cols = []
    for p in chs:
        c = CH_CARDS[p]
        bl = ['<b class="f"></b>'] * c["full"] + ['<b class="s"></b>'] * c["short"] + ['<b class="a"></b>'] * c["added"]
        lab = ui["towers_note"].format(f=c["full"], s=c["short"] + c["added"]) if bl else ui["towers_none"]
        cols.append(f'<li><a href="#{p}" aria-label="{esc(ui["chapter"])} {int(p[2:])}: {esc(lab)}"><span class="tw" style="--n:{len(bl)}">{"".join(bl)}</span>'
                    f'<span class="tw-n">{int(p[2:])}</span><span class="tw-c">{len(bl)}</span></a></li>')
    key = (f'<p class="tw-key"><span>{esc(ui["towers_k"])}</span><i class="f"></i>{esc(ui["towers_full"])}<i class="s"></i>{esc(ui["towers_short"])}'
           f'<i class="a"></i>{esc(ui["added_tag"])}</p>')
    return f'<div class="part-tw"><ol class="tws">{"".join(cols)}</ol>{key}</div>'

def part_opener(lang, part):
    ui = UI[lang]
    lis = []
    for p in part["pages"]:
        n = num_of(lang, p) if (p.startswith("ch") or p == "atlas") else ""
        anchor = "findings" if p == "findings" else p
        lis.append(f'<li><a href="#{anchor}"><b>{n or "·"}</b>{esc(nav_title(lang, p))}</a></li>')
    num = f'<span class="part-num" aria-hidden="true">{part["key"] or "∴"}</span>'
    return (f'<section class="part tone-{part["tone"]}" id="{part["id"]}" aria-labelledby="{part["id"]}-t" data-sl>'
            f'<div class="part-bg" aria-hidden="true"></div><div class="part-in">{num}<p class="part-k">{esc(part_label(lang, part))}</p>'
            f'<h2 class="part-t" id="{part["id"]}-t">{esc(part["title"][lang])}</h2>{words(part["say"][lang])}'
            f'{part_towers(lang, part)}<ol class="part-ch">{"".join(lis)}</ol></div></section>')

def chapter_section(lang, page, part):
    fm, h = page_flow(lang, page)
    num = fm.get("num")
    tail = ""
    if page.startswith("ch"):
        src = f'<a href="#src-{page}">{UI[lang]["src_ch"]} →</a>' if page in SOURCES_BY_PAGE else ""
        tail = f'<p class="chend">{src}<a href="#top">{UI[lang]["top"]} ↑</a></p>'
    data_ch = f' data-ch style="--chn:\'{num}\'"' if page.startswith("ch") and num else ""
    if page == "atlas":
        a0, a1 = h.find("<!--atlas-start-->"), h.find("<!--atlas-end-->")
        intro_h, atlas_h, after_h = (h[:a0], h[a0:a1], h[a1 + 16:]) if a0 >= 0 and a1 > a0 else (h, "", "")
        body = f'<div class="flow prose atlas-intro">{intro_h}</div><div class="flow wide">{atlas_h}</div>' + (f'<div class="flow prose">{after_h}</div>' if after_h.strip() else "")
    else:
        body = f'<div class="flow prose"{data_ch}>{h}</div>{tail}'
    return (f'<section class="chapter tone-{part["tone"]}" id="{page}" data-k="{page}" aria-labelledby="{page}-t">'
            f'{plate(lang, page, fm, h, part)}<div class="sheet">{body}</div></section>')

def cover(lang):
    fm, text = read_page(lang, "index")
    return next((cover_kv(b[2]) for b in blocks(text) if b[0] == "cover"), {})

def intro_section(lang):
    """The cover block of index.md, set right after the prologue: what the survey covers, its counts (each with its
    date), the 19 October supplement, and the route through the parts."""
    ui = UI[lang]; st = STATS
    kv = cover(lang)
    meta = [p.strip() for p in kv.get("meta", "").split(" · ") if p.strip() and "{{stat:" not in p]
    cf, cs = CARD_COUNT["card"], CARD_COUNT["short"]      # the cards on the page now (the registry's 3 October counts are on the About page)
    nums = [(fmt_int(st.get("corpus", 0), lang), ui["n_corpus"]), (fmt_int(st.get("catalogue", 0), lang), ui["n_unique"]),
            (fmt_int(cf + cs, lang), ui["n_cards"].format(f=cf, s=cs)),
            (fmt_int(st.get("fig_works", 0) + st.get("fig_own", 0), lang), ui["n_figs"].format(w=st.get("fig_works", 0), o=st.get("fig_own", 0)))]
    parts = []
    for part in longread.PARTS:
        lis = []
        for p in part["pages"]:
            n = num_of(lang, p) if (p.startswith("ch") or p == "atlas") else ""
            anchor = "findings" if p == "findings" else p
            lis.append(f'<li><a href="#{anchor}"><span class="nn">{n or "·"}</span>{esc(nav_title(lang, p))}</a></li>')
        parts.append(f'<li class="rp tone-{part["tone"]}"><a class="rp-h" href="#{part["id"]}"><span class="rp-k">{esc(part_label(lang, part))}</span>'
                     f'<span class="rp-t">{esc(part["title"][lang])}</span></a><ol>{"".join(lis)}</ol></li>')
    ref = " · ".join(f'<a href="#{p}">{esc(nav_title(lang, p))}</a>' for p in longread.REFERENCE)
    sup = ui["sup_note"].format(n=st.get("supplement_added", 0))
    return (f'<section class="intro" id="survey" aria-labelledby="h-survey"><div class="intro-in"><div class="intro-copy">'
            f'<p class="label">{esc(keep_dates(kv.get("kicker", "")))}</p><h2 id="h-survey" class="intro-t">{esc(ui["intro_h"])}</h2>'
            f'<div class="lede">{md(kv.get("lede", ""), lang)}</div>'
            f'<p class="sup"><span class="tag new">{esc(ui["added_tag"])}</span> {esc(sup)} <a href="#about">{esc(ui["about_l"])} →</a></p>'
            f'<p class="cta"><a class="btn primary" href="#ch01">{ui["cont"]} ↓</a><a class="btn" href="#atlas">{ui["atlas_go"]}</a>'
            f'<a class="btn" href="../paper/index.html">{ui["report"]}</a></p></div>'
            '<dl class="numbers">' + "".join(f"<div><dt>{esc(l)}</dt><dd>{v}</dd></div>" for v, l in nums) + "</dl>"
            + ('<p class="meta">' + "".join(f"<span>{md_inline(p, lang)}</span>" for p in meta) + "</p>" if meta else "") + "</div>"
            f'<nav class="route" id="chapters" aria-labelledby="route-t"><h2 class="route-t" id="route-t">{ui["route"]}</h2>'
            f'<ol class="route-parts">{"".join(parts)}</ol><p class="route-ref"><span>{ui["route_ref"]}:</span> {ref}</p></nav></section>')

def findings_section(lang, part):
    ui = UI[lang]
    fm, text = read_page(lang, "index")
    body = next((b[2] for b in blocks(text) if b[0] == "findings"), "")
    h = link_chapters(rewrite_internal(findings_list(body, lang), lang), lang)
    head = (f'<header class="plate syn-plate" data-sl><div class="plate-bg" aria-hidden="true"></div><div class="plate-in" data-sl>'
            f'<p class="plate-k"><span class="pk-ch">{ui["findings_eb"]}</span><span class="pk-part">{esc(part_label(lang, part))} · {esc(part["title"][lang])}</span></p>'
            f'<h2 class="plate-t" id="findings-t">{ui["findings_h"]}</h2><p class="plate-a">{ui["findings_note"]}</p></div></header>')
    return (f'<section class="chapter syn tone-{part["tone"]}" id="findings" data-k="findings" aria-labelledby="findings-t">{head}'
            f'<div class="sheet"><div class="flow findings">{h}</div></div></section>')

INTRO_S1 = {}   # lang -> title of the former index heading #s-1 (full.html called it #index-s-1)

def reference_section(lang):
    ui = UI[lang]; out = []
    for p in longread.REFERENCE:
        if p == "howto":
            fm, text = read_page(lang, "index")
            hb = "".join(wrap_tables(md(b[1], lang), lang) for b in blocks(text) if b[0] == "md")
            hb = re.sub(r"<h2>(.*?)</h2>", r'<h2 id="s-1">\1</h2>', hb, count=1)   # the former index anchor #s-1
            s1 = re.search(r'<h2 id="s-1">(.*?)</h2>', hb)
            INTRO_S1[lang] = strip_tags(s1.group(1)).strip() if s1 else ""
            moved = "".join(MOVED[lang].values())
            h = shift_heads(link_chapters(rewrite_internal(hb + moved, lang), lang))
            out.append(f'<section class="refsec" id="howto" data-k="howto" aria-labelledby="howto-t"><header class="refhead"><h2 id="howto-t">{ui["howto_t"]}</h2></header>'
                       f'<div class="flow prose">{h}</div></section>')
            continue
        fm, h = page_flow(lang, p)
        lead = fm.get("lead", "")
        out.append(f'<section class="refsec" id="{p}" data-k="{p}" aria-labelledby="{p}-t"><header class="refhead"><h2 id="{p}-t">{esc(fm.get("title", p))}</h2>'
                   + (f'<p class="reflead">{md_inline(lead, lang)}</p>' if lead else "") + f'</header><div class="flow prose">{h}</div></section>')
    return (f'<div class="reference" aria-label="{ui["appendix"]}"><p class="ref-k">{ui["appendix"]}</p>' + "".join(out) + "</div>")

GREEK = re.compile(r"[\u03b1-\u03c9\u03d1\u03d5\u03f0\u03f1\u03f5]+")
CAPS_EL = [re.compile(r'(<th\b[^>]*>)(.*?)(</th>)', re.S), re.compile(r'(<p class="ctl">)(.*?)(</p>)', re.S),
           re.compile(r'(<span class="ctl-l">)(.*?)(</span>)', re.S)]

def keep_greek(html):
    """The design sets table heads, callout titles and scene control labels in capitals, which would turn λ into Λ and
    ρ into Ρ, different symbols: the Greek letters in those elements keep their case (.gk)."""
    def inner(m):
        parts = re.split(r"(<[^>]+>)", m.group(2))
        return m.group(1) + "".join(x if x.startswith("<") else GREEK.sub(lambda g: f'<span class="gk">{g.group(0)}</span>', x) for x in parts) + m.group(3)
    for pat in CAPS_EL:
        html = pat.sub(inner, html)
    return html

def longread_page(lang):
    FIG.update(k=0, ch=None, page=None, list=[])
    kv = cover(lang)
    hero = site_story.hero_html(lang, dict(kicker=keep_dates(kv.get("kicker", "")), subtitle=kv.get("subtitle", ""), meta_line=keep_dates(f'{AUTHORS} · {UI[lang]["edition"]}')))
    stage = site_story.stage_html(lang, card_href, ch1_href="#ch01-fig-2", agensh_href="#agensh",
                                  title_of=lambda w, l: strip_tags(md_inline(card_title(WORKS.get(w["id"], w), l), l)))
    sections = [hero, stage, intro_section(lang)]
    body = []
    for part in longread.PARTS:
        body.append(part_opener(lang, part))
        for p in part["pages"]:
            body.append(findings_section(lang, part) if p == "findings" else chapter_section(lang, p, part))
    ref = reference_section(lang)
    content = keep_greek("\n".join(sections + body + [ref]))
    fm, _ = read_page(lang, "index")
    title = f'{SITE_TITLE[lang]}: {SITE_SUB[lang]}'
    return shell(lang, title, content, desc=strip_tags(md_inline(fm.get("lead", "") or SITE_SUB[lang], lang)))

# ---------------------------------------------------------------- former page addresses
def full_fig_map(lang):
    """full.html numbered figures across the whole text (index, chapters, glossary, about) without resetting."""
    m, n = {}, 0
    for p in ["index"] + CHAPTERS + ["glossary", "about"]:
        figs = [(o, new) for o, new, lab in ANCHORS[lang].get(p, []) if o.startswith("fig-")]
        for o, new in figs:
            n += 1; m[f"fig-{n}"] = new; m[f"zoom-{n}"] = new
    return m

def stub(lang, page):
    """A former page: forwards its fragment to the single page; without JavaScript it lists the places as links."""
    ui = UI[lang]; other = ui["lang_other_code"]
    if page == "full":
        default, title, lab = "top", ui["prologue"], SITE_TITLE[lang]
        amap = {f"p-{p}": PAGE_ANCHOR.get(p, p) for p in PAGE_ORDER}
        amap.update(full_fig_map(lang)); amap["p-index"] = "top"; amap["index-s-1"] = "s-1"
        items = [(f"p-{p}", PAGE_ANCHOR.get(p, p), (f"{num_of(lang, p)}. " if p.startswith("ch") else "") + nav_title(lang, p) if p != "index" else SITE_TITLE[lang]) for p in PAGE_ORDER]
        # the full page's own deep links: sections and cards kept their ids; figures were numbered through the text
        items.append(("index-s-1", "s-1", INTRO_S1.get(lang) or "§ 1"))   # its one introduction heading
        nfig = 0
        for p in ["index"] + CHAPTERS + ["glossary", "about"]:
            for o, n_, t in ANCHORS[lang].get(p, []):
                if o.startswith("fig-"):
                    nfig += 1; f_ = t or f'{ui["fig"]} {nfig}'
                    items += [(f"fig-{nfig}", n_, f_), (f"zoom-{nfig}", n_, ui["stub_zoom"].format(f=f_))]
                elif t and p != "index" and not o.startswith("zoom-"):
                    items.append((n_, n_, t))
        items = list({o: (o, n_, t) for o, n_, t in reversed(items)}.values())[::-1]   # one entry per old id, first wins
    else:
        fm, _ = read_page(lang, page)
        default = PAGE_ANCHOR.get(page, page)
        title = fm.get("title", page)
        lab = f'{ui["chapter"]} {fm.get("num")}' if page.startswith("ch") else (ui["atlas"] if page == "atlas" else ui["appendix"])
        amap = {o: n for o, n, _ in ANCHORS[lang].get(page, []) if o != n}
        items = [(o, n, t) for o, n, t in ANCHORS[lang].get(page, []) if t]
        if page == "atlas":
            items = [(f"a-{w['id']}", f"a-{w['id']}", strip_tags(md_inline(atlas_title(w, lang), lang))) for w in WORKS.values()]
        if page == "sources":
            items = [(f"src-{p}", f"src-{p}", nav_title(lang, p)) for p in SOURCES_BY_PAGE] + [(f"s-{w['id']}", f"s-{w['id']}", strip_tags(card_title(w, lang))) for ws in SOURCES_BY_PAGE.values() for w in ws]
        figt = {n_: t for o, n_, t in ANCHORS[lang].get(page, []) if o.startswith("fig-")}   # a zoom address lands on its figure
        items += [(o, n_, ui["stub_zoom"].format(f=figt.get(n_) or o) if o.startswith("zoom-") else figt.get(n_) or o)
                  for o, n_, t in ANCHORS[lang].get(page, []) if not t]
    js = ("<script>(function(){var m=" + json.dumps(amap, ensure_ascii=False) + ",d=" + json.dumps(default) +
          ";var h=location.hash.slice(1);try{h=decodeURIComponent(h)}catch(e){}location.replace(" + json.dumps(PAGE + "#") + "+encodeURIComponent(h?(m[h]||h):d).replace(/%2F/g,'/'))})()</script>")
    lis = "".join(f'<li id="{esc(o)}"><a href="{PAGE}#{esc(n)}">{esc(t)}</a></li>' for o, n, t in items)
    extra = ""
    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {SITE_TITLE[lang]}</title><meta name="robots" content="noindex"><link rel="canonical" href="{PAGE}#{esc(default)}">
{js}
<script>(function(d){{d.classList.add('js');try{{if(localStorage.getItem('aas-theme')==='light')d.classList.add('light')}}catch(e){{}}}})(document.documentElement)</script>
<link rel="stylesheet" href="../assets/css/site.css"><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"></head>
<body class="stub"><main class="stub-in"><p class="eyebrow">{esc(lab)}</p><h1>{esc(title)}</h1><p>{ui["stub_now"]}</p>
<p class="cta"><a class="btn primary" href="{PAGE}#{esc(default)}">{ui["stub_go"]} →</a><a class="btn" href="../{other}/{page}.html" hreflang="{other}">{ui["stub_lang"]}</a></p>
<details class="stub-list" open><summary>{ui["stub_more"]}</summary><ol>{lis}</ol></details>{extra}</main></body></html>"""

def root_page():
    """site/index.html: the Field edition in English and Russian, then the dated detailed survey and the report."""
    poster = ('<figure class="rootposter" aria-hidden="true">'
              '<img class="theme-dark-only" src="assets/illustrations/topologies-en-dark.svg" alt="" width="1600" height="900">'
              '<img class="theme-light-only" src="assets/illustrations/topologies-en-light.svg" alt="" width="1600" height="900"></figure>') \
        if os.path.isdir(os.path.join(ASSETS, "illustrations")) else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{SITE_TITLE['en']} · {SITE_TITLE['ru']}</title><meta name="description" content="{esc(SITE_SUB['en'])}. {AUTHORS}.">
<meta name="color-scheme" content="dark light"><meta name="theme-color" content="#050507">{HEAD_JS}
<link rel="stylesheet" href="assets/css/site.css"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" hreflang="en" href="en/index.html"><link rel="alternate" hreflang="ru" href="ru/index.html"></head>
<body class="root"><main class="rootmain">
<header>{RING.replace('<svg ', '<svg class="ring" ', 1)}<h1>{SITE_TITLE['en']}</h1><p class="subtitle">{SITE_SUB['en']}</p><p class="byline">{AUTHORS} · November 2026</p></header>
<nav class="choose" aria-label="Language"><a href="en/index.html" hreflang="en" data-lang="en"><b>English</b><span>How communication, scale, memory and collective errors change LLM swarms: eight scenes on one page and a map of about 300 sources, November 2026.</span></a>
<a href="ru/index.html" hreflang="ru" lang="ru" data-lang="ru"><b>Русский</b><span>Как связь, масштаб, память и коллективные ошибки меняют рои LLM-агентов: восемь сцен на одной странице и карта около 300 источников, ноябрь 2026.</span></a></nav>
<p class="rootmore">The detailed survey, {UI['en']['edition']}: <a href="en/{PAGE}" hreflang="en">English</a> · <a href="ru/{PAGE}" hreflang="ru" lang="ru">Русский</a> · <a href="paper/index.html">technical report (PDF, 15 November 2026)</a></p>
{poster}
</main><script>(function(){{try{{var l=(navigator.language||'').slice(0,2)==='ru'?'ru':'en';var a=document.querySelector('.choose a[data-lang="'+l+'"]');if(a)a.classList.add('pref');}}catch(e){{}}}})();</script></body></html>"""

def current_bib():
    """BibTeX of the current catalogue (19 October 2026), one entry per record. data/bib/works.bib stays the registry of
    3 October and is not rewritten (the supplement keeps it on purpose); here its entries take the supplement the way
    updates/2026-10-19/catalogue.json applies it: added and updated records take the supplement's entries
    (updates/2026-10-19/references.bib), a corrected record loses an identifier the catalogue no longer gives it, and
    the header says which and whose it is. Key = canonical work id, as in the registry."""
    def entries(path):
        t = open(os.path.join(ROOT, path), encoding="utf-8").read()
        return {m.group(1): m.group(0) for m in re.finditer(r"^@\w+\{([^,\n]+),\n.*?^\}\n", t, re.M | re.S)}
    reg, sup = entries("data/bib/works.bib"), entries("updates/2026-10-19/references.bib")
    works = catalogue.works()
    owner = {(w.get("identifiers") or {}).get("arxiv"): w for w in works if (w.get("identifiers") or {}).get("arxiv")}
    out, notes = [], []
    for w in works:
        k, kind = w["id"], catalogue.changed(w["id"])
        e = sup[k] if kind in ("added", "updated") else reg[k]
        ax = (w.get("identifiers") or {}).get("arxiv")
        old = re.search(r"^  eprint = \{([^}]*)\},?\n", e, re.M)
        if kind == "corrected" and old and old.group(1) != ax:
            e = re.sub(r"^  (?:eprint|archivePrefix) = \{[^}]*\},?\n", "", e, flags=re.M)
            o = owner.get(old.group(1))
            whose = f'; it identifies {o["title"]} ({o["authors"][0].split()[-1]} et al., key {o["id"]})' if o else ""
            notes.append(f"%   {k}: arXiv:{old.group(1)} removed{whose}, not this work.")
        out.append(e)
    S = catalogue.SUP
    head = [f"% Swarm Dynamics: BibTeX of the catalogue as of {S['checked_at']} ({len(out)} records). Generated by scripts/build_site.py from",
            "% data/bib/works.bib (the registry of 3 October 2026, kept unchanged) and the dated supplement in updates/2026-10-19/:",
            f"% {len(S['added'])} records added and {len(S['updated'])} updated from its references.bib; {len(S['corrected'])} identifier corrected as in its catalogue.json:"]
    return "\n".join(head + notes + ["% Key = canonical work id.", "", ""]) + "\n".join(out)

# ---------------------------------------------------------------- build
def build():
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    # Downloadable scholarly candidate; paper/ is owned and built separately.
    for name in ("swarm-dynamics.pdf", "swarm-dynamics-source.zip", "index.html", "cite-this-report.bib"):
        source = os.path.join(ROOT, "paper", name)
        if os.path.isfile(source):
            os.makedirs(os.path.join(OUT, "paper"), exist_ok=True)
            shutil.copy2(source, os.path.join(OUT, "paper", name))
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    for src, name in (("data/works.json", "works.json"), ("data/bib/works.bib", "works.bib"),            # the registry as of 3 October
                      ("updates/2026-10-19/catalogue.json", "catalogue-2026-10-19.json")):                  # with the 19 October supplement
        if os.path.isfile(os.path.join(ROOT, src)): shutil.copy2(os.path.join(ROOT, src), os.path.join(OUT, "data", name))
    open(os.path.join(OUT, "data", "references-2026-10-19.bib"), "w", encoding="utf-8").write(current_bib())
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
    built = []
    for lang in LANGS:
        os.makedirs(os.path.join(OUT, lang), exist_ok=True)
        # a first pass fills card leads (atlas summaries), section lists and the about page's citation anchor
        for p in CHAPTERS + ["glossary", "sources", "about", "atlas"]:
            page_flow(lang, p)
        hit = next((a for a, t in HEADS[lang].get("about", []) if re.search(r"цитир|cite", t, re.I)), None)
        if hit: CITE_ANCHOR[lang] = "#" + hit
        for d in (ANCHORS, HEADS, MOVED, SCENE_N): d[lang].clear()
        open(os.path.join(OUT, lang, PAGE), "w", encoding="utf-8").write(longread_page(lang)); built.append(f"{lang}/{PAGE}")
        for p in longread.STUB_PAGES:
            open(os.path.join(OUT, lang, p + ".html"), "w", encoding="utf-8").write(stub(lang, p)); built.append(f"{lang}/{p}.html")
    built += build_field.build(site_dir=OUT)   # site/<lang>/index.html: the Field edition
    root = root_page()
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(root)
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(root.replace('<main class="rootmain">', '<main class="rootmain"><p class="eyebrow">404</p>', 1))
    return built

def check():
    errs = []
    cache = {}
    def ids_of(path):
        if path not in cache:
            t = open(path, encoding="utf-8").read()
            cache[path] = set(re.findall(r'\sid="([^"]+)"', t))
        return cache[path]
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            if not f.endswith(".html"): continue
            p = os.path.join(dp, f); t = open(p, encoding="utf-8").read()
            rel = os.path.relpath(p, OUT)
            ids_list = re.findall(r'\sid="([^"]+)"', t)
            seen, dup = set(), set()
            for i in ids_list:
                (dup if i in seen else seen).add(i)
            dup = sorted(dup)
            if dup: errs.append(f"{rel}: duplicate ids {dup[:12]}")
            ids = set(ids_list)
            for href in re.findall(r'(?:href|src|data-full|data-full-light)="([^"]+)"', t):
                if href.startswith(("http://", "https://", "mailto:", "data:")): continue
                target, _, frag = href.partition("#")
                if target:
                    tp = os.path.normpath(os.path.join(dp, target))
                    if not tp.startswith(OUT): errs.append(f"{rel}: points outside site/: {href}"); continue
                    if not os.path.exists(tp): errs.append(f"{rel}: missing {href}"); continue
                    if frag and tp.endswith(".html") and frag not in ids_of(tp): errs.append(f"{rel}: missing anchor {href}")
                elif frag and frag not in ids:
                    errs.append(f"{rel}: missing local anchor #{frag}")
            if re.search(r"\{\{|%%ATLAS%%|%%SOURCES%%|%%SCENE", t): errs.append(f"{rel}: unfilled template mark")
    # every forwarding target of the former pages exists on the single page
    for lang in LANGS:
        page_ids = ids_of(os.path.join(OUT, lang, PAGE))
        for p in longread.STUB_PAGES:
            t = open(os.path.join(OUT, lang, p + ".html"), encoding="utf-8").read()
            m = re.search(r"var m=(\{.*?\}),d=(\"[^\"]*\")", t)
            if not m: errs.append(f"{lang}/{p}.html: no forwarding map"); continue
            amap = json.loads(m.group(1)); d = json.loads(m.group(2))
            for o, n in list(amap.items()) + [("", d)]:
                if n not in page_ids: errs.append(f"{lang}/{p}.html: #{o} -> #{n} missing on the single page")
            # without JavaScript the same addresses work as a list: every forwarded one has its labelled entry, same target
            nojs = {html.unescape(i): (html.unescape(h), strip_tags(lab).strip())
                    for i, h, lab in re.findall(r'<li id="([^"]+)"><a href="' + re.escape(PAGE) + r'#([^"]*)">(.*?)</a></li>', t)}
            for o, n in amap.items():
                if o not in nojs or nojs[o][0] != n or not nojs[o][1]:
                    errs.append(f"{lang}/{p}.html: #{o} -> #{n} has no labelled no-JS entry ({nojs.get(o)})")
    return errs

if __name__ == "__main__":
    built = build()
    print("built", len(built), "pages")
    if "--check" in sys.argv:
        e = check()
        for x in e[:80]: print("LINK", x)
        print("link errors:", len(e))
        sys.exit(1 if e else 0)

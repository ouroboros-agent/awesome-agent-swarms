#!/usr/bin/env python3
"""The longread's editorial structure: one continuous page per language.

scripts/build_site.py renders the chapters from content/{ru,en}/*.md and assembles them in the order given
here. This module holds only what the Markdown files do not: the four parts that group the chapters, the
short bridge copy that opens each part, interface strings of the single page, where each native scene sits
in the flow, and how old page addresses map onto the single page.

Copy rules (see content/FORMAT.md): no reading instructions, no "why it matters" rubrics; every number in a
bridge is one the chapters already state.
"""

# ---------------------------------------------------------------- parts
# A part is an editorial overlay: chapter numbers and texts are unchanged.
PARTS = [
    dict(id="part-1", key="I", pages=["ch01", "ch02", "ch03"], tone="i",
         title={"en": "The field and its events", "ru": "Поле и события"},
         say={"en": "“Swarm” in these 153 works means anything from a pair of agents to tens of thousands. First the count: "
                    "how many agents really run at once, who builds them and on which models. Then the events of 2025–2026, "
                    "including a swarm that nobody designed.",
              "ru": "В этих 153 работах роем называют всё — от пары агентов до десятков тысяч. Сначала подсчёт: сколько агентов "
                    "действительно работают одновременно, кто их строит и на каких моделях. Затем события 2025–2026 годов, "
                    "включая рой, который никто не проектировал."}),
    dict(id="part-2", key="II", pages=["ch04", "ch05", "ch06"], tone="ii",
         title={"en": "What more agents give you", "ru": "Что дают дополнительные агенты"},
         say={"en": "More agents can save time or improve results, depending on what the comparison holds equal. Shared memory "
                    "and coordination introduce another question: can the team combine what its members know?",
              "ru": "Дополнительные агенты могут экономить время или повышать качество — смотря что уравнено в сравнении. "
                    "Общая память и координация ставят другой вопрос: умеет ли команда объединять знания участников?"}),
    dict(id="part-3", key="III", pages=["ch07", "ch08", "ch09", "ch10"], tone="iii",
         title={"en": "What happens between agents", "ru": "Что происходит между агентами"},
         say={"en": "Communication changes behaviour: a team can violate rules its members follow alone, spread a loophole "
                    "through shared files, echo the same answer or converge on a biased consensus. Open platforms add human "
                    "influence to the picture.",
              "ru": "Общение меняет поведение: команда может нарушать правила, которым агенты следуют поодиночке, распространять "
                    "лазейку через общие файлы, повторять один ответ или приходить к предвзятому согласию. На открытых площадках "
                    "добавляется влияние людей."}),
    dict(id="part-4", key="", pages=["findings", "ch11", "atlas"], tone="iv",
         title={"en": "What is shown, what is open", "ru": "Что показано, что открыто"},
         say={"en": "What the studies have shown, what they leave open, and every work in the survey in one table.",
              "ru": "Что работы показали, что оставили открытым, и все работы обзора в одной таблице."}),
]
REFERENCE = ["glossary", "howto", "sources", "about"]          # appendix after the parts

UI = {
 "en": dict(part="Part", epilogue="Epilogue", chapter="Chapter", of="of", appendix="Reference",
            here_top="Overview", contents="Contents", route="Contents", route_ref="Reference",
            findings_eb="Ten findings", howto_t="Cards and labels", src_ch="Sources for this chapter",
            top="Back to the top", cont="Chapter 1", atlas_go="Atlas of works", report="Technical report",
            png="Static chart (PNG)", png_dark="dark", png_light="light", data_t="Data behind the chart",
            schematic="Schematic", data="Survey data", replay="Replay", pause="Pause", play="Play",
            sources_note="Each list follows the order of the chapter.",
            stub_now="This page is now part of the single page of the survey.", stub_go="Open it in place",
            stub_more="Sections, cards and figures of the former page", stub_lang="Русская версия",
            stub_zoom="{f} (enlarged view)", motion_off="Stop the motion", motion_on="Resume the motion", motion_sys="Motion is off in your system settings",
            towers_k="Cards in each chapter", towers_full="full", towers_short="short", towers_note="{f} full and {s} short cards", towers_none="no cards"),
 "ru": dict(part="Часть", epilogue="Эпилог", chapter="Глава", of="из", appendix="Справка",
            here_top="Обзор", contents="Содержание", route="Содержание", route_ref="Справка",
            findings_eb="Десять выводов", howto_t="Карточки и ярлыки", src_ch="Источники главы",
            top="Наверх", cont="Глава 1", atlas_go="Атлас работ", report="Технический отчёт",
            png="Статичный график (PNG)", png_dark="тёмный", png_light="светлый", data_t="Данные графика",
            schematic="Схема", data="Данные обзора", replay="Ещё раз", pause="Пауза", play="Продолжить",
            sources_note="Списки идут в порядке глав.",
            stub_now="Эта страница теперь входит в единую страницу обзора.", stub_go="Открыть на месте",
            stub_more="Разделы, карточки и рисунки прежней страницы", stub_lang="English version",
            stub_zoom="{f} (увеличенный вид)", motion_off="Остановить анимацию", motion_on="Включить анимацию", motion_sys="Анимация выключена в настройках системы",
            towers_k="Карточки в каждой главе", towers_full="подробные", towers_short="краткие", towers_note="подробных карточек — {f}, кратких — {s}", towers_none="карточек нет"),
}

# ---------------------------------------------------------------- scenes in the flow
# Hooks are language-independent: the RU and EN files have the same block sequence (scripts/check_content.py).
#   fig:<file>       the scene replaces that figure and keeps its number and caption
#   after:<card-id>  the scene follows that card;  before:<card-id>  it precedes it
#   callout:<k>      after the k-th callout of the page (1-based);  table:<k>  enhances the k-th table
PLACE = {
    "ch01": {"fig:dash_mechanisms_dark.png": "fieldmap", "fig:dash_scale_dark.png": "scale", "fig:dash_timeline_dark.png": "rhythm",
             "fig:dash_orgs_dark.png": "orgs", "fig:dash_models_dark.png": "models", "fig:dash_topics_dark.png": "topics"},
    "ch04": {"table:1": "ledger", "callout:1": "lambda"},
    "ch05": {"after:agensh-1024": "agensh"},
    "ch06": {"before:hiddenbench": "hidden", "after:scalemas-substrate": "substrate", "after:multi-agent-transactive-memory": "matm"},
    "ch07": {"after:mind-viruses": "virus", "after:deepmind-cheating-whistleblowing": "loophole"},
    "ch08": {"after:ringelmann-effect": "echo"},
    "ch09": {"after:okawa-biased-consensus": "consensus"},
    "ch10": {"after:wiz-moltbook": "moltbook"},
}

# Sections of chapter Markdown that leave the reading flow for the reference appendix. They are kept whole,
# with the id they had on their chapter page, so old links still land on them.
MOVE_TO_HOWTO = {"ch01": ["How to read the cards", "Как читать карточки"]}

# ---------------------------------------------------------------- old addresses
# index.html kept its own anchors (#how, #survey, #scale, #findings, #agensh, #chapters, #howto, #s-1).
# A former page P maps to the single page like this (P = ch01…ch11, glossary, about):
#   P.html            -> index.html#P            (#atlas, #glossary, #sources, #about for the reference pages)
#   P.html#s-N        -> index.html#P-s-N        (section headings keep their counter)
#   P.html#fig-N      -> index.html#P-fig-N      (and #zoom-N)
#   P.html#w-<id>, atlas.html#a-<id>, sources.html#src-<page> / #s-<id>  -> the same fragment
#   full.html#p-P -> #P;  full.html#P-s-N -> same;  full.html#fig-N -> the figure's new id (table in the stub)
STUB_PAGES = [f"ch{n:02d}" for n in range(1, 12)] + ["atlas", "glossary", "sources", "about", "full"]

#!/usr/bin/env python3
"""Generate README.md and README.ru.md from content/ (findings, chapter titles) and data/stats.json.
  python scripts/build_readme.py"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
st = json.load(open(os.path.join(ROOT, "data/stats.json")))
aud = os.path.join(ROOT, "data/provenance/identity_audit.json")
cls = json.load(open(aud))["class_counts"] if os.path.exists(aud) else {}
def findings(lang):
    t = open(os.path.join(ROOT, f"content/{lang}/index.md")).read()
    m = re.search(r":::findings\n(.*?)\n:::", t, re.S)
    return [re.match(r"\s*\d+\.\s+\*\*(.+?)\*\*", l).group(1) for l in m.group(1).split("\n") if re.match(r"\s*\d+\.\s+\*\*(.+?)\*\*", l)]
def chapters(lang):
    return [(n, re.search(r"^title:\s*(.+)$", open(os.path.join(ROOT, f"content/{lang}/ch{n:02d}.md")).read(), re.M).group(1)) for n in range(1, 12)]
scholarly = cls["paper"]
other_records = st["unique_works"] - scholarly
dossiers = cls["bundle"]
EN = f"""# Awesome Agent Swarms

**Research on the dynamics of LLM agent collectives** — a bilingual (English / Russian) research survey, atlas and resource catalogue.

> **On the Dynamics of LLM Agent Swarms: Scaling, Coordination, and Collective Behavior**
> Anton Razzhigaev, Ouroboros · self-published technical report · corpus cut-off 3 October 2026

**Status:** private candidate. The repository and site are not public yet; nothing here has been deployed. The text has not been peer-reviewed. Ouroboros is an AI agent system: this is a human–AI collaboration (see *About* on the site).

## What is here

| | |
|---|---|
| **Site** (`site/`, open `site/index.html`) | Static RU+EN site: orientation and key findings, 11 thematic chapters with disclosure cards, a filterable atlas of all works, glossary, sources, single-page full text. Works without JavaScript; dark Ouroboros theme with a light toggle. |
| **Scholarly version** (`paper/`) | Self-published technical report in ACL format, private draft: [PDF](paper/swarm-dynamics.pdf), [LaTeX](paper/main.tex), [source ZIP](paper/swarm-dynamics-source.zip), [build instructions](paper/BUILD.md). |
| **[CATALOG.md](CATALOG.md)** / [CATALOG.ru.md](CATALOG.ru.md) | Every cited paper, preprint, system card, lab post, incident report, essay and dataset, grouped by theme, one line each. |
| **Data** (`data/`) | `works.json`: canonical registry (IDs, aliases, identifiers, metadata); `figures.json`: figure provenance and rights; `bib/works.bib`: BibTeX export (key = work ID); `provenance/`: source manifest, change and preservation map, identity audit, QA. |
| **Content** (`content/en`, `content/ru`) | The survey text in Markdown with a small block syntax (`content/FORMAT.md`). |

**Counts** (measured by `scripts/build_registry.py` and `scripts/identity_audit.py`): {st['corpus']} works in the analytic corpus · {st['cards_full']} full and {st['cards_short']} short cards (including {st['cards_added_after_import']} short cards added after import, outside the analytic corpus) · {st['related_rows']} related-work rows · {st['fig_works']} figures from the works and {st['fig_own']} own charts.

{st['unique_works']} unique records for works and resources after merging versions. Of these, {scholarly} are classified as scholarly works—journal articles, conference and workshop papers, and preprints. The other {other_records} include reports, system cards, other resources, and {dossiers} composite case dossiers. See the [identity audit](data/provenance/IDENTITY_AUDIT.md) for classification and counting rules.

## Key findings

Ten findings, stated for the corpus as of 3 October 2026; each is qualified and linked to its evidence on the site:

""" + "\n".join(f"{i}. {f}" for i, f in enumerate(findings("en"), 1)) + """

## Chapters

""" + "\n".join(f"{n}. {t}" for n, t in chapters("en")) + """

Plus: atlas of works (filters by topic, evidence class, scale, source type, chapter), glossary, sources, about.

## Build

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make charts site catalog check     # charts → site/ → CATALOG*.md, RIGHTS.md → content checks
make qa                            # real-browser checks (needs Google Chrome and Playwright WebKit)
```

`scripts/check_content.py` verifies RU/EN structural parity (same cards, figures, tables, links and numbers) and, with `--source`, that the edit preserved every card, figure, link and number of the October 2026 text. `scripts/qa_browser.py` loads every page in Chromium and WebKit at phone and desktop sizes, with and without JavaScript.

## Cite

```bibtex
@techreport{razzhigaev2026dynamics,
  title       = {On the Dynamics of {LLM} Agent Swarms: Scaling, Coordination, and Collective Behavior},
  author      = {Razzhigaev, Anton and {Ouroboros}},
  year        = {2026},
  institution = {Self-published technical report},
  url         = {https://github.com/ouroboros-agent/awesome-agent-swarms},
  note        = {Research survey; corpus cut-off 3 October 2026}
}
```

See also [CITATION.cff](CITATION.cff).

## Licence

Text, tables and data: CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)). Code: MIT ([LICENSE](LICENSE)). Figures reproduced from the surveyed works keep their owners' rights and are not covered by these licences — see [RIGHTS.md](RIGHTS.md).

[Русская версия](README.ru.md)
"""
RU = f"""# Awesome Agent Swarms

**Исследования динамики коллективов LLM-агентов** — двуязычный (русский / английский) обзор исследований, атлас работ и каталог ресурсов.

> **Динамика роёв LLM-агентов: масштабирование, координация и коллективное поведение**
> (On the Dynamics of LLM Agent Swarms: Scaling, Coordination, and Collective Behavior)
> Anton Razzhigaev, Ouroboros · самостоятельно опубликованный технический отчёт · срез корпуса 3 октября 2026

**Статус:** приватный кандидат. Репозиторий и сайт пока не публичны, ничего не развёрнуто. Текст не проходил рецензирование. Ouroboros — система ИИ-агентов; это совместная работа человека и ИИ (см. «Об обзоре» на сайте).

## Что здесь есть

| | |
|---|---|
| **Сайт** (`site/`, открыть `site/index.html`) | Статический сайт RU+EN: вводная страница и главные выводы, 11 тематических глав с раскрывающимися карточками, атлас всех работ с фильтрами, словарик, источники, весь текст на одной странице. Работает без JavaScript; тёмная тема Ouroboros и переключатель светлой. |
| **Научная версия** (`paper/`) | Самостоятельный технический отчёт в формате ACL, приватный черновик: [PDF](paper/swarm-dynamics.pdf), [LaTeX](paper/main.tex), [ZIP исходников](paper/swarm-dynamics-source.zip), [сборка](paper/BUILD.md). |
| **[CATALOG.ru.md](CATALOG.ru.md)** / [CATALOG.md](CATALOG.md) | Все цитируемые статьи, препринты, системные карты, посты лабораторий, отчёты об инцидентах, эссе и датасеты по темам, по строке на работу. |
| **Данные** (`data/`) | `works.json` — реестр (ID, синонимы, идентификаторы, метаданные); `figures.json` — происхождение и права рисунков; `bib/works.bib` — BibTeX (ключ = ID работы); `provenance/` — манифест источников, карта изменений и сохранности, аудит идентичности, QA. |
| **Текст** (`content/ru`, `content/en`) | Текст обзора в Markdown с небольшим синтаксисом блоков (`content/FORMAT.md`). |

**Счёт** (`scripts/build_registry.py`, `scripts/identity_audit.py`): {st['corpus']} работ в аналитическом корпусе · {st['cards_full']} подробных и {st['cards_short']} кратких карточек (включая {st['cards_added_after_import']} краткие карточки, добавленные после импорта вне аналитического корпуса) · {st['related_rows']} строк «Ещё по теме» · {st['fig_works']} рисунков из работ и {st['fig_own']} собственных графиков.

{st['unique_works']} уникальных записей о работах и ресурсах после объединения версий. Из них {scholarly} классифицированы как научные работы — журнальные статьи, конференционные и воркшоп-публикации, препринты; остальные {other_records} включают отчёты, системные карты, другие ресурсы и {dossiers} составных досье. Классификация и правила подсчёта — в [аудите идентичности](data/provenance/IDENTITY_AUDIT.md).

## Главные выводы

Десять выводов о корпусе на 3 октября 2026 года; на сайте у каждого — условия и ссылки на доказательства:

""" + "\n".join(f"{i}. {f}" for i, f in enumerate(findings("ru"), 1)) + """

## Главы

""" + "\n".join(f"{n}. {t}" for n, t in chapters("ru")) + """

А также атлас работ (фильтры по теме, классу доказательств, масштабу, типу источника и главе), словарик, источники, «Об обзоре».

## Сборка

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
make charts site catalog check     # графики → site/ → CATALOG*.md, RIGHTS.md → проверки текста
make qa                            # проверка в настоящих браузерах (нужны Google Chrome и Playwright WebKit)
```

`scripts/check_content.py` сверяет структуру RU и EN (те же карточки, рисунки, таблицы, ссылки и числа), а с `--source` — что правка сохранила все карточки, рисунки, ссылки и числа октябрьского текста 2026 года. `scripts/qa_browser.py` открывает каждую страницу в Chromium и WebKit на телефоне и десктопе, с JavaScript и без.

## Как цитировать

См. BibTeX в [README.md](README.md#cite) и [CITATION.cff](CITATION.cff).

## Лицензия

Текст, таблицы и данные — CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)). Код — MIT ([LICENSE](LICENSE)). Рисунки из работ остаются под правами владельцев и не покрываются этими лицензиями — см. [RIGHTS.md](RIGHTS.md).

[English version](README.md)
"""
open(os.path.join(ROOT, "README.md"), "w").write(EN); open(os.path.join(ROOT, "README.ru.md"), "w").write(RU)
print("README.md", len(EN), "README.ru.md", len(RU))

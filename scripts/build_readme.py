#!/usr/bin/env python3
"""Generate README.md and README.ru.md: an entry into the survey with embedded illustrations.

  python scripts/build_readme.py

Chapter titles and leads come from content/{en,ru}/chNN.md; counts come from data/stats.json and data/works.json (the
analytic corpus and registry as of the 3 October 2026 cut-off) and from scripts/catalogue.py (the catalogue with the
19 October 2026 supplement). The posters and charts are standalone SVG files in assets/illustrations/ (written by
scripts/site_story.py in the B «Контекст» design: no script, web fonts or network), shown through <picture> so GitHub
picks the dark or light variant.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import site_story
import catalogue

ST = json.load(open(os.path.join(ROOT, "data/stats.json"), encoding="utf-8"))
CAT = len(catalogue.works())
SUP_N = len(catalogue.SUP["added"])
LD = site_story.ladder(site_story.load_works())
NB = "\u00a0"


def fnum_d(v):
    return f"{v:.1f}".replace(".", ",")


def fnum(n, lang):
    s = f"{int(n):,}"
    return s.replace(",", " ") if lang == "ru" else s


def front(lang, page):
    text = open(os.path.join(ROOT, "content", lang, page + ".md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = {}
    for line in (m.group(1).split("\n") if m else []):
        k, _, v = line.partition(":")
        if k.strip(): fm[k.strip()] = v.strip()
    return fm


def plain(s, lang):
    """Markdown inline -> plain text for a one-line summary."""
    s = re.sub(r"\{\{stat:(\w+)\}\}", lambda m: fnum(ST.get(m.group(1), 0), lang) if isinstance(ST.get(m.group(1)), int) else "", s or "")
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"[*_`]", "", s).strip()


def first_sentence(s):
    parts = re.split(r"(?<=[.?!])\s+(?=[A-ZА-ЯЁ«“\"(])", s, maxsplit=1)
    return parts[0]


def chapters(lang):
    out = []
    for n in range(1, 12):
        fm = front(lang, f"ch{n:02d}")
        lead = first_sentence(plain(fm.get("lead", ""), lang))
        out.append(f"{n}. [{fm.get('title', '')}](content/{lang}/ch{n:02d}.md). {lead}".rstrip())
    return "\n".join(out)


def picture(name, lang, alt):
    base = "assets/illustrations"
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{base}/{name}-{lang}-dark.svg">\n'
            f'  <img src="{base}/{name}-{lang}-light.svg" alt="{alt}">\n</picture>')


def chart(name, lang, alt):
    base = "assets/charts"
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{base}/{name}_{lang}_dark.png">\n'
            f'  <img src="{base}/{name}_{lang}_light.png" alt="{alt}">\n</picture>')


BIB = """```bibtex
@techreport{razzhigaev2026dynamics,
  title       = {On the Dynamics of {LLM} Agent Swarms: Scaling, Coordination, and Collective Behavior},
  author      = {Razzhigaev, Anton and {Ouroboros}},
  year        = {2026},
  institution = {Self-published technical report},
  url         = {https://github.com/ouroboros-agent/awesome-agent-swarms},
  note        = {Research survey; corpus cut-off 3 October 2026}
}
```"""

K = dict(corpus=ST["corpus"], known=LD["known"], med=LD["median"], fig_works=ST["fig_works"], cat=CAT, sup=SUP_N)
MEM = dict(site_story.MEMORY)

EN = f"""# Awesome Agent Swarms

**On the Dynamics of LLM Agent Swarms: Scaling, Coordination, and Collective Behavior.** A survey of what happens when many LLM agents work on one task: how they divide the work, pass findings and errors to each other and reach agreement, and what more agents buy in time, quality and tokens. The analysis rests on {K['corpus']} studies, system cards, engineering reports and incident investigations, mostly from 2025–2026, up to the 3 October 2026 cut-off; a dated supplement of 19 October 2026 adds {K['sup']} more works and corrects two conclusions. By Anton Razzhigaev and Ouroboros, in English and Russian.

{picture("topologies", "en", "Six agents drawn as context windows, connected in three ways: independently, through a coordinator, through a shared log. Agent 3's finding is a lime block; agents 1 and 5 redo the work in coral, receive a copy from the coordinator, or find the entry in the log.")}

Whether a swarm helps depends on what the comparison held fixed. In the Claude Opus 5.5 system card, a team of five reaches the same ProgramBench level 2.7 times faster than one agent and spends about 1.9 times the tokens (the survey's estimate from the card's chart). At equal total output tokens, OpenAI's published GPT-5.6 Sol curves put one agent ahead of a swarm of 4 on three benchmarks, and a swarm of 16 on the two where that team size was measured. The survey keeps such settings apart and gives every result with its scale, its comparison condition and its evidence class.

## What changed on 19 October 2026

A targeted search after the cut-off added five new preprints, two engineering reports (Google Research's Deep Review and the UK AI Security Institute's Transect) and a February paper on Moltbook, read in its October revision; two records were updated and one identifier corrected. The new works are discussed in Chapters 4–6, 9 and 10 and carry the label "added 19 October 2026". Two conclusions change:

- **Shared memory.** The survey had one direct comparison of shared and private memory within a team, in which private memory was slightly better (49.43 vs 48.62). ScaleMAS, from FAIR (Meta) and Harvard, adds a second: four identical Qwen3.5-9B agents answer {MEM['shared']}% of BrowseComp-Plus questions with a shared store, {MEM['private']}% with private stores and {MEM['none']}% independently, at equal team size rather than equal compute. Whether shared memory helps depends on the task, the retrieval mechanism and what the agents actually retrieve.
- **A skewed index is not skewed reading.** In Multi-Agent Transactive Memory, 77.82% of the ALFWorld index comes from one trained model; in version 2, that source supplies 25.6% of SVMRank retrievals, while 31 minority sources occupy 1.4% of the index but supply 40.7% of SVMRank retrievals.

{picture("memory", "en", f"ScaleMAS, BrowseComp-Plus: four identical agents answer {MEM['shared']}% correctly with a shared store, {MEM['private']}% with private stores and {MEM['none']}% without a store; equal team size, not equal compute. The earlier ablation found private memory slightly better, 49.43 vs 48.62.")}

This was a targeted update, not a systematic review or a replication of experiments; [About](content/en/about.md) gives its scope, and [`updates/2026-10-19/`](updates/2026-10-19/en.md) holds the dated supplement with its registry delta, catalogue and BibTeX. The charts of the {K['corpus']}-work analytic corpus and the PDF remain the 3 October edition.

## Where to read

- **Website** in `site/`: the whole survey as one continuous page in English (`site/en/index.html`) and Russian (`site/ru/index.html`), in a dark design where every agent is a context window drawn as a tower of blocks (a light theme is one switch away). It runs from the prologue, six agents and three ways to connect them, through three parts and eleven chapters to the findings, the open questions and an atlas of all {fnum(K['cat'], 'en')} works and resources with filters, then a glossary, sources and notes on method. Native scenes and charts explain the mechanisms and the corpus along the way. The files are static: open `site/index.html` in a browser, or run `python3 -m http.server -d site` and go to `http://localhost:8000`.
- **Technical report:** [PDF](paper/swarm-dynamics.pdf) in ACL format, with its [LaTeX source](paper/main.tex), a [source archive](paper/swarm-dynamics-source.zip) and [build notes](paper/BUILD.md). It is the edition of 3 October 2026 and does not include the supplement.
- **Catalogue:** [CATALOG.md](CATALOG.md) lists every cited work by theme, one line each, with the 19 October additions marked ([in Russian](CATALOG.ru.md)).
- **Data:** the [registry of works](data/works.json) as of 3 October, its [BibTeX](data/bib/works.bib) and [figure provenance](data/figures.json); the supplement's [registry delta](updates/2026-10-19/registry-delta.json) and [catalogue of {K['cat']} records](updates/2026-10-19/catalogue.json); the catalogue's current [BibTeX](site/data/references-2026-10-19.bib), with the corrected identifier.

The atlas lists {K['cat']} works and resources (catalogue as of 19 October); the survey’s charts use the {K['corpus']} works of the analytic corpus, with detailed metadata, as of 3 October.

## How big real swarms are

{picture("scale", "en", f"Of {K['known']} works that state how many agents run at once, the median swarm has {K['med']} agents; " + "; ".join(f"{v} have at least {fnum(t, 'en')}" for t, v in LD['rows']) + ".")}

Of these {K['corpus']} works, {K['known']} state how many agents run at the same time, and the median is {K['med']}. Live LLM swarms of 10,000 agents and more are known only from lab reports without a control run, while controlled experiments are mostly small. The map below places each work by agent count and evidence class; [Chapter 1](content/en/ch01.md) separates three meanings of “swarm size”: agents working at once, participants over a whole period, and platform capacity.

{chart("dash_scale", "en", "Every work in the corpus placed by number of agents (log scale) and evidence class, with simultaneous counts, cumulative counts and stated platform capacity marked differently.")}

## One run in numbers: 1,024 agents on pandoc

{picture("agensh-pandoc", "en", "Share of pandoc's hidden tests passed in 6 hours: 33.89% with one agent, 41.75% with 8, 43.11% with 32, 50.94% with 128, 55.06% with 1,024; ticks mark the mean over five tasks for 1–128 agents (19.31, 20.68, 26.52 and 28.78%).")}

In *Agensh: Scaling Organizational Intelligence to 1,024 Agents*, Microsoft Research gave up to 1,024 identical GPT-5.6-sol agents with no appointed leader six hours to rebuild pandoc, which they could study only by running it. The share of hidden tests passed rose from 33.89% for one agent to 55.06% for 1,024. Time was held equal, tokens were not, and the 1,024-agent team ran on pandoc only. [Chapter 5](content/en/ch05.md) covers the run and the roles that emerged in it.

## Chapters

The links open the Markdown text of each chapter, which GitHub renders; the website shows the same text with its figures, cards and filters.

{chapters("en")}

The [ten findings](content/en/index.md) close the main text, before the open questions. [About](content/en/about.md) describes how the corpus was assembled, and the [glossary](content/en/glossary.md) defines terms used in a narrow sense.

## Rights

Text, tables and data: CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)). Build code: MIT ([LICENSE](LICENSE)). The {K['fig_works']} figures reproduced from the surveyed works keep their owners' rights and are not covered by these licences; [RIGHTS.md](RIGHTS.md) gives the terms for each one.

## Cite

{BIB}

See also [CITATION.cff](CITATION.cff).

## Authors

Anton Razzhigaev set the scope of the survey, made the editorial decisions and is responsible for the publication. Ouroboros, an AI agent system, collected and read the sources, wrote the cards, ran the checks and prepared the text.

## Build

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium webkit
make site catalog check          # site/ and illustrations → CATALOG, RIGHTS, README → content checks
make coverage                    # every card, figure, link and heading is on the single page (PREV=<previous site/> compares editions)
make charts                      # optional: redraws the survey's own Chapter 1 charts from data; the committed PNGs are the published ones
make qa qa-features              # the page, figures, scenes and interactions; desktop/phone, JavaScript/no-JavaScript
```

[content/FORMAT.md](content/FORMAT.md) describes the text format, the order of the single page and how former page addresses map onto it; `scripts/check_content.py` checks that the English and Russian texts match block for block.

[Русская версия](README.ru.md)
"""

RU = f"""# Awesome Agent Swarms

**Динамика роёв LLM-агентов: масштабирование, координация и коллективное поведение.** Обзор того, что происходит, когда над одной задачей работает много LLM-агентов: как они делят работу, передают друг другу находки и ошибки, приходят к согласию и что дают лишние агенты по времени, качеству и токенам. Анализ опирается на {K['corpus']} исследования, системные карты, инженерные отчёты и разборы инцидентов, в основном 2025–2026 годов, до среза 3 октября 2026 года; датированное дополнение от 19 октября 2026 года добавляет ещё {K['sup']} работ и уточняет два вывода. Авторы — Anton Razzhigaev и Ouroboros; текст на русском и английском.

{picture("topologies", "ru", "Шесть агентов как окна контекста, связанные тремя способами: независимо, через координатора и через общий журнал. Находка агента 3 — салатовый блок; агенты 1 и 5 делают ту же работу заново (коралловые блоки), получают копию от координатора или находят запись в журнале.")}

Поможет ли рой, зависит от того, что уравняли при сравнении. В системной карте Claude Opus 5.5 команда из пяти агентов доходит до того же уровня ProgramBench в 2,7 раза быстрее одиночки и тратит примерно в 1,9 раза больше токенов (оценка обзора по графику из карты). При равной сумме выходных токенов опубликованные кривые OpenAI для GPT-5.6 Sol ставят одного агента впереди роя из 4 на трёх бенчмарках и роя из 16 на двух, где такую команду измеряли. Обзор держит такие условия раздельно и у каждого результата указывает масштаб, условие сравнения и класс доказательств.

## Что изменилось 19 октября 2026 года

Целевой поиск после среза добавил пять новых препринтов, два инженерных отчёта (Deep Review от Google Research и Transect от UK AI Security Institute) и февральскую работу о Moltbook, прочитанную в октябрьской версии; две записи обновлены, у одной исправлен идентификатор. Новые работы разобраны в главах 4–6, 9 и 10 и помечены ярлыком «добавлено 19 октября 2026». Меняются два вывода:

- **Общая память.** В обзоре было одно прямое сравнение общей и личной памяти внутри команды, и в нём личная память оказалась чуть лучше (49,43 против 48,62). ScaleMAS от FAIR (Meta) и Гарварда добавляет второе: четыре одинаковых агента Qwen3.5-9B отвечают верно на {fnum_d(MEM['shared'])}% вопросов BrowseComp-Plus с общим хранилищем, на {fnum_d(MEM['private'])}% с личными хранилищами и на {fnum_d(MEM['none'])}% без хранилища — при равном числе агентов, а не равных вычислениях. Польза общей памяти зависит от задачи, устройства поиска и того, что агенты реально извлекают.
- **Перекошенный индекс ещё не значит перекошенное чтение.** В Multi-Agent Transactive Memory 77,82% индекса ALFWorld дала одна обученная модель; во второй версии работы на этот источник приходится 25,6% извлечений SVMRank, а 31 малый источник занимает 1,4% индекса, но даёт 40,7% извлечений SVMRank.

{picture("memory", "ru", f"ScaleMAS, BrowseComp-Plus: четыре одинаковых агента отвечают верно на {fnum_d(MEM['shared'])}% вопросов с общим хранилищем, на {fnum_d(MEM['private'])}% с личными и на {fnum_d(MEM['none'])}% без хранилища; равное число агентов, а не равные вычисления. Прежняя абляция дала обратное: личная память чуть лучше, 49,43 против 48,62.")}

Это целевое обновление, а не систематический обзор и не повторение опытов; его границы описаны в разделе [«Об обзоре»](content/ru/about.md), а само датированное дополнение с реестром изменений, каталогом и BibTeX лежит в [`updates/2026-10-19/`](updates/2026-10-19/ru.md). Графики по {K['corpus']} работам аналитического корпуса и PDF остаются редакцией 3 октября.

## Где читать

- **Сайт** в `site/`: весь обзор одной непрерывной страницей, по-русски (`site/ru/index.html`) и по-английски (`site/en/index.html`), в тёмном оформлении, где каждый агент — окно контекста, нарисованное башней блоков (светлая тема включается одним переключателем). Он идёт от пролога — шесть агентов и три способа их связать — через три части и одиннадцать глав к выводам, открытым вопросам и атласу всех {fnum(K['cat'], 'ru')} работ и ресурсов с фильтрами, а за ними — словарик, источники и заметки о методе. По ходу текста механизмы и корпус объясняют встроенные схемы и графики. Это статические файлы: откройте `site/index.html` в браузере или запустите `python3 -m http.server -d site` и перейдите на `http://localhost:8000`.
- **Технический отчёт:** [PDF](paper/swarm-dynamics.pdf) в формате ACL (на английском), [исходник LaTeX](paper/main.tex), [архив исходников](paper/swarm-dynamics-source.zip) и [инструкция по сборке](paper/BUILD.md). Это редакция 3 октября 2026 года, дополнение в неё не входит.
- **Каталог:** [CATALOG.ru.md](CATALOG.ru.md) — все цитируемые работы по темам, по строке на работу, добавленные 19 октября помечены ([на английском](CATALOG.md)).
- **Данные:** [реестр работ](data/works.json) на 3 октября, его [BibTeX](data/bib/works.bib) и [происхождение рисунков](data/figures.json); в дополнении — [реестр изменений](updates/2026-10-19/registry-delta.json) и [каталог из {K['cat']} записей](updates/2026-10-19/catalogue.json); актуальный [BibTeX](site/data/references-2026-10-19.bib) каталога, с исправленным идентификатором.

В атласе {K['cat']} работ и ресурсов (каталог на 19 октября); графики обзора построены по {K['corpus']} работам аналитического корпуса с подробными метаданными (на 3 октября).

## Насколько велики настоящие рои

{picture("scale", "ru", f"Из {K['known']} работ, где названо число одновременно работающих агентов, медианный рой — {K['med']} агентов; " + "; ".join(f"не меньше {fnum(t, 'ru')} агентов — в {v}" for t, v in LD['rows']) + ".")}

Из этих {K['corpus']} работ {K['known']} называют число агентов, работающих одновременно; медиана — {K['med']}. Живые рои LLM из 10{' '}000 агентов и больше известны только по отчётам лабораторий без контрольного запуска, а контролируемые опыты в основном малы. Карта ниже показывает каждую работу по числу агентов и классу доказательств; в [главе 1](content/ru/ch01.md) разведены три смысла «размера роя»: агенты, работающие одновременно, участники за весь период и ёмкость платформы.

{chart("dash_scale", "ru", "Каждая работа корпуса по числу агентов (логарифмическая шкала) и классу доказательств; одновременное число, накопленный итог и заявленная ёмкость платформы отмечены по-разному.")}

## Один запуск в числах: 1 024 агента на pandoc

{picture("agensh-pandoc", "ru", "Доля пройденных скрытых тестов pandoc за 6 часов: 33,89 % у одного агента, 41,75 % у 8, 43,11 % у 32, 50,94 % у 128, 55,06 % у 1 024; черты — среднее по пяти задачам для 1–128 агентов (19,31, 20,68, 26,52 и 28,78 %).")}

В работе *Agensh: Scaling Organizational Intelligence to 1,024 Agents* исследователи Microsoft Research дали до 1{' '}024 одинаковых агентов GPT-5.6-sol без назначенного руководителя шесть часов на то, чтобы воссоздать pandoc, изучая готовую программу только по её запускам. Доля пройденных скрытых тестов выросла с 33,89{' '}% у одного агента до 55,06{' '}% у 1{' '}024. Уравнено было время, а не токены; команду из 1{' '}024 агентов проверяли только на pandoc. Подробный разбор и роли, возникшие в прогоне, — в [главе 5](content/ru/ch05.md).

## Главы

Ссылки ведут на Markdown-текст глав, который GitHub показывает как страницу; на сайте тот же текст идёт с рисунками, карточками и фильтрами.

{chapters("ru")}

[Десять выводов](content/ru/index.md) стоят в конце основного текста, перед открытыми вопросами. В разделе [«Об обзоре»](content/ru/about.md) описано, как собран корпус, а в [словарике](content/ru/glossary.md) — термины, которые обзор использует в узком смысле.

## Права

Текст, таблицы и данные — CC BY 4.0 ([LICENSE-CONTENT.md](LICENSE-CONTENT.md)), код сборки — MIT ([LICENSE](LICENSE)). Рисунки, воспроизведённые из работ (их {K['fig_works']}), остаются под правами владельцев и этими лицензиями не покрываются; условия по каждому — в [RIGHTS.md](RIGHTS.md).

## Как цитировать

{BIB}

См. также [CITATION.cff](CITATION.cff).

## Авторы

Антон Разжигаев задал рамку обзора, принимал редакционные решения и отвечает за публикацию. Ouroboros — система ИИ-агентов — собрала и прочитала источники, написала карточки, провела проверки и подготовила текст.

## Сборка

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium webkit
make site catalog check          # site/ и иллюстрации → CATALOG, RIGHTS, README → проверки текста
make coverage                    # каждая карточка, рисунок, ссылка и заголовок есть на единой странице (PREV=<прежний site/> сравнивает редакции)
make charts                      # по желанию: перерисовывает собственные графики главы 1 по данным; в репозитории лежат опубликованные PNG
make qa qa-features              # страница, рисунки, схемы и интерактив; компьютер/телефон, JavaScript и без него
```

Формат текста, порядок единой страницы и то, как прежние адреса страниц переходят на неё, описаны в [content/FORMAT.md](content/FORMAT.md); `scripts/check_content.py` проверяет, что русский и английский тексты совпадают блок в блок.

[English version](README.md)
"""

if __name__ == "__main__":
    site_story.write_illustrations()
    for name, text in (("README.md", EN), ("README.ru.md", RU)):
        assert "{" not in re.sub(r"```bibtex.*?```", "", text, flags=re.S), f"unfilled placeholder in {name}"
        for path in re.findall(r'(?:src|srcset)="([^"]+)"|\]\(((?!https?:)[^)#]+)', text):
            p = path[0] or path[1]
            assert os.path.exists(os.path.join(ROOT, p)), f"{name}: missing {p}"
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(text)
    print("README.md", len(EN), "README.ru.md", len(RU))

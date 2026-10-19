#!/usr/bin/env python3
"""Content coverage of the single page: nothing from the sources or from the former pages may go missing.

  python scripts/check_coverage.py                      # against content/ and data/
  python scripts/check_coverage.py --old qa/oldsite     # also against a build of the former multipage site
  python scripts/check_coverage.py --prev <dir>         # also against the previous single-page edition (a copy of its site/)
  python scripts/check_coverage.py --json out.json

Checks per language on site/<lang>/index.html:
  cards       every :::card / :::short id from content/<lang>/*.md is on the page exactly once (id="w-<id>")
  figures     every file in data/figures.json is on the page (image, or the static PNG behind a native chart)
  links       every external URL written in content/<lang>/*.md is a link on the page
  headings    every Markdown heading text is on the page
  blocks      timeline entries, related-work rows, glossary terms, atlas rows (one per record of the current catalogue,
              scripts/catalogue.py), source entries: counts match
  forwarding  every former page exists and forwards (checked by scripts/build_site.py --check)
With --old, against the former multipage build (index, ch01–ch11, atlas, glossary, sources, about):
  ids         every card, related-row, atlas-row and source id of the former pages exists on the single page
  hrefs       every external link of the former pages is on the single page
  text        every paragraph, list item, table cell and caption of the former pages' main content is on the page
              (whitespace-normalised); the few intentional removals are listed with their reason
With --prev, against the previous edition of the single page (<dir>/<lang>/index.html):
  ids, hrefs  every id and every external link of that page exists on the new one
  text        every paragraph, list item, table cell, caption and heading is still on the page, unless it is one of the
              corrections listed in PREV_CHANGED with its reason (a claim the 19 October supplement superseded, a sentence
              that gained a dated addition, a label that now carries its date)
Exit code 1 on any missing item.
"""
import argparse, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import catalogue
CATALOGUE = catalogue.works()        # 288 records: the registry of 3 October with the 19 October supplement
PAGES = [f"ch{n:02d}" for n in range(1, 12)] + ["index", "atlas", "glossary", "sources", "about"]

# Former index-page copy that the single page deliberately does not repeat (it restated the Agensh card in ch. 5).
INTENTIONAL = {
    "en": [("In “Agensh: Scaling Organizational Intelligence to 1,024 Agents”", "index Agensh case, first paragraph: restates the Agensh card the scene now follows in Ch. 5"),
           ("This goes further than spreading prompts across processes", "index Agensh case: restates the card's 'no boss, not no structure' paragraph"),
           ("In six hours a single agent passed 33.89% of pandoc's hidden tests", "index Agensh case: the result is in the card and in the chart right below"),
           ("The full card is in Chapter 5", "index Agensh case: links to the card and the two runs that now follow it on the same page"),
           ("How big real swarms are", "index scale section heading: Ch. 1 'How many agents there really are' now holds the dashboard"),
           ("Across the 153 works in the survey, “swarm” covers very different systems", "index scale lede: restated by Ch. 1 text and the dashboard's tabs"),
           ("Findings", "index section label; the findings keep their own heading in the epilogue"),
           ("Chapters", "index chapter-grid label; replaced by the route in the intro"),
           ("Eleven chapters and an atlas of works", "index chapter-grid heading; replaced by the route in the intro"),
           ("Bars show the share of the 99 works. The survey's count over 153 works, cut-off 3 October 2026; see Chapter 1", "the ladder now sits inside Chapter 1: the sentence is kept, its pointer to Chapter 1 dropped")],
    "ru": [("В работе «Agensh: Scaling Organizational Intelligence to 1,024 Agents»", "разбор Agensh с прежней главной, первый абзац: повторяет карточку Agensh в гл. 5"),
           ("Это интереснее простого распределения промптов по процессам", "разбор Agensh: повторяет абзац карточки"),
           ("За шесть часов одиночный агент дошёл до 33,89", "разбор Agensh: результат есть в карточке и на графике ниже"),
           ("Подробный разбор — в главе 5", "разбор Agensh: ссылки на карточку и два запуска, которые теперь идут следом"),
           ("Насколько велики настоящие рои", "заголовок раздела масштаба с прежней главной: его место занял дашборд в гл. 1"),
           ("В 153 работах обзора под роем понимают очень разные системы", "вводка раздела масштаба: её повторяют текст гл. 1 и вкладки дашборда"),
           ("Выводы", "метка раздела прежней главной"), ("Главы", "метка сетки глав прежней главной; её заменил маршрут во вступлении"),
           ("Одиннадцать глав и атлас работ", "заголовок сетки глав прежней главной; его заменил маршрут во вступлении"),
           ("Полоса — доля от 99 работ. Расчёт обзора по 153 работам, срез 3 октября 2026 — глава 1", "лесенка теперь стоит в главе 1: фраза сохранена без ссылки на главу 1")],
}
INTENTIONAL_HREF = {"https://arxiv.org/html/2609.26781v1": "HTML version of the Agensh paper from the index case's closing paragraph; the card and the chart's source line link the same paper (arXiv:2609.26781)"}
REASON = "former index-page copy the single page does not repeat"

# Texts of the previous single-page edition (cut-off 3 October 2026) that this edition changes on purpose. Each entry is
# the start of the old text and the reason; anything else missing fails --prev.
SUP = "superseded by the 19 October 2026 supplement"
PREV_CHANGED = {
 "en": [("LLM agent swarms · a survey of 153 works, 2025–2026", "the former prologue's eyebrow; the title screen now carries the cover's kicker with both dates"),
        ("01 · Independent 02 · Through a coordinator 03 · Through shared memory", "the former stage caption joined the three scheme names and their beats in one block; each beat now has its own step (every sentence is still on the page)"),
        ("works in the analytic corpus", "label now says what the corpus is and gives its date: works behind the survey's charts (as of 3 October)"),
        ("cards: 31 full and 118 short", "the card count now includes the 8 short cards of the 19 October supplement (31 full and 126 short)"),
        ("Cut-off: 3 October 2026 Authors: Anton Razzhigaev, Ouroboros", "the cover's meta line gained the supplement date"),
        ("17 short cards", "chapter card count now includes the 19 October cards"), ("11 short cards", "chapter card count now includes the 19 October cards"),
        ("14 short cards", "chapter card count now includes the 19 October cards"), ("≈ 35 min read", "reading time recomputed after the 19 October additions"),
        ("The number of agents can move three different things", "Chapter 4's introduction names the new section on where extra compute goes"),
        ("Communication raises the final result where intermediate progress is verifiable", "Chapter 4 takeaway gained the Cohere result (19 October)"),
        ("The shared context is at the top (or on the left); agent 17's working steps", "description of the former Agensh timeline figure; the room now draws agent 17's window as a tower and describes it in its own title"),
        ("In the 1,024-agent run the board accumulated 148,079 entries, 56,472 of them FAIL", "the same counts are now the room's replay figures (148,079 entries, 56,472 FAIL)"),
        ("If equal agents do not find a good structure during the task", "Chapter 5's learned-organization introduction names the market of bids (19 October)"),
        ("A second difficulty for swarm memory is not length but distribution", SUP + ": there are now two direct comparisons of shared and private memory, on different tasks"),
        ("Memory can also be kept outside the agents", "Chapter 6's population-memory introduction names the UCLA work (19 October)"),
        ("To Eun Kim, Fernando Diaz, Negar Arabzadeh and colleagues at CMU and Berkeley", "MATM card corrected with version 2 (Appendix H): a skewed index is not equally skewed retrieval"),
        ("Open: no work measures how swarm memory grows with the number of participants", SUP + ": the 'only direct comparison' claim is replaced by the two comparisons and the corrected synthesis"),
        ("Safety of Latent Communication CISPA, September 2026", "related-work row tracks version 3 and the three authors; the 27.9 → 76.9 result is marked as already in version 2"),
        ("09.2026 Safety of Latent Communication CISPA, September 2026", "the same row in the atlas"),
        ("Each finding is stated for the corpus as of 3 October 2026", "the findings note says where the supplement refines a finding"),
        ("Does a trained swarm beat one long-running agent at equal tokens?", "Chapter 11, question 2: notes that learned self-orchestration is compared at equal training, not answer, cost"),
        ("How does swarm memory behave with hundreds of agents and a shared store?", SUP + ": Chapter 11, question 4 no longer speaks of a single comparison"),
        ("How much of the collective effects is dynamics, and how much is the prompt?", "Chapter 11, question 8 adds the collective-risk dilemma's objective control"),
        ("Atlas · 280 works and resources", "the atlas now lists the 288 records of the catalogue with the supplement"),
        ("The list below is built from the cards and the related-work rows, in chapter order.", "the sources note points to the supplement"),
        ("Every work cited in the cards and related-work tables, grouped by chapter.", "the sources lead dates its exceptions: rows whose note records a later change, such as the 19 October supplement's"),
        ("To Eun Kim, Xuhong He, Dishank Jain, Ambuj Agrawal, Negar Arabzadeh et al. (6 authors). Multi-Agent Transactive Memory", "source entry tracks version 2"),
        ("CISPA, September 2026. Safety of Latent Communication", "source entry now names the three authors and tracks version 3"),
        ("Cut-off: 3 October 2026. Later preprint versions, reviews and prize decisions are not in the text", "About: the cut-off now mentions the supplement"),
        ("Cards: 31 full and 118 short; plus 100 rows", "About: the card counts are dated and the supplement's cards and catalogue size are added")],
 "ru": [("Рои LLM-агентов · обзор 153 работ 2025–2026", "надпись над прежним прологом; титульный экран теперь несёт надпись обложки с обеими датами"),
        ("01 · Независимо 02 · Через координатора 03 · Через общую память", "подпись прежней сцены объединяла названия трёх схем и их шаги; теперь у каждого шага свой экран (все фразы на странице)"),
        ("работ в аналитическом корпусе", "подпись объясняет, что это за корпус, и даёт дату: работы, по которым посчитаны графики (на 3 октября)"),
        ("карточек: 31 подробных и 118 кратких", "счёт карточек включает 8 кратких карточек дополнения 19 октября (31 и 126)"),
        ("Срез: 3 октября 2026 Авторы: Anton Razzhigaev, Ouroboros", "строка обложки получила дату дополнения"),
        ("17 кратких", "счёт карточек главы включает карточки 19 октября"), ("11 кратких", "счёт карточек главы включает карточки 19 октября"),
        ("14 кратких", "счёт карточек главы включает карточки 19 октября"),
        ("Число агентов может сдвинуть три разные вещи", "вводка главы 4 называет новый раздел о том, куда направить добавочные вычисления"),
        ("Общение поднимает итог там, где промежуточный прогресс проверяем", "итог главы 4 дополнен результатом Cohere (19 октября)"),
        ("Сверху или слева — общий контекст, снизу или справа — рабочий шаг агента 17", "описание прежнего рисунка Agensh со шкалой времени; комната рисует окно агента 17 башней и описывает его в своём заголовке"),
        ("В прогоне на 1 024 агента на доске накопилось 148 079 записей", "те же числа теперь стоят в комнате крупными цифрами реплея (148 079 записей, 56 472 FAIL)"),
        ("Если равные агенты по ходу задачи не находят хорошей структуры", "вводка о выученной организации в главе 5 называет рынок ставок (19 октября)"),
        ("Вторая трудность роевой памяти — не длина, а распределённость", "заменено дополнением 19 октября: прямых сравнений общей и личной памяти теперь два, на разных задачах"),
        ("Память можно держать и вне агентов", "вводка о памяти популяции в главе 6 называет работу UCLA (19 октября)"),
        ("Ким, Диас, Арабзаде и соавторы из CMU и Berkeley", "карточка MATM исправлена по версии 2 (приложение H): перекошенный индекс не означает столь же перекошенного чтения"),
        ("Открыто: ни одна работа не измеряет, как память роя растёт", "заменено дополнением 19 октября: тезис о «единственном прямом сравнении» заменён двумя сравнениями и уточнённым выводом"),
        ("Safety of Latent Communication CISPA, сентябрь 2026", "строка «Ещё по теме» учитывает версию 3 и трёх авторов; результат 27,9 → 76,9 отмечен как бывший уже в версии 2"),
        ("09.2026 Safety of Latent Communication CISPA, сентябрь 2026", "та же строка в атласе"),
        ("Каждый вывод сформулирован для корпуса на 3 октября 2026", "примечание к выводам говорит, где дополнение уточняет вывод"),
        ("Побеждает ли обученный рой одного долгого агента при равных токенах?", "глава 11, вопрос 2: выученная самооркестровка сравнена при равных затратах обучения, а не ответа"),
        ("Как ведёт себя память роя при сотнях агентов и общем хранилище?", "заменено дополнением 19 октября: вопрос 4 главы 11 больше не говорит о единственном сравнении"),
        ("Сколько в коллективных эффектах динамики, а сколько промпта?", "вопрос 8 главы 11 добавляет контроль формулировки цели из дилеммы коллективного риска"),
        ("Атлас · 280 работ и ресурсов", "атлас перечисляет 288 записей каталога с дополнением"),
        ("Список ниже собирается из карточек и строк «Ещё по теме», в порядке глав.", "примечание к источникам указывает на дополнение"),
        ("Все работы из карточек и таблиц «Ещё по теме», по главам.", "вводка к источникам называет исключения из даты статуса: строки с примечанием о более позднем изменении, например из дополнения 19 октября"),
        ("To Eun Kim, Xuhong He, Dishank Jain, Ambuj Agrawal, Negar Arabzadeh и др. (всего 6). Multi-Agent Transactive Memory", "запись источника учитывает версию 2"),
        ("Muhammad Huzaifa, Sina Mavali, Thorsten Eisenhofer (3 автора). Safety of Latent Communication", "запись источника называет трёх авторов отдельно и учитывает версию 3"),
        ("Срез: 3 октября 2026 года. Более поздние версии препринтов, рецензии и решения о премиях в текст не входят", "«Об обзоре»: срез упоминает дополнение"),
        ("Карточки: 31 подробных и 118 кратких; ещё 100 строк", "«Об обзоре»: счёт карточек датирован, добавлены карточки дополнения и размер каталога")],
}
# ids of the previous page that were internals of its prologue and Agensh figures, not addresses
PREV_INTERNAL_IDS = {"stage-cap": "caption element of the former prologue stage", "tip": "tooltip element of the former Agensh line chart",
                     "chn-d": "screen-reader description of the former Agensh timeline figure; the room's figure carries its own"}


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = s.replace(" ", " ").replace(" ", " ").replace(" ", " ").replace("‑", "-")   # non-breaking spaces and hyphen (dated labels) are the same text
    return re.sub(r"\s+", " ", s).strip()


def read(p):
    return open(p, encoding="utf-8").read()


def page_text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return norm(h)


def md_files(lang):
    d = os.path.join(ROOT, "content", lang)
    return {f[:-3]: read(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".md")}


def heading_text(m):
    return norm(re.sub(r"[*_`]", "", re.sub(r"\s*\{:[^}]*\}\s*$", "", m)))   # attr_list marks ({: .upd }) are not text


def check_lang(lang, old, prev=None):
    R = {"lang": lang, "missing": {}, "counts": {}}
    h = read(os.path.join(SITE, lang, "index.html"))
    text = page_text(h)
    ids = re.findall(r'\sid="([^"]+)"', h)
    idset = set(ids)
    hrefs = set(html.unescape(x) for x in re.findall(r'href="([^"]+)"', h))
    srcs = set(re.findall(r'(?:src|href|data-full|data-full-light)="([^"]+)"', h))
    md = md_files(lang)
    # cards
    cards = [cid for t in md.values() for cid in re.findall(r"^:::(?:card|short)\s+(\S+)", t, re.M)]
    R["counts"]["cards"] = len(cards)
    R["missing"]["cards"] = [c for c in cards if ids.count("w-" + c) != 1]
    # figures
    figs = json.load(open(os.path.join(ROOT, "data", "figures.json"), encoding="utf-8"))["figures"]
    miss = []
    for f in figs:
        name = f["file"]
        if name.startswith("dash_"):
            base = name.replace("_dark.png", "")
            if not any(s.endswith(f"{base}_{lang}_dark.png") for s in srcs): miss.append(name)
        elif not any(s.endswith("/" + name) for s in srcs): miss.append(name)
    R["counts"]["figures"] = len(figs); R["missing"]["figures"] = miss
    # external links written in the Markdown
    urls = set()
    for t in md.values():
        for u in re.findall(r"\]\((https?://[^)\s]+)\)", t): urls.add(u)
    R["counts"]["links"] = len(urls)
    R["missing"]["links"] = sorted(u for u in urls if u not in hrefs)
    # headings
    heads = [heading_text(m) for t in md.values() for m in re.findall(r"^#{2,4}\s+(.+)$", t, re.M)]
    R["counts"]["headings"] = len(heads)
    R["missing"]["headings"] = [x for x in heads if x not in text]
    # blocks
    tl = sum(len([l for l in b.split("\n") if l.strip()]) for t in md.values() for b in re.findall(r"^:::timeline\n(.*?)\n:::", t, re.M | re.S))
    rel = sum(max(0, len([l for l in b.split("\n") if l.strip().startswith("|")]) - 2) for t in md.values() for b in re.findall(r"^:::related\n(.*?)\n:::", t, re.M | re.S))
    gl = len(re.findall(r"^- \*\*", md.get("glossary", ""), re.M))
    R["counts"].update(timeline_md=tl, timeline_page=h.count('<ol class="timeline">') and len(re.findall(r'<ol class="timeline">.*?</ol>', h, re.S)) and sum(x.count("<li>") for x in re.findall(r'<ol class="timeline">.*?</ol>', h, re.S)),
                       related_md=rel, related_page=sum(x.count("<li") for x in re.findall(r'<ul class="related">.*?</ul>', h, re.S)),
                       glossary_md=gl, atlas_rows=h.count('class="w" id="a-'), sources=len(re.findall(r'<li id="s-', h)))
    bad = []
    if R["counts"]["timeline_md"] != R["counts"]["timeline_page"]: bad.append("timeline")
    if R["counts"]["related_md"] != R["counts"]["related_page"]: bad.append("related")
    if R["counts"]["atlas_rows"] != len(CATALOGUE): bad.append("atlas")
    R["missing"]["blocks"] = bad
    # against the former multipage build
    if old:
        oids, ohrefs, otexts = set(), set(), []
        for p in PAGES:
            fp = os.path.join(old, lang, p + ".html")
            if not os.path.exists(fp): continue
            t = read(fp)
            m = re.search(r'<main id="main"[^>]*>(.*?)</main>', t, re.S)
            body = m.group(1) if m else t
            for i in re.findall(r'\sid="((?:w|a|src)-[^"]+|s-[a-z][^"]*)"', body): oids.add(i)
            for u in re.findall(r'href="(https?://[^"]+)"', body): ohrefs.add(html.unescape(u))
            body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", body, flags=re.S)
            # page chrome of the former pages (pager, back-to-top, reading time, expand-all, the index's chapter grid and buttons) is not content
            for rx in (r'<p class="chend">.*?</p>', r'<ul class="chmeta">.*?</ul>', r'<p class="cta">.*?</p>', r'<nav class="pager".*?</nav>',
                       r'<section class="sec chmap".*?</section>', r'<span class="fnum">.*?</span>', r'<a class="orig"[^>]*>.*?</a>'):
                body = re.sub(rx, " ", body, flags=re.S)
            for blk in re.findall(r"<(p|li|td|th|dd|dt|figcaption|h[1-4]|time)(?:\s[^>]*)?>(.*?)</\1>", body, re.S):
                s = norm(blk[1])
                if len(s) >= 3: otexts.append((p, s))
        R["counts"]["old_ids"] = len(oids); R["counts"]["old_hrefs"] = len(ohrefs); R["counts"]["old_texts"] = len(otexts)
        R["missing"]["old_ids"] = sorted(i for i in oids if i not in idset)
        R["missing"]["old_hrefs"] = sorted(u for u in ohrefs if u not in hrefs and u not in INTENTIONAL_HREF)
        R["intentional_hrefs"] = {u: r for u, r in INTENTIONAL_HREF.items() if u in ohrefs and u not in hrefs}
        lost, intentional = [], []
        seen = set()
        for p, s in otexts:
            if s in seen: continue
            seen.add(s)
            if s in text: continue
            why = next((r for x, r in INTENTIONAL[lang] if s == x or (len(x) > 20 and s.startswith(x))), None)
            if why: intentional.append((p, s[:90], why)); continue
            lost.append((p, s[:200]))
        R["missing"]["old_text"] = lost
        R["intentional"] = {"reason": REASON, "items": intentional}
    if prev:
        p = read(os.path.join(prev, lang, "index.html"))
        m = re.search(r'<main id="main"[^>]*>(.*?)</main>', p, re.S)
        body = m.group(1) if m else p
        pids = set(re.findall(r'\sid="([^"]+)"', re.sub(r"<(svg|script)[^>]*>.*?</\1>", " ", body, flags=re.S))) - set(PREV_INTERNAL_IDS)   # SVG and script internals are not addresses
        phrefs = set(html.unescape(u) for u in re.findall(r'href="(https?://[^"]+)"', body))
        body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", body, flags=re.S)
        ptexts = []
        for blk in re.findall(r"<(p|li|td|th|dd|dt|figcaption|h[1-5]|time)(?:\s[^>]*)?>(.*?)</\1>", body, re.S):
            s_ = norm(blk[1])
            if len(s_) >= 3 and s_ not in ptexts: ptexts.append(s_)
        R["counts"].update(prev_ids=len(pids), prev_hrefs=len(phrefs), prev_texts=len(ptexts))
        R["missing"]["prev_ids"] = sorted(i for i in pids if i not in idset)
        R["missing"]["prev_hrefs"] = sorted(u for u in phrefs if u not in hrefs)
        changed, lost = [], []
        for s_ in ptexts:
            if s_ in text: continue
            why = next((r for x, r in PREV_CHANGED[lang] if s_ == x or (len(x) > 24 and s_.startswith(x))), None)
            (changed if why else lost).append((s_[:110], why) if why else s_[:220])
        R["missing"]["prev_text"] = lost
        R["prev_changed"] = changed
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default=None)
    ap.add_argument("--prev", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    out = [check_lang(l, a.old, a.prev) for l in ("en", "ru")]
    fail = False
    for R in out:
        print(f"[{R['lang']}] counts: " + ", ".join(f"{k}={v}" for k, v in R["counts"].items()))
        for k, v in R["missing"].items():
            if v:
                fail = True
                print(f"  MISSING {k}: {len(v)}")
                for x in v[:12]: print("    -", x)
        if R.get("prev_changed"):
            print(f"  changed since the previous edition, each with its reason: {len(R['prev_changed'])}")
            for x, why in R["prev_changed"]: print(f"    ~ {x[:80]} — {why}")
        if R.get("intentional"):
            print(f"  intentional removals: {len(R['intentional']['items'])} ({R['intentional']['reason']})")
    if a.json: json.dump(out, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("coverage:", "FAIL" if fail else "OK")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

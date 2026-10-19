#!/usr/bin/env python3
"""The prologue of the single page and the README illustrations, in the B «Контекст» design.

Every agent is a context window drawn as a tower of blocks. scripts/build_site.py takes the title screen (hero_html), the
prologue (stage_html: six agents and three ways to connect them, then the scale of real swarms), the state rules for the
stage (state_css) and the Agensh figures (board_svg, bars_svg, proto_svg, used by scripts/scenes_mech.py);
scripts/build_readme.py takes the standalone SVG posters and charts (no script, fonts or network).
Standard library only. Every number here is either computed from data/works.json (the analytic corpus as of the
3 October 2026 cut-off) or quoted from a card whose anchor is linked next to it. The approved exemplars this grew out of,
prototype-v2/ and design-20261019/ (direction B), stay unchanged.
"""
import html
import json
import math
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB = "\u00a0"


def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def esc(s):
    return html.escape(str(s), quote=True)


def fnum(v, lang, dec=None):
    """1024 -> '1 024' / '1,024'; 33.89 -> '33,89' / '33.89'."""
    if dec is None:
        dec = 0 if float(v) == int(v) else 2
    s = f"{v:,.{dec}f}"
    if lang == "ru":
        s = s.replace(",", NB).replace(".", ",")
    return s


# ---------------------------------------------------------------- text
T = {
 "ru": dict(
    agent="агент {k}",
    lane_w="у каждого свой контекст · канала между агентами нет", lane_n="свой контекст у каждого · канала нет",
    sel="отбор", sel1="голосование", sel2="или лучший из N",
    hub="координатор", hub_m="контекст заполняется",
    log="общий журнал", log_s="только добавление",
    rows=[(6, "беру таблицы", False), (4, "тест сносок падает", False), (3, "находка: редкий случай", True)],
    live={"t6": "таблицы: тесты прошли", "t3": "находка: редкий случай", "t2": "беру сноски", "t4": "сноски: не вышло"},
    tags=[("src", "нашёл"), ("redo", "сам, заново"), ("got", "получил"), ("ask", "спросил журнал"), ("done", "закончил")],
    stage_t="Шесть агентов и три способа их связать",
    stage_d=("Одни и те же шесть агентов. Независимо: у каждого своя дорожка, находка агента 3 остаётся у него, агенты 1 и 5 доходят до неё сами, "
             "ответы сходятся только на отборе. Через координатора: все связи ведут к центральному узлу, он пересылает находку агента 3 агентам 1 и 5. "
             "Через общую память: агент 3 записывает находку в журнал, агенты 1 и 5 находят её, когда спрашивают журнал."),
    eyebrow="Рои LLM-агентов · обзор {corpus}{nb}работ 2025–2026",
    h1="Один агент нашёл решение. <span>Как о нём узнают остальные?</span>",
    deck="Шесть копий одной модели, одна находка. Меняется канал между ними: его нет, он проходит через координатора или через общий журнал. Агент{nb}3 нашёл решение, нужное агентам{nb}1 и{nb}5.",
    modes_legend="Схема связи между агентами", pause="Пауза", play="Продолжить",
    modes=[
      ("ind", "01", "Независимо", "канала нет",
       "Каждый работает в своём контексте. Находка остаётся у автора, остальные доходят до неё сами — или нет. Ответы сводят в конце: голосованием или выбором лучшего из N.",
       "Университет Висконсина в Мадисоне: по семи наборам задач голосование пяти независимых ответов даёт 0,769, лучший вариант дебатов тех же агентов — 0,738 (Qwen2.5-7B).", "debate-or-vote", "гл.{nb}4"),
      ("coord", "02", "Через координатора", "всё через один узел",
       "Агенты пишут только координатору, он решает, кому что переслать. Вся картина — в одном контексте: в этом сила схемы и её предел.",
       "Google Research, DeepMind и MIT, команды из трёх агентов при общем бюджете токенов: у координатора на 285{nb}% больше шагов рассуждения, чем у одиночки; в финансовом анализе 63,1{nb}% против 34,9{nb}%, на исправлении кода все команды хуже одного агента.",
       "kim-scaling-agent-systems", "гл.{nb}4"),
      ("mem", "03", "Через общую память", "журнал, который надо спросить",
       "Находку записывают в общий журнал, и она остаётся там, даже когда автор закончил работу. Узнаёт её тот, кто спросил.",
       "Так устроена доска в Agensh у Microsoft Research — с одним отличием: новые записи там ещё и приходят агентам сами, на границах вызовов инструментов.",
       None, "Разбор ниже"),
    ],
    beats={
      "ind": ["Шесть копий одной модели, одна задача. У каждого свой контекст, канала между ними нет.",
              "Агент 3 нашёл решение. Передать его некому.",
              "Агенты 1 и 5 доходят до того же сами — одна и та же работа сделана трижды.",
              "Ответы встречаются только в конце: на голосовании или при выборе лучшего из N."],
      "coord": ["Все каналы ведут к координатору. Напрямую агенты друг другу не пишут.",
                "Агент 3 нашёл решение и отправляет его координатору.",
                "Координатор решает, кому оно нужно, и пересылает агентам 1 и 5.",
                "Остальные не узнали — если координатор прав, им и не нужно. А его контекст тем временем заполняется."],
      "mem": ["Общий журнал: записи только добавляются. Рассылки нет — новое узнаёт тот, кто спросил.",
              "Агент 3 записывает находку в журнал.",
              "Агенты 1 и 5 перед следующим шагом ищут по журналу — и находят запись.",
              "Агент 3 уже закончил работу, а запись осталась. Кто журнал не спрашивал, о находке не знает."],
    },
    # scale
    sc_eyebrow="Масштаб", sc_h="Насколько велики настоящие рои",
    sc_lede=("В {corpus} работах обзора под роем понимают очень разные системы: небольшие команды в контролируемых опытах и десятки тысяч агентов в отчётах лабораторий. "
             "Здесь считается число агентов, которые работают одновременно в одном прогоне или системе; регистрации и участники за всё время — другая величина."),
    sc_unit="агентов — медианный рой. Посчитано по {known} из {corpus}{nb}работ: тем, что называют число одновременно работающих агентов.",
    sc_fig="Сколько из этих {known}{nb}работ описывают рой не меньше N агентов",
    sc_tip="{v} из {known}",
    sc_rows={
      10: ("<b>16</b> копий Claude Opus 4.6 две недели писали компилятор C в общем Git без переписки · Anthropic", "anthropic-c-compiler"),
      100: ("<b>100</b> копий Claude Opus 5.5 в системной карте Anthropic: 24 часа на доказательство теоремы в Lean или сбор базы знаний", "opus55-card"),
      1000: ("<b>1{nb}020</b> активных одновременно — пик Agensh: 1{nb}024{nb}участника, шесть часов, pandoc · Microsoft Research", "agensh-1024"),
      10000: ("<b>≈10{nb}000</b> агентов OpenAI на задаче Навье–Стокса, без контрольного запуска; ≈30{nb}000 на внутренней платформе Anthropic, на разных задачах. Ещё две работы на этом пороге — симуляции с политиками, заранее снятыми с модели", "openai-navier-stokes"),
    },
    sc_src="Полоса — доля от {known}{nb}работ. Расчёт обзора по {corpus} работам, срез 3 октября 2026 — <a href=\"{ch1_href}\">глава 1, «{ch1}»</a>.",
    sc_card="к карточке",
    # Agensh case
    ag_eyebrow="Разбор · Microsoft Research, сентябрь 2026", ag_h="Тысяча агентов без назначенного руководителя",
    ag_p1=[
      "В работе <span class=\"work\">«Agensh: Scaling Organizational Intelligence to 1,024 Agents»</span> исследователи Microsoft Research дали 1{nb}024{nb}копиям одной LLM шесть часов на воссоздание pandoc. Исходного кода у команды не было: поведение готовой программы можно было изучать, запуская её. Агенты получили Git, чат и общий журнал находок, но не руководителя, который распределял бы задачи.",
      "У каждого работника была своя ветка. Прежде чем писать код, он читал, что уже сделано, и оставлял в журнале <code>CLAIM</code>: за какую часть берётся. Совпали заявки — можно договориться в чате. Неудачная попытка попадала в <code>FAIL</code>, готовое изменение после проверки и слияния — в <code>PATCH_SUMMARY</code>, чтобы следующему агенту не приходилось восстанавливать ход работы по чужим диалогам.",
      "Здесь важны три разных канала. В Git хранится код и история изменений; в чате участники договариваются; общий контекст сохраняет находки и намерения. Новые записи приходят на границах обращений к инфраструктуре, старые можно найти поиском. Пока один агент работает в своей ветке, остальные продолжают менять общий проект.",
    ],
    ag_fig="Как запись с доски доходит до агента (схема)",
    ag_key=["Новые записи других агентов приходят сами, пачкой, на границе очередного обращения к инфраструктуре.",
            "Старые записи агент получает, только если ищет."],
    ag_note="В прогоне на 1{nb}024{nb}агента на доске накопилось 148{nb}079 записей, 56{nb}472 из них — <code>FAIL</code> (расчёт обзора по реплею прогона).",
    ag_h3="Кто будет собирать чужой код",
    ag_p2=[
      "В небольших командах авторы наблюдали договорённости об интерфейсах. В больших появились устойчивые связи с рецензентами и участники, которые брались за интеграцию чужих изменений. В прогоне на 128{nb}агентов двое договорились о протоколе: автор обновляет и тестирует ветку, затем передаёт хеш коммита коллеге для проверки и слияния. После неудач они пересмотрели договорённость и передали коллеге весь цикл обновления, проверки и merge. Другие агенты стали пользоваться тем же порядком.",
      "Это интереснее простого распределения промптов по процессам: участники меняли сам способ совместной работы. При этом стартовали они не с пустого листа. Общий промпт уже задавал цикл «прочитать контекст → выбрать задачу → сделать → проверить → слить». Роли и договорённости возникали внутри этой обвязки.",
      "За шесть часов одиночный агент дошёл до 33,89{nb}% скрытых тестов pandoc, команда из 1{nb}024 — до 55,06{nb}%. Время было одинаковым, токены — нет. Если у вас жёсткий срок, такой параллелизм выглядит полезным; чтобы судить об экономии, нужно отдельно сравнить расход. А для устройства собственного роя здесь есть конкретный вопрос: как проверенная правка одного агента становится доступна остальным — и кто отвечает за её интеграцию?",
    ],
    ag_chart="Доля пройденных скрытых тестов pandoc за 6{nb}часов, %",
    ag_vals="Значения по размерам команды",
    ag_src="Zhan et al., Microsoft Research, <a class=\"ext\" href=\"https://arxiv.org/abs/2609.26781\" rel=\"noopener\">arXiv:2609.26781</a> (2026), числа из рис. 1.",
    ag_cond="Условия сравнения",
    ag_dl=[("Задача", "Воссоздать pandoc без интернета, наблюдая только, как работает готовая программа. Метрика — доля пройденных скрытых тестов (ProgramBench)."),
           ("Уравнено", "<strong>Время: 6{nb}часов на команду любого размера.</strong> Токены не уравнены, итоговый расход не опубликован."),
           ("Агенты", "Одна модель GPT-5.6-sol в обвязке Copilot, один промпт на всех, распорядителя нет. Из 1{nb}024 одновременно активны до 1{nb}020."),
           ("Прогоны", "Команду из 1{nb}024 проверили только на pandoc; остальные четыре задачи — с командами до 128{nb}агентов.")],
    ag_more=("Подробный разбор — в <a href=\"{agensh}\">главе 5, «{ch5}»</a>; текст работы — <a class=\"ext\" href=\"https://arxiv.org/html/2609.26781v1\" rel=\"noopener\">arXiv 2609.26781</a>. "
             "Рядом — два других запуска равных агентов: <a href=\"{cc}\">16{nb}копий Claude Opus 4.6 на компиляторе C</a> и <a href=\"{opus}\">сотня Claude Opus 5.5 из системной карты Anthropic</a>."),
    # channels figure
    ch_t="Как записи общего контекста доходят до агента в Agensh",
    ch_d=("Сверху или слева — общий контекст, снизу или справа — рабочий шаг агента 17. Старые записи агент получает поиском, по запросу. "
          "Новые записи других агентов (CLAIM, FAIL, PATCH_SUMMARY) приходят ему сами, пачками, на границе каждого обращения к инфраструктуре: git, тесты, чат."),
    ch_board="общий контекст", ch_board_s="доска заявок и находок", ch_agent="агент 17", ch_agent_s="один из 1{nb}024", ch_calls="обращается к:",
    ch_old="раньше", ch_new="новые записи других агентов", ch_pull="старое — по запросу", ch_pull2=("старое —", "по запросу"),
    ch_push=["+3 записи", "+1 запись", "+1 запись"], ch_push_s="приходят сами", ch_b=["поиск", "git", "тесты", "чат"], ch_time="время",
    # line chart
    li_d="Доля пройденных скрытых тестов pandoc за 6 часов: 33,89 % у одного агента, 41,75 у 8, 43,11 у 32, 50,94 у 128, 55,06 у 1 024. Ось числа агентов логарифмическая.",
    li_axis="агентов в команде, логарифмическая шкала",
    li_pts=["1{nb}агент", "8 агентов", "32 агента", "128 агентов", "1{nb}024 агента"],
    li_rows=["1{nb}агент", "8", "32", "128", "1{nb}024"], pct="{nb}%",
    # poster
    po_t1="Один агент нашёл решение.", po_t2="Как о нём узнают остальные?",
    po_brand="Awesome Agent Swarms", po_brand2="· обзор {corpus} работ о роях LLM-агентов",
    po_leg=["знает о находке агента 3", "дошёл до неё сам, заново"],
    po_panels=[("ind", "01", "Независимо", "канала нет", "Находка остаётся у автора. Остальные доходят до неё сами; ответы сводит отбор."),
               ("coord", "02", "Через координатора", "всё через один узел", "Координатор решает, кому переслать, и держит всю картину в своём контексте."),
               ("mem", "03", "Через общую память", "журнал, который надо спросить", "Запись живёт в журнале и после автора. Узнаёт её тот, кто спросил.")],
    po_know={"ind": {3: "нашёл", 1: "заново", 5: "заново"}, "coord": {3: "нашёл", 1: "получил", 5: "получил"}, "mem": {3: "нашёл", 1: "спросил", 5: "спросил"}},
    po_rows=[(6, "беру таблицы", False), (4, "тест сносок падает", False), (3, "находка", True)],
    po_foot="Схема условная: шесть агентов, одна находка. Измерения — в обзоре: 11 глав, атлас работ, русская и английская версии.",
    po_desc=("Три схемы связи шести агентов. Независимо: находка агента 3 остаётся у него, агенты 1 и 5 доходят до неё сами, ответы сводит отбор. "
             "Через координатора: находка идёт к координатору, он пересылает её агентам 1 и 5. Через общую память: агент 3 записывает находку в журнал, агенты 1 и 5 находят её, когда спрашивают."),
    # README charts
    rs_t="Сколько агентов в настоящих роях", rs_s="{known} из {corpus} работ называют число одновременно работающих агентов; медиана — {med}",
    rs_axis="работ с роем не меньше N агентов",
    rp_t="Agensh: 1 024 агента на pandoc", rp_s="Доля пройденных скрытых тестов за 6 часов, %. Уравнено время, не токены.",
    rp_src="Zhan et al., Microsoft Research, arXiv:2609.26781 (2026), рис. 1",
 ),
 "en": dict(
    agent="agent {k}",
    lane_w="each has its own context · no channel between agents", lane_n="own context each · no channel",
    sel="selection", sel1="voting", sel2="or best of N",
    hub="coordinator", hub_m="context fills up",
    log="shared log", log_s="append-only",
    rows=[(6, "taking tables", False), (4, "footnote test fails", False), (3, "finding: rare edge case", True)],
    live={"t6": "tables: tests pass", "t3": "finding: rare edge case", "t2": "taking footnotes", "t4": "footnotes: no luck"},
    tags=[("src", "found it"), ("redo", "redid it"), ("got", "received"), ("ask", "asked the log"), ("done", "done")],
    stage_t="Six agents and three ways to connect them",
    stage_d=("The same six agents. Independent: each has its own lane; agent 3's finding stays with it, agents 1 and 5 reach it on their own, "
             "and the answers meet only at selection. Through a coordinator: every link leads to a central node, which forwards agent 3's finding to agents 1 and 5. "
             "Through shared memory: agent 3 writes the finding to a log, and agents 1 and 5 find it when they query the log."),
    eyebrow="LLM agent swarms · a survey of {corpus} works, 2025–2026",
    h1="One agent found the answer. <span>How do the others find out?</span>",
    deck="Six copies of one model, one finding. What changes is the channel between them: none, a coordinator, or a shared log. Agent{nb}3 has found what agents{nb}1 and{nb}5 need.",
    modes_legend="How the agents are connected", pause="Pause", play="Resume",
    modes=[
      ("ind", "01", "Independent", "no channel",
       "Each agent works in its own context. A finding stays with its author; the others reach it on their own, or never do. The answers are combined at the end, by voting or by picking the best of N.",
       "University of Wisconsin–Madison: across seven task sets, voting over five independent answers scores 0.769; the best debate variant among the same agents scores 0.738 (Qwen2.5-7B).", "debate-or-vote", "Ch.{nb}4"),
      ("coord", "02", "Through a coordinator", "everything goes through one node",
       "Agents write only to the coordinator, which decides what to forward to whom. The whole picture sits in one context: that is the scheme's strength and its limit.",
       "Google Research, DeepMind and MIT, three-agent teams under a shared token budget: the coordinator setup takes 285% more reasoning steps than a single agent; in financial analysis it scores 63.1% vs 34.9%, while on code repair every team does worse than one agent.",
       "kim-scaling-agent-systems", "Ch.{nb}4"),
      ("mem", "03", "Through shared memory", "a log you have to ask",
       "A finding is written to a shared log and stays there after its author has finished. Whoever asks learns it.",
       "This is how the board in Microsoft Research's Agensh works, with one difference: new entries there also reach the agents on their own, at tool-call boundaries.",
       None, "Case study below"),
    ],
    beats={
      "ind": ["Six copies of one model, one task. Each has its own context; there is no channel between them.",
              "Agent 3 finds the answer. There is no one to pass it to.",
              "Agents 1 and 5 work it out on their own: the same work, done three times.",
              "The answers meet only at the end, in a vote or when the best of N is picked."],
      "coord": ["Every channel leads to the coordinator. Agents never write to each other directly.",
                "Agent 3 finds the answer and sends it to the coordinator.",
                "The coordinator decides who needs it and forwards it to agents 1 and 5.",
                "The others never hear of it; if the coordinator is right, they don't need to. Meanwhile its context keeps filling up."],
      "mem": ["A shared log: entries are only ever appended. Nothing is broadcast; whoever asks learns what is new.",
              "Agent 3 writes the finding to the log.",
              "Before their next step, agents 1 and 5 search the log and find the entry.",
              "Agent 3 has finished, but its entry stays. An agent that never asks the log never learns of the finding."],
    },
    sc_eyebrow="Scale", sc_h="How big real swarms are",
    sc_lede=("Across the {corpus} works in the survey, “swarm” covers very different systems: small teams in controlled experiments and tens of thousands of agents in lab reports. "
             "Here we count agents that work at the same time in one run or system; registrations and all-time participants are a different quantity."),
    sc_unit="agents in the median swarm. Counted over the {known} of {corpus}{nb}works that state how many agents work at the same time.",
    sc_fig="How many of these {known}{nb}works describe a swarm of at least N agents",
    sc_tip="{v} of {known}",
    sc_rows={
      10: ("<b>16</b> copies of Claude Opus 4.6 spent two weeks writing a C compiler in a shared Git repository, without messaging each other · Anthropic", "anthropic-c-compiler"),
      100: ("<b>100</b> copies of Claude Opus 5.5 in Anthropic's system card: 24 hours to prove a theorem in Lean or build a knowledge base", "opus55-card"),
      1000: ("<b>1,020</b> active at once, the peak in Agensh: 1,024{nb}participants, six hours, pandoc · Microsoft Research", "agensh-1024"),
      10000: ("<b>≈10,000</b> OpenAI agents on Navier–Stokes, without a control run; ≈30,000 on Anthropic’s internal platform, on different tasks. The other two works at this threshold simulate policies extracted from the model in advance", "openai-navier-stokes"),
    },
    sc_src="Bars show the share of the {known}{nb}works. The survey's count over {corpus} works, cut-off 3 October 2026; see <a href=\"{ch1_href}\">Chapter 1, “{ch1}”</a>.",
    sc_card="to the card",
    ag_eyebrow="Case study · Microsoft Research, September 2026", ag_h="A thousand agents, no appointed leader",
    ag_p1=[
      "In <span class=\"work\">“Agensh: Scaling Organizational Intelligence to 1,024 Agents”</span>, researchers at Microsoft Research gave 1,024 copies of one LLM six hours to rebuild pandoc. The team had no source code; the only way to study the finished program was to run it. The agents got Git, a chat and a shared log of findings, but no leader to hand out the work.",
      "Each worker had its own branch. Before writing code, it read what had already been done and left a <code>CLAIM</code> in the log saying which part it was taking. If two claims collided, the agents could settle it in the chat. A failed attempt went into a <code>FAIL</code> entry; a finished change, once checked and merged, into a <code>PATCH_SUMMARY</code>, so the next agent would not have to reconstruct the work from other agents' conversations.",
      "Three different channels are at work here. Git holds the code and its history; the chat is where participants negotiate; the shared context keeps findings and intentions. New entries arrive at the boundaries of calls to the infrastructure, and older ones can be found by search. While one agent works in its branch, the others keep changing the shared project.",
    ],
    ag_fig="How a board entry reaches an agent (schematic)",
    ag_key=["New entries from other agents arrive on their own, in a batch, at the boundary of the next call to the infrastructure.",
            "Old entries reach the agent only if it searches for them."],
    ag_note="In the 1,024-agent run the board accumulated 148,079 entries, 56,472 of them <code>FAIL</code> (the survey's count from a replay of the run).",
    ag_h3="Who integrates the others' code",
    ag_p2=[
      "In small teams the authors saw agreements about interfaces. In larger ones, stable pairings with reviewers appeared, along with participants who took on integrating other agents' changes. In the 128-agent run, two agents agreed on a protocol: the author updates and tests the branch, then hands the commit hash to a colleague, who reviews and merges it. After failures they revised the deal and handed the colleague the whole cycle of updating, checking and merging. Other agents adopted the same procedure.",
      "This goes further than spreading prompts across processes: the participants changed the way they worked together. They did not start from a blank page, though. The shared prompt already prescribed the cycle “read the context → pick a task → do it → check it → merge it”, and roles and agreements emerged inside that harness.",
      "In six hours a single agent passed 33.89% of pandoc's hidden tests; the 1,024-agent team passed 55.06%. Time was held equal, tokens were not. Under a hard deadline this kind of parallelism looks useful; whether it saves anything is a separate comparison of spend. For anyone designing a swarm, the run poses a concrete question: how does one agent's verified change become available to the others, and who is responsible for integrating it?",
    ],
    ag_chart="Share of pandoc's hidden tests passed in 6{nb}hours, %",
    ag_vals="Values by team size",
    ag_src="Zhan et al., Microsoft Research, <a class=\"ext\" href=\"https://arxiv.org/abs/2609.26781\" rel=\"noopener\">arXiv:2609.26781</a> (2026), numbers from Fig. 1.",
    ag_cond="Comparison conditions",
    ag_dl=[("Task", "Rebuild pandoc without Internet access, only by observing how the finished program behaves. Metric: share of hidden tests passed (ProgramBench)."),
           ("Held equal", "<strong>Time: 6{nb}hours for a team of any size.</strong> Tokens were not matched, and total spend was not published."),
           ("Agents", "One model, GPT-5.6-sol, in the Copilot harness; one prompt for all; no dispatcher. Of the 1,024, up to 1,020 were active at once."),
           ("Runs", "The 1,024-agent team ran on pandoc only; the other four tasks used teams of up to 128 agents.")],
    ag_more=("The full card is in <a href=\"{agensh}\">Chapter 5, “{ch5}”</a>; the paper is <a class=\"ext\" href=\"https://arxiv.org/html/2609.26781v1\" rel=\"noopener\">arXiv 2609.26781</a>. "
             "Two other runs of peer agents sit next to it: <a href=\"{cc}\">16{nb}copies of Claude Opus 4.6 on a C compiler</a> and <a href=\"{opus}\">the hundred Claude Opus 5.5 agents from Anthropic's system card</a>."),
    ch_t="How shared-context entries reach an agent in Agensh",
    ch_d=("The shared context is at the top (or on the left); agent 17's working steps are at the bottom (or on the right). The agent gets old entries by searching, on request. "
          "New entries from other agents (CLAIM, FAIL, PATCH_SUMMARY) reach it on their own, in batches, at the boundary of each call to the infrastructure: git, tests, chat."),
    ch_board="shared context", ch_board_s="board of claims and findings", ch_agent="agent 17", ch_agent_s="one of 1,024", ch_calls="calls to:",
    ch_old="earlier", ch_new="new entries from other agents", ch_pull="old ones, on request", ch_pull2=("old ones,", "on request"),
    ch_push=["+3 entries", "+1 entry", "+1 entry"], ch_push_s="arrive on their own", ch_b=["search", "git", "tests", "chat"], ch_time="time",
    li_d="Share of pandoc's hidden tests passed in 6 hours: 33.89% with one agent, 41.75 with 8, 43.11 with 32, 50.94 with 128, 55.06 with 1,024. The agent-count axis is logarithmic.",
    li_axis="agents in the team, log scale",
    li_pts=["1 agent", "8 agents", "32 agents", "128 agents", "1,024 agents"],
    li_rows=["1{nb}agent", "8", "32", "128", "1,024"], pct="%",
    po_t1="One agent found the answer.", po_t2="How do the others find out?",
    po_brand="Awesome Agent Swarms", po_brand2="· a survey of {corpus} works on LLM agent swarms",
    po_leg=["knows agent 3's finding", "reached it again on its own"],
    po_panels=[("ind", "01", "Independent", "no channel", "The finding stays with its author. The others reach it on their own; selection combines the answers."),
               ("coord", "02", "Through a coordinator", "everything via one node", "The coordinator decides whom to tell and holds the whole picture in its context."),
               ("mem", "03", "Through shared memory", "a log you have to ask", "The entry outlives its author in the log. Whoever asks learns it.")],
    po_know={"ind": {3: "found it", 1: "again", 5: "again"}, "coord": {3: "found it", 1: "received", 5: "received"}, "mem": {3: "found it", 1: "asked", 5: "asked"}},
    po_rows=[(6, "taking tables", False), (4, "footnote test fails", False), (3, "finding", True)],
    po_foot="A schematic: six agents, one finding. The measurements are in the survey: 11 chapters, an atlas of works, English and Russian editions.",
    po_desc=("Three ways to connect six agents. Independent: agent 3's finding stays with it, agents 1 and 5 reach it on their own, and selection merges the answers. "
             "Through a coordinator: the finding goes to the coordinator, which forwards it to agents 1 and 5. Through shared memory: agent 3 writes the finding to a log, and agents 1 and 5 find it when they ask."),
    rs_t="How many agents real swarms have", rs_s="{known} of {corpus} works state how many agents work at once; the median is {med}",
    rs_axis="works with a swarm of at least N agents",
    rp_t="Agensh: 1,024 agents on pandoc", rp_s="Share of hidden tests passed in 6 hours, %. Time was held equal, not tokens.",
    rp_src="Zhan et al., Microsoft Research, arXiv:2609.26781 (2026), Fig. 1",
 ),
}


def tx(lang, key, **kw):
    s = T[lang][key]
    kw.setdefault("nb", NB)
    return s.format(**kw) if isinstance(s, str) else s


def sub_nb(s):
    return s.replace("{nb}", NB)


# ---------------------------------------------------------------- the B «Контекст» edition: texts of the hero and the stage
# The stage tells the prologue as context windows: every agent is a tower of blocks (its context), a finding is a lime
# block, work done again is coral, a copy that arrived is an outlined lime block. Texts of the three schemes are the ones
# above (modes, beats); the scale steps quote Chapter 1 and count data/works.json.
T["ru"].update(
    hero_lines=["Динамика", "роёв", "LLM-агентов"],
    hero_hook="Знание агента живёт в его контексте. Как находка одного попадает в контекст другого — и чем за это платят?",
    hero_cue="Листайте", hero_skip="К обзору",
    st_label="Канал между агентами",
    st_note="Схема механизма, не измерение: шесть агентов, одна находка; моменты и длительности условны.",
    st_titles={"ind": "01 · НЕЗАВИСИМО", "coord": "02 · ЧЕРЕЗ КООРДИНАТОРА", "mem": "03 · ЧЕРЕЗ ОБЩУЮ ПАМЯТЬ", "sky": "МАСШТАБ"},
    st_agent="агент{nb}{k}", st_agent_n="{k}", st_coord="коорд.",
    st_found="нашёл", st_again="заново", st_copy="копия", st_got="получил", st_asked="спросил", st_entry="запись", st_done="закончил",
    st_entry_of="находка агента{nb}3",
    st_select="отбор: голосование или лучший из N",
    st_fill="контекст координатора заполняется", st_fill_n="контекст заполняется",
    st_shelf="общий журнал · записи только добавляются",
    st_sky_cap="{n} работ по возрастанию числа одновременно работающих агентов", st_sky_cap_n="{n} работ · лог. шкала",
    st_sky_cap2="высота столбца — логарифмическая шкала · срез 3 октября 2026",
    st_median="медиана{nb}{v}", st_thr="≥{t} агентов — {c}", st_thr_n="≥{t}: {c}",
    st_marks={"anthropic-c-compiler": "компилятор C · 16", "opus55-card": "Opus 5.5 · 100", "agensh-1024": "Agensh · 1{nb}020",
              "openai-navier-stokes": "OpenAI · ≈10{nb}000", "anthropic-institute-pace": "Anthropic · ≈30{nb}000"},
    st_grid="1{nb}024 окна одной модели · 6 часов · pandoc", st_grid_n="1{nb}024 окна · 6 часов · pandoc",
    st_scale_label="Масштаб", st_scale_h="Шесть агентов на схеме. Сколько их в настоящих роях?",
    st_scale_p1="В {corpus} работах обзора (срез 3 октября 2026) роем называют всё — от пары агентов до десятков тысяч. {known} из них называют число агентов, которые работают одновременно в одном прогоне или системе. Медиана — {med}.",
    st_scale_thr="Пороги среди этих {known} работ: {thr}.",
    st_scale_p2=("Живых систем с 10{nb}000 и больше одновременных агентов две: рой OpenAI на задаче Навье–Стокса (порядка 10{nb}000) и внутренняя платформа Anthropic (около 30{nb}000, но на разных задачах). "
                 "Ещё две работы на этом пороге — популяции, где политики заранее сняты с модели."),
    st_scale_p3=("Самые большие числа отвечают на другой вопрос, чем «сколько агентов работало вместе в один момент»: 1,5 млн регистраций Moltbook — ёмкость платформы, "
                 "около 1{nb}200 участников доски в инциденте с Hugging Face — накопленный итог за всё окно наблюдения."),
    st_scale_gap="Контролируемые опыты в основном малы, а живые рои от 10{nb}000 агентов известны только по отчётам лабораторий без контрольного запуска.",
    st_scale_more="Три величины «размера роя» и каждая работа на одной карте — глава 1",
    st_grid_beat=("1{nb}024 одинаковых агента, шесть часов, ни одного назначенного руководителя. С открытыми данными таких запусков равных агентов в 2026 году два: "
                  "этот и шестнадцать копий Claude на компиляторе C."),
    st_grid_more="Разбор — в главе 5",
    ag_room_lead=("Рой до 1{nb}024 одинаковых агентов без распорядителя держится вместе и сам выдвигает роли. Как устроен канал между ними, "
                  "что измерили и что при этом не уравняли."),
    ag_bars_t="Доля пройденных скрытых тестов pandoc за 6 часов",
    ag_bars_axis="% скрытых тестов pandoc · у всех 6 часов", ag_bars_axis_n="% тестов pandoc · 6 часов",
    ag_bars_mean="среднее по 5 задачам", ag_bars_hours="агенто-часы относительно одного агента · лог. шкала · верхние оценки", ag_bars_hours_n="агенто-часы, ×",
    ag_bars_none="нет оценки",
    ag_bars_desc=("Доля пройденных скрытых тестов pandoc за 6 часов: 33,89% у 1 агента, 41,75% у 8, 43,11% у 32, 50,94% у 128, 55,06% у 1 024; черта — среднее по пяти задачам "
                  "(19,31, 20,68, 26,52 и 28,78% для 1, 8, 32 и 128 агентов). Ниже — агенто-часы относительно одного агента: около 117 у 128 агентов и около 800 у 1 024, "
                  "логарифмическая шкала, верхние оценки обзора."),
    ag_hours_note="Агенто-часы относительно одного агента — верхние оценки, расчёт обзора. Это не токены: расход токенов в работе не опубликован.",
    ag_board_t="Окно агента 17: что в него приходит",
    ag_board_desc=("Схема: окно агента 17 заполняется его собственными шагами; на каждой границе обращения к git, тестам или чату в него пачкой приходят новые записи доски — "
                   "CLAIM, FAIL, PATCH_SUMMARY; старую запись агент получает поиском."),
    ag_board_win="окно агента{nb}17", ag_board_board="доска", ag_board_batch="{b}: новые записи пачкой", ag_board_b=["git", "тесты", "чат"],
    ag_board_search="поиск: старая запись",
    ag_kinds=[("CLAIM", "k-claim", "за какую часть берусь"), ("FAIL", "k-fail", "попытка не удалась"), ("PATCH_SUMMARY", "k-patch", "изменение проверено и влито")],
    ag_board_note="Схема по описанию работы: как запись с доски доходит до агента. Число записей в пачке условно.",
    ag_proto_t="Протокол, о котором договорились двое из 128",
    ag_proto_desc=("Сначала автор обновляет и тестирует ветку и передаёт хеш коммита коллеге, тот проверяет и сливает. После неудач автор передаёт коллеге весь цикл: "
                   "коллега обновляет, проверяет и сливает."),
    ag_proto_rows=[("СНАЧАЛА", [("автор", "обновляет и тестирует ветку"), ("→", "хеш коммита"), ("коллега", "проверяет и сливает")]),
                   ("ПОСЛЕ НЕУДАЧ", [("автор", "передаёт весь цикл"), ("→", ""), ("коллега", "обновляет, проверяет и сливает")])],
    ag_proto_note="Порядок по описанию работы; другие агенты стали пользоваться тем же порядком.",
    ag_replay=[("11{nb}111", "pull-request'ов в прогоне на 1{nb}024 агента"), ("2{nb}800", "из них влито — 25%"), ("148{nb}079", "записей на доске"), ("56{nb}472", "из них — FAIL")],
    ag_replay_note="Реплей прогона на 1{nb}024 агента, расчёт обзора (из карточки выше).",
    sky_title_of="{t} — {v}",
    mem_t="Общая или личная память: те же четыре агента", mem_s="ScaleMAS (FAIR/Meta, Гарвард, 12 октября 2026): успешные ответы на BrowseComp-Plus, табл. 2",
    mem_labels=["общее хранилище", "личное у каждого", "без хранилища"],
    mem_note=("Равное число агентов (четыре Qwen3.5-9B), а не равные вычисления. Прежняя абляция (Scaling Teams or Time) дала обратное: "
              "личная память чуть лучше, 49,43 против 48,62. Дополнение 19 октября 2026."),
)
T["en"].update(
    hero_lines=["On the dynamics", "of LLM agent", "swarms"],
    hero_hook="An agent knows what is in its context. How does one agent's finding reach another agent's context, and what does that cost?",
    hero_cue="Scroll", hero_skip="To the survey",
    st_label="The channel between agents",
    st_note="A schematic of the mechanism, not a measurement: six agents, one finding; timings are illustrative.",
    st_titles={"ind": "01 · INDEPENDENT", "coord": "02 · THROUGH A COORDINATOR", "mem": "03 · THROUGH SHARED MEMORY", "sky": "SCALE"},
    st_agent="agent{nb}{k}", st_agent_n="{k}", st_coord="coord.",
    st_found="found", st_again="again", st_copy="copy", st_got="got it", st_asked="asked", st_entry="entry", st_done="done",
    st_entry_of="agent{nb}3's finding",
    st_select="selection: vote or best of N",
    st_fill="the coordinator's context fills up", st_fill_n="context fills up",
    st_shelf="shared log · append-only",
    st_sky_cap="{n} works, by the number of agents working at the same time", st_sky_cap_n="{n} works · log scale",
    st_sky_cap2="bar height on a log scale · cut-off 3 October 2026",
    st_median="median{nb}{v}", st_thr="≥{t} agents: {c}", st_thr_n="≥{t}: {c}",
    st_marks={"anthropic-c-compiler": "C compiler · 16", "opus55-card": "Opus 5.5 · 100", "agensh-1024": "Agensh · 1,020",
              "openai-navier-stokes": "OpenAI · ≈10,000", "anthropic-institute-pace": "Anthropic · ≈30,000"},
    st_grid="1,024 windows of one model · 6 hours · pandoc", st_grid_n="1,024 windows · 6 hours · pandoc",
    st_scale_label="Scale", st_scale_h="Six agents in the schematic. How many are there in real swarms?",
    st_scale_p1="Across the survey's {corpus} works (cut-off 3 October 2026), “swarm” means anything from a pair of agents to tens of thousands. {known} of them state how many agents work at the same time in one run or system. The median is {med}.",
    st_scale_thr="Thresholds among these {known} works: {thr}.",
    st_scale_p2=("There are two live systems with 10,000 or more agents at once: OpenAI's swarm on the Navier–Stokes problem (on the order of 10,000) and Anthropic's internal platform (about 30,000, but on different tasks). "
                 "The other two works at this threshold are populations whose policies were extracted from the model in advance."),
    st_scale_p3=("The biggest numbers answer a different question from “how many agents worked together at one moment”: Moltbook's 1.5 million registrations are a platform's capacity, "
                 "and the roughly 1,200 board participants in the Hugging Face incident are a total accumulated over the whole observation window."),
    st_scale_gap="Controlled experiments are mostly small, while live swarms of 10,000 agents or more are known only from lab reports without a control run.",
    st_scale_more="Three meanings of “swarm size”, and every work on one map: Chapter 1",
    st_grid_beat=("1,024 identical agents, six hours, no appointed leader. Among runs of equal agents with open data, 2026 has two: "
                  "this one and sixteen copies of Claude on a C compiler."),
    st_grid_more="The case study is in Chapter 5",
    ag_room_lead=("A swarm of up to 1,024 identical agents with no dispatcher holds together and puts forward roles on its own. How the channel between them works, "
                  "what was measured, and what was not held equal."),
    ag_bars_t="Share of pandoc's hidden tests passed in 6 hours",
    ag_bars_axis="% of pandoc's hidden tests · 6 hours for every team", ag_bars_axis_n="% of pandoc tests · 6 hours",
    ag_bars_mean="mean over 5 tasks", ag_bars_hours="agent-hours relative to one agent · log scale · upper estimates", ag_bars_hours_n="agent-hours, ×",
    ag_bars_none="no estimate",
    ag_bars_desc=("Share of pandoc's hidden tests passed in 6 hours: 33.89% with 1 agent, 41.75% with 8, 43.11% with 32, 50.94% with 128, 55.06% with 1,024; the tick is the mean over five tasks "
                  "(19.31, 20.68, 26.52 and 28.78% for 1, 8, 32 and 128 agents). Below, agent-hours relative to one agent: about 117 for 128 agents and about 800 for 1,024, "
                  "on a log scale, the survey's upper estimates."),
    ag_hours_note="Agent-hours relative to one agent are upper estimates, the survey's calculation. They are not tokens: the paper does not publish token use.",
    ag_board_t="Agent 17's window: what reaches it",
    ag_board_desc=("Schematic: agent 17's window fills with its own steps; at each boundary of a call to git, tests or chat, a batch of new board entries arrives in it — "
                   "CLAIM, FAIL, PATCH_SUMMARY; an old entry reaches the agent by search."),
    ag_board_win="agent{nb}17's window", ag_board_board="board", ag_board_batch="{b}: new entries in a batch", ag_board_b=["git", "tests", "chat"],
    ag_board_search="search: an old entry",
    ag_kinds=[("CLAIM", "k-claim", "the part I am taking"), ("FAIL", "k-fail", "an attempt that failed"), ("PATCH_SUMMARY", "k-patch", "a change checked and merged")],
    ag_board_note="A schematic after the paper's description of how a board entry reaches an agent. The number of entries per batch is illustrative.",
    ag_proto_t="The protocol two of the 128 agents agreed on",
    ag_proto_desc=("At first the author updates and tests the branch and hands the commit hash to a colleague, who reviews and merges it. After failures the author hands the colleague "
                   "the whole cycle: the colleague updates, checks and merges."),
    ag_proto_rows=[("AT FIRST", [("author", "updates and tests the branch"), ("→", "commit hash"), ("colleague", "reviews and merges")]),
                   ("AFTER FAILURES", [("author", "hands over the whole cycle"), ("→", ""), ("colleague", "updates, checks and merges")])],
    ag_proto_note="The order as the paper describes it; other agents then adopted the same procedure.",
    ag_replay=[("11,111", "pull requests in the 1,024-agent run"), ("2,800", "of them merged: 25%"), ("148,079", "entries on the board"), ("56,472", "of them FAIL")],
    ag_replay_note="Replay of the 1,024-agent run, the survey's count (from the card above).",
    sky_title_of="{t}: {v}",
    mem_t="Shared or private memory: the same four agents", mem_s="ScaleMAS (FAIR/Meta, Harvard, 12 October 2026): successful answers on BrowseComp-Plus, Table 2",
    mem_labels=["a shared store", "a private store each", "no store"],
    mem_note=("Equal team size (four Qwen3.5-9B agents), not equal compute. The earlier ablation (Scaling Teams or Time) found the opposite: "
              "private memory slightly better, 49.43 versus 48.62. Supplement of 19 October 2026."),
)


def nb(s):
    return s.replace("{nb}", NB)


# ---------------------------------------------------------------- the stage: one brick model for every state
# Every block of every tower lists the states in which it is visible and how it is painted there. The sticky stage
# switches data-s as the reader scrolls (assets/js/story.js); the same markup filtered to one state is the static figure
# for readers without JavaScript or with reduced motion.
STATES = ["ind-0", "ind-2", "ind-3", "coord-0", "coord-2", "coord-3", "mem-0", "mem-2", "mem-3", "sky-1", "sky-2", "sky-3"]
TOWER_STATES = [s for s in STATES if not s.startswith("sky")]
PAINT = ["lime", "copy", "redo", "over", "dim"]
COLS = [1, 2, 3, "C", 4, 5, 6]      # agents 1..3, the coordinator's slot, agents 4..6
NS = 16                             # block slots per window


def _plan():
    P = {}

    def base(n):
        return {t: {s: "own" for s in range(n[t - 1])} for t in range(1, 7)}
    P["ind-0"] = base([3, 4, 3, 3, 4, 3])
    st = base([5, 8, 6, 8, 5, 8]); st[3][5] = "lime"
    for t, top in ((1, 10), (5, 11)):
        for s in range(5, top):
            st[t][s] = "redo"
        st[t][top] = "copy"
    P["ind-2"] = st
    P["ind-3"] = {t: dict(v) for t, v in st.items()}
    st = base([3, 3, 3, 3, 3, 3]); st["C"] = {s: "own" for s in range(3)}; P["coord-0"] = st
    st = base([5, 6, 6, 6, 5, 6]); st[3][5] = "lime"; st[1][5] = "copy"; st[5][5] = "copy"
    st["C"] = {s: "own" for s in range(10)}; st["C"][6] = "lime"; P["coord-2"] = st
    st = base([8, 8, 8, 8, 8, 8]); st[3][5] = "lime"; st[1][5] = "copy"; st[5][5] = "copy"
    st["C"] = {s: ("over" if s >= 13 else "own") for s in range(NS)}; st["C"][6] = "lime"; P["coord-3"] = st
    P["mem-0"] = base([3, 3, 3, 3, 3, 3])
    st = base([6, 7, 7, 7, 6, 7]); st[3][5] = "lime"; st[1][6] = "copy"; st[5][6] = "copy"; P["mem-2"] = st
    st = base([8, 8, 7, 8, 8, 8]); st[3] = {s: "dim" for s in range(7)}; st[3][5] = "lime"; st[1][6] = "copy"; st[5][6] = "copy"; P["mem-3"] = st
    return P


PLAN = _plan()
GEOM = {
    "wide": dict(W=1000, H=880, X0=150, CW=90, GAP=26, BASE=716, SH=34, BH=27, LBL=26, TOPLBL=92),
    "narrow": dict(W=1000, H=1180, X0=44, CW=112, GAP=24, BASE=930, SH=46, BH=38, LBL=40, TOPLBL=118),
}
SKY_MARKS = ["anthropic-c-compiler", "opus55-card", "agensh-1024", "openai-navier-stokes", "anthropic-institute-pace"]


def sky_works(works=None):
    """The works of the analytic corpus that state how many agents work at the same time (cut-off 3 October 2026)."""
    out = []
    for w in (works or load_works()):
        c = w.get("corpus") or {}
        if w.get("in_analytic_corpus") and c.get("scale_kind") == "simultaneous" and isinstance(c.get("agents_max_simultaneous"), (int, float)):
            out.append(dict(w=w, id=w["id"], n=c["agents_max_simultaneous"]))
    out.sort(key=lambda x: (x["n"], x["id"]))
    return out


def stage_svg(var, lang, only=None, title_of=None, cls="st-svg"):
    """The whole stage in one geometry (wide or narrow); `only` filters it to one state (a static figure)."""
    L = T[lang]
    g = GEOM[var]
    W, H, X0, CW, GAP, BASE, SH, BH, LBL = g["W"], g["H"], g["X0"], g["CW"], g["GAP"], g["BASE"], g["SH"], g["BH"], g["LBL"]
    colx = {c: X0 + i * (CW + GAP) for i, c in enumerate(COLS)}
    sy = lambda s: BASE - (s + 1) * SH + (SH - BH)
    states = [only] if only else STATES
    sid = f"{var}-{only or 'dyn'}"
    o = []

    def k(cls_, on, inner, gid=None):   # gid: an id on the moving stage, where story.js times the group to a flight
        on_ = [s for s in on if s in states]
        if on_:
            ident = f' id="{sid}-{gid}"' if gid and not only else ""
            o.append(f'<g class="k {cls_}"{ident} data-on="{" ".join(on_)}">{inner}</g>')

    o.append(f'<svg class="{cls} v-{var}" viewBox="0 0 {W} {H}" data-s="{only or "ind-0"}" aria-hidden="true" focusable="false">')
    o.append(f'<defs><pattern id="g32-{sid}" width="16" height="16" patternUnits="userSpaceOnUse"><rect x="1.5" y="1.5" width="13" height="13" rx="2" class="gp"/></pattern></defs>')
    for c in COLS:
        x = colx[c]
        on = [s for s in TOWER_STATES if (c != "C" or s.startswith("coord"))]
        fh = NS * SH + 10
        lab = L["st_coord"] if c == "C" else nb((L["st_agent_n"] if var == "narrow" else L["st_agent"]).format(k=c, nb="{nb}"))
        k("frame" + (" fc" if c == "C" else ""), on,
          f'<rect class="fr" x="{x - 5}" y="{BASE - fh + 4}" width="{CW + 10}" height="{fh}" rx="6"/>'
          f'<text class="tl" x="{x + CW / 2}" y="{BASE - fh - 14}" text-anchor="middle">{esc(lab)}</text>')
    for c in COLS:
        x = colx[c]
        for s in range(NS):
            on, paint = [], {p: [] for p in PAINT}
            for st in TOWER_STATES:
                cell = PLAN[st].get(c, {}).get(s)
                if cell:
                    on.append(st)
                    if cell != "own":
                        paint[cell].append(st)
            on = [z for z in on if z in states]
            if not on:
                continue
            attrs = "".join(f' data-{p}="{" ".join(z for z in v if z in states)}"' for p, v in paint.items() if any(z in states for z in v))
            bid = f' id="{sid}-b{c}-{s}"' if not only else ""      # the moving stage names its blocks for the flights; static figures need no ids
            o.append(f'<rect class="k bk"{bid} style="--lv:{s}" x="{x}" y="{sy(s)}" width="{CW}" height="{BH}" rx="3" data-on="{" ".join(on)}"{attrs}/>')
    ybar = 100 if var == "wide" else 132
    k("sel", ["ind-3"], f'<rect class="selbar" x="{X0}" y="{ybar}" width="{colx[6] + CW - X0}" height="10" rx="5"/>'
      + "".join(f'<line class="sell" x1="{colx[t] + CW / 2}" y1="{ybar + 10}" x2="{colx[t] + CW / 2}" y2="{BASE - NS * SH - 12 - LBL - 10}"/>' for t in range(1, 7))
      + f'<text class="cap" x="{X0}" y="{ybar - 14}">{esc(L["st_select"])}</text>')

    def inlab(c, s_, text, on, dark):   # a label on block s_ of tower c; on the moving stage it waits for the block's flight
        k("bl", on, f'<text class="bin{" dk" if dark else ""}" x="{colx[c] + CW / 2}" y="{sy(s_) + BH * .5}" dy=".35em" text-anchor="middle">{esc(text)}</text>', f"l{c}-{s_}")
    found = [z for z in TOWER_STATES if z not in ("ind-0", "coord-0", "mem-0")]
    inlab(3, 5, L["st_found"], found, True)
    inlab(1, 10, L["st_again"], ["ind-2", "ind-3"], False)
    inlab(5, 11, L["st_again"], ["ind-2", "ind-3"], False)
    inlab("C", 6, L["st_copy"], ["coord-2", "coord-3"], True)
    inlab(1, 5, L["st_got"], ["coord-2", "coord-3"], False)
    inlab(5, 5, L["st_got"], ["coord-2", "coord-3"], False)
    inlab(1, 6, L["st_asked"], ["mem-2", "mem-3"], False)
    inlab(5, 6, L["st_asked"], ["mem-2", "mem-3"], False)
    if var == "wide":
        for t, top in ((1, 10), (5, 11)):
            x = colx[t] + CW + 8
            k("brace", ["ind-2", "ind-3"], f'<path class="brc" d="M{x},{sy(top - 1) + BH} h6 V{sy(5)} h-6"/>')
    cx = colx["C"] + CW / 2
    k("wires", ["coord-0", "coord-2", "coord-3"], "".join(f'<path class="wire" d="M{colx[t] + CW / 2},{BASE + 12} V{BASE + 34} H{cx} V{BASE + 12}"/>' for t in range(1, 7)))
    k("ovl", ["coord-3"], f'<text class="cap coral" x="{cx}" y="{BASE + (76 if var == "wide" else 92)}" text-anchor="middle">{esc(L["st_fill"] if var == "wide" else L["st_fill_n"])}</text>')
    sy0 = BASE + 40
    k("shelf-g", ["mem-0", "mem-2", "mem-3"], f'<rect class="shelf" x="{X0}" y="{sy0}" width="{colx[6] + CW - X0}" height="{BH + 16}" rx="6"/>'
      f'<text class="cap" x="{X0}" y="{sy0 + BH + 52}">{esc(L["st_shelf"])}</text>')
    rid = "" if only else f' id="{sid}-rec"'
    k("rec", ["mem-2", "mem-3"], f'<rect class="recb"{rid} x="{colx[3]}" y="{sy0 + 8}" width="{CW}" height="{BH}" rx="3"/>'
      f'<text class="bin dk" x="{colx[3] + CW / 2}" y="{sy0 + 8 + BH * .5}" dy=".35em" text-anchor="middle">{esc(L["st_entry"])}</text>'
      + (f'<text class="bt lime" x="{colx[3] + CW + 14}" y="{sy0 + 8 + BH * .72}">{esc(nb(L["st_entry_of"]))}</text>' if var == "wide" else ""))
    for t in (1, 5):   # agents 1 and 5 query the journal once the entry is in it
        k("beam", ["mem-2", "mem-3"], f'<line class="beamq" x1="{colx[t] + CW / 2}" y1="{BASE + 6}" x2="{colx[t] + CW / 2}" y2="{sy0 - 2}"/>', f"q{t}")
    k("done3", ["mem-3"], f'<text class="cap" x="{colx[3] + CW / 2}" y="{BASE - (8 * SH) - 22}" text-anchor="middle">{esc(L["st_done"])}</text>')
    # the skyline: the works of the analytic corpus that state a simultaneous count, sorted, on a log scale
    sky = ["sky-1", "sky-2"]
    SW = sky_works()
    nw = len(SW)
    sx0, sx1 = X0, colx[6] + CW
    bw = (sx1 - sx0) / nw
    top = 150 if var == "wide" else 190
    hmax = BASE - top
    HV = lambda v: (math.log10(v) + .35) / (math.log10(30000) + .35) * hmax
    med_i = (nw - 1) // 2
    for i, x_ in enumerate(SW):
        if not any(s in states for s in sky):
            break
        x = sx0 + i * bw
        h = HV(x_["n"])
        c_ = "sb" + (" med" if i == med_i else "") + (" mk" if x_["id"] in SKY_MARKS else "") + (" ag" if x_["id"] == "agensh-1024" else "")
        tt = f'<title>{esc(L["sky_title_of"].format(t=title_of(x_["w"], lang) if title_of else x_["id"], v=fnum(x_["n"], lang)))}</title>'
        o.append(f'<rect class="k {c_}" style="--i:{i}" data-on="{" ".join(s for s in sky if s in states)}" x="{x + bw * .12:.1f}" y="{BASE - h:.1f}" width="{bw * .76:.1f}" height="{h:.1f}">{tt}</rect>')
    med = statistics.median(x_["n"] for x_ in SW)
    xm = sx0 + med_i * bw + bw / 2
    k("skl", sky, f'<text class="cap lime" x="{xm}" y="{BASE - HV(med) - 40}" text-anchor="middle">{esc(nb(L["st_median"]).format(v=fnum(med, lang)))}</text>'
      f'<line class="tick lime" x1="{xm}" y1="{BASE - HV(med) - 30}" x2="{xm}" y2="{BASE - HV(med) - 6}"/>')
    if var == "wide":
        k("skl", sky, f'<text class="cap" x="{sx0}" y="{BASE + 40}">{esc(L["st_sky_cap"].format(n=nw))}</text><text class="cap dim" x="{sx0}" y="{BASE + 68}">{esc(L["st_sky_cap2"])}</text>')
    else:
        k("skl", sky, f'<text class="cap" x="{sx0}" y="{BASE + 56}">{esc(L["st_sky_cap_n"].format(n=nw))}</text>')
    for t in THRESHOLDS:
        cnt = sum(1 for x_ in SW if x_["n"] >= t)
        y = BASE - HV(t)
        first = next(i for i, x_ in enumerate(SW) if x_["n"] >= t)
        xx = sx0 + first * bw
        lbl = (L["st_thr"] if var == "wide" else L["st_thr_n"]).format(t=fnum(t, lang), c=cnt)
        k("thr", ["sky-1", "sky-2"], f'<line class="thl" x1="{sx0}" y1="{y}" x2="{sx1}" y2="{y}"/><line class="thk" x1="{xx}" y1="{y - 8}" x2="{xx}" y2="{y + 8}"/><text class="thn" x="{sx0}" y="{y - 10}">{esc(lbl)}</text>')
    for mid in SKY_MARKS:
        i = next(i for i, x_ in enumerate(SW) if x_["id"] == mid)
        x = sx0 + i * bw + bw / 2
        y = BASE - HV(SW[i]["n"])
        short = nb(L["st_marks"][mid]) if var == "wide" else fnum(SW[i]["n"], lang).replace(" ", NB)
        if var != "wide" and mid in ("openai-navier-stokes", "anthropic-institute-pace"):
            short = "≈" + short
        k("mkl" + (" agl" if mid == "agensh-1024" else ""), ["sky-2"], f'<line class="mkline" x1="{x}" y1="{y - 6}" x2="{x}" y2="{y - 40}"/><text class="mkt" x="{x - 6}" y="{y - 48}" text-anchor="end">{esc(short)}</text>')
    gs = 480 if var == "wide" else 640
    gx, gy = (X0, 150) if var == "wide" else ((W - gs) / 2, 200)
    k("grid", ["sky-3"], f'<g transform="translate({gx},{gy}) scale({gs / 512})"><rect class="g32" x="0" y="0" width="512" height="512" fill="url(#g32-{sid})"/></g>'
      f'<text class="cap" x="{gx}" y="{gy + gs + (46 if var == "wide" else 58)}">{esc(nb(L["st_grid"] if var == "wide" else L["st_grid_n"]))}</text>')
    for key, t in L["st_titles"].items():
        k("stt", [s for s in STATES if s.startswith(key)], f'<text class="stt" x="{X0}" y="{52 if var == "wide" else 66}">{esc(t)}</text>')
    o.append("</svg>")
    return "".join(o)


def state_css():
    """Which blocks a state shows and how it paints them; the same rules serve the sticky stage and the static figures."""
    r = []
    for st in STATES:
        r.append(f'.st-svg[data-s="{st}"] .k[data-on~="{st}"]{{opacity:1;visibility:visible}}')
        r.append(f'.st-svg[data-s="{st}"] .bk[data-lime~="{st}"]{{fill:var(--lime);stroke:var(--lime)}}')
        r.append(f'.st-svg[data-s="{st}"] .bk[data-copy~="{st}"]{{fill:var(--lime-bg);stroke:var(--lime);stroke-width:3}}')
        r.append(f'.st-svg[data-s="{st}"] .bk[data-redo~="{st}"]{{fill:var(--coral-bg);stroke:var(--coral)}}')
        r.append(f'.st-svg[data-s="{st}"] .bk[data-over~="{st}"]{{fill:var(--coral);stroke:var(--coral)}}')
        r.append(f'.st-svg[data-s="{st}"] .bk[data-dim~="{st}"]{{fill:transparent;stroke:var(--line-3)}}')
    return "\n".join(r)


def towers_svg(cls="hero-tw"):
    """The title screen: six context windows filling with blocks; one block, agent 3's finding, is lime."""
    W, H, X0, CW, GAP, BASE, SH, BH = 900, 980, 40, 112, 26, 940, 52, 44
    o = [f'<svg class="{cls}" viewBox="0 0 {W} {H}" aria-hidden="true" focusable="false" preserveAspectRatio="xMaxYMax meet">']
    for t in range(6):
        x = X0 + t * (CW + GAP)
        o.append(f'<rect class="fr" x="{x - 6}" y="{BASE - 17 * SH}" width="{CW + 12}" height="{17 * SH + 8}" rx="8"/>')
        for s in range([9, 12, 10, 13, 11, 8][t]):
            o.append(f'<rect class="hb{" lime" if (t == 2 and s == 9) else ""}" style="--d:{round(.25 + s * .11 + t * .07, 2)}s" x="{x}" y="{BASE - (s + 1) * SH + (SH - BH)}" width="{CW}" height="{BH}" rx="4"/>')
    o.append("</svg>")
    return "".join(o)


def hero_html(lang, cover, survey_href="#survey"):
    """The title screen of the single page. `cover` is the :::cover block of index.md (kicker, subtitle, meta)."""
    L = T[lang]
    lines = "".join(f"<span>{esc(x)}</span>" for x in L["hero_lines"])
    meta = esc(cover.get("meta_line", ""))
    return (f'<header class="hero" aria-labelledby="h1"><div class="hero-in">'
            f'<p class="kicker">{esc(cover.get("kicker", ""))}</p><h1 id="h1">{lines}</h1>'
            f'<p class="sub">{esc(cover.get("subtitle", ""))}</p><p class="hook">{esc(L["hero_hook"])}</p>'
            f'<p class="meta">{meta}</p></div>'
            f'<div class="hero-art">{towers_svg()}</div>'
            f'<p class="cue"><a href="#how">{esc(L["hero_cue"])}</a><a class="cue-skip" href="{survey_href}">{esc(L["hero_skip"])} ↓</a></p></header>')


def stage_html(lang, href, ch1_href="#ch01", agensh_href="#agensh", title_of=None):
    """#how: the prologue as a sticky stage beside its text. Each step names the state it shows; without JavaScript, or
    with reduced motion, the stage is hidden and every scheme carries a static figure of its end state."""
    L = T[lang]
    ld = ladder(load_works())
    modes = {m[0]: m for m in L["modes"]}
    def stat(state):
        return (f'<figure class="static" aria-hidden="true"><div class="vw">{stage_svg("wide", lang, state, title_of)}</div>'
                f'<div class="vn">{stage_svg("narrow", lang, state, title_of)}</div></figure>')
    steps = [f'<div class="step intro" data-s="ind-0" id="how-1"><p class="label">{esc(L["st_label"])}</p>'
             f'<h2 id="how-h">{L["h1"]}</h2><p class="deck">{esc(nb(L["deck"]))}</p><p class="note">{esc(L["st_note"])}</p></div>']
    n = 1
    for m in ("ind", "coord", "mem"):
        _, num, name, short, desc, ev, wid, more = modes[m]
        b = L["beats"][m]
        link = (f' <a href="{href(wid)}">{esc(nb(more))}{NB}→</a>' if wid else f' <a href="{agensh_href}">{esc(nb(more))}{NB}↓</a>')
        n += 1
        steps.append(f'<div class="grp" data-g="{m}" id="m-{m}"><div class="step" data-s="{m}-0" id="how-{n}"><h3><span class="num">{num}</span>{esc(name)} <span class="short">— {esc(short)}</span></h3>'
                     f'{stat(m + "-3")}<p class="mtext">{esc(desc)}</p><p class="beat">{esc(b[0])}</p></div>')
        n += 1
        steps.append(f'<div class="step" data-s="{m}-2" id="how-{n}"><p class="beat">{esc(b[1])}</p><p class="beat">{esc(b[2])}</p></div>')
        n += 1
        steps.append(f'<div class="step" data-s="{m}-3" id="how-{n}"><p class="beat">{esc(b[3])}</p><p class="ev">{esc(nb(ev))}{link}</p></div></div>')
    thr = " · ".join((L["st_thr"].format(t=fnum(t, lang), c=c)) for t, c in ld["rows"])
    kw = dict(corpus=ld["corpus"], known=ld["known"], med=fnum(ld["median"], lang))
    n += 1
    steps.append(f'<div class="grp" data-g="sky"><div class="step" data-s="sky-1" id="how-{n}"><p class="label">{esc(L["st_scale_label"])}</p><h2>{esc(L["st_scale_h"])}</h2>'
                 f'{stat("sky-2")}<p class="deck">{esc(L["st_scale_p1"].format(**kw))}</p><p class="beat sm">{esc(L["st_scale_thr"].format(known=ld["known"], thr=thr))}</p></div>')
    n += 1
    steps.append(f'<div class="step" data-s="sky-2" id="how-{n}"><p class="beat sm">{esc(nb(L["st_scale_p2"]))}</p><p class="mtext">{esc(nb(L["st_scale_p3"]))}</p>'
                 f'<p class="beat sm lime">{esc(nb(L["st_scale_gap"]))}</p><p class="ev"><a href="{ch1_href}">{esc(L["st_scale_more"])}{NB}→</a></p></div>')
    n += 1
    steps.append(f'<div class="step" data-s="sky-3" id="how-{n}"><p class="beat big">{esc(nb(L["st_grid_beat"]))}</p><p class="ev"><a href="{agensh_href}">{esc(L["st_grid_more"])}{NB}↓</a></p></div></div>')
    stage = f'<div class="vw">{stage_svg("wide", lang, None, title_of)}</div><div class="vn">{stage_svg("narrow", lang, None, title_of)}</div>'
    return (f'<section class="scrolly" id="how" aria-labelledby="how-h"><div class="stage" aria-hidden="true">{stage}</div>'
            f'<div class="steps">{"".join(steps)}</div></section>')


# ---------------------------------------------------------------- Agensh: agent 17's window, the result, the protocol
PANDOC = [(1, 33.89), (8, 41.75), (32, 43.11), (128, 50.94), (1024, 55.06)]
MEAN5 = [(1, 19.31), (8, 20.68), (32, 26.52), (128, 28.78)]
AGENT_HOURS = [(1, 1), (128, 117), (1024, 800)]


def board_svg(lang):
    """Agent 17's window: its own blocks, and board entries arriving in batches at tool-call boundaries; an old entry by search."""
    import random
    L = T[lang]
    W, H = 760, 640
    TX, CW, BASE, SH, BH, NSL = 330, 150, 600, 30, 24, 18
    rnd = random.Random(11)
    seq = []
    for b in range(3):
        seq += [("own", None), ("own", None), ("bnd", L["ag_board_b"][b])]
        seq += [("rec", rnd.choice(["claim", "fail", "patch"])) for _ in range(rnd.choice([2, 3]))]
    seq += [("own", None), ("q", None), ("old", "patch")]
    o = [f'<svg class="b17" viewBox="0 0 {W} {H}" role="img" aria-labelledby="b17-t"><title id="b17-t">{esc(L["ag_board_desc"])}</title>',
         f'<rect class="fr" x="{TX - 8}" y="{BASE - NSL * SH - 2}" width="{CW + 16}" height="{NSL * SH + 10}" rx="8"/>'
         f'<text class="tl" x="{TX + CW / 2}" y="{BASE - NSL * SH - 18}" text-anchor="middle">{esc(nb(L["ag_board_win"]))}</text>',
         f'<rect class="fr board" x="20" y="{BASE - NSL * SH - 2}" width="200" height="{NSL * SH + 10}" rx="8"/>'
         f'<text class="tl" x="120" y="{BASE - NSL * SH - 18}" text-anchor="middle">{esc(L["ag_board_board"])}</text>']
    for i in range(22):
        o.append(f'<rect class="brd k-{rnd.choice(["claim", "fail", "patch"])}" x="{36 + (i % 4) * 44}" y="{BASE - 14 - (i // 4) * 30 - 26}" width="36" height="20" rx="3"/>')
    lvl = 0
    for kk, (kind, v) in enumerate(seq):
        y = BASE - (lvl + 1) * SH + (SH - BH)
        if kind == "own":
            o.append(f'<rect class="ob" style="--k:{kk}" x="{TX}" y="{y}" width="{CW}" height="{BH}" rx="3"/>'); lvl += 1
        elif kind in ("rec", "old"):
            o.append(f'<rect class="rb k-{v}{" old" if kind == "old" else ""}" style="--k:{kk}" x="{TX + 10}" y="{y}" width="{CW - 20}" height="{BH}" rx="3"/>'); lvl += 1
        elif kind == "bnd":
            o.append(f'<g class="bd" style="--k:{kk}"><line x1="{TX - 26}" y1="{y + BH + 2}" x2="{TX + CW + 26}" y2="{y + BH + 2}"/>'
                     f'<text x="{TX + CW + 34}" y="{y + BH + 7}">{esc(L["ag_board_batch"].format(b=v))}</text></g>')
        else:
            tx_, ty_ = 36 + 44 + 36, BASE - 14 - 30 - 16
            o.append(f'<g class="bd q" style="--k:{kk}"><path d="M{TX - 10},{y + 12} C{TX - 70},{y + 12} {tx_ + 60},{ty_} {tx_ + 4},{ty_}"/>'
                     f'<circle cx="{tx_ - 18}" cy="{ty_}" r="15" class="qr"/><text x="{TX + CW + 34}" y="{y + 18}">{esc(L["ag_board_search"])}</text></g>')
    o.append("</svg>")
    return "".join(o)


def bars_svg(lang, var):
    """Pandoc pass rate by team size (bars), the mean over five tasks (ticks), and agent-hours relative to one agent below."""
    L = T[lang]
    if var == "wide":
        W, H, X0, X1, Y0, YT = 1000, 640, 80, 960, 380, 70
    else:
        W, H, X0, X1, Y0, YT = 360, 520, 24, 350, 300, 56
    sizes = [v for v, _ in PANDOC]
    step = (X1 - X0) / len(sizes)
    bw = step * .56
    Y = lambda v: Y0 - v / 60 * (Y0 - YT)
    o = [f'<svg class="bars v-{var}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="bars-{var}-t"><title id="bars-{var}-t">{esc(L["ag_bars_desc"])}</title>']
    for v in (0, 20, 40, 60):
        o.append(f'<line class="gl" x1="{X0}" y1="{Y(v)}" x2="{X1}" y2="{Y(v)}"/><text class="gt" x="{X0 - 8}" y="{Y(v) + 5}" text-anchor="end">{v}</text>')
    pan, mean, hrs = dict(PANDOC), dict(MEAN5), dict(AGENT_HOURS)
    for i, n_ in enumerate(sizes):
        cx = X0 + step * i + step / 2
        v = pan[n_]
        o.append(f'<g class="bar" style="--i:{i}"><rect class="bv{" ag" if n_ == 1024 else ""}" x="{cx - bw / 2}" y="{Y(v)}" width="{bw}" height="{Y0 - Y(v)}" rx="4"/>'
                 f'<text class="bvv" x="{cx}" y="{Y(v) - 16}" text-anchor="middle">{fnum(v, lang, 2)}</text></g>')
        if n_ in mean:
            o.append(f'<line class="mn" x1="{cx - bw / 2 - 6}" y1="{Y(mean[n_])}" x2="{cx + bw / 2 + 6}" y2="{Y(mean[n_])}"/>')
        o.append(f'<text class="bx" x="{cx}" y="{Y0 + 34}" text-anchor="middle">{fnum(n_, lang)}</text>')
    o.append(f'<text class="cap" x="{X0}" y="{YT - (30 if var == "wide" else 26)}">{esc(L["ag_bars_axis"] if var == "wide" else L["ag_bars_axis_n"])}</text>')
    if var == "wide":
        o.append(f'<line class="mn" x1="{X1 - 190}" y1="{YT - 44}" x2="{X1 - 164}" y2="{YT - 44}"/><text class="cap" x="{X1 - 156}" y="{YT - 38}">{esc(L["ag_bars_mean"])}</text>')
    HY0 = Y0 + 70
    HH = (H - HY0 - 40)
    HL = lambda v: math.log10(v) / math.log10(1000) * HH
    o.append(f'<text class="cap coral" x="{X0}" y="{HY0 - (12 if var == "wide" else 10)}">{esc(L["ag_bars_hours"] if var == "wide" else L["ag_bars_hours_n"])}</text>')
    for i, n_ in enumerate(sizes):
        cx = X0 + step * i + step / 2
        if n_ in hrs:
            h = max(4, HL(hrs[n_]))
            o.append(f'<rect class="hv" x="{cx - bw / 2}" y="{HY0}" width="{bw}" height="{h}" rx="3"/><text class="hvv" x="{cx}" y="{HY0 + h + 26}" text-anchor="middle">×{fnum(hrs[n_], lang)}</text>')
        else:
            o.append(f'<text class="hvn" x="{cx}" y="{HY0 + (22 if var == "wide" else 18)}" text-anchor="middle">{esc(L["ag_bars_none"]) if var == "wide" else "—"}</text>')
    o.append("</svg>")
    return "".join(o)


def proto_svg(lang):
    L = T[lang]
    W, H = 780, 300
    o = [f'<svg class="proto" viewBox="0 0 {W} {H}" role="img" aria-labelledby="pr-t"><title id="pr-t">{esc(L["ag_proto_desc"])}</title>']
    for r, ((name, cells), y) in enumerate(zip(L["ag_proto_rows"], (30, 170))):
        o.append(f'<text class="stt sm" x="0" y="{y + 16}">{esc(name)}</text>')
        x = 0
        for j, ((who, what), w) in enumerate(zip(cells, (300, 120, 340))):
            if who == "→":
                o.append(f'<line class="arr" x1="{x + 10}" y1="{y + 70}" x2="{x + w - 16}" y2="{y + 70}"/><path class="arrh" d="M{x + w - 18},{y + 62} l12,8 l-12,8z"/>'
                         f'<text class="pl lime" x="{x + w / 2}" y="{y + 56}" text-anchor="middle">{esc(what)}</text>')
            else:
                on = "" if (r == 1 and j == 0) else " on"     # after the failures the author no longer runs the cycle
                o.append(f'<rect class="pbox{on}" x="{x}" y="{y + 36}" width="{w - 20}" height="68" rx="6"/><text class="pw" x="{x + 16}" y="{y + 62}">{esc(who)}</text>'
                         f'<text class="pl" x="{x + 16}" y="{y + 88}">{esc(what)}</text>')
            x += w
    o.append("</svg>")
    return "".join(o)


# ---------------------------------------------------------------- scale ladder (computed)
THRESHOLDS = [10, 100, 1000, 10000]


def ladder(works):
    """Simultaneous agent counts over the analytic corpus, the way Chapter 1 counts them."""
    corpus = [w for w in works if w.get("corpus")]
    known = [w["corpus"]["agents_max_simultaneous"] for w in corpus
             if w["corpus"].get("scale_kind") == "simultaneous" and isinstance(w["corpus"].get("agents_max_simultaneous"), (int, float))]
    med = statistics.median(known) if known else 0
    return dict(corpus=len(corpus), known=len(known), median=int(med) if float(med) == int(med) else med,
                rows=[(t, sum(1 for x in known if x >= t)) for t in THRESHOLDS])


def load_works():
    return json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))["works"]


_SKY = sky_works()
assert len(_SKY) == 99 and statistics.median(x["n"] for x in _SKY) == 7, (len(_SKY),)
assert [(t, sum(1 for x in _SKY if x["n"] >= t)) for t in THRESHOLDS] == [(10, 42), (100, 15), (1000, 7), (10000, 4)]


# ---------------------------------------------------------------- standalone SVG for the README (no script, fonts or network)
FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
COND = "'SF Pro Display Condensed', 'Arial Narrow', 'Roboto Condensed', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
PAL = {
    "dark": dict(bg="#050507", panel="#0B0C10", line="#2A2D35", frame="#3A3E47", ink="#F4F5F7", ink2="#CDD1D8", ink3="#9298A3", head="#FFFFFF",
                 lime="#C8F542", lime_ink="#C8F542", lime_bg="#2A3311", coral="#FF5B3A", coral_bg="#3A1A13", block="#14151A", block_line="#5C626C", on_lime="#0A0B0E", mean="#4A4F58"),
    "light": dict(bg="#F4F4EF", panel="#FFFFFF", line="#D9D9D2", frame="#B9BAB3", ink="#0A0B0E", ink2="#33363D", ink3="#5E636C", head="#050507",
                  lime="#B5E22E", lime_ink="#4A6800", lime_bg="#EAF5C8", coral="#D63C1E", coral_bg="#FBE2DC", block="#FFFFFF", block_line="#8A8E96", on_lime="#0A0B0E", mean="#D0D1CA"),
}
_W = {"narrow": set("iljtfrI.,:;'|!()[] "), "wide": set("mwMWЖШЩЮМДФЫ@%")}


def text_px(s, fs):
    """Rough advance width of a system sans string, for wrapping poster captions."""
    w = 0.0
    for ch in s:
        w += .32 if ch in _W["narrow"] else .86 if ch in _W["wide"] else .62 if ch.isupper() else .56
    return w * fs


def wrap(s, max_px, fs):
    lines, cur = [], ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if cur and text_px(cand, fs) > max_px:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def _towers(C, ox, oy, state, lang, coord=False, shelf=False, scale=1.0):
    """One panel of the poster: the end state of one scheme, drawn as context windows."""
    L = T[lang]
    NSL = 16 if coord else 12                     # the coordinator's window holds 16 blocks; the top three overflow
    CW, GAP, SH, BH = 44 * scale, 10 * scale, (12 if coord else 16) * scale, (10 if coord else 13) * scale
    cols = [1, 2, 3, "C", 4, 5, 6] if coord else [1, 2, 3, 4, 5, 6]
    plan = PLAN[state]
    o = []
    base = oy + NSL * SH
    for i, c in enumerate(cols):
        x = ox + i * (CW + GAP)
        o.append(f'<rect x="{n(x - 3)}" y="{n(oy - 4)}" width="{n(CW + 6)}" height="{n(NSL * SH + 8)}" rx="4" fill="none" stroke="{C["frame"]}"' + (' stroke-dasharray="4 4"' if c == "C" else "") + '/>')
        lab = L["st_coord"] if c == "C" else str(c)
        o.append(f'<text x="{n(x + CW / 2)}" y="{n(oy - 12)}" text-anchor="middle" font-family="{MONO}" font-size="{n(13 * scale)}" fill="{C["ink3"]}">{esc(lab)}</text>')
        for s in range(NSL):
            cell = plan.get(c, {}).get(s)
            if not cell:
                continue
            y = base - (s + 1) * SH + (SH - BH)
            fill, stroke, sw = C["block"], C["block_line"], 1
            if cell == "lime":
                fill, stroke = C["lime"], C["lime"]
            elif cell == "copy":
                fill, stroke, sw = C["lime_bg"], C["lime"], 2.4
            elif cell == "redo":
                fill, stroke = C["coral_bg"], C["coral"]
            elif cell == "over":
                fill, stroke = C["coral"], C["coral"]
            elif cell == "dim":
                fill = "none"
            o.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(CW)}" height="{n(BH)}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    if coord:
        cx = ox + 3 * (CW + GAP) + CW / 2
        o.append(f'<path d="' + "".join(f"M{n(ox + i * (CW + GAP) + CW / 2)} {n(base + 8)}V{n(base + 22)}H{n(cx)}V{n(base + 8)}" for i in range(7) if i != 3) + f'" fill="none" stroke="{C["frame"]}"/>')
    if shelf:
        w_ = 6 * (CW + GAP) - GAP
        o.append(f'<rect x="{n(ox)}" y="{n(base + 12)}" width="{n(w_)}" height="{n(BH + 10)}" rx="4" fill="none" stroke="{C["ink3"]}" stroke-dasharray="4 5"/>')
        o.append(f'<rect x="{n(ox + 2 * (CW + GAP))}" y="{n(base + 17)}" width="{n(CW)}" height="{n(BH)}" rx="2" fill="{C["lime"]}"/>')
    return "".join(o)


def poster_svg(lang, theme, corpus):
    """README poster: the question, and the end state of the three schemes as context windows."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1600, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["po_t1"])} {esc(L["po_t2"])}</title><desc id="d">{esc(L["po_desc"])}</desc>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>',
         f'<text x="64" y="96" font-family="{MONO}" font-size="20" letter-spacing="3" fill="{C["ink3"]}">{esc(L["po_brand"].upper())} {esc(L["po_brand2"].format(corpus=corpus).upper())}</text>',
         f'<text x="64" y="186" font-family="{COND}" font-stretch="condensed" font-size="72" font-weight="900" fill="{C["head"]}">{esc(L["po_t1"].upper())}</text>',
         f'<text x="64" y="262" font-family="{COND}" font-stretch="condensed" font-size="72" font-weight="900" fill="{C["lime_ink"]}">{esc(L["po_t2"].upper())}</text>']
    pw, gap, x0, y0 = 472, 28, 64, 318
    for i, (mode, num, title, tag, cap) in enumerate(L["po_panels"]):
        x = x0 + i * (pw + gap)
        o.append(f'<rect x="{x}" y="{y0}" width="{pw}" height="512" rx="16" fill="{C["panel"]}" stroke="{C["line"]}"/>')
        o.append(f'<text x="{x + 26}" y="{y0 + 44}" font-family="{MONO}" font-size="16" letter-spacing="2" fill="{C["lime_ink"]}">{num}</text>'
                 f'<text x="{x + 64}" y="{y0 + 46}" font-family="{COND}" font-stretch="condensed" font-size="30" font-weight="850" fill="{C["head"]}">{esc(title.upper())}</text>'
                 f'<text x="{x + 64}" y="{y0 + 74}" font-family="{FONT}" font-size="18" fill="{C["ink3"]}">{esc(tag)}</text>')
        coord, shelf = mode == "coord", mode == "mem"
        sc = .95 if coord else 1.1
        cols = 7 if coord else 6
        span = cols * 54 * sc - 10 * sc
        o.append(_towers(C, x + (pw - span) / 2, y0 + 120, mode + "-3", lang, coord=coord, shelf=shelf, scale=sc))
        for j, line in enumerate(wrap(cap, pw - 52, 19)[:3]):
            o.append(f'<text x="{x + 26}" y="{y0 + 432 + j * 27}" font-family="{FONT}" font-size="19" fill="{C["ink2"]}">{esc(line)}</text>')
    o.append(f'<g transform="translate(64 856)"><rect x="0" y="-13" width="26" height="14" rx="2" fill="{C["lime"]}"/>'
             f'<text x="36" y="0" font-family="{FONT}" font-size="18" fill="{C["ink2"]}">{esc(L["po_leg"][0])}</text>'
             f'<rect x="360" y="-13" width="26" height="14" rx="2" fill="{C["coral_bg"]}" stroke="{C["coral"]}"/>'
             f'<text x="396" y="0" font-family="{FONT}" font-size="18" fill="{C["ink2"]}">{esc(L["po_leg"][1])}</text>'
             f'<text x="0" y="30" font-family="{FONT}" font-size="16" fill="{C["ink3"]}">{esc(L["po_foot"])}</text></g>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def scale_chart_svg(lang, theme, ld):
    """README: the skyline of the works that state a simultaneous count, with the median and the thresholds."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1200, 560
    SW = sky_works()
    kw = dict(known=ld["known"], corpus=ld["corpus"], med=fnum(ld["median"], lang))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["rs_t"])}</title>',
         f'<desc id="d">{esc(L["rs_s"].format(**kw))}. ' + "; ".join(f"≥{fnum(t, lang)}: {v}" for t, v in ld["rows"]) + '.</desc>',
         f'<rect width="{W}" height="{H}" rx="24" fill="{C["bg"]}"/>',
         f'<text x="56" y="80" font-family="{COND}" font-stretch="condensed" font-size="46" font-weight="900" fill="{C["head"]}">{esc(L["rs_t"].upper())}</text>',
         f'<text x="56" y="118" font-family="{FONT}" font-size="20" fill="{C["ink3"]}">{esc(L["rs_s"].format(**kw))}</text>']
    x0, x1, base, top = 56, W - 56, H - 70, 170
    bw = (x1 - x0) / len(SW)
    HV = lambda v: (math.log10(v) + .35) / (math.log10(30000) + .35) * (base - top)
    for t, c in ld["rows"]:
        y = base - HV(t)
        o.append(f'<line x1="{x0}" x2="{x1}" y1="{n(y)}" y2="{n(y)}" stroke="{C["frame"]}" stroke-dasharray="3 6"/>'
                 f'<text x="{x0}" y="{n(y - 8)}" font-family="{MONO}" font-size="16" fill="{C["ink2"]}">{esc(L["st_thr"].format(t=fnum(t, lang), c=c))}</text>')
    med_i = (len(SW) - 1) // 2
    for i, x_ in enumerate(SW):
        h = HV(x_["n"])
        fill = C["lime"] if (i == med_i or x_["id"] == "agensh-1024") else (C["head"] if x_["id"] in SKY_MARKS else C["ink3"])
        o.append(f'<rect x="{n(x0 + i * bw + bw * .12)}" y="{n(base - h)}" width="{n(bw * .76)}" height="{n(h)}" fill="{fill}"/>')
    xm = x0 + med_i * bw + bw / 2
    o.append(f'<text x="{n(xm)}" y="{n(base - HV(7) - 36)}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="600" fill="{C["lime_ink"]}">{esc(nb(L["st_median"]).format(v=kw["med"]))}</text>')
    o.append(f'<text x="{x0}" y="{base + 36}" font-family="{FONT}" font-size="17" fill="{C["ink3"]}">{esc(L["st_sky_cap"].format(n=len(SW)))} · {esc(L["st_sky_cap2"])}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def pandoc_chart_svg(lang, theme):
    """README: the Agensh result as towers, with the mean over five tasks."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1200, 560
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["rp_t"])}</title>', f'<desc id="d">{esc(L["li_d"])}</desc>',
         f'<rect width="{W}" height="{H}" rx="24" fill="{C["bg"]}"/>',
         f'<text x="56" y="80" font-family="{COND}" font-stretch="condensed" font-size="46" font-weight="900" fill="{C["head"]}">{esc(L["rp_t"].upper())}</text>',
         f'<text x="56" y="118" font-family="{FONT}" font-size="20" fill="{C["ink3"]}">{esc(L["rp_s"])}</text>']
    X0, X1, Y0, YT = 120, 1140, 470, 170
    step = (X1 - X0) / len(PANDOC)
    bw = step * .52
    Y = lambda v: Y0 - v / 60 * (Y0 - YT)
    for v in (0, 20, 40, 60):
        o.append(f'<line x1="{X0}" x2="{X1}" y1="{n(Y(v))}" y2="{n(Y(v))}" stroke="{C["line"]}"/><text x="{X0 - 14}" y="{n(Y(v) + 6)}" text-anchor="end" font-family="{MONO}" font-size="16" fill="{C["ink3"]}">{v}</text>')
    mean = dict(MEAN5)
    for i, (k_, v) in enumerate(PANDOC):
        cx = X0 + step * i + step / 2
        o.append(f'<rect x="{n(cx - bw / 2)}" y="{n(Y(v))}" width="{n(bw)}" height="{n(Y0 - Y(v))}" rx="4" fill="{C["lime"] if k_ == 1024 else C["ink2"]}"/>'
                 f'<text x="{n(cx)}" y="{n(Y(v) - 14)}" text-anchor="middle" font-family="{COND}" font-stretch="condensed" font-size="32" font-weight="850" fill="{C["head"]}">{fnum(v, lang, 2)}</text>'
                 f'<text x="{n(cx)}" y="{Y0 + 32}" text-anchor="middle" font-family="{MONO}" font-size="17" fill="{C["ink3"]}">{fnum(k_, lang)}</text>')
        if k_ in mean:
            o.append(f'<line x1="{n(cx - bw / 2 - 6)}" x2="{n(cx + bw / 2 + 6)}" y1="{n(Y(mean[k_]))}" y2="{n(Y(mean[k_]))}" stroke="{C["mean"]}" stroke-width="4"/>')
    o.append(f'<text x="{X1}" y="{Y0 + 66}" text-anchor="end" font-family="{FONT}" font-size="17" fill="{C["ink3"]}">{esc(L["ag_bars_mean"])} — {esc(L["rp_src"])}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


MEMORY = [("shared", 55.1), ("private", 46.8), ("none", 38.0)]     # ScaleMAS, Table 2 (card in Chapter 6)


def memory_chart_svg(lang, theme):
    """README: the 19 October correction on shared memory, as three panels of four context windows."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1200, 560
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["mem_t"])}</title>',
         f'<desc id="d">{esc(L["mem_s"])}: ' + "; ".join(f"{lab} {fnum(v, lang, 1)}%" for lab, (_, v) in zip(L["mem_labels"], MEMORY)) + f'. {esc(L["mem_note"])}</desc>',
         f'<rect width="{W}" height="{H}" rx="24" fill="{C["bg"]}"/>',
         f'<text x="56" y="80" font-family="{COND}" font-stretch="condensed" font-size="44" font-weight="900" fill="{C["head"]}">{esc(L["mem_t"].upper())}</text>',
         f'<text x="56" y="118" font-family="{FONT}" font-size="19" fill="{C["ink3"]}">{esc(L["mem_s"])}</text>']
    pw, x0, y0 = 352, 56, 150
    for i, ((mode, v), lab) in enumerate(zip(MEMORY, L["mem_labels"])):
        x = x0 + i * (pw + 20)
        hot = mode == "shared"
        o.append(f'<rect x="{x}" y="{y0}" width="{pw}" height="300" rx="12" fill="{C["panel"]}" stroke="{C["line"]}"/>')
        o.append(f'<text x="{x + 24}" y="{y0 + 76}" font-family="{COND}" font-stretch="condensed" font-size="64" font-weight="900" fill="{C["lime_ink"] if hot else C["head"]}">{fnum(v, lang, 1)}%</text>')
        o.append(f'<rect x="{x + 24}" y="{y0 + 94}" width="{pw - 48}" height="6" rx="2" fill="{C["line"]}"/><rect x="{x + 24}" y="{y0 + 94}" width="{n((pw - 48) * v / 60)}" height="6" rx="2" fill="{C["lime"] if hot else C["ink2"]}"/>')
        o.append(f'<text x="{x + 24}" y="{y0 + 128}" font-family="{MONO}" font-size="15" letter-spacing="1.5" fill="{C["ink2"]}">{esc(lab.upper())}</text>')
        bx, base = x + 44, y0 + 260
        for t in range(4):
            tx_ = bx + t * 70
            o.append(f'<rect x="{tx_ - 3}" y="{base - 102}" width="56" height="106" rx="4" fill="none" stroke="{C["frame"]}"/>')
            fill_ = [6, 7, 6, 7][t] if mode == "shared" else ([6, 5, 6, 5][t] if mode == "private" else [5, 6, 5, 6][t])
            for b in range(fill_):
                lime = (mode != "none" and b == fill_ - 1 and (t != 1 or mode == "shared"))
                o.append(f'<rect x="{tx_}" y="{base - (b + 1) * 14 + 3}" width="50" height="11" rx="2" fill="{C["lime"] if lime else C["block"]}" stroke="{C["lime"] if lime else C["block_line"]}"/>')
            if mode == "private":
                o.append(f'<rect x="{tx_ - 3}" y="{base + 14}" width="56" height="18" rx="4" fill="none" stroke="{C["ink3"]}" stroke-dasharray="4 4"/>')
        if mode == "shared":
            o.append(f'<rect x="{bx - 3}" y="{base + 14}" width="{3 * 70 + 56}" height="18" rx="4" fill="none" stroke="{C["ink3"]}" stroke-dasharray="4 4"/>')
    for j, line in enumerate(wrap(L["mem_note"], W - 112, 18)[:2]):
        o.append(f'<text x="56" y="{y0 + 350 + j * 26}" font-family="{FONT}" font-size="18" fill="{C["ink3"]}">{esc(line)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def write_illustrations(out_dir=None):
    """assets/illustrations/: posters and charts for the README, both languages, dark and light."""
    out_dir = out_dir or os.path.join(ROOT, "assets", "illustrations")
    os.makedirs(out_dir, exist_ok=True)
    ld = ladder(load_works())
    files = []
    for lang in ("en", "ru"):
        for theme in ("dark", "light"):
            for name, svg in ((f"topologies-{lang}-{theme}.svg", poster_svg(lang, theme, ld["corpus"])),
                              (f"scale-{lang}-{theme}.svg", scale_chart_svg(lang, theme, ld)),
                              (f"agensh-pandoc-{lang}-{theme}.svg", pandoc_chart_svg(lang, theme)),
                              (f"memory-{lang}-{theme}.svg", memory_chart_svg(lang, theme))):
                p = os.path.join(out_dir, name)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(svg)
                files.append(p)
    return files


if __name__ == "__main__":
    for p in write_illustrations():
        print(os.path.relpath(p, ROOT), os.path.getsize(p))
    assert not re.search(r"\{\w+\}", open(os.path.join(ROOT, "assets", "illustrations", "topologies-en-dark.svg"), encoding="utf-8").read())

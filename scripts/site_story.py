#!/usr/bin/env python3
"""Topology story for the index page and the README: six agents, three ways to connect them.

Ported from the approved exemplar prototype-v2/src/build.py (those files stay unchanged) and made bilingual.
scripts/build_site.py takes the hero, the scale ladder and the Agensh case for both index pages;
scripts/build_readme.py takes the standalone SVG posters and charts (no script, fonts or network).
Standard library only. Every number here is either computed from data/works.json or quoted from a card
whose anchor is linked next to it.
"""
import html
import json
import math
import os
import re
import statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AG = [1, 2, 3, 4, 5, 6]
# Clockwise from the upper left, so the agents walk the ring and the rows of the log in the same order.
ANG = {1: 240, 2: 300, 3: 0, 4: 60, 5: 120, 6: 180}
ANG_N = {1: 210, 2: 270, 3: 330, 4: 30, 5: 90, 6: 150}
NB = " "


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


# ---------------------------------------------------------------- geometry
def edge(c, hw, hh, toward, m=0.0):
    """Exit point of the ray from the rectangle centre towards `toward`, plus a margin m."""
    dx, dy = toward[0] - c[0], toward[1] - c[1]
    L = math.hypot(dx, dy) or 1
    tx_ = hw / abs(dx) if dx else 1e9
    ty_ = hh / abs(dy) if dy else 1e9
    t = min(tx_, ty_)
    return (c[0] + dx * t + dx / L * m, c[1] + dy * t + dy / L * m)


class Geo:
    def __init__(self, W, H, cw, chh, pad, tag_room=26, coll=92, hub=(168, 88), card=(352, 168), gap=16, ang=None):
        ang = ang or ANG
        self.W, self.H, self.cw, self.chh = W, H, cw, chh
        self.coll_size, self.hub_size, self.card_size = coll, hub, card
        top = pad + chh / 2 + tag_room
        bot = H - pad - chh / 2
        step = (bot - top) / 5
        self.ind = {k: (pad + cw / 2, top + (k - 1) * step) for k in AG}
        self.coll = (W - pad - coll / 2, (top + bot) / 2)
        cx, cy = W / 2, H / 2
        rx = W / 2 - pad - cw / 2
        ry = H / 2 - pad - chh / 2 - tag_room * 0.7
        self.coord = {k: (cx + rx * math.cos(math.radians(ang[k])), cy + ry * math.sin(math.radians(ang[k]))) for k in AG}
        self.hub = (cx, cy)
        xs = [cx - (cw + gap), cx, cx + (cw + gap)]
        yt = pad + chh / 2 + tag_room
        yb = H - pad - chh / 2 - tag_room
        self.mem = {1: (xs[0], yt), 2: (xs[1], yt), 3: (xs[2], yt), 4: (xs[2], yb), 5: (xs[1], yb), 6: (xs[0], yb)}
        self.card = (cx, cy)

    def pos(self, mode):
        return {"ind": self.ind, "coord": self.coord, "mem": self.mem}[mode]

    def lane(self, k):
        x, y = self.ind[k]
        cxl = self.coll[0] - self.coll_size / 2 - 8
        ey = self.coll[1] + (k - 3.5) * 11
        sx = x + self.cw / 2 + 12
        bend = cxl - 150
        return f"M{n(sx)} {n(y)}H{n(bend)}C{n(bend + 70)} {n(y)} {n(cxl - 60)} {n(ey)} {n(cxl)} {n(ey)}"

    def spoke(self, k):
        a = self.coord[k]
        s = edge(a, self.cw / 2, self.chh / 2, self.hub, 6)
        e = edge(self.hub, self.hub_size[0] / 2, self.hub_size[1] / 2, a, 6)
        return f"M{n(s[0])} {n(s[1])}L{n(e[0])} {n(e[1])}"

    def conn(self, k):
        x, y = self.mem[k]
        ch = self.card_size[1] / 2
        if y < self.card[1]:
            return f"M{n(x)} {n(y + self.chh / 2 + 6)}V{n(self.card[1] - ch - 6)}"
        return f"M{n(x)} {n(y - self.chh / 2 - 6)}V{n(self.card[1] + ch + 6)}"


def tag_w(text, fs=14):
    return round(len(text) * fs * 0.58 + 22)


# ---------------------------------------------------------------- stage (hero)
# Two geometries of one scene: wide (desktop, tablet) and portrait (phone). CSS shows one and story.js animates
# the visible one. Agents, channels and states are the same; only coordinates and type size change.
VARIANTS = {
    "w": dict(W=640, H=520, pad=16, coll=92, hub=(168, 88), card=(352, 168), gap=16, ang=ANG, tag_fs=14, tag_h=22,
              lane="lane_w", lane_anchor="middle", below_c=(4, 5), cs_dy=(26, 46, 63),
              row=dict(y0=-12, h=26, x0=-166, w=332, dot=-150, tx=-138, head=-50, rule=-36, clip=(-34, 114))),
    "n": dict(W=486, H=500, pad=14, coll=84, hub=(176, 84), card=(408, 196), gap=12, ang=ANG_N, tag_fs=16, tag_h=24,
              lane="lane_n", lane_anchor="end", below_c=(4, 5, 6), cs_dy=(30, 50, 68),
              row=dict(y0=-20, h=30, x0=-194, w=388, dot=-176, tx=-162, head=-62, rule=-46, clip=(-42, 136))),
}


def stage_svg(v, lang):
    P = VARIANTS[v]
    L = T[lang]
    W, H, cw, chh = P["W"], P["H"], 128, 44
    g = Geo(W, H, cw, chh, P["pad"], coll=P["coll"], hub=P["hub"], card=P["card"], gap=P["gap"], ang=P["ang"])
    R = P["row"]
    o = [f'<svg class="tp tp-{v}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="tp-t-{v} tp-d-{v}">',
         f'<title id="tp-t-{v}">{esc(L["stage_t"])}</title>',
         f'<desc id="tp-d-{v}">{esc(L["stage_d"])}</desc>',
         '<defs>'
         f'<marker id="ah-em-{v}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M1 1L9 5L1 9"/></marker>'
         f'<clipPath id="rows-clip-{v}"><rect x="-{g.card_size[0] / 2}" y="{R["clip"][0]}" width="{g.card_size[0]}" height="{R["clip"][1]}"/></clipPath>'
         '</defs>']
    # independent
    o.append('<g class="layer layer-ind">')
    lx = (g.ind[1][0] + cw / 2 + 12 + g.coll[0] - g.coll_size / 2) / 2
    if P["lane_anchor"] == "end":  # on the narrow stage the label hugs the right edge so it clears agent 1's tag
        lx = W - P["pad"]
    o.append(f'<text class="lc" x="{n(lx)}" y="26" text-anchor="{P["lane_anchor"]}">{esc(L[P["lane"]])}</text>')
    for k in AG:
        o.append(f'<path class="ch lane" data-ch="ind-{k}" d="{g.lane(k)}"/>')
    cx, cy = g.coll
    s = g.coll_size
    d1, d2, d3 = P["cs_dy"]
    o.append(f'<g class="coll" transform="translate({n(cx)} {n(cy)})"><rect class="cb" x="{-s / 2}" y="{-s / 2}" width="{s}" height="{s}" rx="22"/>')
    for k in AG:
        col, row = (k - 1) % 3, (k - 1) // 3
        o.append(f'<rect class="slot" data-n="{k}" x="{-35 + col * 26}" y="{-22 + row * 26}" width="18" height="18" rx="5"/>')
    o.append(f'<text class="ct" y="{s / 2 + d1}" text-anchor="middle">{esc(L["sel"])}</text>'
             f'<text class="cs" y="{s / 2 + d2}" text-anchor="middle">{esc(L["sel1"])}</text>'
             f'<text class="cs" y="{s / 2 + d3}" text-anchor="middle">{esc(L["sel2"])}</text></g>')
    o.append('</g>')
    # coordinator
    o.append('<g class="layer layer-coord">')
    for k in AG:
        o.append(f'<path class="ch spoke" data-ch="co-{k}" d="{g.spoke(k)}"/>')
    hx, hy = g.hub
    hw, hh = g.hub_size
    mw = hw - 52
    o.append(f'<g class="hub" transform="translate({n(hx)} {n(hy)})"><rect class="hb" x="{-hw / 2}" y="{-hh / 2}" width="{hw}" height="{hh}" rx="22"/>'
             f'<text class="ht" y="-11" text-anchor="middle">{esc(L["hub"])}</text>'
             f'<rect class="mt" x="{-mw / 2}" y="5" width="{mw}" height="6" rx="3"/><rect class="mf" x="{-mw / 2}" y="5" width="{mw}" height="6" rx="3"/>'
             f'<text class="ml" y="30" text-anchor="middle">{esc(L["hub_m"])}</text></g>')
    o.append('</g>')
    # shared memory
    o.append('<g class="layer layer-mem">')
    for k in AG:
        o.append(f'<path class="ch conn" data-ch="me-{k}" d="{g.conn(k)}"/>')
    mx, my = g.card
    cw2, chh2 = g.card_size
    o.append(f'<g class="log" transform="translate({n(mx)} {n(my)})"><rect class="lb" x="{-cw2 / 2}" y="{-chh2 / 2}" width="{cw2}" height="{chh2}" rx="20"/>'
             f'<text class="lh" x="{-cw2 / 2 + 20}" y="{R["head"]}">{esc(L["log"])}</text>'
             f'<text class="ls" x="{cw2 / 2 - 20}" y="{R["head"]}" text-anchor="end">{esc(L["log_s"])}</text>'
             f'<line class="ld" x1="{-cw2 / 2 + 20}" x2="{cw2 / 2 - 20}" y1="{R["rule"]}" y2="{R["rule"]}"/>'
             f'<g class="rows" clip-path="url(#rows-clip-{v})" data-y0="{R["y0"]}" data-h="{R["h"]}" data-x0="{R["x0"]}" data-w="{R["w"]}" data-dot="{R["dot"]}" data-tx="{R["tx"]}">')
    rh = R["h"] - 2
    for j, (k, t, hot) in enumerate(L["rows"]):
        o.append(f'<g class="row{" k" if hot else ""}" transform="translate(0 {R["y0"] + j * R["h"]})">'
                 f'<rect class="rh" x="{R["x0"]}" y="{-rh / 2}" width="{R["w"]}" height="{rh}" rx="8"/>'
                 f'<circle class="rd" cx="{R["dot"]}" r="4"/><text class="rt" x="{R["tx"]}" dy=".35em">{esc(L["agent"].format(k=k))} · {esc(t)}</text></g>')
    o.append('</g></g>')
    o.append('</g>')
    # agents
    o.append('<g class="ags">')
    th = P["tag_h"]
    for k in AG:
        ix, iy = g.ind[k]
        px, py = g.coord[k]
        qx, qy = g.mem[k]
        up, dn = -(chh / 2 + 19), chh / 2 + 19
        tyc = dn if k in P["below_c"] else up
        tym = dn if k in (4, 5, 6) else up
        style = (f"--ix:{n(ix)}px;--iy:{n(iy)}px;--cx:{n(px)}px;--cy:{n(py)}px;--mx:{n(qx)}px;--my:{n(qy)}px;"
                 f"--tyi:{n(up)}px;--tyc:{n(tyc)}px;--tym:{n(tym)}px;--d:{(k - 1) * 0.37:.2f}s")
        data = f'data-ind="{n(ix)},{n(iy)}" data-coord="{n(px)},{n(py)}" data-mem="{n(qx)},{n(qy)}"'
        o.append(f'<g class="ag" data-n="{k}" {data} style="{style}">')
        chip = f'x="{-cw / 2}" y="{-chh / 2}" width="{cw}" height="{chh}" rx="{chh / 2}"'
        o.append(f'<g class="body"><rect class="chip" {chip}/><rect class="chip-k" {chip}/>'
                 f'<circle class="st" cx="-41" r="5"/><circle class="st-k" cx="-41" r="5"/><text class="al" x="-28" dy=".35em">{esc(L["agent"].format(k=k))}</text></g>')
        o.append('<g class="tgs">')
        for key, text in L["tags"]:
            w = tag_w(text, P["tag_fs"])
            o.append(f'<g class="tg tg-{key}"><rect x="{-w / 2}" y="{-th / 2}" width="{w}" height="{th}" rx="{th / 2}"/><text dy=".35em" text-anchor="middle">{esc(text)}</text></g>')
        o.append('</g></g>')
    o.append('</g>')
    o.append('<g class="fx"></g>')
    o.append('</svg>')
    return "\n".join(o)


# Without scripts the scene shows the end state of the chosen mode; these rules repeat the classes story.js sets.
FINAL = {
    "ind": {1: ["k", "redo"], 3: ["k", "src"], 5: ["k", "redo"]},
    "coord": {1: ["k", "got"], 3: ["k", "src"], 5: ["k", "got"]},
    "mem": {1: ["k", "ask"], 3: ["k", "src"], 5: ["k", "ask"]},
}


def mode_css():
    out = []
    for m, key in (("ind", "i"), ("coord", "c"), ("mem", "m")):
        decl = f"transform:translate(var(--{key}x),var(--{key}y));--ty:var(--ty{key})"
        vis = "opacity:1;visibility:visible;transition:opacity .6s .45s,visibility 0s"
        for sel in (f'html.js .hero[data-mode="{m}"]', f'html:not(.js) .hero:has(#m-{m}:checked)'):
            out.append(f'{sel} .ag{{{decl}}}')
            out.append(f'{sel} .layer-{m}{{{vis}}}')
            out.append(f'{sel} .nm-{m}{{display:block}}')
            out.append(f'{sel} .beats-{m}{{visibility:visible}}')
    for m, agents in FINAL.items():
        sel = f"html:not(.js) .hero:has(#m-{m}:checked)"
        for k, classes in agents.items():
            for c in classes:
                out.append(f'{sel} .ag[data-n="{k}"]{{--s-{c}:1}}')
    return "\n".join(out)


# ---------------------------------------------------------------- Agensh: how entries reach an agent
# One chronology, two layouts: time runs right (wide screen) or down (phone). data-t is the position on the
# time axis from 0 to 1; story.js plays it once when the figure scrolls into view.
CH_T0, CH_T1 = 262, 728
CH_B = [292, 490, 614, 708]
CH_E = [("CLAIM", 314), ("FAIL", 374), ("CLAIM", 426), ("PATCH_SUMMARY", 502), ("FAIL", 628)]
CH_G = [(0, 3, 490), (3, 4, 614), (4, 5, 708)]


def ct(x):
    return f"{(x - CH_T0) / (CH_T1 - CH_T0):.3f}"


def pill_w(text):
    return round(len(text) * 6.7 + 14)


def channels_wide(lang):
    L = T[lang]
    o = []
    W, H = 740, 262
    o.append(f'<svg class="chn chn-w" viewBox="0 0 {W} {H}" role="img" aria-labelledby="chn-t-w chn-d">')
    o.append(f'<title id="chn-t-w">{esc(L["ch_t"])}</title>')
    o.append('<defs><marker id="ah-bl-w" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah-bl" d="M1 1L9 5L1 9"/></marker>'
             '<marker id="ah-tx-w" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-tx" d="M1 1L9 5L1 9"/></marker></defs>')
    o.append(f'<text class="rl" x="0" y="56">{esc(L["ch_board"])}</text><text class="rs" x="0" y="75">{esc(L["ch_board_s"])}</text>')
    o.append(f'<text class="rl" x="0" y="174">{esc(L["ch_agent"])}</text><text class="rs" x="0" y="193">{esc(sub_nb(L["ch_agent_s"]))}</text>')
    o.append(f'<text class="rs" x="0" y="216">{esc(L["ch_calls"])}</text>')
    o.append('<rect class="trk" x="152" y="40" width="576" height="38" rx="12"/>')
    for x in (164, 194, 224):
        o.append(f'<rect class="old" x="{x}" y="54" width="22" height="10" rx="3"/>')
    o.append(f'<text class="an" x="204" y="30" text-anchor="middle">{esc(L["ch_old"])}</text>')
    o.append(f'<text class="an" x="490" y="30" text-anchor="middle">{esc(L["ch_new"])}</text>')
    for text, x in CH_E:
        w = pill_w(text)
        o.append(f'<g class="en" data-t="{ct(x)}"><rect x="{x}" y="48" width="{w}" height="22" rx="6"/><text x="{x + w / 2}" y="59" dy=".35em" text-anchor="middle">{text}</text></g>')
    xs = [CH_T0] + CH_B + [CH_T1]
    o.append('<g class="work">')
    for a, b in zip(xs[:-1], xs[1:]):
        a2 = a + (8 if a != CH_T0 else 0)
        o.append(f'<rect x="{a2}" y="170" width="{max(4, b - 8 - a2)}" height="12" rx="6"/>')
    o.append('</g>')
    o.append(f'<rect class="ph" data-axis="x" data-a="{CH_T0}" data-b="{CH_T1}" x="{CH_T0}" y="160" width="2" height="32" rx="1"/>')
    o.append(f'<g class="pull" data-t="{ct(292)}"><path d="M292 164C292 124 236 110 214 84" marker-end="url(#ah-bl-w)" marker-start="url(#ah-bl-w)"/>'
             f'<text x="248" y="146" text-anchor="end">{esc(L["ch_pull"])}</text></g>')
    for i, (a, b, bx) in enumerate(CH_G):
        ax = CH_E[a][1]
        sub = f'<text class="sub" x="{bx - 8}" y="144" text-anchor="end">{esc(L["ch_push_s"])}</text>' if i == 0 else ""
        o.append(f'<g class="push" data-t="{ct(bx)}"><path d="M{ax} 84H{bx}V162" marker-end="url(#ah-bl-w)"/><text x="{bx - 8}" y="126" text-anchor="end">{esc(L["ch_push"][i])}</text>{sub}</g>')
    for b, lab in zip(CH_B, L["ch_b"]):
        o.append(f'<g class="bd" data-t="{ct(b)}"><circle cx="{b}" cy="176" r="6"/><text x="{b}" y="216" text-anchor="middle">{esc(lab)}</text></g>')
    o.append(f'<g class="tax"><path d="M{CH_T0} 242H{CH_T1}" marker-end="url(#ah-tx-w)"/><text x="{CH_T1}" y="258" text-anchor="end">{esc(L["ch_time"])}</text></g>')
    o.append('</svg>')
    return "\n".join(o)


def channels_tall(lang):
    """Phone: time runs down, the board on the left, the agent on the right; arrows are horizontal."""
    L = T[lang]
    o = []
    W, H = 340, 560
    Y0, Y1 = 132, 512

    def Y(x):
        return Y0 + (x - CH_T0) / (CH_T1 - CH_T0) * (Y1 - Y0)

    BAR, TRK_R, BR = 250, 136, 148
    o.append(f'<svg class="chn chn-t" viewBox="0 0 {W} {H}" role="img" aria-labelledby="chn-t-t chn-d">')
    o.append(f'<title id="chn-t-t">{esc(L["ch_t"])}</title>')
    o.append('<defs><marker id="ah-bl-t" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah-bl" d="M1 1L9 5L1 9"/></marker>'
             '<marker id="ah-tx-t" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path class="ah-tx" d="M1 1L9 5L1 9"/></marker></defs>')
    o.append(f'<text class="rl" x="8" y="20">{esc(L["ch_board"])}</text><text class="rs" x="8" y="40">{esc(L["ch_board_s"])}</text>')
    o.append(f'<text class="rl" x="{BAR - 12}" y="20">{esc(L["ch_agent"])}</text><text class="rs" x="{BAR - 12}" y="40">{esc(sub_nb(L["ch_agent_s"]))}</text>')
    o.append(f'<rect class="trk" x="4" y="58" width="{TRK_R - 4}" height="{Y1 - 58 + 10}" rx="14"/>')
    for i in range(3):
        o.append(f'<rect class="old" x="16" y="{72 + i * 14}" width="40" height="9" rx="3"/>')
    o.append(f'<text class="an" x="16" y="128">{esc(L["ch_old"])}</text>')
    for text, x in CH_E:
        w = pill_w(text)
        y = Y(x)
        o.append(f'<g class="en" data-t="{ct(x)}"><rect x="14" y="{n(y - 11)}" width="{w}" height="22" rx="6"/><text x="{n(14 + w / 2)}" y="{n(y)}" dy=".35em" text-anchor="middle">{text}</text></g>')
    ys = [Y0] + [Y(b) for b in CH_B] + [Y1]
    o.append('<g class="work">')
    for a, b in zip(ys[:-1], ys[1:]):
        a2 = a + (8 if a != Y0 else 0)
        o.append(f'<rect x="{BAR - 6}" y="{n(a2)}" width="12" height="{n(max(4, b - 8 - a2))}" rx="6"/>')
    o.append('</g>')
    o.append(f'<rect class="ph" data-axis="y" data-a="{Y0}" data-b="{Y1}" x="{BAR - 16}" y="{Y0}" width="32" height="2" rx="1"/>')
    yb0 = Y(CH_B[0])
    p1, p2 = L["ch_pull2"]
    o.append(f'<g class="pull" data-t="{ct(CH_B[0])}"><path d="M{BAR - 8} {n(yb0 - 4)}C{BAR - 60} {n(yb0 - 40)} 128 90 66 87" marker-end="url(#ah-bl-t)" marker-start="url(#ah-bl-t)"/>'
             f'<text x="{BAR + 16}" y="{n(yb0 + 22)}">{esc(p1)}</text><text x="{BAR + 16}" y="{n(yb0 + 38)}">{esc(p2)}</text></g>')
    for i, (a, b, bx) in enumerate(CH_G):
        ya, yb = Y(CH_E[a][1]), Y(bx)
        o.append(f'<g class="push" data-t="{ct(bx)}"><path d="M{TRK_R + 2} {n(ya)}H{BR}V{n(yb)}H{BAR - 12}" marker-end="url(#ah-bl-t)"/>'
                 f'<text x="{(BR + BAR) / 2 - 2}" y="{n(yb - 9)}" text-anchor="middle">{esc(L["ch_push"][i])}</text></g>')
    for b, lab in zip(CH_B, L["ch_b"]):
        y = Y(b)
        o.append(f'<g class="bd" data-t="{ct(b)}"><circle cx="{BAR}" cy="{n(y)}" r="6"/><text x="{BAR + 16}" y="{n(y)}" dy=".35em">{esc(lab)}</text></g>')
    o.append(f'<g class="tax"><path d="M{BAR} {Y1 + 10}V{Y1 + 30}" marker-end="url(#ah-tx-t)"/><text x="{BAR + 14}" y="{Y1 + 26}">{esc(L["ch_time"])}</text></g>')
    o.append('</svg>')
    return "\n".join(o)


def channels_svg(lang):
    return f'<p class="sr" id="chn-d">{esc(T[lang]["ch_d"])}</p>\n' + channels_wide(lang) + "\n" + channels_tall(lang)


# ---------------------------------------------------------------- Agensh: result by team size
PANDOC = [(1, 33.89), (8, 41.75), (32, 43.11), (128, 50.94), (1024, 55.06)]


def line_svg(lang):
    L = T[lang]
    W, H = 480, 290
    x0, x1, y0, y1 = 44, 452, 236, 26

    def X(v):
        return x0 + math.log2(v) / 10 * (x1 - x0)

    def Y(p):
        return y0 - (p - 30) / 30 * (y0 - y1)

    o = [f'<svg class="ln-svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="li-t li-d">',
         f'<desc id="li-d">{esc(L["li_d"])}</desc>',
         '<defs><linearGradient id="wash" x1="0" x2="0" y1="0" y2="1"><stop class="w0" offset="0"/><stop class="w1" offset="1"/></linearGradient></defs>']
    for p in (30, 40, 50, 60):
        o.append(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{n(Y(p))}" y2="{n(Y(p))}"/><text class="tky" x="{x0 - 10}" y="{n(Y(p))}" dy=".35em">{p}</text>')
    for v, _ in PANDOC:
        o.append(f'<text class="tk" x="{n(X(v))}" y="{y0 + 24}">{fnum(v, lang)}</text>')
    o.append(f'<text class="axl" x="{x1}" y="{y0 + 48}" text-anchor="end">{esc(L["li_axis"])}</text>')
    pts = " ".join(f"{n(X(v))},{n(Y(p))}" for v, p in PANDOC)
    area = f"M{n(X(1))} {y0}L" + "L".join(f"{n(X(v))} {n(Y(p))}" for v, p in PANDOC) + f"L{n(X(1024))} {y0}Z"
    o.append(f'<path class="area" d="{area}"/>')
    o.append(f'<polyline class="ln" points="{pts}" pathLength="1"/>')
    for (v, p), lab in zip(PANDOC, L["li_pts"]):
        val = fnum(p, lang, 2)
        lab = sub_nb(lab)
        o.append(f'<g class="pt" tabindex="0" role="img" aria-label="{esc(lab)}: {val}{esc(sub_nb(L["pct"]))}" data-v="{val}{esc(sub_nb(L["pct"]))}" data-label="{esc(lab)}">'
                 f'<circle class="hit" cx="{n(X(v))}" cy="{n(Y(p))}" r="16"/><circle class="mk" cx="{n(X(v))}" cy="{n(Y(p))}" r="5"/></g>')
    o.append(f'<text class="val" x="{n(X(1) + 2)}" y="{n(Y(33.89) + 26)}">{fnum(33.89, lang, 2)}</text>')
    o.append(f'<text class="val" x="{n(X(1024))}" y="{n(Y(55.06) - 16)}" text-anchor="end">{fnum(55.06, lang, 2)}</text>')
    o.append('</svg>')
    return "\n".join(o)


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


# ---------------------------------------------------------------- HTML sections for the index page
def hero_html(lang, ld, href):
    """href(work_id) -> link to the card on the site."""
    L = T[lang]
    nb = NB
    o = [f'<section class="hero auto" id="how" data-mode="ind" aria-labelledby="h1">',
         '<div class="copy">',
         f'<p class="eyebrow">{esc(L["eyebrow"].format(corpus=ld["corpus"], nb=nb))}</p>',
         f'<h1 id="h1">{L["h1"]}</h1>',
         f'<p class="deck">{esc(sub_nb(L["deck"]))}</p>',
         '</div>',
         '<figure class="stage" aria-labelledby="stage-cap"><div class="stage-art">',
         stage_svg("w", lang), stage_svg("n", lang),
         '</div><figcaption class="narr" id="stage-cap" data-beat="0"><div class="narr-head">']
    for m, num, name, *_ in L["modes"]:
        o.append(f'<span class="nm nm-{m}">{num} · {esc(name)}</span>')
    o.append('<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'
             f'<button class="pp" type="button" aria-label="{esc(L["pause"])}" data-pause="{esc(L["pause"])}" data-play="{esc(L["play"])}">'
             '<svg class="i-pause" viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="2" width="2.4" height="8" rx="1"/><rect x="7.1" y="2" width="2.4" height="8" rx="1"/></svg>'
             '<svg class="i-play" viewBox="0 0 12 12" aria-hidden="true"><path d="M3.5 2.2v7.6a.6.6 0 0 0 .9.5l6-3.8a.6.6 0 0 0 0-1l-6-3.8a.6.6 0 0 0-.9.5z"/></svg>'
             '</button></div><div class="beats-wrap">')
    for m in ("ind", "coord", "mem"):
        o.append(f'<ol class="beats beats-{m}">' + "".join(f"<li>{esc(b)}</li>" for b in L["beats"][m]) + "</ol>")
    o.append('</div></figcaption></figure>')
    icons = {
        "ind": '<path d="M4 6h11M4 12h11M4 18h11"/><rect x="17" y="9" width="5" height="6" rx="1.5"/>',
        "coord": '<circle cx="12" cy="12" r="3.2"/><path d="M12 8.8V3M12 15.2V21M8.9 10.4 4 7.5M15.1 13.6 20 16.5M8.9 13.6 4 16.5M15.1 10.4 20 7.5"/>',
        "mem": '<rect x="5" y="8.5" width="14" height="7" rx="2"/><path d="M7 3v5.5M12 3v5.5M17 3v5.5M7 15.5V21M12 15.5V21M17 15.5V21"/>',
    }
    o.append(f'<fieldset class="modes"><legend class="sr">{esc(L["modes_legend"])}</legend>')
    for m, num, name, tag, desc, ev, wid, more in L["modes"]:
        chk = " checked" if m == "ind" else ""
        link = f' <a class="evl" href="{href(wid)}">{esc(sub_nb(more))} →</a>' if wid else f' <a class="evl" href="#agensh">{esc(sub_nb(more))} ↓</a>'
        o.append(f'<div class="mode"><input type="radio" name="mode" id="m-{m}" value="{m}"{chk}>'
                 f'<label for="m-{m}"><svg class="mi" viewBox="0 0 24 24" aria-hidden="true">{icons[m]}</svg>'
                 f'<span class="mt">{esc(name)}</span><span class="mg">{esc(tag)}</span><span class="prog" aria-hidden="true"><i></i></span></label>'
                 f'<div class="md"><p>{esc(desc)}</p><p class="ev">{esc(sub_nb(ev))}{link}</p></div></div>')
    o.append('</fieldset></section>')
    data = {"agent": L["agent"], "live": L["live"], "rows": [[k, t] for k, t, _ in L["rows"][:2]]}
    o.append(f'<script type="application/json" id="story-i18n">{json.dumps(data, ensure_ascii=False)}</script>')
    return "\n".join(o)


def scale_html(lang, ld, href, ch1_title, ch1_href="ch01.html"):
    L = T[lang]
    kw = dict(corpus=ld["corpus"], known=ld["known"], nb=NB)
    o = ['<section class="sec" id="scale" aria-labelledby="h-scale"><header class="sec-head">',
         f'<p class="eyebrow">{esc(L["sc_eyebrow"])}</p><h2 id="h-scale">{esc(L["sc_h"])}</h2>',
         f'<p class="lede">{esc(L["sc_lede"].format(**kw))}</p></header>',
         '<div class="scale"><div class="hero-num">',
         f'<b>{fnum(ld["median"], lang)}</b><p>{esc(L["sc_unit"].format(**kw))}</p></div>',
         f'<figure class="ladder"><figcaption class="fig-t">{esc(L["sc_fig"].format(**kw))}</figcaption><ol>']
    for t, v in ld["rows"]:
        text, wid = L["sc_rows"][t]
        tip = L["sc_tip"].format(v=v, known=ld["known"])
        o.append(f'<li style="--v:{v};--of:{ld["known"]}"><span class="th">≥{NB}{fnum(t, lang)}</span>'
                 f'<span class="bar" data-tip="{esc(tip)}"><i></i></span><b class="v">{v}</b>'
                 f'<span class="ex">{sub_nb(text)} <a class="exl" href="{href(wid)}" aria-label="{esc(L["sc_card"])}">→</a></span></li>')
    o.append(f'</ol><p class="src">{sub_nb(L["sc_src"]).format(known=ld["known"], corpus=ld["corpus"], ch1=esc(ch1_title), ch1_href=ch1_href)}</p></figure></div></section>')
    return "\n".join(o)


def agensh_html(lang, href, ch5_title):
    L = T[lang]
    o = ['<section class="sec" id="agensh" aria-labelledby="h-agensh"><header class="sec-head">',
         f'<p class="eyebrow">{esc(L["ag_eyebrow"])}</p><h2 id="h-agensh">{esc(L["ag_h"])}</h2></header>',
         '<div class="read">' + "".join(f"<p>{sub_nb(p)}</p>" for p in L["ag_p1"]) + '</div>',
         f'<figure class="wide chn-fig"><figcaption class="fig-t">{esc(L["ag_fig"])}</figcaption><div class="chn-art">',
         channels_svg(lang), '</div><ul class="fig-key">',
         f'<li><span class="k k-push"></span>{esc(L["ag_key"][0])}</li><li><span class="k k-pull"></span>{esc(L["ag_key"][1])}</li></ul>',
         f'<p class="fig-note">{sub_nb(L["ag_note"])}</p></figure>',
         f'<div class="read"><h3>{esc(L["ag_h3"])}</h3>' + "".join(f"<p>{sub_nb(p)}</p>" for p in L["ag_p2"]) + '</div>',
         '<div class="result"><figure class="lchart" id="line-chart">',
         f'<figcaption class="fig-t" id="li-t">{esc(sub_nb(L["ag_chart"]))}</figcaption>', line_svg(lang),
         '<div class="tip" id="tip" aria-hidden="true"></div>',
         f'<ul class="rowvals" aria-label="{esc(L["ag_vals"])}">']
    for lab, (v, p) in zip(L["li_rows"], PANDOC):
        o.append(f'<li><span>{sub_nb(lab)}</span> <b>{fnum(p, lang, 2)}</b></li>')
    o.append(f'</ul><p class="src">{L["ag_src"]}</p></figure>')
    o.append(f'<aside class="cond" aria-labelledby="h-cond"><h3 id="h-cond">{esc(L["ag_cond"])}</h3><dl>'
             + "".join(f"<dt>{esc(a)}</dt><dd>{sub_nb(b)}</dd>" for a, b in L["ag_dl"]) + '</dl></aside></div>')
    more = sub_nb(L["ag_more"]).format(agensh=href("agensh-1024"), cc=href("anthropic-c-compiler"), opus=href("opus55-card"), ch5=esc(ch5_title))
    o.append(f'<p class="ag-more">{more}</p></section>')
    return "\n".join(o)


# ---------------------------------------------------------------- standalone SVG for the README
FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
PAL = {
    "dark": dict(bg="#0a0c0d", panel="#101416", panel_line="#1f2629", chip="#161b1d", line="#262d30", ink="#eef2ef", ink2="#b4bcb8", ink3="#7f8884",
                 head="#ffffff", em="#22a876", eml="#5fe3b3", am="#c08426", aml="#f1b65b", bl="#4b93e6", bll="#8ac6ff",
                 hot="#123527", slot="#3a4245", chip_line="#3a4245", hub="#1d1810", log="#0f1620", glow=".2", track="#18201d", grid="#1c2224"),
    "light": dict(bg="#f6f8f7", panel="#ffffff", panel_line="#dfe5e2", chip="#ffffff", line="#d5dcd8", ink="#0d1311", ink2="#3a433f", ink3="#68716d",
                  head="#070a09", em="#13895f", eml="#0f8a5c", am="#b06d0b", aml="#c47b12", bl="#2b6fd0", bll="#2b6fd0",
                  hot="#e1f4ea", slot="#d3dad6", chip_line="#c9d1cd", hub="#fff4e2", log="#eef5ff", glow=".1", track="#e3ece7", grid="#e4e9e6"),
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


def poster_panel(mode, ox, oy, lang, C):
    L = T[lang]
    W, H, cw, chh = 448, 330, 112, 40
    g = Geo(W, H, cw, chh, 8, tag_room=22, coll=84, hub=(150, 76), card=(312, 136), gap=12)
    know = L["po_know"][mode]
    o = [f'<g transform="translate({ox} {oy})">']
    if mode == "ind":
        for k in AG:
            hot = k in know
            o.append(f'<path d="{g.lane(k)}" fill="none" stroke="{C["eml"] if hot else C["line"]}" stroke-opacity="{.55 if hot else 1}" stroke-width="{1.6 if hot else 1.2}"/>')
        cx, cy = g.coll
        s = g.coll_size
        o.append(f'<rect x="{n(cx - s / 2)}" y="{n(cy - s / 2)}" width="{s}" height="{s}" rx="20" fill="{C["chip"]}" stroke="{C["ink3"]}" stroke-opacity=".6"/>')
        for k in AG:
            col, row = (k - 1) % 3, (k - 1) // 3
            o.append(f'<rect x="{n(cx - 32 + col * 23)}" y="{n(cy - 20 + row * 23)}" width="18" height="18" rx="5" fill="{C["em"] if k in know else C["slot"]}"/>')
        o.append(f'<text x="{n(cx)}" y="{n(cy + s / 2 + 26)}" text-anchor="middle" font-family="{FONT}" font-size="18" font-weight="600" fill="{C["ink"]}">{esc(L["sel"])}</text>')
    elif mode == "coord":
        for k in AG:
            hot = k in know
            mk = ' marker-end="url(#pa)"' if k == 3 else (' marker-start="url(#pa)"' if hot else "")
            o.append(f'<path d="{g.spoke(k)}" fill="none" stroke="{C["eml"] if hot else C["aml"]}" stroke-opacity="{.9 if hot else .35}" stroke-width="{2 if hot else 1.3}"{mk}/>')
        hx, hy = g.hub
        hw, hh = g.hub_size
        o.append(f'<rect x="{n(hx - hw / 2)}" y="{n(hy - hh / 2)}" width="{hw}" height="{hh}" rx="20" fill="{C["hub"]}" stroke="{C["aml"]}" stroke-width="1.6"/>')
        o.append(f'<text x="{n(hx)}" y="{n(hy - 6)}" text-anchor="middle" font-family="{FONT}" font-size="19" font-weight="600" fill="{C["ink"]}">{esc(L["hub"])}</text>')
        o.append(f'<rect x="{n(hx - 52)}" y="{n(hy + 10)}" width="104" height="6" rx="3" fill="{C["am"]}" fill-opacity=".25"/><rect x="{n(hx - 52)}" y="{n(hy + 10)}" width="90" height="6" rx="3" fill="{C["aml"]}"/>')
    else:
        for k in AG:
            hot = k in know
            mk = ' marker-end="url(#pa)"' if k == 3 else (' marker-start="url(#pa)"' if hot else "")
            dash = ' stroke-dasharray="5 5"' if hot and k != 3 else ""
            o.append(f'<path d="{g.conn(k)}" fill="none" stroke="{C["eml"] if hot else C["bll"]}" stroke-opacity="{.9 if hot else .35}" stroke-width="{2 if hot else 1.3}"{dash}{mk}/>')
        mx, my = g.card
        cw2, chh2 = g.card_size
        o.append(f'<rect x="{n(mx - cw2 / 2)}" y="{n(my - chh2 / 2)}" width="{cw2}" height="{chh2}" rx="18" fill="{C["log"]}" stroke="{C["bll"]}" stroke-opacity=".7" stroke-width="1.4"/>')
        o.append(f'<text x="{n(mx - cw2 / 2 + 18)}" y="{n(my - chh2 / 2 + 30)}" font-family="{FONT}" font-size="16" font-weight="600" fill="{C["bll"]}">{esc(L["log"])}</text>')
        for j, (k, t, hot) in enumerate(L["po_rows"]):
            yy = my - chh2 / 2 + 62 + j * 26
            if hot:
                o.append(f'<rect x="{n(mx - cw2 / 2 + 8)}" y="{n(yy - 12)}" width="{cw2 - 16}" height="24" rx="8" fill="{C["em"]}" fill-opacity=".16"/>')
            o.append(f'<circle cx="{n(mx - cw2 / 2 + 22)}" cy="{n(yy)}" r="4" fill="{C["eml"] if hot else C["ink3"]}"/>'
                     f'<text x="{n(mx - cw2 / 2 + 34)}" y="{n(yy)}" dy=".35em" font-family="{FONT}" font-size="16" fill="{C["ink"] if hot else C["ink2"]}">{esc(L["agent"].format(k=k))} · {esc(t)}</text>')
    pos = g.pos(mode)
    for k in AG:
        x, y = pos[k]
        hot = k in know
        dash = ' stroke-dasharray="4 4"' if (mode == "ind" and k in (1, 5)) else ""
        o.append(f'<rect x="{n(x - cw / 2)}" y="{n(y - chh / 2)}" width="{cw}" height="{chh}" rx="{chh / 2}" fill="{C["hot"] if hot else C["chip"]}" stroke="{C["eml"] if hot else C["chip_line"]}" stroke-width="{1.6 if hot else 1.2}"{dash}/>')
        o.append(f'<circle cx="{n(x - 36)}" cy="{n(y)}" r="5" fill="{C["eml"] if hot else C["ink3"]}"/>'
                 f'<text x="{n(x - 24)}" y="{n(y)}" dy=".35em" font-family="{FONT}" font-size="18" font-weight="600" fill="{C["ink"]}">{esc(L["agent"].format(k=k))}</text>')
        if hot:
            label = know[k]
            w = tag_w(label, 14)
            below = (mode == "coord" and k in (4, 5)) or (mode == "mem" and k in (4, 5, 6))
            tx_, ty_ = x, y + (chh / 2 + 17) * (1 if below else -1)
            if mode == "ind":  # the column between agents is tight, so the tag sits on the lane to the right
                tx_, ty_ = x + cw / 2 + 14 + w / 2, y
            o.append(f'<rect x="{n(tx_ - w / 2)}" y="{n(ty_ - 11)}" width="{w}" height="22" rx="11" fill="{C["panel"]}" stroke="{C["eml"]}" stroke-opacity=".5"/>'
                     f'<text x="{n(tx_)}" y="{n(ty_)}" dy=".35em" text-anchor="middle" font-family="{FONT}" font-size="14" fill="{C["eml"]}">{esc(label)}</text>')
    o.append("</g>")
    return "\n".join(o)


def poster_svg(lang, theme, corpus):
    L = T[lang]
    C = PAL[theme]
    W, H = 1600, 900
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["po_t1"])} {esc(L["po_t2"])}</title>',
         f'<desc id="d">{esc(L["po_desc"])}</desc>',
         f'<defs><marker id="pa" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M1 1L9 5L1 9" fill="none" stroke="{C["eml"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></marker>'
         f'<radialGradient id="glow" cx="78%" cy="0%" r="75%"><stop offset="0" stop-color="{C["em"]}" stop-opacity="{C["glow"]}"/><stop offset="1" stop-color="{C["em"]}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="32" fill="{C["bg"]}"/><rect width="{W}" height="{H}" rx="32" fill="url(#glow)"/>',
         f'<g transform="translate(64 62)"><circle cx="14" cy="14" r="10" fill="none" stroke="{C["em"]}" stroke-width="3.5"/><circle cx="24" cy="14" r="3.6" fill="{C["eml"]}"/></g>',
         f'<text x="104" y="84" font-family="{FONT}" font-size="22" font-weight="600" fill="{C["ink2"]}">{esc(L["po_brand"])} <tspan fill="{C["ink3"]}" font-weight="400">{esc(L["po_brand2"].format(corpus=corpus))}</tspan></text>',
         f'<text x="64" y="170" font-family="{FONT}" font-size="60" font-weight="650" letter-spacing="-2" fill="{C["head"]}">{esc(L["po_t1"])}</text>',
         f'<text x="64" y="240" font-family="{FONT}" font-size="60" font-weight="650" letter-spacing="-2" fill="{C["ink3"]}">{esc(L["po_t2"])}</text>',
         f'<g transform="translate(1188 150)"><circle cx="8" cy="0" r="7" fill="{C["eml"]}"/><text x="26" y="0" dy=".35em" font-family="{FONT}" font-size="21" fill="{C["ink2"]}">{esc(L["po_leg"][0])}</text></g>',
         f'<g transform="translate(1188 190)"><rect x="0" y="-9" width="17" height="18" rx="9" fill="none" stroke="{C["eml"]}" stroke-dasharray="4 4" stroke-width="1.6"/><text x="26" y="0" dy=".35em" font-family="{FONT}" font-size="21" fill="{C["ink2"]}">{esc(L["po_leg"][1])}</text></g>']
    pw, ph, gap, x0, y0 = 472, 556, 28, 64, 280
    for i, (mode, num, title, tag, cap) in enumerate(L["po_panels"]):
        x = x0 + i * (pw + gap)
        o.append(f'<rect x="{x}" y="{y0}" width="{pw}" height="{ph}" rx="24" fill="{C["panel"]}" stroke="{C["panel_line"]}"/>')
        o.append(f'<text x="{x + 28}" y="{y0 + 50}" font-family="{MONO}" font-size="17" fill="{C["ink3"]}">{num}</text>'
                 f'<text x="{x + 64}" y="{y0 + 51}" font-family="{FONT}" font-size="29" font-weight="650" letter-spacing="-.6" fill="{C["ink"]}">{esc(title)}</text>'
                 f'<text x="{x + 64}" y="{y0 + 80}" font-family="{FONT}" font-size="19" fill="{C["ink3"]}">{esc(tag)}</text>')
        o.append(poster_panel(mode, x + 12, y0 + 100, lang, C))
        lines = wrap(cap, pw - 56, 19)
        assert len(lines) <= 3, ("poster caption too long", cap)
        for j, line in enumerate(lines):
            o.append(f'<text x="{x + 28}" y="{y0 + 470 + j * 27}" font-family="{FONT}" font-size="19" fill="{C["ink2"]}">{esc(line)}</text>')
    o.append(f'<text x="64" y="870" font-family="{FONT}" font-size="19" fill="{C["ink3"]}">{esc(L["po_foot"])}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def scale_chart_svg(lang, theme, ld):
    """README: the scale ladder as a standalone horizontal bar chart."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1200, 520
    kw = dict(known=ld["known"], corpus=ld["corpus"], med=fnum(ld["median"], lang))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["rs_t"])}</title>',
         f'<desc id="d">{esc(L["rs_s"].format(**kw))}. ' + "; ".join(f"≥{fnum(t, lang)}: {v}" for t, v in ld["rows"]) + '.</desc>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>',
         f'<text x="56" y="86" font-family="{FONT}" font-size="40" font-weight="650" letter-spacing="-1.2" fill="{C["head"]}">{esc(L["rs_t"])}</text>',
         f'<text x="56" y="128" font-family="{FONT}" font-size="21" fill="{C["ink3"]}">{esc(L["rs_s"].format(**kw))}</text>']
    # median block
    o.append(f'<rect x="56" y="168" width="44" height="4" rx="2" fill="{C["eml"]}"/>')
    o.append(f'<text x="50" y="330" font-family="{FONT}" font-size="168" font-weight="650" letter-spacing="-8" fill="{C["head"]}">{fnum(ld["median"], lang)}</text>')
    med_lab = {"ru": ["агентов —", "медианный рой"], "en": ["agents in the", "median swarm"]}[lang]
    for j, s in enumerate(med_lab):
        o.append(f'<text x="56" y="{384 + j * 30}" font-family="{FONT}" font-size="22" fill="{C["ink2"]}">{esc(s)}</text>')
    bx, bw, top, rh = 470, 470, 196, 70
    o.append(f'<text x="330" y="{top - 22}" font-family="{FONT}" font-size="18" fill="{C["ink3"]}">{esc(L["rs_axis"])}</text>')
    for i, (t, v) in enumerate(ld["rows"]):
        y = top + i * rh
        o.append(f'<line x1="330" x2="{W - 56}" y1="{y}" y2="{y}" stroke="{C["grid"]}"/>')
        o.append(f'<text x="330" y="{y + rh / 2}" dy=".35em" font-family="{MONO}" font-size="20" fill="{C["ink2"]}">≥{NB}{fnum(t, lang)}</text>')
        o.append(f'<rect x="{bx}" y="{y + rh / 2 - 13}" width="{bw}" height="26" rx="5" fill="{C["track"]}"/>')
        o.append(f'<rect x="{bx}" y="{y + rh / 2 - 13}" width="{n(max(6, bw * v / ld["known"]))}" height="26" rx="5" fill="{C["em"]}"/>')
        o.append(f'<text x="{bx + bw + 28}" y="{y + rh / 2}" dy=".35em" font-family="{FONT}" font-size="30" font-weight="650" fill="{C["head"]}">{v}</text>')
    y = top + len(ld["rows"]) * rh
    o.append(f'<line x1="330" x2="{W - 56}" y1="{y}" y2="{y}" stroke="{C["grid"]}"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def pandoc_chart_svg(lang, theme):
    """README: the Agensh pandoc curve as a standalone line chart."""
    L = T[lang]
    C = PAL[theme]
    W, H = 1200, 560
    x0, x1, y0, y1 = 120, 1100, 470, 190

    def X(v):
        return x0 + math.log2(v) / 10 * (x1 - x0)

    def Y(p):
        return y0 - (p - 30) / 30 * (y0 - y1)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
         f'<title id="t">{esc(L["rp_t"])}</title>', f'<desc id="d">{esc(L["li_d"])}</desc>',
         f'<defs><linearGradient id="wash" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{C["em"]}" stop-opacity=".22"/><stop offset="1" stop-color="{C["em"]}" stop-opacity="0"/></linearGradient></defs>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{C["bg"]}"/>',
         f'<text x="56" y="86" font-family="{FONT}" font-size="40" font-weight="650" letter-spacing="-1.2" fill="{C["head"]}">{esc(L["rp_t"])}</text>',
         f'<text x="56" y="128" font-family="{FONT}" font-size="21" fill="{C["ink3"]}">{esc(L["rp_s"])}</text>']
    for p in (30, 40, 50, 60):
        o.append(f'<line x1="{x0}" x2="{x1}" y1="{n(Y(p))}" y2="{n(Y(p))}" stroke="{C["grid"]}"/>'
                 f'<text x="{x0 - 18}" y="{n(Y(p))}" dy=".35em" text-anchor="end" font-family="{MONO}" font-size="18" fill="{C["ink3"]}">{p}</text>')
    for v, _ in PANDOC:
        o.append(f'<text x="{n(X(v))}" y="{y0 + 34}" text-anchor="middle" font-family="{MONO}" font-size="18" fill="{C["ink3"]}">{fnum(v, lang)}</text>')
    o.append(f'<text x="{x1}" y="{y0 + 66}" text-anchor="end" font-family="{FONT}" font-size="18" fill="{C["ink3"]}">{esc(L["li_axis"])} · {esc(L["rp_src"])}</text>')
    area = f"M{n(X(1))} {y0}L" + "L".join(f"{n(X(v))} {n(Y(p))}" for v, p in PANDOC) + f"L{n(X(1024))} {y0}Z"
    o.append(f'<path d="{area}" fill="url(#wash)"/>')
    o.append(f'<polyline points="{" ".join(f"{n(X(v))},{n(Y(p))}" for v, p in PANDOC)}" fill="none" stroke="{C["em"]}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
    for v, p in PANDOC:
        o.append(f'<circle cx="{n(X(v))}" cy="{n(Y(p))}" r="8" fill="{C["em"]}" stroke="{C["bg"]}" stroke-width="3"/>'
                 f'<text x="{n(X(v))}" y="{n(Y(p) - 22)}" text-anchor="middle" font-family="{FONT}" font-size="22" font-weight="650" fill="{C["head"]}">{fnum(p, lang, 2)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def load_works():
    return json.load(open(os.path.join(ROOT, "data", "works.json"), encoding="utf-8"))["works"]


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
                              (f"agensh-pandoc-{lang}-{theme}.svg", pandoc_chart_svg(lang, theme))):
                p = os.path.join(out_dir, name)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(svg)
                files.append(p)
    return files


if __name__ == "__main__":
    for p in write_illustrations():
        print(os.path.relpath(p, ROOT), os.path.getsize(p))
    assert not re.search(r"\{\w+\}", open(os.path.join(ROOT, "assets", "illustrations", "topologies-en-dark.svg"), encoding="utf-8").read())

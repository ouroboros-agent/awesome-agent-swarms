# Showcase videos and first-screen checks of the Field page

Everything here opens the built page from its file in a real engine (Playwright's Chromium and WebKit) and lets the
page draw itself. Nothing is installed or fetched; any request other than `file:`, `data:`, `about:` or `blob:` is
refused and reported. `ffmpeg` and `ffprobe` are needed for the videos.

| file | what it does |
|---|---|
| `vclock.js` | A deterministic clock, installed before the page's scripts. The page keeps asking for animation frames, reading the time and starting CSS transitions; this file decides when "now" is. One call advances the page by one video frame: canvas, CSS transitions (through the Web Animations API) and the tab strip's smooth scroll move on the same clock. `Math.random` is a seeded generator, so the page's dice fall the same way in every capture. |
| `stage.py` | Opens the page on that clock; reads where its steps are and where a reader arrives at each; makes the capture copy for the phone video. |
| `render.py` | The two videos. The storyboards are the functions `tour()` and `teaser()`. |
| `survey.py` | One still of every state of the page at one window size (45 frames and a sheet): for choosing shots and for looking at a layout. |
| `hero_probe.py` | Measures and photographs the first screen at 14 phone and 9 tablet and desktop window sizes, four schemes each, in both engines and languages; `--states` adds reduced motion, turning the phone, a hiding browser bar, arrival at the address of the second state, no JavaScript, and the keyboard on a first screen taller than its window; `--strict` fails on a defect. |

## The videos

```sh
make field                                   # the pages the videos are taken from
python scripts/showcase/render.py OUT --kind mobile     # OUT/swarm-dynamics-tour-mobile-ru.mp4   1080x1920, WebKit
python scripts/showcase/render.py OUT --kind desktop    # OUT/swarm-dynamics-tour-desktop-ru.mp4  1920x1080, Chromium
python scripts/showcase/render.py OUT --kind mobile --board teaser    # OUT/swarm-dynamics-mobile-ru.mp4
```

Two storyboards. `tour` (the default) shows every part of the page in 24.75 s: the four schemes of the first screen,
"delivered is not read", the pull-out to 1,024 agents, the scale of real swarms, the growth curve and a hundred agents
spent three ways, self-organisation (the board of claims, the steps 8, 128 and 1,024 with the integrators that appear,
their merges into main), memory (three kinds of store when authors leave, a record published, a record found after its
author is gone), beliefs (an idea that spreads, the paragraph that stops it, a cascade, collusion compared across
models), the map. The run fails if any of these parts is on screen for less than a fifth of a second in the frames it
took (`parts` in the timeline file). Not shown: 21 further states of the same scenes (14 of the 36 steps are shown)
and the closing step with its four questions. `teaser` is the selection of 15 November 2026 (the first screen,
the scale, the growth curve, a spreading idea, the map: 23.9 s), kept as it was.

`--lang en` takes the English page; `--preview --strip 12` renders at 1x with a sheet of every twelfth frame, for
working on the storyboard; `--reencode` repeats only the delivery encode from the lossless master of an earlier run
(`--work DIR`, default `OUT/work`). There is no real-time waiting, and the page's random choices are seeded.
Bit-identical MP4 output is not guaranteed: on 15 November 2026 the retained `teaser` repeats matched,
while the retained second `tour` runs had different file hashes. The cause of that difference was not established.

What is and is not the page's own in a video:

- **Every frame is a photograph of the page** in the engine named in `<name>.timeline.json`. Nothing is drawn,
  retouched or laid over it; there is no title card, caption or logo that the page does not show itself.
- **The camera is the scroll position.** Inside one part of the page the scroll is eased, as a reader's would be.
  Between distant parts the page is jumped with `scrollTo` (listed under `storyboard.moves` with equal start and end
  times; three jumps in `teaser`, thirteen in `tour`): the reader would scroll through up to thirty screens there. The
  page answers a jump itself, re-forming its 1,024 dots into the next figure. In `tour` a jump lands where a reader
  arrives at that step: where a card's text is taller than its box and moves inside it, at the text's first line (from
  the step just before: at the step's top, where the previous card has left the window).
- **The page's clock runs faster than the video's** (`storyboard.speeds`; per shot under `shots`). `teaser`: about 2x
  while the four schemes of the first screen play, 1x during the pull-out to 1,024 agents, 1.1x to 2.2x elsewhere; the
  page moves from one scheme to the next by itself, and the remainder of a scheme's time, in which nothing moves, is
  passed in a quarter of a second. `tour`: 2.8x to 5.4x on the first screen, where each scheme is chosen by a click on
  its tab, as a reader chooses one; 1x during the pull-out; 1.4x to 5x in the scenes, so that every counter the page
  animates is seen at its final value (70% and 1% of the spreading idea, 11,111 and 2,800 pull requests) before the
  video moves on. A faster clock is made of more of the page's own frames (never a step longer than 40 ms), of which
  the last is photographed.
- **`tour` takes its first frame 1.05 s after the page has opened**, when the six agents stand in their places and
  agent 3 has found its solution: the first frame is what a player shows before the video starts.
- **Phone video only: the canvas is drawn at the capture resolution.** The page draws its canvas at no more than two
  device pixels per CSS pixel; a 432x768 window at 1080x1920 needs 2.5. `stage.capture_copy` raises that one number in
  a copy of the page (kept in the work folder); geometry, timing and every drawing call are unchanged. The desktop
  video (1280x720 at 1.5) is taken from the page as built.
- The window sizes are a large phone's browser area (432x768 CSS px) and a laptop's (1280x720).

`<name>.timeline.json` records, for every frame, the video time, the page's time, the scroll position, the selected
scheme and the active step; under `shots`, each shot with its seconds of video and of the page; under `parts`, each
part of the page a storyboard promises with the frames that show it; under `coverage`, which of the four schemes were
on the first screen and which steps were shown. `stills/` holds full-size frames: the last frame of each shot (`tour`),
or the frame half a second after each storyboard mark (`teaser`).

## The first screen

```sh
make qa-first-screen                         # = hero_probe.py qa/first-screen --label site --strict --states ...
python scripts/showcase/hero_probe.py OUT --label before --page ru=OLD/ru/index.html --page en=OLD/en/index.html
```

Per frame: the radius of the agents' circles, the bounding box of what the canvas shows, canvas ink behind the page's
own text lines, intro lines over tab or caption lines, canvas labels whose boxes intersect or reach into a circle,
script errors, and whether the page still asks for a next frame. On a window where the first screen is taller than the
window (`--hx` in the page), each scheme is measured at the top and after its excess has been scrolled in twelve
steps. `fold-280x653` is measured but not judged: at 280 px the width limits the figure and its longest chip still
reaches a neighbouring circle by about 3 px.

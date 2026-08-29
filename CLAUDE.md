# Pairwell — architecture notes

A private PWA for Philipp & Eunice. Four tools: Skincare, Hair, Workout, Kitchen.

**Live:** https://glowgiver.github.io/pairwell/ · repo `glowgiver/pairwell` (public)

Product language is **English** throughout — interface, data, commit messages.
Exercise vocabulary stays as it is ("RIR", "Hip Thrust"); that is the language
spoken in the gym. Ingredient names stay German; that is what is on the packet.

## Architecture — read before changing anything

**Two layers, decided deliberately** (not up for revisiting unless you raise it):

1. **`data/*.json`** — the truth. Routines, recipes, training plans, targets.
   No HTML, no styling, no UI logic.

2. **`hub/**/index.html`** — the display. Self-contained pages that work offline
   once the service worker has cached them. No runtime fetch of JSON.

**Why no runtime fetch:** offline reliability in a gym or a bathroom matters more
than loading one source live. Note the honest detail: the build scripts *inline*
the JSON as `const T = {…}` and render in the browser, so these are small
single-page apps with embedded data, not pre-rendered HTML. They are blank
without JavaScript.

**The bridge is `scripts/build_*.py`.** A manual step, no watcher.

```
data/*.json  --[scripts/build_*.py]-->  hub/**/index.html
```

## Layout

```
pairwell/
├── data/
│   ├── profiles.json      daily targets, mirror-meal logic
│   ├── training.json      14 sessions; still holds full exercise objects
│   ├── exercises.json     canonical library — 43 movements, one cue, one demo video
│   ├── routines.json      skincare (both people, two different shapes) + hair
│   └── kitchen.json       standards + Asian Base Block; no recipes yet
│
├── scripts/
│   ├── build_workout_page.py    training.json + exercises.json → workout page
│   ├── build_routines_page.py   routines.json → skincare + hair pages
│   ├── recompute_macros.py      derives kitchen macros; holds no data itself
│   ├── check_routine_rules.py   checks the seasonal plan against its own rules
│   ├── verify_videos.py         re-checks all 43 demo links for rot
│   └── _archive/                one-time migration; refuses to run
│
└── hub/
    ├── index.html         dashboard
    ├── app.css            the one palette — pages must not redefine tokens
    ├── app.js             the one person model (PW.get / PW.set / mountSwitcher)
    ├── manifest.json · sw.js · icons/
    ├── skincare/ · hair/ · workout/     built
    └── kitchen/                          placeholder — needs a recipe model first
```

## Person handling

`hub/app.js` owns it. A two-pill switcher on every page writes
`localStorage["hub.person"]` as `"P"` or `"E"`, and pages re-render on the
`pw:person` event. There is no first-run prompt — it defaults to Philipp and one
tap changes it.

The application is **not** built twice. One page per module; the person is a
parameter of the display, like location is in the workout module. Hair and
Kitchen are shared and say so rather than duplicating.

Note on storage: Safari's 7-day eviction of script-written data hits
`localStorage` and IndexedDB equally, so switching API does not help. Installed
home-screen web apps are exempt, which is how Pairwell is used. If logging is
ever added, IndexedDB plus an export button is the plan — the export is the
real safeguard.

## Two routine shapes

`routines.json` carries a `_model` field per person because they differ:

- **philipp** `weekly` — one AM routine, one active per weekday. His PM *step
  sequence* is still not recorded, only the active; the page says so rather than
  inventing steps.
- **eunice** `seasonal-weekly` — four seasons, each with its own AM routine and a
  different PM protocol for all seven days. The page resolves today's season
  first and shows only that.

Safety rules are data, with an `appliesTo` field so they surface on the day they
govern. A scoped rule shows only on its days; an unscoped critical rule shows
daily; advisory ones live in the disclosure.

## Style

Dark theme, tokens in `hub/app.css`. Accents: `--skin` teal, `--hair` violet,
`--train` blue, `--food` orange; `--philipp` blue, `--eunice` violet.

Rules learned the hard way:

- **Type floor.** 13px for secondary, 15px+ for anything actionable. The workout
  page still violates this (8.5–10.5px) and is due a typography pass.
- **44px minimum touch targets** (`var(--tap)`).
- **Real `<button>`s** with `aria-pressed` / `aria-selected`, never click-handling
  `<div>`s.
- **Escape everything** interpolated into `innerHTML` via `esc()`.
- Every page: `← Hub` link top left, the person switcher top right.

## Privacy

Zero external requests. No analytics, no CDN, no web fonts. Demo videos are
plain links with `rel="noopener"`, never iframes — an embed would contact
YouTube for every exercise on the page.

**The site is public.** Nothing identifying belongs in `data/`: no addresses,
postcodes, workplaces, or route descriptions. Personal routines and targets are
fine; anything that could locate a person is not. This was cleaned up once
already — see the "Generalise locating detail" commit.

## Deploying

`main` holds the project. The site is served from the **`gh-pages` branch**,
which contains the contents of `hub/` at its root.

```bash
python3 scripts/build_workout_page.py
python3 scripts/build_routines_page.py
# bump `const CACHE = "hub-vX"` in hub/sw.js
git add -A && git commit -m "..."
git push
git subtree push --prefix hub origin gh-pages
```

Bumping the cache version is what makes both phones pick up the change. The
fetch strategy is stale-while-revalidate, so a stale phone self-corrects on the
*next* open — but bump it anyway.

## Known gaps

- **Kitchen has no recipes.** `cookedWeightG` for the Asian Base Block is an
  estimate; weigh a batch and re-run `recompute_macros.py`. The custom food in
  MacroFactor may still hold the old 105 kcal/100 g — it should be 140.
- **No Today screen.** `weeklyRhythm`, the seasonal plans and `am.steps` are all
  present and unused. This is the highest-value next build.
- **Sessions still duplicate exercise objects** instead of referencing
  `exercises.json` by id.
- **Philipp's PM steps** are unrecorded.
- **Demo videos are verified live, not verified good** — nobody has watched them.

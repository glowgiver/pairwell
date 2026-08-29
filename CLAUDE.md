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
│   ├── build_hub_page.py        all four sources → the Today screen
│   ├── build_workout_page.py    training.json + exercises.json → workout page
│   ├── build_routines_page.py   routines.json → skincare + hair pages
│   ├── build_kitchen_page.py    kitchen.json → splitter + method
│   ├── recompute_macros.py      derives kitchen macros; holds no data itself
│   ├── check_routine_rules.py   checks both protocols against their own rules
│   ├── verify_videos.py         re-checks all 43 demo links for rot
│   ├── make_backup_doc.py       routines.json → backups/ standalone HTML
│   └── _archive/                one-time migration; refuses to run
│
├── sources/               GITIGNORED — the original documents the data came
│                          from. Two still contain the locating detail that was
│                          scrubbed in 9bf4883, so they must never be committed.
│                          Kept because three transcriptions lost content and
│                          only the originals revealed it.
│
├── backups/               generated, self-contained, committed
│
└── hub/
    ├── index.html         dashboard
    ├── app.css            the one palette — pages must not redefine tokens
    ├── app.js             the one person model (PW.get / PW.set / mountSwitcher)
    ├── manifest.json · sw.js · icons/
    └── skincare/ · hair/ · workout/ · kitchen/   all generated
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

- **philipp** `weekly-phased` — one 5-step AM routine, and a fixed 6-step PM
  base where only step 03 rotates. The weekday schedule itself changes across
  three phases (adapalene 2×/week in weeks 1–4, 3× from week 5), so the page
  resolves the phase before it resolves the day. Phase is per-person state in
  `localStorage`, not a fact about the protocol.
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

- **Type floor.** 13px for secondary, 15px+ for anything actionable. All five
  pages hold this. The single exception is the bottom-bar labels at 12px, where
  the 22px icon carries the meaning and the target is 58px.
- **Contrast.** Everything clears WCAG AA (4.5:1) against its *composited*
  background. Note the trap: white on `--skin` / `--hair` / `--train` / `--food`
  fails (1.78–3.24) — those accents are built to carry dark text. Filled chips
  and active pills use `var(--bg)` as ink.
- **Three type roles**, all device-resident because web fonts are banned here:
  `--f-ui` for what you scan, `--f-read` for what you read, `--f-data` for what
  you check. Numbers get `font-variant-numeric: tabular-nums`.
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
python3 scripts/build_hub_page.py       # Today screen
python3 scripts/build_routines_page.py  # skincare + hair
python3 scripts/build_workout_page.py
python3 scripts/build_kitchen_page.py
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
- **Kitchen has one recipe, not a library.** The Base Block and the splitter
  work; actual dishes are still to be written.
- **No MacroFactor import.** Designed in the product audit, not built. No export
  file has ever been seen, so the importer must discover the schema rather than
  assume column names.
- **Sessions still duplicate exercise objects** instead of referencing
  `exercises.json` by id.
- **Demo videos are verified live, not verified good** — nobody has watched them.
  `verify_videos.py` confirms each link resolves and that the title and channel
  still match what was recorded; it cannot confirm the video shows good form.

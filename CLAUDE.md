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
│   ├── kitchen.json       standards + Asian Base Block + energyFactors
│   ├── foods.json         58 ingredients, per 100 g — so recipes hold no macros
│   └── recipes.json       dishes as amounts only; macros derived, never typed
│
├── scripts/
│   ├── build_hub_page.py        all four sources → the Today screen
│   ├── build_workout_page.py    training.json + exercises.json → workout page
│   ├── build_routines_page.py   routines.json → skincare + hair pages
│   ├── build_kitchen_page.py    kitchen.json → splitter + method
│   ├── recompute_macros.py      derives kitchen macros; holds no data itself
│   ├── read_inbox.py            inbox/*.md → recipes.json, blocking on unknowns
│   ├── adapt_recipe.py          fits a found recipe to the mirror-meal target
│   ├── check_targets.py         are the targets themselves arithmetically possible?
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
├── inbox/                 GITIGNORED except TEMPLATE.md — recipes as found,
│                          one dish per file, before they become data
│
├── private/               GITIGNORED — body.json (weight, body fat, age,
│                          steps) and MacroFactor exports. Anything describing
│                          a body rather than a plan. check_targets.py is the
│                          only reader; no build script may inline it.
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

Tokens in `hub/app.css`, **two themes**. Accents: `--skin` teal, `--hair`
violet, `--train` blue, `--food` orange; `--philipp` blue, `--eunice` violet.

The themes invert rather than merely darken: dark mode uses pale accents
carrying dark ink, light mode uses deep accents carrying near-white ink.
Because filled chips take their ink from `var(--bg)`, that flip needs no
per-theme special-casing in any page. Three states — `auto` (stamps nothing,
follows the OS), `light` and `dark` stamp `data-theme` on `<html>`. The toggle
sits beside the person switcher and cycles them.

Two traps this exposed, both worth remembering:

- **Never hardcode ink on a filled accent.** `rgba(11,18,32,.75)` looked right
  in dark mode and became dark-on-dark in light mode. Inherit and vary weight.
- **Transparency on a filled pill fails somewhere.** At `.75` the light/teal
  combination hits 3.60 and the dark/blue one 4.00. Full opacity passes all
  eight combinations.
- **The same applies to the shell, and worse.** The bottom bar was a frosted
  92% panel; what scrolls under it decides the composite, so the inactive
  labels measured 4.91 over the page ground and 4.19 over dark ink. A ratio
  that depends on scroll position is not a ratio. The bar is opaque now and
  there is no `color-mix` left in `hub/`.

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

## Recipes — the division of labour

They find dishes; the repo decides the grams. A recipe is stored as **amounts
only**. `scripts/adapt_recipe.py` derives every macro from `foods.json`, then
scales exactly two things — the ingredients tagged `role: "protein"` and those
tagged `role: "fiber"` — to hit the target. Aromatics, sauce and vegetables are
the dish's character and are never touched.

It solves both targets **simultaneously**, not one after the other: legumes carry
protein and meat carries no fibre, so sequential adjustment overshoots. Two
equations, two unknowns. Then it rounds to weighable amounts and re-derives from
the rounded grams, so the report describes the food that will actually be cooked.

When rescaling cannot reach the target — usually because the dish has no
fibre source at all — the adapter does not stop at saying so. It proposes what
to **add**, in grams, from a curated shortlist in `kitchen.json` (`topUps`),
then **re-fits the whole dish around the addition**. That second step is the
point: 125 g of lentils brings 12 g of protein with its fibre, so the chicken
has to come down, and reporting the addition without re-solving would repeat
the sequential mistake `solve()` exists to avoid.

Two rules keep the shortlist honest:

- **It is curated, not derived.** `foods.json` knows psyllium husk is 2.5 kcal
  per gram of fibre and would propose it every time. `topUps` lists what
  belongs in food; cost only ranks what is already acceptable.
- **Every candidate has a `maxG`.** Without it the ranking proposed 478 g of
  spinach per serving — the exact failure `inbox/WHAT-TO-LOOK-FOR.md` warns
  about. When nothing fits under its cap, the script proposes a **pair**,
  bulk plus density, which is the shape the brief asks for anyway.

Proposals are printed, never applied. Adding an ingredient changes the dish,
and that is a cooking decision. A recipe may declare `cuisine` to filter the
shortlist; without one nothing is filtered and chickpeas may turn up in a Thai
curry.

**No macro is ever typed for a dish.** This is the same rule the Asian Base Block
learned the hard way, and it is the reason a recipe cannot be added by pasting a
nutrition panel — the ingredients go in, the numbers come out.

```
inbox/*.md --[read_inbox.py]--> data/recipes.json --[adapt_recipe.py]--> grams + a fit report
                                      + data/foods.json
```

**`inbox/` is where recipes land before they are data**, and it is gitignored for
the same reason `sources/` is: a saved recipe page is someone else's copyrighted
text and this repo is public. The link and the amounts are what we keep. Only
`inbox/TEMPLATE.md` is committed.

`read_inbox.py` reads the whole folder at once and answers the two questions
only this repo can answer — is every ingredient known, and is every amount a
weight. Spoon measures are converted and **flagged as approximate**; unknown
ingredients and vague amounts block that file. A blocked recipe is never
written: a half-resolved recipe in the library is worse than none, because its
macros would be quietly wrong rather than obviously missing.

`check_targets.py` is the other half: it asks whether a target can be hit at all
before anyone cooks against it. Today it says no — see Known gaps.

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

- **The mirror-meal target cannot be cooked.** 425 kcal / 40 g protein / 17 g
  fibre / 12 g fat, minus the 1.5 mandated Base blocks, leaves 246 kcal to carry
  33.5 g protein, 14.6 g fibre and 10.3 g fat — macros whose own energy content
  is 257 kcal, before any digestible carbohydrate. It is unreachable by ~11 kcal
  at the theoretical floor and by far more in real food. The kitchen page now
  shows this check live (`energyFactors` in `kitchen.json`). Until fibre per meal
  drops or the meal grows, **no recipe can satisfy the spec** — which is why a
  recipe recommender would be building on sand.
- **`cookedWeightG` is estimated, not weighed.** Weigh a batch, type it into the
  splitter, re-run `recompute_macros.py`. The custom food in MacroFactor may
  still hold the old 105 kcal/100 g — it should be 140.
- **Kitchen has one recipe, not a library.** The Base Block, the splitter, the
  day ledger and the adapter all work; the library holds a single real dish
  (Philipp's breakfast). Dishes come from them, never invented here.
- **The daily targets are over-specified too.** Philipp's four targets imply
  1662 kcal against a 1600 budget, Eunice's 1598 against 1580. `check_targets.py`
  reports both. Philipp's 62 kcal gap is the one worth resolving.
- **Philipp's breakfast is written down twice** — typed in `profiles.json`
  (410 kcal) and derived from `recipes.json` (380). The typed figures drive the
  day ledger. Generic tables versus an unknown original; the packets would settle
  it. `check_targets.py` prints the disagreement rather than picking a winner.
- ~~No MacroFactor import.~~ Built. `scripts/import_macrofactor.py` reads an
  .xlsx with the standard library alone and discovers the schema: sheet names
  from the workbook, headers from row 1, and date columns from the number
  formats in `styles.xml` rather than from what a header is called. Output goes
  to `private/`.
- **The repo is public, not only the site.** Stripping a field out of the built
  pages hides nothing if the JSON it came from is committed. Body composition
  now lives in `private/body.json`; `data/profiles.json` and `data/training.json`
  carry none, and `check_targets.py` reads the private file directly.
  **The history still does.** Bodyweight was in `data/training.json` from the
  first commit and body fat from `44468a7`, both pushed. Removing it from `main`
  does not remove it from the 27 commits behind `main`, and on GitHub a rewrite
  does not fully help: unreachable commits stay reachable by SHA until GitHub
  garbage-collects, which needs a support request. The complete fix is a fresh
  repository; the partial one is a rewrite plus that request. Undecided.
- **Locating detail is back in `routines.json`.** `9bf4883` generalised it once,
  but the skincare protocol names the city and one district, because the water
  hardness rules are genuinely about that water. It is committed and served.
  Generalising it costs real meaning, so it is a judgement call, not a cleanup.
- **Sessions still duplicate exercise objects** instead of referencing
  `exercises.json` by id.
- **Demo videos are verified live, not verified good** — nobody has watched them.
  `verify_videos.py` confirms each link resolves and that the title and channel
  still match what was recorded; it cannot confirm the video shows good form.

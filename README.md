# Pairwell

A small offline-first PWA for two people: skincare, hair, workouts and kitchen.
Built to be opened on a phone and understood in one glance — no accounts, no
tracking, no server.

**Live:** https://glowgiver.github.io/pairwell/

## How it works

Two layers, deliberately:

```
data/*.json  --[scripts/build_*.py]-->  hub/**/index.html
```

`data/` holds the truth — routines, training plans, recipes, targets. No HTML,
no styling. `hub/` holds finished, self-contained pages that work offline once
the service worker has cached them. The build scripts are the only bridge, and
they run by hand — there is no watcher.

After changing anything in `data/`, rebuild:

```bash
python3 scripts/build_workout_page.py
python3 scripts/build_routines_page.py
```

Then bump `const CACHE` in `hub/sw.js` so both phones pick up the new version.

## Scripts

| Script | Does |
|---|---|
| `build_workout_page.py` | training.json + exercises.json → the workout page |
| `build_routines_page.py` | routines.json → the skincare and hair pages |
| `recompute_macros.py` | derives every macro in kitchen.json from ingredients + one measured cooked weight |
| `check_routine_rules.py` | checks the seasonal skincare plan against its own safety rules |
| `verify_videos.py` | re-checks all 43 exercise demo links for rot |

`scripts/_archive/` holds a one-time migration that must not be run again; it
refuses to execute.

## Privacy

No external requests, no analytics, no CDN. Demo videos are plain links rather
than embeds, so YouTube is only contacted if someone taps one.

The site itself is public, so nothing identifying belongs in `data/`. Personal
routines and targets live here; addresses, workplaces and anything that could
locate a person do not.

## State

Skincare, hair and workout are built. Kitchen is not — it needs a recipe model
first. See `CLAUDE.md` for the architecture rules.

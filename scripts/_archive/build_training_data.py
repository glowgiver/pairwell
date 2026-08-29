# =============================================================================
# ARCHIVED 2026-08-29 — DO NOT RUN.
#
# This was a ONE-TIME migration: it transcribed the original
# Workout_Hub_Philipp_and_Eunice.html into data/training.json.
# That job is done.
#
# Running it now would OVERWRITE data/training.json with these frozen
# literals and silently destroy every edit made since the migration.
#
# data/training.json is the canonical source of training data.
# Edit that file directly, then run scripts/build_workout_page.py.
#
# Kept only as a record of where the data originally came from.
# =============================================================================

import json

def ex(name, ref, focus, tier, sets, reps, extras=None, cue=""):
    return {"name": name, "ref": ref, "focus": focus, "tier": tier, "sets": sets, "reps": reps,
            "extras": dict(extras or []), "cue": cue}

def duo(name, focus, tier, sets, reps, p_load, e_load, cue="", extras=None):
    return {"name": name, "focus": focus, "tier": tier, "sets": sets, "reps": reps,
            "extras": dict(extras or []), "philippLoad": p_load, "euniceLoad": e_load, "cue": cue, "shared": True}

FOCUS_LABEL = {"a": "upper body", "g": "legs/glutes", "p": "inner thigh", "c": "core"}

data = {
  "_source": "Workout_Hub_Philipp_and_Eunice.html (uploaded 2026-08-28)",
  "_supersedes": "earlier training.json draft — this is the authoritative extraction",

  "meta": {
    "title": "Workout Hub · Philipp & Eunice · 2026",
    "edition": "Lean Athletic Edition",
    "structure": "Full-Body, Primary/Maintenance tiers, taper-focused",
    "locations": ["gym", "home", "travel"],
  },

  "profiles": {
    "philipp": {
      "badge": "Lean Athletic",
      "goal": "K-Idol Taper · Fettabbau · Muskelerhalt",
      "meta": {"weight": "81.2 → 77 kg", "bodyFat": "20.6 → 16%", "intensity": "RIR 2"}
    },
    "eunice": {
      "badge": "Toned & Curvy",
      "goal": "Hwasa-Look · Glutes · Schulter-Hüft-Relation",
      "meta": {"bodyFat": "29 → 22%", "focus": "Glutes + Rücken", "intensity": "RIR 2-3"}
    },
    "shared": {
      "badge": "Zusammen",
      "goal": "same exercises, own load — alternating sets",
      "meta": {"when": "Sunday", "mode": "alternating sets", "setup": "1 station"}
    }
  },

  "weeklyRhythm": {
    "philipp": [
      {"day": "Mo", "what": "Pad · Zone 1", "type": "move"},
      {"day": "Di", "what": "Gym · Push", "type": "training"},
      {"day": "Mi", "what": "Pad · Zone 2", "type": "move"},
      {"day": "Do", "what": "Gehen", "type": "move"},
      {"day": "Fr", "what": "Gym · Pull", "type": "training"},
      {"day": "Sa", "what": "Spaziergang", "type": "move"},
      {"day": "So", "what": "Shared", "type": "training"}
    ],
    "eunice": [
      {"day": "Mo", "what": "Gym solo", "type": "training"},
      {"day": "Di", "what": "frei", "type": "rest"},
      {"day": "Mi", "what": "Gehen", "type": "move"},
      {"day": "Do", "what": "frei", "type": "rest"},
      {"day": "Fr", "what": "Gym · mit Philipp", "type": "training"},
      {"day": "Sa", "what": "frei", "type": "rest"},
      {"day": "So", "what": "Shared", "type": "training"}
    ]
  },

  "locationNotes": {
    "gym": "Holmes Place · cable tower + machines. All primary exercises run on the cable tower — constant tension, exact progression.",
    "home": "Bodylastics tubes + door anchor. Bands mimic the cable tower 1:1. More resistance = bundle another tube. Height = anchor high/mid/low. Constant tension = stand farther from the door.",
    "travel": "Tubes only + door anchor. Everything with Bodylastics + door anchor, no dumbbells needed. Tempo 3-0-1 and standing farther from anchor substitute for more weight."
  },

  "equipmentByLocation": {
    "gym": ["cable tower", "machines", "glute drive", "leg press"],
    "home": ["Bodylastics tubes", "door anchor high/low", "ankle strap"],
    "travel": ["3+ tubes", "door anchor", "tempo 3-0-1"]
  },

  "sessions": {

    "gym": {
      "philipp": {
        "push": {
          "title": "Push + Taper", "day": "Dienstag", "focus": "side delt · chest · lat · triceps",
          "exercises": [
            ex("Cable Lateral Raise", "taper driver #1", "a", "primary", 3, "12-15",
               [("load","5 kg/arm"),("rir","RIR 2"),("rest","60s")],
               "Fresh first — most important move for the look. Constant tension at the bottom. Lead with the elbow to shoulder height. Goal: clean 15 → then 6 kg."),
            ex("Cable Chest Press (high-to-low)", "upper chest", "a", "primary", 4, "10-12",
               [("load","20 kg"),("rir","RIR 2"),("rest","90s")],
               "Anchor high, stand away from tower, press forward-downward across the chest. 4 sets — chest is second focus."),
            ex("Wide Lat Pulldown", "lat width → taper", "a", "primary", 3, "12-15",
               [("load","45 kg"),("rir","RIR 2"),("rest","90s")],
               "Second most important taper muscle after side delt — trained in both sessions."),
            ex("Triceps Pushdown (Rope)", "arm definition", "a", "primary", 3, "12-15",
               [("load","17.5 kg"),("rir","RIR 1-2"),("rest","60s")],
               "Elbows fixed at sides, separate the rope at the bottom, brief hold."),
            ex("Leg Press (light)", "leg proportion", "g", "maint", 2, "20",
               [("load","~70 kg"),("rir","RIR 3"),("rest","60s")],
               "Maintenance only — hold, don't build. High reps, light weight, never progress."),
            ex("Cable Crunch", "waist", "c", "maint", 3, "12-15",
               [("load","25 kg"),("rir","RIR 2"),("rest","45s")],
               "Fold ribs to hips, hands fixed at ears."),
            ex("Hollow Hold", "waist detail", "c", "maint", 3, "30s", [("rest","45s")],
               "Lower back flat, arms long.")
          ]
        },
        "pull": {
          "title": "Pull + Haltung", "day": "Freitag", "focus": "side delt · lat · back · rear delt",
          "exercises": [
            ex("Cable Lateral Raise", "taper driver #1", "a", "primary", 3, "12-15",
               [("load","5 kg/arm"),("rir","RIR 2"),("rest","60s")], "2nd side-delt hit of the week."),
            ex("Wide Lat Pulldown", "lat width", "a", "primary", 3, "12-15",
               [("load","45 kg"),("rir","RIR 2"),("rest","90s")],
               "Replaces removed pull-up — that thickened upper trap and shortened neckline."),
            ex("Cable Row (neutral)", "upper back", "a", "primary", 3, "10-12",
               [("load","35 kg"),("rir","RIR 2"),("rest","90s")],
               "Sit upright, pull to belly, elbows close, moderate — don't overload."),
            ex("Rear Delt Fly (Cable)", "rear delt", "a", "primary", 3, "15",
               [("load","9 kg"),("rir","RIR 1"),("rest","60s")], "Arms nearly straight, lead with pinkies."),
            ex("Cable Face Pull", "shoulder health", "a", "maint", 2, "15",
               [("load","10 kg"),("rir","RIR 1"),("rest","45s")],
               "Maintenance — antagonist to all pressing."),
            ex("Seated Hamstring Curl", "hamstrings", "g", "maint", 2, "15",
               [("load","50 kg"),("rir","RIR 3"),("rest","60s")], "Maintenance, controlled, no momentum."),
            ex("Cable Biceps Curl", "arm detail", "a", "maint", 2, "15",
               [("load","15 kg"),("rir","RIR 2"),("rest","45s")], "Maintenance.")
          ]
        }
      },
      "eunice": {
        "solo": {
          "title": "Lower + Push", "day": "Montag · solo", "focus": "fixed machines only — no setup, no cable",
          "note": "Monday alone in the gym. Deliberately machines only: fixed path, nothing can go wrong, no spotting needed. Cable exercises happen Friday with Philipp.",
          "exercises": [
            ex("Glute Drive Machine", "priority #1", "g", "primary", 4, "12-15",
               [("rir","RIR 2-3"),("rest","90s")],
               "Fresh first — top exercise. Full hip extension, 1s hold at top, squeeze. 4 sets — glutes are the goal."),
            ex("Leg Press (wide + high)", "quads + glutes + inner thigh", "g", "primary", 3, "12-15",
               [("rir","RIR 2-3"),("rest","90s")], "Feet wide and high, knees out."),
            ex("Adductor Machine", "inner thigh", "g", "primary", 3, "15-20",
               [("rir","RIR 1-2"),("rest","60s")], "Slow squeeze (3s in), controlled release."),
            ex("Seated Leg Curl", "hamstrings", "g", "primary", 3, "12-15",
               [("rir","RIR 2-3"),("rest","75s")], "Antagonist to leg press."),
            ex("Chest Press Machine", "chest", "a", "maint", 2, "10-12",
               [("rir","RIR 2-3"),("rest","75s")], "Maintenance — fixed path, nothing to set up."),
            ex("Triceps Machine", "arm detail", "a", "maint", 2, "12-15",
               [("rir","RIR 1-2"),("rest","60s")], "Maintenance, machine instead of cable rope for solo simplicity."),
            ex("Ab Machine", "core", "c", "maint", 2, "12-15",
               [("rir","RIR 2-3"),("rest","45s")], "Maintenance, weighted fixed path.")
          ]
        },
        "pull": {
          "title": "Upper + Glutes", "day": "Freitag · mit Philipp", "focus": "cable tower — alternating sets with Philipp",
          "note": "Friday with Philipp at the cable tower. She's out at 13:00, he arrives ~15:30. Same station: her set, his set. Her rest is his work time.",
          "exercises": [
            ex("Cable Lateral Raise", "shoulder-hip relation", "a", "primary", 3, "12-15",
               [("load","2.5 kg/arm"),("rir","RIR 2-3"),("rest","60s")],
               "New for her. Emphasized shoulder makes the waist look narrower — the Hwasa effect."),
            ex("Wide Lat Pulldown", "back width", "a", "primary", 3, "12-15",
               [("load","25 kg"),("rir","RIR 2-3"),("rest","90s")], "Back width makes the waist look smaller."),
            ex("Cable Row (neutral)", "upper back", "a", "primary", 3, "10-12",
               [("load","20 kg"),("rir","RIR 2-3"),("rest","75s")], "Posture + defined back look."),
            ex("Glute Drive Machine", "glutes 2x/week", "g", "primary", 3, "12-15",
               [("rir","RIR 2-3"),("rest","75s")],
               "Glutes again — 2x/week drives growth. 3 sets here so Monday's 4-set block isn't overloaded. (Philipp does 2 maintenance sets here.)"),
            ex("Rear Delt + Face Pull", "rear delt", "a", "primary", 3, "15",
               [("load","shared station"),("rir","RIR 1-2"),("rest","60s")],
               "New — was completely missing. Rear delt fly into face pull."),
            ex("Cable Biceps Curl", "arm detail", "a", "maint", 2, "15",
               [("load","7.5 kg"),("rir","RIR 2-3"),("rest","45s")], "Maintenance."),
            ex("Cable Crunch", "core", "c", "maint", 3, "12-15",
               [("rir","RIR 2-3"),("rest","45s")], "Maintenance, kneeling.")
          ]
        }
      }
    },

    "home": {
      "philipp": {
        "push": {
          "title": "Push + Taper", "day": "Home · Push", "focus": "Bodylastics — cable feel at home",
          "exercises": [
            ex("Band Lateral Raise (cross-body)", "gym: Cable Lat Raise", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2"),("rest","60s")],
               "Stand on the band with the opposite foot so it crosses the body — keeps tension at the bottom like the cable."),
            ex("Band Chest Press", "gym: Cable Chest Press", "a", "primary", 4, "10-12",
               [("load","Rot (L3) + Grün (L2)"),("rir","RIR 2"),("rest","90s")],
               "Low anchor behind, stand away from door, press forward-upward."),
            ex("Band Lat Pulldown (kneeling)", "gym: Lat Pulldown", "a", "primary", 3, "12-15",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")],
               "Anchor at top of door, kneeling, wide grip, elbows down-out to ribs."),
            ex("Band Triceps Pushdown", "gym: Triceps Pushdown", "a", "primary", 3, "12-15",
               [("load","Rot (L3)"),("rir","RIR 1-2"),("rest","60s")], "High anchor, elbows fixed at sides."),
            ex("Band Squat (light)", "gym: Leg Press", "g", "maint", 2, "20",
               [("load","Blau (L4)"),("rir","RIR 3"),("rest","60s")], "Maintenance — hold only."),
            ex("Band Kneeling Crunch", "gym: Cable Crunch", "c", "maint", 3, "12-15",
               [("load","Blau (L4)"),("rir","RIR 2"),("rest","45s")], "Anchor high, kneeling."),
            ex("Hollow Hold", "gym: Hollow Hold", "c", "maint", 3, "30s", [("rest","45s")],
               "Lower back flat, build to 40s.")
          ]
        },
        "pull": {
          "title": "Pull + Haltung", "day": "Home · Pull", "focus": "Bodylastics — pulling + posture",
          "exercises": [
            ex("Band Lateral Raise (cross-body)", "gym: Cable Lat Raise", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2"),("rest","60s")], "2nd side-delt hit."),
            ex("Band Lat Pulldown (kneeling)", "gym: Lat Pulldown", "a", "primary", 3, "12-15",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")],
               "Anchor top, kneeling — replaces pull-up, no bar needed."),
            ex("Band Seated Row (low anchor)", "gym: Cable Row", "a", "primary", 3, "10-12",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")],
               "Low anchor or looped around both feet, sit upright, pull to belly."),
            ex("Band Rear Delt Pull-Apart", "gym: Rear Delt Fly", "a", "primary", 3, "15",
               [("load","Grün (L2)"),("rir","RIR 1"),("rest","60s")],
               "No anchor: band in both hands, arms straight, pull apart to chest."),
            ex("Band Face Pull (mid anchor)", "gym: Face Pull", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 1"),("rest","45s")], "Maintenance — anchor at head height."),
            ex("Band RDL (bilateral)", "gym: Hamstring Curl", "g", "maint", 2, "15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 3"),("rest","60s")],
               "Maintenance. Carabiners folded into one handle, stand on loop."),
            ex("Band Biceps Curl", "gym: Cable Curl", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 2"),("rest","45s")], "Maintenance.")
          ]
        }
      },
      "eunice": {
        "solo": {
          "title": "Lower + Push", "day": "Home · Lower", "focus": "Bodylastics — glute focus",
          "exercises": [
            ex("Band Hip Thrust", "gym: Glute Drive", "g", "primary", 4, "15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 2-3"),("rest","75s")],
               "First — glutes are priority. Tube over feet, shoulders on couch, handles over hips."),
            ex("Band Squat (wide + high)", "gym: Leg Press", "g", "primary", 3, "12-15",
               [("load","Blau (L4)"),("rir","RIR 2-3"),("rest","75s")],
               "Stand on tube, feet wider, handles at shoulders, 3s down."),
            ex("Band Adductor Squeeze (lying)", "gym: Adductor", "g", "primary", 3, "15-20",
               [("load","light band"),("rir","RIR 1-2"),("rest","45s")],
               "Band around ankles, on back, legs apart, 3s squeeze together."),
            ex("Band RDL (bilateral)", "gym: Leg Curl", "g", "primary", 3, "12-15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 2-3"),("rest","75s")], "Hamstrings."),
            ex("Push-Up (knee or standard)", "gym: Chest Press", "a", "maint", 2, "10-15",
               [("rir","RIR 2-3"),("rest","60s")], "Maintenance. Knee version to regress, 3s down."),
            ex("Band Triceps Pushdown", "gym: Triceps Machine", "a", "maint", 2, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2-3"),("rest","60s")], "Maintenance."),
            ex("Dead Bug", "gym: Ab Machine", "c", "maint", 2, "10/side", [("rest","45s")],
               "Maintenance, lower back flat.")
          ]
        },
        "pull": {
          "title": "Upper + Glutes", "day": "Home · Upper", "focus": "Bodylastics — back + glutes",
          "exercises": [
            ex("Band Lateral Raise (cross-body)", "gym: Cable Lat Raise", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2-3"),("rest","60s")], "Emphasized shoulder for Hwasa silhouette."),
            ex("Band Lat Pulldown (kneeling)", "gym: Lat Pulldown", "a", "primary", 3, "12-15",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","90s")], "Anchor top, shoulder blades down."),
            ex("Band Seated Row", "gym: Cable Row", "a", "primary", 3, "10-12",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","75s")], "Around both feet or low anchor, upright."),
            ex("Band Hip Thrust", "gym: Glute Drive", "g", "primary", 3, "15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 2-3"),("rest","60s")], "Glutes 2x/week."),
            ex("Band Rear Delt Pull-Apart", "gym: Rear Delt + Face Pull", "a", "primary", 3, "15-20",
               [("load","Grün (L2)"),("rir","RIR 1-2"),("rest","45s")], "Band in both hands, pull apart to chest."),
            ex("Band Biceps Curl", "gym: Cable Curl", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","45s")], "Maintenance."),
            ex("Dead Bug", "gym: Cable Crunch", "c", "maint", 3, "10/side", [("rest","45s")], "Maintenance.")
          ]
        }
      },
      "shared": {
        "sun": {
          "title": "Shared Session", "day": "Sonntag · gemeinsam", "focus": "same exercises · own tubes · alternating",
          "note": "Sunday together at home. Both do the same exercises simultaneously — Philipp the stronger tubes, Eunice the lighter. If at the gym instead: same plan, cable tower instead of bands.",
          "exercises": [
            duo("Band Lateral Raise (cross-body)", "a", "primary", 3, "12-15", "Gelb (L1)", "Gelb (L1), less tension",
                "Opposite foot on band, lead with elbow to shoulder height.", [("rir","RIR 2"),("rest","60s")]),
            duo("Band Lat Pulldown (kneeling)", "a", "primary", 3, "12-15", "Blau (L4) + Schwarz (L5)", "Grün (L2)",
                "Anchor top, elbows down-out, squeeze lats.", [("rest","90s")]),
            duo("Band Seated Row", "a", "primary", 3, "10-12", "Blau (L4) + Schwarz (L5)", "Grün (L2)",
                "Around both feet, upright, pull to belly, no momentum.", [("rest","75s")]),
            duo("Band Hip Thrust", "g", "primary", 3, "15", "Blau (L4) gefaltet · maintenance", "Blau (L4) gefaltet · primary",
                "Tube over hips, shoulders supported, 2s squeeze at top.", [("rir","RIR 2-3"),("rest","60s")]),
            duo("Band Rear Delt Pull-Apart", "a", "primary", 3, "15", "Grün (L2)", "Grün (L2)",
                "Band in both hands, pull apart to chest.", [("rir","RIR 1-2"),("rest","45s")]),
            duo("Band Biceps Curl", "a", "maint", 2, "15", "Rot (L3)", "Grün (L2)",
                "Stand on band, elbows fixed, slow down.", [("rest","45s")]),
            duo("Hollow Hold / Dead Bug", "c", "maint", 3, "30s", "Hollow Hold + Flutter", "Dead Bug 10/side",
                "Core finisher — each own variant, lower back flat.", [("rest","45s")])
          ]
        }
      }
    },

    "travel": {
      "philipp": {
        "push": {
          "title": "Push + Taper", "day": "Travel · Push", "focus": "tubes + door anchor only",
          "exercises": [
            ex("Cross-Body Band Lateral Raise", "taper #1", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2"),("rest","60s")],
               "Opposite foot on tube for tension at bottom. Too heavy? Foot closer to center."),
            ex("Band Chest Press (high-to-low)", "upper chest", "a", "primary", 4, "10-12",
               [("load","Schwarz (L5)"),("rir","RIR 2"),("rest","90s")], "Anchor high, press forward-downward."),
            ex("Band Lat Pulldown (kneeling)", "lat width", "a", "primary", 3, "12-15",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")], "Only vertical pull."),
            ex("Band Overhead Triceps Extension", "arm detail", "a", "primary", 3, "10-12",
               [("load","Rot (L3)"),("rir","RIR 1-2"),("rest","60s")], "Low anchor, handles behind head, elbows high."),
            ex("Band Squat (light)", "leg proportion", "g", "maint", 2, "20",
               [("load","Blau (L4)"),("rir","RIR 3"),("rest","60s")], "Maintenance."),
            ex("Kneeling Band Crunch", "waist", "c", "maint", 3, "12-15",
               [("load","Blau (L4)"),("rir","RIR 2"),("rest","45s")], "Anchor high, kneeling."),
            ex("Hollow Body Hold", "waist detail", "c", "maint", 3, "30s", [("rest","45s")],
               "Lower back flat, extend legs to progress.")
          ]
        },
        "pull": {
          "title": "Pull + Haltung", "day": "Travel · Pull", "focus": "tubes + door anchor only",
          "exercises": [
            ex("Cross-Body Band Lateral Raise", "taper #1", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2"),("rest","60s")], "2nd side-delt hit."),
            ex("Band Lat Pulldown (kneeling)", "lat width", "a", "primary", 3, "12-15",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")], "Replaces pull-up."),
            ex("Seated Band Row", "upper back", "a", "primary", 3, "10-12",
               [("load","Blau (L4) + Schwarz (L5)"),("rir","RIR 2"),("rest","90s")],
               "Sit on floor, tube around both feet, upright, no momentum."),
            ex("Band Rear Delt Pull-Apart", "rear delt", "a", "primary", 3, "15",
               [("load","Grün (L2)"),("rir","RIR 1"),("rest","60s")], "No anchor, arms straight, pull apart."),
            ex("Band Face Pull", "shoulder health", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 1"),("rest","45s")], "Maintenance, anchor at head height."),
            ex("Band Single-Leg RDL", "hamstrings", "g", "maint", 2, "12/side",
               [("load","Blau (L4)"),("rir","RIR 3"),("rest","60s")], "Maintenance."),
            ex("Band Biceps Curl", "arm detail", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 2"),("rest","45s")], "Maintenance.")
          ]
        }
      },
      "eunice": {
        "solo": {
          "title": "Lower + Push", "day": "Travel · Lower", "focus": "tubes + door anchor only",
          "exercises": [
            ex("Band Hip Thrust", "glutes #1", "g", "primary", 4, "15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 2-3"),("rest","75s")], "First. Tube over feet, shoulders supported."),
            ex("Band Squat (wide)", "quads + inner thigh", "g", "primary", 3, "12-15",
               [("load","Blau (L4)"),("rir","RIR 2-3"),("rest","75s")], "Stand on tube, feet wide, 3s down."),
            ex("Lateral Lunge (tempo)", "inner thigh", "g", "primary", 3, "10/side",
               [("rir","RIR 2-3"),("rest","45s")], "Wide step to side, sit into hip, other leg straight."),
            ex("Band Single-Leg RDL", "hamstrings", "g", "primary", 3, "12/side",
               [("load","Blau (L4)"),("rir","RIR 2-3"),("rest","60s")], "One foot on tube, soft knee, 3s down."),
            ex("Push-Up (knee or standard)", "chest", "a", "maint", 2, "10-15",
               [("rir","RIR 2-3"),("rest","60s")], "Maintenance."),
            ex("Band Overhead Triceps Extension", "arm detail", "a", "maint", 2, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2-3"),("rest","60s")], "Maintenance."),
            ex("Dead Bug", "core", "c", "maint", 2, "10/side", [("rest","45s")], "Maintenance.")
          ]
        },
        "pull": {
          "title": "Upper + Glutes", "day": "Travel · Upper", "focus": "tubes + door anchor only",
          "exercises": [
            ex("Cross-Body Band Lateral Raise", "shoulder", "a", "primary", 3, "12-15",
               [("load","Gelb (L1)"),("rir","RIR 2-3"),("rest","60s")], "Emphasized shoulder for silhouette."),
            ex("Band Lat Pulldown (kneeling)", "back width", "a", "primary", 3, "12-15",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","90s")], "Anchor top."),
            ex("Seated Band Row", "upper back", "a", "primary", 3, "10-12",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","75s")], "Tube around both feet."),
            ex("Band Hip Thrust", "glutes 2x", "g", "primary", 3, "15",
               [("load","Blau (L4) gefaltet"),("rir","RIR 2-3"),("rest","60s")], "Tube over hips."),
            ex("Band Rear Delt Pull-Apart", "rear delt", "a", "primary", 3, "15-20",
               [("load","Grün (L2)"),("rir","RIR 1-2"),("rest","45s")], "Tube in both hands, pull apart."),
            ex("Band Biceps Curl", "arm detail", "a", "maint", 2, "15",
               [("load","Grün (L2)"),("rir","RIR 2-3"),("rest","45s")], "Maintenance."),
            ex("Dead Bug", "core", "c", "maint", 3, "10/side", [("rest","45s")], "Maintenance.")
          ]
        }
      },
      "shared": {
        "sun": {
          "title": "Shared Session", "day": "Travel · gemeinsam", "focus": "same exercises · own tubes",
          "note": "Together while traveling. Both do the same exercises, Philipp the stronger tubes. Each grabs their own — no conflict.",
          "exercises": [
            duo("Cross-Body Band Lateral Raise", "a", "primary", 3, "12-15", "Gelb (L1)", "Gelb (L1)",
                "Opposite foot on tube, lead with elbow.", [("rir","RIR 2"),("rest","60s")]),
            duo("Band Lat Pulldown (kneeling)", "a", "primary", 3, "12-15", "Blau (L4) + Schwarz (L5)", "Grün (L2)",
                "Anchor top, elbows down-out.", [("rest","90s")]),
            duo("Seated Band Row", "a", "primary", 3, "10-12", "Blau (L4) + Schwarz (L5)", "Grün (L2)",
                "Tube around both feet, upright.", [("rest","75s")]),
            duo("Band Hip Thrust", "g", "primary", 3, "15", "Blau (L4) · maintenance", "Blau (L4) · primary",
                "Tube over hips, 2s squeeze.", [("rir","RIR 2-3"),("rest","60s")]),
            duo("Band Rear Delt Pull-Apart", "a", "primary", 3, "15", "Grün (L2)", "Grün (L2)",
                "Tube in front, pull apart to chest.", [("rir","RIR 1-2"),("rest","45s")]),
            duo("Band Biceps Curl", "a", "maint", 2, "15", "Rot (L3)", "Grün (L2)",
                "Stand on tube, elbows fixed.", [("rest","45s")]),
            duo("Hollow Hold / Dead Bug", "c", "maint", 3, "30s", "Hollow + Flutter", "Dead Bug",
                "Core finisher, lower back flat.", [("rest","45s")])
          ]
        }
      }
    }
  },

  "cardioProtocol": {
    "context": "Philipp's weight dropped most in July while traveling (~8,000+ steps/day). Back in Hamburg: 3,000-4,000 steps, plateaued. Structural gap, not a training problem.",
    "zone2": {
      "heartRateRange": "106-124 bpm (age 43)",
      "padSettings": "5-5.5 km/h at 6% incline",
      "note": "at 4 km/h lands around ~100 bpm — Zone 1, too low",
      "appleWatchSetup": "Workout → Indoor Walk → ... → Heart Rate → Range 106-124 bpm, vibrates on drift",
      "duration": "20-30 min",
      "schedule": "Tue/Thu/Sat",
      "eveningRule": "after 20:00 Zone 1 only (under 100 bpm) — Zone 2 late disrupts sleep",
      "adhdBonus": "even 100 bpm rhythmic walking regulates dopamine/noradrenaline — never wasted"
    },
    "stepTarget": {
      "current": "3000-4000/day",
      "goal": 7000,
      "parkingHack": "park on the residential street before the destination rather than the lot — about a 5 min walk each way, same spot every time, no detour. ~1800 steps round trip, ~9000/week",
      "badWeather": "park in the lot — no penalty rule",
      "evening": "pad during show/podcast, Zone 1, effortless NEAT",
      "why": "+3000 steps/day ≈ 200-250 kcal without compensation — bigger lever than the weight gap alone"
    }
  },

  "progression": {
    "philipp": {
      "method": "double progression",
      "primaryRule": "start low in rep range (e.g. 12), climb over weeks to 15 across all sets, then raise load and drop back to 12. Side delt target: clean 15 → 6kg. Pulldown/row/chest: +2.5kg when all sets hit top of range. RIR 2 non-negotiable in a deficit.",
      "maintenanceRule": "2 sets, same weight as last time, RIR 3, never progress — one number, no decision",
      "missedSessionRule": "never two in a row. One missed session is life, two is a pattern. Sunday shared session is the safety net — minimum 1x/week structurally guaranteed.",
      "deload": "every 6-8 weeks, 1 light week at ~60%. In a deficit, err earlier — cortisol is the enemy of muscle retention."
    },
    "eunice": {
      "method": "double progression, tuned for growth",
      "primaryRule": "form before load; on glutes she can push closer to failure (RIR 1-2)",
      "mindMuscle": "squeeze and hold at the top of every rep — feeling the muscle matters more than the number",
      "formFirst": "a clean rep beats a heavy one you don't feel in the target muscle",
      "deload": "every 8 weeks, 1 light week — needed less often than Philipp since she's building, not cutting"
    }
  },

  "_gaps": [
    "Eunice's exact current per-exercise loads for many maintenance movements are marked as ranges/placeholders in the source HTML, not all individually confirmed via MacroFactor yet",
    "Demo video links are auto-generated YouTube search queries, not curated links"
  ]
}

import sys

sys.exit(
    "REFUSED: this is an archived one-time migration.\n"
    "Running it would overwrite data/training.json with frozen 2026-08-28 literals\n"
    "and destroy any edits made since. data/training.json is canonical — edit it\n"
    "directly, then run scripts/build_workout_page.py.\n"
    "If you genuinely need the original extraction, read this file; don't execute it."
)

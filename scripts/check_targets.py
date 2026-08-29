"""Are the targets themselves arithmetically possible?

Two questions, both answerable without any recipe existing:

  1. Do a person's four daily targets agree with their calorie target?
     Protein, fat and carbohydrate have fixed energy contents. If the four
     numbers imply more calories than the calorie target allows, no diet
     satisfies all four — the targets contradict each other, not the food.

  2. Is one mirror meal reachable? Same idea, one level down, with the
     Asian Base blocks already on the plate.

Read-only. Prints a report and exits non-zero if anything is impossible.
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def lo(v):
    """mirrorMeals.fatG is the range "12-15". Take the charitable end."""
    return float(str(v).split("-")[0])


def bodies():
    """Body composition, from private/body.json.

    Not in data/, and not optional-by-accident: this repo is public, so the
    one file describing bodies rather than plans is gitignored. Absent, the
    energy-balance section says so and checks nothing.
    """
    path = os.path.join(BASE, "..", "private", "body.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("people", {})


def measured_expenditure(key):
    """MacroFactor's adaptive TDEE, if it has been imported.

    Measured beats modelled. Katch-McArdle knows a body's size; it cannot know
    what six months of dieting has done to what that body actually spends.
    """
    path = os.path.join(BASE, "..", "private", "macrofactor", key, "expenditure.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    cols = d.get("columns") or []
    if len(cols) < 2:
        return None
    date_c, val_c = cols[0], cols[1]
    series = [(r[date_c], r[val_c]) for r in d.get("rows", [])
              if isinstance(r.get(val_c), (int, float))]
    if not series:
        return None
    series.sort()
    vals = [v for _, v in series]
    recent = vals[-14:]
    return {"latest": vals[-1], "recent": sum(recent) / len(recent),
            "first": vals[0], "n": len(vals),
            "from": series[0][0], "to": series[-1][0],
            "trend14": vals[-1] - vals[-15] if len(vals) > 15 else None}


def energy_balance(profiles, training):
    """Is the calorie target the right distance below maintenance?

    Katch-McArdle, because lean mass is the one input the recorded body-fat
    figure gives us directly. The activity factor is the soft part, so this
    prints a band rather than a number, and the band is wide on purpose.

    None of it outranks the scale. If the weight trend disagrees with this
    arithmetic, the weight trend is right and the arithmetic is wrong.
    """
    print("\nENERGY BALANCE — how far below maintenance is the calorie target?\n")
    rhythm = (training or {}).get("weeklyRhythm", {})
    bodyData = bodies()
    findings = []

    for key, p in profiles["people"].items():
        body = bodyData.get(key) or {}
        w, bf = body.get("weightKg"), body.get("bodyFatPct")
        if not w or bf is None:
            print("  %s — no body composition in private/body.json, "
                  "nothing can be checked." % p["displayName"])
            findings.append("%s has no body composition in private/body.json, "
                            "so none of their targets can be sanity-checked."
                            % p["displayName"])
            continue

        lbm = w * (1 - bf / 100.0)
        bmr = 370 + 21.6 * lbm
        days = rhythm.get(key, [])
        n_train = sum(1 for x in days if x.get("type") == "training")
        n_move = sum(1 for x in days if x.get("type") == "move")
        # a sedentary base, plus what the week actually contains
        factor = 1.2 + 0.05 * n_train + 0.025 * n_move
        target = p["dailyTargets"]["calories"]

        print("  %s — %.1f kg at %.1f%% body fat, %.1f kg lean" % (p["displayName"], w, bf, lbm))
        print("    BMR %.0f kcal  ·  %d training + %d active days  ->  factor %.3f"
              % (bmr, n_train, n_move, factor))
        lo, hi = bmr * (factor - 0.075), bmr * (factor + 0.075)
        print("    MODELLED maintenance around %.0f-%.0f kcal" % (lo, hi))

        for label, tdee in (("low", lo), ("high", hi)):
            deficit = tdee - target
            pct = 100.0 * deficit / tdee
            kg = deficit * 7 / 7700.0
            print("      vs %-4s  deficit %4.0f kcal (%4.1f%%)  ->  %.2f kg/week"
                  % (label, deficit, pct, kg))

        safe_lo, safe_hi = 0.005 * w * 7700 / 7, 0.010 * w * 7700 / 7
        phase = p.get("_phase") or {}
        if phase:
            print("    PHASE — %s, since %s, review %s (was %s kcal)"
                  % (phase.get("name"), phase.get("startedOn"),
                     phase.get("reviewOn"), phase.get("was")))
        meas = measured_expenditure(key)
        if meas:
            print("    MEASURED — MacroFactor, %d days to %s" % (meas["n"], meas["to"]))
            print("      expenditure %.0f now, %.0f on a 14-day mean (estimate said %.0f-%.0f)"
                  % (meas["latest"], meas["recent"], lo, hi))
            if meas["trend14"] is not None and abs(meas["trend14"]) >= 25:
                print("      %+.0f kcal over the last fortnight — %s"
                      % (meas["trend14"], "falling" if meas["trend14"] < 0 else "rising"))
            d_meas = meas["recent"] - target
            print("      real deficit %.0f kcal (%.1f%%) -> %.2f kg/week"
                  % (d_meas, 100.0 * d_meas / meas["recent"], d_meas * 7 / 7700.0))
            drop = meas["first"] - meas["latest"]
            # A near-zero deficit is a failure when you meant to cut and the
            # plan is what a maintenance phase is for. Which one it is is not
            # something arithmetic can tell; the phase declaration can.
            on_purpose = bool(phase) and abs(d_meas) < 250
            if drop > 300:
                print("      expenditure has fallen %.0f kcal since %s"
                      % (drop, meas["from"]))
                if not on_purpose:
                    findings.append(
                        "%s's measured expenditure has fallen %.0f kcal since %s, "
                        "to %.0f. A %d kcal intake is now only %.0f kcal below it."
                        % (p["displayName"], drop, meas["from"], meas["latest"],
                           target, meas["latest"] - target))
            if on_purpose:
                print("      -> intake sits at measured expenditure. That is the "
                      "declared phase, not a stalled cut.")
                print("      -> judge it on the expenditure line climbing, not on "
                      "the scale. Review %s." % phase.get("reviewOn"))
            elif d_meas < safe_lo:
                print("      -> smaller than the retention band, not larger. The estimate "
                      "above is stale; believe this line.")
            print()

        # Muscle retention holds at 0.5-1.0% bodyweight per week. Faster is where
        # lean mass starts going with the fat.
        safe_lo, safe_hi = 0.005 * w * 7700 / 7, 0.010 * w * 7700 / 7
        print("    retention-safe deficit for %.1f kg: %.0f-%.0f kcal/day "
              "(%.2f-%.2f kg/week)" % (w, safe_lo, safe_hi, 0.005 * w, 0.010 * w))
        # Only judge from the model when there is nothing measured. Printing both
        # verdicts produced a report that argued with itself.
        if not meas:
            worst = hi - target
            if worst > safe_hi:
                print("    -> at the high estimate this is FASTER than muscle retention allows")
                findings.append("%s's deficit reaches %.0f kcal at the high maintenance "
                                "estimate, past the %.0f kcal retention ceiling."
                                % (p["displayName"], worst, safe_hi))
            elif (lo - target) < safe_lo:
                print("    -> at the low estimate this is slower than the usual band; fine, "
                      "but progress will be hard to see")

        # protein against bodyweight, which is the only way to judge it
        pro = p["dailyTargets"]["proteinG"]
        gkg = pro / w
        verdict = ("low end" if gkg < 1.7 else
                   "mid range" if gkg < 2.0 else "high end")
        print("    protein %d g = %.2f g/kg bodyweight (%.2f g/kg lean) — %s of 1.6-2.2"
              % (pro, gkg, pro / lbm, verdict))
        if gkg < 1.7:
            findings.append("%s's protein is %.2f g/kg, the bottom of the useful range "
                            "for someone lifting in a deficit." % (p["displayName"], gkg))

        fib = p["dailyTargets"]["fiberG"]
        dens = fib / target * 1000
        print("    fibre %d g = %.1f g per 1000 kcal (guideline is about 14)" % (fib, dens))
        if dens > 25:
            findings.append("%s's fibre is %.1f g per 1000 kcal, nearly double the "
                            "guideline density." % (p["displayName"], dens))

        tw = body.get("targetWeightKg")
        if tw:
            print("    goal %.1f -> %.1f kg" % (w, tw))
        print()

    print("  The activity factor is a guess with about +-300 kcal in it. MacroFactor's\n"
          "  adaptive TDEE is measured rather than assumed — where the two disagree,\n"
          "  believe MacroFactor.\n")
    return findings


def main():
    profiles, kitchen = load("profiles.json"), load("kitchen.json")
    try:
        training = load("training.json")
    except (IOError, OSError):
        training = None
    ef = kitchen["energyFactors"]
    fails = []

    fails.extend(energy_balance(profiles, training))

    print("DAILY TARGETS — do the four numbers agree with the calorie budget?\n")
    for key, p in profiles["people"].items():
        t = p["dailyTargets"]
        # Net carbs are digestible; fibre is carbohydrate too and carries its own
        # (smaller) energy. Both have to fit inside the calorie target.
        implied = (t["proteinG"] * ef["proteinG"] + t["fatG"] * ef["fatG"] +
                   t["netCarbsG"] * 4 + t["fiberG"] * ef["fiberG"])
        delta = implied - t["calories"]
        verdict = "consistent" if delta <= 0 else "OVER by %.0f kcal" % delta
        print("  %-8s %4d kcal target   macros imply %4.0f kcal   %s"
              % (p["displayName"], t["calories"], implied, verdict))
        if delta > 0:
            fails.append("%s's daily targets imply %.0f kcal but allow %d — "
                         "all four cannot be met at once."
                         % (p["displayName"], implied, t["calories"]))

    print("\nONE MIRROR MEAL — is it reachable once the carb base is on the plate?\n")
    base = kitchen["asianMacroBase"]
    pb = base["computed"]["perBlock"]
    m = profiles["mirrorMeals"]["lunch"]

    for label, blocks in sorted(base["blockRules"].items(), key=lambda kv: kv[1]):
        need_p = m["proteinG"] - pb["proteinG"] * blocks
        need_fib = m["fiberG"] - pb["fiberG"] * blocks
        need_fat = lo(m["fatG"]) - pb["fatG"] * blocks
        have = m["calories"] - pb["calories"] * blocks
        floor = need_p * ef["proteinG"] + need_fat * ef["fatG"] + need_fib * ef["fiberG"]
        delta = floor - have
        verdict = "reachable (%.0f kcal spare)" % -delta if delta <= 0 \
            else "IMPOSSIBLE, %.0f kcal over" % delta
        print("  %-22s %.1f blocks   %3.0f kcal left, macros floor %3.0f   %s"
              % (label, blocks, have, floor, verdict))
        if delta > 0:
            fails.append("A %.1f-block meal needs %.0f kcal of macros in %.0f kcal."
                         % (blocks, floor, have))

    print("\n  Note: the floor prices fibre at %g kcal/g and assumes zero digestible\n"
          "  carbohydrate comes with it. Real food is dearer, so a 'reachable'\n"
          "  verdict here is necessary, not sufficient." % ef["fiberG"])

    # A fixed breakfast written into profiles.json AND stored as a recipe is two
    # sources for one fact. Compare them rather than trusting whichever is read first.
    try:
        recipes = load("recipes.json")["recipes"]
        foods = load("foods.json")["foods"]
    except (IOError, OSError):
        recipes = foods = None
    if recipes and foods:
        print("\nTYPED vs DERIVED — where the same fact is written down twice\n")
        for key, p in profiles["people"].items():
            fb = p.get("fixedBreakfast")
            if not fb:
                continue
            match = [r for r in recipes if r.get("person") == key and r["slot"] == "breakfast"]
            if not match or not match[0].get("computed"):
                continue
            c = match[0]["computed"]
            print("  %s's breakfast — %s" % (p["displayName"], match[0]["title"]))
            for label, typed_k, calc_k in (("kcal", "calories", "calories"),
                                           ("protein", "proteinG", "proteinG"),
                                           ("fibre", "fiberG", "fiberG"),
                                           ("fat", "fatG", "fatG")):
                t_v, c_v = fb.get(typed_k), c.get(calc_k)
                if t_v is None or c_v is None:
                    continue
                d_v = c_v - t_v
                mark = "" if abs(d_v) <= max(1.0, abs(t_v) * 0.05) else "   <-- disagree"
                print("    %-8s typed %6.1f   derived %6.1f   %+6.1f%s"
                      % (label, t_v, c_v, d_v, mark))
            print("    The typed figures drive the day ledger. The derived ones come from\n"
                  "    generic tables. Neither is authoritative — the packets are.")

    if fails:
        print("\n%d contradiction(s):\n" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("\nAll targets internally consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Are the targets themselves arithmetically possible?

Two questions, both answerable without any recipe existing:

  1. Do a person's four daily targets agree with their calorie target?
     Protein, fat and carbohydrate have fixed energy contents. If the four
     numbers imply more calories than the calorie target allows, no diet
     satisfies all four — the targets contradict each other, not the food.

  2. Is one mirror meal reachable? Same idea, one level down, with the
     Asian Base blocks already on the plate.

  3. Can it actually be cooked? Question 2 prices macros at their Atwater
     minimum and assumes no digestible carbohydrate rides along, so its
     "reachable" is necessary and not sufficient. This one builds real
     plates out of foods.json instead — block, aroma base, vegetable, fat,
     a protein and a fibre source — and reports which of them land inside
     the spec. A spec no plate satisfies is not a hard recipe; it is a
     wrong number.

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
    """mirrorMeals.fatG is a range like "0-14". Take the charitable end.

    Since 2026-08-30 the low end is 0: fat is a ceiling, not a target. A meal
    that comes in leaner is not a miss, it is slack handed to the snack.
    """
    return float(str(v).split("-")[0])


def hi(v):
    """The other end of the same range; a plain number is its own ceiling."""
    return float(str(v).split("-")[-1])


MACROS = ("calories", "proteinG", "fatG", "fiberG")

# Every dish in this kitchen gets an aroma base — Cooking_Standards calls the
# alternative spartan and bans it. Costing it here keeps the search honest:
# a spec that only fits with naked chicken does not fit.
AROMA_BASE = {"knoblauch": 8, "ingwer": 8, "sojasauce": 10,
              "chili": 3, "fruehlingszwiebel": 15}

# Powders and seeds are excluded on purpose. foods.json knows psyllium husk is
# 80 g of fibre per 100 g and would satisfy any spec with a spoonful of it,
# which proves nothing about dinner. Same reason topUps is curated.
NOT_A_MEAL = ("flohsamenschalen", "leinsamen", "chiasamen", "haferkleie",
              "whey", "magerquark", "skyr", "huettenkaese", "eiklar")


def nutr(foods, key, grams):
    per = foods[key].get("per100g", foods[key])
    return dict((m, per.get(m, 0) * grams / 100.0) for m in MACROS)


def plus(*parts):
    out = dict((m, 0.0) for m in MACROS)
    for part in parts:
        for m in out:
            out[m] += part.get(m, 0)
    return out


def plates(foods, block, blocks, spec):
    """Every real plate that satisfies the mirror-meal spec.

    Protein and fibre are the two targets; the protein source and the fibre
    source are the two unknowns. Solving them together rather than in turn is
    the same rule adapt_recipe.py follows, and for the same reason — legumes
    carry protein, so fixing fibre afterwards overshoots.

    Returns (list of (kcal, macros, amounts), set of protein sources that work).
    """
    roles = {}
    for key, food in foods.items():
        roles.setdefault(food.get("role"), []).append(key)
    proteins = [k for k in roles.get("protein", []) if k not in NOT_A_MEAL]
    fibers = [k for k in roles.get("fiber", []) if k not in NOT_A_MEAL]
    vegs = roles.get("veg", []) + [k for k in roles.get("carb", []) if k == "konjaknudeln"]
    fats = [k for k in roles.get("fat", [])] + ["kokosmilch_light"]

    aroma = plus(*[nutr(foods, k, g) for k, g in AROMA_BASE.items() if k in foods])
    carb = dict((m, block[m] * blocks) for m in MACROS)
    want_p, want_fib = spec["proteinG"], spec["fiberG"]
    fat_lo, fat_hi = lo(spec["fatG"]), hi(spec["fatG"])

    found, sources = [], set()
    for pk in proteins:
        pn = foods[pk].get("per100g", foods[pk])
        for fk in fibers:
            fn = foods[fk].get("per100g", foods[fk])
            det = (pn["proteinG"] * fn.get("fiberG", 0)
                   - pn.get("fiberG", 0) * fn["proteinG"]) / 10000.0
            if abs(det) < 1e-9:
                continue                      # the two move together; no solution
            for vk in vegs:
                for vg in (100, 150, 200):
                    for fatk in fats:
                        for fg in ((0, 40, 60, 80) if fatk == "kokosmilch_light"
                                   else (0, 4, 6, 8, 10)):
                            rest = plus(carb, aroma, nutr(foods, vk, vg),
                                        nutr(foods, fatk, fg))
                            need_p = want_p - rest["proteinG"]
                            need_f = want_fib - rest["fiberG"]
                            a = (need_p * fn.get("fiberG", 0) / 100.0
                                 - need_f * fn["proteinG"] / 100.0) / det
                            b = (pn["proteinG"] / 100.0 * need_f
                                 - pn.get("fiberG", 0) / 100.0 * need_p) / det
                            if not (40 <= a <= 260 and 20 <= b <= 260):
                                continue      # not a portion anyone would serve
                            # Round to what a scale shows, then re-derive, so the
                            # numbers describe the food that would be cooked.
                            a, b = round(a / 5) * 5, round(b / 5) * 5
                            tot = plus(rest, nutr(foods, pk, a), nutr(foods, fk, b))
                            if abs(tot["proteinG"] - want_p) > 2:
                                continue
                            if tot["fiberG"] < want_fib - 0.5:
                                continue
                            if not fat_lo <= tot["fatG"] <= fat_hi:
                                continue
                            if tot["calories"] > spec["calories"] + 10:
                                continue
                            sources.add(pk)
                            found.append((tot["calories"], tot,
                                          {pk: a, fk: b, vk: vg, fatk: fg}))
    found.sort(key=lambda r: abs(r[0] - spec["calories"]))
    return found, sources


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
        # Never negative. With no fat floor the blocks can already carry more
        # fat than the meal demands, and a negative "need" would credit those
        # calories back and understate the floor.
        need_fat = max(0.0, lo(m["fatG"]) - pb["fatG"] * blocks)
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
          "  verdict here is necessary, not sufficient. The next section is the\n"
          "  sufficient one." % ef["fiberG"])

    # The question above asks whether the arithmetic permits the meal. This one
    # asks whether the pantry does, which is the question that decides whether
    # anyone can cook dinner.
    try:
        foods = load("foods.json")["foods"]
    except (IOError, OSError):
        foods = None
    if foods:
        print("\nREAL FOOD — does any actual plate satisfy the spec?\n")
        print("  spec  %d kcal · %g g protein · %g g fibre · fat %s g"
              % (m["calories"], m["proteinG"], m["fiberG"], m["fatG"]))
        print("  every plate below also carries the full aroma base "
              "(garlic, ginger, soy, chilli, spring onion)\n")
        all_proteins = set(k for k, f in foods.items()
                           if f.get("role") == "protein" and k not in NOT_A_MEAL)
        for label, blocks in sorted(base["blockRules"].items(), key=lambda kv: kv[1]):
            found, sources = plates(foods, pb, blocks, m)
            if not found:
                print("  %-22s %.1f blocks   NO PLATE FITS" % (label, blocks))
                fails.append("No combination in foods.json satisfies the mirror meal "
                             "on %.1f blocks. The spec is a wrong number, not a hard "
                             "recipe." % blocks)
                continue
            kcal, tot, amounts = found[0]
            print("  %-22s %.1f blocks   %4d plates fit   %d of %d protein sources"
                  % (label, blocks, len(found), len(sources), len(all_proteins)))
            print("      closest: %.0f kcal · %.1f P · %.1f fibre · %.1f fat"
                  % (kcal, tot["proteinG"], tot["fiberG"], tot["fatG"]))
            print("      %.1f block + %s" % (blocks, ", ".join(
                "%s %d g" % (k, g) for k, g in sorted(amounts.items(),
                                                      key=lambda kv: -kv[1]) if g)))
            missing = sorted(all_proteins - sources)
            if missing:
                print("      out of reach here: %s" % ", ".join(missing))
        print("\n  A protein source listed as out of reach is not banned — it cannot\n"
              "  carry 40 g of protein inside this fat ceiling. Salmon and eggs are\n"
              "  breakfast and snack foods in this plan for that reason alone.")

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

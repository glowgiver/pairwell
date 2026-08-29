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


def main():
    profiles, kitchen = load("profiles.json"), load("kitchen.json")
    ef = kitchen["energyFactors"]
    fails = []

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

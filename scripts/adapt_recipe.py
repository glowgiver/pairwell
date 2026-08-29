"""Take a recipe as found and fit it to the mirror-meal target.

The division of labour: you find dishes, this decides the grams. It scales the
protein sources and the fibre sources — nothing else — because those are the two
things a target actually constrains. Aromatics, sauce and vegetables are the
dish's character and are left exactly as the recipe wrote them.

It solves both targets at once rather than one after the other, since legumes
carry protein and meat carries none of the fibre; adjusting them in sequence
overshoots. Two equations, two unknowns:

    a * protein_from_protein_sources + b * protein_from_fibre_sources = protein still needed
    a * fibre_from_protein_sources   + b * fibre_from_fibre_sources   = fibre still needed

Then it rounds to weighable amounts and re-derives every figure from the rounded
grams, so the report describes the food you will actually cook.

Usage:  python3 scripts/adapt_recipe.py            # adapt all, write back
        python3 scripts/adapt_recipe.py <id>       # one recipe
        python3 scripts/adapt_recipe.py --dry-run  # report only, write nothing
"""

import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
MACROS = ("calories", "proteinG", "carbsG", "fiberG", "fatG")

SCALED = ("protein", "fiber")     # the only roles the adapter is allowed to move


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def zero():
    return dict((k, 0.0) for k in MACROS)


def add(acc, per100, grams):
    for k in MACROS:
        acc[k] += per100[k] * grams / 100.0
    return acc


def weighable(g):
    """Round to something a kitchen scale and a human can both handle."""
    if g < 10:
        return round(g * 2) / 2.0          # half grams for spices and oil
    if g < 50:
        return float(round(g))
    return float(round(g / 5.0) * 5)


def totals(recipe, foods, block, servings_divisor=True):
    acc = add(zero(), block, 100.0 * recipe.get("blocks", 0)) if recipe.get("blocks") else zero()
    for ing in recipe["ingredients"]:
        f = foods[ing["food"]]
        add(acc, f["per100g"], ing["g"])
    n = recipe.get("servings", 1) if servings_divisor else 1
    return dict((k, v / n) for k, v in acc.items())


def solve(recipe, foods, block, target):
    """Return {ingredient index: new grams}, or None if the recipe cannot be fitted."""
    groups = {"protein": [], "fiber": []}
    fixed = add(zero(), block, 100.0 * recipe.get("blocks", 0)) if recipe.get("blocks") else zero()

    for i, ing in enumerate(recipe["ingredients"]):
        role = foods[ing["food"]]["role"]
        if role in groups:
            groups[role].append(i)
        else:
            add(fixed, foods[ing["food"]]["per100g"], ing["g"])

    n = float(recipe.get("servings", 1))

    def group_totals(idxs):
        acc = zero()
        for i in idxs:
            add(acc, foods[recipe["ingredients"][i]["food"]]["per100g"],
                recipe["ingredients"][i]["g"])
        return acc

    A, B = group_totals(groups["protein"]), group_totals(groups["fiber"])

    # per serving
    need_p = target["proteinG"] - fixed["proteinG"] / n
    need_f = target["fiberG"] - fixed["fiberG"] / n
    ap, af = A["proteinG"] / n, A["fiberG"] / n
    bp, bf = B["proteinG"] / n, B["fiberG"] / n

    det = ap * bf - af * bp
    if groups["fiber"] and abs(det) > 1e-6:
        a = (need_p * bf - need_f * bp) / det
        b = (ap * need_f - af * need_p) / det
    elif ap > 1e-6:
        a, b = need_p / ap, 1.0          # no fibre source to move — protein only
    else:
        return None, "no protein source to scale"

    notes = []
    for name, val in (("protein", a), ("fibre", b)):
        if val <= 0:
            return None, ("the %s sources would have to go negative — this dish "
                          "cannot reach the target by rescaling alone" % name)
    clamped = []
    if a > 3 or a < 0.3:
        clamped.append("protein x%.2f" % a); a = min(max(a, 0.3), 3.0)
    if b > 3 or b < 0.3:
        clamped.append("fibre x%.2f" % b); b = min(max(b, 0.3), 3.0)
    if clamped:
        notes.append("clamped: " + ", ".join(clamped) + " — the recipe is too far from the target")

    changes = {}
    for i in groups["protein"]:
        changes[i] = weighable(recipe["ingredients"][i]["g"] * a)
    for i in groups["fiber"]:
        changes[i] = weighable(recipe["ingredients"][i]["g"] * b)
    return (changes, notes), None


def report(recipe, foods, block, target, changes, notes):
    orig = [ing["g"] for ing in recipe["ingredients"]]
    for i, g in (changes or {}).items():
        recipe["ingredients"][i]["g"] = g
    result = totals(recipe, foods, block)

    print("\n" + "=" * 66)
    print(recipe["title"])
    print("=" * 66)

    print("\nBLOCK 1 — what changed from the original\n")
    if not target:
        print("  nothing — this recipe is not fitted to a target, only measured")
    any_change = False
    for i, ing in enumerate(recipe["ingredients"]):
        if changes and i in changes and abs(orig[i] - ing["g"]) > 0.01:
            print("  %-28s %6.0f g  ->  %6.0f g" % (foods[ing["food"]]["name"], orig[i], ing["g"]))
            any_change = True
    if target and not any_change:
        print("  nothing — the amounts as found already hit the target")
    for n in notes or []:
        print("  ! " + n)

    if target:
        print("\nBLOCK 2 — target vs result (per serving)\n")
        rows = [("Calories", "calories", target["calories"], "kcal"),
                ("Protein", "proteinG", target["proteinG"], "g"),
                ("Fibre", "fiberG", target["fiberG"], "g"),
                ("Fat", "fatG", target["fatG"], "g")]
        print("  %-14s %8s %8s %9s" % ("", "target", "result", "delta"))
        for label, key, tgt, unit in rows:
            val = result[key]
            if isinstance(tgt, str):                       # the "12-15" fat range
                lo, hi = [float(x) for x in tgt.split("-")]
                d = 0 if lo <= val <= hi else (val - lo if val < lo else val - hi)
                tgt_s = tgt
            else:
                d = val - tgt
                tgt_s = "%.0f" % tgt
            flag = "" if abs(d) < 0.05 else ("  <-- off" if abs(d) > max(2.0, abs(float(str(tgt).split('-')[0])) * 0.05) else "")
            print("  %-14s %8s %8.1f %+9.1f%s" % (label + " " + unit, tgt_s, val, d, flag))

        fat_lo = float(str(target["fatG"]).split("-")[0])
        if result["fatG"] < fat_lo:
            short = fat_lo - result["fatG"]
            print("\n  Fat is %.1f g short. %.0f g of oil closes it and costs %.0f kcal,"
                  % (short, short, short * 9))
            print("  which would put the meal at %.0f kcal." % (result["calories"] + short * 9))
    else:
        print("\nBLOCK 2 — macros (per serving)\n")
        for label, key, unit in (("Calories", "calories", "kcal"), ("Protein", "proteinG", "g"),
                                 ("Fibre", "fiberG", "g"), ("Fat", "fatG", "g"),
                                 ("Carbs", "carbsG", "g")):
            print("  %-14s %8.1f %s" % (label, result[key], unit))

    print("\nBLOCK 3 — method\n")
    for i, s in enumerate(recipe["steps"], 1):
        print("  %d. %s" % (i, s))
    if recipe.get("blocks"):
        print("  +  serve on %.1f Asian Base block(s)" % recipe["blocks"])
    return result


def main():
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    args = [a for a in args if not a.startswith("--")]
    only = args[0] if args else None

    foods = load("foods.json")["foods"]
    recipes = load("recipes.json")
    profiles, kitchen = load("profiles.json"), load("kitchen.json")
    block = kitchen["asianMacroBase"]["computed"]["per100gCooked"]
    mirror = profiles["mirrorMeals"]["lunch"]

    missing = set()
    for r in recipes["recipes"]:
        for ing in r["ingredients"]:
            if ing["food"] not in foods:
                missing.add(ing["food"])
    if missing:
        print("Unknown foods, add them to data/foods.json first: " + ", ".join(sorted(missing)))
        return 1

    touched = 0
    for r in recipes["recipes"]:
        if only and r["id"] != only:
            continue
        touched += 1
        target = mirror if (r["slot"] == "mirror" and not r.get("fixed")) else None
        changes, notes, err = None, None, None
        if target:
            out, err = solve(r, foods, block, target)
            if err:
                print("\n%s: %s" % (r["title"], err))
            else:
                changes, notes = out
        result = report(r, foods, block, target, changes, notes)
        r["computed"] = dict((k, round(v, 1)) for k, v in result.items())
        r["computed"]["_generated"] = "by scripts/adapt_recipe.py — do not edit by hand"
        r["adapted"] = {"target": "mirrorMeals" if target else "none (not rescaled)",
                        "notes": notes or []}

    if not touched:
        print("No recipe with id %r." % only)
        return 1
    if dry:
        print("\n--dry-run: recipes.json not written.")
        return 0
    with open(os.path.join(DATA, "recipes.json"), "w", encoding="utf-8") as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\nwritten data/recipes.json  (%d recipe(s))" % touched)
    return 0


if __name__ == "__main__":
    sys.exit(main())

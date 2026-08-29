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


def _cands(kitchen, role, cuisine):
    """Curated shortlist, filtered by what the dish will accept.

    foods.json has cheaper options on paper — psyllium husk wins fibre on
    arithmetic and loses it in a braise. The list in kitchen.json is what
    belongs in food; cost only ranks what is already acceptable.
    """
    out = []
    for c in (kitchen.get("topUps") or {}).get(role, []):
        goes = c.get("goesWith") or ["any"]
        if cuisine and "any" not in goes and cuisine not in goes:
            continue
        out.append(c)
    return out


def _yield_of(foods, c, key):
    return foods[c["food"]]["per100g"][key] / 100.0


def _cost(foods, c, grams):
    per = foods[c["food"]]["per100g"]
    return (per["calories"] * grams / 100.0, per["proteinG"] * grams / 100.0)


def _fiber_options(foods, cands, gap):
    """Single ingredients that close the gap under their own volume cap,
    and failing that, the two-part split the kitchen brief actually asks for.

    Ranked by calories, but only among things that fit in a lunchbox. Cheapest
    per gram of fibre is spinach, and 478 g of it is not dinner.
    """
    singles, splits = [], []
    for c in cands:
        y = _yield_of(foods, c, "fiberG")
        if not y:
            continue
        g = gap / y
        if g <= c["maxG"]:
            kcal, prot = _cost(foods, c, g)
            singles.append((kcal, [(c, g)], prot))
    if singles:
        singles.sort(key=lambda r: r[0])
        return singles, "single"

    for bulky in [c for c in cands if c.get("kind") == "bulky"]:
        yb = _yield_of(foods, bulky, "fiberG")
        gb = bulky["maxG"]
        rest = gap - yb * gb
        if rest <= 0:
            continue
        for d in [c for c in cands if c.get("kind") == "dense"]:
            yd = _yield_of(foods, d, "fiberG")
            if not yd:
                continue
            gd = rest / yd
            if gd > d["maxG"]:
                continue
            k1, p1 = _cost(foods, bulky, gb)
            k2, p2 = _cost(foods, d, gd)
            splits.append((k1 + k2, [(bulky, gb), (d, gd)], p1 + p2))
    splits.sort(key=lambda r: r[0])
    return splits, "split"


def topups(recipe, foods, block, kitchen, target, result):
    """Scaling moved what was already in the pan. This says what to add.

    Proposals, printed. Nothing is written back: putting lentils in a dish is
    a decision about the dish, and the script does not get to make it.
    """
    gap_p = target["proteinG"] - result["proteinG"]
    gap_f = target["fiberG"] - result["fiberG"]
    if gap_p < 1.0 and gap_f < 0.5:
        return

    cuisine = recipe.get("cuisine")
    n = float(recipe.get("servings", 1))
    print("\nBLOCK 2b — what to add, since rescaling did not get there\n")
    if cuisine:
        art = "an" if cuisine[0].lower() in "aeiou" else "a"
        print("  filtered to what suits %s %s dish" % (art, cuisine))
    else:
        print("  this recipe declares no cuisine, so nothing is filtered out —")
        print("  add \"cuisine\" to it and this list gets shorter and better")

    added_kcal, added_p = 0.0, 0.0
    picks = []

    if gap_f >= 0.5:
        print("\n  Fibre short by %.1f g:" % gap_f)
        opts, kind = _fiber_options(foods, _cands(kitchen, "fiber", cuisine), gap_f)
        if not opts:
            print("    nothing on the shortlist closes this, alone or in a pair.")
            print("    The dish is too far from the target — look for another.")
        else:
            if kind == "split":
                print("    no single ingredient closes it inside a sensible")
                print("    portion, so these are pairs — bulk plus density:")
            for kcal, parts, prot in opts[:3]:
                desc = " + ".join("%s %.0f g" % (foods[c["food"]]["name"], weighable(g))
                                  for c, g in parts)
                extra = "  (+%.1f g protein)" % prot if prot >= 1.0 else ""
                print("    %-52s %+4.0f kcal%s" % (desc, kcal, extra))
            for c, g in opts[0][1]:
                if c.get("note"):
                    print("      %s: %s" % (foods[c["food"]]["name"], c["note"]))
            added_kcal, added_p = opts[0][0], opts[0][2]
            picks.extend((c["food"], g) for c, g in opts[0][1])
            print("    grams are per serving (x%.0f for the batch)" % n)

    gap_p2 = gap_p - added_p
    if gap_p2 >= 1.0:
        label = "Protein short by %.1f g" % gap_p
        if added_p >= 1.0:
            label += " — %.1f g after the fibre pick above" % gap_p2
        print("\n  %s:" % label)
        rows = []
        for c in _cands(kitchen, "protein", cuisine):
            y = _yield_of(foods, c, "proteinG")
            if not y:
                continue
            g = gap_p2 / y
            if g > c["maxG"]:
                continue
            rows.append((_cost(foods, c, g)[0], g, c))
        rows.sort(key=lambda r: r[0])
        if not rows:
            print("    nothing closes this inside a sensible portion.")
        for kcal, g, c in rows[:3]:
            note = "  — " + c["note"] if c.get("note") else ""
            print("    %-26s %5.0f g/serving  %+4.0f kcal%s"
                  % (foods[c["food"]]["name"], weighable(g), kcal, note))
        if rows:
            added_kcal += rows[0][0]
            picks.append((rows[0][2]["food"], rows[0][1]))

    if not picks:
        return

    # Adding a legume adds protein as well as fibre, so the meat has to come
    # down. Saying "+148 kcal and it fits" without re-solving is the same
    # sequential mistake solve() exists to avoid — do the whole thing again
    # with the addition in the pan, and print the dish that actually works.
    import copy
    r2 = copy.deepcopy(recipe)
    for food_id, g in picks:
        r2["ingredients"].append({"food": food_id, "g": weighable(g) * n})
    out2, err2 = solve(r2, foods, block, target)
    print("\n  Take the first of each and re-fit the whole dish:\n")
    if err2:
        print("    still cannot be fitted — %s" % err2)
        return
    changes2, notes2 = out2
    for i, g in changes2.items():
        r2["ingredients"][i]["g"] = g
    final = totals(r2, foods, block)
    orig_g = dict((ing["food"], ing["g"]) for ing in recipe["ingredients"])
    for ing in r2["ingredients"]:
        was = orig_g.get(ing["food"])
        name = foods[ing["food"]]["name"]
        if was is None:
            print("    %-28s %6s      %6.0f g   NEW" % (name, "", ing["g"]))
        elif abs(was - ing["g"]) > 0.5:
            print("    %-28s %6.0f g  ->  %6.0f g" % (name, was, ing["g"]))
    print("\n    %-14s %8s %8s" % ("", "target", "result"))
    for label, key in (("Calories", "calories"), ("Protein", "proteinG"),
                       ("Fibre", "fiberG"), ("Fat", "fatG")):
        t = target[key]
        print("    %-14s %8s %8.1f" % (label, t if isinstance(t, str) else "%.0f" % t,
                                       final[key]))
    for nt in notes2 or []:
        print("    ! " + nt)
    fat_lo = float(str(target["fatG"]).split("-")[0])
    if final["fatG"] < fat_lo:
        short = fat_lo - final["fatG"]
        print("\n    Still %.1f g short on fat: %.0f g of oil, +%.0f kcal, "
              "meal at %.0f." % (short, short, short * 9,
                                 final["calories"] + short * 9))
    print("\n    Amounts are for the whole recipe (%d servings), as written." % n)


def report(recipe, foods, block, target, changes, notes, kitchen=None):
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

        if kitchen:
            topups(recipe, foods, block, kitchen, target, result)
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
                # not fatal any more: the dish cannot be rescaled into the
                # target, which is exactly when the top-up list is worth
                # printing. Keep the target so the gap is still measured.
                notes = ["could not rescale: " + err]
            else:
                changes, notes = out
        result = report(r, foods, block, target, changes, notes, kitchen)
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

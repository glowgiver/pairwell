"""Derive every macro figure in data/kitchen.json from two inputs:

    1. the ingredient list (raw grams + per-100g-raw nutrition)
    2. one measured cooked weight

This script holds NO data of its own. It only calculates. That is the whole
point: the old file kept per-block macros, per-100g-cooked macros and the batch
yield as three separately maintained numbers, and they drifted ~34% apart.
Numbers that follow from each other must be computed, not typed.

Run after changing ingredients or after weighing a batch:

    python3 scripts/recompute_macros.py

Raw-vs-cooked is handled correctly by construction: nutrition is summed from
RAW weights (that is what the packaging states), and portioning divides by the
COOKED weight (that is what the scale shows). Water loss needs no separate
term — it is already inside the measured cooked weight.
"""

import json
import os

BASE = os.path.dirname(__file__)
PATH = os.path.join(BASE, "..", "data", "kitchen.json")

KEYS = ["calories", "proteinG", "carbsG", "fiberG", "fatG"]


def r(value, places):
    """Round for display without pretending to precision we don't have."""
    return round(value, places)


def main():
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)

    base = data["asianMacroBase"]
    ingredients = base["ingredients"]
    yield_ = base["yield"]

    cooked_g = yield_["cookedWeightG"]
    blocks = yield_["blocks"]

    # --- sum nutrition from RAW weights -----------------------------------
    total = {k: 0.0 for k in KEYS}
    raw_solids = 0
    for ing in ingredients:
        if ing.get("isWater"):
            continue
        raw_solids += ing["g"]
        factor = ing["g"] / 100.0
        for k in KEYS:
            total[k] += ing["per100gRaw"][k] * factor

    # --- sanity check: can this cooked weight even exist? -----------------
    water_g = sum(i["g"] for i in ingredients if i.get("isWater"))
    max_possible = raw_solids + water_g
    warnings = []
    if cooked_g > max_possible:
        warnings.append(
            "cookedWeightG (%d g) exceeds raw solids + water (%d g). "
            "Nothing can weigh more than what went into the pot."
            % (cooked_g, max_possible)
        )
    if cooked_g < raw_solids:
        warnings.append(
            "cookedWeightG (%d g) is below the raw solids (%d g). "
            "Grains gain water, they do not lose it."
            % (cooked_g, raw_solids)
        )

    # --- derive ------------------------------------------------------------
    per_100g = {k: r(total[k] / cooked_g * 100, 1) for k in KEYS}
    per_block = {k: r(total[k] / blocks, 1) for k in KEYS}
    grams_per_block = r(cooked_g / blocks, 0)

    base["computed"] = {
        "_generated": "by scripts/recompute_macros.py — do not edit by hand",
        "rawSolidsG": raw_solids,
        "batchTotal": {k: r(total[k], 1) for k in KEYS},
        "per100gCooked": per_100g,
        "perBlock": per_block,
        "gramsPerBlock": grams_per_block,
    }

    log = data["macroFactorLogging"]["asianBaseCustomFoodPer100gCooked"]
    log.clear()
    log["_generated"] = "by scripts/recompute_macros.py — do not edit by hand"
    log.update(per_100g)

    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # --- report ------------------------------------------------------------
    status = yield_.get("_status", "")
    print("Asian Base Block — recomputed")
    print("  raw solids        %6d g" % raw_solids)
    print("  water             %6d g" % water_g)
    print("  cooked weight     %6d g   %s" % (cooked_g, status))
    print("  blocks            %6d     (%g g each)" % (blocks, grams_per_block))
    print()
    print("  batch total       %6.0f kcal · %.1f g protein · %.1f g fiber"
          % (total["calories"], total["proteinG"], total["fiberG"]))
    print("  per 100 g cooked  %6.1f kcal · %.1f g protein · %.1f g fiber"
          % (per_100g["calories"], per_100g["proteinG"], per_100g["fiberG"]))
    print("  per block         %6.1f kcal · %.1f g protein · %.1f g fiber"
          % (per_block["calories"], per_block["proteinG"], per_block["fiberG"]))
    print()
    print("  MacroFactor custom food: %.0f kcal / 100 g cooked" % per_100g["calories"])
    print("  logging 150 g          = %.0f kcal · %.1f g protein"
          % (per_100g["calories"] * 1.5, per_100g["proteinG"] * 1.5))

    if warnings:
        print()
        for w in warnings:
            print("  WARNING: " + w)

    if status == "ESTIMATED":
        print()
        print("  NOTE: cooked weight is estimated. Weigh the next batch and put the")
        print("        real number in yield.cookedWeightG, then re-run this script.")


if __name__ == "__main__":
    main()

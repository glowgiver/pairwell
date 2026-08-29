"""Check Eunice's seasonal skincare plan against its own safety rules.

The plan states four golden rules and then lays out 28 evenings. Nothing stops
those two halves drifting apart when a season gets edited, and the rules exist
for a reason — the MFU limit in particular. So check them mechanically.

    python3 scripts/check_routine_rules.py

Exits non-zero if any evening violates a rule.
"""

import json
import os
import re
import sys

PATH = os.path.join(os.path.dirname(__file__), "..", "data", "routines.json")

# Devices that need a conductive medium and must not sit under an oil.
ELECTRICAL = re.compile(r"booster pro|high focus shot", re.I)
# Gua Sha is manual and is *meant* to be used over oil, so it is not covered.
OILS = re.compile(r"freiöl|rose hip oil", re.I)

RETINOL = re.compile(r"retinol", re.I)
EXOSOME = re.compile(r"exosome", re.I)
AIR_SHOT = re.compile(r"air shot", re.I)
MFU = re.compile(r"high focus shot", re.I)


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    eunice = data["skincare"].get("eunice", {})
    seasons = eunice.get("seasons")
    if not seasons:
        print("No seasonal plan found — nothing to check.")
        return 0

    problems = []
    checked = 0

    for name, season in seasons.items():
        mfu_nights = []

        for evening in season["pmWeekly"]:
            checked += 1
            day = evening["day"]
            where = "%s/%s" % (name, day)
            joined = " > ".join(evening["steps"])

            has_retinol = bool(RETINOL.search(joined))
            has_exosome = bool(EXOSOME.search(joined))
            has_air_shot = bool(AIR_SHOT.search(joined))
            has_mfu = bool(MFU.search(joined))

            if has_mfu:
                mfu_nights.append(day)

            # Rule: no-mix actives
            if has_retinol and has_exosome:
                problems.append("%s: Exosome Shot on a retinol night" % where)
            if has_retinol and has_air_shot:
                problems.append("%s: Booster Pro Air Shot on a retinol night" % where)
            if has_mfu and has_exosome:
                problems.append("%s: Exosome Shot on a High Focus Shot night" % where)
            if has_mfu and has_air_shot:
                problems.append("%s: Booster Pro Air Shot on a High Focus Shot night" % where)

            # Rule: conductivity — oils insulate, so they come after any device
            first_oil = next((i for i, s in enumerate(evening["steps"]) if OILS.search(s)), None)
            last_device = next((i for i in range(len(evening["steps"]) - 1, -1, -1)
                                if ELECTRICAL.search(evening["steps"][i])), None)
            if first_oil is not None and last_device is not None and first_oil < last_device:
                problems.append("%s: oil applied before a device (insulates it)" % where)

        # Rule: MFU at most once a week
        if len(mfu_nights) > 1:
            problems.append("%s: High Focus Shot on %d nights (%s) — the limit is 1/week"
                            % (name, len(mfu_nights), ", ".join(mfu_nights)))
        elif not mfu_nights:
            problems.append("%s: no High Focus Shot night at all — check this is intended" % name)

    print("Checked %d evenings across %d seasons." % (checked, len(seasons)))
    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("No rule violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

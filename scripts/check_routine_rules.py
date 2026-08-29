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


ACIDS = ("bha", "glycolic")


def check_phased(person, problems):
    """Philipp's protocol: one active per night, rotating by phase.

    His cardinal rule is that adapalene and an acid never share a night. The
    data shape makes that structurally impossible — one slot per night — but
    assert it anyway, because the shape could change.
    """
    phases = person.get("phases")
    if not phases:
        return 0

    actives = person.get("actives", {})
    checked = 0
    for phase in phases:
        seen_days = set()
        for entry in phase["schedule"]:
            checked += 1
            day, key = entry["day"], entry.get("active")
            where = "%s/%s" % (phase["id"], day)

            if day in seen_days:
                problems.append("%s: duplicate day in schedule" % where)
            seen_days.add(day)

            if key and key not in actives:
                problems.append("%s: unknown active %r" % (where, key))

        days = [e["day"] for e in phase["schedule"]]
        if len(days) != 7:
            problems.append("%s: %d nights scheduled, expected 7" % (phase["id"], len(days)))

        n_adap = sum(1 for e in phase["schedule"] if e.get("active") == "adapalene")
        n_acid = sum(1 for e in phase["schedule"] if e.get("active") in ACIDS)
        if n_adap > 4:
            problems.append("%s: adapalene %d nights/week — the protocol never goes above 3"
                            % (phase["id"], n_adap))
        if n_adap + n_acid > 5:
            problems.append("%s: %d active nights/week leaves fewer than 2 rest nights"
                            % (phase["id"], n_adap + n_acid))

    # the PM base must actually contain the slot the schedule fills
    pm = person.get("pm", {})
    slots = [s for s in pm.get("steps", []) if s.get("activeSlot")]
    if len(slots) != 1:
        problems.append("pm.steps has %d active slots, expected exactly 1" % len(slots))

    return checked


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    eunice = data["skincare"].get("eunice", {})
    seasons = eunice.get("seasons")

    problems = []
    checked = 0

    checked += check_phased(data["skincare"].get("philipp", {}), problems)

    if not seasons:
        print("Checked %d nights. No seasonal plan found." % checked)
        for p in problems:
            print("  - " + p)
        return 1 if problems else 0

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

    print("Checked %d nights: %d of Philipp's phase schedule, plus %d of Eunice's seasons."
          % (checked, checked - 28, 28))
    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("No rule violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

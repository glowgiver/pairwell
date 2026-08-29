"""Read the recipe inbox and say what is missing before anyone cooks anything.

The bottleneck in turning a found recipe into data is never the typing. It is
the two questions only this repo can answer: is every ingredient known, and is
every amount a weight? This answers both for a whole batch of recipes at once,
so a folder filled over a week costs one command rather than one conversation
per dish.

  python3 scripts/read_inbox.py            # report only
  python3 scripts/read_inbox.py --write    # also append the clean ones to recipes.json

Files that are not clean are never written. A half-resolved recipe in the
library is worse than none: its macros would be quietly wrong.
"""

import glob
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "..", "data")
INBOX = os.path.join(BASE, "..", "inbox")

# Spoon measures are volume; the target is weight. These are the usual
# approximations and they are approximations — flagged in the report so the
# number can be replaced by a real one off a scale.
SPOONS = {"el": 15.0, "essloffel": 15.0, "tbsp": 15.0, "tablespoon": 15.0,
          "tl": 5.0, "teeloffel": 5.0, "tsp": 5.0, "teaspoon": 5.0,
          "prise": 0.5, "pinch": 0.5}

AMOUNT = re.compile(r"^\s*([\d.,/]+)\s*([a-zA-ZäöüÄÖÜ]*)\.?\s+(.*?)\s*$")


def fold(s):
    """Normalise for matching: case, umlauts, punctuation, spacing."""
    s = s.lower()
    for a, b in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss"), ("é", "e")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", s)


def number(tok):
    tok = tok.replace(",", ".")
    if "/" in tok:
        a, _, b = tok.partition("/")
        try:
            return float(a) / float(b)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(tok)
    except ValueError:
        return None


def match_food(text, foods):
    """Best food id for a free-text ingredient, or None."""
    want = fold(text)
    if not want:
        return None, []
    exact, starts, subs = [], [], []
    for fid, f in foods.items():
        for cand in (fid, f["name"]):
            c = fold(cand)
            if not c:
                continue
            if c == want:
                exact.append(fid)
            elif want.startswith(c) or c.startswith(want):
                starts.append(fid)
            elif c in want or want in c:
                subs.append(fid)
    for bucket in (exact, starts, subs):
        uniq = sorted(set(bucket))
        if len(uniq) == 1:
            return uniq[0], []
        if len(uniq) > 1:
            return None, uniq          # ambiguous — make a human choose
    return None, []


def parse(path, foods):
    r = {"file": os.path.basename(path), "ingredients": [], "steps": [],
         "problems": [], "notes": [], "meta": {}}
    section = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.strip().startswith("#") and not line.strip().startswith("##"):
                if not r.get("title") and line.lstrip("# ").strip():
                    r["title"] = line.lstrip("# ").strip()
                continue
            s = line.strip()
            if not s:
                continue
            if s.lower().startswith("## ingredient"):
                section = "ing"; continue
            if s.lower().startswith("## step"):
                section = "step"; continue
            if ":" in s and section is None:
                k, _, v = s.partition(":")
                r["meta"][k.strip().lower()] = v.split("#")[0].strip()
                continue
            if section == "step":
                r["steps"].append(s.lstrip("-* ").strip())
                continue
            if section == "ing":
                m = AMOUNT.match(s)
                if not m:
                    r["problems"].append("cannot read an amount from: %s" % s)
                    continue
                qty, unit, name = number(m.group(1)), fold(m.group(2)), m.group(3)
                if qty is None:
                    r["problems"].append("cannot read the number in: %s" % s)
                    continue
                if unit in ("g", "gramm", "gram", ""):
                    grams = qty
                elif unit in ("ml", "milliliter"):
                    grams = qty
                    r["notes"].append("%s: %g ml taken as %g g" % (name, qty, qty))
                elif unit in SPOONS:
                    grams = qty * SPOONS[unit]
                    r["notes"].append("%s: %g %s taken as %g g (approximate)"
                                      % (name, qty, m.group(2), grams))
                else:
                    r["problems"].append("unknown unit %r in: %s" % (m.group(2), s))
                    continue
                fid, ambiguous = match_food(name, foods)
                if fid:
                    r["ingredients"].append({"food": fid, "g": round(grams, 1),
                                             "_as_written": name})
                elif ambiguous:
                    r["problems"].append("%r matches several foods: %s"
                                         % (name, ", ".join(ambiguous)))
                else:
                    r["problems"].append("%r is not in foods.json yet" % name)
    if not r.get("title"):
        r["problems"].append("no title — the first line should be '# Dish name'")
    return r


def main():
    write = "--write" in sys.argv
    foods = json.load(open(os.path.join(DATA, "foods.json"), encoding="utf-8"))["foods"]
    lib = json.load(open(os.path.join(DATA, "recipes.json"), encoding="utf-8"))
    known = set(r["id"] for r in lib["recipes"])

    files = sorted(f for f in glob.glob(os.path.join(INBOX, "*.md"))
                   if os.path.basename(f) != "TEMPLATE.md")

    # Anything that is not markdown is something a human dropped for Claude to
    # read — a photo of a cookbook page, a saved article. Name them rather than
    # skipping them silently, so nothing sits in the folder forgotten.
    others = sorted(f for f in glob.glob(os.path.join(INBOX, "*"))
                    if not f.endswith(".md") and os.path.isfile(f))
    if others:
        print("Waiting to be transcribed (this script only reads .md):")
        for f in others:
            print("  - " + os.path.basename(f))
        print("  Ask Claude to turn these into .md files, then run this again.\n")

    if not files:
        if not others:
            print("inbox/ is empty. Copy inbox/TEMPLATE.md and fill it in.")
        return 0

    clean, blocked = [], 0
    for path in files:
        r = parse(path, foods)
        print("\n" + "-" * 62)
        print("%s   (%s)" % (r.get("title", "?"), r["file"]))
        print("-" * 62)
        print("  %d ingredient(s), %d step(s)" % (len(r["ingredients"]), len(r["steps"])))
        for n in r["notes"]:
            print("  ~ " + n)
        if r["problems"]:
            blocked += 1
            print("  BLOCKED:")
            for p in r["problems"]:
                print("    - " + p)
            continue

        rid = re.sub(r"-+", "-",
                     re.sub(r"[^a-z0-9]+", "-", r["title"].lower())).strip("-")
        if rid in known:
            print("  SKIPPED: a recipe with id %r is already in the library." % rid)
            continue
        meta = r["meta"]
        person = meta.get("person", "both").lower()
        entry = {
            "id": rid, "title": r["title"],
            "slot": meta.get("slot", "mirror"),
            "person": None if person in ("both", "", "none") else person,
            "servings": int(float(meta.get("servings", 1))),
            "blocks": float(meta.get("blocks", 1)),
            "source": meta.get("source", "inbox/" + r["file"]),
            "ingredients": [{"food": i["food"], "g": i["g"]} for i in r["ingredients"]],
            "steps": r["steps"], "computed": {}, "adapted": {},
        }
        clean.append(entry)
        print("  READY: %s, %d serving(s), %.1f block(s), for %s"
              % (entry["slot"], entry["servings"], entry["blocks"],
                 entry["person"] or "both"))

    print("\n" + "=" * 62)
    print("%d ready, %d blocked, %d file(s) read" % (len(clean), blocked, len(files)))
    if blocked:
        print("\nBlocked recipes need a decision, not a guess: add the missing food to\n"
              "data/foods.json (with real per-100 g numbers), or fix the amount.")
    if clean and write:
        lib["recipes"].extend(clean)
        with open(os.path.join(DATA, "recipes.json"), "w", encoding="utf-8") as fh:
            json.dump(lib, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        print("\nAppended %d recipe(s) to data/recipes.json." % len(clean))
        print("Next: python3 scripts/adapt_recipe.py   then rebuild the kitchen page.")
    elif clean:
        print("\nNothing written. Re-run with --write to add the ready ones.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

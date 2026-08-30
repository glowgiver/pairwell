"""Build hub/kitchen/index.html from kitchen.json + profiles.json + recipes.json.

The page answers the two questions actually asked in a kitchen:

  "How do I cook the base?"   — ingredients and Ninja steps
  "How much do we each get?"  — weigh the pan, get two portions and their macros

The splitter is the point. Everything else on the page is reference. All macros
come from the derived block in kitchen.json, never from hand-typed figures —
see scripts/recompute_macros.py for why that matters.
"""

import json
import os

BASE = os.path.dirname(__file__)
KITCHEN = os.path.join(BASE, "..", "data", "kitchen.json")
PROFILES = os.path.join(BASE, "..", "data", "profiles.json")
RECIPES = os.path.join(BASE, "..", "data", "recipes.json")
FOODS = os.path.join(BASE, "..", "data", "foods.json")
OUT = os.path.join(BASE, "..", "hub", "kitchen", "index.html")

# Recipes carry only ids and grams; the names live in foods.json. Ship a lookup
# of just the names — the nutrition tables are the build's business, not the page's.
_foods = json.load(open(FOODS, encoding="utf-8"))["foods"]
_recipes = json.load(open(RECIPES, encoding="utf-8"))["recipes"]

def strip_body(profiles):
    """Body composition is for the scripts, not for the pages.

    The site is public. No page needs a bodyweight to render, so none of them
    gets one — this keeps profiles.json usable by check_targets.py without
    putting anyone's weight and body fat on a URL anybody can open.
    """
    import copy
    out = copy.deepcopy(profiles)
    for person in out.get("people", {}).values():
        person.pop("body", None)
    out.pop("_bodyNote", None)
    return out

def strip_buildonly(kitchen):
    """topUps is for adapt_recipe.py, not for the browser.

    Same reasoning as shipping only foodNames: the page renders none of it,
    so it has no business being inlined into every phone that opens Kitchen.
    """
    import copy
    out = copy.deepcopy(kitchen)
    out.pop("topUps", None)
    return out



def _fine_tune_fiber():
    """The capped day-level fibre adjustment, resolved to what the page needs.

    Deliberately read from kitchen.json's dayFineTuning and NOT from topUps:
    adapt_recipe.py must never see psyllium husk, because on cost it would win
    every proposal it is offered for. A glass of water at the end of a day is a
    different question from what belongs stirred into a braise.
    """
    kit = json.load(open(KITCHEN, encoding="utf-8"))
    cands = (kit.get("dayFineTuning") or {}).get("fiber") or []
    if not cands:
        return None
    c = cands[0]
    food = _foods.get(c["food"])
    if not food or not food["per100g"]["fiberG"]:
        return None
    return {
        "name": food["name"],
        "maxG": c["maxG"],
        "note": c.get("note", ""),
        "fiberPerG": round(food["per100g"]["fiberG"] / 100.0, 4),
    }


# What a dish is mostly made of, so the picker can be scanned by eye instead of
# read. Derived from the heaviest ingredient tagged role:protein — nothing new
# is typed, and a recipe that gains a different protein reclassifies itself.
#
# This is the honest version of the audit's "dish thumbnails", not the good one.
# The good one is a photograph, and there is none to use: the recipes came from
# other people's pages and this repo is public, so their photos cannot be
# committed. A bundled photo of a dish actually cooked here would be a drop-in
# improvement over these glyphs, and would still make zero external requests.
_KIND_BY_FOOD = {
    "huehnerbrust": "poultry", "haehnchenschenkel": "poultry",
    "haehnchen_ganz": "poultry", "putenbrust": "poultry",
    "lachs": "fish", "garnelen": "fish",
    "rinderbrust": "beef", "rinderfilet": "beef", "hackfleisch": "beef",
    "magerquark": "dairy", "skyr": "dairy", "huettenkaese": "dairy",
    "ehrmann_pudding": "dairy",
    "whey": "shake",
    "eier": "egg", "ei": "egg",
}


def _base_shopping():
    """The block batch as its own lines, and the blocks that batch yields.

    Deliberately NOT matched against foods.json. The base block's raw
    components — jasmine rice, raw quinoa, dry red lentils — are not in the
    food table at all, because the block carries its own computed macros in
    kitchen.json rather than deriving them per ingredient. A first attempt at
    matching by name quietly paired raw quinoa with "Quinoa, gekocht" and dry
    lentils with "Rote Linsen, gekocht" — three times the calories per gram,
    on the wrong side of cooking — and lost the rice entirely.

    A shopping list needs a name and an amount, which these lines already are.
    """
    base = json.load(open(KITCHEN, encoding="utf-8"))["asianMacroBase"]
    return {
        "ingredients": [dict(item=i["item"], amount=i["amount"])
                        for i in base["ingredients"]],
        "blocksPerBatch": base["yield"]["blocks"],
    }


def _dish_kinds():
    out = {}
    for r in _recipes:
        best, kind = 0, "plant"
        for i in r.get("ingredients", []):
            f = _foods.get(i["food"]) or {}
            if f.get("role") != "protein":
                continue
            if i.get("g", 0) > best:
                best = i["g"]
                kind = _KIND_BY_FOOD.get(i["food"], "plant")
        out[r["id"]] = kind
    return out


data = {
    "kitchen": strip_buildonly(json.load(open(KITCHEN, encoding="utf-8"))),
    "profiles": strip_body(json.load(open(PROFILES, encoding="utf-8"))),
    "recipes": _recipes,
    "foodNames": dict((k, v["name"]) for k, v in _foods.items()),
    "dishKinds": _dish_kinds(),
    # The block is cooked from real ingredients that have to be bought. The
    # shopping list said "plus 10 Asian Base Blocks" and left you to remember
    # what that meant at the shop.
    "baseShopping": _base_shopping(),
    # Resolved here rather than in the page for the same reason foodNames exists:
    # the page gets the one number it needs, not the nutrition table it came from.
    "fineTuneFiber": _fine_tune_fiber(),
}
data_json = json.dumps(data, ensure_ascii=False)

def _digest(rel):
    """Content hash for a shared asset, so a stale HTTP cache entry cannot
    outlive a change. The service worker revalidates eventually; this closes
    the window before it does."""
    import hashlib
    p = os.path.join(BASE, "..", "hub", rel)
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:8]

ASSET_V = {"css": _digest("app.css"), "js": _digest("app.js")}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Kitchen · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css?v=__CSSV__">
<style>
  :root{ --accent:var(--food); }

  body{
    background:var(--bg);color:var(--text);
    font-family:var(--f-ui);
    -webkit-font-smoothing:antialiased;
    min-height:100dvh;max-width:600px;margin:0 auto;
    padding:
      calc(env(safe-area-inset-top) + 20px)
      calc(env(safe-area-inset-right) + 18px)
      calc(var(--bar) + 26px)
      calc(env(safe-area-inset-left) + 18px);
  }

  h1{font-size:29px;font-weight:700;letter-spacing:-.02em;margin:0 0 6px;color:var(--accent)}
  .sub{font-family:var(--f-read);font-size:15.5px;line-height:1.6;color:var(--muted);margin:0 0 20px}

  .card{
    background:var(--surface);border:1px solid var(--line);
    border-radius:16px;margin-bottom:14px;overflow:hidden;
  }
  .ch{
    display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
    padding:15px 18px 12px;border-bottom:1px solid var(--line);
  }
  .ch .k{
    font-family:var(--f-data);
    font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--accent);
  }
  .ch .meta{font-family:var(--f-data);font-size:13px;color:var(--muted2);margin-left:auto}
  .ch .title{font-size:17px;font-weight:600;width:100%;margin-top:3px;letter-spacing:-.01em}

  /* ---- the day ledger: what the person switcher is for on this page ---- */
  .ledger{padding:2px 0}
  /* The fine-tuning line sits under the ledger and only appears on a fully
     planned day. Quiet by default, amber when the gap is too big for powder. */
  .finetune{margin:8px 0 0;padding:10px 12px;border-radius:10px;font:400 13px/1.45 var(--f-read);
            background:var(--surface-2);border:1px solid var(--line);border-left:3px solid var(--food)}
  .finetune b{font-family:var(--f-data);font-variant-numeric:tabular-nums}
  .finetune.warn{background:transparent;border-style:dashed;color:var(--muted)}
  .lrow{display:grid;grid-template-columns:1fr auto;gap:2px 14px;padding:13px 18px;align-items:baseline}
  .lrow+.lrow{border-top:1px solid var(--line)}
  .lrow .lb{font-size:16px;font-weight:600;letter-spacing:-.01em}
  .lrow .ls span.tag{
    font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted2);
  }
  .lrow .lv{
    font-family:var(--f-data);font-size:16px;font-weight:600;
    font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap;
  }
  .lrow .ls{grid-column:1/-1;display:flex;gap:13px;flex-wrap:wrap;margin-top:5px}
  .lrow .ls span{font-family:var(--f-data);font-size:13px;color:var(--muted2);
    font-variant-numeric:tabular-nums}
  .lrow .ls b{color:var(--text);font-weight:600}
  .lrow.left{background:var(--surface-2)}
  .lrow.left .lb{color:var(--accent)}
  .lrow.left .lv{color:var(--accent)}
  .lrow .ls span.short b{color:var(--warn)}

  .empty{
    padding:16px 18px;font-family:var(--f-read);font-size:15px;
    line-height:1.6;color:var(--muted);
  }
  .rmac{display:flex;gap:13px;flex-wrap:wrap;padding:0 18px 14px}
  .rmac span{font-family:var(--f-data);font-size:13px;color:var(--muted2);
    font-variant-numeric:tabular-nums}
  .rmac b{color:var(--text);font-weight:600}
  .card details{
    background:transparent;border:0;border-top:1px solid var(--line);
    border-radius:0;margin:0;
  }
  .card details summary{font-size:15px;font-weight:500;color:var(--muted)}
  .rnote{
    border-top:1px solid var(--line);padding:14px 18px;
    font-family:var(--f-read);font-size:14.5px;line-height:1.6;color:var(--muted);
  }
  .rnote b{color:var(--text);font-weight:600}
  .brief{padding:4px 18px 16px}
  .brief .env{
    font-family:var(--f-data);font-size:15px;font-weight:600;color:var(--accent);
    font-variant-numeric:tabular-nums;padding:10px 0 4px;line-height:1.5;
  }
  .brief h4{
    font-family:var(--f-data);font-size:13px;font-weight:600;letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted2);margin:14px 0 6px;
  }
  .brief ul{margin:0;padding:0;list-style:none}
  .brief li{
    font-family:var(--f-read);font-size:15px;line-height:1.55;color:var(--muted);
    padding:4px 0 4px 16px;position:relative;
  }
  .brief li::before{content:"";position:absolute;left:0;top:11px;
    width:5px;height:5px;border-radius:50%;background:var(--muted2)}
  .brief p{margin:8px 0 0;font-family:var(--f-read);font-size:14.5px;
    line-height:1.6;color:var(--muted2)}
  .rnote .path{
    display:block;margin-top:7px;font-family:var(--f-data);font-size:13px;
    color:var(--accent);letter-spacing:.01em;
  }
  /* The second step is the one that gets forgotten, so it gets its own line
     rather than trailing off the end of a paragraph. */
  .rnote .then{
    display:block;margin-top:11px;padding-top:11px;
    border-top:1px solid var(--line);
  }
  .rnote .then b{display:block;margin-bottom:2px}
  .card details[open] summary{color:var(--text);border-bottom:1px solid var(--line)}

  /* ---- the splitter: the reason this page exists ---- */
  .weigh{padding:18px}
  .weigh label{
    display:block;font-family:var(--f-data);font-size:13px;
    letter-spacing:.1em;text-transform:uppercase;color:var(--muted2);margin-bottom:10px;
  }
  .weigh-row{display:flex;gap:10px;align-items:stretch}
  .weigh input{
    flex:1;min-width:0;min-height:var(--tap);
    background:var(--surface-2);border:1px solid var(--line-2,var(--line));
    border-radius:12px;padding:0 16px;
    font-family:var(--f-data);font-size:22px;font-weight:600;
    color:var(--text);font-variant-numeric:tabular-nums;
  }
  .weigh input:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
  .weigh .unit{
    display:flex;align-items:center;padding:0 14px;border-radius:12px;
    background:var(--surface-2);border:1px solid var(--line);
    font-family:var(--f-data);font-size:15px;color:var(--muted2);
  }
  .hint{font-family:var(--f-read);font-size:14.5px;line-height:1.55;color:var(--muted2);margin:11px 0 0}

  .split{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line);
    border-top:1px solid var(--line)}
  .half{background:var(--surface);padding:16px 18px}
  .half .who{
    font-family:var(--f-data);font-size:13px;letter-spacing:.1em;text-transform:uppercase;
    display:flex;align-items:center;gap:7px;margin-bottom:9px;
  }
  .half .dot{width:8px;height:8px;border-radius:50%;background:var(--who)}
  .half.p .who{color:var(--philipp)} .half.p{--who:var(--philipp)}
  .half.e .who{color:var(--eunice)}  .half.e{--who:var(--eunice)}
  .half .g{
    font-family:var(--f-data);font-size:27px;font-weight:700;
    font-variant-numeric:tabular-nums;letter-spacing:-.02em;line-height:1;
  }
  .half .kcal{font-family:var(--f-data);font-size:15px;color:var(--muted);margin-top:6px;
    font-variant-numeric:tabular-nums}
  .macros{display:flex;gap:12px;flex-wrap:wrap;margin-top:9px}
  .macros span{
    font-family:var(--f-data);font-size:13px;color:var(--muted2);
    font-variant-numeric:tabular-nums;
  }
  .macros b{color:var(--text);font-weight:600}

  .n{font-family:var(--f-data);font-size:13px;font-weight:600;color:var(--muted2);
    font-variant-numeric:tabular-nums}
  .t{font-size:16px;font-weight:600;line-height:1.4}
  ol.steps .t{font-weight:500}
  .amt{font-family:var(--f-data);font-size:15px;color:var(--accent);
    font-variant-numeric:tabular-nums;text-align:right}
  ul.ing li{grid-template-columns:1fr auto}

  .flag{
    border:1px solid var(--line);border-left:3px solid var(--accent);
    background:var(--surface-2);border-radius:0 12px 12px 0;
    padding:14px 17px;margin-bottom:14px;
  }
  .flag .ft{
    font-family:var(--f-data);font-size:13px;font-weight:600;letter-spacing:.09em;
    text-transform:uppercase;color:var(--accent);margin-bottom:6px;
  }
  .flag p{margin:0;font-family:var(--f-read);font-size:15px;line-height:1.6;color:var(--muted)}
  .flag.warn{border-left-color:var(--warn);background:var(--warn-fill)}
  .flag.warn .ft{color:var(--warn)}

  details{
    background:var(--surface);border:1px solid var(--line);
    border-radius:14px;margin-bottom:12px;overflow:hidden;
  }
  details summary{
    min-height:var(--tap);display:flex;align-items:center;gap:9px;
    padding:13px 18px;cursor:pointer;font-size:15px;font-weight:600;
    list-style:none;color:var(--text);
  }
  details summary::-webkit-details-marker{display:none}
  details summary::after{
    content:"";margin-left:auto;width:8px;height:8px;flex:none;
    border-right:2px solid var(--muted2);border-bottom:2px solid var(--muted2);
    transform:rotate(45deg);transition:transform .18s ease;
  }
  details[open] summary::after{transform:rotate(-135deg)}
  details summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
  .dl{padding:2px 18px 16px}
  .dl div{padding:9px 0;border-top:1px solid var(--line)}
  .dl .dk{font-family:var(--f-data);font-size:13px;letter-spacing:.07em;
    text-transform:uppercase;color:var(--muted2);margin-bottom:3px}
  .dl .dv{font-family:var(--f-read);font-size:15px;line-height:1.55;color:var(--muted)}
  .dl .dv strong{color:var(--text)}

  /* ---- the planner: pick a dish, get the other one and the shopping list ---- */
  /* min-width:0 matters here: a grid item defaults to min-width:auto, so a
     long unbroken dish title (or a wrapped meta line) can hold the whole
     track open past the viewport instead of wrapping inside it — that is
     what was cutting text off on a phone. Stacking to one column below
     480px sidesteps it entirely once titles get long, columns get narrow. */
  .planrow{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
  .planslot{background:var(--surface);padding:14px 16px;min-width:0}
  .planslot-snack{border-top:1px solid var(--line);padding:14px 16px}
  .planslot-snack .ps-list{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  @media (max-width:480px){
    .planrow{grid-template-columns:1fr}
    .planslot-snack .ps-list{grid-template-columns:1fr}
  }
  .ps-label{
    font-family:var(--f-data);font-size:13px;letter-spacing:.1em;text-transform:uppercase;
    color:var(--muted2);margin-bottom:10px;
  }
  .ps-hint{text-transform:none;letter-spacing:0;font-family:var(--f-read);color:var(--muted2)}
  .ps-portion + .ps-portion{margin-top:18px;padding-top:16px;border-top:1px solid var(--line)}
  .ps-tier{margin:14px 0 6px;font:600 12px/1 var(--f-ui);letter-spacing:.06em;
           text-transform:uppercase;color:var(--muted)}
  .ps-rest{margin-top:14px;border-top:1px solid var(--line)}
  .ps-rest>summary{cursor:pointer;font:400 13px/1.4 var(--f-read);color:var(--muted);
                   padding:12px 0;min-height:var(--tap);display:flex;align-items:center}
  .ps-note{
    margin:0 0 12px;font-family:var(--f-read);font-size:14px;line-height:1.55;
    color:var(--muted2);
  }
  .ps-list{display:flex;flex-direction:column;gap:8px;min-width:0}
  .dishpick{
    display:block;width:100%;text-align:left;min-height:var(--tap);min-width:0;
    background:var(--surface-2);border:1px solid var(--line-2,var(--line));
    border-radius:12px;padding:9px 12px;cursor:pointer;position:relative;
  }
  .dishpick:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
  .dishpick.picked{border-color:var(--accent);background:var(--accent);color:var(--bg)}
  .dp-title{
    display:block;font-size:15px;font-weight:600;line-height:1.35;
    overflow-wrap:break-word;word-break:break-word;
  }
  .dp-meta{
    display:block;margin-top:3px;font-family:var(--f-data);font-size:12.5px;
    color:var(--muted2);font-variant-numeric:tabular-nums;line-height:1.5;
    overflow-wrap:break-word;
  }
  .dishpick.picked .dp-meta{color:var(--bg);opacity:.82}
  .dp-pair{
    display:block;margin-top:6px;padding-top:6px;border-top:1px solid var(--line);
    font-family:var(--f-data);font-size:12.5px;line-height:1.5;
    font-variant-numeric:tabular-nums;color:var(--muted2);overflow-wrap:break-word;
  }
  .dp-pair.ok{color:var(--accent)}
  .dp-pair.warn{color:var(--warn)}
  /* A pair that is one spoon of husk away is not a failure — red said "error"
     for something that works. Reserve --warn for actually being over budget;
     the pairs that genuinely cannot close no longer print a line at all,
     because they are folded into the disclosure. */
  .dp-pair.husk{color:var(--muted)}
  .dp-badge{
    display:inline-block;margin-top:6px;font-family:var(--f-data);font-size:11.5px;
    font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--accent);
  }
  .ps-change{
    margin-top:10px;min-height:var(--tap);background:none;border:1px solid var(--line);
    border-radius:10px;padding:0 16px;font-size:13px;color:var(--muted);cursor:pointer;
  }

  /* ---- shopping list ticks ------------------------------------------
     The whole row is the button. In a shop the phone is held one-handed
     and the other hand is full. */
  ul.ing li.shop{padding:0;display:block}
  .shoptick{
    width:100%;min-height:var(--tap);
    display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:12px;
    padding:8px 18px;background:none;border:0;cursor:pointer;
    font-family:inherit;font-size:15px;color:var(--text);text-align:left;
  }
  .shoptick .box{
    position:relative;
    width:20px;height:20px;border:1.5px solid var(--muted2);border-radius:5px;
  }
  .shoptick .amt{
    font-family:var(--f-data);font-size:14px;color:var(--accent);
    font-variant-numeric:tabular-nums;
  }
  .shoptick[aria-pressed="true"] .box{
    background:var(--accent);border-color:var(--accent);
  }
  /* The tick is drawn in the page ground — the one ink a filled accent is
     built to carry, in either theme. */
  .shoptick[aria-pressed="true"] .box::after{
    content:"";position:absolute;left:6px;top:2.5px;
    width:4px;height:9px;
    border:solid var(--bg);border-width:0 2px 2px 0;
    transform:rotate(45deg);
  }
  li.shop.got .shoptick .t{text-decoration:line-through;color:var(--muted2)}
  li.shop.got .shoptick .amt{color:var(--muted2)}
  .shoptick:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}

  /* ---- the three jobs ------------------------------------------------ */
  .ktabs{display:flex;gap:6px;margin-bottom:14px}
  .ktab{
    flex:1;min-height:var(--tap);padding:8px 4px;border-radius:12px;
    border:1px solid var(--line);background:var(--surface);
    font-family:inherit;font-size:15px;font-weight:600;color:var(--muted);
    cursor:pointer;
  }
  .ktab span{
    display:block;font-family:var(--f-data);font-size:12.5px;font-weight:400;
    color:var(--muted2);margin-top:2px;
  }
  .ktab[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
  /* Vary the weight on a filled accent, never the ink. */
  .ktab[aria-selected="true"] span{color:inherit;font-weight:400;opacity:.85}
  .ktab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  /* ---- a dish's own scale reading ------------------------------------- */
  .dishsplit{padding:14px 18px;border-top:1px solid var(--line);background:var(--surface-2)}
  .dishsplit label{
    display:block;font-family:var(--f-data);font-size:12.5px;letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted2);margin-bottom:8px;
  }
  .dishsplit .weigh-row{display:flex;align-items:center;gap:10px}
  .dishsplit input{
    flex:1;min-width:0;min-height:var(--tap);padding:0 14px;
    border:1px solid var(--line);border-radius:11px;background:var(--surface);
    color:var(--text);font-family:var(--f-data);font-size:19px;font-weight:600;
    font-variant-numeric:tabular-nums;
  }
  .dishsplit input:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
  .dishsplit .unit{font-family:var(--f-data);font-size:14px;color:var(--muted2)}
  .serveout{margin-top:11px;font-size:16px;color:var(--text)}
  .serveout b{font-family:var(--f-data);font-size:20px;font-weight:700}
  .serveout.muted{
    font-family:var(--f-read);font-size:14.5px;color:var(--muted);line-height:1.55;
  }
  .perserve{
    margin-top:12px;padding-top:11px;border-top:1px solid var(--line);
    display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
  }
  .perserve .ps-k{
    font-family:var(--f-data);font-size:12.5px;letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted2);
  }
  .perserve .ps-v{font-family:var(--f-data);font-size:17px;font-weight:700;color:var(--text)}
  .perserve .ps-m{display:flex;gap:12px;margin-left:auto}
  .perserve .ps-m span{font-family:var(--f-data);font-size:13.5px;color:var(--muted)}
  .perserve .ps-m b{color:var(--text);font-weight:700}

  .dp-top{display:flex;align-items:flex-start;gap:9px}
  .dp-icon{
    width:22px;height:22px;flex:none;margin-top:1px;
    stroke:currentColor;fill:none;stroke-width:1.6;
    stroke-linecap:round;stroke-linejoin:round;opacity:.75;
  }
  .dishpick.picked .dp-icon{opacity:.9}
  .dp-cuisine{
    display:inline-block;margin-right:8px;
    font-family:var(--f-data);font-size:12px;letter-spacing:.07em;
    text-transform:uppercase;color:var(--accent);font-weight:600;
  }
  .dishpick.picked .dp-cuisine{color:inherit;opacity:.85}

  /* Inside the reference card the rows are already contained, so they drop
     their own borders and radii and read as one list. */
  .refcard > details{
    background:none;border:0;border-top:1px solid var(--line);
    border-radius:0;margin:0;
  }
  .refcard > details:first-of-type{border-top:0}

  /* ---- what goes in the bowl ----------------------------------------- */
  .blockdial{padding:0;border-top:1px solid var(--line);background:var(--surface-2)}
  .bowl{padding:13px 18px;border-bottom:1px solid var(--line)}
  .bowl-k{
    font-family:var(--f-data);font-size:12px;letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted2);margin-bottom:4px;
  }
  .bowl-v{font-size:16px;line-height:1.45;color:var(--text)}
  .bowl-v b{font-family:var(--f-data);font-weight:700}
  .bowl-v i{color:var(--muted2);font-style:italic;font-size:14px}
  .bowl-v .plus{color:var(--muted2)}
  .bowl-v .g{font-family:var(--f-data);font-size:13px;color:var(--muted2)}
  .bowl-m{
    margin-top:4px;font-family:var(--f-data);font-size:13px;color:var(--muted);
    font-variant-numeric:tabular-nums;
  }

  .dp-carb{
    display:inline-block;margin-right:8px;
    font-family:var(--f-data);font-size:12px;letter-spacing:.06em;
    color:var(--muted2);
  }
  .dp-carb.own{color:var(--text);font-weight:600}
  .dishpick.picked .dp-carb{color:inherit;opacity:.8}

  .bd-note{
    padding:0 18px 14px;font-family:var(--f-read);font-size:14.5px;
    line-height:1.55;color:var(--muted);
  }

  .bd-head{
    display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
    padding:12px 18px 6px;font-size:14px;font-weight:600;color:var(--text);
  }
  .bd-head span{font-family:var(--f-data);font-size:12.5px;color:var(--muted2);margin-left:auto}
  /* Name and stepper on one line, the consequence underneath. Three columns
     on a 375px screen crushed the numbers into four wrapped lines. */
  .bd-row{
    display:grid;grid-template-columns:1fr auto;align-items:center;
    gap:6px 12px;padding:8px 18px 12px;
  }
  .bd-who{display:flex;align-items:center;gap:7px;font-size:15px;font-weight:600}
  .bd-who .dot{width:8px;height:8px;border-radius:50%;background:var(--who)}
  .bd-step{display:flex;align-items:center;gap:2px}
  .bd-b{
    width:var(--tap);height:var(--tap);border:1px solid var(--line);
    background:var(--surface);color:var(--text);border-radius:11px;
    font-family:inherit;font-size:20px;line-height:1;cursor:pointer;
  }
  .bd-b:disabled{opacity:.35;cursor:default}
  .bd-b:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .bd-n{
    min-width:2.4em;text-align:center;font-family:var(--f-data);
    font-size:18px;font-weight:700;font-variant-numeric:tabular-nums;
  }
  .bd-out{
    grid-column:1/3;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
    font-family:var(--f-data);font-size:12.5px;color:var(--muted2);
    font-variant-numeric:tabular-nums;
  }
  .bd-out b{font-size:17px;color:var(--text)}
  .bd-out .bd-delta{margin-left:auto}
  .bd-delta{color:var(--warn)}
  .bd-delta.ok{color:var(--muted2)}

  /* The library, kept reachable but no longer three thousand pixels tall. */
  details.library > summary{font-weight:600}

  /* A picked dish, or the base block: slot, name, size — enough to know what
     it is without opening it. */
  /* Named areas so the disclosure chevron keeps its own column instead of
     wrapping onto a third row once the title runs long. */
  .cookcard > details > summary{
    display:grid;
    grid-template-columns:auto auto 1fr auto;
    grid-template-areas:"k icon title chev" "k icon meta chev";
    align-items:center;gap:1px 10px;padding:14px 18px;
  }
  .cookcard > details > summary .dp-icon{grid-area:icon;margin:0;align-self:center}
  .cookcard > details > summary .k{
    grid-area:k;align-self:center;
    font-family:var(--f-data);font-size:12px;letter-spacing:.09em;
    text-transform:uppercase;color:var(--accent);font-weight:600;
  }
  .cookcard > details > summary .title{
    grid-area:title;font-size:16px;font-weight:600;color:var(--text);
  }
  .cookcard > details > summary .meta{
    grid-area:meta;justify-self:start;
    font-family:var(--f-data);font-size:13px;color:var(--muted2);
  }
  .cookcard > details > summary::after{grid-area:chev;margin-left:0;align-self:center}

  @media (prefers-reduced-motion:reduce){ details summary::after{transition:none} }
</style>
</head>
<body>

<div class="pw-bar">
  <a class="pw-back" href="../"><svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg> Hub</a>
  <div id="switcher"></div>
</div>

<h1>Kitchen</h1>
<p class="sub" id="sub"></p>
<div id="stage"></div>

<script src="../app.js?v=__JSV__"></script>
<script>
const D = __DATA__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}
function n1(v){ return (Math.round(v*10)/10).toFixed(1).replace(/\\.0$/,""); }
function n0(v){ return Math.round(v); }
/* mirrorMeals.fatG is a range like "0-14", deliberately. Print it, do not round it.
   A range that starts at 0 is a ceiling wearing a range's clothes; say so, because
   "0-14 g" invites you to hunt for a lower bound that does not exist. */
function g(v){
  if(isFinite(v)) return n0(v);
  var m = String(v).match(/^0\\s*-\\s*(.+)$/);
  return m ? "\u2264" + m[1] : String(v);
}

/* Every figure in the ledger is derived here rather than read from the
   pre-computed budget fields in profiles.json. Those fields agree today; the
   point is that they cannot silently stop agreeing. */
function mealsOfDay(who){
  var prof = D.profiles.people[who];
  var t = prof.dailyTargets;
  var mm = D.profiles.mirrorMeals;
  var rows = [];

  if(prof.fixedBreakfast){
    var b = prof.fixedBreakfast;
    rows.push({ label:"Breakfast", tag:"fixed", kcal:b.calories, p:b.proteinG,
                fib:b.fiberG, fat:b.fatG, ing:b.ingredients });
  }
  /* Once a dish is actually picked in the planner below, the ledger uses its
     real computed macros instead of the abstract mirror target — Baked Feta
     Salmon really does carry 1.2 g fibre, not 14, and "left for snacks"
     should know that, not just the idealised number. */
  ["lunch","dinner"].forEach(function(k){
    var picked = PLAN[k] ? recipeById(PLAN[k]) : null;
    var c = picked ? picked.computed : mm[k];
    rows.push({ label:k.charAt(0).toUpperCase()+k.slice(1), tag: picked ? "picked" : "mirror",
                kcal:c.calories, p:c.proteinG, fib:c.fiberG, fat:c.fatG });
  });
  pickedSnacks(who).forEach(function(id){
    var c = recipeById(id).computed;
    rows.push({ label:recipeById(id).title, tag:"snack", kcal:c.calories, p:c.proteinG,
                fib:c.fiberG, fat:c.fatG });
  });

  var used = rows.reduce(function(a,r){
    a.kcal += r.kcal; a.p += r.p; a.fib += r.fib || 0;
    return a;
  }, {kcal:0, p:0, fib:0});

  rows.push({
    label: prof.fixedBreakfast ? "Left for snacks" : "Left for breakfast + snacks",
    tag: "open", left: true,
    kcal: t.calories - used.kcal,
    p:    t.proteinG - used.p,
    fib:  t.fiberG   - used.fib
  });
  return rows;
}

/* What the rest of the plate has to deliver once the carb base is on it.
   This is recipeChecks.proteinCheck made arithmetic instead of advisory. */
function mealRemainder(){
  var blocks = base.blockRules.standardLeanDish;
  var pb = comp.perBlock;
  var m = D.profiles.mirrorMeals.lunch;
  /* Fat has no floor since 2026-08-30, so the blocks can already exceed what the
     meal demands. Clamped at zero — a negative need would credit those calories
     back and make the feasibility floor look lower than it is. */
  var fatLo = parseFloat(String(m.fatG).split("-")[0]);
  return {
    blocks: blocks,
    from:  { kcal:pb.calories*blocks, p:pb.proteinG*blocks,
             fib:pb.fiberG*blocks, fat:pb.fatG*blocks },
    need:  { kcal:m.calories - pb.calories*blocks,
             p:  m.proteinG - pb.proteinG*blocks,
             fib:m.fiberG   - pb.fiberG*blocks,
             fat:Math.max(0, fatLo - pb.fatG*blocks),
             fatMax:parseFloat(String(m.fatG).split("-").pop()) - pb.fatG*blocks }
  };
}

/* Can the target be hit at all? Price the macros it asks for at their own
   energy content. If that floor is above the calories left, no choice of
   ingredient rescues it — the target contradicts itself. */
function feasibility(){
  var r = mealRemainder();
  var f = D.kitchen.energyFactors;
  if(!f) return null;
  var floor = r.need.p*f.proteinG + r.need.fat*f.fatG + r.need.fib*f.fiberG;
  return { floor:floor, have:r.need.kcal, over:floor - r.need.kcal };
}

var base = D.kitchen.asianMacroBase;
var comp = base.computed;
var per100 = comp.per100gCooked;

/* Last weight typed, so you do not retype it while the pan is still hot. */
function loadWeight(){
  try{ var v = parseFloat(localStorage.getItem("hub.kitchen.weight")); if(v>0) return v; }catch(e){}
  return comp.gramsPerBlock * base.yield.blocks;   // a full batch
}
function saveWeight(v){
  try{ localStorage.setItem("hub.kitchen.weight", String(v)); }catch(e){}
}

var weight = loadWeight();

function macrosFor(grams){
  var f = grams/100;
  return {
    kcal: per100.calories*f, p: per100.proteinG*f,
    c: per100.carbsG*f, fib: per100.fiberG*f, fat: per100.fatG*f
  };
}

function splitHTML(){
  var each = weight/2;
  var m = macrosFor(each);
  function half(cls,who){
    return '<div class="half ' + cls + '">' +
      '<div class="who"><span class="dot"></span>' + esc(who) + '</div>' +
      '<div class="g">' + n0(each) + ' g</div>' +
      '<div class="kcal">' + n0(m.kcal) + ' kcal</div>' +
      '<div class="macros">' +
        '<span>P <b>' + n1(m.p) + '</b></span>' +
        '<span>C <b>' + n1(m.c) + '</b></span>' +
        '<span>Fib <b>' + n1(m.fib) + '</b></span>' +
        '<span>F <b>' + n1(m.fat) + '</b></span>' +
      '</div></div>';
  }
  return '<div class="split">' + half("p","Philipp") + half("e","Eunice") + '</div>';
}

function ledgerHTML(who){
  var prof = D.profiles.people[who];
  var rows = mealsOfDay(who);

  var body = rows.map(function(r){
    var short = r.left && r.fib != null && r.fib <= 2 ? " short" : "";
    return '<div class="lrow' + (r.left ? ' left' : '') + '">' +
      '<div class="lb">' + esc(r.label) + '</div>' +
      '<div class="lv">' + n0(r.kcal) + ' kcal</div>' +
      '<div class="ls"><span class="tag">' + esc(r.tag) + '</span>' +
        '<span>P <b>' + g(r.p) + ' g</b></span>' +
        (r.fib == null ? '' : '<span class="' + short.trim() + '">Fib <b>' +
                              g(r.fib) + ' g</b></span>') +
        (r.fat == null ? '' : '<span>F <b>' + g(r.fat) + ' g</b></span>') +
      '</div></div>';
  }).join("");

  var t = prof.dailyTargets;
  var card = '<div class="card"><div class="ch"><span class="k">' +
    esc(PW.PEOPLE[who].name) + '\u2019s day</span>' +
    '<span class="meta">' + n0(t.calories) + ' kcal &middot; ' + n0(t.proteinG) + ' g P</span>' +
    '</div><div class="ledger">' + body + '</div></div>';

  /* The last few grams. Only once lunch, dinner AND a snack are all picked is
     the day actually specified — before that "left over" is just budget, not a
     shortfall. Capped hard: psyllium is fine for a rounding error and wrong as
     a replacement for a dish, and the cap is what keeps that line honest. */
  /* The last few grams. Only once lunch, dinner AND a snack are all picked is
     the day actually specified — before that "left over" is budget, not a
     shortfall. Capped hard: psyllium is fine for a rounding error and wrong as
     a replacement for a dish, and the cap is what keeps that line honest. */
  var ft = D.fineTuneFiber;
  var snacksDone = pickedSnacks(who).length === snackSlots(who);
  if(ft && PLAN.lunch && PLAN.dinner && snacksDone){
    var open = rows[rows.length - 1];
    if(open.left && open.fib > 0.05){
      var needG = open.fib / ft.fiberPerG;
      if(needG <= ft.maxG){
        card += '<div class="finetune"><b>' + g(needG) + ' g ' + esc(ft.name) + '</b> ' +
                'schlie\u00dfen die letzten ' + g(open.fib) + ' g Ballaststoffe \u2014 ' +
                esc(ft.note) + '.</div>';
      } else {
        card += '<div class="finetune warn">' + g(open.fib) + ' g Ballaststoffe fehlen \u2014 ' +
                'das w\u00e4ren ' + g(needG) + ' g ' + esc(ft.name) + ', mehr als die ' +
                ft.maxG + ' g, die hier erlaubt sind. Die L\u00fccke geh\u00f6rt ins Gericht, ' +
                'nicht ins Pulver.</div>';
      }
    }
  }

  /* The ingredients only exist for whoever has a fixed breakfast. */
  if(prof.fixedBreakfast){
    card += '<details><summary>' + esc(PW.PEOPLE[who].name) +
      '\u2019s breakfast, as built</summary><div class="dl">' +
      prof.fixedBreakfast.ingredients.map(function(i){
        return '<div><div class="dk">' + esc(i.item) + '</div>' +
               '<div class="dv"><strong>' + esc(i.amount) + '</strong></div></div>';
      }).join("") + '</div></details>';
  }
  return card;
}

function mealHTML(){
  var r = mealRemainder();
  var m = D.profiles.mirrorMeals.lunch;
  return '<div class="card"><div class="ch"><span class="k">One mirror meal</span>' +
    '<span class="meta">' + n0(m.calories) + ' kcal target</span>' +
    '<span class="title">What the plate still needs</span></div>' +
    '<div class="ledger">' +
      '<div class="lrow"><div class="lb">' + n1(r.blocks) + ' Asian Base block' +
        (r.blocks === 1 ? '' : 's') + '</div>' +
        '<div class="lv">' + n0(r.from.kcal) + ' kcal</div>' +
        '<div class="ls"><span class="tag">carb base</span>' +
        '<span>P <b>' + n1(r.from.p) + ' g</b></span>' +
        '<span>Fib <b>' + n1(r.from.fib) + ' g</b></span>' +
        '<span>F <b>' + n1(r.from.fat) + ' g</b></span></div></div>' +
      '<div class="lrow left"><div class="lb">Protein source + veg</div>' +
        '<div class="lv">' + n0(r.need.kcal) + ' kcal</div>' +
        '<div class="ls"><span class="tag">the rest</span>' +
        '<span>P <b>' + n1(r.need.p) + ' g</b></span>' +
        '<span>Fib <b>' + n1(r.need.fib) + ' g</b></span>' +
        '<span>F <b>' + (r.need.fat > 0 ? n1(r.need.fat)
                          : "\u2264" + n1(r.need.fatMax)) + ' g</b></span></div></div>' +
    '</div></div>' + feasibilityHTML();
}

function feasibilityHTML(){
  var f = feasibility();
  if(!f || f.over <= 0) return "";
  return '<div class="flag warn"><div class="ft">This target cannot be cooked</div><p>' +
    'Those macros are worth ' + n0(f.floor) + ' kcal on their own \u2014 protein at 4, fat at 9, ' +
    'fibre at 2 kcal per gram \u2014 but only ' + n0(f.have) + ' kcal are left for them. ' +
    'That is ' + n0(f.over) + ' kcal over before any digestible carbohydrate comes along for ' +
    'the ride, so no ingredient choice fixes it. Either the fibre per meal comes down or the ' +
    'meal gets bigger.' +
    '</p></div>';
}

/* Recipes whose `person` is null belong to both — that is what a mirror meal is. */
function recipesFor(who){
  return (D.recipes || []).filter(function(r){
    return !r.person || r.person === who;
  });
}

/* The library grows by dropping files in a folder, and the folder is in iCloud,
   so it is reachable from the phone you are holding. Say so on the page — this
   is the one thing about the kitchen module that is not self-evident. */
function addNote(){
  return '<div class="rnote">More dishes go in the <b>inbox</b> folder \u2014 one per ' +
    'file. The ingredients and amounts as you found them, or just a photo of them. ' +
    'Do not adjust anything to fit; that is the job of the next step.' +
    '<span class="path">Files \u203a iCloud Drive \u203a Pairwell \u203a inbox</span>' +
    '<span class="then"><b>Then ask Claude Code to read the inbox.</b>' +
    'Nothing happens on its own \u2014 the files sit there until someone runs it. ' +
    'It works out the grams, and says what to add if a dish comes up short.</span></div>';
}

/* What to hunt for. The envelope is derived from the same two files the rest of
   the page uses, so it cannot quietly disagree with the target it describes. */
function lookForHTML(){
  var r = mealRemainder();
  var fat = String(D.profiles.mirrorMeals.lunch.fatG).split("-");
  var fatLo = Math.max(0, parseFloat(fat[0]) - comp.perBlock.fatG * r.blocks);
  var fatHi = parseFloat(fat[fat.length - 1]) - comp.perBlock.fatG * r.blocks;
  /* A floor of zero is not a range to hunt inside, it is a ceiling to stay under. */
  var fatText = fatLo > 0 ? n0(fatLo) + '–' + n0(fatHi) + ' g fat'
                          : 'up to ' + n0(fatHi) + ' g fat';

  function list(items){
    return '<ul>' + items.map(function(t){ return '<li>' + t + '</li>'; }).join("") + '</ul>';
  }

  return '<details><summary>What to look for</summary><div class="brief">' +
    '<div class="env">' + n0(r.need.kcal) + ' kcal · ' + n0(r.need.p) + ' g protein · ' +
      n0(r.need.fib) + ' g fibre · ' + fatText + '</div>' +
    '<p>Per serving, the dish on its own — ' + n1(r.blocks) + ' Base block is already ' +
      'going on the plate beside it, so the recipe should bring no rice, noodles or potato ' +
      'of its own.</p>' +

    '<h4>The shape that fits</h4>' +
    list(['~100–150 g lean protein',
          '~100 g cooked legume — fibre that fits in a box',
          '~200 g quick greens or mushrooms — volume, cheap in calories',
          'an aromatic sauce with almost no fat']) +
    '<p>Never one fibre source alone: ' + n0(r.need.fib) + ' g of it from lentils costs about ' +
      '180 kcal, close to half the budget, and the same from spinach is over half a kilo of ' +
      'spinach. ' +
      'The legume and the greens also carry around 15 g of protein between them, which is ' +
      'why the meat portion is smaller than it looks.</p>' +

    '<h4>Works</h4>' +
    list(['Cod, prawns, turkey, chicken breast, pork fillet',
          'Braises and one-pot stews — Taiwanese, Vietnamese, Japanese',
          'Stir-fries heavy on vegetables, with a weighable protein portion',
          'Sauce on stock, soy, vinegar, mustard, tomato or quark']) +

    '<h4>Too rich to fit</h4>' +
    list(['Coconut milk at full fat, cream, cheese sauce, peanut or satay — the light tin is fine, 40–80 g of it fits',
          'Deep-fried, battered, breaded',
          'Eggs or tempeh as the only protein — neither reaches 40 g inside the fat ceiling',
          'Salads that reach their fibre through sheer volume',
          'Protein minced into a mixture, so no portion can be weighed']) +

    '<h4>What to write down</h4>' +
    '<p>The ingredients in grams, and the method. Skip the nutrition panel — every ' +
      'figure here is worked out from the ingredients, so a number copied off a website ' +
      'is at best ignored and at worst believed by mistake.</p>' +
    '</div></details>';
}

/* ---- the planner: lunch and dinner target the SAME macros (mirrorMeals.lunch
   covers both), so any two ready mirror dishes already "fit" on their own.
   What this adds is honesty about real dishes that fall short (Pho Bo's fibre
   gap, say) by ranking the other slot's candidates on how well the PAIR closes
   the full day, not just how each dish does alone. ---- */
function loadPlan(){
  var empty = {lunch:null, dinner:null, snacks:[]};
  try{
    var v = JSON.parse(localStorage.getItem("hub.kitchen.plan") || "{}");
    /* Migration: the plan used to hold one snack for everybody, which quietly
       understated a two-portion day by a portion. */
    var snacks = Array.isArray(v.snacks) ? v.snacks.slice() : (v.snack ? [v.snack] : []);
    return { lunch: v.lunch || null, dinner: v.dinner || null, snacks: snacks };
  }catch(e){ return empty; }
}

/* How many portions of the afternoon bowl this person eats. Data, not a guess:
   the two of them scoop from one tub and he takes twice what she does. */
function snackSlots(who){
  var n = D.profiles.people[who].afternoonPortions;
  return (typeof n === "number" && n > 0) ? n : 1;
}
function pickedSnacks(who){
  return PLAN.snacks.slice(0, snackSlots(who))
    .filter(function(id){ return id && recipeById(id); });
}
/* ---- how many base blocks each of them puts on the plate ---------------
   The dish is fitted to the plate target MINUS one standard block, so dish
   plus one block lands on the target. The count is a dial rather than a
   property of the recipe, because their days are different sizes: 1900 kcal
   against 1580. Taking fewer than the baseline leaves protein and fibre a
   little short; taking more only adds. */
function blockCount(who){
  try{
    var v = parseFloat(localStorage.getItem("hub.kitchen.blocks." + PW.PEOPLE[who].code));
    if(v >= 0 && v <= 4) return v;
  }catch(e){}
  return baselineBlocks();
}
function setBlockCount(who, v){
  try{ localStorage.setItem("hub.kitchen.blocks." + PW.PEOPLE[who].code, String(v)); }catch(e){}
}
function baselineBlocks(){
  var b = D.kitchen.asianMacroBase.blockRules.standardLeanDish;
  return typeof b === "number" ? b : 1;
}
function perBlock(){ return D.kitchen.asianMacroBase.computed.perBlock; }

/* Not every dish is eaten on a block. Pho arrives with rice noodles and the
   quinoa version arrives with quinoa: those dishes ARE the whole plate, and
   putting a rice block beside them would be carb on carb. */
function takesBlocks(r){
  return r.slot === "mirror" && r.carb !== "own";
}
function blocksFor(r, who){ return takesBlocks(r) ? blockCount(who) : 0; }

/* A plate = one serving of the dish + n blocks. */
function plateFor(r, n){
  var c = r.computed || {}, b = perBlock();
  return {
    kcal: (c.calories || 0) + b.calories * n,
    p:    (c.proteinG || 0) + b.proteinG * n,
    fib:  (c.fiberG   || 0) + b.fiberG   * n,
    fat:  (c.fatG     || 0) + b.fatG     * n
  };
}

/* What actually goes in the bowl, in grams, for one person. The page could
   already derive this and never said it in one place: the dish grams sat in
   the splitter and the block count sat in the dial. */
function bowlLineHTML(r, who){
  var n = blocksFor(r, who);
  var w = loadDishWeight(r.id);
  var gpb = D.kitchen.asianMacroBase.computed.gramsPerBlock;
  var dishG = w ? w / r.servings : null;
  var pl = plateFor(r, n);
  return '<div class="bowl">' +
    '<div class="bowl-k">' + esc(PW.PEOPLE[who].name) + '\u2019s bowl</div>' +
    '<div class="bowl-v">' +
      (dishG ? '<b>' + n0(dishG) + ' g</b> ' + esc(r.title) : esc(r.title) + ' <i>(weigh the batch)</i>') +
      (n > 0
        ? ' <span class="plus">+</span> <b>' + n1(n) + '</b> base block' +
          (n === 1 ? '' : 's') + ' <span class="g">(' + n0(gpb * n) + ' g)</span>'
        : (r.carb === "own"
            ? ' <span class="g">\u2014 no block, it brings its own carb</span>'
            : '')) +
    '</div>' +
    '<div class="bowl-m">' + n0(pl.kcal) + ' kcal &middot; P ' + n1(pl.p) +
      ' &middot; Fib ' + n1(pl.fib) + ' &middot; F ' + n1(pl.fat) + '</div>' +
  '</div>';
}

function blockDialHTML(r){
  var target = D.profiles.mirrorMeals.lunch;
  /* Own-carb dishes still show both bowls — they just have no dial, because
     there is nothing to turn. */
  if(!takesBlocks(r)){
    return '<div class="blockdial">' +
      PW.ORDER.map(function(w){ return bowlLineHTML(r, w); }).join("") +
      '<div class="bd-note">Eaten as it is. The carb is already in the dish, so ' +
      'no Asian Macro Block goes beside it.</div></div>';
  }
  var rows = PW.ORDER.map(function(who){
    var n = blockCount(who);
    var pl = plateFor(r, n);
    var over = pl.kcal - target.calories;
    return '<div class="bd-row" style="--who:' + PW.PEOPLE[who].color + '">' +
      '<div class="bd-who"><span class="dot"></span>' + esc(PW.PEOPLE[who].name) + '</div>' +
      '<div class="bd-step">' +
        '<button type="button" class="bd-b" data-blk="' + who + '" data-d="-0.5"' +
          (n <= 0 ? ' disabled' : '') + ' aria-label="Fewer blocks">&minus;</button>' +
        '<span class="bd-n">' + n1(n) + '</span>' +
        '<button type="button" class="bd-b" data-blk="' + who + '" data-d="0.5"' +
          (n >= 4 ? ' disabled' : '') + ' aria-label="More blocks">+</button>' +
      '</div>' +
      '<div class="bd-out"><b>' + n0(pl.kcal) + ' kcal</b>' +
        '<span>P ' + n1(pl.p) + ' &middot; Fib ' + n1(pl.fib) + ' &middot; F ' + n1(pl.fat) + '</span>' +
        '<span class="bd-delta' + (Math.abs(over) <= 25 ? ' ok' : '') + '">' +
          (over >= 0 ? '+' : '') + n0(over) + ' vs ' + n0(target.calories) + '</span>' +
      '</div></div>';
  }).join("");

  var bowls = PW.ORDER.map(function(w){ return bowlLineHTML(r, w); }).join("");

  return '<div class="blockdial">' + bowls +
    '<div class="bd-head">Base blocks on the plate' +
      '<span>' + n0(perBlock().calories) + ' kcal each &middot; baseline ' +
      n1(baselineBlocks()) + '</span></div>' + rows + '</div>';
}

/* ---- the cooked weight of a dish's batch --------------------------------
   The base block has one of these; every dish now gets its own. Macros per
   serving never needed the weight — they come from the ingredients divided by
   the servings. What the weight buys is the only thing you cannot derive:
   how many grams of THIS pan make one serving. */
function dishWeightKey(id){ return "hub.kitchen.weight." + id; }
function loadDishWeight(id){
  try{ var v = parseFloat(localStorage.getItem(dishWeightKey(id))); if(v > 0) return v; }
  catch(e){}
  return null;
}
function saveDishWeight(id, v){
  try{ localStorage.setItem(dishWeightKey(id), String(v)); }catch(e){}
}

function dishSplitHTML(r){
  var w = loadDishWeight(r.id);
  var c = r.computed || {};
  var per = w ? w / r.servings : null;

  var macros =
    '<div class="perserve">' +
      '<div class="ps-k">Per serving</div>' +
      '<div class="ps-v">' + n0(c.calories || 0) + ' kcal</div>' +
      '<div class="ps-m">' +
        '<span>P <b>' + n1(c.proteinG || 0) + '</b></span>' +
        '<span>Fib <b>' + n1(c.fiberG || 0) + '</b></span>' +
        '<span>F <b>' + n1(c.fatG || 0) + '</b></span>' +
      '</div>' +
    '</div>';

  return '<div class="dishsplit">' +
    '<label for="w-' + esc(r.id) + '">Weigh the pan, minus the pan</label>' +
    '<div class="weigh-row">' +
      '<input id="w-' + esc(r.id) + '" class="dishweight" data-dish="' + esc(r.id) + '" ' +
        'type="number" inputmode="decimal" min="1" step="1" ' +
        'value="' + (w ? n0(w) : "") + '" placeholder="cooked batch">' +
      '<span class="unit">grams</span>' +
    '</div>' +
    (per
      ? '<div class="serveout"><b>' + n0(per) + ' g</b> per serving &middot; ' +
        n0(r.servings) + ' servings</div>'
      : '<div class="serveout muted">Weigh the batch once and this becomes grams ' +
        'per serving. The macros below hold either way — they come from the ' +
        'ingredients, not from the scale.</div>') +
    macros +
  '</div>';
}

function savePlan(p){
  try{ localStorage.setItem("hub.kitchen.plan", JSON.stringify(p)); }catch(e){}
}
var PLAN = loadPlan();

/* Which tab, remembered per device. Plan is the default because that is the
   question you open the Kitchen with most often. */
var TAB = (function(){
  try{
    var v = localStorage.getItem("hub.kitchen.tab");
    if(v === "plan" || v === "shop" || v === "cook") return v;
  }catch(e){}
  return "plan";
})();
function setTab(t){
  TAB = t;
  try{ localStorage.setItem("hub.kitchen.tab", t); }catch(e){}
  render();
  window.scrollTo(0, 0);
}

/* Which shopping-list lines are already in the basket. Cleared whenever the
   plan changes, because a tick against the old list means nothing once the
   dishes — and therefore the amounts — have moved. */
function loadGot(){
  try{
    var v = JSON.parse(localStorage.getItem("hub.kitchen.got") || "[]");
    return Array.isArray(v) ? v : [];
  }catch(e){ return []; }
}
function saveGot(list){
  try{ localStorage.setItem("hub.kitchen.got", JSON.stringify(list)); }catch(e){}
}
function toggleGot(fid){
  var list = loadGot();
  var i = list.indexOf(fid);
  if(i === -1) list.push(fid); else list.splice(i, 1);
  saveGot(list);
}
function clearGot(){ saveGot([]); }

function mirrorRecipes(){
  return (D.recipes || []).filter(function(r){ return r.slot === "mirror" && r.computed; });
}
function snackRecipes(who){
  /* Snacks may be person-specific in a way mirror meals never are: the two
     Vorratsdosen are mixed in one session but with different dairy, because
     one of us does not eat Magerquark. A null person still means "both". */
  return (D.recipes || []).filter(function(r){
    return r.slot === "snack" && r.computed && (!r.person || r.person === who);
  });
}
function recipeById(id){
  var found = null;
  (D.recipes || []).forEach(function(r){ if(r.id === id) found = r; });
  return found;
}

/* Lower is better. Fibre-short and fat-over-ceiling are weighted heaviest
   because those are the two macros a single dish genuinely misses here —
   see the Pho Bo / Crispy Sweet Chili Chicken gaps. Protein shortfall matters;
   a calorie miss is softest, appetite already varies day to day. */
function pairFit(a, b){
  var mm = D.profiles.mirrorMeals.lunch;
  var fatHi = parseFloat(String(mm.fatG).split("-").pop());
  var tKcal = mm.calories*2, tP = mm.proteinG*2, tFib = mm.fiberG*2, tFatHi = fatHi*2;
  var c = a.computed, d = b.computed;
  var sKcal = c.calories + d.calories, sP = c.proteinG + d.proteinG,
      sFib = c.fiberG + d.fiberG, sFat = c.fatG + d.fatG;
  var dKcal = Math.abs(sKcal - tKcal) / tKcal;
  var dP   = Math.max(0, tP   - sP)   / tP;
  var dFib = Math.max(0, tFib - sFib) / tFib;
  var dFat = Math.max(0, sFat - tFatHi) / tFatHi;
  return { score: dKcal*0.5 + dP*1.5 + dFib*2 + dFat*2,
           kcal:sKcal, p:sP, fib:sFib, fat:sFat, tKcal:tKcal, tP:tP, tFib:tFib, tFatHi:tFatHi };
}
function pairCloses(fit){
  return fit.fib >= fit.tFib - 0.5 && fit.fat <= fit.tFatHi + 0.5 && fit.p >= fit.tP - 0.5;
}

/* Only decorates a candidate when picking it would actually CLOSE the day —
   a found-recipe library is fibre-poor by nature, so on most picks every
   single candidate falls short, and repeating a red warning nine times over
   is noise, not information. Silence is the honest default; a green line is
   the exception worth calling out. */
function pairCompareLine(otherR, r){
  var fit = pairFit(otherR, r);
  if(pairCloses(fit)){
    return '<span class="dp-pair ok">\u2713 closes the day \u2014 together ' +
      n0(fit.kcal) + ' kcal &middot; ' + n1(fit.p) + ' g P &middot; ' + n1(fit.fib) +
      ' g Fib &middot; ' + n1(fit.fat) + ' g F</span>';
  }
  if(pairTier(fit) === 1){
    var ft = D.fineTuneFiber;
    return '<span class="dp-pair husk">plus ' + g((fit.tFib - fit.fib) / ft.fiberPerG) +
      ' g ' + esc(ft.name) + ' \u2014 ' + n1(fit.fib) + ' of ' + n1(fit.tFib) + ' g fibre</span>';
  }
  return "";
}

/* Three tiers, not two. The library now holds dishes that are deliberately
   fibre-light — a pho stops being a pho if you fix its fibre by hand — so a
   pair can also be one spoon of husk away from closing. That is a different
   answer from "no", and folding it in with the failures would hide exactly the
   dishes this household wants to eat. Protein and fat still have to be right:
   powder only ever buys fibre. */
function pairTier(fit){
  if(pairCloses(fit)) return 0;
  var ft = D.fineTuneFiber;
  var proteinFatOk = fit.p >= fit.tP - 0.5 && fit.fat <= fit.tFatHi + 0.5;
  if(ft && proteinFatOk && (fit.tFib - fit.fib) / ft.fiberPerG <= ft.maxG) return 1;
  return 2;
}

/* A shape and a cuisine, so the picker can be scanned rather than read. Both
   are derived — the shape from the heaviest protein, the cuisine from the
   recipe's own field — so nothing here is typed twice.

   Ten of twenty-two dishes are poultry, so the shape alone would not separate
   the ones you actually choose between. The cuisine does that work; the shape
   catches the salmon and the pho at a glance. */
var DISH_GLYPH = {
  poultry: '<circle cx="9" cy="14.5" r="4.5"/><path d="M12.2 11.3 17 6.5a3 3 0 1 1 2.2 2.2l-4.8 4.8"/>',
  fish:    '<path d="M3 12c3-4 8-5 12-3 1.6.8 3 2 4 3-1 1-2.4 2.2-4 3-4 2-9 1-12-3Z"/><path d="M19 9l2-2.5v11L19 15"/><circle cx="8" cy="11" r=".9"/>',
  beef:    '<path d="M4 9.5C4 7.3 7.6 5.5 12 5.5s8 1.8 8 4v5c0 2.2-3.6 4-8 4s-8-1.8-8-4Z"/><path d="M9 10.5c1.6-1 4.4-1 6 0"/>',
  dairy:   '<path d="M6.5 8.5h11l-1 10.6A2 2 0 0 1 14.5 21h-5a2 2 0 0 1-2-1.9Z"/><path d="M4.8 8.5h14.4"/><path d="M9.5 5.5h5"/>',
  shake:   '<path d="M8.6 3.5h6.8l-.6 4H9.2Z"/><path d="M9.2 7.5h5.6l.8 11a2 2 0 0 1-2 2.1h-3.2a2 2 0 0 1-2-2.1Z"/>',
  egg:     '<path d="M12 3.2c3.3 0 6 4.4 6 8.6S15.3 20.8 12 20.8 6 15.9 6 11.8 8.7 3.2 12 3.2Z"/>',
  plant:   '<path d="M20 4C10 4 5 9 5 15c0 2 .6 3.7 1.6 5C13.2 20 20 14 20 4Z"/><path d="M6.6 20C9.2 15 13 11.2 18 8.4"/>'
};

function dishIcon(r){
  var kind = (D.dishKinds && D.dishKinds[r.id]) || "plant";
  return '<svg class="dp-icon" viewBox="0 0 24 24" aria-hidden="true">' +
    (DISH_GLYPH[kind] || DISH_GLYPH.plant) + '</svg>';
}

/* "asian" is a continent rather than a cuisine, which kitchen.json already
   says about itself. Shown as recorded rather than guessed at.

   "none" is a real value here, not a missing one: it tells adapt_recipe.py to
   filter nothing from the top-up shortlist. It is a fact about the solver, not
   a label for a person, so it does not get a tag. */
function cuisineTag(r){
  var c = r.cuisine;
  if(!c || c === "none") return '';
  return '<span class="dp-cuisine">' + esc(c.replace(/-/g, " ")) + '</span>';
}

/* Whether you need to put a block beside it is a fact about the dish worth
   knowing before you pick it, not after. */
function carbTag(r){
  if(r.slot !== "mirror") return '';
  return r.carb === "own"
    ? '<span class="dp-carb own">own carb</span>'
    : '<span class="dp-carb">+ block</span>';
}

function dishChip(r, opts){
  opts = opts || {};
  var c = r.computed || {};
  /* Mirror dishes are eaten by both, so their servings convert to days for
     two. Snacks are not meal-prepped on that same 1-per-person-per-day
     assumption, so just say how many the batch makes. */
  var tail = r.slot === "mirror"
    ? (function(){
        var days = r.servings / 2;
        return (Math.round(days*10)/10) + (days === 1 ? ' day' : ' days') + ' for two';
      })()
    : r.servings + (r.servings === 1 ? ' serving' : ' servings');
  /* Choosing dinner should be recognition, not a spreadsheet read. While you
     are still deciding, a dish shows its name, its size and — once there is
     something to pair it against — the verdict. The five macro figures are the
     inputs to that verdict rather than the verdict itself, so they come back
     the moment the dish is actually picked. */
  var full = n0(c.calories) + ' kcal &middot; ' + n1(c.proteinG) + ' g P &middot; ' +
             n1(c.fiberG) + ' g Fib &middot; ' + n1(c.fatG) + ' g F &middot; ' + tail;
  var brief = n0(c.calories) + ' kcal &middot; ' + tail;

  return '<button class="dishpick' + (opts.picked ? ' picked' : '') + '" data-slot="' +
    esc(opts.slot) + '" data-id="' + esc(r.id) + '">' +
    '<span class="dp-top">' + dishIcon(r) +
      '<span class="dp-title">' + esc(r.title) + '</span></span>' +
    '<span class="dp-meta">' + cuisineTag(r) + carbTag(r) +
      (opts.picked ? full : brief) + '</span>' +
    (opts.compareLine || '') +
    (opts.badge ? '<span class="dp-badge">' + esc(opts.badge) + '</span>' : '') +
    '</button>';
}

function slotHTML(slot){
  var list = mirrorRecipes();
  var label = slot.charAt(0).toUpperCase() + slot.slice(1);
  var otherSlot = slot === "lunch" ? "dinner" : "lunch";
  var pickedId = PLAN[slot];
  if(pickedId && !recipeById(pickedId)){ pickedId = null; PLAN[slot] = null; savePlan(PLAN); }

  if(pickedId){
    var picked = recipeById(pickedId);
    return '<div class="planslot"><div class="ps-label">' + label + '</div>' +
      dishChip(picked, {slot:slot, picked:true}) +
      '<button class="ps-change" data-slot="' + esc(slot) + '">change</button></div>';
  }

  var otherId = PLAN[otherSlot];
  var otherR = otherId ? recipeById(otherId) : null;
  var scored = list.map(function(r){
    return { r:r, fit: otherR ? pairFit(otherR, r) : null };
  });

  function chips(items, withBadge){
    return items.map(function(x, i){
      return dishChip(x.r, {
        slot: slot,
        badge: (withBadge && i === 0) ? "closest fit" : "",
        compareLine: otherR ? pairCompareLine(otherR, x.r) : ""
      });
    }).join("");
  }

  /* Nothing picked in the other slot yet, so there is no pair to judge. */
  if(!otherR){
    return '<div class="planslot"><div class="ps-label">' + label + '</div>' +
      '<div class="ps-list">' + chips(scored, false) + '</div></div>';
  }

  scored.sort(function(a, b){ return a.fit.score - b.fit.score; });
  var fits = scored.filter(function(x){ return pairTier(x.fit) === 0; });
  var near = scored.filter(function(x){ return pairTier(x.fit) === 1; });
  var no   = scored.filter(function(x){ return pairTier(x.fit) === 2; });

  var body = "";
  if(fits.length) body += '<div class="ps-list">' + chips(fits, true) + '</div>';
  if(near.length){
    body += '<div class="ps-tier">' +
      (fits.length ? 'Or, with a spoon of husk' : 'One spoon of husk short') +
      '</div><div class="ps-list">' + chips(near, !fits.length) + '</div>';
  }
  /* What cannot work is folded away rather than removed. An empty list is a
     mystery; a closed disclosure is an answer, and it stays one tap away. */
  if(no.length){
    body += '<details class="ps-rest"><summary>' + no.length +
      (no.length === 1 ? ' more that cannot close' : ' more that cannot close') +
      ' the day with ' + esc(otherR.title) + '</summary><div class="ps-list">' +
      chips(no, false) + '</div></details>';
  }
  if(!fits.length && !near.length){
    body = '<p class="ps-note">Nothing here closes the day with ' + esc(otherR.title) +
      ', not even with husk. Pick what you want to eat and take the gap, or change ' +
      'the other dish.</p>' + body;
  }

  return '<div class="planslot"><div class="ps-label">' + label +
    ' <span class="ps-hint">&middot; ranked to fit ' + esc(otherR.title) + '</span>' +
    '</div>' + body + '</div>';
}

/* What is actually left for a snack once breakfast (if fixed) and the
   lunch/dinner picks (real macros if chosen, else the mirror target) are
   accounted for. Deliberately ignores any snack already picked — this is
   the budget to rank CANDIDATES against, not what remains after one. */
function remainingBeforeSnack(who){
  var prof = D.profiles.people[who];
  var t = prof.dailyTargets;
  var mm = D.profiles.mirrorMeals;
  var kcal = t.calories, p = t.proteinG, fib = t.fiberG;
  if(prof.fixedBreakfast){
    kcal -= prof.fixedBreakfast.calories; p -= prof.fixedBreakfast.proteinG; fib -= prof.fixedBreakfast.fiberG;
  }
  ["lunch","dinner"].forEach(function(k){
    var picked = PLAN[k] ? recipeById(PLAN[k]) : null;
    var c = picked ? picked.computed : mm[k];
    kcal -= c.calories; p -= c.proteinG; fib -= c.fiberG;
  });
  /* Portions already chosen are spent, so the next one is ranked against what
     is actually left rather than against the whole afternoon again. */
  pickedSnacks(who).forEach(function(id){
    var c = recipeById(id).computed;
    kcal -= c.calories; p -= c.proteinG; fib -= c.fiberG;
  });
  return { kcal:kcal, p:p, fib:fib };
}

/* Lower is better. A snack that blows past the remaining calories is
   penalised; one that still leaves protein or fibre short is penalised more
   — those are the two the day structurally struggles with, same weighting
   as pairFit above. */
function snackFit(remaining, snack){
  var c = snack.computed;
  var kcalOver = Math.max(0, c.calories - Math.max(remaining.kcal, 0));
  var pShort   = Math.max(0, remaining.p   - c.proteinG);
  var fibShort = Math.max(0, remaining.fib - c.fiberG);
  return kcalOver / Math.max(remaining.kcal, 1) * 1.0 +
         pShort   / Math.max(remaining.p, 1)   * 1.5 +
         fibShort / Math.max(remaining.fib, 1) * 1.5;
}

/* A single snack rarely closes what a whole meal left open — that is normal,
   not a problem, so it stays silent by default. The one thing worth flagging
   is a snack that overshoots the calories actually left. */
function snackOvershoots(remaining, snack){
  return (remaining.kcal - snack.computed.calories) < -100;
}
function snackCompareLine(remaining, snack){
  var c = snack.computed;
  var kcalLeft = remaining.kcal - c.calories, pLeft = remaining.p - c.proteinG,
      fibLeft = remaining.fib - c.fiberG;
  if(!snackOvershoots(remaining, snack)) return "";
  return '<span class="dp-pair warn">⚠ over budget — leaves ' + n0(kcalLeft) +
    ' kcal &middot; ' + n1(pLeft) + ' g P &middot; ' + n1(fibLeft) + ' g Fib</span>';
}

function snackSlotHTML(){
  var who = PW.get();
  var slots = snackSlots(who);
  /* The plan is one household plan — lunch and dinner are mirror meals and the
     afternoon bowl is shared, so slot 2 simply is Philipp's second portion.
     Do NOT truncate the list when Eunice is showing: pickedSnacks() slices to
     the person's own count for display, and truncating here would throw his
     second pick away the moment she chose anything. */
  var dirty = false;
  for(var i = 0; i < slots; i++){
    if(PLAN.snacks[i] && !recipeById(PLAN.snacks[i])){ PLAN.snacks[i] = null; dirty = true; }
    if(PLAN.snacks[i] === undefined){ PLAN.snacks[i] = null; }
  }
  if(dirty) savePlan(PLAN);

  function label(i){
    return slots === 1 ? "Snack" : "Snack " + (i + 1) + " of " + slots;
  }

  var out = "";
  var nextOpen = -1;
  for(var j = 0; j < slots; j++){
    if(PLAN.snacks[j]){
      out += '<div class="ps-portion"><div class="ps-label">' + label(j) + '</div>' +
        dishChip(recipeById(PLAN.snacks[j]), {slot:"snack:" + j, picked:true}) +
        '<button class="ps-change" data-slot="snack:' + j + '">change</button></div>';
    }else if(nextOpen < 0){
      nextOpen = j;
    }
  }

  /* One list at a time. Two ranked lists side by side is a decision too many,
     and the second portion should be ranked against what the first one left. */
  if(nextOpen >= 0){
    var remaining = remainingBeforeSnack(who);
    var scored = snackRecipes(who).map(function(r){ return { r:r, s: snackFit(remaining, r) }; });
    scored.sort(function(a,b){ return a.s - b.s; });
    if(!scored.length){
      out += '<div class="ps-portion"><div class="ps-label">' + label(nextOpen) + '</div>' +
        '<div class="empty">No snack recipes ready yet.</div></div>';
    }else{
      out += '<div class="ps-portion"><div class="ps-label">' + label(nextOpen) +
        ' <span class="ps-hint">&middot; ranked to fit ' + esc(PW.PEOPLE[who].name) +
        '\u2019s remaining ' + n0(Math.max(remaining.kcal, 0)) + ' kcal</span></div>' +
        '<div class="ps-list">' + scored.map(function(x, i){
          return dishChip(x.r, {
            slot: "snack:" + nextOpen,
            badge: i === 0 ? "closest fit" : "",
            compareLine: snackCompareLine(remaining, x.r)
          });
        }).join("") + '</div></div>';
    }
  }
  return '<div class="planslot planslot-snack">' + out + '</div>';
}

/* Everything the shop and the fit flags both need, computed once. Returns
   null until there is a full pair to reason about. */
function shoppingBasis(){
  var lunch  = PLAN.lunch  ? recipeById(PLAN.lunch)  : null;
  var dinner = PLAN.dinner ? recipeById(PLAN.dinner) : null;
  if(!lunch || !dinner) return null;

  var snacks = pickedSnacks(PW.get()).map(recipeById);
  var totals = {}, blocks = 0;
  var chosen = [lunch, dinner];
  snacks.forEach(function(r){ chosen.push(r); });
  /* Blocks are no longer a property of the recipe. A mirror dish makes
     servings/2 days for two, and on each of those days each of them puts
     their own number of blocks on the plate. */
  var perDay = blockCount("philipp") + blockCount("eunice");
  chosen.forEach(function(r){
    if(takesBlocks(r)) blocks += (r.servings / 2) * perDay;
    (r.ingredients || []).forEach(function(i){
      totals[i.food] = (totals[i.food] || 0) + i.g;
    });
  });

  return { lunch:lunch, dinner:dinner, snacks:snacks, totals:totals,
           blocks:blocks, fit:pairFit(lunch, dinner) };
}

/* Does this pair work? That is a planning question, so it lives with the
   picker rather than with the shopping list. */
function pairFlagsHTML(){
  var b = shoppingBasis();
  if(!b) return "";

  var lunchDays = b.lunch.servings/2, dinnerDays = b.dinner.servings/2;
  var mismatch = lunchDays !== dinnerDays
    ? '<div class="flag warn"><div class="ft">Different lengths</div><p>' +
      esc(b.lunch.title) + ' makes ' + (Math.round(lunchDays*10)/10) + ' day(s) of lunch for two, ' +
      esc(b.dinner.title) + ' makes ' + (Math.round(dinnerDays*10)/10) + ' day(s) of dinner. ' +
      'Cook the shorter one again partway through, or scale the batch by hand.</p></div>'
    : '';

  var fit = b.fit;
  var closes = pairCloses(fit);
  var fitFlag = '<div class="flag' + (closes ? '' : ' warn') + '"><div class="ft">' +
    (closes ? 'This pair closes the day' : 'This pair does not close the day') + '</div><p>' +
    'Together: ' + n0(fit.kcal) + ' kcal, ' + n1(fit.p) + ' g protein (target ' + n0(fit.tP) +
    '), ' + n1(fit.fib) + ' g fibre (target ' + n0(fit.tFib) + '), ' + n1(fit.fat) +
    ' g fat (ceiling ' + n0(fit.tFatHi) + ') — both mirror meals combined.' +
    (closes ? '' : ' The gap is real — close it with a snack, or pick a different pairing above.') +
    '</p></div>';

  return mismatch + fitFlag;
}

function shoppingListHTML(){
  var b = shoppingBasis();
  if(!b) return '<div class="card"><div class="ch"><span class="k">Shopping list</span>' +
    '<span class="meta">household</span></div>' +
    '<div class="empty">Pick a lunch and a dinner under <b>Plan</b> and the list ' +
    'builds itself.</div></div>';

  var totals = b.totals;
  /* Ticked in a shop, one-handed, with a basket in the other hand — so the
     whole row is the target, not a 20 px box, and the state survives the
     screen locking between aisles. */
  var got = loadGot();
  var rows = Object.keys(totals).sort(function(a,b2){ return totals[b2] - totals[a]; })
    .map(function(fid){
      var on = got.indexOf(fid) !== -1;
      return '<li class="shop' + (on ? ' got' : '') + '">' +
        '<button type="button" class="shoptick" data-food="' + esc(fid) + '" ' +
        'aria-pressed="' + on + '">' +
        '<span class="box" aria-hidden="true"></span>' +
        '<span class="t">' + esc(D.foodNames[fid] || fid) + '</span>' +
        '<span class="amt">' + n0(totals[fid]) + ' g</span>' +
        '</button></li>';
    }).join("");

  var done = Object.keys(totals).filter(function(f){ return got.indexOf(f) !== -1; }).length;

  return '<div class="card"><div class="ch"><span class="k">Shopping list</span>' +
    '<span class="meta">' + done + ' of ' + Object.keys(totals).length + ' &middot; household</span>' +
    '<span class="title">' + esc(b.lunch.title) + ' + ' + esc(b.dinner.title) +
      b.snacks.map(function(r){ return ' + ' + esc(r.title); }).join('') + '</span></div>' +
    '<ul class="ing">' + rows + '</ul>' +
    '</div>' + baseBlockShoppingHTML(b);
}

/* The block has ingredients you have to buy, and the list used to end at
   "plus 10 Asian Base Blocks" — a number with no shopping in it. Scaled from
   the batch the recipe is written for. */
function baseBlockShoppingHTML(b){
  var need = Math.ceil(b.blocks);
  if(!(need > 0) || !D.baseShopping) return "";
  var per = D.baseShopping.blocksPerBatch || 10;
  var batches = need / per;

  function scale(amount){
    var m = /^([0-9.,]+)\s*(g|ml|tsp)$/.exec(amount.trim());
    if(!m) return amount;
    var v = parseFloat(m[1].replace(",", ".")) * batches;
    if(m[2] === "tsp") return (Math.round(v * 2) / 2) + " tsp";
    return (v < 50 ? Math.round(v) : Math.round(v / 5) * 5) + " " + m[2];
  }

  var rows = D.baseShopping.ingredients.map(function(i){
    return '<li><div class="t">' + esc(i.item) + '</div>' +
           '<div class="amt">' + esc(scale(i.amount)) + '</div></li>';
  }).join("");

  return '<div class="card"><div class="ch"><span class="k">Asian Base Block</span>' +
    '<span class="meta">' + n0(need) + ' block' + (need === 1 ? '' : 's') +
      ' &middot; ' + n1(batches) + ' batch' + (batches === 1 ? '' : 'es') + '</span>' +
    '<span class="title">Philipp ' + n1(blockCount("philipp")) + ' &middot; Eunice ' +
      n1(blockCount("eunice")) + ' per plate</span></div>' +
    '<ul class="ing">' + rows + '</ul>' +
    '<div class="rnote">One batch makes ' + n0(per) + ' blocks. The method is under ' +
    '<b>Cook</b>.</div></div>';
}

function plannerHTML(){
  return '<div class="card"><div class="ch"><span class="k">Plan the batch</span>' +
    '<span class="meta">lunch &amp; dinner are the same for both of you</span></div>' +
    '<div class="planrow">' + slotHTML("lunch") + slotHTML("dinner") + '</div>' +
    snackSlotHTML() +
    '</div>' + pairFlagsHTML();
}

function recipesHTML(who){
  var list = recipesFor(who);
  var head = '<div class="card"><div class="ch"><span class="k">Recipes</span>' +
    '<span class="meta">' + list.length + ' for ' + esc(PW.PEOPLE[who].name) + '</span></div>';

  if(!list.length){
    return head + '<div class="empty">Nothing here yet.</div>' +
      lookForHTML() + addNote() + '</div>';
  }

  /* Collapsed. The picked dishes are spelled out above; this is the library
     you browse, not the thing you cook from, and open it was three thousand
     pixels of the same rows the picker had already shown. */
  return head + '<details class="library"><summary>All ' + list.length +
    ' recipes</summary>' + list.map(function(r){
    var c = r.computed || {};
    var ing = (r.ingredients || []).map(function(i){
      return '<li><div class="t">' + esc(D.foodNames[i.food] || i.food) + '</div>' +
             '<div class="amt">' + esc(i.note || (i.g + " g")) + '</div></li>';
    }).join("");
    var steps = (r.steps || []).map(function(st,i){
      return '<li><span class="n">' + (i+1) + '</span><div class="t">' + esc(st) + '</div></li>';
    }).join("");
    return '<div class="lrow"><div class="lb">' + esc(r.title) + '</div>' +
      '<div class="lv">' + n0(c.calories || 0) + ' kcal</div>' +
      '<div class="ls"><span class="tag">' + esc(r.slot) + '</span>' +
        '<span>P <b>' + n1(c.proteinG || 0) + ' g</b></span>' +
        '<span>Fib <b>' + n1(c.fiberG || 0) + ' g</b></span>' +
        '<span>F <b>' + n1(c.fatG || 0) + ' g</b></span>' +
      '</div></div>' +
      '<details><summary>Ingredients and method</summary>' +
        '<ul class="ing">' + ing + '</ul>' +
        (steps ? '<ol class="steps">' + steps + '</ol>' : '') +
      '</details>';
  }).join("") + '</details>' + lookForHTML() + addNote() + '</div>';
}

/* The dish actually being cooked, spelled out. Until now the method for your
   picked dish sat collapsed inside a list of twenty other dishes, while the
   page gave three full cards to the carb base nobody has to look up. */
function pickedDetailHTML(open){
  var want = [];
  if(PLAN.lunch && PLAN.lunch === PLAN.dinner){
    want.push({ slot: "Lunch & dinner", id: PLAN.lunch });
  }else{
    if(PLAN.lunch)  want.push({ slot: "Lunch",  id: PLAN.lunch });
    if(PLAN.dinner) want.push({ slot: "Dinner", id: PLAN.dinner });
  }
  var snacks = pickedSnacks(PW.get());
  var seenSnack = {};
  snacks.forEach(function(id){
    if(seenSnack[id]) return;
    seenSnack[id] = 1;
    want.push({ slot: "Snack", id: id });
  });

  return want.map(function(x){
    var r = recipeById(x.id);
    if(!r) return "";
    var ing = (r.ingredients || []).map(function(i){
      return '<li><div class="t">' + esc(D.foodNames[i.food] || i.food) + '</div>' +
             '<div class="amt">' + esc(i.note || (i.g + " g")) + '</div></li>';
    }).join("");
    var steps = (r.steps || []).map(function(st, i){
      return '<li><span class="n">' + (i + 1) + '</span><div class="t">' + esc(st) + '</div></li>';
    }).join("");
    /* Open on the Cook tab — this is now the page you are standing in front of
       with the pan, so the dish should not need a tap to appear. */
    return '<div class="card cookcard"><details' + (open ? ' open' : '') + '><summary>' +
      '<span class="k">' + esc(x.slot) + '</span>' + dishIcon(r) +
      '<span class="title">' + esc(r.title) + '</span>' +
      '<span class="meta">' + n0(r.servings) + ' serving' + (r.servings === 1 ? '' : 's') + '</span>' +
      '</summary>' +
      '<ul class="ing">' + ing + '</ul>' +
      (steps ? '<ol class="steps">' + steps + '</ol>' : '') +
      (r.slot === "mirror" ? blockDialHTML(r) : '') +
      dishSplitHTML(r) +
      '</details></div>';
  }).join("");
}

function render(){
  /* base.purpose describes the Asian Base Block — one component of one dish.
     It was standing in as the subtitle for the whole module. */
  document.getElementById("sub").textContent =
    "Plan the batch, shop for it, cook it, split it.";

  var splitter =
    '<div class="card"><div class="ch"><span class="k">Split the batch</span>' +
    '<span class="meta">' + n0(per100.calories) + ' kcal / 100 g</span></div>' +
    '<div class="weigh">' +
      '<label for="w">Weigh the pan, minus the pan</label>' +
      '<div class="weigh-row">' +
        '<input id="w" type="number" inputmode="decimal" min="1" step="1" value="' + n0(weight) + '">' +
        '<span class="unit">grams</span>' +
      '</div>' +
      '<p class="hint">Cooked weight, not raw. Everything below follows from this one number.</p>' +
    '</div>' + splitHTML() + '</div>';

  /* The data's own note is written for whoever maintains the file. This is the
     version for whoever is holding the pan. */
  var estimated = base.yield._status === "ESTIMATED"
    ? '<div class="flag"><div class="ft">Worth doing once</div><p>' +
      'These numbers assume the batch comes out at about ' +
      n0(comp.gramsPerBlock * base.yield.blocks) + ' g. Nobody has weighed one yet. ' +
      'Next time you cook it, put the real cooked weight in the box above and tell ' +
      'Claude — being 50 g out shifts every figure here by roughly 6%.' +
      '</p></div>'
    : '';

  /* The base block is a component cooked the same way every time, so it folds
     like the dishes do rather than occupying twelve hundred pixels between the
     splitter and the day. */
  var ing = '<div class="card cookcard"><details><summary>' +
    '<span class="k">Base block</span><span class="title">Ingredients</span>' +
    '<span class="meta">' + n0(comp.batchTotal.calories) + ' kcal total</span></summary>' +
    '<ul class="ing">' +
    base.ingredients.map(function(i){
      return '<li><div class="t">' + esc(i.item) + '</div>' +
             '<div class="amt">' + esc(i.amount) + '</div></li>';
    }).join("") + '</ul></details></div>';

  var steps = '<div class="card cookcard"><details><summary>' +
    '<span class="k">Base block</span><span class="title">Method</span>' +
    '<span class="meta">' + esc(D.kitchen.hardware.device.split(" ").slice(0,2).join(" ")) + '</span></summary>' +
    '<ol class="steps">' + base.steps.map(function(s,i){
      return '<li><span class="n">' + (i+1) + '</span><div class="t">' + esc(s) + '</div></li>';
    }).join("") + '</ol></details></div>';

  var mf = D.kitchen.macroFactorLogging.asianBaseCustomFoodPer100gCooked;
  var rows = "";
  ["calories","proteinG","carbsG","fiberG","fatG"].forEach(function(k){
    rows += '<div><div class="dk">' + esc(k.replace("G","").replace("calories","kcal")) +
      '</div><div class="dv">' + esc(mf[k]) + ' per 100 g</div></div>';
  });

  var blockRows = "";
  for(var k in base.blockRules){
    blockRows += '<div><div class="dk">' + esc(k.replace(/([A-Z])/g," $1").toLowerCase()) +
      '</div><div class="dv"><strong>' + esc(base.blockRules[k]) + ' block' +
      (base.blockRules[k] === 1 ? '' : 's') + '</strong></div></div>';
  }

  /* Four top-level accordions for four pieces of reference became one card
     with four rows inside it. Same content, one thing in the scroll. */
  var extras =
    '<div class="card refcard"><div class="ch"><span class="k">Reference</span>' +
    '<span class="meta">standards, logging, substitutions</span></div>' +
    '<details><summary>Log it in MacroFactor</summary><div class="dl">' + rows +
      '<div><div class="dk">Note</div><div class="dv">' + esc(D.kitchen.macroFactorLogging._actionRequired) + '</div></div>' +
    '</div></details>' +
    '<details><summary>How many blocks per dish</summary><div class="dl">' + blockRows + '</div></details>' +
    '<details><summary>If quinoa runs out</summary><div class="dl">' +
      '<div><div class="dk">Replace with</div><div class="dv">' + esc(base.substitutions.quinoaUnavailable.replaceWith) + '</div></div>' +
      '<div><div class="dk">Water</div><div class="dv">' + esc(base.substitutions.quinoaUnavailable.waterAdjustment) + '</div></div>' +
      '<div><div class="dk">Ninja</div><div class="dv">' + esc(base.substitutions.quinoaUnavailable.ninjaSettings) + '</div></div>' +
    '</div></details>' +
    '<details><summary>Standards we cook to</summary><div class="dl">' +
      Object.keys(D.kitchen.culinaryStandards).map(function(k){
        return '<div><div class="dk">' + esc(k.replace(/([A-Z])/g," $1").toLowerCase()) +
          '</div><div class="dv">' + esc(D.kitchen.culinaryStandards[k]) + '</div></div>';
      }).join("") + '</div></details>' +
    '</div>';

  /* Three jobs, three tabs. Cooking, shopping and accounting happen at
     different moments, in different rooms, in different states of mess —
     stacking them into one scroll meant each had to be found by scrolling
     past the others. */
  var picked = (PLAN.lunch ? 1 : 0) + (PLAN.dinner ? 1 : 0);
  var got = loadGot();
  var basis = shoppingBasis();
  var shopCount = basis ? Object.keys(basis.totals).length : 0;
  var shopLeft = basis
    ? Object.keys(basis.totals).filter(function(f){ return got.indexOf(f) === -1; }).length
    : 0;

  var TABS = [
    { id:"plan", label:"Plan",
      note: picked === 2 ? "set" : (picked ? "1 of 2" : "nothing picked") },
    { id:"shop", label:"Shop",
      note: !basis ? "—" : (shopLeft ? shopLeft + " left" : "all in") },
    { id:"cook", label:"Cook",
      note: basis ? "ready" : "—" }
  ];

  var tabBar = '<div class="ktabs" role="tablist">' + TABS.map(function(t){
    return '<button type="button" role="tab" class="ktab" data-tab="' + t.id + '" ' +
      'aria-selected="' + (TAB === t.id) + '">' + esc(t.label) +
      '<span>' + esc(t.note) + '</span></button>';
  }).join("") + '</div>';

  var body;
  if(TAB === "shop"){
    body = shoppingListHTML();
  }else if(TAB === "cook"){
    body = basis
      ? pickedDetailHTML(true) + splitter + estimated + ing + steps
      : '<div class="card"><div class="ch"><span class="k">Cook</span></div>' +
        '<div class="empty">Nothing picked yet. Choose a lunch and a dinner under ' +
        '<b>Plan</b> and they appear here with their method and their split.</div></div>' +
        splitter + estimated + ing + steps;
  }else{
    body = plannerHTML() +
      ledgerHTML(PW.get()) + mealHTML() +
      recipesHTML(PW.get()) + extras;
  }

  document.getElementById("stage").innerHTML = tabBar + body;

  document.querySelectorAll(".ktab").forEach(function(b){
    b.addEventListener("click", function(){ setTab(b.dataset.tab); });
  });

  var input = document.getElementById("w");
  if(input) input.addEventListener("input", function(){
    var v = parseFloat(input.value);
    if(!(v > 0)) return;
    weight = v; saveWeight(v);
    var card = input.closest(".card");
    card.querySelector(".split").outerHTML = splitHTML();
  });

  /* Each dish carries its own scale reading. Updated in place — a re-render
     would close the card you are cooking from. */
  document.querySelectorAll(".dishweight").forEach(function(el){
    el.addEventListener("input", function(){
      var v = parseFloat(el.value);
      if(!(v > 0)) return;
      saveDishWeight(el.dataset.dish, v);
      var r = recipeById(el.dataset.dish);
      var out = el.closest(".dishsplit").querySelector(".serveout");
      out.className = "serveout";
      out.innerHTML = '<b>' + n0(v / r.servings) + ' g</b> per serving &middot; ' +
        n0(r.servings) + ' servings';
    });
  });
}

/* "lunch" and "dinner" address the plan directly; "snack:N" addresses one
   portion of the afternoon bowl. */
function setSlot(slot, id){
  var m = /^snack:([0-9]+)$/.exec(slot);
  if(m) PLAN.snacks[Number(m[1])] = id;
  else PLAN[slot] = id;
  savePlan(PLAN);
  clearGot();
}

/* Delegated once on the stage, not inside render() — the buttons are replaced
   on every render(), but the stage element itself is not. */
document.getElementById("stage").addEventListener("click", function(ev){
  var pick = ev.target.closest(".dishpick");
  if(pick){
    setSlot(pick.dataset.slot, pick.dataset.id);
    render();
    return;
  }
  var change = ev.target.closest(".ps-change");
  if(change){
    setSlot(change.dataset.slot, null);
    render();
    return;
  }
  /* Ticked in place — a full re-render would throw away the scroll position
     halfway down a shopping list, which is the one thing you cannot afford
     while walking a supermarket. */
  var blk = ev.target.closest("[data-blk]");
  if(blk){
    var who = blk.dataset.blk;
    var v = Math.min(Math.max(blockCount(who) + parseFloat(blk.dataset.d), 0), 4);
    setBlockCount(who, v);
    render();
    return;
  }
  var tick = ev.target.closest(".shoptick");
  if(tick){
    toggleGot(tick.dataset.food);
    var on = tick.getAttribute("aria-pressed") !== "true";
    tick.setAttribute("aria-pressed", String(on));
    tick.closest("li").classList.toggle("got", on);
  }
});

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs("kitchen", "../");
render();
window.addEventListener("pw:person", render);
</script>

</body>
</html>
"""

html = HTML.replace("__DATA__", data_json)\
        .replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written kitchen/index.html  (%d bytes)" % len(html))

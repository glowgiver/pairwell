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


data = {
    "kitchen": strip_buildonly(json.load(open(KITCHEN, encoding="utf-8"))),
    "profiles": strip_body(json.load(open(PROFILES, encoding="utf-8"))),
    "recipes": _recipes,
    "foodNames": dict((k, v["name"]) for k, v in _foods.items()),
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

  ol.steps,ul.ing{list-style:none;margin:0;padding:6px 0}
  ol.steps li,ul.ing li{
    display:grid;grid-template-columns:26px 1fr;gap:12px;
    padding:11px 18px;align-items:baseline;
  }
  ol.steps li+li,ul.ing li+li{border-top:1px solid var(--line)}
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
  .dp-badge{
    display:inline-block;margin-top:6px;font-family:var(--f-data);font-size:11.5px;
    font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--accent);
  }
  .ps-change{
    margin-top:10px;min-height:36px;background:none;border:1px solid var(--line);
    border-radius:10px;padding:0 14px;font-size:13px;color:var(--muted);cursor:pointer;
  }

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
  if(PLAN.snack){
    var s = recipeById(PLAN.snack);
    if(s){
      rows.push({ label:s.title, tag:"snack", kcal:s.computed.calories, p:s.computed.proteinG,
                  fib:s.computed.fiberG, fat:s.computed.fatG });
    }
  }

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
  try{
    var v = JSON.parse(localStorage.getItem("hub.kitchen.plan") || "{}");
    return { lunch: v.lunch || null, dinner: v.dinner || null, snack: v.snack || null };
  }catch(e){ return {lunch:null, dinner:null, snack:null}; }
}
function savePlan(p){
  try{ localStorage.setItem("hub.kitchen.plan", JSON.stringify(p)); }catch(e){}
}
var PLAN = loadPlan();

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
  if(!pairCloses(fit)) return "";
  return '<span class="dp-pair ok">✓ closes the day — together ' +
    n0(fit.kcal) + ' kcal &middot; ' + n1(fit.p) + ' g P &middot; ' + n1(fit.fib) +
    ' g Fib &middot; ' + n1(fit.fat) + ' g F</span>';
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
  return '<button class="dishpick' + (opts.picked ? ' picked' : '') + '" data-slot="' +
    esc(opts.slot) + '" data-id="' + esc(r.id) + '">' +
    '<span class="dp-title">' + esc(r.title) + '</span>' +
    '<span class="dp-meta">' + n0(c.calories) + ' kcal &middot; ' + n1(c.proteinG) + ' g P &middot; ' +
      n1(c.fiberG) + ' g Fib &middot; ' + n1(c.fatG) + ' g F &middot; ' + tail + '</span>' +
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
    var r = recipeById(pickedId);
    return '<div class="planslot"><div class="ps-label">' + label + '</div>' +
      dishChip(r, {slot:slot, picked:true}) +
      '<button class="ps-change" data-slot="' + esc(slot) + '">change</button></div>';
  }

  var otherId = PLAN[otherSlot];
  var otherR = otherId ? recipeById(otherId) : null;
  var scored = list.map(function(r){
    return { r:r, fit: otherR ? pairFit(otherR, r) : null };
  });
  if(otherR) scored.sort(function(a,b){ return a.fit.score - b.fit.score; });
  var anyCloses = otherR ? scored.some(function(x){ return pairCloses(x.fit); }) : false;

  var body = scored.map(function(x, i){
    return dishChip(x.r, {
      slot:slot,
      badge: (otherR && i === 0) ? "closest fit" : "",
      compareLine: otherR ? pairCompareLine(otherR, x.r) : ""
    });
  }).join("");

  /* One honest line instead of nine repeated warnings — this is the common
     case with a fibre-poor library, and it should read as information, not
     as the app scolding every choice. */
  var noneClose = (otherR && !anyCloses)
    ? '<p class="ps-note">None of these close the day with ' + esc(otherR.title) +
      ' on their own — the closest still leaves a real gap. Pick freely; ' +
      'close it with a snack, or look for dishes with more built-in fibre.</p>'
    : '';

  return '<div class="planslot"><div class="ps-label">' + label +
    (otherR ? ' <span class="ps-hint">&middot; ranked to fit ' + esc(otherR.title) + '</span>' : '') +
    '</div>' + noneClose + '<div class="ps-list">' + body + '</div></div>';
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
  var pickedId = PLAN.snack;
  if(pickedId && !recipeById(pickedId)){ pickedId = null; PLAN.snack = null; savePlan(PLAN); }

  if(pickedId){
    var r = recipeById(pickedId);
    return '<div class="planslot planslot-snack"><div class="ps-label">Snack</div>' +
      dishChip(r, {slot:"snack", picked:true}) +
      '<button class="ps-change" data-slot="snack">change</button></div>';
  }

  var remaining = remainingBeforeSnack(who);
  var scored = snackRecipes(who).map(function(r){ return { r:r, s: snackFit(remaining, r) }; });
  scored.sort(function(a,b){ return a.s - b.s; });
  var body = scored.map(function(x, i){
    return dishChip(x.r, {
      slot:"snack",
      badge: i === 0 ? "closest fit" : "",
      compareLine: snackCompareLine(remaining, x.r)
    });
  }).join("");

  if(!scored.length){
    return '<div class="planslot planslot-snack"><div class="ps-label">Snack</div>' +
      '<div class="empty">No snack recipes ready yet.</div></div>';
  }

  return '<div class="planslot planslot-snack"><div class="ps-label">Snack ' +
    '<span class="ps-hint">&middot; ranked to fit ' + esc(PW.PEOPLE[who].name) +
    '’s remaining ' + n0(Math.max(remaining.kcal, 0)) + ' kcal</span></div>' +
    '<div class="ps-list">' + body + '</div></div>';
}

function shoppingListHTML(){
  var lunch = PLAN.lunch ? recipeById(PLAN.lunch) : null;
  var dinner = PLAN.dinner ? recipeById(PLAN.dinner) : null;
  if(!lunch || !dinner) return "";
  var snack = PLAN.snack ? recipeById(PLAN.snack) : null;

  var fit = pairFit(lunch, dinner);
  var totals = {}, blocks = 0;
  var chosen = [lunch, dinner];
  if(snack) chosen.push(snack);
  chosen.forEach(function(r){
    blocks += (r.blocks || 0) * r.servings;
    (r.ingredients || []).forEach(function(i){
      totals[i.food] = (totals[i.food] || 0) + i.g;
    });
  });

  var rows = Object.keys(totals).sort(function(a,b){ return totals[b] - totals[a]; })
    .map(function(fid){
      return '<li><div class="t">' + esc(D.foodNames[fid] || fid) + '</div>' +
             '<div class="amt">' + n0(totals[fid]) + ' g</div></li>';
    }).join("");

  var lunchDays = lunch.servings/2, dinnerDays = dinner.servings/2;
  var mismatch = lunchDays !== dinnerDays
    ? '<div class="flag warn"><div class="ft">Different lengths</div><p>' +
      esc(lunch.title) + ' makes ' + (Math.round(lunchDays*10)/10) + ' day(s) of lunch for two, ' +
      esc(dinner.title) + ' makes ' + (Math.round(dinnerDays*10)/10) + ' day(s) of dinner. ' +
      'Cook the shorter one again partway through, or scale the batch by hand.</p></div>'
    : '';

  var closes = pairCloses(fit);
  var fitFlag = '<div class="flag' + (closes ? '' : ' warn') + '"><div class="ft">' +
    (closes ? 'This pair closes the day' : 'This pair does not close the day') + '</div><p>' +
    'Together: ' + n0(fit.kcal) + ' kcal, ' + n1(fit.p) + ' g protein (target ' + n0(fit.tP) +
    '), ' + n1(fit.fib) + ' g fibre (target ' + n0(fit.tFib) + '), ' + n1(fit.fat) +
    ' g fat (ceiling ' + n0(fit.tFatHi) + ') — both mirror meals combined.' +
    (closes ? '' : ' The gap is real — close it with a snack, or pick a different pairing above.') +
    '</p></div>';

  return mismatch + fitFlag +
    '<div class="card"><div class="ch"><span class="k">Shopping list</span>' +
    '<span class="meta">' + Object.keys(totals).length + ' items</span>' +
    '<span class="title">' + esc(lunch.title) + ' + ' + esc(dinner.title) +
      (snack ? ' + ' + esc(snack.title) : '') + '</span></div>' +
    '<ul class="ing">' + rows + '</ul>' +
    (blocks > 0 ? '<div class="rnote">Plus <strong>' + n0(blocks) + ' Asian Base Block' +
      (blocks === 1 ? '' : 's') + '</strong> — see Method below for the batch recipe.</div>' : '') +
    '</div>';
}

function plannerHTML(){
  return '<div class="card"><div class="ch"><span class="k">Plan the batch</span>' +
    '<span class="meta">pick lunch, dinner, snack</span></div>' +
    '<div class="planrow">' + slotHTML("lunch") + slotHTML("dinner") + '</div>' +
    snackSlotHTML() +
    '</div>' + shoppingListHTML();
}

function recipesHTML(who){
  var list = recipesFor(who);
  var head = '<div class="card"><div class="ch"><span class="k">Recipes</span>' +
    '<span class="meta">' + list.length + ' for ' + esc(PW.PEOPLE[who].name) + '</span></div>';

  if(!list.length){
    return head + '<div class="empty">Nothing here yet.</div>' +
      lookForHTML() + addNote() + '</div>';
  }

  return head + list.map(function(r){
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
  }).join("") + lookForHTML() + addNote() + '</div>';
}

function render(){
  document.getElementById("sub").textContent = base.purpose;

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

  var ing = '<div class="card"><div class="ch"><span class="k">Ingredients</span>' +
    '<span class="meta">' + n0(comp.batchTotal.calories) + ' kcal total</span>' +
    '<span class="title">Asian Base Block</span></div><ul class="ing">' +
    base.ingredients.map(function(i){
      return '<li><div class="t">' + esc(i.item) + '</div>' +
             '<div class="amt">' + esc(i.amount) + '</div></li>';
    }).join("") + '</ul></div>';

  var steps = '<div class="card"><div class="ch"><span class="k">Method</span>' +
    '<span class="meta">' + esc(D.kitchen.hardware.device.split(" ").slice(0,2).join(" ")) + '</span></div>' +
    '<ol class="steps">' + base.steps.map(function(s,i){
      return '<li><span class="n">' + (i+1) + '</span><div class="t">' + esc(s) + '</div></li>';
    }).join("") + '</ol></div>';

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

  var extras =
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
      }).join("") + '</div></details>';

  document.getElementById("stage").innerHTML =
    ledgerHTML(PW.get()) + mealHTML() + plannerHTML() + recipesHTML(PW.get()) +
    splitter + estimated + ing + steps + extras;

  var input = document.getElementById("w");
  input.addEventListener("input", function(){
    var v = parseFloat(input.value);
    if(!(v > 0)) return;
    weight = v; saveWeight(v);
    var card = input.closest(".card");
    card.querySelector(".split").outerHTML = splitHTML();
  });
}

/* Delegated once on the stage, not inside render() — the buttons are replaced
   on every render(), but the stage element itself is not. */
document.getElementById("stage").addEventListener("click", function(ev){
  var pick = ev.target.closest(".dishpick");
  if(pick){
    PLAN[pick.dataset.slot] = pick.dataset.id;
    savePlan(PLAN);
    render();
    return;
  }
  var change = ev.target.closest(".ps-change");
  if(change){
    PLAN[change.dataset.slot] = null;
    savePlan(PLAN);
    render();
  }
});

PW.mountRail();
PW.mountThemeToggle(document.getElementById("switcher"));
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

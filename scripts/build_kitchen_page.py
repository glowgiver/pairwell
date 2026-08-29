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

data = {
    "kitchen": json.load(open(KITCHEN, encoding="utf-8")),
    "profiles": json.load(open(PROFILES, encoding="utf-8")),
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
/* mirrorMeals.fatG is the range "12-15", deliberately. Print it, do not round it. */
function g(v){ return isFinite(v) ? n0(v) : String(v); }

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
  ["lunch","dinner"].forEach(function(k){
    var m = mm[k];
    rows.push({ label:k.charAt(0).toUpperCase()+k.slice(1), tag:"mirror",
                kcal:m.calories, p:m.proteinG, fib:m.fiberG, fat:m.fatG });
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
  var fatLo = parseFloat(String(m.fatG).split("-")[0]);
  return {
    blocks: blocks,
    from:  { kcal:pb.calories*blocks, p:pb.proteinG*blocks,
             fib:pb.fiberG*blocks, fat:pb.fatG*blocks },
    need:  { kcal:m.calories - pb.calories*blocks,
             p:  m.proteinG - pb.proteinG*blocks,
             fib:m.fiberG   - pb.fiberG*blocks,
             fat:fatLo      - pb.fatG*blocks }
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
        '<span>F <b>' + n1(r.need.fat) + ' g</b></span></div></div>' +
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
    'file. The ingredients and amounts as you found them, or just a photo of them; ' +
    'they get fitted to the target from there.' +
    '<span class="path">Files \u203a iCloud Drive \u203a Pairwell \u203a inbox</span></div>';
}

/* What to hunt for. The envelope is derived from the same two files the rest of
   the page uses, so it cannot quietly disagree with the target it describes. */
function lookForHTML(){
  var r = mealRemainder();
  var fat = String(D.profiles.mirrorMeals.lunch.fatG).split("-");
  var fatLo = parseFloat(fat[0]) - comp.perBlock.fatG * r.blocks;
  var fatHi = parseFloat(fat[fat.length - 1]) - comp.perBlock.fatG * r.blocks;

  function list(items){
    return '<ul>' + items.map(function(t){ return '<li>' + t + '</li>'; }).join("") + '</ul>';
  }

  return '<details><summary>What to look for</summary><div class="brief">' +
    '<div class="env">' + n0(r.need.kcal) + ' kcal · ' + n0(r.need.p) + ' g protein · ' +
      n0(r.need.fib) + ' g fibre · ' + n0(fatLo) + '–' + n0(fatHi) + ' g fat</div>' +
    '<p>Per serving, the dish on its own — ' + n1(r.blocks) + ' Base block is already ' +
      'going on the plate beside it, so the recipe should bring no rice, noodles or potato ' +
      'of its own.</p>' +

    '<h4>The shape that fits</h4>' +
    list(['~100–150 g lean protein',
          '~100 g cooked legume — fibre that fits in a box',
          '~200 g quick greens or mushrooms — volume, cheap in calories',
          'an aromatic sauce with almost no fat']) +
    '<p>Never one fibre source alone: ' + n0(r.need.fib) + ' g of it from lentils costs about ' +
      '180 kcal, half the budget, and the same from spinach is over half a kilo of spinach. ' +
      'The legume and the greens also carry around 15 g of protein between them, which is ' +
      'why the meat portion is smaller than it looks.</p>' +

    '<h4>Works</h4>' +
    list(['Cod, prawns, turkey, chicken breast, pork fillet',
          'Braises and one-pot stews — Taiwanese, Vietnamese, Japanese',
          'Stir-fries heavy on vegetables, with a weighable protein portion',
          'Sauce on stock, soy, vinegar, mustard, tomato or quark']) +

    '<h4>Too rich to fit</h4>' +
    list(['Coconut milk, cream, cheese sauce, peanut or satay',
          'Deep-fried, battered, breaded',
          'Salmon or tofu as the only protein — both leave no room for the fibre',
          'Salads that reach their fibre through sheer volume',
          'Protein minced into a mixture, so no portion can be weighed']) +

    '<h4>What to write down</h4>' +
    '<p>The ingredients in grams, and the method. Skip the nutrition panel — every ' +
      'figure here is worked out from the ingredients, so a number copied off a website ' +
      'is at best ignored and at worst believed by mistake.</p>' +
    '</div></details>';
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
    ledgerHTML(PW.get()) + mealHTML() + recipesHTML(PW.get()) +
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

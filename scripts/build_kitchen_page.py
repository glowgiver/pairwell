"""Build hub/kitchen/index.html from kitchen.json + profiles.json.

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
OUT = os.path.join(BASE, "..", "hub", "kitchen", "index.html")

data = {
    "kitchen": json.load(open(KITCHEN, encoding="utf-8")),
    "profiles": json.load(open(PROFILES, encoding="utf-8")),
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

  document.getElementById("stage").innerHTML = splitter + estimated + ing + steps + extras;

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
</script>

</body>
</html>
"""

html = HTML.replace("__DATA__", data_json)\
        .replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written kitchen/index.html  (%d bytes)" % len(html))

import hashlib, json, os

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "..", "data", "style.json")
OUT_PATH = os.path.join(BASE, "..", "hub", "style", "index.html")

data = json.load(open(DATA_PATH, encoding="utf-8"))
data_json = json.dumps(data, ensure_ascii=False)

def _digest(rel):
    """Content hash for a shared asset, so a stale HTTP cache entry cannot
    outlive a change."""
    p = os.path.join(BASE, "..", "hub", rel)
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:8]

ASSET_V = {"css": _digest("app.css"), "js": _digest("app.js")}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Style · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css?v=__CSSV__">
<style>
  /* Palette lives in ../app.css — only the accent choice is page-local. */
  :root{ --accent:var(--style); }

  body{
    background:var(--bg);
    color:var(--text);
    font-family:var(--f-ui);
    -webkit-font-smoothing:antialiased;
    min-height:100dvh;
    padding:
      calc(env(safe-area-inset-top) + 22px)
      calc(env(safe-area-inset-right) + 16px)
      calc(var(--bar) + 26px)
      calc(env(safe-area-inset-left) + 16px);
    max-width:640px;
    margin:0 auto;
  }

  h1{font-size:27px;font-weight:700;letter-spacing:-.02em;margin:0 0 4px;color:var(--accent)}
  .sub{font-family:var(--f-read);font-size:15px;color:var(--muted);margin:0 0 20px;line-height:1.55}

  .empty{padding:22px 18px;font-family:var(--f-read);font-size:15px;
    color:var(--muted);line-height:1.6;border:1px solid var(--line);
    border-radius:14px;background:var(--surface)}
  .empty strong{color:var(--text)}

  .ref-card{margin-bottom:16px;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:var(--surface)}
  .ref-head{padding:14px 16px;border-bottom:1px solid var(--line);background:var(--surface-2)}
  .ref-title{font-size:18px;font-weight:700}
  .ref-intro{font-family:var(--f-read);font-size:14.5px;color:var(--muted);margin-top:4px;line-height:1.55}
  .ref-body{padding:4px 16px}
  .ref-item{display:grid;grid-template-columns:104px 1fr;gap:10px;padding:10px 0;border-bottom:1px solid var(--line)}
  .ref-item:last-child{border-bottom:none}
  .ref-item-k{font-family:var(--f-data);font-size:13px;font-weight:700;color:var(--accent)}
  .ref-item-v{font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.55}
  .ref-item-v strong{color:var(--text)}

  .tagrow{display:flex;flex-wrap:wrap;gap:7px;padding:12px 16px 14px}
  .tag{
    font-family:var(--f-data);font-size:13px;padding:5px 10px;border-radius:20px;
    background:var(--surface-2);border:1px solid var(--line);color:var(--text);
  }

  .note{padding:11px 16px 14px;font-family:var(--f-read);font-size:14.5px;
    color:var(--muted);line-height:1.55;border-top:1px solid var(--line)}
  .note strong{color:var(--text)}

  /* Seasons — one sub-card per calendar season, inside the wardrobe card. */
  .season{padding:13px 16px;border-bottom:1px solid var(--line)}
  .season:last-child{border-bottom:none}
  .season-h{font-size:15.5px;font-weight:700;display:flex;align-items:baseline;gap:8px}
  .season-h .heading{font-family:var(--f-read);font-style:italic;font-weight:400;font-size:13.5px;color:var(--muted2)}
  .season dl{margin:8px 0 0;display:grid;grid-template-columns:auto 1fr;gap:4px 10px}
  .season dt{font-family:var(--f-data);font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2);white-space:nowrap}
  .season dd{margin:0;font-family:var(--f-read);font-size:14.5px;color:var(--text);line-height:1.5}

  /* Brands */
  .brandrow{display:flex;justify-content:space-between;gap:12px;padding:10px 16px;border-bottom:1px solid var(--line)}
  .brandrow:last-child{border-bottom:none}
  .brandrow .bn{font-weight:600;font-size:15px}
  .brandrow .bc{font-family:var(--f-data);font-size:13px;color:var(--muted2);text-align:right}

  /* Chino plan */
  .plan-item{padding:12px 16px;border-bottom:1px solid var(--line)}
  .plan-item:last-child{border-bottom:none}
  .plan-item .pi-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
  .plan-item .pi-name{font-weight:700;font-size:15px}
  .plan-item .pi-status{font-family:var(--f-data);font-size:12px;font-weight:600;
    text-transform:uppercase;letter-spacing:.04em;padding:2px 8px;border-radius:20px;
    background:var(--surface-2);color:var(--accent);white-space:nowrap}
  .plan-item .pi-detail{font-family:var(--f-read);font-size:14px;color:var(--muted);margin-top:4px;line-height:1.5}
  .plan-item .pi-detail b{color:var(--text);font-weight:600}

  /* Outfit planner */
  .outfitrow{padding:12px 16px;border-bottom:1px solid var(--line)}
  .outfitrow:last-child{border-bottom:none}
  .outfitrow .or-day{font-family:var(--f-data);font-size:13px;font-weight:700;
    text-transform:uppercase;letter-spacing:.05em;color:var(--accent)}
  .outfitrow .or-body{margin-top:5px}
  .outfitrow dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:3px 10px}
  .outfitrow dt{font-family:var(--f-data);font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2)}
  .outfitrow dd{margin:0;font-family:var(--f-read);font-size:14.5px;color:var(--text)}
  .outfitrow .or-empty{font-family:var(--f-read);font-size:14px;font-style:italic;color:var(--muted2);margin-top:4px}

  @media (prefers-reduced-motion:reduce){ * { transition:none !important } }
</style>
</head>
<body>

<div class="pw-bar">
  <a class="pw-back" href="../"><svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg> Hub</a>
  <div id="switcher"></div>
</div>

<h1>Style</h1>
<p class="sub">Color type, wardrobe, brands, sizes — a lookup, not a checklist.</p>

<div id="stage"></div>

<script src="../app.js?v=__JSV__"></script>
<script>
const S = __DATA__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

function person(){ return PW.get(); }
function profile(){ return S[person()]; }

function colorAnalysisCard(c){
  if(!c) return "";
  var rows = [
    ["Traits", c.traits], ["Skin", c.skin], ["Tan", c.tan],
    ["Brows/lashes", c.browsLashes], ["Eyes", c.eyes]
  ].filter(function(r){ return r[1]; }).map(function(r){
    return '<div class="ref-item"><div class="ref-item-k">' + esc(r[0]) + '</div>' +
      '<div class="ref-item-v">' + esc(r[1]) + '</div></div>';
  }).join("");

  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Color analysis — ' + esc(c.type) + '</div>' +
    (c.note ? '<div class="ref-intro">' + esc(c.note) + '</div>' : '') +
    '</div><div class="ref-body">' + rows + '</div>' +
    (c.colors && c.colors.length
      ? '<div class="tagrow">' + c.colors.map(function(col){
          return '<span class="tag">' + esc(col) + '</span>';
        }).join("") + '</div>'
      : "") +
    (c.avoid ? '<div class="note"><strong>Avoid:</strong> ' + esc(c.avoid) + '</div>' : '') +
    '</div>';
}

function seasonalWardrobeCard(w){
  if(!w) return "";
  var FIELDS = [
    ["tops", "Tops"], ["outerwear", "Outerwear"], ["bottoms", "Bottoms"],
    ["shoes", "Shoes"], ["accessories", "Accessories"]
  ];
  var seasons = (w.seasons || []).map(function(s){
    var dl = FIELDS.filter(function(f){ return s[f[0]]; }).map(function(f){
      return '<dt>' + esc(f[1]) + '</dt><dd>' + esc(s[f[0]]) + '</dd>';
    }).join("");
    return '<div class="season"><div class="season-h">' + esc(s.season) +
      (s.heading ? '<span class="heading">' + esc(s.heading) + '</span>' : '') +
      '</div><dl>' + dl + '</dl></div>';
  }).join("");

  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Seasonal wardrobe</div>' +
    (w.paletteNote ? '<div class="ref-intro">' + esc(w.paletteNote) + '</div>' : '') +
    '</div>' + seasons +
    (w.styleNote ? '<div class="note">' + esc(w.styleNote) + '</div>' : '') +
    (w.note ? '<div class="note">' + esc(w.note) + '</div>' : '') +
    '</div>';
}

function brandsCard(brands){
  if(!brands || !brands.length) return "";
  var rows = brands.map(function(b){
    return '<div class="brandrow"><span class="bn">' + esc(b.name) + '</span>' +
      (b.category ? '<span class="bc">' + esc(b.category) + '</span>' : '') + '</div>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Brands</div></div>' + rows + '</div>';
}

function sizeCard(sz){
  if(!sz) return "";
  var FIELDS = [
    ["collar", "Collar"], ["armLength", "Arm length"], ["shoulder", "Shoulder"],
    ["chest", "Chest"], ["waist", "Waist"], ["hip", "Hip"],
    ["sleeveLength", "Sleeve"], ["shirtLength", "Shirt length"]
  ];
  var rows = FIELDS.filter(function(f){ return sz[f[0]]; }).map(function(f){
    return '<div class="ref-item"><div class="ref-item-k">' + esc(f[1]) + '</div>' +
      '<div class="ref-item-v">' + esc(sz[f[0]]) + '</div></div>';
  }).join("");
  var notes = (sz.notes || []).map(function(n){
    return '<div class="note">' + esc(n) + '</div>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Size</div></div>' +
    '<div class="ref-body">' + rows + '</div>' + notes + '</div>';
}

function chinoPlanCard(p){
  if(!p) return "";
  var purchases = (p.purchases || []).map(function(x){
    return '<div class="plan-item"><div class="pi-head">' +
      '<span class="pi-name">' + esc(x.brand) + ' — ' + esc(x.model) + '</span>' +
      (x.status ? '<span class="pi-status">' + esc(x.status) + '</span>' : '') + '</div>' +
      '<div class="pi-detail"><b>Colors:</b> ' + esc(x.colors) + '</div>' +
      (x.priceNew ? '<div class="pi-detail"><b>Price:</b> ' + esc(x.priceNew) + ' · ' + esc(x.whereNew) + '</div>' : '') +
      (x.secondHandSearch ? '<div class="pi-detail"><b>Second-hand:</b> ' + esc(x.secondHandSearch) + '</div>' : '') +
      '</div>';
  }).join("");
  var roadmap = (p.roadmap || []).map(function(x){
    return '<div class="plan-item"><div class="pi-head">' +
      '<span class="pi-name">' + esc(x.phase) + '</span>' +
      (x.status ? '<span class="pi-status">' + esc(x.status) + '</span>' : '') + '</div>' +
      '<div class="pi-detail"><b>' + esc(x.item) + '</b> — ' + esc(x.colors) + '</div>' +
      (x.purpose ? '<div class="pi-detail">' + esc(x.purpose) + '</div>' : '') +
      '</div>';
  }).join("");

  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Chino plan</div>' +
    '<div class="ref-intro">' + esc(p.goal) + '</div></div>' +
    '<div class="ref-body">' +
    (p.midGoal ? '<div class="ref-item"><div class="ref-item-k">Interim</div><div class="ref-item-v">' + esc(p.midGoal) + '</div></div>' : "") +
    (p.fit ? '<div class="ref-item"><div class="ref-item-k">Fit</div><div class="ref-item-v">' + esc(p.fit) + '</div></div>' : "") +
    '</div>' + purchases + roadmap + '</div>';
}

function outfitPlannerCard(op){
  if(!op || !op.days) return "";
  var FIELDS = [
    ["top", "Top"], ["bottom", "Bottom"], ["shoes", "Shoes"],
    ["accessories", "Accessories"], ["outerwear", "Outerwear"]
  ];
  var rows = op.days.map(function(d){
    var filled = FIELDS.filter(function(f){ return d[f[0]]; });
    var body = filled.length
      ? '<dl>' + filled.map(function(f){
          return '<dt>' + esc(f[1]) + '</dt><dd>' + esc(d[f[0]]) + '</dd>';
        }).join("") + '</dl>'
      : '<div class="or-empty">Not planned yet</div>';
    return '<div class="outfitrow"><div class="or-day">' + esc(d.day) + '</div>' +
      '<div class="or-body">' + body + '</div></div>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Outfit planner</div></div>' + rows + '</div>';
}

function renderStage(){
  var stage = document.getElementById("stage");
  var p = profile();

  if(!p){
    stage.innerHTML = '<div class="empty"><strong>No style profile yet</strong> for ' +
      esc(PW.PEOPLE[person()].name) + '. Philipp\\'s is the first one in — Eunice\\'s ' +
      'gets added the same way once there is something to transcribe.</div>';
    return;
  }

  stage.innerHTML =
    colorAnalysisCard(p.colorAnalysis) +
    seasonalWardrobeCard(p.seasonalWardrobe) +
    brandsCard(p.brands) +
    sizeCard(p.size) +
    chinoPlanCard(p.chinoPlan) +
    outfitPlannerCard(p.outfitPlanner);
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs("style", "../");

window.addEventListener("pw:person", renderStage);

renderStage();
</script>

</body>
</html>
"""

html = html.replace("__DATA__", data_json)\
        .replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Wrote", OUT_PATH, "(" + str(len(html)) + " bytes)")

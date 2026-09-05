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
  /* Stacked first. Several values here are full paragraphs, and a fixed label
     column on a 375px screen leaves them about 215px wide — a text ribbon.
     The side-by-side form is an enhancement for wider screens only. */
  .ref-item{padding:10px 0;border-bottom:1px solid var(--line)}
  .ref-item:last-child{border-bottom:none}
  .ref-item-k{font-family:var(--f-data);font-size:13px;font-weight:700;color:var(--accent)}
  .ref-item-v{font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.55;margin-top:3px}
  .ref-item-v strong{color:var(--text)}

  /* Short values — measurements — keep the label column at every width,
     because "38 cm" on its own line is wasted space, not clarity. */
  .ref-item.compact{display:grid;grid-template-columns:104px 1fr;gap:10px;align-items:baseline}
  .ref-item.compact .ref-item-v{margin-top:0}

  @media (min-width:480px){
    .ref-item{display:grid;grid-template-columns:120px 1fr;gap:12px;align-items:baseline}
    .ref-item .ref-item-v{margin-top:0}
  }

  .tagrow{display:flex;flex-wrap:wrap;gap:7px;padding:12px 16px 14px}
  .tag{
    font-family:var(--f-data);font-size:13px;padding:5px 10px;border-radius:20px;
    background:var(--surface-2);border:1px solid var(--line);color:var(--text);
  }

  .note{padding:11px 16px 14px;font-family:var(--f-read);font-size:14.5px;
    color:var(--muted);line-height:1.55;border-top:1px solid var(--line)}
  .note strong{color:var(--text)}

  /* Colour swatches. The name always sits BESIDE the chip, never on it —
     these are arbitrary wardrobe colours, so no contrast ratio against them
     can be guaranteed and text on top would be a coin flip. */
  .sw{display:flex;flex-wrap:wrap;gap:10px 14px;padding:13px 16px 15px}
  .sw-item{display:flex;align-items:center;gap:8px;min-height:24px}
  /* Outlined with --muted2, not --line: half this palette is deep navy and
     charcoal, which vanish against the dark card if the ring is as faint as
     a divider. --muted2 is a mid-tone that holds in both themes. */
  .sw-dot{width:20px;height:20px;border-radius:6px;border:1px solid var(--muted2);flex:none}
  .sw-name{font-family:var(--f-data);font-size:13px;color:var(--text);white-space:nowrap}
  .sw-why{font-family:var(--f-read);font-size:13px;color:var(--muted2);line-height:1.4}
  /* When each swatch carries a reason, one per row — inline flow turned the
     two-word names into two-line names. */
  .sw.reasons{gap:11px}
  .sw.reasons .sw-item{width:100%;align-items:baseline}
  .sw.reasons .sw-dot{align-self:center}
  .sw-label{
    font-family:var(--f-data);font-size:12.5px;font-weight:700;letter-spacing:.09em;
    text-transform:uppercase;color:var(--muted2);padding:12px 16px 0;
  }
  /* One level below .sw-label — the two branches of an unresolved question,
     which are subordinate to it rather than siblings of Core and Avoid. */
  .sw-sub{
    font-family:var(--f-data);font-size:13px;font-weight:600;
    color:var(--accent);padding:10px 16px 0;
  }

  /* Silhouette rules — the rule reads as a heading, the reason underneath it. */
  .rule{padding:12px 16px;border-bottom:1px solid var(--line)}
  .rule:last-child{border-bottom:none}
  .rule-r{font-size:15px;font-weight:700;line-height:1.35}
  .rule-w{font-family:var(--f-read);font-size:14.5px;color:var(--muted);
    margin-top:4px;line-height:1.55}

  /* Buy next — ordered, because the order is the advice. */
  .buy{list-style:none;margin:0;padding:4px 0}
  .buy li{display:grid;grid-template-columns:26px 1fr;gap:12px;
    padding:12px 16px;align-items:baseline;border-bottom:1px solid var(--line)}
  .buy li:last-child{border-bottom:none}
  .buy .n{font-family:var(--f-data);font-size:15px;font-weight:700;color:var(--accent);
    font-variant-numeric:tabular-nums}
  .buy .t{font-size:15.5px;font-weight:700}
  .buy .c{font-family:var(--f-data);font-size:13px;color:var(--muted2);margin-top:2px}
  .buy .p{font-family:var(--f-read);font-size:14.5px;color:var(--muted);
    margin-top:5px;line-height:1.55}

  /* Reference figures */
  .refperson{padding:11px 16px;border-bottom:1px solid var(--line)}
  .refperson:last-child{border-bottom:none}
  .refperson .rp-n{font-size:15px;font-weight:700}
  .refperson .rp-w{font-family:var(--f-read);font-size:14.5px;color:var(--muted);
    margin-top:3px;line-height:1.55}

  /* A revision note — something that was deliberately changed, with the reason.
     Same shape as .note but marked, so it does not read as original source. */
  .rev{padding:12px 16px;border-top:1px solid var(--line);background:var(--surface-2)}
  .rev-t{font-family:var(--f-data);font-size:12.5px;font-weight:700;letter-spacing:.08em;
    text-transform:uppercase;color:var(--accent)}
  .rev p{margin:5px 0 0;font-family:var(--f-read);font-size:14.5px;
    color:var(--muted);line-height:1.55}
  .rev p strong{color:var(--text)}

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
<p class="sub">Direction, palette, silhouette, sizes — a lookup, not a checklist.</p>

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

/* The frame everything else is read through, so it comes first. */
function directionCard(d){
  if(!d) return "";
  var refs = (d.references || []).map(function(r){
    return '<div class="refperson"><div class="rp-n">' + esc(r.name) + '</div>' +
      '<div class="rp-w">' + esc(r.why) + '</div></div>';
  }).join("");

  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Direction — ' + esc(d.register) + '</div>' +
    (d.thesis ? '<div class="ref-intro">' + esc(d.thesis) + '</div>' : '') +
    '</div><div class="ref-body">' +
    (d.builtFrom ? '<div class="ref-item"><div class="ref-item-k">Built from</div>' +
      '<div class="ref-item-v">' + esc(d.builtFrom) + '</div></div>' : '') +
    (d.ageRead ? '<div class="ref-item"><div class="ref-item-k">Age read</div>' +
      '<div class="ref-item-v">' + esc(d.ageRead) + '</div></div>' : '') +
    (d.readOfCurrentPhotos ? '<div class="ref-item"><div class="ref-item-k">Where it stands</div>' +
      '<div class="ref-item-v">' + esc(d.readOfCurrentPhotos) + '</div></div>' : '') +
    '</div>' +
    (refs
      ? '<div class="sw-label">Reference</div>' +
        (d.referencesNote ? '<div class="rule-w" style="padding:0 16px 6px">' + esc(d.referencesNote) + '</div>' : '') +
        refs
      : '') +
    (d.onTheOriginalFraming
      ? '<div class="rev"><div class="rev-t">On the framing</div><p>' + esc(d.onTheOriginalFraming) + '</p></div>'
      : '') +
    (d.notThis
      ? '<div class="rev"><div class="rev-t">Not this — ' + esc(d.notThis.register) + '</div>' +
        '<p>' + esc(d.notThis.why) + '</p></div>'
      : '') +
    '</div>';
}

/* Its own card rather than a line in Direction, because it is the one change
   that outranks every garment on the page. */
function hairCard(h){
  if(!h) return "";
  var rows = [
    ["Now", h.current], ["Cut", h.cut], ["Shape", h.shape],
    ["Color", h.color], ["Product", h.product]
  ].filter(function(r){ return r[1]; }).map(function(r){
    return '<div class="ref-item"><div class="ref-item-k">' + esc(r[0]) + '</div>' +
      '<div class="ref-item-v">' + esc(r[1]) + '</div></div>';
  }).join("");

  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Hair — the biggest lever</div>' +
    (h.priority ? '<div class="ref-intro">' + esc(h.priority) + '</div>' : '') +
    '</div><div class="ref-body">' + rows + '</div>' +
    (h.why ? '<div class="note">' + esc(h.why) + '</div>' : '') +
    '</div>';
}

function swatches(list, withWhy){
  return '<div class="sw' + (withWhy ? ' reasons' : '') + '">' + list.map(function(c){
    return '<div class="sw-item">' +
      '<span class="sw-dot" style="background:' + esc(c.hex) + '"></span>' +
      '<span class="sw-name">' + esc(c.name) + '</span>' +
      (withWhy && c.why ? '<span class="sw-why">' + esc(c.why) + '</span>' : '') +
      '</div>';
  }).join("") + '</div>';
}

function paletteCard(p){
  if(!p) return "";

  /* Split deliberately: what is settled sits above what is still a coin toss,
     and the conditional block says outright that it is unresolved rather than
     presenting two half-palettes as if either were the answer. */
  var cond = "";
  if(p.conditional){
    var c = p.conditional;
    cond = '<div class="sw-label">Depends on the undertone</div>' +
      (c.note ? '<div class="rule-w" style="padding:0 16px 4px">' + esc(c.note) + '</div>' : '') +
      (c.ifWarm ? '<div class="sw-sub">If warm — Dark Autumn</div>' + swatches(c.ifWarm, false) : '') +
      (c.ifCool ? '<div class="sw-sub">If cool — Dark Winter</div>' + swatches(c.ifCool, false) : '');
  }

  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Palette — ' + esc(p.type) + '</div>' +
    (p.rule ? '<div class="ref-intro">' + esc(p.rule) + '</div>' : '') +
    '</div><div class="ref-body">' +
    (p.established ? '<div class="ref-item"><div class="ref-item-k">Settled</div>' +
      '<div class="ref-item-v">' + esc(p.established) + '</div></div>' : '') +
    (p.open ? '<div class="ref-item"><div class="ref-item-k">Still open</div>' +
      '<div class="ref-item-v">' + esc(p.open) + '</div></div>' : '') +
    '</div>' +
    (p.core ? '<div class="sw-label">Core — safe either way</div>' + swatches(p.core, false) : '') +
    cond +
    (p.avoid ? '<div class="sw-label">Avoid</div>' + swatches(p.avoid, true) : '') +
    (p.confidence
      ? '<div class="rev"><div class="rev-t">Confidence</div><p>' + esc(p.confidence) + '</p></div>'
      : '') +
    '</div>';
}

function silhouetteCard(s){
  if(!s || !s.rules) return "";
  var rules = s.rules.map(function(r){
    return '<div class="rule"><div class="rule-r">' + esc(r.rule) + '</div>' +
      '<div class="rule-w">' + esc(r.why) + '</div></div>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Silhouette</div>' +
    '<div class="ref-intro">Six rules. They do more work than any single garment.</div>' +
    '</div>' + rules + '</div>';
}

function buyNextCard(list){
  if(!list || !list.length) return "";
  var items = list.map(function(b, i){
    return '<li><span class="n">' + (i + 1) + '</span><div>' +
      '<div class="t">' + esc(b.item) + '</div>' +
      (b.colors ? '<div class="c">' + esc(b.colors) + '</div>' : '') +
      (b.why ? '<div class="p">' + esc(b.why) + '</div>' : '') +
      '</div></li>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head">' +
    '<div class="ref-title">Buy next</div>' +
    '<div class="ref-intro">In this order. The order is the advice.</div>' +
    '</div><ul class="buy">' + items + '</ul></div>';
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
    return '<div class="brandrow"><div><span class="bn">' + esc(b.name) + '</span>' +
      (b.note ? '<div class="rule-w">' + esc(b.note) + '</div>' : '') + '</div>' +
      (b.category ? '<span class="bc">' + esc(b.category) + '</span>' : '') + '</div>';
  }).join("");
  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Brands</div></div>' + rows + '</div>';
}

function sizeCard(sz){
  if(!sz) return "";
  var FIELDS = [
    ["collar", "Collar"], ["shoulder", "Shoulder"], ["chest", "Chest"],
    ["belly", "Belly"], ["waist", "Waist"], ["hip", "Hip"],
    ["armLength", "Arm length"], ["sleeveLength", "Sleeve"],
    ["shirtLength", "Shirt length"]
  ];
  var rows = FIELDS.filter(function(f){ return sz[f[0]]; }).map(function(f){
    return '<div class="ref-item compact"><div class="ref-item-k">' + esc(f[1]) + '</div>' +
      '<div class="ref-item-v"><strong>' + esc(sz[f[0]]) + '</strong></div></div>';
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

  var rev = p.revision
    ? '<div class="rev"><div class="rev-t">Revised ' + esc(p.revision.date) + '</div>' +
      '<p><strong>' + esc(p.revision.change) + '</strong></p>' +
      '<p>' + esc(p.revision.why) + '</p></div>'
    : "";

  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Chino plan</div>' +
    '<div class="ref-intro">' + esc(p.goal) + '</div></div>' +
    rev +
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
  return '<div class="ref-card"><div class="ref-head"><div class="ref-title">Outfit planner</div>' +
    (op.note ? '<div class="ref-intro">' + esc(op.note) + '</div>' : '') +
    '</div>' + rows + '</div>';
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

  /* Ordered by how much each one changes, not by how the source notes were
     filed: direction frames everything, hair outranks any garment, palette and
     silhouette are the rules, and only then the things you actually buy. */
  stage.innerHTML =
    directionCard(p.direction) +
    hairCard(p.hair) +
    paletteCard(p.palette) +
    silhouetteCard(p.silhouette) +
    buyNextCard(p.buyNext) +
    seasonalWardrobeCard(p.seasonalWardrobe) +
    chinoPlanCard(p.chinoPlan) +
    brandsCard(p.brands) +
    sizeCard(p.size) +
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

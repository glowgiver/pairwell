import hashlib, json, os

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "..", "data", "style.json")
OUT_PATH = os.path.join(BASE, "..", "hub", "style", "index.html")

data = json.load(open(DATA_PATH, encoding="utf-8"))


def strip_private(node):
    """Drop every key starting with "_" before the data is inlined.

    Those keys are repo bookkeeping — _source, _revised, _gaps, _undertone,
    size._note — and no renderer reads one. Until now the build inlined the
    file wholesale, so all of it shipped to a public site inside a page that
    never displayed a character of it.

    That is worth fixing for its own sake, but the real reason is the shape of
    the mistake it invites: this repository keeps notes-to-self in the same
    file as the data, and `_excluded` exists precisely to record something
    that must not become public. A build that inlines whatever it is handed
    makes the next such note a publishing decision nobody remembers making.
    Prefixing a key is now the way to keep it in the repo and out of the page.
    """
    if isinstance(node, dict):
        return {k: strip_private(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [strip_private(v) for v in node]
    return node


data_json = json.dumps(strip_private(data), ensure_ascii=False)

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

  /* Jump bar. Ten cards is roughly seven screens, and the two things looked up
     most often in a shop — Size and Brands — sit at the bottom because the
     reading order is by importance, not by how often you need it. Rather than
     fight that, this gives every card a one-tap address. It scrolls
     horizontally and is built from the cards actually rendered, so it cannot
     drift out of step with them. */
  .jump{
    display:flex;gap:8px;overflow-x:auto;overscroll-behavior-x:contain;
    margin:0 -16px 18px;padding:2px 16px 6px;
    scrollbar-width:none;-webkit-overflow-scrolling:touch;
  }
  .jump::-webkit-scrollbar{display:none}
  .jump a{
    flex:none;display:inline-flex;align-items:center;min-height:var(--tap);
    padding:0 14px;border-radius:22px;text-decoration:none;
    background:var(--surface);border:1px solid var(--line);
    font-family:var(--f-data);font-size:15px;color:var(--muted);
  }
  .jump a:active{background:var(--surface-2);color:var(--text)}
  .jump a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  /* The top bar is sticky, so an anchor that lands flush at the viewport top
     lands underneath it. Its height is min-height var(--tap) plus 8px of
     padding either side. */
  .ref-card{
    margin-bottom:16px;border:1px solid var(--line);border-radius:14px;
    overflow:hidden;background:var(--surface);
    scroll-margin-top:calc(var(--tap) + 26px);
  }
  .ref-head{padding:14px 16px;border-bottom:1px solid var(--line);background:var(--surface-2)}
  /* A real h2, not a styled div: this page is ten sections of reference text
     and without headings it has no outline to navigate by at all. */
  .ref-title{font-size:18px;font-weight:700;margin:0;letter-spacing:-.01em}
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
  /* .sw-sub lived here for the two branches of the unresolved undertone
     question. The question is answered, there are no branches, and a rule
     nothing uses is worse than no rule. */

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

  /* Progressive disclosure, same shape the skincare page already uses. What
     goes in here is the read-once justification — why a recommendation was
     changed, how well supported it is. Real reference content never folds:
     hiding a colour or a measurement behind a tap would defeat the page. */
  details.fold{border-top:1px solid var(--line);background:var(--surface-2)}
  details.fold summary{
    min-height:var(--tap);display:flex;align-items:center;gap:9px;
    padding:11px 16px;cursor:pointer;list-style:none;
    font-family:var(--f-data);font-size:15px;font-weight:600;color:var(--muted);
  }
  details.fold summary::-webkit-details-marker{display:none}
  details.fold summary::after{
    content:"";margin-left:auto;width:8px;height:8px;flex:none;
    border-right:2px solid var(--muted2);border-bottom:2px solid var(--muted2);
    transform:rotate(45deg);transition:transform .18s ease;
  }
  details.fold[open] summary{color:var(--text)}
  details.fold[open] summary::after{transform:rotate(-135deg)}
  details.fold summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
  details.fold .rev{border-top:none;padding-top:0}
  details.fold .note{border-top:none}

  /* An intro paragraph belonging to a .sw-label section. Was an inline style
     repeated at three call sites. */
  .sect-note{font-family:var(--f-read);font-size:14.5px;color:var(--muted);
    line-height:1.55;padding:2px 16px 4px}

  /* Seasons — one sub-card per calendar season, inside the wardrobe card. */
  .season{padding:13px 16px;border-bottom:1px solid var(--line)}
  .season:last-child{border-bottom:none}
  /* Style is the only module with no notion of "today", which is why it is
     absent from the Today screen. The wardrobe is the one place a date does
     mean something, so the current season is marked — cheap, and it turns
     four blocks of text into one answer plus three for reference. */
  .season.now{background:var(--surface-2)}
  .season-h{font-size:15.5px;font-weight:700;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
  .season-h .now-pill{
    /* 13px, the secondary floor. The .pi-status pill nearby is 12px and
       predates the rule; new markup holds it. */
    font-family:var(--f-data);font-size:13px;font-weight:700;letter-spacing:.06em;
    text-transform:uppercase;padding:2px 8px;border-radius:20px;
    background:var(--accent);color:var(--bg);
  }
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

  /* Deliberately no scroll-behavior:smooth. This page is around fifteen
     screens tall, so animating a jump from the index to Size is a couple of
     seconds of blur on the way to somewhere you already chose. A jump link
     should jump; the browser's Back button restores the previous position. */
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

<main id="stage"></main>

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

/* Card functions return a card's INSIDE — head plus body. renderStage wraps
   each one in its <section> and derives the anchor id from the nav label, so
   the jump bar and the cards cannot disagree about what a section is called
   or whether it exists. Both arguments are HTML and are escaped by callers,
   because most titles are a literal joined to an escaped value. */
function head(title, intro){
  return '<div class="ref-head"><h2 class="ref-title">' + title + '</h2>' +
    (intro ? '<div class="ref-intro">' + intro + '</div>' : '') + '</div>';
}

/* For the read-once material: why something was changed, how well supported a
   call is. Never for a colour, a measurement or a rule. */
function fold(label, inner){
  if(!inner) return "";
  return '<details class="fold"><summary>' + esc(label) + '</summary>' + inner + '</details>';
}

function slug(s){
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

/* The frame everything else is read through, so it comes first. */
function directionCard(d){
  if(!d) return "";
  var refs = (d.references || []).map(function(r){
    return '<div class="refperson"><div class="rp-n">' + esc(r.name) + '</div>' +
      '<div class="rp-w">' + esc(r.why) + '</div></div>';
  }).join("");

  return head('Direction — ' + esc(d.register), d.thesis ? esc(d.thesis) : "") +
    '<div class="ref-body">' +
    (d.builtFrom ? '<div class="ref-item"><div class="ref-item-k">Built from</div>' +
      '<div class="ref-item-v">' + esc(d.builtFrom) + '</div></div>' : '') +
    (d.ageRead ? '<div class="ref-item"><div class="ref-item-k">Age read</div>' +
      '<div class="ref-item-v">' + esc(d.ageRead) + '</div></div>' : '') +
    (d.readOfCurrentPhotos ? '<div class="ref-item"><div class="ref-item-k">Where it stands</div>' +
      '<div class="ref-item-v">' + esc(d.readOfCurrentPhotos) + '</div></div>' : '') +
    '</div>' +
    (refs
      ? '<div class="sw-label">Reference</div>' +
        (d.referencesNote ? '<div class="sect-note">' + esc(d.referencesNote) + '</div>' : '') +
        refs
      : '') +
    /* "Not this" stays open — it is a rule about what to avoid, which is
       lookup content. The note about how this file came to be written is
       not, and folds. */
    (d.notThis
      ? '<div class="rev"><div class="rev-t">Not this — ' + esc(d.notThis.register) + '</div>' +
        '<p>' + esc(d.notThis.why) + '</p></div>'
      : '') +
    fold("How this was framed", d.onTheOriginalFraming
      ? '<div class="rev"><p>' + esc(d.onTheOriginalFraming) + '</p></div>'
      : "");
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

  return head('Hair — the biggest lever', h.priority ? esc(h.priority) : "") +
    '<div class="ref-body">' + rows + '</div>' +
    /* The reasoning stays open here on purpose: this card asks him to go to a
       barber and say something specific, and the why is what makes that
       worth doing. */
    (h.why ? '<div class="note">' + esc(h.why) + '</div>' : '');
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

  /* The undertone used to be an open question and this card used to say so,
     showing two half-palettes side by side under "if warm" / "if cool". The
     gold-versus-silver test settled it cool, so the shape changed with the
     answer: one palette, then the colours the answer took away. Keeping the
     ruled-out list visible is the point — camel and stone are what he would
     otherwise reach for, so the card has to say why they are gone, not just
     omit them. */
  function group(g, label, withWhy){
    if(!g || !g.colors) return "";
    return '<div class="sw-label">' + esc(label) + '</div>' +
      (g.note ? '<div class="sect-note">' + esc(g.note) + '</div>' : '') +
      swatches(g.colors, withWhy);
  }

  return head('Palette — ' + esc(p.type), p.rule ? esc(p.rule) : "") +
    '<div class="ref-body">' +
    (p.established ? '<div class="ref-item"><div class="ref-item-k">Colouring</div>' +
      '<div class="ref-item-v">' + esc(p.established) + '</div></div>' : '') +
    (p.resolved ? '<div class="ref-item"><div class="ref-item-k">Undertone</div>' +
      '<div class="ref-item-v">' + esc(p.resolved) + '</div></div>' : '') +
    (p.metal ? '<div class="ref-item"><div class="ref-item-k">Metal</div>' +
      '<div class="ref-item-v">' + esc(p.metal) + '</div></div>' : '') +
    '</div>' +
    (p.core ? '<div class="sw-label">Core</div>' + swatches(p.core, false) : '') +
    group(p.accent, "Accents", false) +
    group(p.ruledOut, "Ruled out by the undertone test", true) +
    (p.avoid ? '<div class="sw-label">Avoid — wrong at any undertone</div>' + swatches(p.avoid, true) : '') +
    fold("How solid is this?", p.confidence
      ? '<div class="rev"><p>' + esc(p.confidence) + '</p></div>'
      : "");
}

function silhouetteCard(s){
  if(!s || !s.rules) return "";
  var rules = s.rules.map(function(r){
    return '<div class="rule"><div class="rule-r">' + esc(r.rule) + '</div>' +
      '<div class="rule-w">' + esc(r.why) + '</div></div>';
  }).join("");
  /* The count came from counting the rules, so it is counted rather than
     written down — the sentence used to say "six" and the array is data. */
  return head('Silhouette', s.rules.length +
    ' rules. They do more work than any single garment.') + rules;
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
  return head('Buy next', 'In this order. The order is the advice.') +
    '<ol class="buy">' + items + '</ol>';
}

/* Meteorological seasons, northern hemisphere — the boundaries a wardrobe
   actually follows. Astronomical dates would put the first three weeks of
   September in Summer, which is not what anyone wears. */
function currentSeason(){
  return ["Winter","Winter","Spring","Spring","Spring","Summer",
          "Summer","Summer","Autumn","Autumn","Autumn","Winter"][new Date().getMonth()];
}

function seasonalWardrobeCard(w){
  if(!w) return "";
  var FIELDS = [
    ["tops", "Tops"], ["outerwear", "Outerwear"], ["bottoms", "Bottoms"],
    ["shoes", "Shoes"], ["accessories", "Accessories"]
  ];
  var now = currentSeason();
  var seasons = (w.seasons || []).map(function(s){
    var here = s.season === now;
    var dl = FIELDS.filter(function(f){ return s[f[0]]; }).map(function(f){
      return '<dt>' + esc(f[1]) + '</dt><dd>' + esc(s[f[0]]) + '</dd>';
    }).join("");
    return '<div class="season' + (here ? ' now' : '') + '"><div class="season-h">' +
      esc(s.season) +
      (here ? '<span class="now-pill">Now</span>' : '') +
      (s.heading ? '<span class="heading">' + esc(s.heading) + '</span>' : '') +
      '</div><dl>' + dl + '</dl></div>';
  }).join("");

  return head('Seasonal wardrobe', w.paletteNote ? esc(w.paletteNote) : "") +
    seasons +
    (w.styleNote ? '<div class="note">' + esc(w.styleNote) + '</div>' : '') +
    fold("What changed here", w.note ? '<div class="note">' + esc(w.note) + '</div>' : "");
}

function brandsCard(brands){
  if(!brands || !brands.length) return "";
  var rows = brands.map(function(b){
    return '<div class="brandrow"><div><span class="bn">' + esc(b.name) + '</span>' +
      (b.note ? '<div class="rule-w">' + esc(b.note) + '</div>' : '') + '</div>' +
      (b.category ? '<span class="bc">' + esc(b.category) + '</span>' : '') + '</div>';
  }).join("");
  return head('Brands', 'Where the sizes are already known.') + rows;
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
  return head('Size', 'The one card that gets opened in a shop.') +
    '<div class="ref-body">' + rows + '</div>' + notes;
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

  /* The change itself is one line and stays visible; the paragraph arguing
     for it is what folds. Moved below the plan too — it used to sit between
     the heading and the fit, so the first thing this card said was a note
     about its own edit history. */
  var rev = p.revision
    ? fold("Revised " + p.revision.date,
        '<div class="rev"><p><strong>' + esc(p.revision.change) + '</strong></p>' +
        '<p>' + esc(p.revision.why) + '</p></div>')
    : "";

  return head('Chino plan', esc(p.goal)) +
    '<div class="ref-body">' +
    (p.midGoal ? '<div class="ref-item"><div class="ref-item-k">Interim</div><div class="ref-item-v">' + esc(p.midGoal) + '</div></div>' : "") +
    (p.fit ? '<div class="ref-item"><div class="ref-item-k">Fit</div><div class="ref-item-v">' + esc(p.fit) + '</div></div>' : "") +
    '</div>' + purchases + roadmap + rev;
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
  return head('Outfit planner', op.note ? esc(op.note) : "") + rows;
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
     silhouette are the rules, and only then the things you actually buy.
     The jump bar is what makes that order affordable — reading order stays
     by importance, and Size is still one tap away. */
  var CARDS = [
    ["Direction",  directionCard(p.direction)],
    ["Hair",       hairCard(p.hair)],
    ["Palette",    paletteCard(p.palette)],
    ["Silhouette", silhouetteCard(p.silhouette)],
    ["Buy next",   buyNextCard(p.buyNext)],
    ["Wardrobe",   seasonalWardrobeCard(p.seasonalWardrobe)],
    ["Chinos",     chinoPlanCard(p.chinoPlan)],
    ["Brands",     brandsCard(p.brands)],
    ["Size",       sizeCard(p.size)],
    ["Planner",    outfitPlannerCard(p.outfitPlanner)]
  ].filter(function(c){ return c[1]; });

  var jump = CARDS.length > 1
    ? '<nav class="jump" aria-label="Jump to section">' + CARDS.map(function(c){
        return '<a href="#' + slug(c[0]) + '">' + esc(c[0]) + '</a>';
      }).join("") + '</nav>'
    : "";

  stage.innerHTML = jump + CARDS.map(function(c){
    return '<section class="ref-card" id="' + slug(c[0]) + '">' + c[1] + '</section>';
  }).join("");
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

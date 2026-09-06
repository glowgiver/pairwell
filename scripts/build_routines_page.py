"""Build hub/skincare/index.html and hub/hair/index.html from data/routines.json.

Same pattern as build_workout_page.py: read the data, inline it, render in the
browser. No runtime fetch, so both pages work offline once cached.

The two people have different routine shapes and the page handles both:

  philipp  "weekly"          one AM routine, one active per weekday
  eunice   "seasonal-weekly" four seasons, each with its own AM routine and
                             a different PM protocol for all seven days

So the skincare page resolves today's season first, then today's day, and
shows only that. Safety rules carrying an appliesTo field surface on the day
they govern.
"""

import json
import os

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, "..", "data", "routines.json")
OUT_SKIN = os.path.join(BASE, "..", "hub", "skincare", "index.html")
OUT_HAIR = os.path.join(BASE, "..", "hub", "hair", "index.html")

data = json.load(open(DATA, encoding="utf-8"))
data_json = json.dumps(data, ensure_ascii=False)


def _digest(rel):
    """Content hash for a shared asset, so a stale HTTP cache entry cannot
    outlive a change. The service worker revalidates eventually; this closes
    the window before it does."""
    import hashlib
    p = os.path.join(BASE, "..", "hub", rel)
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:8]

ASSET_V = {"css": _digest("app.css"), "js": _digest("app.js")}

SHARED_CSS = """
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

  h1{font-size:29px;font-weight:700;letter-spacing:-.02em;margin:0 0 4px;color:var(--accent)}
  .sub{font-family:var(--f-read);font-size:15.5px;color:var(--muted);margin:0 0 20px;line-height:1.6}

  /* Type floor: 14px for secondary, 16px+ for anything you act on.
     This page is read standing at a sink. */
  .card{
    background:var(--surface);border:1px solid var(--line);
    border-radius:16px;margin-bottom:14px;overflow:hidden;
  }
  .card-head{
    display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;
    padding:15px 18px 12px;border-bottom:1px solid var(--line);
  }
  .card-head .k{
    font-family:var(--f-data);font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
    color:var(--accent);
  }
  .card-head .meta{font-family:var(--f-data);font-size:13px;color:var(--muted2);margin-left:auto}
  .card-head .focus{font-size:15px;color:var(--text);font-weight:600;width:100%;margin-top:2px}

  ol.steps .n{
    font-family:var(--f-data);font-variant-numeric:tabular-nums;font-size:13px;font-weight:700;color:var(--muted2);
    font-variant-numeric:tabular-nums;
  }
  ol.steps .t{font-size:16.5px;font-weight:600;line-height:1.35}
  ol.steps .p{font-size:15px;color:var(--muted);margin-top:3px;line-height:1.45}
  ol.steps .h{font-family:var(--f-read);font-size:15px;color:var(--muted2);margin-top:4px;line-height:1.55}

  .empty{padding:20px 18px;font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.55}

  /* day strip */
  .days{display:flex;gap:5px;margin-bottom:14px}
  .day{
    flex:1;min-height:var(--tap);border-radius:11px;
    border:1px solid var(--line);background:var(--surface);
    color:var(--muted);font-family:inherit;font-size:13px;font-weight:600;
    cursor:pointer;padding:6px 2px;
  }
  .day small{display:block;font-family:var(--f-data);font-size:13px;font-weight:400;color:var(--muted2);margin-top:2px}
  .day[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
  .day[aria-pressed="true"] small{color:inherit;font-weight:400}
  .day:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  .season{
    display:inline-flex;align-items:center;gap:8px;
    font-family:var(--f-data);font-size:13px;color:var(--muted);
    background:var(--surface-2);border:1px solid var(--line);
    border-radius:9px;padding:7px 12px;margin-bottom:14px;
  }
  .season b{color:var(--text);font-weight:600}

  /* phase strip — which stage of the protocol he is on */
  .phase-bar{margin-bottom:12px}
  .phase-toggle{
    display:inline-flex;align-items:center;gap:9px;
    min-height:var(--tap);padding:0 14px;border-radius:11px;
    border:1px solid var(--line);background:var(--surface);
    font-family:inherit;font-size:14px;color:var(--muted);cursor:pointer;
  }
  .phase-toggle .pl{
    font-family:var(--f-data);font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted2);
  }
  .phase-toggle b{color:var(--text);font-weight:600}
  .phase-toggle .chev{
    width:7px;height:7px;border-right:2px solid var(--muted2);
    border-bottom:2px solid var(--muted2);transform:rotate(45deg);margin-left:2px;
  }
  .phase-toggle[aria-expanded="true"] .chev{transform:rotate(-135deg)}
  .phase-toggle:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  .phases{display:flex;gap:5px;margin-bottom:10px}
  .phase{
    flex:1;min-height:var(--tap);border-radius:11px;
    border:1px solid var(--line);background:var(--surface);
    color:var(--muted);font-family:inherit;font-size:13px;font-weight:600;
    cursor:pointer;padding:6px 4px;
  }
  .phase small{display:block;font-family:var(--f-data);font-size:13px;font-weight:400;color:var(--muted2);margin-top:2px}
  .phase[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg)}
  .phase[aria-pressed="true"] small{color:inherit;font-weight:400}
  .phase:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .phase-note{
    font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.5;
    margin-bottom:14px;padding-left:2px;
  }

  /* the one step that changes night to night */
  ol.steps .t.active-step{color:var(--accent)}

  /* safety */
  .rule{
    border:1px solid var(--line);border-left:3px solid var(--muted2);
    background:var(--surface-2);border-radius:0 12px 12px 0;
    padding:13px 16px;margin-bottom:12px;
  }
  .rule.critical{border-left-color:var(--warn);background:var(--warn-fill)}
  .rule .rt{
    font-family:var(--f-data);font-size:13px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
    color:var(--muted2);margin-bottom:6px;display:flex;align-items:center;gap:7px;
  }
  .rule.critical .rt{color:var(--warn)}
  .rule p{margin:0;font-family:var(--f-read);font-size:15px;line-height:1.6;color:var(--muted)}
  .rule.critical p{color:var(--text)}

  /* progressive disclosure */
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

  /* The routine you are not doing right now: present, one tap away, and not
     costing a screen of scroll. Its own card keeps its styling inside. */
  details.other-routine{background:none;border:0;margin-top:14px}
  details.other-routine > summary{
    color:var(--muted);font-weight:600;
    background:var(--surface);border:1px solid var(--line);border-radius:14px;
  }
  details.other-routine > summary .n{
    font-family:var(--f-data);font-size:13px;font-weight:400;color:var(--muted2);
  }
  details.other-routine[open] > summary{
    border-bottom-left-radius:0;border-bottom-right-radius:0;
  }
  .dl{padding:2px 18px 16px}
  .dl div{padding:9px 0;border-top:1px solid var(--line)}
  .dl .dk{font-family:var(--f-data);font-size:13px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted2);margin-bottom:3px}
  .dl .dv{font-family:var(--f-read);font-size:15px;line-height:1.6;color:var(--muted)}
  .dl .dv strong{color:var(--text)}

  .foot{font-size:13px;color:var(--muted2);line-height:1.6;margin-top:20px}

  /* Weekly check — a "when did I last do this" row, one per infrequent
     treatment. Shared by Hair's shower schedule and Skincare's weekly
     devices, so it takes its color from --accent rather than a fixed hue. */
  .schedrow{
    display:grid;grid-template-columns:1fr auto;align-items:baseline;
    gap:2px 12px;padding:13px 18px;border-bottom:1px solid var(--line);
  }
  .schedrow.other{opacity:.45}
  .sr-name{font-size:16px;font-weight:600}
  .sr-who{font-family:var(--f-data);font-size:12.5px;font-weight:400;color:var(--muted2)}
  .sr-cadence{
    grid-column:1;font-family:var(--f-data);font-size:13px;color:var(--muted2);
  }
  .sr-state{
    grid-column:2;grid-row:1;font-family:var(--f-data);font-size:13px;
    color:var(--muted);text-align:right;
  }
  .sr-state.due,.sr-state.late,.sr-state.unknown{color:var(--accent);font-weight:600}
  .sr-btn{
    grid-column:2;grid-row:2;justify-self:end;
    min-height:36px;padding:0 14px;border-radius:10px;
    font-family:inherit;font-size:13.5px;font-weight:600;cursor:pointer;
  }
  .sr-btn.dobtn{background:var(--accent);border:1px solid var(--accent);color:var(--bg)}
  .sr-btn.undone{background:none;border:1px solid var(--line);color:var(--muted)}
  .sr-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .dl em{font-style:italic;color:var(--muted2)}

  @media (prefers-reduced-motion:reduce){
    details summary::after{transition:none}
  }
"""

SHARED_JS_HEAD = """
const R = __DATA__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

/* Turn a JSON key into a readable label. The Products list used the raw key
   as its heading, so "vitaminC" and "eyeCreamAM" rendered as VITAMINC and
   EYECREAMAM — a mashed word that read like an error code. The heading is
   shown uppercase by CSS, so all this has to do is restore the word breaks
   the key name swallowed, and keep known acronyms whole. */
var ACRO = { am:"AM", pm:"PM", spf:"SPF", bha:"BHA", pha:"PHA", pdrn:"PDRN", uv:"UV" };
function humanizeLabel(k){
  return String(k)
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([a-zA-Z])(\\d)/g, "$1 $2")
    .replace(/(\\d)([a-zA-Z])/g, "$1 $2")
    .split(" ")
    .map(function(w){ return ACRO[w.toLowerCase()] || w; })
    .join(" ");
}

var DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
var DAY_LONG = {Mon:"Monday",Tue:"Tuesday",Wed:"Wednesday",Thu:"Thursday",
                Fri:"Friday",Sat:"Saturday",Sun:"Sunday"};

function todayKey(){
  // JS weeks start on Sunday; ours start on Monday.
  return DAYS[(new Date().getDay() + 6) % 7];
}

function stepList(steps, render){
  if(!steps || !steps.length) return "";
  return '<ol class="steps">' + steps.map(function(s,i){
    return '<li><span class="n">' + (i+1) + '</span><div>' + render(s) + '</div></li>';
  }).join("") + '</ol>';
}
"""


SKIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Skincare · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css?v=__CSSV__">
<style>
  :root{ --accent:var(--skin); }
__CSS__
</style>
</head>
<body>

<div class="pw-bar">
  <a class="pw-back" href="../"><svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg> Hub</a>
  <div id="switcher"></div>
</div>

<h1>Skincare</h1>
<p class="sub" id="sub"></p>

<div id="season"></div>
<div class="days" id="days"></div>
<div id="stage"></div>

<script src="../app.js?v=__JSV__"></script>
<script>
__JSHEAD__

var state = { day: todayKey() };
var phasePanelOpen = false;

function person(){ return PW.get(); }
function routine(){ return R.skincare[person()]; }

/* ---- weekly check: when was it last done -----------------------------
   Same idea as Hair's shower schedule, applied to skincare's own
   easy-to-miss weekly devices (MFU, Collagen Glow Pen) — a mark-done
   button plus a due state, so a skipped Saturday shows as overdue
   instead of quietly vanishing back into "next week". */

function doneKey(id){ return "hub.skin.done." + id + "." + PW.person().code; }

function today0(){ var d = new Date(); d.setHours(0,0,0,0); return d; }

function lastDone(id){
  try{
    var v = localStorage.getItem(doneKey(id));
    if(!v) return null;
    var d = new Date(v + "T00:00:00");
    return isNaN(d) ? null : d;
  }catch(e){ return null; }
}

function markDone(id){
  var d = today0();
  var iso = d.getFullYear() + "-" +
            String(d.getMonth()+1).padStart(2,"0") + "-" +
            String(d.getDate()).padStart(2,"0");
  try{ localStorage.setItem(doneKey(id), iso); }catch(e){}
}
function clearDone(id){ try{ localStorage.removeItem(doneKey(id)); }catch(e){} }

/* Returns {state, days, label} where state is one of
   unknown | done | soon | due | late. */
function dueState(t){
  var last = lastDone(t.id);
  if(!last) return { state:"unknown", days:null, label:"Never logged" };
  var days = Math.round((today0() - last) / 86400000);
  if(days === 0) return { state:"done", days:0, label:"Done today" };

  var due = t.everyDays || 7;
  var late = t.everyDaysMax || due;
  if(days >= late && late > due) return { state:"late", days:days, label:days + " days ago — overdue" };
  if(days > due && late === due) return { state:"late", days:days, label:days + " days ago — overdue" };
  if(days >= due) return { state:"due", days:days, label:"Due — " + days + " days ago" };
  var left = due - days;
  return { state:"soon", days:days, label:"In " + left + " day" + (left === 1 ? "" : "s") };
}

/* Which season covers today. Eunice's plan is seasonal; Philipp's is not. */
function seasonFor(r, date){
  if(!r.seasons) return null;
  var m = (date || new Date()).getMonth() + 1;
  for(var k in r.seasons){
    if(r.seasons[k].monthNumbers.indexOf(m) !== -1) return { key:k, data:r.seasons[k] };
  }
  return null;
}

function renderDays(){
  var wrap = document.getElementById("days");
  wrap.innerHTML = "";
  var today = todayKey();
  DAYS.forEach(function(d){
    var b = document.createElement("button");
    b.type = "button";
    b.className = "day";
    b.setAttribute("aria-pressed", String(state.day === d));
    b.setAttribute("aria-label", DAY_LONG[d] + (d === today ? " (today)" : ""));
    b.innerHTML = esc(d) + (d === today ? '<small>today</small>' : '<small>&nbsp;</small>');
    b.addEventListener("click", function(){ state.day = d; renderDays(); renderStage(); });
    wrap.appendChild(b);
  });
}

/* Philipp's PM is a fixed base where step 03 is a slot. Fill the slot with
   whichever active the current phase puts on this weekday. A rest night drops
   the slot entirely rather than leaving a hole. */
function currentPhase(r){
  var want = phaseOverride(r) || r.currentPhase;
  var found = r.phases.filter(function(p){ return p.id === want; })[0];
  return found || r.phases[r.phases.length - 1];
}

function phaseOverride(r){
  try { return localStorage.getItem("hub.phase." + person()); } catch(e){ return null; }
}

function buildPhasedPM(r){
  if(!r.pm || !r.phases) return null;
  var phase = currentPhase(r);
  var entry = phase.schedule.filter(function(e){ return e.day === state.day; })[0];
  var key = entry && entry.active;
  var active = key && r.actives[key];

  var out = [];
  r.pm.steps.forEach(function(s){
    if(!s.activeSlot){ out.push(s); return; }
    if(!active) return;                       // rest night: no step 03 at all
    /* Every other row reads function / product / how. This one used to put
       the product name where the function belongs, so step 03 was the only
       step in the routine you had to read differently. The data already
       carries the right title — "Active of the night" — it was being
       discarded. */
    out.push({
      step: s.step,
      product: active.name + (active.optional ? " · optional" : ""),
      how: active.how,
      isActive: true
    });
  });
  return out;
}

/* One line by default. The strip and its explanation only matter when you are
   deciding whether to move phase — roughly every four weeks — so they do not
   get to push the routine below the fold every day. */
function phaseHTML(r){
  var cur = currentPhase(r);
  var open = phasePanelOpen;
  var strip = open
    ? '<div class="phases" id="phases" role="group" aria-label="Protocol phase">' +
        r.phases.map(function(p){
          return '<button type="button" class="phase" data-phase="' + esc(p.id) + '"' +
            ' aria-pressed="' + (p.id === cur.id) + '">' + esc(p.label) +
            '<small>' + esc(p.subtitle) + '</small></button>';
        }).join("") + '</div>' +
        '<div class="phase-note">' + esc(cur.note) + '</div>'
    : '';
  return '<div class="phase-bar">' +
      '<button type="button" class="phase-toggle" id="phaseToggle" aria-expanded="' + open + '">' +
        '<span class="pl">Phase</span><b>' + esc(cur.label) + '</b>' +
        '<span class="chev" aria-hidden="true"></span>' +
      '</button>' +
    '</div>' + strip;
}

function ruleHTML(rule){
  return '<div class="rule' + (rule.critical ? ' critical' : '') + '">' +
    '<div class="rt">' + (rule.critical ? '&#9888; ' : '') + esc(rule.title) + '</div>' +
    '<p>' + esc(rule.rule) + '</p></div>';
}

function renderStage(){
  var r = routine();
  var stage = document.getElementById("stage");
  var sub = document.getElementById("sub");
  var seasonEl = document.getElementById("season");
  var isToday = state.day === todayKey();
  var when = isToday ? "Today" : DAY_LONG[state.day];

  /* Nothing recorded for this person yet — say so, don't show the other one's. */
  if(!r || (!r.am && !r.seasons)){
    seasonEl.innerHTML = "";
    sub.textContent = "";
    stage.innerHTML = '<div class="card"><div class="empty">' +
      'No routine recorded for ' + esc(PW.PEOPLE[person()].name) + ' yet.' +
      '</div></div>';
    return;
  }

  var season = seasonFor(r);
  var am, pmSteps = null, pmFocus = null;

  if(season){
    seasonEl.innerHTML = '<div class="season">' + esc(season.data.months) +
      ' &middot; <b>' + esc(season.key) + '</b></div>';
    sub.textContent = season.data.goal;
    am = season.data.am;
    var ev = season.data.pmWeekly.filter(function(e){ return e.day === state.day; })[0];
    if(ev){ pmSteps = ev.steps; pmFocus = ev.focus; }
  } else {
    sub.textContent = r.skinType || "";
    am = r.am;
    seasonEl.innerHTML = r.phases ? phaseHTML(r) : "";
    pmSteps = buildPhasedPM(r);
  }

  /* Morning */
  var amBody = am && am.steps && am.steps.length
    ? stepList(am.steps, function(s){
        if(typeof s === "string") return '<div class="t">' + esc(s) + '</div>';
        return '<div class="t">' + esc(s.step) + '</div>' +
               (s.product ? '<div class="p">' + esc(s.product) + '</div>' : '') +
               (s.how ? '<div class="h">' + esc(s.how) + '</div>' : '');
      })
    : '<div class="empty">No morning routine recorded.</div>';

  var amExtra = "";
  if(am && am.weeklyExtra && state.day === "Fri"){
    amExtra = '<div class="rule"><div class="rt">Friday only</div><p>' +
      esc(am.weeklyExtra) + '</p></div>';
  }

  var morning = '<div class="card"><div class="card-head">' +
    '<span class="k">Morning</span>' +
    (am && am.durationMin ? '<span class="meta">' + esc(am.durationMin) + ' min</span>' : '') +
    '</div>' + amBody + '</div>' + amExtra;

  /* Evening — both models render as numbered steps. */
  var evening;
  if(pmSteps && pmSteps.length){
    var restNight = r.phases && !pmSteps.some(function(s){ return s.isActive; });
    evening = '<div class="card"><div class="card-head">' +
      '<span class="k">' + (isToday ? 'Tonight' : esc(DAY_LONG[state.day]) + ' evening') + '</span>' +
      (r.pm && r.pm.durationMin ? '<span class="meta">' + esc(r.pm.durationMin) + ' min</span>' : '') +
      (pmFocus ? '<span class="focus">' + esc(pmFocus) + '</span>' : '') +
      (restNight ? '<span class="focus">Rest night — no active</span>' : '') +
      '</div>' +
      stepList(pmSteps, function(s){
        if(typeof s === "string") return '<div class="t">' + esc(s) + '</div>';
        return '<div class="t' + (s.isActive ? ' active-step' : '') + '">' + esc(s.step) + '</div>' +
               (s.product ? '<div class="p">' + esc(s.product) + '</div>' : '') +
               (s.how ? '<div class="h">' + esc(s.how) + '</div>' : '');
      }) + '</div>';
  } else {
    evening = '<div class="card"><div class="card-head"><span class="k">' +
      (isToday ? 'Tonight' : esc(DAY_LONG[state.day]) + ' evening') +
      '</span></div><div class="empty">No evening routine recorded.</div></div>';
  }
  if(r.applicationRule){
    evening += '<div class="rule"><div class="rt">How to apply</div><p>' +
      esc(r.applicationRule) + '</p></div>';
  }

  /* Inline only what you need to see before touching anything: rules tied to
     this specific day, plus the critical ones. The always-on advisory rules
     live in the disclosure below, so nothing appears twice. */
  var dayRules = (r.safetyRules || []).filter(function(rule){
    // A rule scoped to particular days shows on those days only — even a
    // critical one, or the MFU boundaries would shout on all seven.
    if(rule.appliesTo) return rule.appliesTo.indexOf(state.day.toLowerCase()) !== -1;
    return rule.critical;
  }).map(ruleHTML).join("");

  /* Everything else, behind a tap */
  var details = "";
  var allRules = (r.safetyRules || []);
  if(allRules.length){
    details += '<details><summary>All rules (' + allRules.length + ')</summary><div class="dl">' +
      allRules.map(function(x){
        return '<div><div class="dk">' + esc(x.title) + '</div><div class="dv">' + esc(x.rule) + '</div></div>';
      }).join("") + '</div></details>';
  }
  if(r.coreProducts){
    var rows = "";
    for(var k in r.coreProducts){
      rows += '<div><div class="dk">' + esc(humanizeLabel(k)) + '</div><div class="dv">' + esc(r.coreProducts[k]) + '</div></div>';
    }
    details += '<details><summary>Products</summary><div class="dl">' + rows + '</div></details>';
  }
  if(r.concerns && r.concerns.length || r.timeline || r.skinType){
    var b = "";
    if(r.skinType) b += '<div><div class="dk">Skin</div><div class="dv">' + esc(r.skinType) + '</div></div>';
    if(r.concerns && r.concerns.length)
      b += '<div><div class="dk">Focus</div><div class="dv">' + esc(r.concerns.join(" · ")) + '</div></div>';
    if(r.timeline) b += '<div><div class="dk">Timeline</div><div class="dv">' + esc(r.timeline) + '</div></div>';
    details += '<details><summary>Background</summary><div class="dl">' + b + '</div></details>';
  }
  if(r.seasons){
    var seasonRows = "";
    for(var sk in r.seasons){
      seasonRows += '<div><div class="dk">' + esc(sk) + ' &middot; ' + esc(r.seasons[sk].months) +
        '</div><div class="dv">' + esc(r.seasons[sk].goal) + '</div></div>';
    }
    details += '<details><summary>The four seasons</summary><div class="dl">' + seasonRows + '</div></details>';
  }

  /* Weekly check — the devices that are easy to skip on a bad Saturday and
     then forget about entirely, since nothing else on the page would tell
     you. Only rendered when the person actually has any (Eunice today). */
  var weekly = "";
  if(r.weeklyTreatments && r.weeklyTreatments.length){
    weekly = '<div class="card"><div class="card-head">' +
      '<span class="k">Weekly check</span></div>' +
      r.weeklyTreatments.map(function(t){
        var d = dueState(t);
        return '<div class="schedrow">' +
          '<div class="sr-name">' + esc(t.title) + '</div>' +
          '<div class="sr-cadence">' + esc(t.cadence) + '</div>' +
          '<div class="sr-state ' + d.state + '">' + esc(d.label) + '</div>' +
          (d.state === "done"
            ? '<button type="button" class="sr-btn undone" data-undone="' + esc(t.id) + '">Undo</button>'
            : '<button type="button" class="sr-btn dobtn" data-done="' + esc(t.id) + '">Done</button>') +
        '</div>';
      }).join("") +
    '</div>';
  }

  /* After 18:00 the evening is what you need first — and the other routine
     folds away rather than merely moving below. Standing at the sink at 22:00
     you should not scroll 700 px of this morning to reach tonight's step one.
     Browsing another day is planning rather than doing, so both stay open. */
  function folded(label, count, html){
    return '<details class="other-routine"><summary>' + esc(label) +
      (count ? '<span class="n">' + count + ' steps</span>' : '') +
      '</summary>' + html + '</details>';
  }

  var amCount = (am && am.steps) ? am.steps.length : 0;
  var pmCount = pmSteps ? pmSteps.length : 0;
  var eveningFirst = new Date().getHours() >= 18 && isToday;

  var body;
  if(!isToday){
    body = morning + evening;
  }else if(eveningFirst){
    body = evening + folded("Morning", amCount, morning);
  }else{
    body = morning + folded("Tonight", pmCount, evening);
  }
  stage.innerHTML = body + weekly + dayRules + details;

  document.querySelectorAll("[data-done]").forEach(function(b){
    b.addEventListener("click", function(){ markDone(b.dataset.done); renderStage(); });
  });
  document.querySelectorAll("[data-undone]").forEach(function(b){
    b.addEventListener("click", function(){ clearDone(b.dataset.undone); renderStage(); });
  });

  /* Phase strip lives above the stage, so wire it after each render. */
  var toggle = document.getElementById("phaseToggle");
  if(toggle){
    toggle.addEventListener("click", function(){
      phasePanelOpen = !phasePanelOpen;
      renderStage();
    });
  }
  var ph = document.getElementById("phases");
  if(ph){
    ph.querySelectorAll("[data-phase]").forEach(function(b){
      b.addEventListener("click", function(){
        try { localStorage.setItem("hub.phase." + person(), b.getAttribute("data-phase")); }catch(e){}
        phasePanelOpen = false;
        renderStage();
      });
    });
  }
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs("skincare", "../");
window.addEventListener("pw:person", renderStage);

renderDays();
renderStage();
</script>

</body>
</html>
"""


HAIR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Hair · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css?v=__CSSV__">
<style>
  :root{ --accent:var(--hair); }
__CSS__
  .both{
    display:inline-flex;align-items:center;gap:7px;
    font-size:13px;color:var(--muted);
    background:var(--surface-2);border:1px solid var(--line);
    border-radius:9px;padding:7px 12px;margin-bottom:14px;
  }
  .both b{color:var(--text);font-weight:600}
  .card.other{opacity:.5}

  .card.today{border-color:var(--hair)}
  .card.today ol.steps .t.treat-step{color:var(--hair)}
  .todaydone{display:flex;flex-wrap:wrap;gap:8px;padding:12px 18px 14px;border-top:1px solid var(--line)}
  .todaydone .dobtn{margin-left:0;flex:1 1 auto}
  /* A treatment this session deliberately skips — it still shows "due" in
     the Schedule card below (its own clock never moved), so silence here
     would read as the page having forgotten it rather than as a choice. */
  .skipnote{padding:11px 18px 14px;border-top:1px solid var(--line);
    font-family:var(--f-read);font-size:14px;color:var(--muted);line-height:1.5}
  .todaybody{padding:14px 18px;display:flex;flex-direction:column;gap:8px}
  .tline{font-size:15.5px;line-height:1.45;color:var(--muted)}
  .tline b{color:var(--text);font-weight:600}
  .tline.due b{color:var(--hair)}
  .tline.ok{color:var(--muted2)}

  .duebar{
    display:flex;align-items:center;gap:12px;flex-wrap:wrap;
    padding:11px 18px;border-bottom:1px solid var(--line);background:var(--surface-2);
  }
  .duepill{
    font-family:var(--f-data);font-size:13px;font-weight:600;
    letter-spacing:.04em;color:var(--muted);
  }
  /* Accent as ink on the page ground — the pairing that holds in both themes. */
  .duepill.due,.duepill.late{color:var(--hair)}
  .duepill.late{font-weight:700}
  .duepill.done{color:var(--ok,var(--muted))}
  .dobtn,.undone{
    margin-left:auto;min-height:var(--tap);padding:0 16px;border-radius:11px;
    font-family:inherit;font-size:14px;font-weight:600;cursor:pointer;
  }
  .dobtn{background:var(--hair);border:1px solid var(--hair);color:var(--bg)}
  .undone{background:none;border:1px solid var(--line);color:var(--muted)}
  .dobtn:focus-visible,.undone:focus-visible{outline:2px solid var(--hair);outline-offset:2px}
  .inline-caution{
    padding:11px 18px 14px;font-family:var(--f-read);font-size:15px;line-height:1.55;
    color:var(--muted2);border-top:1px solid var(--line);
  }
</style>
</head>
<body>

<div class="pw-bar">
  <a class="pw-back" href="../"><svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg> Hub</a>
  <div id="switcher"></div>
</div>

<h1>Hair</h1>
<p class="sub" id="sub"></p>

<div class="both">One protocol &middot; <b>both of you</b></div>
<div id="stage"></div>

<script src="../app.js?v=__JSV__"></script>
<script>
__JSHEAD__

function person(){ return PW.get(); }

/* ---- when was it last done -------------------------------------------
   Not a log: exactly one date per treatment per person. That is the whole
   difference between a page that states "weekly" and a page that can tell
   you whether today is the day. Per person, because they shower separately
   even where the protocol is shared. */

function doneKey(id){ return "hub.hair.done." + id + "." + PW.person().code; }

function today0(){ var d = new Date(); d.setHours(0,0,0,0); return d; }

function lastDone(id){
  try{
    var v = localStorage.getItem(doneKey(id));
    if(!v) return null;
    var d = new Date(v + "T00:00:00");
    return isNaN(d) ? null : d;
  }catch(e){ return null; }
}

function markDone(id){
  var d = today0();
  var iso = d.getFullYear() + "-" +
            String(d.getMonth()+1).padStart(2,"0") + "-" +
            String(d.getDate()).padStart(2,"0");
  try{ localStorage.setItem(doneKey(id), iso); }catch(e){}
  /* A treatment that supersedes another (skipsIfDue) does that other one's
     job too, not just today's — chelating pulls out the same calcium and
     magnesium the citric rinse would have dissolved. Leaving citric's own
     date untouched would show it "overdue" the very next day, which is the
     wrong answer to "does hair need de-scaling again" one day after it was
     just done by the deeper treatment. So marking chelating done resets
     whatever it stands in for too. */
  (R.hair.scheduled || []).forEach(function(t){
    if(t.skipsIfDue && t.skipsIfDue.indexOf(id) !== -1){
      try{ localStorage.setItem(doneKey(t.id), iso); }catch(e){}
    }
  });
}
function clearDone(id){ try{ localStorage.removeItem(doneKey(id)); }catch(e){} }

/* Returns {state, days, label} where state is one of
   unknown | done | soon | due | late. */
function dueState(t){
  var last = lastDone(t.id);
  if(!last) return { state:"unknown", days:null, label:"Never logged" };
  var days = Math.round((today0() - last) / 86400000);
  if(days === 0) return { state:"done", days:0, label:"Done today" };

  var due = t.everyDays || 7;
  var late = t.everyDaysMax || due;
  if(days >= late && late > due) return { state:"late", days:days, label:days + " days ago — overdue" };
  if(days > due && late === due) return { state:"late", days:days, label:days + " days ago — overdue" };
  if(days >= due) return { state:"due", days:days, label:"Due — " + days + " days ago" };
  var left = due - days;
  return { state:"soon", days:days, label:"In " + left + " day" + (left === 1 ? "" : "s") };
}

function isDue(t){
  var st = dueState(t).state;
  return st === "due" || st === "late" || st === "unknown";
}

/* Today's shower as ONE sequence.

   The page used to print the four cards and leave you to merge three prose
   "order" sentences while standing in the shower — wash, then mask, then
   citric, but each of those sentences only described its own treatment.
   Chelating replaces the shampoo rather than following it, which is the part
   that is easiest to get wrong from prose alone. */
function showerSequence(who){
  var h = R.hair;
  var base = h.everyShower.steps;
  var candidates = h.scheduled.filter(function(t){
    return (t.who === "both" || t.who === who) && isDue(t);
  });
  var dueIds = candidates.map(function(t){ return t.id; });

  /* skipsIfDue: a deeper treatment can make a lighter one redundant for this
     one session — chelating already does citric's job by a different route.
     The lighter treatment's own clock is untouched (it isn't marked done),
     so it is simply due again at the next wash; only this session skips it. */
  var skipped = candidates.filter(function(t){
    return t.skipsIfDue && t.skipsIfDue.some(function(id){ return dueIds.indexOf(id) !== -1; });
  }).map(function(t){
    var coveredBy = t.skipsIfDue.filter(function(id){ return dueIds.indexOf(id) !== -1; })
      .map(function(id){
        var m = h.scheduled.filter(function(x){ return x.id === id; })[0];
        return m ? m.title : id;
      });
    return { treat: t, coveredBy: coveredBy };
  });
  var skippedIds = skipped.map(function(s){ return s.treat.id; });
  var due = candidates.filter(function(t){ return skippedIds.indexOf(t.id) === -1; })
    .sort(function(a, b){ return (a.rank || 0) - (b.rank || 0); });

  var out = [];
  base.forEach(function(s, i){
    var n = i + 1;
    var replacing = due.filter(function(t){ return t.replacesStep === n; })[0];
    if(replacing){
      out.push({ step: replacing.title, how: replacing.recipe + " " + replacing.order,
                 treat: replacing });
    }else{
      out.push({ step: s.step, how: s.how,
                 extra: s.perPerson && s.perPerson[who] });
    }
    due.filter(function(t){ return t.afterStep === n; }).forEach(function(t){
      out.push({ step: t.title, how: t.recipe, treat: t });
    });
  });
  return { steps: out, due: due, skipped: skipped };
}

/* "wash plus X and Y and Z" read badly, and it was wrong about chelating,
   which replaces the shampoo rather than joining it. */
function listWords(a){
  if(a.length <= 1) return a[0] || "";
  return a.slice(0, -1).join(", ") + " and " + a[a.length - 1];
}
function showerSummary(seq){
  if(!seq.due.length) return "A normal wash \u2014 nothing extra due";
  var swap = seq.due.filter(function(t){ return t.replacesStep; });
  var add  = seq.due.filter(function(t){ return !t.replacesStep; });
  var addWords = add.length
    ? "plus " + listWords(add.map(function(t){ return t.title.toLowerCase(); }))
    : "";
  if(swap.length){
    /* Two clauses, not two list items — joining them with "and" produced
       "instead of the usual shampoo and plus the mask". */
    var swapWords = listWords(swap.map(function(t){ return t.title.toLowerCase(); }));
    var head = swapWords.charAt(0).toUpperCase() + swapWords.slice(1) +
               " instead of the usual shampoo";
    return addWords ? head + ", " + addWords : head;
  }
  return "A normal wash" + (addWords ? " " + addWords : "");
}

function renderStage(){
  var h = R.hair;
  var who = person();
  var stage = document.getElementById("stage");
  /* The reasoning is real but it is not what you came for; it now opens under
     "Why this protocol" instead of above the first step. */
  document.getElementById("sub").textContent =
    "Sulfate-free, conditioned, and rinsed clear of hard water.";

  /* Every shower — four steps, with the amount that differs per person
     shown only for whoever is currently selected. */
  var wash = '<div class="card"><div class="card-head">' +
    '<span class="k">Every shower</span></div>' +
    stepList(h.everyShower.steps, function(s){
      var extra = s.perPerson && s.perPerson[who];
      return '<div class="t">' + esc(s.step) + '</div>' +
             (s.how ? '<div class="h">' + esc(s.how) + '</div>' : '') +
             (extra ? '<div class="p"><strong>' + esc(PW.PEOPLE[who].name) + '</strong> &middot; ' +
                      esc(extra) + '</div>' : '');
    }) + '</div>';

  /* Scheduled treatments. Ones that belong to the other person are shown
     greyed rather than hidden, so nobody wonders where they went. */
  /* One compact schedule instead of three full cards.

     Those cards each carried their own prose "order" sentence, and the citric
     one read "Shampoo → rinse → pour the citric solution → leave-in as normal"
     — with no mask in it anywhere. Follow that card and the mask has nowhere
     to go but after the citric rinse, which is exactly the wrong way round and
     exactly what happened. Three statements of order on one page, only one of
     them complete.

     Order now lives in ONE place: the sequence above. This says when, not how. */
  var sched =
    '<div class="card"><div class="card-head">' +
      '<span class="k">Schedule</span>' +
      '<span class="meta">' + esc(PW.PEOPLE[who].name) + '</span></div>' +
    h.scheduled.map(function(t){
      var mine = t.who === "both" || t.who === who;
      var d = mine ? dueState(t) : null;
      return '<div class="schedrow' + (mine ? '' : ' other') + '">' +
        '<div class="sr-name">' + esc(t.title) +
          (t.who === "both" ? '' : ' <span class="sr-who">' +
            esc(PW.PEOPLE[t.who].name) + ' only</span>') + '</div>' +
        '<div class="sr-cadence">' + esc(t.cadence) + '</div>' +
        (mine
          ? '<div class="sr-state ' + d.state + '">' + esc(d.label) + '</div>' +
            (d.state === "done"
              ? '<button type="button" class="sr-btn undone" data-undone="' + esc(t.id) + '">Undo</button>'
              : '<button type="button" class="sr-btn dobtn" data-done="' + esc(t.id) + '">Done</button>')
          : '<div class="sr-state"></div><div></div>') +
      '</div>';
    }).join("") +
    /* The detail each treatment needs on its own — what to mix, what too much
       looks like — without restating the order the sequence already owns. */
    '<details><summary>What each one is, and when to ease off</summary><div class="dl">' +
      h.scheduled.map(function(t){
        return '<div><div class="dk">' + esc(t.title) + '</div><div class="dv">' +
          esc(t.recipe) +
          (t.caution ? ' <em>' + esc(t.caution) + '</em>' : '') +
          '</div></div>';
      }).join("") +
    '</div></details></div>';

  /* Lead with the answer to the question the page exists to answer. Before
     this it opened on frequencies and left the date arithmetic to the reader. */
  var seq = showerSequence(who);
  var todayCard =
    '<div class="card today"><div class="card-head">' +
      '<span class="k">Today, in order</span>' +
      '<span class="meta">' + esc(PW.PEOPLE[who].name) + '</span>' +
      '<span class="focus">' + esc(showerSummary(seq)) + '</span>' +
    '</div>' +
    stepList(seq.steps, function(x){
      return '<div class="t' + (x.treat ? ' treat-step' : '') + '">' + esc(x.step) + '</div>' +
             (x.how ? '<div class="h">' + esc(x.how) + '</div>' : '') +
             (x.extra ? '<div class="p"><strong>' + esc(PW.PEOPLE[who].name) +
                        '</strong> &middot; ' + esc(x.extra) + '</div>' : '');
    }) +
    (seq.due.length
      ? '<div class="todaydone">' + seq.due.map(function(t){
          return '<button type="button" class="dobtn" data-done="' + esc(t.id) + '">' +
                 esc(t.title) + ' done</button>';
        }).join("") + '</div>'
      : '') +
    /* A treatment skipped for today must say so here, not just vanish —
       it still shows "due" in the Schedule list below, since its own clock
       never moved, and that would otherwise read as the page forgetting it. */
    (seq.skipped.length
      ? '<div class="skipnote">' + seq.skipped.map(function(s){
          return esc(s.treat.title) + ' skipped today — ' +
                 esc(s.coveredBy.join(", ")) + ' already covers it this session.';
        }).join(" ") + '</div>'
      : '') +
    '</div>';

  var note = h.individualNotes[who];
  var personal = note
    ? '<div class="rule"><div class="rt">Note for ' + esc(PW.PEOPLE[who].name) + '</div><p>' +
      esc(note) + '</p></div>' : "";

  /* Detail behind a tap */
  /* Every buy row is the same card — an eyebrow, then the bold product name
     with its shop and price, then the note. Ranked options and lone products
     differ only in what the eyebrow says, so the whole list reads as one list
     instead of flipping grammar halfway down: the leave-in and towel used to
     put the product NAME in the tiny eyebrow slot and the price in the body,
     the exact inverse of the shampoo cards above them. */
  var PROD_CAT = { shampoo:"Shampoo", leaveIn:"Leave-in", towel:"Towel",
    citricAcid:"Citric acid", chelator:"Chelating shampoo", mask:"Deep mask",
    testStrips:"Test strips" };

  function buyCard(eyebrow, name, where, price, note, inci){
    /* Separator is the raw middle-dot, not the &middot; entity: this string
       goes through esc(), which would turn the entity's & into &amp; and
       print "&middot;" verbatim. The data already uses the raw · anyway. */
    var meta = [where, price].filter(Boolean).join(" · ");
    return '<div><div class="dk">' + esc(eyebrow) + '</div>' +
      '<div class="dv"><strong>' + esc(name) + '</strong>' +
      (meta ? ' · ' + esc(meta) : '') +
      (note ? '<br>' + esc(note) : '') +
      (inci ? '<br>' + esc(inci) : '') + '</div></div>';
  }

  function productBlock(k){
    var p = h.products[k];
    if(!p) return "";
    var cat = PROD_CAT[k] || k;
    if(p.options){
      /* The category and its shared note, then one card per option. */
      return (p._note
          ? '<div><div class="dk">' + esc(cat) + '</div><div class="dv">' + esc(p._note) + '</div></div>'
          : '') +
        p.options.map(function(o){
          return buyCard(o.rank, o.name, o.where, o.price, o.note, o.inci);
        }).join("");
    }
    return buyCard(cat, p.name, p.where, p.price, p.note, p.inci);
  }

  var productList = ["shampoo","leaveIn","towel","citricAcid","chelator","mask","testStrips"]
    .map(productBlock).join("");

  var packages = h.rollout.packages.map(function(p){
    return '<div><div class="dk">' + esc(p.id) + ' &middot; ' + esc(p.title) + ' &middot; ' + esc(p.cost) + '</div>' +
      '<div class="dv"><strong>' + esc(p.when) + '</strong><br>' +
      p.items.map(function(i){ return '&bull; ' + esc(i); }).join('<br>') +
      '<br><em>' + esc(p.note) + '</em></div></div>';
  }).join("");

  var tracking = h.tracking.map(function(t){
    return '<div><div class="dk">' + esc(t.what) + '</div><div class="dv">' + esc(t.how) + '</div></div>';
  }).join("");

  var details =
    '<details><summary>Products &amp; where to buy</summary><div class="dl">' +
      productList + '</div></details>' +
    '<details><summary>Rollout plan</summary><div class="dl">' +
      '<div><div class="dk">Golden rule</div><div class="dv">' + esc(h.rollout.goldenRule) + '</div></div>' +
      packages + '</div></details>' +
    '<details><summary>What to track</summary><div class="dl">' + tracking + '</div></details>' +
    '<details><summary>Why this protocol</summary><div class="dl">' +
      /* Moved down from the top of the page, where forty-four words on
         sulfates stood between arriving and the first instruction. */
      '<div><div class="dk">The problem</div><div class="dv">' + esc(h.context.why) + '</div></div>' +
      '<div><div class="dk">Water</div><div class="dv">' + esc(h.context.waterHardness) + '</div></div>' +
      '<div><div class="dk">Verify</div><div class="dv">' + esc(h.context.verify) + '</div></div>' +
    '</div></details>';

  /* `wash` is the same four steps the sequence above already contains, so it
     no longer ships — the sequence IS the wash, with today's extras folded in
     where they belong. */
  stage.innerHTML = todayCard + sched + personal + details;
  wireDoneButtons();
}

function wireDoneButtons(){
  document.querySelectorAll("[data-done]").forEach(function(b){
    b.addEventListener("click", function(){ markDone(b.dataset.done); renderStage(); });
  });
  document.querySelectorAll("[data-undone]").forEach(function(b){
    b.addEventListener("click", function(){ clearDone(b.dataset.undone); renderStage(); });
  });
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
/* This page shipped without a tab bar, so the only way off it was the back
   link at the top — which scrolls away. */
PW.mountTabs("hair", "../");
window.addEventListener("pw:person", renderStage);

renderStage();
</script>

</body>
</html>
"""


def build(template, out_path):
    html = template.replace("__CSS__", SHARED_CSS)
    html = html.replace("__JSHEAD__", SHARED_JS_HEAD)
    html = html.replace("__DATA__", data_json)\
        .replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("written %-32s %6d bytes" % (os.path.basename(os.path.dirname(out_path)) + "/index.html", len(html)))


build(SKIN_HTML, OUT_SKIN)
build(HAIR_HTML, OUT_HAIR)

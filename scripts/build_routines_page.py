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


SHARED_CSS = """
  body{
    background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    -webkit-font-smoothing:antialiased;
    min-height:100dvh;max-width:600px;margin:0 auto;
    padding:
      calc(env(safe-area-inset-top) + 20px)
      calc(env(safe-area-inset-right) + 18px)
      calc(env(safe-area-inset-bottom) + 40px)
      calc(env(safe-area-inset-left) + 18px);
  }

  h1{font-size:29px;font-weight:700;letter-spacing:-.02em;margin:0 0 4px;color:var(--accent)}
  .sub{font-size:14px;color:var(--muted);margin:0 0 20px;line-height:1.5}

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
    font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
    color:var(--accent);
  }
  .card-head .meta{font-size:13px;color:var(--muted2);margin-left:auto}
  .card-head .focus{font-size:15px;color:var(--text);font-weight:600;width:100%;margin-top:2px}

  ol.steps{list-style:none;margin:0;padding:6px 0}
  ol.steps li{
    display:grid;grid-template-columns:26px 1fr;gap:12px;
    padding:11px 18px;align-items:baseline;
  }
  ol.steps li + li{border-top:1px solid var(--line)}
  ol.steps .n{
    font-size:13px;font-weight:700;color:var(--muted2);
    font-variant-numeric:tabular-nums;
  }
  ol.steps .t{font-size:16.5px;font-weight:600;line-height:1.35}
  ol.steps .p{font-size:14.5px;color:var(--muted);margin-top:3px;line-height:1.45}
  ol.steps .h{font-size:14px;color:var(--muted2);margin-top:3px;line-height:1.45;font-style:italic}

  .empty{padding:20px 18px;font-size:15px;color:var(--muted);line-height:1.55}

  /* day strip */
  .days{display:flex;gap:5px;margin-bottom:14px}
  .day{
    flex:1;min-height:var(--tap);border-radius:11px;
    border:1px solid var(--line);background:var(--surface);
    color:var(--muted);font-family:inherit;font-size:13px;font-weight:600;
    cursor:pointer;padding:6px 2px;
  }
  .day small{display:block;font-size:10px;font-weight:400;color:var(--muted2);margin-top:2px}
  .day[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
  .day[aria-pressed="true"] small{color:rgba(255,255,255,.8)}
  .day:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  .season{
    display:inline-flex;align-items:center;gap:8px;
    font-size:13px;color:var(--muted);
    background:var(--surface-2);border:1px solid var(--line);
    border-radius:9px;padding:7px 12px;margin-bottom:14px;
  }
  .season b{color:var(--text);font-weight:600}

  /* phase strip — which stage of the protocol he is on */
  .phases{display:flex;gap:5px;margin-bottom:10px}
  .phase{
    flex:1;min-height:var(--tap);border-radius:11px;
    border:1px solid var(--line);background:var(--surface);
    color:var(--muted);font-family:inherit;font-size:13px;font-weight:600;
    cursor:pointer;padding:6px 4px;
  }
  .phase small{display:block;font-size:10.5px;font-weight:400;color:var(--muted2);margin-top:2px}
  .phase[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
  .phase[aria-pressed="true"] small{color:rgba(255,255,255,.8)}
  .phase:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .phase-note{
    font-size:13.5px;color:var(--muted);line-height:1.5;
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
  .rule.critical{border-left-color:#F4666F;background:rgba(244,102,111,.10)}
  .rule .rt{
    font-size:13px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
    color:var(--muted2);margin-bottom:6px;display:flex;align-items:center;gap:7px;
  }
  .rule.critical .rt{color:#F4666F}
  .rule p{margin:0;font-size:14.5px;line-height:1.55;color:var(--muted)}
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
  .dl{padding:2px 18px 16px}
  .dl div{padding:9px 0;border-top:1px solid var(--line)}
  .dl .dk{font-size:13px;letter-spacing:.07em;text-transform:uppercase;color:var(--muted2);margin-bottom:3px}
  .dl .dv{font-size:14.5px;line-height:1.5;color:var(--muted)}
  .dl .dv strong{color:var(--text)}

  .foot{font-size:13px;color:var(--muted2);line-height:1.6;margin-top:20px}

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
<link rel="stylesheet" href="../app.css">
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

<script src="../app.js"></script>
<script>
__JSHEAD__

var state = { day: todayKey() };

function person(){ return PW.get(); }
function routine(){ return R.skincare[person()]; }

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
    out.push({
      step: active.name + (active.optional ? " · optional" : ""),
      how: active.how,
      isActive: true
    });
  });
  return out;
}

function phaseHTML(r){
  var cur = currentPhase(r);
  return '<div class="phases" id="phases" role="group" aria-label="Protocol phase">' +
    r.phases.map(function(p){
      return '<button type="button" class="phase" data-phase="' + esc(p.id) + '"' +
        ' aria-pressed="' + (p.id === cur.id) + '">' + esc(p.label) +
        '<small>' + esc(p.subtitle) + '</small></button>';
    }).join("") + '</div>' +
    '<div class="phase-note">' + esc(cur.note) + '</div>';
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
      rows += '<div><div class="dk">' + esc(k) + '</div><div class="dv">' + esc(r.coreProducts[k]) + '</div></div>';
    }
    details += '<details><summary>Products</summary><div class="dl">' + rows + '</div></details>';
  }
  if(r.concerns && r.concerns.length || r.timeline || r.skinType){
    var b = "";
    if(r.skinType) b += '<div><div class="dk">Skin</div><div class="dv">' + esc(r.skinType) + '</div></div>';
    if(r.concerns && r.concerns.length)
      b += '<div><div class="dk">Focus</div><div class="dv">' + esc(r.concerns.join(" &middot; ")) + '</div></div>';
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

  /* After 18:00 the evening is what you need first. */
  var eveningFirst = new Date().getHours() >= 18 && isToday;
  stage.innerHTML = (eveningFirst ? evening + morning : morning + evening) + dayRules + details;

  /* Phase strip lives above the stage, so wire it after each render. */
  var ph = document.getElementById("phases");
  if(ph){
    ph.querySelectorAll("[data-phase]").forEach(function(b){
      b.addEventListener("click", function(){
        try { localStorage.setItem("hub.phase." + person(), b.getAttribute("data-phase")); }catch(e){}
        renderStage();
      });
    });
  }
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
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
<link rel="stylesheet" href="../app.css">
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
  .inline-caution{
    padding:11px 18px 14px;font-size:14px;line-height:1.5;
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

<script src="../app.js"></script>
<script>
__JSHEAD__

function person(){ return PW.get(); }

function renderStage(){
  var h = R.hair;
  var who = person();
  var stage = document.getElementById("stage");
  document.getElementById("sub").textContent = h.context.why;

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
  var sched = h.scheduled.map(function(t){
    var mine = t.who === "both" || t.who === who;
    return '<div class="card' + (mine ? '' : ' other') + '"><div class="card-head">' +
      '<span class="k">' + esc(t.cadence) + '</span>' +
      '<span class="meta">' + (t.who === "both" ? "both" : esc(PW.PEOPLE[t.who].name) + " only") + '</span>' +
      '<span class="focus">' + esc(t.title) + '</span></div>' +
      '<ol class="steps">' +
        '<li><span class="n">&bull;</span><div><div class="p">' + esc(t.recipe) + '</div></div></li>' +
        '<li><span class="n">&rarr;</span><div><div class="h">' + esc(t.order) + '</div></div></li>' +
      '</ol>' +
      (t.caution ? '<div class="inline-caution">' + esc(t.caution) + '</div>' : '') +
      '</div>';
  }).join("");

  var note = h.individualNotes[who];
  var personal = note
    ? '<div class="rule"><div class="rt">Note for ' + esc(PW.PEOPLE[who].name) + '</div><p>' +
      esc(note) + '</p></div>' : "";

  /* Detail behind a tap */
  var shampoo = h.products.shampoo.options.map(function(o){
    return '<div><div class="dk">' + esc(o.rank) + ' &middot; ' + esc(o.price) + '</div>' +
      '<div class="dv"><strong>' + esc(o.name) + '</strong> &middot; ' + esc(o.where) + '<br>' +
      esc(o.note) + '</div></div>';
  }).join("");

  var others = "";
  ["leaveIn","towel","citricAcid","chelator","mask","testStrips"].forEach(function(k){
    var p = h.products[k];
    if(!p) return;
    others += '<div><div class="dk">' + esc(p.name) + '</div><div class="dv">' +
      esc([p.price, p.where].filter(Boolean).join(" &middot; ")) +
      (p.note ? '<br>' + esc(p.note) : '') +
      (p.inci ? '<br>' + esc(p.inci) : '') + '</div></div>';
  });

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
      '<div><div class="dk">Shampoo — priority order</div><div class="dv">' +
      esc(h.products.shampoo._note) + '</div></div>' + shampoo + others + '</div></details>' +
    '<details><summary>Rollout plan</summary><div class="dl">' +
      '<div><div class="dk">Golden rule</div><div class="dv">' + esc(h.rollout.goldenRule) + '</div></div>' +
      packages + '</div></details>' +
    '<details><summary>What to track</summary><div class="dl">' + tracking + '</div></details>' +
    '<details><summary>Why this protocol</summary><div class="dl">' +
      '<div><div class="dk">Water</div><div class="dv">' + esc(h.context.waterHardness) + '</div></div>' +
      '<div><div class="dk">Verify</div><div class="dv">' + esc(h.context.verify) + '</div></div>' +
    '</div></details>';

  stage.innerHTML = wash + sched + personal + details;
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));
window.addEventListener("pw:person", renderStage);

renderStage();
</script>

</body>
</html>
"""


def build(template, out_path):
    html = template.replace("__CSS__", SHARED_CSS)
    html = html.replace("__JSHEAD__", SHARED_JS_HEAD)
    html = html.replace("__DATA__", data_json)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("written %-32s %6d bytes" % (os.path.basename(os.path.dirname(out_path)) + "/index.html", len(html)))


build(SKIN_HTML, OUT_SKIN)
build(HAIR_HTML, OUT_HAIR)

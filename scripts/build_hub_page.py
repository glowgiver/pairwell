"""Build hub/index.html — the Today screen.

Replaces the four-tile launcher. Every input already existed and none of it was
being used: weeklyRhythm knows what today's training is, the seasonal plans and
pmWeeklyPlan know tonight's routine, am.steps knows the morning, profiles.json
knows the targets, and the session durations recovered from the workout source
supply the "~50 min".

Resolution order matters: person, then weekday, then — for Eunice — season, then
— for Philipp — protocol phase. The page shows one day for one person and
nothing else.
"""

import hashlib
import json
import os

BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "..", "hub", "index.html")

def load(name):
    return json.load(open(os.path.join(BASE, "..", "data", name), encoding="utf-8"))

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


def meal_titles():
    """id -> title, and nothing else.

    The hub needs to name the dishes already picked in Kitchen, which lives in
    localStorage as ids. Inlining all of recipes.json to resolve three strings
    would put every ingredient and method on the Today screen; this ships the
    two hundred bytes the card actually renders.
    """
    return {r["id"]: r["title"] for r in load("recipes.json")["recipes"]}


data = {
    "profiles": strip_body(load("profiles.json")),
    "training": load("training.json"),
    "routines": load("routines.json"),
    "kitchen": strip_buildonly(load("kitchen.json")),
    "mealTitles": meal_titles(),
}
data_json = json.dumps(data, ensure_ascii=False)


def _digest(rel):
    p = os.path.join(BASE, "..", "hub", rel)
    import hashlib as _h
    return _h.sha1(open(p, "rb").read()).hexdigest()[:8]

ASSET_V = {"css": _digest("app.css"), "js": _digest("app.js")}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pairwell</title>
<meta name="theme-color" content="#0B1220">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Pairwell">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="icons/icon-192.png">
<link rel="stylesheet" href="app.css?v=__CSSV__">
<style>
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

  header{margin-bottom:22px}
  .date{
    font-family:var(--f-data);font-size:13px;letter-spacing:.13em;
    text-transform:uppercase;color:var(--muted2);margin:0 0 7px;
  }
  h1{font-size:30px;line-height:1.15;font-weight:700;letter-spacing:-.025em;margin:0}
  h1 .who{color:var(--who-active,var(--philipp))}

  /* One card per part of the day. The accent says which module it belongs to,
     so the colour is doing navigational work, not decoration. */
  .card{
    display:block;text-decoration:none;color:inherit;
    background:var(--surface);border:1px solid var(--line);
    border-left:3px solid var(--accent);
    border-radius:0 16px 16px 0;margin-bottom:12px;overflow:hidden;
    transition:background .18s ease, transform .18s ease;
  }
  .card:active{background:var(--surface-2);transform:scale(.99)}
  .card:focus-visible{outline:2px solid var(--accent);outline-offset:3px}

  .ch{display:flex;align-items:baseline;gap:10px;padding:14px 18px 0}
  .ch .k{
    font-family:var(--f-data);font-size:13px;font-weight:600;
    letter-spacing:.12em;text-transform:uppercase;color:var(--accent);
  }
  .ch .meta{font-family:var(--f-data);font-size:13px;color:var(--muted2);margin-left:auto}
  .cb{padding:8px 18px 16px}
  .headline{font-size:19px;font-weight:600;letter-spacing:-.012em;line-height:1.35}
  .detail{
    font-family:var(--f-read);font-size:15px;line-height:1.55;
    color:var(--muted);margin-top:5px;
  }
  .detail .sep{color:var(--muted2)}
  .rest{color:var(--muted)}

  .warn{
    display:flex;gap:9px;align-items:flex-start;
    margin:10px 18px 14px;padding:11px 13px;
    border-radius:0 10px 10px 0;border-left:3px solid var(--warn);
    background:var(--warn-fill);
  }
  .warn .wt{
    font-family:var(--f-data);font-size:12.5px;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;color:var(--warn);
  }
  .warn p{margin:4px 0 0;font-family:var(--f-read);font-size:14.5px;line-height:1.5;color:var(--text)}

  /* A declared phase, not a warning: same shape as .warn, the module accent
     instead of the alarm colour, because nothing here is wrong. */
  .phase{
    margin:10px 18px 14px;padding:11px 13px;
    border-radius:0 10px 10px 0;border-left:3px solid var(--food);
    background:var(--surface-2);
  }
  .phase .pt{
    font-family:var(--f-data);font-size:12.5px;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;color:var(--food);
  }
  .phase p{margin:4px 0 0;font-family:var(--f-read);font-size:14.5px;
    line-height:1.5;color:var(--text)}
  .phase .pm{margin-top:6px;font-family:var(--f-data);font-size:13px;color:var(--muted2)}
  .targets{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px}
  .targets div{font-family:var(--f-data);font-size:13px;color:var(--muted2);
    font-variant-numeric:tabular-nums}
  .targets b{display:block;font-size:17px;color:var(--text);font-weight:700;margin-top:2px}

  .meals{display:flex;flex-direction:column;gap:3px;margin-top:2px}
  .meals div{font-size:14.5px;color:var(--text);display:flex;gap:8px}
  .meals span{
    font-family:var(--f-data);font-size:13px;color:var(--muted2);
    min-width:52px;flex:none;
  }

  .phase details.why{margin-top:8px}
  .phase details.why summary{
    font-family:var(--f-data);font-size:13px;color:var(--muted2);
    cursor:pointer;list-style:none;min-height:var(--tap);
    display:flex;align-items:center;
  }
  .phase details.why summary::-webkit-details-marker{display:none}
  .phase details.why summary::after{content:" ▾";margin-left:4px}
  .phase details.why[open] summary::after{content:" ▴"}
  .phase details.why summary:focus-visible{outline:2px solid var(--food);outline-offset:2px}

  footer{
    margin-top:26px;font-family:var(--f-data);font-size:13px;color:var(--muted2);
    display:flex;justify-content:space-between;align-items:center;
  }
  #status.offline{color:var(--food)}

  @media (prefers-reduced-motion:reduce){
    .card{transition:none} .card:active{transform:none}
  }
</style>
</head>
<body>

<div class="pw-bar">
  <span></span>
  <div id="switcher"></div>
</div>

<header>
  <p class="date" id="date">Pairwell</p>
  <h1><span id="greeting">Hello</span>, <span class="who" id="name">Philipp</span></h1>
</header>

<main id="today"></main>

<footer>
  <span id="status">Available offline</span>
  <span>v3</span>
</footer>

<script src="app.js?v=__JSV__"></script>
<script>
const D = __DATA__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

var DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
function todayKey(){ return DAYS[(new Date().getDay() + 6) % 7]; }

function person(){ return PW.get(); }

/* ---- resolvers: each answers one question about today ---- */

function trainingToday(who, day){
  var rhythm = (D.training.weeklyRhythm[who] || []).filter(function(r){ return r.day === day; })[0];
  if(!rhythm) return null;
  if(rhythm.type !== "training") return { rest:true, what: rhythm.what };

  /* Preferred location first, then anywhere else. Sunday's shared session is
     defined at home and travel only — a gym-preferring person would find
     nothing there, and must never be handed a different day's session
     instead. That fallback used to show Tuesday's Push every Sunday. */
  var pref = "gym";
  try{
    var st = JSON.parse(localStorage.getItem("hub.workout." + who) || "null");
    if(st && st.loc && D.training.sessions[st.loc]) pref = st.loc;
  }catch(e){}

  var LONG = {Mon:"Monday",Tue:"Tuesday",Wed:"Wednesday",Thu:"Thursday",
              Fri:"Friday",Sat:"Saturday",Sun:"Sunday"};
  var want = LONG[day].toLowerCase();

  function findAt(loc){
    var atLoc = D.training.sessions[loc] || {};
    var pool = [];
    Object.keys(atLoc[who] || {}).forEach(function(k){ pool.push(atLoc[who][k]); });
    Object.keys(atLoc.shared || {}).forEach(function(k){ pool.push(atLoc.shared[k]); });
    return pool.filter(function(s){
      return (s.day||"").toLowerCase().indexOf(want) !== -1;
    })[0] || null;
  }

  var order = [pref].concat(Object.keys(D.training.sessions).filter(function(l){
    return l !== pref;
  }));
  for(var i = 0; i < order.length; i++){
    var hit = findAt(order[i]);
    if(hit) return { rest:false, session:hit, loc:order[i],
                     elsewhere:(order[i] !== pref), what:rhythm.what };
  }

  /* A training day with no session recorded for it. Say so plainly. */
  return { rest:false, session:null, what:rhythm.what };
}

/* Hair, but only when it has something to say. Same one-date-per-treatment
   store the Hair page writes — the Hub reads it, never writes it. */
function hairDue(who){
  var sched = (D.routines.hair && D.routines.hair.scheduled) || [];
  var code = PW.PEOPLE[who].code;
  var t0 = new Date(); t0.setHours(0,0,0,0);

  return sched.filter(function(t){
    return t.who === "both" || t.who === who;
  }).map(function(t){
    var raw = null;
    try{ raw = localStorage.getItem("hub.hair.done." + t.id + "." + code); }catch(e){}
    if(!raw) return { t:t, state:"unknown", days:null };
    var d = new Date(raw + "T00:00:00");
    if(isNaN(d)) return { t:t, state:"unknown", days:null };
    var days = Math.round((t0 - d) / 86400000);
    var due = t.everyDays || 7;
    var late = t.everyDaysMax || due;
    if(days === 0) return { t:t, state:"done", days:0 };
    if(days >= late && late > due) return { t:t, state:"late", days:days };
    if(days > due && late === due) return { t:t, state:"late", days:days };
    if(days >= due) return { t:t, state:"due", days:days };
    return { t:t, state:"soon", days:days };
  }).filter(function(x){
    return x.state === "due" || x.state === "late" || x.state === "unknown";
  });
}

function seasonFor(r){
  if(!r.seasons) return null;
  var m = new Date().getMonth()+1;
  for(var k in r.seasons){
    if(r.seasons[k].monthNumbers.indexOf(m) !== -1) return r.seasons[k];
  }
  return null;
}

function skincareToday(who, day){
  var r = D.routines.skincare[who];
  if(!r) return null;
  var season = seasonFor(r);
  var out = { am:null, pm:null, pmLabel:null, rules:[] };

  if(season){
    out.am = season.am;
    var ev = season.pmWeekly.filter(function(e){ return e.day === day; })[0];
    if(ev){ out.pm = ev.steps.join(" · "); out.pmLabel = ev.focus; }
  } else if(r.phases){
    out.am = r.am;
    var want = null;
    try{ want = localStorage.getItem("hub.phase." + who); }catch(e){}
    var phase = r.phases.filter(function(p){ return p.id === (want || r.currentPhase); })[0]
             || r.phases[r.phases.length-1];
    var entry = phase.schedule.filter(function(e){ return e.day === day; })[0];
    var act = entry && entry.active && r.actives[entry.active];
    out.pmLabel = act ? act.name : "Rest night";
    out.pm = act ? "Cleanse · dry fully · " + act.name.toLowerCase() + " · hyaluronic · eye · moisturise"
                 : "Cleanse · hyaluronic · eye · moisturise";
  }

  out.rules = (r.safetyRules || []).filter(function(x){
    return x.appliesTo && x.appliesTo.indexOf(day.toLowerCase()) !== -1 && x.critical;
  });
  return out;
}

function card(href, accent, kicker, meta, headline, detail){
  return '<a class="card" href="' + href + '" style="--accent:' + accent + '">' +
    '<div class="ch"><span class="k">' + esc(kicker) + '</span>' +
    (meta ? '<span class="meta">' + esc(meta) + '</span>' : '') + '</div>' +
    '<div class="cb"><div class="headline">' + headline + '</div>' +
    (detail ? '<div class="detail">' + detail + '</div>' : '') +
    '</div></a>';
}

function render(){
  var who = person();
  var day = todayKey();
  var hour = new Date().getHours();
  var prof = D.profiles.people[who];

  document.getElementById("name").textContent = PW.PEOPLE[who].name;

  var skin = skincareToday(who, day);
  var train = trainingToday(who, day);

  /* Morning */
  var morning = "";
  if(skin && skin.am){
    var steps = skin.am.steps.map(function(s){
      return typeof s === "string" ? s : s.step;
    });
    morning = card("skincare/", "var(--skin)", "Morning",
      skin.am.durationMin ? skin.am.durationMin + " min" : "",
      esc(steps.length + " steps"),
      esc(steps.join(" · ")));
  }

  /* Training */
  var training = "";
  if(train){
    if(train.rest){
      training = card("workout/", "var(--train)", "Training", "",
        '<span class="rest">' + esc(train.what || "Rest day") + '</span>', "");
    } else if(!train.session){
      /* Better to admit the gap than to show the wrong workout. */
      training = card("workout/", "var(--train)", "Training", "",
        '<span class="rest">' + esc(train.what || "Training day") + '</span>',
        "No session recorded for today.");
    } else {
      var s = train.session;
      var names = s.exercises.slice(0,3).map(function(e){ return e.name; }).join(" · ");
      var together = /together|with /i.test(s.day || "");
      training = card("workout/", "var(--train)", "Training",
        train.loc.charAt(0).toUpperCase() + train.loc.slice(1) +
          (together ? " · together" : ""),
        esc(s.title),
        '<span class="pw-num">' + s.exercises.length + ' exercises</span>' +
        (s.durationMin ? ' <span class="sep">·</span> <span class="pw-num">~' + s.durationMin + ' min</span>' : '') +
        '<br>' + esc(names) + ' …');
    }
  }

  /* Food — the targets are constants and were the only thing this card showed.
     What actually changed today is the plan, and it was already sitting in
     localStorage one page away. */
  var t = prof.dailyTargets;
  var blocks = D.kitchen.asianMacroBase.blockRules.standardLeanDish;

  var plan = null;
  try{ plan = JSON.parse(localStorage.getItem("hub.kitchen.plan") || "null"); }catch(e){}
  function mealName(id){ return id && D.mealTitles[id] ? D.mealTitles[id] : null; }
  var lunch  = plan ? mealName(plan.lunch)  : null;
  var dinner = plan ? mealName(plan.dinner) : null;

  var targetsRow =
    '<div class="targets">' +
      '<div>Protein<b>' + t.proteinG + ' g</b></div>' +
      '<div>Fibre<b>' + t.fiberG + ' g</b></div>' +
      '<div>Fat<b>' + t.fatG + ' g</b></div>' +
    '</div>';

  var food;
  if(lunch || dinner){
    /* Lead with the meal you have not eaten yet. */
    var next = (hour >= 15 ? (dinner || lunch) : (lunch || dinner));
    food = card("kitchen/", "var(--food)", "Food",
      t.calories + " kcal",
      esc(next),
      '<div class="meals">' +
        (lunch  ? '<div><span>Lunch</span>'  + esc(lunch)  + '</div>' : '') +
        (dinner ? '<div><span>Dinner</span>' + esc(dinner) + '</div>' : '') +
      '</div>' + targetsRow);
  } else {
    food = card("kitchen/", "var(--food)", "Food",
      blocks + (blocks === 1 ? " block / meal" : " blocks / meal"),
      esc(t.calories + " kcal"),
      targetsRow);
  }

  /* Why the number changed. Without this the target just moves one day and
     the scale goes up a kilo two days later, which reads as failure. */
  var ph = prof._phase;
  if(ph){
    food = food.replace("</a>",
      '</a><div class="phase"><div class="pt">' + esc(ph.name) + '</div>' +
      '<div class="pm">' + (ph.was == null ? '' :
        'was ' + esc(String(ph.was)) + ' kcal <span class="sep">·</span> ') +
      'review ' + esc(ph.reviewOn) + '</div>' +
      /* The reasoning matters, but not at a glance — a dashboard is for
         recognition, and this was 45 words of it. */
      (ph.expect ? '<details class="why"><summary>What to expect</summary>' +
        '<p>' + esc(ph.expect) + '</p></details>' : '') +
      '</div>');
  }

  /* Tonight */
  var tonight = "";
  if(skin && skin.pm){
    tonight = card("skincare/", "var(--skin)", "Tonight", "",
      esc(skin.pmLabel || "Evening routine"), esc(skin.pm));
    if(skin.rules.length){
      var r = skin.rules[0];
      tonight = tonight.replace("</a>",
        '</a><div class="warn"><div><div class="wt">&#9888; ' + esc(r.title) + '</div>' +
        '<p>' + esc(r.rule) + '</p></div></div>');
    }
  }

  /* Hair — silent unless something is actually due. A card that says
     "nothing to do" every day is a card you stop reading. */
  var hair = "";
  var due = hairDue(who);
  if(due.length){
    var lead = due[0];
    hair = card("hair/", "var(--hair)", "Hair",
      due.length > 1 ? due.length + " due" : "",
      esc(lead.t.title),
      esc(lead.state === "unknown"
            ? "Never logged — " + lead.t.cadence.toLowerCase()
            : lead.state === "late"
              ? "Overdue — last done " + lead.days + " days ago"
              : "Due — last done " + lead.days + " days ago") +
      (due.length > 1
        ? ' <span class="sep">·</span> plus ' + esc(due[1].t.title.toLowerCase())
        : ''));
  }

  /* After 18:00 tonight leads. Before that, the morning does. */
  var order = hour >= 18
    ? [tonight, hair, training, food, morning]
    : [morning, hair, training, food, tonight];

  document.getElementById("today").innerHTML = order.join("");
}

/* header chrome */
(function(){
  var d = new Date();
  var days = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  var months = ["January","February","March","April","May","June",
                "July","August","September","October","November","December"];
  document.getElementById("date").textContent =
    days[d.getDay()] + ", " + d.getDate() + " " + months[d.getMonth()];
  var h = d.getHours();
  document.getElementById("greeting").textContent =
    h < 5 ? "Good night" : h < 11 ? "Good morning" : h < 18 ? "Hello" : "Good evening";
})();

(function(){
  var el = document.getElementById("status");
  function paint(){
    el.textContent = navigator.onLine ? "Available offline" : "Offline — showing saved version";
    el.classList.toggle("offline", !navigator.onLine);
  }
  window.addEventListener("online", paint);
  window.addEventListener("offline", paint);
  paint();
})();

PW.mountRail();
PW.mountThemeToggle(document.getElementById("switcher"));
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs("hub", "");
window.addEventListener("pw:person", render);
render();
PW.registerServiceWorker("sw.js");
</script>

</body>
</html>
"""

html = HTML.replace("__DATA__", data_json).replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written index.html  (%d bytes)" % len(html))

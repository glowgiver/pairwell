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

import json
import os

BASE = os.path.dirname(__file__)
OUT = os.path.join(BASE, "..", "hub", "index.html")

def load(name):
    return json.load(open(os.path.join(BASE, "..", "data", name), encoding="utf-8"))

data = {
    "profiles": load("profiles.json"),
    "training": load("training.json"),
    "routines": load("routines.json"),
    "kitchen": load("kitchen.json"),
}
data_json = json.dumps(data, ensure_ascii=False)

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
<link rel="stylesheet" href="app.css">
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
    border-radius:0 10px 10px 0;border-left:3px solid #F4666F;
    background:rgba(244,102,111,.10);
  }
  .warn .wt{
    font-family:var(--f-data);font-size:12.5px;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;color:#F4666F;
  }
  .warn p{margin:4px 0 0;font-family:var(--f-read);font-size:14.5px;line-height:1.5;color:var(--text)}

  .targets{display:flex;gap:16px;flex-wrap:wrap;margin-top:8px}
  .targets div{font-family:var(--f-data);font-size:13px;color:var(--muted2);
    font-variant-numeric:tabular-nums}
  .targets b{display:block;font-size:17px;color:var(--text);font-weight:700;margin-top:2px}

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

<script src="app.js"></script>
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

  /* Find the session whose day label mentions today, at whichever location
     that person last used. Falls back to the first session. */
  var loc = "gym";
  try{
    var st = JSON.parse(localStorage.getItem("hub.workout." + who) || "null");
    if(st && st.loc && D.training.sessions[st.loc]) loc = st.loc;
  }catch(e){}
  var atLoc = D.training.sessions[loc] || {};
  var pool = [];
  Object.keys(atLoc[who] || {}).forEach(function(k){ pool.push(atLoc[who][k]); });
  Object.keys(atLoc.shared || {}).forEach(function(k){ pool.push(atLoc.shared[k]); });

  var LONG = {Mon:"Monday",Tue:"Tuesday",Wed:"Wednesday",Thu:"Thursday",
              Fri:"Friday",Sat:"Saturday",Sun:"Sunday"};
  var hit = pool.filter(function(s){
    return (s.day||"").toLowerCase().indexOf(LONG[day].toLowerCase()) !== -1;
  })[0] || pool[0];

  return hit ? { rest:false, session:hit, loc:loc, what:rhythm.what } : { rest:true, what:rhythm.what };
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
    } else {
      var s = train.session;
      var names = s.exercises.slice(0,3).map(function(e){ return e.name; }).join(" · ");
      training = card("workout/", "var(--train)", "Training",
        train.loc.charAt(0).toUpperCase()+train.loc.slice(1),
        esc(s.title),
        '<span class="pw-num">' + s.exercises.length + ' exercises</span>' +
        (s.durationMin ? ' <span class="sep">·</span> <span class="pw-num">~' + s.durationMin + ' min</span>' : '') +
        '<br>' + esc(names) + ' …');
    }
  }

  /* Food */
  var t = prof.dailyTargets;
  var blocks = D.kitchen.asianMacroBase.blockRules.standardLeanDish;
  var food = card("kitchen/", "var(--food)", "Food",
    blocks + " blocks / meal",
    esc(t.calories + " kcal"),
    '<div class="targets">' +
      '<div>Protein<b>' + t.proteinG + ' g</b></div>' +
      '<div>Fibre<b>' + t.fiberG + ' g</b></div>' +
      '<div>Fat<b>' + t.fatG + ' g</b></div>' +
    '</div>');

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

  /* After 18:00 tonight leads. Before that, the morning does. */
  var order = hour >= 18
    ? [tonight, training, food, morning]
    : [morning, training, food, tonight];

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
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs(null, "");
window.addEventListener("pw:person", render);
render();
PW.registerServiceWorker("sw.js");
</script>

</body>
</html>
"""

html = HTML.replace("__DATA__", data_json)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written index.html  (%d bytes)" % len(html))

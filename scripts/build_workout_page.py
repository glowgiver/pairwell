import json, os

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "..", "data", "training.json")
OUT_PATH = os.path.join(BASE, "..", "hub", "workout", "index.html")

data = json.load(open(DATA_PATH, encoding="utf-8"))
data_json = json.dumps(data, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Workout · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css">
<style>
  /* Palette lives in ../app.css — only the accent choice is page-local. */
  :root{ --accent:var(--train); }

  body{
    background:var(--bg);
    color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    -webkit-font-smoothing:antialiased;
    min-height:100dvh;
    padding:
      calc(env(safe-area-inset-top) + 22px)
      calc(env(safe-area-inset-right) + 16px)
      calc(env(safe-area-inset-bottom) + 32px)
      calc(env(safe-area-inset-left) + 16px);
    max-width:640px;
    margin:0 auto;
  }

  h1{font-size:27px;font-weight:700;letter-spacing:-.02em;margin:0 0 4px;color:var(--train)}
  .sub{font-size:13px;color:var(--muted);margin:0 0 20px}

  /* location pills */
  .pills{display:flex;gap:8px;margin-bottom:16px}
  .pill{
    flex:1;min-height:var(--tap);padding:9px 6px;border-radius:12px;
    border:1px solid var(--line);background:var(--surface);
    text-align:center;cursor:pointer;font-family:inherit;
    color:var(--muted);transition:background .15s;
  }
  .pill b{display:block;font-size:13px;font-weight:700;color:var(--text)}
  .pill span{display:block;font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin-top:2px}
  .pill[aria-pressed="true"]{background:var(--train);border-color:var(--train)}
  .pill[aria-pressed="true"] b, .pill[aria-pressed="true"] span{color:#fff}
  .pill[aria-pressed="true"] span{color:rgba(255,255,255,.75)}
  .pill:focus-visible{outline:2px solid var(--train);outline-offset:2px}

  .stage{
    border:1px solid var(--line);border-radius:14px;
    background:var(--surface);overflow:hidden;
  }

  .profile{padding:16px 18px;border-bottom:1px solid var(--line);position:relative}
  .profile::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--accent)}
  .pname{font-size:19px;font-weight:700;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .pbadge{
    font-size:9.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
    padding:2px 8px;border-radius:20px;background:var(--accent);color:#fff;
  }
  .pgoal{font-size:12px;color:var(--muted);margin-top:3px;font-style:italic}
  .pmeta{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}
  .pmeta div{font-size:9.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2)}
  .pmeta strong{display:block;font-size:13px;color:var(--text);text-transform:none;letter-spacing:0;margin-top:2px;font-weight:700}

  .notice{padding:11px 18px;font-size:12px;line-height:1.55;color:var(--muted);border-bottom:1px solid var(--line);background:var(--surface-2)}
  .notice strong{color:var(--text)}

  .sess-tabs{display:flex;border-bottom:1px solid var(--line)}
  .sess-tab{
    flex:1;min-height:var(--tap);padding:9px 6px;text-align:center;cursor:pointer;
    font-size:12px;font-weight:700;color:var(--muted);
    background:none;border:0;border-bottom:2px solid transparent;
    font-family:inherit;
  }
  .sess-tab span{display:block;font-size:9px;font-weight:400;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-top:2px}
  .sess-tab[aria-selected="true"]{color:var(--text);border-bottom-color:var(--accent)}
  .sess-tab.together[aria-selected="true"]{border-bottom-color:var(--eunice)}
  .sess-tab:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}

  .sess-head{padding:16px 18px 12px;border-bottom:1px solid var(--line)}
  .sess-title{font-size:22px;font-weight:700;letter-spacing:-.01em}
  .sess-focus{font-size:12px;color:var(--muted);font-style:italic;margin-top:3px}

  .opt-banner{
    margin:14px 18px 0;padding:11px 14px;border-radius:10px;
    border:1px dashed var(--line);background:var(--surface-2);
    font-size:12px;color:var(--muted);line-height:1.55;
  }
  .opt-banner strong{color:var(--text)}

  .tier-head{display:flex;align-items:center;gap:8px;padding:14px 18px 6px}
  .tier-dot{width:9px;height:9px;border-radius:50%}
  .tier-dot.primary{background:var(--accent)}
  .tier-dot.maint{background:var(--muted2)}
  .tier-name{font-size:13px;font-weight:700}
  .tier-desc{font-size:9.5px;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-left:auto}

  .ex{border-bottom:1px solid var(--line);padding:12px 18px}
  .ex:last-child{border-bottom:none}
  .ex.maint{background:rgba(255,255,255,.015)}
  .ex-name{font-size:14.5px;font-weight:700;margin-bottom:2px}
  .ex-ref{font-size:10.5px;color:var(--muted2);margin-bottom:6px}
  .tag-row{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
  .tag{font-size:10px;padding:2.5px 8px;border-radius:5px;border:1px solid var(--line);color:var(--muted)}
  .tag.sr{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
  .tag.load{background:var(--surface-2);color:var(--text);border-color:var(--line)}
  .ex-cue{font-size:12px;color:var(--muted);line-height:1.55}
  .ex-cue strong{color:var(--text)}

  .duo{display:flex;gap:0;margin-top:8px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
  .duo-half{flex:1;padding:8px 10px;font-size:11.5px;line-height:1.4}
  .duo-half.p{background:rgba(90,141,238,.08);border-right:1px solid var(--line)}
  .duo-half.e{background:rgba(201,166,242,.08)}
  .duo-half .who{font-size:9px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);display:block;margin-bottom:3px}
  .duo-half strong{color:var(--text)}

  /* guide */
  .guide{padding:4px 0}
  .ref-card{margin:14px 18px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--bg)}
  .ref-head{padding:13px 15px;border-bottom:1px solid var(--line);background:var(--surface-2)}
  .ref-title{font-size:16.5px;font-weight:700}
  .ref-intro{font-size:11.5px;color:var(--muted);line-height:1.55;margin-top:5px}
  .ref-intro strong{color:var(--text)}
  .ref-body{padding:4px 15px}
  .ref-item{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:9px 0;border-bottom:1px solid var(--line)}
  .ref-item:last-child{border-bottom:none}
  .ref-item-k{font-size:11px;font-weight:700;color:var(--accent)}
  .ref-item-v{font-size:11.5px;color:var(--muted);line-height:1.55}
  .ref-item-v strong{color:var(--text)}
  .hr-zone{display:flex;gap:6px;margin:10px 0}
  .hrz{flex:1;text-align:center;padding:9px 6px;border-radius:8px;border:1px solid var(--line)}
  .hrz.z2{background:rgba(90,141,238,.1);border-color:var(--accent)}
  .hrz-n{font-size:14px;font-weight:700}
  .hrz-l{font-size:8.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2);margin-top:2px}

  @media (prefers-reduced-motion:reduce){ * { transition:none !important } }
</style>
</head>
<body>

<div class="pw-bar">
  <a class="pw-back" href="../"><svg viewBox="0 0 24 24"><path d="m15 5-7 7 7 7"/></svg> Hub</a>
  <div id="switcher"></div>
</div>

<h1>Workout</h1>
<p class="sub">Gym, home, travel — set to whoever this phone belongs to.</p>

<div class="pills" id="pills"></div>
<div class="stage" id="stage"></div>

<script src="../app.js"></script>
<script>
const T = __DATA__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

var state = { loc: "gym", sess: null };

function person(){ return PW.get(); }

var LOC_LABEL = {
  gym: ["Gym","Cable + machines"],
  home: ["Home","Bodylastics"],
  travel: ["Travel","Tubes only"],
  guide: ["Guide","Week + cardio"]
};

function el(tag, cls, html){
  var e = document.createElement(tag || "div");
  if(cls) e.className = cls;
  if(html !== undefined) e.innerHTML = html;
  return e;
}

/* Sessions available to the current person at the current location:
   their own, plus the Sunday session they train together. "Together" is a
   session, not a third person — it belongs in both their weeks. */
function sessionsFor(loc, who){
  var atLoc = T.sessions[loc] || {};
  var out = [];
  var own = atLoc[who] || {};
  Object.keys(own).forEach(function(k){
    out.push({ key: who + ":" + k, data: own[k], together: false });
  });
  var shared = atLoc.shared || {};
  Object.keys(shared).forEach(function(k){
    out.push({ key: "shared:" + k, data: shared[k], together: true });
  });
  return out;
}

function setLoc(loc){
  state.loc = loc; state.sess = null;
  renderPills(); renderStage();
}
function setSess(s){ state.sess = s; renderStage(); }

function renderPills(){
  var wrap = document.getElementById("pills");
  wrap.innerHTML = "";
  ["gym","home","travel","guide"].forEach(function(loc){
    var lbl = LOC_LABEL[loc];
    var p = el("button", "pill",
      "<b>" + esc(lbl[0]) + "</b><span>" + esc(lbl[1]) + "</span>");
    p.type = "button";
    p.setAttribute("aria-pressed", String(state.loc === loc));
    p.addEventListener("click", function(){ setLoc(loc); });
    wrap.appendChild(p);
  });
}

function tagHTML(extras){
  var out = "";
  for(var k in extras){
    out += '<span class="tag' + (k==="load" ? " load" : "") + '">' + esc(extras[k]) + '</span>';
  }
  return out;
}

var FOCUS_LABEL = { a: "upper body", g: "legs / glutes", p: "inner thigh", c: "core" };

function exHTML(e){
  var duoBlock = "";
  if(e.shared){
    duoBlock = '<div class="duo">' +
      '<div class="duo-half p"><span class="who">Philipp</span><strong>' + esc(e.philippLoad) + '</strong></div>' +
      '<div class="duo-half e"><span class="who">Eunice</span><strong>' + esc(e.euniceLoad) + '</strong></div>' +
      '</div>';
  }
  return '<div class="ex' + (e.tier === "maint" ? " maint" : "") + '">' +
    '<div class="ex-name">' + esc(e.name) + '</div>' +
    (e.ref ? '<div class="ex-ref">' + esc(e.ref) + '</div>' : '') +
    '<div class="tag-row">' +
      '<span class="tag sr">' + esc(e.sets) + ' × ' + esc(e.reps) + '</span>' +
      '<span class="tag">' + esc(FOCUS_LABEL[e.focus]) + '</span>' +
      tagHTML(e.extras) +
    '</div>' +
    (e.cue ? '<div class="ex-cue">' + esc(e.cue) + '</div>' : '') +
    duoBlock +
    '</div>';
}

function renderStage(){
  var stage = document.getElementById("stage");
  var who = person();

  if(state.loc === "guide"){
    stage.innerHTML = profileHTML() + guideHTML();
    return;
  }

  var list = sessionsFor(state.loc, who);

  if(!list.length){
    stage.innerHTML = profileHTML() + noticeHTML() +
      '<div style="padding:36px 18px;text-align:center;color:var(--muted);font-size:13px">' +
      'No plan for this combination yet.</div>';
    return;
  }

  var keys = list.map(function(s){ return s.key; });
  if(!state.sess || keys.indexOf(state.sess) === -1) state.sess = keys[0];
  var current = list.filter(function(s){ return s.key === state.sess; })[0];
  var sess = current.data;

  var tabs = list.map(function(s){
    return '<button type="button" role="tab" class="sess-tab' + (s.together ? " together" : "") +
      '" aria-selected="' + (state.sess === s.key) + '" data-sess="' + esc(s.key) + '">' +
      esc(s.data.title) + '<span>' + esc(s.data.day) + '</span></button>';
  }).join("");

  var primary = sess.exercises.filter(function(e){ return e.tier === "primary"; });
  var maint = sess.exercises.filter(function(e){ return e.tier === "maint"; });

  stage.innerHTML =
    profileHTML() +
    noticeHTML() +
    '<div class="sess-tabs" role="tablist">' + tabs + '</div>' +
    '<div class="sess-head"><div class="sess-title">' + esc(sess.title) + '</div>' +
    '<div class="sess-focus">' + esc(sess.focus) + '</div></div>' +
    (sess.note ? '<div class="opt-banner">' + esc(sess.note) + '</div>' : '') +
    '<div class="tier-head"><span class="tier-dot primary"></span><span class="tier-name">Primary</span>' +
    '<span class="tier-desc">Progressive · RIR 2</span></div>' +
    primary.map(exHTML).join("") +
    (maint.length ? '<div class="tier-head"><span class="tier-dot maint"></span><span class="tier-name">Maintenance</span>' +
    '<span class="tier-desc">2 sets · RIR 3 · never progress</span></div>' +
    maint.map(exHTML).join("") : "");

  stage.querySelectorAll("[data-sess]").forEach(function(t){
    t.addEventListener("click", function(){ setSess(t.getAttribute("data-sess")); });
  });
}

function profileHTML(){
  var who = person();
  var prof = T.profiles[who];
  var meta = "";
  for(var k in prof.meta){
    meta += '<div>' + esc(k) + '<strong>' + esc(prof.meta[k]) + '</strong></div>';
  }
  return '<div class="profile" style="--accent:' + (who === "eunice" ? "var(--eunice)" : "var(--philipp)") + '">' +
    '<div class="pname">' + esc(PW.PEOPLE[who].name) + '<span class="pbadge">' + esc(prof.badge) + '</span></div>' +
    '<div class="pgoal">' + esc(prof.goal) + '</div>' +
    '<div class="pmeta">' + meta + '</div>' +
    '</div>';
}

function noticeHTML(){
  var note = T.locationNotes[state.loc];
  return note ? '<div class="notice">' + esc(note) + '</div>' : "";
}

function guideHTML(){
  var wk = T.weeklyRhythm[person()] || [];
  var wkRows = wk.map(function(d){
    return '<div class="ref-item"><div class="ref-item-k">' + esc(d.day) + '</div>' +
      '<div class="ref-item-v">' + esc(d.what) + '</div></div>';
  }).join("");
  var weekCard = '<div class="ref-card"><div class="ref-head"><div class="ref-title">Your week</div></div>' +
    '<div class="ref-body">' + wkRows + '</div></div>';

  var c = T.cardioProtocol;
  var z = c.zone2;
  var cardioCard = '<div class="ref-card"><div class="ref-head"><div class="ref-title">Zone 2 cardio</div>' +
    '<div class="ref-intro">' + c.context + '</div></div><div class="ref-body">' +
    '<div class="hr-zone">' +
    '<div class="hrz"><div class="hrz-n">&lt;106</div><div class="hrz-l">Zone 1</div></div>' +
    '<div class="hrz z2"><div class="hrz-n">' + z.heartRateRange.split(" ")[0] + '</div><div class="hrz-l">Zone 2 ✓</div></div>' +
    '<div class="hrz"><div class="hrz-n">&gt;124</div><div class="hrz-l">too high</div></div>' +
    '</div>' +
    '<div class="ref-item"><div class="ref-item-k">Setup</div><div class="ref-item-v">' + z.padSettings + ' · ' + z.note + '</div></div>' +
    '<div class="ref-item"><div class="ref-item-k">Duration</div><div class="ref-item-v">' + z.duration + ', ' + z.schedule + '</div></div>' +
    '<div class="ref-item"><div class="ref-item-k">Evening</div><div class="ref-item-v">' + z.eveningRule + '</div></div>' +
    '</div></div>';

  var s = T.cardioProtocol.stepTarget;
  var stepsCard = '<div class="ref-card"><div class="ref-head"><div class="ref-title">Steps · the real lever</div></div>' +
    '<div class="ref-body">' +
    '<div class="ref-item"><div class="ref-item-k">Current</div><div class="ref-item-v">' + s.current + '</div></div>' +
    '<div class="ref-item"><div class="ref-item-k">Goal</div><div class="ref-item-v"><strong>' + s.goal + '/day</strong></div></div>' +
    '<div class="ref-item"><div class="ref-item-k">Parking</div><div class="ref-item-v">' + s.parkingHack + '</div></div>' +
    '<div class="ref-item"><div class="ref-item-k">Why</div><div class="ref-item-v">' + s.why + '</div></div>' +
    '</div></div>';

  var p = T.progression[person()];
  var progCard = p ? '<div class="ref-card"><div class="ref-head"><div class="ref-title">Progression</div>' +
    '<div class="ref-intro">' + p.method + '</div></div><div class="ref-body">' +
    '<div class="ref-item"><div class="ref-item-k">Primary</div><div class="ref-item-v">' + p.primaryRule + '</div></div>' +
    (p.maintenanceRule ? '<div class="ref-item"><div class="ref-item-k">Maint.</div><div class="ref-item-v">' + p.maintenanceRule + '</div></div>' : '') +
    (p.mindMuscle ? '<div class="ref-item"><div class="ref-item-k">Focus</div><div class="ref-item-v">' + p.mindMuscle + '</div></div>' : '') +
    '<div class="ref-item"><div class="ref-item-k">Deload</div><div class="ref-item-v">' + p.deload + '</div></div>' +
    '</div></div>' : '';

  return '<div class="guide">' + weekCard + stepsCard + cardioCard + progCard + '</div>';
}

PW.mountRail();
PW.mountSwitcher(document.getElementById("switcher"));

// Switching person keeps the location but resets the session, since the
// two people don't train the same split.
window.addEventListener("pw:person", function(){
  state.sess = null;
  renderStage();
});

renderPills();
renderStage();
</script>

</body>
</html>
"""

html = html.replace("__DATA__", data_json)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("written, length:", len(html))

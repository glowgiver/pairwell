import json, os

BASE = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE, "..", "data", "training.json")
LIB_PATH = os.path.join(BASE, "..", "data", "exercises.json")
OUT_PATH = os.path.join(BASE, "..", "hub", "workout", "index.html")

data = json.load(open(DATA_PATH, encoding="utf-8"))
data_json = json.dumps(data, ensure_ascii=False)

# Demo links live in the exercise library. Sessions still carry their own
# exercise objects, so match on name (and on the aliases the library records
# for movements that were filed under two names).
lib = json.load(open(LIB_PATH, encoding="utf-8"))
videos = {}
for entry in lib["exercises"].values():
    v = entry.get("video")
    if not v:
        continue
    for name in [entry["name"]] + entry.get("aliases", []):
        videos[name] = v["url"]

session_names = {
    e["name"]
    for loc in data["sessions"].values()
    for person in loc.values()
    for s in person.values()
    for e in s["exercises"]
}
unmatched = sorted(session_names - set(videos))
if unmatched:
    print("WARNING: no demo video for:", ", ".join(unmatched))

videos_json = json.dumps(videos, ensure_ascii=False)

def _digest(rel):
    """Content hash for a shared asset, so a stale HTTP cache entry cannot
    outlive a change. The service worker revalidates eventually; this closes
    the window before it does."""
    import hashlib
    p = os.path.join(BASE, "..", "hub", rel)
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:8]

ASSET_V = {"css": _digest("app.css"), "js": _digest("app.js")}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Workout · Pairwell</title>
<meta name="theme-color" content="#0B1220">
<link rel="stylesheet" href="../app.css?v=__CSSV__">
<style>
  /* Palette lives in ../app.css — only the accent choice is page-local. */
  :root{ --accent:var(--train); }

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

  h1{font-size:27px;font-weight:700;letter-spacing:-.02em;margin:0 0 4px;color:var(--train)}
  .sub{font-family:var(--f-read);font-size:15px;color:var(--muted);margin:0 0 20px;line-height:1.55}

  /* location pills */
  .pills{display:flex;gap:8px;margin-bottom:16px}
  .pill{
    flex:1;min-height:var(--tap);padding:9px 6px;border-radius:12px;
    border:1px solid var(--line);background:var(--surface);
    text-align:center;cursor:pointer;font-family:inherit;
    color:var(--muted);transition:background .15s;
  }
  .pill b{display:block;font-size:15px;font-weight:700;color:var(--text)}
  .pill span{display:block;font-family:var(--f-data);font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);margin-top:2px}
  .pill[aria-pressed="true"]{background:var(--train);border-color:var(--train)}
  .pill[aria-pressed="true"] b, .pill[aria-pressed="true"] span{color:var(--bg)}
  /* Weight only. This used to say color:inherit, which inherited --muted from
     the button and put grey on the filled accent at 1.14:1 — the sub-label was
     invisible on whichever location was selected. Vary the weight, never the
     ink, on a filled accent. */
  .pill[aria-pressed="true"] span{font-weight:400}
  .pill:focus-visible{outline:2px solid var(--train);outline-offset:2px}

  .stage{
    border:1px solid var(--line);border-radius:14px;
    background:var(--surface);overflow:hidden;
  }

  .profile{padding:16px 18px;border-bottom:1px solid var(--line);position:relative}
  .profile::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--accent)}
  .pname{font-size:19px;font-weight:700;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
  .pbadge{
    font-family:var(--f-data);font-size:13px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
    padding:2px 8px;border-radius:20px;background:var(--accent);color:var(--bg);
  }
  .pgoal{font-size:13.5px;color:var(--muted);margin-top:3px;font-style:italic}
  .pmeta{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px}
  .pmeta div{font-family:var(--f-data);font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2)}
  .pmeta strong{display:block;font-size:13px;color:var(--text);text-transform:none;letter-spacing:0;margin-top:2px;font-weight:700}

  .notice{padding:12px 18px;font-family:var(--f-read);font-size:15px;line-height:1.6;color:var(--muted);border-bottom:1px solid var(--line);background:var(--surface-2)}
  .notice strong{color:var(--text)}

  .sess-tabs{display:flex;border-bottom:1px solid var(--line)}
  .sess-tab{
    flex:1;min-height:var(--tap);padding:9px 6px;text-align:center;cursor:pointer;
    font-size:14px;font-weight:700;color:var(--muted);
    background:none;border:0;border-bottom:2px solid transparent;
    font-family:inherit;
  }
  .sess-tab span{display:block;font-family:var(--f-data);font-size:13px;font-weight:400;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-top:2px}
  .sess-tab[aria-selected="true"]{color:var(--text);border-bottom-color:var(--accent)}
  .sess-tab.together[aria-selected="true"]{border-bottom-color:var(--eunice)}
  /* A day trained with the other person is underlined in *their* colour, so it
     reads the same from both sides. --partner is set inline per tab. */
  .sess-tab.duo[aria-selected="true"]{border-bottom-color:var(--partner)}
  .sess-tab:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}

  .sess-head{padding:16px 18px 12px;border-bottom:1px solid var(--line)}
  .sess-title{font-size:22px;font-weight:700;letter-spacing:-.01em}
  .sess-focus{font-size:13.5px;color:var(--muted);font-style:italic;margin-top:3px}
  .sess-dur{display:block;font-family:var(--f-data);font-variant-numeric:tabular-nums;font-size:13px;font-weight:400;color:var(--muted2);margin-top:3px}

  .opt-banner{
    margin:14px 18px 0;padding:11px 14px;border-radius:10px;
    border:1px dashed var(--line);background:var(--surface-2);
    font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.6;
  }
  .opt-banner strong{color:var(--text)}

  .tier-head{display:flex;align-items:center;gap:8px;padding:14px 18px 6px}
  .tier-dot{width:9px;height:9px;border-radius:50%}
  .tier-dot.primary{background:var(--accent)}
  .tier-dot.maint{background:var(--muted2)}
  .tier-name{font-size:15px;font-weight:700}
  .tier-desc{font-family:var(--f-data);font-size:13px;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-left:auto}

  .ex{border-bottom:1px solid var(--line);padding:12px 18px}
  .ex:last-child{border-bottom:none}
  .ex.maint{background:rgba(255,255,255,.015)}
  .ex-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
  .ex-name{font-size:17px;font-weight:700;letter-spacing:-.01em;margin-bottom:3px}
  .ex-ref{font-family:var(--f-data);font-size:13px;color:var(--muted2);margin-bottom:6px}

  /* Demo link. A plain link, not an embed: an iframe would load YouTube for
     every exercise on the page, including the ones nobody opens. */
  .demo{
    flex:none;display:inline-flex;align-items:center;gap:7px;
    min-height:var(--tap);padding:0 14px;border-radius:11px;
    border:1px solid var(--line);background:var(--surface-2);
    color:var(--accent);text-decoration:none;
    font-size:14px;font-weight:600;
  }
  .demo svg{width:15px;height:15px;fill:currentColor}
  .demo:active{background:var(--accent);color:var(--bg)}
  .demo:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  .tag-row{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-bottom:6px}
  .tag{font-family:var(--f-data);font-variant-numeric:tabular-nums;font-size:13px;padding:4px 10px;border-radius:6px;border:1px solid var(--line);color:var(--muted)}
  .tag.sr{background:var(--accent);color:var(--bg);border-color:var(--accent);
    font-weight:700;font-size:15px;padding:4px 11px;letter-spacing:.01em}
  .tag.load{background:var(--surface-2);color:var(--text);border-color:var(--line)}
  /* On a shared day every exercise is the same station unless it says here
     that it is not. Marking only the exceptions keeps five badges off the
     screen; the session banner states the rule. */
  .ex-solo{
    display:flex;align-items:flex-start;gap:8px;
    margin:9px 0 2px;padding:7px 11px;border-radius:9px;line-height:1.5;
    background:var(--surface-2);border:1px solid var(--line);
    font-family:var(--f-data);font-size:13px;color:var(--muted);
  }
  .ex-solo svg{width:15px;height:15px;flex:none;margin-top:2px;stroke:currentColor;fill:none;
    stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
  .ex-solo b{color:var(--text);font-weight:700}

  .ex-cue{font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.6}
  .ex-cue strong{color:var(--text)}

  /* On a shared station the other person's setting belongs on the card —
     whoever has their phone out sets both pins. */
  .ex-mate{
    display:flex;align-items:baseline;gap:8px;margin-top:8px;
    font-family:var(--f-data);font-size:13px;color:var(--muted);
  }
  .ex-mate .who{
    font-size:13px;text-transform:uppercase;letter-spacing:.05em;
    color:var(--bg);background:var(--mate);padding:2px 8px;border-radius:6px;
    font-weight:600;flex:none;
  }
  .ex-mate b{color:var(--text);font-variant-numeric:tabular-nums}

  /* In list order the tier has no heading to sit under, so it rides along
     as the first tag on the card. */
  .tag.tier{display:inline-flex;align-items:center;gap:6px}
  .tag.tier::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--accent)}
  .tag.tier.maint{color:var(--muted2)}
  .tag.tier.maint::before{background:var(--muted2)}

  .duo{display:flex;gap:0;margin-top:8px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
  .duo-half{flex:1;padding:10px 12px;font-size:14px;line-height:1.45}
  .duo-half.p{background:rgba(90,141,238,.08);border-right:1px solid var(--line)}
  .duo-half.e{background:rgba(201,166,242,.08)}
  .duo-half .who{font-family:var(--f-data);font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted2);display:block;margin-bottom:3px}
  .duo-half strong{color:var(--text)}

  /* guide */
  .guide{padding:4px 0}
  .ref-card{margin:14px 18px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--bg)}
  .ref-head{padding:13px 15px;border-bottom:1px solid var(--line);background:var(--surface-2)}
  .ref-title{font-size:18px;font-weight:700}
  .ref-intro{font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.55;margin-top:5px}
  .ref-intro strong{color:var(--text)}
  .ref-body{padding:4px 15px}
  .ref-item{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:9px 0;border-bottom:1px solid var(--line)}
  .ref-item:last-child{border-bottom:none}
  .ref-item-k{font-family:var(--f-data);font-size:13px;font-weight:700;color:var(--accent)}
  .ref-item-v{font-family:var(--f-read);font-size:15px;color:var(--muted);line-height:1.55}
  .ref-item-v strong{color:var(--text)}
  .hr-zone{display:flex;gap:6px;margin:10px 0}
  .hrz{flex:1;text-align:center;padding:9px 6px;border-radius:8px;border:1px solid var(--line)}
  .hrz.z2{background:rgba(90,141,238,.1);border-color:var(--accent)}
  .hrz-n{font-family:var(--f-data);font-variant-numeric:tabular-nums;font-size:18px;font-weight:700}
  .hrz-l{font-family:var(--f-data);font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted2);margin-top:2px}

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

<script src="../app.js?v=__JSV__"></script>
<script>
const T = __DATA__;
const VIDEOS = __VIDEOS__;

function esc(s){
  return String(s == null ? "" : s)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

/* A phone locks constantly during a workout. Without this, reopening drops you
   back on gym/push while the browser restores the old scroll offset — so you
   land deep inside a session you are not doing, and it looks like it
   remembered. Keyed per person: they train different splits. */
function stashKey(){ return "hub.workout." + PW.get(); }

function loadState(){
  try{
    var raw = localStorage.getItem(stashKey());
    if(raw){
      var v = JSON.parse(raw);
      if(v && LOC_LABEL[v.loc]) return { loc: v.loc, sess: v.sess || null };
    }
  }catch(e){}
  return { loc: "gym", sess: null };
}

function saveState(){
  try{ localStorage.setItem(stashKey(), JSON.stringify({loc: state.loc, sess: state.sess})); }
  catch(e){}
}

function person(){ return PW.get(); }

var LOC_LABEL = {
  gym: ["Gym","Cables"],
  home: ["Home","Bands"],
  travel: ["Travel","Tubes"],
  guide: ["Guide","Week"]
};

var state = loadState();

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
  saveState(); renderPills(); renderStage();
}
function setSess(s){ state.sess = s; saveState(); renderStage(); }

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

/* The partner's version of the same movement, by name. Only exact matches
   count, which is exactly right: those are the cards where the two of you
   stand at one station and swap the pin. Where the names differ (his fly and
   face pull against her superset of both) there is nothing to line up. */
function partnerExercises(sess){
  var map = {};
  if(!sess.partner) return map;
  var key = String(state.sess).split(":")[1];
  var theirs = ((T.sessions[state.loc] || {})[sess.partner.toLowerCase()] || {})[key];
  if(!theirs) return map;
  theirs.exercises.forEach(function(e){ map[e.name] = e; });
  return map;
}

function tagHTML(extras){
  var out = "";
  for(var k in extras){
    out += '<span class="tag' + (k==="load" ? " load" : "") + '">' + esc(extras[k]) + '</span>';
  }
  return out;
}

var FOCUS_LABEL = { a: "upper body", g: "legs / glutes", p: "inner thigh", c: "core" };

function exHTML(e, mate, mateName){
  var duoBlock = "";
  if(e.shared){
    duoBlock = '<div class="duo">' +
      '<div class="duo-half p"><span class="who">Philipp</span><strong>' + esc(e.philippLoad) + '</strong></div>' +
      '<div class="duo-half e"><span class="who">Eunice</span><strong>' + esc(e.euniceLoad) + '</strong></div>' +
      '</div>';
  }
  var demo = VIDEOS[e.name]
    ? '<a class="demo" href="' + esc(VIDEOS[e.name]) + '" target="_blank" rel="noopener noreferrer"' +
      ' aria-label="Watch a demo of ' + esc(e.name) + '">' +
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>Demo</a>'
    : '';

  /* Shown only in list order, where there is no tier heading above the card. */
  var tierTag = mateName
    ? '<span class="tag tier' + (e.tier === "maint" ? " maint" : "") + '">' +
      (e.tier === "maint" ? "maintenance" : "primary") + '</span>'
    : '';

  var mateLoad = (mate && mate.extras && mate.extras.load)
    ? '<div class="ex-mate" style="--mate:var(--' + esc(String(mateName).toLowerCase()) + ')">' +
      '<span class="who">' + esc(mateName) + '</span><b>' + esc(mate.extras.load) + '</b>' +
      '<span>' + esc(mate.sets) + ' × ' + esc(mate.reps) + '</span></div>'
    : '';

  return '<div class="ex' + (e.tier === "maint" ? " maint" : "") + '">' +
    '<div class="ex-head"><div><div class="ex-name">' + esc(e.name) + '</div>' +
    (e.ref ? '<div class="ex-ref">' + esc(e.ref) + '</div>' : '') + '</div>' +
    demo + '</div>' +
    '<div class="tag-row">' +
      tierTag +
      '<span class="tag sr">' + esc(e.sets) + ' × ' + esc(e.reps) + '</span>' +
      '<span class="tag">' + esc(FOCUS_LABEL[e.focus]) + '</span>' +
      tagHTML(e.extras) +
    '</div>' +
    (e.solo
      ? '<div class="ex-solo">' +
        '<svg viewBox="0 0 24 24" aria-hidden="true">' +
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>' +
        '<circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/></svg>' +
        '<span><b>On your own.</b> ' + esc(e.solo) + '.</span></div>'
      : '') +
    mateLoad +
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
    var partner = s.data.partner;
    return '<button type="button" role="tab" class="sess-tab' + (s.together ? " together" : "") +
      (partner ? " duo" : "") + '"' +
      (partner ? ' style="--partner:var(--' + esc(partner.toLowerCase()) + ')"' : '') +
      ' aria-selected="' + (state.sess === s.key) + '" data-sess="' + esc(s.key) + '">' +
      esc(s.data.title) + '<span>' + esc(s.data.day) + '</span></button>';
  }).join("");

  var primary = sess.exercises.filter(function(e){ return e.tier === "primary"; });
  var maint = sess.exercises.filter(function(e){ return e.tier === "maint"; });

  /* A session trained with the other person is rendered in list order, not
     grouped by tier. On your own the two tiers are the useful split — what to
     push, what to hold. Standing next to someone, the order you walk the gym
     in beats the label, and grouping by tier tore the two people's lists apart
     at different points. The tier still shows, as a dot on each card. */
  var body;
  if(sess.partner){
    var partnerSess = partnerExercises(sess);
    body = sess.exercises.map(function(e){
      return exHTML(e, partnerSess[e.name], sess.partner);
    }).join("");
  } else {
    body =
      '<div class="tier-head"><span class="tier-dot primary"></span><span class="tier-name">Primary</span>' +
      '<span class="tier-desc">Progressive · RIR 2</span></div>' +
      primary.map(function(e){ return exHTML(e); }).join("") +
      (maint.length ? '<div class="tier-head"><span class="tier-dot maint"></span><span class="tier-name">Maintenance</span>' +
      '<span class="tier-desc">2 sets · RIR 3 · never progress</span></div>' +
      maint.map(function(e){ return exHTML(e); }).join("") : "");
  }

  /* The exercises come first. The profile header is planning information —
     body-fat targets are not what you need on the third set. */
  stage.innerHTML =
    '<div class="sess-tabs" role="tablist">' + tabs + '</div>' +
    '<div class="sess-head"><div class="sess-title">' + esc(sess.title) +
    (sess.durationMin ? '<span class="sess-dur">' + esc(sess.exercises.length) +
      ' exercises &middot; ~' + esc(sess.durationMin) + ' min</span>' : '') + '</div>' +
    '<div class="sess-focus">' + esc(sess.focus) + '</div></div>' +
    (sess.note ? '<div class="opt-banner">' + esc(sess.note) + '</div>' : '') +
    body +
    noticeHTML() +
    profileHTML();

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
PW.mountThemeToggle(document.getElementById("switcher"));
PW.mountSwitcher(document.getElementById("switcher"));
PW.mountTabs("workout", "../");

// Switching person keeps the location but resets the session, since the
// two people don't train the same split.
window.addEventListener("pw:person", function(){
  var restored = loadState();
  state.loc = restored.loc; state.sess = restored.sess;
  renderPills(); renderStage();
});

renderPills();
renderStage();
saveState();
</script>

</body>
</html>
"""

html = html.replace("__DATA__", data_json)\
        .replace("__CSSV__", ASSET_V["css"]).replace("__JSV__", ASSET_V["js"])
html = html.replace("__VIDEOS__", videos_json)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("written, length:", len(html))

/* Pairwell — shared app behaviour.
   Owns the one thing every page needs: who is using it.

   Storage: localStorage["hub.person"] holds "P" or "E" (the format the
   workout page already expected). Safari's 7-day eviction of script-written
   storage does not apply to home-screen-installed web apps, which is how
   Pairwell is used. Losing it is harmless anyway — it falls back to Philipp
   and one tap restores it. */

(function (global) {
  "use strict";

  var KEY = "hub.person";

  var PEOPLE = {
    philipp: { id: "philipp", name: "Philipp", initial: "P", code: "P", color: "var(--philipp)" },
    eunice:  { id: "eunice",  name: "Eunice",  initial: "E", code: "E", color: "var(--eunice)"  }
  };

  var ORDER = ["philipp", "eunice"];
  var DEFAULT = "philipp";

  function get() {
    try {
      var v = localStorage.getItem(KEY);
      if (v === "P") return "philipp";
      if (v === "E") return "eunice";
    } catch (e) { /* private mode, blocked storage — fall through */ }
    return DEFAULT;
  }

  function set(id) {
    if (!PEOPLE[id]) return;
    try {
      localStorage.setItem(KEY, PEOPLE[id].code);
    } catch (e) { /* still switch for this session even if we can't persist */ }
    paintRail(id);
    global.dispatchEvent(new CustomEvent("pw:person", { detail: { person: id } }));
  }

  function person() { return PEOPLE[get()]; }

  /* Set on :root as well as the rail, so any page can tint a heading or a
     border with var(--who-active) without knowing who is selected. */
  function paintRail(id) {
    document.documentElement.style.setProperty("--who-active", PEOPLE[id].color);
    var rail = document.querySelector(".pw-person-rail");
    if (rail) rail.style.setProperty("--who-active", PEOPLE[id].color);
  }

  /* Renders the P / E switcher into `el`. Re-renders itself on change,
     so a page only has to listen for "pw:person" to update its own content. */
  function mountSwitcher(el) {
    if (!el) return;
    el.className = "pw-switch";
    el.setAttribute("role", "group");
    el.setAttribute("aria-label", "Active person");

    ORDER.forEach(function (id) {
      var p = PEOPLE[id];
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("data-person", id);
      b.style.setProperty("--who", p.color);
      b.innerHTML = '<span class="pw-dot" aria-hidden="true"></span>' + p.initial;
      b.setAttribute("aria-label", p.name);
      b.addEventListener("click", function () {
        if (get() !== id) set(id);
      });
      el.appendChild(b);
    });

    function paint() {
      var current = get();
      Array.prototype.forEach.call(el.children, function (b) {
        b.setAttribute("aria-pressed", String(b.getAttribute("data-person") === current));
      });
    }

    global.addEventListener("pw:person", paint);
    paint();
    paintRail(get());
  }

  /* Adds the fixed colour rail marking the active person. */
  function mountRail() {
    if (document.querySelector(".pw-person-rail")) return;
    var rail = document.createElement("div");
    rail.className = "pw-person-rail";
    rail.setAttribute("aria-hidden", "true");
    document.body.appendChild(rail);
    paintRail(get());
  }

  /* Four modules, each keeping its own accent so you know where you are.
     Icons match the ones the hub already used. */
  var TABS = [
    { id: "skincare", label: "Skincare", href: "skincare/", accent: "var(--skin)",
      path: '<path d="M12 3c-3.5 3.2-5.5 6-5.5 9a5.5 5.5 0 0 0 11 0c0-3-2-5.8-5.5-9Z"/><path d="M9.5 13.5a2.5 2.5 0 0 0 2.5 2.5"/>' },
    { id: "hair", label: "Hair", href: "hair/", accent: "var(--hair)",
      path: '<path d="M5 20c0-8 3-14 7-14s7 6 7 14"/><path d="M8.5 20c0-6 1.5-10 3.5-10s3.5 4 3.5 10"/>' },
    { id: "workout", label: "Workout", href: "workout/", accent: "var(--train)",
      path: '<path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10"/>' },
    { id: "kitchen", label: "Kitchen", href: "kitchen/", accent: "var(--food)",
      path: '<path d="M5 4v7a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V4"/><path d="M7 13v7"/><path d="M17 20V4c-1.7.8-2.5 2.7-2.5 5s.8 3.8 2.5 4"/>' }
  ];

  /* `current` is the module id, or null on the hub. `base` is the prefix that
     reaches the hub root — "" from the hub, "../" from a module page. */
  function mountTabs(current, base) {
    if (document.querySelector(".pw-tabs")) return;
    base = base === undefined ? "" : base;
    var nav = document.createElement("nav");
    nav.className = "pw-tabs";
    nav.setAttribute("aria-label", "Modules");
    nav.innerHTML = TABS.map(function (t) {
      var here = t.id === current;
      return '<a href="' + base + t.href + '" style="--tab:' + t.accent + '"' +
        (here ? ' aria-current="page"' : '') + '>' +
        '<svg viewBox="0 0 24 24" aria-hidden="true">' + t.path + '</svg>' +
        '<span>' + t.label + '</span></a>';
    }).join("");
    document.body.appendChild(nav);
  }

  function registerServiceWorker(path) {
    if (!("serviceWorker" in navigator)) return;
    global.addEventListener("load", function () {
      navigator.serviceWorker.register(path || "sw.js");
    });
  }

  /* Paint once as soon as the script runs, so the first render is correct. */
  if (document.documentElement) paintRail(get());

  global.PW = {
    PEOPLE: PEOPLE,
    ORDER: ORDER,
    get: get,
    set: set,
    person: person,
    mountSwitcher: mountSwitcher,
    mountRail: mountRail,
    mountTabs: mountTabs,
    TABS: TABS,
    registerServiceWorker: registerServiceWorker
  };
})(window);

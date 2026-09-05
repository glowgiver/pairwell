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

  /* The sticky bar only grows its dividing rule once it is actually holding
     position. A 1px sentinel in normal flow above it, cancelled by a -1px
     margin so it shifts nothing, tells us when that happens. */
  function mountStickyBar() {
    var bar = document.querySelector(".pw-bar");
    if (!bar || bar.dataset.stickyMounted) return;
    bar.dataset.stickyMounted = "1";

    var probe = document.createElement("div");
    probe.setAttribute("aria-hidden", "true");
    probe.style.cssText = "height:1px;margin-bottom:-1px;pointer-events:none";
    bar.parentNode.insertBefore(probe, bar);

    try {
      new IntersectionObserver(function (entries) {
        bar.classList.toggle("stuck", !entries[0].isIntersecting);
      }).observe(probe);
    } catch (e) {
      /* No IntersectionObserver — the bar still sticks, just without the rule. */
    }
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

  /* Five modules, each keeping its own accent so you know where you are.
     Icons match the ones the hub already used. */
  var TABS = [
    /* Home earns a tab because the top-bar link scrolls away with the page,
       and on an installed home-screen app there is no browser chrome to fall
       back on. Neutral accent — the hub is not a module. */
    { id: "hub", label: "Home", href: "", accent: "var(--text)",
      path: '<path d="M4 10.6 12 4l8 6.6"/><path d="M6.5 9.4V20h11V9.4"/>' },
    { id: "skincare", label: "Skincare", href: "skincare/", accent: "var(--skin)",
      path: '<path d="M12 3c-3.5 3.2-5.5 6-5.5 9a5.5 5.5 0 0 0 11 0c0-3-2-5.8-5.5-9Z"/><path d="M9.5 13.5a2.5 2.5 0 0 0 2.5 2.5"/>' },
    { id: "hair", label: "Hair", href: "hair/", accent: "var(--hair)",
      path: '<path d="M5 20c0-8 3-14 7-14s7 6 7 14"/><path d="M8.5 20c0-6 1.5-10 3.5-10s3.5 4 3.5 10"/>' },
    { id: "workout", label: "Workout", href: "workout/", accent: "var(--train)",
      path: '<path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10"/>' },
    { id: "kitchen", label: "Kitchen", href: "kitchen/", accent: "var(--food)",
      path: '<path d="M5 4v7a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V4"/><path d="M7 13v7"/><path d="M17 20V4c-1.7.8-2.5 2.7-2.5 5s.8 3.8 2.5 4"/>' },
    { id: "style", label: "Style", href: "style/", accent: "var(--style)",
      path: '<path d="M8 4h8l2 3-4 2 1 11H7l1-11-4-2Z"/><path d="M9 4a3 3 0 0 0 6 0"/>' }
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
      /* From the hub itself, base and href are both empty — "./" keeps that
         an explicit link to this page rather than an empty href. */
      var url = base + t.href || "./";
      return '<a href="' + url + '" style="--tab:' + t.accent + '"' +
        (here ? ' aria-current="page"' : '') + '>' +
        '<svg viewBox="0 0 24 24" aria-hidden="true">' + t.path + '</svg>' +
        '<span>' + t.label + '</span></a>';
    }).join("");
    document.body.appendChild(nav);
  }


  /* ---- theme ---------------------------------------------------------
     Three states: "auto" follows the phone, "light" and "dark" pin it.
     Stored per device, like the person. */

  var THEME_KEY = "hub.theme";
  var THEMES = ["auto", "light", "dark"];

  var ICONS = {
    auto:  '<path d="M12 3v18"/><path d="M12 8a4 4 0 0 1 0 8"/><circle cx="12" cy="12" r="9"/>',
    light: '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"/>',
    dark:  '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.8 6.8 0 0 0 10.5 10.5Z"/>'
  };

  function getTheme() {
    try {
      var v = localStorage.getItem(THEME_KEY);
      if (THEMES.indexOf(v) !== -1) return v;
    } catch (e) {}
    return "auto";
  }

  /* What the theme actually resolves to right now — "auto" defers to the OS. */
  function resolvedTheme() {
    var t = getTheme();
    if (t !== "auto") return t;
    try {
      return global.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    } catch (e) { return "dark"; }
  }

  function applyTheme() {
    var t = getTheme();
    var root = document.documentElement;
    if (t === "auto") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", t);

    /* Keep the iOS status bar in step, or it stays dark over a light page. */
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", resolvedTheme() === "light" ? "#F2F5FB" : "#0B1220");
  }

  function setTheme(t) {
    if (THEMES.indexOf(t) === -1) return;
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
    applyTheme();
    global.dispatchEvent(new CustomEvent("pw:theme", { detail: { theme: t } }));
  }

  /* `where` is "before" (the old top-bar behaviour) or "in" (append, used by
     the hub footer). The toggle is a setting used about twice a year, so it
     no longer sits in the top bar of all five pages competing with the person
     switcher for the best real estate on the screen. */
  function mountThemeToggle(el, where) {
    if (!el) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "pw-theme" + (where === "in" ? " pw-theme-foot" : "");
    if (where === "in") el.appendChild(b);
    else el.parentNode.insertBefore(b, el);

    function paint() {
      var t = getTheme();
      b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + ICONS[t] + '</svg>' +
                    '<span class="lbl">Theme: ' + t + '</span>';
      b.setAttribute("aria-label", "Theme: " + t + ". Tap to change.");
      b.title = "Theme: " + t;
    }
    b.addEventListener("click", function () {
      setTheme(THEMES[(THEMES.indexOf(getTheme()) + 1) % THEMES.length]);
      paint();
    });
    paint();
  }

  /* Repaint when the OS flips and we are on auto. */
  try {
    global.matchMedia("(prefers-color-scheme: light)").addEventListener("change", function () {
      if (getTheme() === "auto") applyTheme();
    });
  } catch (e) {}

  applyTheme();

  function registerServiceWorker(path) {
    if (!("serviceWorker" in navigator)) return;
    global.addEventListener("load", function () {
      navigator.serviceWorker.register(path || "sw.js");
    });
  }

  /* Paint once as soon as the script runs, so the first render is correct. */
  if (document.documentElement) paintRail(get());

  /* Every page has a .pw-bar, so wire it here rather than in five places. */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountStickyBar);
  } else {
    mountStickyBar();
  }

  global.PW = {
    PEOPLE: PEOPLE,
    ORDER: ORDER,
    get: get,
    set: set,
    person: person,
    mountSwitcher: mountSwitcher,
    mountRail: mountRail,
    mountTabs: mountTabs,
    mountStickyBar: mountStickyBar,
    mountThemeToggle: mountThemeToggle,
    getTheme: getTheme,
    setTheme: setTheme,
    resolvedTheme: resolvedTheme,
    TABS: TABS,
    registerServiceWorker: registerServiceWorker
  };
})(window);

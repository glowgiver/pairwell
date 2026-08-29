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

  function paintRail(id) {
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

  function registerServiceWorker(path) {
    if (!("serviceWorker" in navigator)) return;
    global.addEventListener("load", function () {
      navigator.serviceWorker.register(path || "sw.js");
    });
  }

  global.PW = {
    PEOPLE: PEOPLE,
    ORDER: ORDER,
    get: get,
    set: set,
    person: person,
    mountSwitcher: mountSwitcher,
    mountRail: mountRail,
    registerServiceWorker: registerServiceWorker
  };
})(window);

# Pairwell — Engine Ordner

Private PWA für Philipp & Eunice. Vier Tools: Skincare, Haare, Workout, Küche.
Gehostet später auf GitHub Pages (Repo-Name/URL noch nicht final entschieden).

## Architektur — bitte lesen, bevor du was änderst

**Zwei-Schichten-Prinzip, bewusst so entschieden (nicht zur Diskussion, außer der User bringt es explizit auf):**

1. **`data/*.json`** — die Wahrheit. Rohdaten: Tagesprofile, Rezepte, Trainingspläne,
   Skincare/Haar-Routinen. Kein HTML, kein Styling, keine UI-Logik.

2. **`hub/*/index.html`** — die Anzeige. Fertige, eigenständige HTML-Dateien.
   Kein Runtime-Fetch von JSON, kein Framework. Jede Seite ist eine einzelne Datei,
   die offline funktioniert, sobald der Service Worker sie gecacht hat.

**Warum kein Runtime-Fetch:** Offline-Zuverlässigkeit im Gym/Alltag ist wichtiger
als "eine Quelle live nachladen". Fertige HTML-Dateien sind robuster, weil sie nicht
von Netzwerk- oder Cache-Zuständen abhängen. Das wurde mit dem User im Chat explizit
so festgelegt (Option B von zwei durchgesprochenen Architekturen).

**Der Verbindungsweg zwischen den beiden Schichten sind die `scripts/build_*.py`
Skripte.** Sie lesen `data/*.json` und schreiben die passende `hub/*/index.html`.
Das ist ein manueller Build-Schritt, kein Watch-Prozess — nach jeder Datenänderung
das passende Skript neu laufen lassen.

```
data/*.json  --[scripts/build_*.py]-->  hub/*/index.html
```

## Ordnerstruktur

```
pairwell-engine/
├── data/
│   ├── profiles.json      Tagesprofile beider Personen (kcal/Protein/Fett/Ballaststoffe)
│   ├── kitchen.json        Mirror-Meal-System, Asian Base Blocks, Ninja-Standards
│   ├── training.json       Vollständige Trainingsdatenbank (98 Übungen, alle Locations)
│   └── routines.json       Skincare + Haare — siehe Lücken unten
│
├── scripts/
│   ├── build_training_data.py   Baut training.json neu (aktuell aus HTML-Quelle
│   │                             hartcodiert — siehe TODO unten)
│   └── build_workout_page.py    Liest training.json → schreibt hub/workout/index.html
│
└── hub/
    ├── index.html          Dashboard, 4 Kacheln, Personenwahl (P/E), localStorage
    ├── manifest.json        PWA-Manifest
    ├── sw.js                 Service Worker, Cache-Version aktuell "hub-v1"
    ├── icons/                App-Icons (192, 512, maskable-512)
    ├── workout/index.html    FERTIG — generiert aus training.json
    ├── skincare/index.html   PLATZHALTER — noch nicht gebaut
    ├── hair/index.html       PLATZHALTER — noch nicht gebaut
    └── kitchen/index.html    PLATZHALTER — noch nicht gebaut
```

## Personalisierung — wichtiges Detail

Das Dashboard (`hub/index.html`) fragt beim allerersten Öffnen "Wer bist du?"
und speichert die Antwort in `localStorage["hub.person"]` als `"P"` oder `"E"`.

Jede Unterseite sollte das beim Laden auslesen und sich automatisch auf die
richtige Person einstellen — `hub/workout/index.html` macht das bereits
(siehe `loadPerson()` im Script). Neue Seiten (Skincare, Haare, Küche) sollten
dasselbe Muster übernehmen, damit man beim Reinklicken nicht erneut wählen muss.

Küche ist bewusst NICHT personenabhängig (Mirror-System — beide identisch).

## Bekannte Lücken (siehe `_gaps`-Felder in den JSONs)

- **Eunices Skincare-Routine fehlt komplett** — bewusst zurückgestellt, kommt später
- **Eunices exakte Maintenance-Trainingslasten** teils nicht MacroFactor-verifiziert,
  nur aus der ursprünglichen Workout-Hub-HTML übernommen
- `build_training_data.py` baut die Daten aktuell aus fest eincodierten Python-Literalen
  (Abschrift der ursprünglichen Workout-Hub-HTML). Das ist okay für jetzt, aber kein
  eleganter Dauerzustand — bei größeren Trainingsänderungen eher direkt in
  `data/training.json` editieren und `build_workout_page.py` neu laufen lassen,
  statt das Build-Skript anzufassen.

## Style-Konventionen für neue Seiten

Dark Theme, gleiche CSS-Variablen wie im Dashboard:

```css
--bg:#0B1220; --surface:#131C2E; --surface-2:#1A2540; --line:#25324F;
--text:#EEF2F9; --muted:#8B9AB8;
--skin:#7FD1C1;   /* Skincare-Akzent */
--hair:#C9A6F2;   /* Haare-Akzent */
--train:#5A8DEE;  /* Workout-Akzent */
--food:#F2A65A;   /* Küche-Akzent */
```

Jede Unterseite: Link "← Hub" oben links zurück zu `../`, kein zusätzliches
Framework, kein `localStorage`-Zugriff außerhalb von `hub.person` (siehe
Persistent-Storage-Regeln, falls später Logging/Historie gebraucht wird — das
läuft über eine andere API, nicht `localStorage`, wegen iOS-Limits).

## Nächste sinnvolle Schritte

1. Skincare-Seite bauen (Philipp-Daten in `routines.json` sind vollständig,
   Eunice fehlt noch — Seite kann trotzdem schon für Philipp gebaut werden)
2. Haare-Seite bauen (komplett dokumentiert, ein gemeinsames Protokoll)
3. Küche-Seite bauen (aus `kitchen.json` — Rezeptlogik, Block-Rechner)
4. Sobald alles steht: Repo-Name final festlegen, GitHub Pages aktivieren,
   `sw.js`-Cache-Version auf `hub-v2` hochzählen beim ersten echten Deploy

## Deploy-Hinweis (für später)

`sw.js` cached alle Seiten beim ersten Laden. Bei jeder inhaltlichen Änderung
an einer `hub/*/index.html` muss `const CACHE = "hub-vX"` in `sw.js` hochgezählt
werden — sonst sehen die Handys weiter die alte, gecachte Version.

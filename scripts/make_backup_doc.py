"""Generate a standalone, printable backup of Eunice's seasonal skincare protocol.

The app is the living version. This exists so the protocol survives independently
of it — one self-contained HTML file, no CSS or JS dependencies, prints cleanly.

    python3 scripts/make_backup_doc.py

Regenerate after editing data/routines.json. Do not hand-edit the output.
"""

import html as H
import json
import os

BASE = os.path.dirname(__file__)
DATA = os.path.join(BASE, "..", "data", "routines.json")
OUT_DIR = os.path.join(BASE, "..", "backups")
OUT = os.path.join(OUT_DIR, "eunice-skincare-protocol.html")

GENERATED_ON = "29 August 2026"


def esc(s):
    return H.escape(str(s))


def steps_ol(items):
    return "".join(
        '<li><span class="n">%d</span><div class="t">%s</div></li>' % (i + 1, esc(x))
        for i, x in enumerate(items)
    )


def build(e):
    rules = "".join(
        '<div class="rule%s"><div class="rt">%s%s</div><p>%s</p></div>' % (
            " critical" if r.get("critical") else "",
            "&#9888; " if r.get("critical") else "",
            esc(r["title"]), esc(r["rule"]))
        for r in e["safetyRules"])

    seasons = ""
    for key, s in e["seasons"].items():
        extra = ('<div class="extra">%s</div>' % esc(s["am"]["weeklyExtra"])
                 if s["am"].get("weeklyExtra") else "")
        nights = "".join(
            '<div class="night"><div class="nh"><b>%s</b><span>%s</span></div>'
            '<ol class="steps">%s</ol></div>' % (
                esc(ev["day"]), esc(ev["focus"]), steps_ol(ev["steps"]))
            for ev in s["pmWeekly"])
        seasons += (
            '<section class="season" id="%s"><div class="shead"><h2>%s</h2>'
            '<span class="months">%s</span></div><p class="goal">%s</p>'
            '<div class="card"><div class="ch">Morning &middot; %s min</div>'
            '<ol class="steps">%s</ol>%s</div>'
            '<div class="nights">%s</div></section>' % (
                esc(key), esc(key.title()), esc(s["months"]), esc(s["goal"]),
                esc(s["am"]["durationMin"]), steps_ol(s["am"]["steps"]), extra, nights))

    def dl(d):
        return "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v))
                       for k, v in d.items())

    return TEMPLATE % {
        "skinType": esc(e["skinType"]),
        "source": esc(e["_source"]),
        "generated": GENERATED_ON,
        "rules": rules,
        "seasons": seasons,
        "devices": dl(e["devices"]),
        "products": dl(e["coreProducts"]),
        "concerns": esc(" · ".join(e["concerns"])),
    }


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eunice · Seasonal Skincare Protocol</title>
<style>
:root{--bg:#0B1220;--surface:#131C2E;--surface-2:#1A2540;--line:#25324F;
--text:#EEF2F9;--muted:#8B9AB8;--muted2:#5f7492;--accent:#7FD1C1;--crit:#F4666F}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--text);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased;line-height:1.5;
max-width:760px;margin:0 auto;padding:40px 20px 80px}
h1{font-size:31px;font-weight:700;letter-spacing:-.02em;margin:0 0 6px;color:var(--accent)}
.lede{color:var(--muted);font-size:15px;margin:0 0 6px}
.meta{color:var(--muted2);font-size:13px;margin:0 0 30px}
h2{font-size:23px;font-weight:700;letter-spacing:-.02em;margin:0}
.shead{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;
padding-top:34px;margin-bottom:4px;border-top:1px solid var(--line)}
.months{font-size:13px;color:var(--muted2)}
.goal{color:var(--muted);font-size:14.5px;margin:0 0 16px;max-width:62ch}
.card,.night{background:var(--surface);border:1px solid var(--line);
border-radius:16px;margin-bottom:12px;overflow:hidden}
.ch,.nh{padding:13px 18px;border-bottom:1px solid var(--line);
font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}
.nh{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.nh b{color:var(--accent)}
.nh span{font-size:14.5px;font-weight:600;letter-spacing:0;text-transform:none;color:var(--text)}
ol.steps{list-style:none;margin:0;padding:6px 0}
ol.steps li{display:grid;grid-template-columns:24px 1fr;gap:12px;padding:10px 18px;align-items:baseline}
ol.steps li+li{border-top:1px solid var(--line)}
.n{font-size:13px;font-weight:700;color:var(--muted2);font-variant-numeric:tabular-nums}
.t{font-size:15.5px;line-height:1.45}
.extra{padding:12px 18px;border-top:1px solid var(--line);
font-size:14px;color:var(--muted);background:var(--surface-2)}
.rule{border:1px solid var(--line);border-left:3px solid var(--muted2);
background:var(--surface-2);border-radius:0 12px 12px 0;padding:14px 17px;margin-bottom:12px}
.rule.critical{border-left-color:var(--crit);background:rgba(244,102,111,.10)}
.rt{font-size:13px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;
color:var(--muted2);margin-bottom:6px}
.rule.critical .rt{color:var(--crit)}
.rule p{margin:0;font-size:14.5px;color:var(--muted)}
.rule.critical p{color:var(--text)}
dl{display:grid;gap:1px;background:var(--line);border:1px solid var(--line);
border-radius:14px;overflow:hidden;margin:0 0 12px}
dl>div{background:var(--surface);padding:12px 17px}
dt{font-size:12.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted2);margin-bottom:3px}
dd{margin:0;font-size:14.5px;color:var(--text)}
footer{margin-top:44px;padding-top:20px;border-top:1px solid var(--line);
font-size:12.5px;color:var(--muted2);line-height:1.7}
@media print{
  body{background:#fff;color:#111;max-width:none}
  .card,.night,.rule,dl>div{background:#fff;border-color:#ccc}
  h1,.ch,.nh b,.rule.critical .rt{color:#000}
  .season,.night,.rule{break-inside:avoid}
}
</style>
</head>
<body>
<h1>Seasonal Skincare Protocol</h1>
<p class="lede">Eunice &middot; %(skinType)s</p>
<p class="meta">Backup copy generated from data/routines.json on %(generated)s.
Source: %(source)s. The living version is in the Pairwell app.</p>

<h2 style="font-size:19px;margin-bottom:12px">The golden rules</h2>
%(rules)s

%(seasons)s

<div class="shead"><h2>Devices</h2></div>
<dl>%(devices)s</dl>
<div class="shead"><h2>Products</h2></div>
<dl>%(products)s</dl>

<footer>
Generated backup &mdash; not the source of truth. Edit <code>data/routines.json</code>
and re-run <code>scripts/make_backup_doc.py</code>.<br>
Concerns: %(concerns)s.<br>
Not medical advice. The device boundaries above are the protocol's own limits.
</footer>
</body>
</html>
"""


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    e = data["skincare"]["eunice"]
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = build(e)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    nights = sum(len(s["pmWeekly"]) for s in e["seasons"].values())
    print("written %s  (%d bytes)" % (os.path.relpath(OUT, os.path.join(BASE, "..")), len(doc)))
    print("  %d seasons · %d evenings · %d rules"
          % (len(e["seasons"]), nights, len(e["safetyRules"])))


if __name__ == "__main__":
    main()

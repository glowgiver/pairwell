"""Take the newest image out of ~/Downloads and install it as a look picture.

This is Pairwell's answer to the "Übernehmen" button in Teaching Hub's image
dialog, and it is a script rather than a button for a reason worth stating.
Teaching Hub can offer a button because `engine/hub.py` is an HTTP server
running on this machine, so a click can reach `/api/image/adopt` and move a
file. Pairwell is a static page served from GitHub Pages with no backend at
all; the page in the browser cannot write into the repository, and adding a
server to make it possible would undo the thing the app is built around.

What is portable is the useful half — adopt_download's actual job: find the
file that was just saved, put it where it belongs under the name the build
expects, and re-render. That needs no server.

    python3 scripts/adopt_look_image.py                 # what is still missing
    python3 scripts/adopt_look_image.py school-day      # newest download -> school-day.png
    python3 scripts/adopt_look_image.py weekend --replace
    python3 scripts/adopt_look_image.py weekend --file ~/Desktop/x.png

It refuses to overwrite without --replace, the same bargain Teaching Hub
makes, because the expensive mistake here is silently replacing an
illustration you meant to keep.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_slug import slug

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
DATA = os.path.join(ROOT, "data", "style.json")
IMG_DIR = os.path.join(ROOT, "hub", "style", "img")
SW = os.path.join(ROOT, "hub", "sw.js")
DOWNLOADS = os.path.expanduser("~/Downloads")
EXT = (".png", ".jpg", ".jpeg", ".webp")


def targets():
    """[(slug, label, existing filename or None)] for every image the Style
    page can show — the five looks, plus hair, plus whatever else in the file
    grows an `imageStyle`. Adding a sixth look or a second illustrated field
    needs no change here: anything with `imageStyle` is picked up on its own,
    the same way build_style_page.py finds files by scanning the folder
    rather than by a hardcoded list.
    """
    data = json.load(open(DATA, encoding="utf-8"))
    out = []
    have = {}
    if os.path.isdir(IMG_DIR):
        for n in os.listdir(IMG_DIR):
            if os.path.splitext(n)[1].lower() in EXT:
                have[slug(os.path.splitext(n)[0])] = n
    for person in data:
        p = data[person]
        if not isinstance(p, dict):
            continue
        for o in (p.get("looks") or {}).get("items", []):
            s = slug(o["occasion"])
            out.append((s, o["occasion"], have.get(s)))
        if isinstance(p.get("hair"), dict) and p["hair"].get("imageStyle"):
            out.append(("hair", "Hair", have.get("hair")))
    return out


def newest_download():
    if not os.path.isdir(DOWNLOADS):
        return None
    files = [
        os.path.join(DOWNLOADS, n)
        for n in os.listdir(DOWNLOADS)
        if os.path.splitext(n)[1].lower() in EXT
    ]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def status():
    rows = targets()
    print("Item                 File                        State")
    print("-" * 66)
    for s, occ, have in rows:
        print("%-20s %-27s %s" % (occ[:20], (have or s + ".png"),
                                  "ok" if have else "missing"))
    missing = [s for s, _, have in rows if not have]
    print()
    print("%d of %d still missing." % (len(missing), len(rows)))
    if missing:
        print("Prompts are on the Style page under \"Image prompt\".")
        print("Then: python3 scripts/adopt_look_image.py %s" % missing[0])


def rebuild():
    for script in ("build_style_page.py", "build_sw.py"):
        r = subprocess.run([sys.executable, os.path.join(BASE, script)],
                           capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            return False
    return True


def bump_cache():
    """Step hub-vN. Forgetting this is the documented failure mode — the file
    is deployed and the phones keep serving the old one — and the script knows
    for certain that an asset just changed, which is more than a person does.
    """
    s = open(SW, encoding="utf-8").read()
    import re
    m = re.search(r'const CACHE = "hub-v(\d+)"', s)
    if not m:
        return None
    n = int(m.group(1)) + 1
    s = s[:m.start()] + 'const CACHE = "hub-v%d"' % n + s[m.end():]
    open(SW, "w", encoding="utf-8").write(s)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("look", nargs="?", help="look slug, e.g. school-day")
    ap.add_argument("--file", help="use this file instead of the newest download")
    ap.add_argument("--replace", action="store_true",
                    help="overwrite an illustration that is already there")
    a = ap.parse_args()

    if not a.look:
        status()
        return 0

    rows = targets()
    match = [r for r in rows if r[0] == a.look]
    if not match:
        print("No look or image called %r." % a.look)
        print("Known: %s" % ", ".join(r[0] for r in rows))
        return 1
    s, occasion, have = match[0]

    if have and not a.replace:
        print("%s already exists (%s). Pass --replace to overwrite it." % (occasion, have))
        return 1

    src = os.path.expanduser(a.file) if a.file else newest_download()
    if not src or not os.path.isfile(src):
        print("Nothing to adopt — no image found in ~/Downloads." if not a.file
              else "No such file: %s" % src)
        return 1

    age = time.time() - os.path.getmtime(src)
    if not a.file and age > 3600:
        # Not fatal: a deliberate "the one I made an hour ago" is legitimate.
        # Saying which file and how old it is beats silently taking the wrong one.
        print("Note: newest download is %d minutes old." % (age / 60))

    os.makedirs(IMG_DIR, exist_ok=True)
    if have:
        os.remove(os.path.join(IMG_DIR, have))
    dst = os.path.join(IMG_DIR, s + os.path.splitext(src)[1].lower())
    shutil.copy2(src, dst)
    print("%s  <-  %s (%.0f KB)" % (os.path.basename(dst), os.path.basename(src),
                                    os.path.getsize(dst) / 1024))

    if not rebuild():
        return 1
    n = bump_cache()
    if n:
        print("sw.js cache bumped to hub-v%d" % n)

    left = [r[1] for r in targets() if not r[2]]
    print()
    # " · " rather than ", ": one of the occasions is "Colour, carefully",
    # and a comma-separated list containing a comma reads as six items.
    print("Still drawn: %s" % (" · ".join(left) if left else "none — everything is illustrated"))
    print("Deploy: git add -A && git commit && git push && "
          "git subtree push --prefix hub origin gh-pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())

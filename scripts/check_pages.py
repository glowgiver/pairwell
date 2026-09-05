"""Syntax-check the JavaScript the build scripts emit into hub/**/index.html.

Why this exists: the pages are Python strings that contain JavaScript, and
Python's own escaping runs first. A `\\"` written inside a triple-quoted
template collapses to a bare `"` before the browser ever sees it, which turns

    ? " <span class=\\"sep\\">-</span> plus "

into a double-quoted string full of unescaped double quotes. The build script
succeeds, the file is written, the page loads — and then dies on the first
statement with a SyntaxError, showing a blank stage. Nothing in the build
catches it, and reading the DOM does not either, because the DOM is empty.

That bug shipped once. This script is the guard: it pulls each inline <script>
out of the built pages and runs `node --check` over it.

Requires node on PATH. Without node it says so and exits 0, rather than
pretending the pages were verified.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(__file__)
HUB = os.path.join(BASE, "..", "hub")

PAGES = [
    "index.html",
    os.path.join("skincare", "index.html"),
    os.path.join("hair", "index.html"),
    os.path.join("workout", "index.html"),
    os.path.join("kitchen", "index.html"),
    os.path.join("style", "index.html"),
]

# app.js is hand-written rather than emitted, but it is the file every page
# depends on, so a syntax error there takes all five down at once.
STANDALONE = ["app.js", "sw.js"]


def scripts_in(html):
    """Inline <script> bodies, skipping the ones that only carry a src."""
    return [
        m.group(1)
        for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
        if m.group(1).strip()
    ]


def check(node, label, source):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(source)
        path = fh.name
    try:
        r = subprocess.run([node, "--check", path], capture_output=True, text=True)
    finally:
        os.unlink(path)
    if r.returncode == 0:
        return True
    # node reports the temp path and its own line numbers; both are noise here.
    msg = r.stderr.replace(path, label).strip().splitlines()
    print("  FAIL  %s" % label)
    for line in msg[:6]:
        print("        %s" % line)
    return False


def main():
    node = shutil.which("node")
    if not node:
        print("node not on PATH — pages NOT syntax-checked.")
        return 0

    ok = True
    checked = 0

    for rel in PAGES:
        path = os.path.join(HUB, rel)
        if not os.path.exists(path):
            print("  SKIP  %s (not built)" % rel)
            continue
        html = open(path, encoding="utf-8").read()
        blocks = scripts_in(html)
        if not blocks:
            print("  WARN  %s has no inline script" % rel)
            continue
        for i, src in enumerate(blocks):
            label = "%s [script %d]" % (rel, i + 1)
            checked += 1
            if check(node, label, src):
                print("  ok    %s" % label)
            else:
                ok = False

    for rel in STANDALONE:
        path = os.path.join(HUB, rel)
        if not os.path.exists(path):
            continue
        checked += 1
        if check(node, rel, open(path, encoding="utf-8").read()):
            print("  ok    %s" % rel)
        else:
            ok = False

    print()
    print("%d script(s) checked — %s" % (checked, "all parse" if ok else "SYNTAX ERRORS"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

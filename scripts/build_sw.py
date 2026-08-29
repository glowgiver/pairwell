"""Stamp hub/sw.js with the same asset hashes the pages use.

The pages request app.css?v=<hash>. If the shell listed the bare path the
cache key would never match and those two files would fall through to the
network on every load — which is precisely what offline cannot do.

Run after the page builders, before deploying.
"""

import hashlib
import os
import re

BASE = os.path.dirname(__file__)
HUB = os.path.join(BASE, "..", "hub")
SRC = os.path.join(BASE, "sw.template.js")
OUT = os.path.join(HUB, "sw.js")


def digest(rel):
    return hashlib.sha1(open(os.path.join(HUB, rel), "rb").read()).hexdigest()[:8]


def main():
    src = SRC if os.path.exists(SRC) else OUT
    s = open(src, encoding="utf-8").read()
    css, js = digest("app.css"), digest("app.js")
    s = re.sub(r'app\.css\?v=[^"]*', "app.css?v=" + css, s)
    s = re.sub(r'app\.js\?v=[^"]*', "app.js?v=" + js, s)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(s)
    print("sw.js stamped  css=%s js=%s" % (css, js))


if __name__ == "__main__":
    main()

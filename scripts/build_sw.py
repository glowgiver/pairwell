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


IMG_DIR = os.path.join(HUB, "style", "img")
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def style_images():
    """The Style illustrations, as the page requests them.

    build_style_page.py appends the same content hash to each src, so the
    cache key here has to carry it too — the identical trap app.css?v= was
    already documented for, one directory down.
    """
    if not os.path.isdir(IMG_DIR):
        return []
    out = []
    for name in sorted(os.listdir(IMG_DIR)):
        if os.path.splitext(name)[1].lower() not in IMG_EXT:
            continue
        h = hashlib.sha1(open(os.path.join(IMG_DIR, name), "rb").read()).hexdigest()[:8]
        out.append('  "./style/img/%s?v=%s",' % (name, h))
    return out


def main():
    src = SRC if os.path.exists(SRC) else OUT
    s = open(src, encoding="utf-8").read()
    css, js = digest("app.css"), digest("app.js")
    s = re.sub(r'app\.css\?v=[^"]*', "app.css?v=" + css, s)
    s = re.sub(r'app\.js\?v=[^"]*', "app.js?v=" + js, s)

    imgs = style_images()
    block = "\n".join(["  // <style-img>"] + imgs + ["  // </style-img>"])
    s, n = re.subn(r"  // <style-img>.*?  // </style-img>", block, s, flags=re.S)
    if not n:
        raise SystemExit("sw.js has no <style-img> markers — cannot stamp images")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(s)
    print("sw.js stamped  css=%s js=%s  style images=%d" % (css, js, len(imgs)))


if __name__ == "__main__":
    main()

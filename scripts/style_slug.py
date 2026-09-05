"""The one definition of a look's filename slug.

Three things have to agree on what "Colour, carefully" is called on disk: the
page builder that looks for the file, the page's own JavaScript that looks the
result up by key, and the adopt script that writes the file in the first
place. Two of those are Python and import this; the third is JavaScript and
cannot, so `slug()` in build_style_page.py's inline script is a deliberate
mirror of this function and the two must be changed together.

ASCII-only on purpose. The JavaScript side is `replace(/[^a-z0-9]+/g, "-")`,
which turns "ü" into a hyphen. Python's str.isalnum() says "ü" is alphanumeric
and would keep it, so a German occasion name would produce "gruen" on one side
and "gr-n" on the other — a file written by the adopt script that the page
then fails to find, with nothing to show for it but a missing picture.
"""

ASCII = "abcdefghijklmnopqrstuvwxyz0123456789"


def slug(s):
    out = "".join(c if c in ASCII else "-" for c in str(s).lower())
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")

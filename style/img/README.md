# Style illustrations

Drop the generated look illustrations here. The build finds them by filename
and swaps them in for the drawn placeholder — there is no list to update.

    school-day.png
    parent-evening.png
    weekend.png
    evening-out.png
    colour-carefully.png

`.png`, `.jpg`, `.jpeg` and `.webp` all work. The name is the look's
`occasion` from `data/style.json`, lowercased with spaces and punctuation
turned into hyphens; if a file does not appear on the page, that mapping is
the thing to check.

The prompt for each one is on the Style page itself, under *Image prompt —
not generated yet*, with a Copy button. It is assembled at render time from
`looks.imageStyle` plus that look's own `imagePrompt`, so the shared parts —
the graphic-novel ink style, and the description of the same man in all five
so they read as one series — stay in one place and cannot drift apart.

You do not have to copy files here by hand. `scripts/adopt_look_image.py` is
this project's version of Teaching Hub's "Übernehmen" — it takes the newest
image out of `~/Downloads`, installs it under the right name, re-runs both
builds and steps the cache version:

    python3 scripts/adopt_look_image.py                # what is still missing
    python3 scripts/adopt_look_image.py school-day     # newest download -> here
    python3 scripts/adopt_look_image.py weekend --replace

It is a command rather than a button in the app because Pairwell has no
backend — a static page on GitHub Pages cannot write into the repository, and
giving it a server to make that possible would cost the thing the app is
built around.

By hand it is:

    python3 scripts/build_style_page.py   # swaps the image in
    python3 scripts/build_sw.py           # adds it to the offline shell

then bump `CACHE` in `hub/sw.js`. The second step is not optional: without it
the picture only exists once the phone has been online, and a shop is exactly
where it will not be. The adopt script does all three, which is the main
reason to use it.

This folder is committed and published. Keep it to illustrations — no
photographs of a person, per the privacy rule in `CLAUDE.md`.

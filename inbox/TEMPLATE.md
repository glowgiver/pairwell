# Dish name here

source: https://where-you-found-it
servings: 2
slot: mirror          # mirror | breakfast | snack
person: both          # both | philipp | eunice
blocks: 1             # Asian Base blocks per serving, 0 if the dish carries its own carb
cuisine: asian        # optional: asian | european | mediterranean | indian | mexican
                      # only used to decide what may be ADDED if the dish comes
                      # up short — no cuisine means nothing gets filtered out,
                      # so chickpeas may get proposed for a Thai curry

## Ingredients
300 g Hähnchenbrust
120 g Rote Linsen, gekocht
200 g Pak Choi
100 g Shiitake
1 EL Sojasauce
10 g Ingwer
1 TL Sesamöl

## Steps
- Ingwer und Knoblauch anbraten
- Hähnchen scharf anbraten
- Pressure Cook High, 6 Minuten
- Pak Choi unterheben

# ---------------------------------------------------------------------------
# Copy this file, fill it in, drop it in inbox/. One dish per file.
#
# Amounts AS FOUND — do not pre-adjust them to the target. Fitting them is the
# script's job, and it can only see what you changed if you leave the original.
#
# Anything is fine: German or English, grams or EL/TL. Unknown ingredients get
# reported rather than guessed. If an amount is vague ("a handful"), write your
# best gram estimate — a wrong number you can see beats a missing one.
#
# WHAT TO DROP IN HERE, best first:
#   1. This template, filled in. Readable by the script, no transcription needed.
#   2. A raw paste — the ingredient list copied straight off the page, plus the
#      link. Messy is fine; ask Claude to tidy it into the format above.
#   3. A photo or screenshot. Cookbook page, a reel, a handwritten card. Claude
#      reads images; the script will list the file as waiting.
#
# NOT worth your time: printing a web page to PDF. It is mostly cookie banner
# and advertising, and the amounts end up harder to find, not easier.
#
# If a dish misses the target, adapt_recipe.py does not just shrug: it proposes
# what to ADD, in grams, then re-fits the whole dish around the addition — so
# the chicken comes back down when the lentils go in. Proposals only; it never
# edits a recipe by itself.
#
# Then: python3 scripts/read_inbox.py
# ---------------------------------------------------------------------------

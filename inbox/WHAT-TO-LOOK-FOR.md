# What to look for when hunting recipes

Everything here is derived from `data/profiles.json` and `data/kitchen.json`.
If those change, re-run `python3 scripts/check_targets.py` and fix this file.

## The envelope

One serving of the **dish alone**, because one Asian Base block (119 kcal) is
already going on the plate beside it:

    351 kcal  ·  35.7 g protein  ·  12.4 g fibre  ·  7-11 g fat

That is the whole brief. Everything below is just what it implies.

## The shape that fits

No single fibre source works. Lentils are dense enough for a lunchbox but
12.4 g of fibre from lentils alone costs 180 kcal — half the budget. Greens are
cheap in calories but 12.4 g from spinach means 564 g of it, which does not go
in a box. So it is always a **split**:

    ~100-150 g lean protein
    ~100 g    cooked legume        (density)
    ~200 g    quick-cooking greens or mushrooms   (volume, and cheap)
    an aromatic sauce with almost no fat

Legumes and greens carry ~15 g of protein between them, which is why the meat
portion is smaller than it looks.

## Protein sources, by how much room they leave

    Cod, prawns, turkey, chicken breast, pork fillet   ~180 kcal left  fine
    Lean beef 5%                                        ~123 kcal left  tight
    Chicken thigh                                        ~85 kcal left  tight
    Tofu as the only protein                             ~25 kcal left  no
    Salmon                                                    over      no

Salmon and tofu are not banned — they just cannot be the *only* protein, because
they leave nothing for the fibre.

## Green flags

- Braises and one-pot stews: Taiwanese, Vietnamese, Japanese nabe
- Stir-fries heavy on vegetables with a defined protein portion
- Steamed or poached fish with aromatics
- Soups and hot pots
- Sauce built on stock, soy, vinegar, mustard, tomato or quark
- Anything already written in grams

## Red flags, spottable in five seconds

- Coconut milk, cream, cheese sauce, peanut or satay sauce
- Deep-fried, battered, breaded
- Rice, noodles, potato or bread as part of the dish — we bring our own carb
- "Salad" recipes that reach their fibre through sheer volume
- Protein minced into a mixture, so a portion cannot be weighed
- More than ~10 ingredients, or three specialty imports

## What to capture

The **ingredient list in grams** and the method. Nothing else.

Skip the nutrition panel entirely. Every macro here is derived from the
ingredients, so a figure copied off a website is at best ignored and at worst
believed by mistake.

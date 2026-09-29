# Type roles

One semantic role, one token, everywhere. `tools/check-type-roles.mjs` enforces it.

## The roles

| Role | Token (`assets/colors_and_type.css`) | 1440 | 1024 | 768 | 390 / 320 |
|---|---|---|---|---|---|
| Page H1 (all pages except Home) | `--type-page-title` | 48 | 42.34 | 38.75 | 36 |
| Home hero H1 (the one exception) | `--type-display` from 761px, `--type-page-title` below | 66 | 58.6 | 52.4 | 36 |
| Top-level section heading (h2) | `--type-h2` | 33.16 | 27.34 | 24 | 24 |
| Subsection heading, card title, item title (h3) | `--type-h3` | 24 | 21.5 | 20 | 20 |
| Label / key / kicker / numeral | `--type-caption` | 13 | 12.1 | 12 | 12 |

Each step is a real step down: 48 > 33 > 24 > 13 at 1440. Body copy, ledes and
statements (`.h-body`, `.ap-lede`, `--type-statement`) are outside the roles and unchanged.

Not in a role, deliberately: nav and footer text, buttons and tab controls
(`.fx-stage`, `.aw-sw`, `.tw-sel`), and the on-map area names (`.ab-grp`, 12.5px, drawn
over an image). The checker still fails on any visible h1-h4 in `<main>` that no role
claims, so a new heading has to be given a role.

## Before (main at 1eb9d49, 1440px, English; Japanese in brackets)

| Role | Element | Was | Now |
|---|---|---|---|
| h1 | Home | 63.88 (60) | 66 (761px and up); 36 on phones |
| h1 | About, Approach, Investment Focus | 56.56 (45.36) | 48 |
| h1 | Company | 44 (38.16) | 48 |
| h2 | Home statement `.hi-statement` | 42.48 (40) | 33.16 |
| h2 | Approach `.ap-h2`, Focus `.fx-h2`, `.dl-h2` | 38 (32 / 31) | 33.16 |
| h2 | `.h-h2` (Home, About) | 33.16 | 33.16 |
| h3 | Focus `.hs-title` (retagged h2 to h3) | 28 (23) | 24 |
| h2 | Company `.co-label` | 26 (22) | 33.16 |
| h2 | Enquiry `.enq-h` | 22 | 33.16 |
| h3 | About phase names `.aw-stage` | 35.04 (32.16) | 24 |
| h3 | Focus open panel name | 32.84 (26.24) | 24 |
| h3 | Focus card names, Home card names `.hf-cap h3` | 28.96 | 24 |
| h3 | Home `.hm-city` | 28 (26) | 24 |
| h3 | About `London` / `Amsterdam` (were h2, level with "Focus Markets") | 33.16 | 24 |
| h3 | Focus `.dl-n` | 26 | 24 |
| h3 | Focus `.fx-band--rep .fx-name` | 26.52 | 24 |
| h3 | Approach stage names `.lf-pan-h span` | 22.2 | 24 |
| h3 | Focus `.fx-stagehead` | 23.64 (21 in Repositioning) | 24 |
| h3 | Approach five-test titles `.tw-item dt` | 20.8 | 24 |
| h3 | Home `.hp-item h3` | 21 | 24 |
| h3 | Company `.co-tier-n` | 20 | 24 |
| h3 | Focus `.hs-test-n` | 19 | 24 |
| label | Approach phase headings `.lf-gh` (Formation / Execution / Ownership) | 14, 66% cream | 13, full cream |
| label | `.hi-op-k`, `.hf-spec-k`, `.aw-specs-k`, `.fx-*-k`, `.hs-kicker`, `.dl-kicker` | 12.5 | 13 |
| label | `.lf-k`, `.lf-own-n`, `.lf-ap dt`, `.lf-pan-h` numerals | 12 | 13 |
| label | `.am-k`, `.aw-stage-s` | 13 | 13 |

## Decisions (reviewed)

- **Home hero H1 is the one exception.** It uses `--type-display` from 761px up (66px at 1440, 64px before
  the role work). Phones stay on `--type-page-title` (36px, the old 36-38px): the display token's 44px floor
  wraps the English headline to five lines at 320-360px and splits the Japanese one mid-phrase. The Japanese
  Home H1 also gets `keep-all` and a `<wbr>` so phones break as 日本の投資家の / ために.
- **Enquiry "Contact" (`.enq-h`) stays an h2 at `--type-h2` (33px).**
- **"Selective Hospitality" is an h3 at `--type-h3` (24px).** Its three test titles (`.hs-test-n`) are also h3
  at 24px, so parent and children now share a size. Not changed; flagged for follow-up.
- **Approach phase headings are labels** on `--type-caption` in full cream, above stage names on `--type-h3`.
- **About's `London` and `Amsterdam` are h3** (they were h2 siblings of "Focus Markets"), with a new `.h-h3`
  atom next to `.h-h2` in `editorial.css`.

## The "6.4px stage numerals"

They are not collapsing. The `01`-`05` numerals on Approach's "Five Tests" ring are SVG
`<text>` in a `viewBox="0 0 100 100"`, and `.tw-num { font-size: 6.4px }` is in **viewBox
units**. `getComputedStyle` reports 6.4px, but the ring is drawn at 240px (1440) or 200px
(1024 and below), a scale of 2.4 or 2.0, so they render at **15.4px** and **12.8px**
(measured through the SVG's screen transform; box heights 20px and 17px). At 12.8px they
match the 12px `.tw-n` badge in the list beside them. Nothing was changed; the number to
distrust is the computed style, not the page. The checker measures HTML text only, so it
does not repeat that mistake.

The Approach stage numerals that are genuinely small are the `1`-`6` beside each stage name
(`.lf-pan-h b`, 12px at 62% cream). They now sit on the label token (13px at 1440).

## Running the check

```
python3 -m http.server 8099                     # from the repo root
BASE=http://127.0.0.1:8099 node tools/check-type-roles.mjs
WIDTHS=1440,1024,768,390,320 ...                # more widths
```

Verified: 0 failures at 1440, 1024, 768, 390 and 320. Run against main it reports 260
failures (h1 38-64px, h2 22-42.5px, h3 14-35px), so it can fail.

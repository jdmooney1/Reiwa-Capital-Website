# Nav hairline fade: verification

**Element:** `.nav-rule` (built by `shell.js`, on all 16 pages), drawn by `.nav-rule::after`
(1px, `editorial.css`). It only meets a heading where the nav floats transparent over a hero:
Home, About, Approach and Investment Focus, in both languages (8 pages). Company, Privacy,
Disclaimer and 404 have a solid bar from the start, so the rule never crosses text there.

**Fix:** `craft.js` `updateRuleFade()` sets `--rule-o` on the bar from the scroll position:
1 at scroll 0, falling linearly to 0 at `min(distance from the rule to the H1 top - 8px, 96px)`.
The distance is measured live, not hard-coded. Measured scroll to the H1 across the 8 pages and
7 viewports (1440 to 320, plus 844x390 landscape) ranged from 24px to 648px, so the fade length
is 76-96px on phones, and shorter than that only where the heading is that close. Solid bars
and the open menu always show the rule. `prefers-reduced-motion: reduce` gives 0 or 1 only, with
no transition.

## Results

| Check | Result |
|---|---|
| Chromium, 8 hero pages x 6 widths (1440, 1024, 768, 430, 390, 320), 4px scroll steps, 4,607 samples | rule visible at **0 of 1,049** samples where it crosses the H1 (control on main: 631 of 631 visible at 4 widths) |
| Computed opacity, settled, at the first crossing | 0 on all 48 combinations |
| Opacity at rest (scroll 0) | 1 on all 48 |
| Non-monotonic on the way down | 0 |
| Firefox 157, 16 combos (390, 768), 749 samples | 0 of 164 crossing samples visible |
| WebKitGTK, 16 combos (390, 768), 757 samples | 0 of 156 crossing samples visible |
| Reduced motion (390) | `--rule-o` takes only 0 and 1, `transition-duration` 0.00001s |
| CLS, 10 indexed pages at 1440 and 390 | 0 on all |
| Contrast, 583 class representatives | 2 AA failures, both the JA switch over the pale sky on Home at 390, unchanged from main since the header wash was restored; none from this change |

## Scroll up

The rule returns linearly over the last 96px (About at 390: 0.17 at 80px, 0.38 at 60, 0.58 at 40,
0.79 at 20, 1 at 0). Coming back up from the page, the solid bar's rule fades out over 120ms
as the bar goes transparent, then fades back in over the last 96px: a dip, not a flicker. The
logo also steps back while the heading passes under it; that is existing behaviour (identical
on main), not part of this change.

## Before and after

Each strip: main at scroll 0, main at the scroll where the rule meets the first line of the H1,
fix at scroll 0, fix at the same scroll. `home-*`, `about-*`, `ja-about-*`, `focus-*`, at 390 and 768.

![About 390](about-390.jpg)
![Home 390](home-390.jpg)

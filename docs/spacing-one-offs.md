# Spacing one-offs

The site uses 404 fluid `clamp()` values for margins, padding and gaps,
written as 141 different expressions. Six tokens — `--fluid-2xs` … `--fluid-xl`,
defined in `editorial.css` — now carry 224 of those uses. Each replacement
computes within 4px of the expression it replaced at every width from 320 to
2560, verified by comparing every computed spacing value on all 16 pages
against the previous build.

The 180 uses below (66 distinct values) fit none of the six within that tolerance,
so they keep their own expression. They are listed here so the next pass can see
what is deliberate and what is only unexamined. Pages are named once; every one
has an identical Japanese counterpart.

| floor → ceiling | expression | uses | pages |
|---|---|---|---|
| 4 → 8 | `clamp(4px, .6vw, 8px)` / `clamp(4px, 0.6vw, 8px)` | 6 | focus, index |
| 6 → 12 | `clamp(6px, 0.8vw, 12px)` | 1 | index |
| 13 → 17 | `clamp(13px, 1.4vw, 17px)` | 2 | approach |
| 14 → 18 | `clamp(14px, 1.6vw, 18px)` / `clamp(14px,1.6vw,18px)` | 8 | about, disclaimer, privacy |
| 14 → 18 | `clamp(14px,1.5vw,18px)` | 2 | disclaimer |
| 15 → 19 | `clamp(15px, 1.5vw, 19px)` | 6 | company |
| 17 → 30 | `clamp(17px, 1.75vw, 30px)` | 1 | editorial.css |
| 18 → 24 | `clamp(18px, 2.2vw, 24px)` | 4 | focus |
| 18 → 28 | `clamp(18px, 2.2vw, 28px)` | 2 | index |
| 18 → 30 | `clamp(18px, 2vw, 30px)` | 4 | focus, index |
| 18 → 30 | `clamp(18px, 2.4vw, 30px)` | 2 | focus |
| 20 → 26 | `clamp(20px, 2.4vw, 26px)` | 2 | focus |
| 20 → 30 | `clamp(20px, 2vw, 30px)` | 2 | approach |
| 20 → 40 | `clamp(20px, 2.4vw, 40px)` | 2 | approach |
| 20 → 40 | `clamp(20px, 3vw, 40px)` | 2 | focus |
| 20 → 44 | `clamp(20px, 2.4vw, 44px)` | 4 | approach |
| 22 → 30 | `clamp(22px, 3.4vw, 30px)` | 2 | approach |
| 22 → 40 | `clamp(22px, 3vw, 40px)` | 2 | about |
| 22 → 40 | `clamp(22px, 2.6vw, 40px)` | 2 | approach |
| 24 → 36 | `clamp(24px, 3vw, 36px)` | 2 | focus |
| 24 → 38 | `clamp(24px, 2.6vw, 38px)` | 2 | index |
| 24 → 56 | `clamp(24px, 3vw, 56px)` | 1 | editorial.css |
| 26 → 36 | `clamp(26px, 3.4vw, 36px)` | 2 | approach |
| 26 → 38 | `clamp(26px, 2.8vw, 38px)` | 2 | about |
| 26 → 40 | `clamp(26px, 2.8vw, 40px)` | 2 | approach |
| 26 → 40 | `clamp(26px, 3vw, 40px)` | 2 | focus |
| 26 → 42 | `clamp(26px, 2.8vw, 42px)` | 2 | focus |
| 27 → 42 | `clamp(27px, 2.9vw, 42px)` | 2 | focus |
| 28 → 36 | `clamp(28px,3vw,36px)` | 4 | disclaimer, privacy |
| 28 → 40 | `clamp(28px, 2.8vw, 40px)` | 2 | about |
| 28 → 52 | `clamp(28px, 4vw, 52px)` | 2 | focus |
| 28 → 56 | `clamp(28px, 3.2vw, 56px)` | 2 | index |
| 28 → 64 | `clamp(28px, 4vw, 64px)` | 2 | about |
| 28 → 72 | `clamp(28px, 4vw, 72px)` | 2 | approach |
| 30 → 44 | `clamp(30px, 2.6vw, 44px)` | 2 | focus |
| 32 → 40 | `clamp(32px,7vw,40px)` | 8 | disclaimer, privacy |
| 32 → 48 | `clamp(32px, 3.5vw, 48px)` | 2 | about |
| 32 → 52 | `clamp(32px, 3.5vw, 52px)` | 2 | index |
| 32 → 56 | `clamp(32px, 4vw, 56px)` | 2 | about |
| 36 → 47 | `clamp(36px, 3.6vw, 47px)` | 2 | focus |
| 36 → 54 | `clamp(36px, 3.6vw, 54px)` | 2 | approach |
| 36 → 56 | `clamp(36px, 4vw, 56px)` | 2 | index |
| 37 → 48 | `clamp(37px, 3.7vw, 48px)` | 2 | focus |
| 37 → 52 | `clamp(37px, 3.7vw, 52px)` | 2 | focus |
| 37 → 54 | `clamp(37px, 3.7vw, 54px)` | 2 | focus |
| 40 → 52 | `clamp(40px, 3.4vw, 52px)` | 6 | about, approach, focus |
| 40 → 56 | `clamp(40px,4.2vw,56px)` | 4 | disclaimer, privacy |
| 40 → 60 | `clamp(40px, 4.2vw, 60px)` | 2 | about |
| 40 → 60 | `clamp(40px, 4vw, 60px)` | 2 | approach |
| 40 → 62 | `clamp(40px, 4.2vw, 62px)` | 2 | company |
| 40 → 64 | `clamp(40px, 4.4vw, 64px)` | 2 | index |
| 48 → 64 | `clamp(48px,5vw,64px)` | 4 | disclaimer, privacy |
| 48 → 70 | `clamp(48px, 4.8vw, 70px)` | 2 | focus |
| 48 → 72 | `clamp(48px, 5vw, 72px)` | 8 | about, approach, focus |
| 48 → 72 | `clamp(48px, 4.8vw, 72px)` | 2 | about |
| 48 → 76 | `clamp(48px, 4.6vw, 76px)` | 2 | focus |
| 51 → 80 | `clamp(51px, 5.1vw, 80px)` | 2 | focus |
| 56 → 78 | `clamp(56px, 5vw, 78px)` | 2 | focus |
| 56 → 80 | `clamp(56px, 5.4vw, 80px)` | 2 | index |
| 56 → 84 | `clamp(56px, 5.4vw, 84px)` | 4 | about |
| 56 → 84 | `clamp(56px, 5.6vw, 84px)` | 3 | company, editorial.css |
| 64 → 92 | `clamp(64px, 6.2vw, 92px)` | 6 | index |
| 64 → 96 | `clamp(64px,7vw,96px)` | 4 | disclaimer, privacy |
| 72 → 104 | `clamp(72px, 7vw, 104px)` | 2 | index |
| 80 → 112 | `clamp(80px, 7.6vw, 112px)` | 2 | index |
| 88 → 120 | `clamp(88px, 8vw, 120px)` | 2 | index |

## Why a one-off is sometimes right

Three patterns account for most of the list:

- **Ceilings off the 8-scale.** Values like 42px, 47px or 54px were tuned
  against one component, usually to line a gap up with a rule or a photograph
  edge rather than with the vertical rhythm.
- **Steep early slopes.** Some use a high `vw` coefficient so they reach their
  ceiling by ~768px — grid gaps that must open before the desktop breakpoint.
  The six tokens all reach theirs between 1280 and 1714.
- **Section bands.** The largest values (72→104, 80→112, 88→120) are full-bleed
  section padding, which already has its own tokens: `--section`,
  `--section-tight`, `--head-top`, `--head-bottom`.

Two values appear twice because the same number is written two ways
(`.6vw` and `0.6vw`, `clamp(28px,3vw,36px)` and `clamp(28px, 3vw, 36px)`).
Normalising that whitespace is worth doing, but it is cosmetic: the computed
values are identical.

# Reiwa Capital - Brand Specification

Single source of truth for the visual system across the English site
(`/`) and the Japanese site (`/ja/`).

Status: **draft for approval.** Sections marked `DECISION` need your
call before they become binding.

Audit date: 7 September 2026
Audited commit: `61a6a26` (branch `claude/reiwa-design-system-2vf1kn`)

---

## 0. Audit summary - what the current state actually is

The brief anticipated four pages that had drifted into four separate
visual identities. **They have not.** The current build is already
running one consolidated system:

| Dimension | Expected drift | Actual state |
|---|---|---|
| Typeface | One per page | DM Sans only, all 16 pages. Serif and mono retired and aliased. |
| Palette | Sprawl | Two canonical tokens (`--plum`, `--cream`) with all legacy names threaded onto them. |
| Tokens | Per-page values | One token file, `assets/colors_and_type.css`, imported everywhere. |
| Nav | Different per page | Rendered once from a data model in `shell.js`. Identical on every page by construction. |
| Logo | Multiple lockups | One lockup geometry, five colourways. |

The consolidation work described in the brief was largely done in an
earlier pass. What follows records the system that exists, names the
things still off-system, and flags the points where the brief and the
build disagree.

---

## 1. Logo lockup

**One lockup. No variants beyond colourway.**

| Asset | Use |
|---|---|
| `assets/logos/lockup-purple.svg` | Default. Nav on light grounds. |
| `assets/logos/lockup-white.svg` | Nav on dark/hero grounds. |
| `assets/logos/lockup-cream.svg` | On plum grounds. |
| `assets/logos/lockup-black.svg` | Structured data / third-party feeds only. |
| `assets/logos/lockup-warmgrey.svg` | **Unused.** Candidate for deletion. |
| `assets/logos/symbol-purple.svg` | Drawer head emblem. |
| `assets/logos/symbol-cream.svg` | Footer mark. |

Geometry: symbol (a folded, four-part origami-style form) plus wordmark,
both drawn as outlined vector paths. Lockup viewBox `0 0 4419 800`;
symbol viewBox `0 0 747 801`. Fill is hard-coded `#271430` in the purple
and black files.

### DECISION 1 - lockup specification conflict

The brief asks for a lockup that is "serif, letterspaced caps". The
actual asset is neither. It is a custom-drawn wordmark in outlined
paths, and there is no serif face anywhere in the system - the serif
token was deliberately retired and aliased to DM Sans.

Three options:

1. **Keep the drawn lockup as-is** and correct this spec. Zero work.
   Recommended: the drawn mark is the stronger asset, and re-cutting a
   wordmark as letterspaced serif caps is a rebrand, not a design-system
   pass.
2. Keep the symbol, reset the wordmark as letterspaced serif caps. Needs
   a serif face selected, licensed and self-hosted, plus new SVGs in
   five colourways.
3. Full rebrand. Out of scope here.

Nothing has been changed. Say which.

### Clear space and minimum size

Not currently specified anywhere in the codebase. Proposed, pending
approval:

- Clear space: one symbol-width on all four sides.
- Minimum width: 132px (lockup), 24px (symbol).
- Never recolour outside the five approved colourways. Never outline,
  rotate, or apply effects.

---

## 2. Palette

### Canonical - binding

| Token | Value | Role |
|---|---|---|
| `--plum` | `#271430` | Primary ink, dark grounds, footer, hero base. |
| `--cream` | `#FCFAF1` | Primary warm ground. |

Everything else in the system either threads onto these two or is listed
below for your approve/kill call.

### Structural neutrals - keep, no decision needed

| Value | Token | Where |
|---|---|---|
| `#FFFFFF` | `--bg-paper` | Cards and tables on cream. 12 uses. |
| `rgba(39,20,48,0.12)` | `--hairline` | 1px rules on light grounds. |
| `rgba(252,250,241,0.16)` | `--hairline-light` | 1px rules on plum grounds. |
| `rgba(252,250,241,0.70 / 0.48)` | `--fg-inverse-2/-3` | Secondary text on plum. |

### DECISION 2 - every other colour currently in the build

Approve or kill each. "Uses" counts real references, not the token
definition line.

**In active use - killing these needs a replacement:**

| Value | Token | Uses | What it does | Recommendation |
|---|---|---|---|---|
| `#100B14` | (hard-coded) | 4 | Hero letterbox ground behind the home hero image. Sits under a photo, never seen bare. | **Keep**, but tokenise as `--hero-ground`. Hard-coded in `index.html` and `ja/index.html`. |
| `#110A1A` | `--night-black` / `--brand-aubergine-deep` | 2 | Deepest ground. | **Keep** - but see note below, it is off-palette. |
| `#F5CAE0` | `--sakura-pink` | 2 | Row-hover wash on the home "What we do" rows. | **Decision.** It is the one genuinely off-palette hue on the site and reads pastel against the plum/cream discipline. Recommend **kill**, replace with a `--plum` tint at 6% - same affordance, on-system. |
| `#B79AD6` | `--accent-sumire-light` | 2 | Map focus-region stroke. | **Decision.** Recommend **keep** - the map needs a light purple that survives on a cream ground, and this is the only one. |
| `#E3DAEC`, `#ECE6F2` | `--reiwa-lavender` family | 6 | Map focus-region fills. | **Keep.** Derivable as plum tints; recommend redefining them as `color-mix` of `--plum` so they stop being independent values. |
| `#6E5A78` | `--eyebrow-ink` | (all eyebrows) | Section labels. | **Keep.** Muted plum, on-system. |
| `#5E3D78`, `#807388`, `#928799`, `#6E637A`, `#4F4458`, `#B0A8B7` | scattered | 1 each | Assorted purples in `brand.css` / `craft.css` / page `<style>` blocks. | **Kill.** These are six near-identical mid-purples doing one job. Collapse to two plum tints. |
| `#F7F2E8`, `#F4F1E8`, `#F5F0E1`, `#FBFAF6`, `#F2EFE7` | warm ground family | 1 each | Five near-identical creams. | **Kill four.** Keep `--cream` plus one muted step. Nobody can tell these apart. |
| `#E5E1D5`, `#C8C2B2`, `#9A9486`, `#6E6A5F`, `#4A463E`, `#2E2B26`, `#1A1814` | `--warm-300…900` | 1-2 each | Warm grey ramp. | **Trim.** `--warm-100`, `--warm-800`, `--warm-900` have zero references. Delete those three, keep the rest. |
| `#BCB5B7`, `#918790` | `--grey-warm`, `--grey-deep` | 0 | Declared, never used. | **Kill.** |
| `#3A2149` | `--brand-aubergine-soft` | 1 | Soft dark ground. | **Keep or fold into a plum tint.** Low stakes. |

**Declared but entirely unused - kill on sight:**

| Value | Token | Note |
|---|---|---|
| `#E5B6B6` | `--accent-sakura` | Chart series 5. No charts exist on the site. |
| `#B84A4A` | `--accent-ume` | Semantic negative. Unused. |
| `#6F8A6A` | `--accent-matcha` | Semantic positive. Unused. |
| `#5B7A94` | `--accent-ai` | Chart series 2 / semantic info. Unused. |
| `#B5924A` | `--accent-gold` | Semantic caution. Unused. |
| `#4B4856` | `--accent-slate` | Chart series 6. Unused. |
| `#E7EEF6` | (hard-coded) | One reference, cool blue. Off-palette. |
| `#FFFFFF` via `--clear-white` | `--clear-white` | Zero references; `--bg-paper` does this job. |

The six `--accent-*` values plus the full `--chart-1…6` and
`--sem-*` blocks are dead weight: a chart palette for a site with no
charts, and a stoplight semantic set for a brand whose own token file
says it "avoids stoplight UX". Recommend deleting the whole block.
That is ~30 lines out and one fewer place for future drift to start.

### Colour count

- Today: **37 distinct hex values** across CSS, HTML and SVG.
- After the kill list above: **11**.

---

## 3. Typeface pairing

**One family. DM Sans. No pairing.**

Reported state per page - all sixteen pages, EN and JA:

| Page | Family in use |
|---|---|
| `index.html` | DM Sans |
| `about.html` | DM Sans |
| `approach.html` | DM Sans |
| `investment-focus.html` | DM Sans |
| `company.html` | DM Sans |
| `privacy.html`, `404.html`, `contact.html` | DM Sans |
| `ja/*` (8 pages) | DM Sans + JP fallback stack |

There is no second typeface anywhere. `--font-serif` and `--font-mono`
still exist as tokens but are aliased to DM Sans, so they are labels,
not faces. `--font-mono` has one reference and `--font-jp` one.

**Recommendation:** delete `--font-serif` and `--font-mono`. A token
named "serif" that resolves to a sans is a trap for the next person
editing this file.

### Faces shipped

Two weights only, self-hosted, no CDN:

| Face | Weight | File |
|---|---|---|
| DM Sans Regular | 400 | `assets/fonts/DMSans-Regular.ttf` |
| DM Sans Medium | 500 | `assets/fonts/DMSans-Medium.ttf` |

No bold. No italic. `font-display: optional`, both faces preloaded on
every page, so type either lands before first paint or the fallback
holds the layout - text never reflows.

Japanese fallback stack: `'Hiragino Kaku Gothic ProN', 'Hiragino Sans',
'Yu Gothic Medium', 'Yu Gothic', YuGothic, Meiryo, 'Noto Sans JP'`.

**Format note:** the faces ship as `.ttf`. WOFF2 would cut roughly 60-70%
off 116KB of font payload for identical rendering, with universal
browser support. Recommend converting. Not done in this pass - it needs
the licensed source files, not a re-encode of the shipped TTFs.

---

## 4. Type scale

Seven responsive tiers. Every role maps to exactly one tier. No page
defines its own sizes. Clamps land on the named desktop value at
~1280px, tablet at ~1024px, mobile at <=430px.

| Tier | Clamp | Line height | Tracking | Role |
|---|---|---|---|---|
| `--type-display` | `clamp(44px, 34px + 2.4vw, 66px)` | 1.05 | -0.02em | Home hero H1 |
| `--type-page-title` | `clamp(36px, 28px + 1.4vw, 48px)` | 1.10 | -0.015em | Internal page H1 |
| `--type-h2` | `clamp(24px, 13px + 1.4vw, 34px)` | 1.12 | -0.01em | Section heading |
| `--type-h3` | `clamp(20px, 2.1vw, 24px)` | 1.20 | -0.005em | Card / subsection title |
| `--type-statement` | `clamp(18px, 15px + 0.5vw, 22px)` | 1.45 | 0 | Lead paragraph |
| `--type-body-l` | `clamp(16px, 14.5px + 0.25vw, 18px)` | 1.60 | 0 | Body |
| `--type-body` | `clamp(16px, 12px + 0.4vw, 17px)` | 1.60 | 0 | Dense / supporting body |
| `--type-caption` | `clamp(12px, 8px + 0.4vw, 13px)` | 1.40 | 0 | Metadata |
| `--type-label` | `clamp(12px, 8px + 0.4vw, 13px)` | 1.00 | 0.14em | Caps label |
| `--type-eyebrow` | `clamp(12px, 8px + 0.4vw, 13px)` | 1.40 | 0.14em | Section eyebrow |

Japanese overrides: line height opens to 1.5-1.8 and tracking to
`0.01em` at heading and body tiers, set via `html[lang="ja"]` rules.

### Optical correction

`--optical-cap: -0.02em` applied as `text-indent` on display and heading
leads. DM Sans carries a left side-bearing on large caps; a
mathematically flush headline reads indented against the labels beneath
it. Size-proportional so it scales with the type.

### Measure

| Token | Value | Use |
|---|---|---|
| `--measure` | 66ch | Long-form body |
| `--measure-lead` | 38ch | Lead lines at larger type |
| `--measure-body` | 620px | Standard explanatory copy |
| `--measure-statement` | 820px | Positioning statements |
| `--container` | 1280px | Page frame |

### Off-scale instances - to clean up

Several page-level `<style>` blocks still declare raw `clamp()` values
instead of referencing a tier, e.g. `.home-hero h1`, `.wwd-h`,
`.wwd-name`, `.hm-lead`. They land on roughly the right sizes but they
are instances, not tokens - the exact thing this spec exists to stop.
**Not changed in this pass** (it touches rendered type sizes on every
page and wants a visual check). Listed in `fix-report.md`.

---

## 5. Spacing rhythm

8px base. Ten steps.

| Token | Value |
|---|---|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 24px |
| `--space-6` | 32px |
| `--space-7` | 48px |
| `--space-8` | 64px |
| `--space-9` | 96px |
| `--space-10` | 128px |

Gutter: `clamp(72px, 5.8vw + 13px, 96px)` - desktop 72-96, tablet 32-40,
mobile 20-24.

### Radii

Architectural, not friendly. `--radius-none: 0`, `--radius-sm: 2px`,
`--radius-md: 4px`, `--radius-lg: 8px`. Pills (999px) are buttons only.
House rule: nothing above 2px except buttons.

### Motion

One clock. Three easings, four durations.

| Token | Value | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | ~95% of motion |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Two-way / looping |
| `--ease-in` | `cubic-bezier(0.40, 0, 1, 1)` | Exits only |

Durations: 180ms fast interaction, 280ms hover, 450ms section, 600ms
panel. Every legacy alias resolves onto these four.

---

## 6. Navigation

One nav, rendered once from a data model in `shell.js`. Not duplicated
in page markup, so it cannot drift - the only way to change it on one
page is to change it on all.

### English - binding

| Order | Label | Href | Key |
|---|---|---|---|
| 1 | Home | `/` | `home` |
| 2 | About | `about.html` | `about` |
| 3 | Approach | `approach.html` | `approach` |
| 4 | Investment Focus | `investment-focus.html` | `focus` |
| 5 | Contact | `company.html` | `contact` |

Plus the EN/JA toggle, present in the nav bar on every page.

### DECISION 3 - the sixth nav item

The brief specifies six items: Home, About, Approach, Investment Focus,
**Company**, Contact. The build has five, and there is no Company page.
`company.html` **is** the Contact page - it carries
`data-page="contact"`, an H1 reading "Contact", and nothing but an email
address and a LinkedIn link. `contact.html` is a 13-line meta-refresh
redirect pointing at it.

So "Company" and "Contact" are currently one page under two names. You
cannot have both nav items without new content, and new pages are out of
scope for this pass.

Three options:

1. **Keep five items.** Recommended, and what is shipped. The site has
   five things to say and says them.
2. Split: build a real Company page (entity, registration, regulatory
   standing, team) and demote Contact to a footer link. This is the
   right answer if you are courting institutional LPs, who look for
   exactly that page and read its absence as a signal. Needs new copy
   from you.
3. Rename `company.html` to `contact.html` and retire the redirect, so
   the URL matches the page. Tidy, but costs whatever equity the
   `/company.html` URL has.

Recommend 2 in the medium term, 1 now.

### Japanese

| Order | Label | Href |
|---|---|---|
| 1 | ホーム | `/ja/` |
| 2 | Reiwa Capital | `/ja/about.html` |
| 3 | 投資アプローチ | `/ja/approach.html` |
| 4 | 投資戦略 | `/ja/investment-focus.html` |
| 5 | お問い合わせ | `/ja/contact.html` |

Insights removed in this pass - see `fix-report.md`.

The JA nav is a separate composition, not a translation of the EN one:
different labels, and it points at the standalone `/ja/` pages rather
than toggling language in place. That is deliberate (JA SEO brief) but
it does mean the site has two navs to keep in step. Flagged.

### Language toggle

Present on every page. Persists to `localStorage` under `reiwa.lang`,
resolved pre-paint by an inline script in each `<head>` so there is no
flash of the wrong language.

Precedence: `?lang=` query param, then stored choice, then `ja` locale
default. On pages with a `data-ja-url`, JA navigates to the standalone
Japanese page; elsewhere it swaps text in place via `data-en` /
`data-ja` attributes with a 570ms crossfade (instant under
`prefers-reduced-motion`).

### Onward flow

Every page ends with a link to the next; Contact returns to Home,
closing the loop. Home > About > Approach > Investment Focus > Contact >
Home.

---

## 7. Image rules

### Binding

1. **No image appears on more than one page.** Each page owns its
   imagery outright. *Currently violated - see below.*
2. **No tourist landmarks.** No Big Ben, no Parliament, no Tower Bridge,
   no windmills, no Eye. The subject is the building, the street, the
   asset - never the postcard.
3. **Architecture, not people.** No stock businesspeople, no handshakes,
   no boardrooms.
4. **Format: WebP only.** No PNG or JPEG for content imagery. PNG is
   permitted only for favicons and the touch icon.
5. **Two widths minimum** on every content image, served via `srcset`
   with explicit `sizes`.
6. **Explicit `width` and `height`** on every `<img>`, always, to
   reserve layout space.
7. **`loading="lazy"` and `decoding="async"`** on everything below the
   fold. Hero images take `fetchpriority="high"` and a `<link
   rel="preload">` instead.
8. **Alt text is descriptive or empty.** Decorative and background
   imagery takes `alt=""`. Never a filename, never a keyword stuff.
9. **Every image has a traceable licence** recorded before it ships.
   *Currently unmet across the whole library - see `fix-report.md`.*

### Current violations

**Rule 1 - repeated images.** The three strategy backgrounds each appear
on two pages:

| Image | Pages |
|---|---|
| `bg-income-800/980.webp` | `index.html` and `investment-focus.html` |
| `bg-repositioning-800/1535.webp` | `index.html` and `investment-focus.html` |
| `bg-hospitality-800/952.webp` | `index.html` and `investment-focus.html` |

Also mirrored across `ja/index.html` and `ja/investment-focus.html`.

This is arguably defensible - the Home cards are deliberate previews of
the Investment Focus chapters, and the visual link is the point. But it
is the rule as written. Needs your call: either commission three
additional assets so Home and Investment Focus each have their own, or
amend the rule to permit a card-to-chapter pairing. Recommend amending
the rule; three more licensed shots is spend for a subtle gain.

**Rule 2 - landmarks.** `market-london-800/1537.webp` leads with Tower
Bridge in the foreground against the City skyline. Tower Bridge is the
single most photographed object in London. Flagged for replacement.

**Rule 9 - licences.** No licence, source or attribution record exists
for any of the eleven images in `assets/imagery/`. No manifest, no
metadata, no note in the repo. This is the highest-priority item in the
whole pass and the only one carrying real downside.

### Current library

| File | Dimensions | Weight | Page |
|---|---|---|---|
| `home-hero-blur.webp` | 1300x1950 | 50KB | Home hero |
| `about-hero-blur.webp` | 1920x1080 | 17KB | About page head |
| `approach-hero-blur.webp` | 1920x1080 | 11KB | Approach page head |
| `focus-hero-blur.webp` | 1920x1080 | 18KB | Investment Focus page head |
| `market-london-800/1537.webp` | 800/1537 wide | 41/128KB | About - London panel |
| `market-amsterdam-800/1562.webp` | 800/1562 wide | 84/276KB | About - Amsterdam panel |
| `bg-income-800/980.webp` | 800/980 wide | 146/230KB | Home + Investment Focus |
| `bg-repositioning-800/1535.webp` | 800/1535 wide | 75/238KB | Home + Investment Focus |
| `bg-hospitality-800/952.webp` | 800/952 wide | 132/194KB | Home + Investment Focus |

All WebP as of this pass.

---

## 8. Copy conventions

- **British English.** -ise not -ize, -our not -or.
- **Hyphens only.** No em dashes, no en dashes in prose.
- **Sentence case** for headings and nav. Caps reserved for eyebrows and
  labels, where the 0.14em tracking token applies.
- **Strategy names are fixed:** Income, Repositioning, **Hospitality**.
  The third is Hospitality everywhere, EN and JA. Never "Select
  Operating Real Estate".
- **Domain is `reiwa-capital.com`,** with no `www`. Email is
  `info@reiwa-capital.com`.

---

## 9. Open decisions - summary

| # | Decision | Recommendation |
|---|---|---|
| 1 | Lockup: keep drawn mark, or re-cut as serif caps? | Keep the drawn mark, amend the spec. |
| 2 | Colour kill list (37 values down to 11). | Approve the full kill list. |
| 3 | Sixth nav item "Company". | Five now; build a real Company page later. |
| 4 | Repeated strategy images across Home and Investment Focus. | Amend the rule, keep the pairing. |
| 5 | Tower Bridge in the London market image. | Replace. |
| 6 | Image licences - no record exists for any asset. | Resolve before further deployment. |
| 7 | `/ja/insights/` - 20 "coming soon" stubs, now out of nav. | Remove from sitemap, or publish. |

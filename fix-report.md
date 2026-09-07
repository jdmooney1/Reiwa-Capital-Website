# Design System Pass - Fix Report

Branch: `claude/reiwa-design-system-2vf1kn`
Base commit: `61a6a26`
Date: 7 September 2026

---

## Headline

**Ten of the twelve defects in the brief do not exist in this
repository.** Not fixed-in-an-earlier-pass; never present. I searched
the full git history with `git log -S` on each exact string and none of
them has ever been committed to this repo.

The brief describes a different build of the site - most likely an
earlier version that lived elsewhere (a page builder, a design file, or
a deploy that was never version-controlled here). Whatever it is, it is
not what is on `main`.

Read the verification table below before doing anything else with this
brief. If the version you were reviewing is live somewhere, it is not
being served from this repository, and that gap needs closing before any
further work.

---

## 1. Verification of the twelve requested fixes

| # | Requested | Status | Evidence |
|---|---|---|---|
| 1 | Typo "South Kensigngton" -> "South Kensington" | **Not present** | Zero matches. "Kensington" does not appear on the site in any spelling. Never in git history. |
| 2 | Typo "Deep occupierl markets" -> "Deep occupier markets" | **Not present** | Zero matches for "occupierl". "Occupier" appears 13 times, correctly spelled in all 13. |
| 3 | Standardise domain to `reiwa-capital.com` | **Already correct** | All 141 absolute URLs are `https://reiwa-capital.com`. All 53 mailto and text emails are `info@reiwa-capital.com`. `CNAME`, `sitemap.xml`, `robots.txt`, canonicals, hreflang, OG and Twitter tags all consistent. No `www`, no alternative domain, anywhere. |
| 4 | Remove Portfolio and Insights from nav | **Portfolio not present; Insights fixed** | "Portfolio" has zero matches anywhere in the repo. Insights existed only in the **Japanese** nav - now removed. See section 2. |
| 5 | Add EN/JA toggle to nav on every page | **Already present** | Rendered by `shell.js` into `[data-shell="nav"]`, which every one of the 16 pages carries. Persists to `localStorage` key `reiwa.lang`, resolved pre-paint. |
| 6 | "Select Operating Real Estate" -> "Hospitality" | **Already correct** | Zero matches for "Select Operating Real Estate". The third strategy is "Hospitality" in all 16 instances - Home cards, Investment Focus chapter, anchors (`#hospitality`), JA titles and meta. No other naming exists to flag. |
| 7 | Footer strapline -> "Tokyo. Investing in London and Amsterdam." | **Applied, with a caveat** | There is no footer strapline. The nearest match is the **home hero** location line, which renders as "TOKYO · LONDON · AMSTERDAM" because of `text-transform: uppercase`. Changed there. See section 3. |
| 8 | Delete three "...tomorrow" taglines | **Not present** | Zero case-insensitive matches for "tomorrow" anywhere in the repo. None of the three strings has ever been committed. |
| 9 | Parliament/Big Ben duplicated on Home | **Not present** | The Home hero is a blurred Nordic-style corner apartment building. The Home cards are a Georgian London townhouse, an Amsterdam canal terrace at dusk, and an illuminated modern hotel facade. No Parliament, no Big Ben, on Home or any other page. Nothing removed, no placeholder created. |
| 10 | Approach CTA carries another firm's engraved slogan | **Not present** | `approach.html` contains exactly one image: `assets/logos/lockup-purple.svg`, the Reiwa lockup. Its page-head background is an abstract blur. There is no CTA image and no engraved text. Nothing removed, no placeholder created. |
| 11 | Convert all PNGs to WebP | **Done** | Three files, 3.35MB -> 46KB. See section 4. |
| 12 | Nav order Home, About, Approach, Investment Focus, Company, Contact | **Blocked - needs your decision** | There is no Company page. See section 5. |

---

## 2. Changes applied

### 2.1 PNG to WebP

| File | Before | After | Reduction |
|---|---|---|---|
| `about-hero-blur.png` -> `.webp` | 505,369 B | 16,720 B | 96.7% |
| `approach-hero-blur.png` -> `.webp` | 1,282,733 B | 10,912 B | 99.1% |
| `focus-hero-blur.png` -> `.webp` | 1,637,644 B | 18,784 B | 98.9% |
| **Total** | **3,425,746 B** | **46,416 B** | **98.6%** |

All three were 1920x1080 RGBA PNGs of heavily blurred abstract imagery -
the single worst-case content type for PNG, which is why the savings are
this large. Alpha was fully opaque (min 254/255) so nothing was lost
flattening to RGB. Encoded at quality 86, method 6.

Source PNGs deleted. References rewritten in `about.html`,
`approach.html`, `investment-focus.html`, `ja/about.html`,
`ja/approach.html`, `ja/investment-focus.html` and `editorial.css`.

The only PNGs remaining are `favicon-32.png` (960 B) and
`apple-touch-icon.png` (4.3 KB), which must stay PNG for platform
support.

### 2.2 Page weight before and after

Full cold-cache transfer: HTML + shared CSS/JS + self-hosted fonts +
every referenced image. Shared shell is 215 KB across all pages.

| Page | Before | After | Saved |
|---|---|---|---|
| `index.html` | 1,290 KB | 1,290 KB | 0 KB |
| `about.html` | 1,250 KB | 773 KB | **477 KB (-38%)** |
| `approach.html` | 1,501 KB | 259 KB | **1,242 KB (-83%)** |
| `investment-focus.html` | 2,841 KB | 1,260 KB | **1,581 KB (-56%)** |
| `company.html` | 223 KB | 223 KB | 0 KB |
| `privacy.html` | 230 KB | 230 KB | 0 KB |

Repository imagery: **4,940 KB -> 1,640 KB**.

Note: these figures count every `srcset` candidate. A real browser
downloads one width per image, so actual transfer is lower - but the
*relative* saving holds, and on `approach.html` the saving is nearly the
entire page.

`approach.html` going from 1.5 MB to 259 KB is the single highest-ROI
change in this pass. It was shipping a 1.28 MB PNG of a blur.

### 2.3 Hero strapline

`index.html` and `ja/index.html`.

- EN: `Tokyo · London · Amsterdam` -> `Tokyo. Investing in London and Amsterdam.`
- JA: `東京 · ロンドン · アムステルダム` -> `東京拠点。ロンドンとアムステルダムに投資しています。`

The element carried `text-transform: uppercase` with 0.14em caps
tracking, which is right for a three-token list and wrong for a
sentence - it would have rendered as "TOKYO. INVESTING IN LONDON AND
AMSTERDAM." I dropped the uppercase and caps tracking and moved it to
sentence-case body treatment. That is a style change beyond the literal
brief; flagged here rather than silently made.

**Needs your review:** the Japanese line is my translation, not
approved copy. The brief gave an English string only, and leaving JA as
a three-city list while EN became a sentence would have desynced the two
sites.

### 2.4 Insights removed from the Japanese nav

`shell.js`. Removed from `NAV_JA`; `FLOW_JA.focus` rewired to point at
Contact rather than Insights.

Note the brief's reason was "no content exists". That is accurate:
`/ja/insights/` lists 20 article titles, every one tagged 近日公開
("coming soon"). Zero published articles. It was a nav item promising
content that does not exist.

The page itself is **not deleted** and is still in `sitemap.xml`. That
is a decision for you - see section 5.

### 2.5 Cache-bust versions unified

`editorial.css` and `shell.js` both changed, so their query strings were
bumped. Three pages - `ja/uk-real-estate.html`,
`ja/netherlands-real-estate.html`, `ja/insights/index.html` - were on
`editorial.css?v=60` / `shell.js?v=62` while the other 13 were on
`v=69` / `v=63`. All 16 are now on `v=70` / `v=64`.

This was a live bug, not housekeeping: those three JA pages were pinned
to stale cached CSS and JS and would not have picked up the last nine
CSS revisions.

---

## 3. What I did NOT change, and why

### Positioning copy under review

Untouched, as instructed:

- "Investment merit must stand independently of tax, structuring or financial engineering."
- "Tax as an enhancement, not the thesis"
- "We do not pursue investments where economics rely primarily on tax treatment."

### Investment Focus page

Out of scope per the brief. It already inherits the shared tokens, nav
and footer; no typos exist on it to fix. No redesign attempted.

### Off-scale type declarations

Several page-level `<style>` blocks declare raw `clamp()` values rather
than referencing a type tier: `.home-hero h1`, `.wwd-h`, `.wwd-name`,
`.hm-lead`, `.home-hero .loc`, and the equivalents in `about.html` and
`approach.html`. They land near the right sizes but are instances, not
tokens.

Not changed: it alters rendered type sizes on every page and wants a
visual check, which is more than a mechanical pass should do unasked.
Listed in `brand-spec.md` section 4.

### Dead tokens

`brand-spec.md` section 2 lists roughly 30 lines of dead colour tokens -
a six-colour chart palette for a site with no charts, and a stoplight
semantic set for a brand whose own token file says it avoids stoplight
UX. Not deleted: killing tokens is your approve/kill call, and it is the
whole point of that section.

---

## 4. Image slots left as placeholder

**None.**

Both placeholder requests in the brief - the Home London card and the
Approach CTA - were for images that do not exist in this build. Creating
empty slots for them would have introduced two holes into pages that
currently render complete.

If the build you were reviewing does have them, it is not this
repository, and locating it is the priority.

---

## 5. Decisions needed from you

Ordered by consequence.

### D1 - Image licences (highest priority)

**No licence, source or attribution record exists for any of the eleven
images in `assets/imagery/`.** No manifest, no EXIF, no note anywhere in
the repo or its history.

| File | Licence record | Note |
|---|---|---|
| `home-hero-blur.webp` | **None** | Nordic-style corner apartment building |
| `about-hero-blur.webp` | **None** | Abstract blur, wildflowers |
| `approach-hero-blur.webp` | **None** | Abstract blur, pale |
| `focus-hero-blur.webp` | **None** | Abstract blur, red/teal |
| `market-london-800.webp` | **None** | Tower Bridge + City skyline |
| `market-london-1537.webp` | **None** | as above |
| `market-amsterdam-800.webp` | **None** | Canal terrace, golden hour |
| `market-amsterdam-1562.webp` | **None** | as above |
| `bg-income-800/980.webp` | **None** | Georgian London townhouse |
| `bg-repositioning-800/1535.webp` | **None** | Amsterdam canal terrace at dusk |
| `bg-hospitality-800/952.webp` | **None** | Illuminated hotel facade at night |

Three of these read strongly as commercial stock. Two - the London
townhouse and the hotel facade - are identifiable real buildings, which
raises property release questions on top of copyright.

This is the only item in the pass carrying material downside. A firm
positioned to institutional capital does not want an unlicensed-image
letter. **Recommend resolving before any further deploy**, and adding
`assets/imagery/LICENCES.md` as a standing requirement.

### D2 - The sixth nav item

The brief asks for both "Company" and "Contact". There is no Company
page: `company.html` **is** the Contact page (`data-page="contact"`, H1
"Contact", one email address and one LinkedIn link).

Shipped five items. Options in `brand-spec.md` section 6, DECISION 3.
My recommendation: five now; build a real Company page (entity,
registration, regulatory standing, team) when you have the copy - it is
the page institutional LPs look for, and its absence is read as a
signal.

### D3 - Colour kill list

`brand-spec.md` section 2 puts 37 distinct hex values in front of you
with a keep/kill recommendation on each. Approving the list takes it to
11. Nothing applied until you say.

Sharpest single item: `--sakura-pink` `#F5CAE0`, the pastel row-hover
wash on the Home "what we do" rows. It is the one genuinely off-palette
hue on the site. Recommend killing it for a plum tint.

### D4 - Repeated imagery

The three strategy backgrounds each appear on both `index.html` and
`investment-focus.html` (and their JA twins). This breaks the "no
repeated images" rule as written.

It is arguably deliberate - the Home cards preview the Investment Focus
chapters and the visual link is the point. Recommend amending the rule
to permit a card-to-chapter pairing rather than commissioning three more
licensed shots.

### D5 - Tower Bridge

`market-london-800/1537.webp` leads with Tower Bridge against the City
skyline. That is a postcard, and the brief's own rule bans tourist
landmarks. The Amsterdam counterpart is well judged - a working canal
terrace, no windmills, no Eye. London should match it: a street-level
City or West End shot, no bridge.

Not replaced - it needs a licensed replacement, which loops back to D1.

### D6 - Lockup specification

The brief specifies "serif, letterspaced caps". The actual lockup is a
custom-drawn wordmark in outlined vector paths, and there is no serif
face in the system. Options in `brand-spec.md` section 1, DECISION 1.
Recommend keeping the drawn mark. Nothing changed.

### D7 - `/ja/insights/`

Now out of the nav, but the page still exists and is still in
`sitemap.xml`, advertising 20 articles that do not exist. Either
publish, or drop from the sitemap and `noindex` it. Twenty "coming soon"
stubs indexed against a firm courting institutional capital is a thin
signal.

### D8 - Fonts ship as TTF

`assets/fonts/*.ttf`, 116 KB, preloaded on every page. WOFF2 would cut
60-70% off that for identical rendering, with universal support. Not
done here - it needs the licensed source files rather than a re-encode
of the shipped TTFs.

### D9 - Two navs to keep in step

The JA nav is a separate composition in `shell.js`, not a translation:
different labels, pointing at standalone `/ja/` pages. Deliberate per
the JA SEO brief, but it does mean every nav change has to be made
twice. Worth knowing.

### D10 - Branch name

The brief specified `fix/design-system-pass`. This session is pinned to
`claude/reiwa-design-system-2vf1kn` by its own configuration and I
cannot push elsewhere without your say-so. Content is identical; say the
word if you want it renamed or cherry-picked across.

---

## 6. Verification run

- All asset references across all 16 HTML files, `editorial.css`,
  `brand.css`, `craft.css` and `assets/colors_and_type.css` resolve to
  files that exist. No broken links introduced.
- No remaining references to the deleted PNGs.
- Both EN and JA hero straplines updated in step.
- `NAV_JA` and `FLOW_JA` consistent - no orphaned `insights` route.

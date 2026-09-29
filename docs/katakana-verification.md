# Katakana line-break protection: verification

`initKatakanaProtect()` in `craft.js` wraps every run of three or more characters in
U+30A0-U+30FF in a `<span class="jt">` on Japanese pages (`html[lang^=ja]`), at load, before
first paint. This records what it fixes and what was checked.

## Why it was needed

Japanese has no inter-word space, so a line can break between two katakana letters. Chromium's
`word-break: auto-phrase` prevents that, so every earlier Chromium check found no problem.
Safari and Firefox do not have `auto-phrase`. With it stripped, Chromium produces the same
splits Firefox does, so this was a coverage gap in the markup (60 of 187 runs, 32%, had no
`.jt`), not an engine quirk.

## Result

| check | main (`d5ea1fa`) | this branch |
|---|---|---|
| Katakana runs (3+ chars) outside `.jt`, 8 JA pages | 61 distinct page/word pairs | **0 of 215** |
| Split runs, 53 widths x 8 pages: Chromium (auto-phrase off) / Firefox / WebKit | 6 / 6 / 9 | **0 / 0 / 0** |
| Named words at the 7 standard widths (332 occurrences): WebKit | 3 split (ロンドン, テナント, リーシング) | **0** |
| Named words, Firefox / Chromium (auto-phrase off) | 0 | 0 |
| Nested `.jt` after wrapping | n/a | 0 (151 hand-placed spans kept, 90 generated) |

Named words: ロンドン 112, テナント 108, リーシング 56, ウェブサイト 42, ブラウザ 7, ローカル 7
occurrences. On main the splits in Firefox and Chromium occur at other widths (e.g. リーシング
at 912px), which the 53-width sweep covers; the 7 standard widths alone under-report them.

Nothing else moved (branch against main, same harness, three engines):

| check | result |
|---|---|
| Text | `<main>` and full `<body>` text byte-identical on 32 loads |
| Overflow, 16 pages x 7 widths | no page-level overflow; element flags identical to main in all 3 engines (0 of 112 differ) |
| CLS, 10 indexed pages at 1440 and 390 | 0 |
| Contrast (AA, rendered pixels) | 0 failures; 581/581 sampled on main, 583/583 on branch (the +2 is the 404 pages gaining a `jt` class) |
| Layout, Chromium | no block on any JA page moved or changed height by 0.1px; EN pages untouched |
| `収益型` / `再生型` | identical in every engine (the one existing `再生型` wrap in `.dl-n` at 1440 is unchanged) |
| Wrap points, EN | unchanged in every engine |
| Wrap points, JA, WebKit | 2 changed, both the fixed cases: リーシン/グ and ロン/ドン now stay whole |

Engines: Chromium 141 (Playwright), Firefox 157 (geckodriver), WebKitGTK 2.52.6
(WebKitWebDriver). WebKitGTK is a Safari proxy, not Safari. Japanese body text uses system
fonts that the test machine does not have, so exact break positions there do not predict
Safari; the rule under test (no split inside a katakana run) does not depend on them.

## Limits

- **Timing.** The wrapper runs when `craft.js` boots, the same point `shell.js` mounts the
  header and footer. Measured against first contentful paint it lands before or within a few
  ms in most runs; on a throttled slow connection one page wrapped 283ms after first paint.
  Chromium shows no shift (nothing reflows there), but Safari could briefly reflow a word that
  would otherwise have split. Not measurable here without Safari.
- **Runs of one or two katakana** are not wrapped. They cannot be split into more than two
  pieces of one and two characters, which line-breaking rules already keep apart in most cases.
- **Text added after boot** would not be wrapped. Nothing does this today (the nav and footer
  render once).
- Only the tab states of `investment-focus` were driven open for the per-word check; other
  hidden content is covered by the run-coverage count, which reads the DOM, not the layout.

## Re-running it

`tools/check-katakana.mjs` fails on any unprotected run or any split at the tested widths,
with `auto-phrase` removed so Chromium cannot mask a gap. It passes on this branch and fails
on `main` (61 unprotected page/word pairs, 4 splits). Run it after any change to Japanese copy:

    npm i playwright                 # anywhere; the site has no build step
    python3 -m http.server 8099      # from the repo root
    BASE=http://127.0.0.1:8099 node tools/check-katakana.mjs

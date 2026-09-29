/* Item-count check: named groups on the pages must render every item.
 *
 * Fails (exit 1) if, at any tested width in either language, a listed group
 * has fewer visible items than it should, or an item renders with no size, or
 * sits wholly or partly outside the viewport horizontally. It exists because a
 * group that loses items (clipped, collapsed to zero width, or removed) passes
 * the overflow, console and request checks.
 *
 * Usage (same set-up as the other tools):
 *   python3 -m http.server 8099            # from the repo root
 *   BASE=http://127.0.0.1:8099 node tools/check-section-items.mjs
 *
 *   CHROME=/path/to/chrome   use a specific Chromium binary
 *   STEP=8                   width step in px (default 16), 280..1600
 */
import { chromium } from 'playwright';

const BASE = (process.env.BASE || 'http://127.0.0.1:8099').replace(/\/$/, '');
const STEP = +(process.env.STEP || 16);
/* [page, selector, expected visible count] - EN path, JA path */
const GROUPS = [
  ['Home: Built from the Investor Side', '/', '/ja/', '.hp .hp-item', 3],
  ['Home: investor-side roles', '/', '/ja/', '.hi-role', 3],
  ['Home: stage periods', '/', '/ja/', '.hi-phase', 3],
  ['Company: responsibilities tiers', '/company.html', '/ja/company.html', '.co-tiers > li', 3],
];
const STANDARD = [1440, 1024, 768, 430, 390, 360, 320];
const WIDTHS = [...new Set([...STANDARD, ...Array.from({ length: Math.floor((1600 - 280) / STEP) + 1 }, (_, i) => 280 + i * STEP)])].sort((a, b) => b - a);

function inPage([sel, want]) {
  const vw = document.documentElement.clientWidth;
  const els = [...document.querySelectorAll(sel)];
  const shown = els.filter((e) => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden');
  const bad = [];
  shown.forEach((e, i) => {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) bad.push(`#${i + 1} has no size (${Math.round(r.width)}x${Math.round(r.height)})`);
    else if (r.left < -1 || r.right > vw + 1) bad.push(`#${i + 1} outside viewport (${Math.round(r.left)}..${Math.round(r.right)} of ${vw})`);
  });
  return { total: els.length, shown: shown.length, want, bad };
}

const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
let fails = 0, loads = 0;
for (const [name, en, ja, sel, want] of GROUPS) {
  for (const [lang, path] of [['en', en], ['ja', ja]]) {
    const failing = [];
    for (const w of WIDTHS) {
      const ctx = await browser.newContext({ viewport: { width: w, height: 800 } });
      const pg = await ctx.newPage();
      await pg.goto(BASE + path, { waitUntil: 'load' });
      loads++;
      const r = await pg.evaluate(inPage, [sel, want]);
      if (r.shown !== want || r.total !== want || r.bad.length) failing.push(`${w}px: ${r.shown}/${want} visible (${r.total} in DOM)${r.bad.length ? ' ' + r.bad.join('; ') : ''}`);
      await ctx.close();
    }
    if (failing.length) { fails++; console.log(`FAIL ${name} [${lang}] ${sel}\n  ` + failing.slice(0, 6).join('\n  ') + (failing.length > 6 ? `\n  ... ${failing.length} widths` : '')); }
  }
}
await browser.close();
console.log(`${GROUPS.length} groups x 2 languages x ${WIDTHS.length} widths (${loads} loads)`);
console.log(fails ? `\nFAIL (${fails})` : '\nPASS');
process.exit(fails ? 1 : 0);

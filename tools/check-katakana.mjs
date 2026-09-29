/* Katakana line-break check for the Japanese pages.
 *
 * Fails (exit 1) if either of these is true:
 *   1. a run of three or more characters in U+30A0-U+30FF sits outside a .jt
 *      no-break span once craft.js has run, or
 *   2. a katakana run is split across two lines at any tested width.
 *
 * It removes `word-break: auto-phrase` from the page before measuring. That
 * property is Chromium-only and hides exactly the defect this looks for; with
 * it left in, a Chromium run passes on a page that splits in Safari and Firefox.
 *
 * Usage (needs Playwright and a Chromium; the site itself has no build step):
 *   npm i playwright                       # anywhere, e.g. a temp directory
 *   python3 -m http.server 8099            # from the repo root
 *   BASE=http://127.0.0.1:8099 node tools/check-katakana.mjs
 *
 *   CHROME=/path/to/chrome   use a specific Chromium binary
 *   STEP=16                  width step in px (default 32); the 7 standard widths always run
 *   PAGES=index,about        limit to some pages (default: all eight)
 */
import { chromium } from 'playwright';

const BASE = (process.env.BASE || 'http://127.0.0.1:8099').replace(/\/$/, '');
const STEP = +(process.env.STEP || 32);
const PAGES = (process.env.PAGES || 'index,about,approach,investment-focus,company,privacy,disclaimer,404').split(',');
const STANDARD = [1440, 1280, 1024, 768, 430, 390, 320];
const WIDTHS = [...new Set([...STANDARD, ...Array.from({ length: Math.floor((1120 - 320) / STEP) + 1 }, (_, i) => 320 + i * STEP)])].sort((a, b) => b - a);

/* Runs in the page. Returns { unprotected, splits }. */
function inPage() {
  const RUN = /[゠-ヿ]{3,}/g;
  // 1. coverage: every run must sit inside a .jt
  const unprotected = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw.nextNode());) {
    const el = n.parentElement;
    if (!el || /^(SCRIPT|STYLE|NOSCRIPT|TITLE)$/.test(el.tagName)) continue;
    RUN.lastIndex = 0;
    for (let m; (m = RUN.exec(n.nodeValue));) if (!el.closest('.jt')) unprotected.push(m[0]);
  }
  // 2. splits: a run whose letters land on two different lines. Read per block
  //    (text flattened across inline elements) so a word that straddles an
  //    element boundary, e.g. リー<b>シング</b>, is still seen as one word.
  const splits = [];
  const INLINE = new Set(['SPAN', 'B', 'I', 'EM', 'STRONG', 'SMALL', 'WBR', 'BR', 'A', 'SUP', 'SUB', 'CODE', 'ABBR', 'TIME', 'MARK', 'U', 'S', 'Q', 'CITE', 'DFN', 'VAR', 'KBD', 'SAMP', 'BDI', 'BDO', 'RUBY', 'RT', 'RP']);
  const leaf = (el) => ![...el.children].some((c) => !INLINE.has(c.tagName));
  document.querySelectorAll('body *').forEach((el) => {
    if (!leaf(el) || !el.checkVisibility || !el.checkVisibility() || /^(SCRIPT|STYLE|NOSCRIPT|TITLE)$/.test(el.tagName)) return;
    if (!/[゠-ヿ]{3,}/.test(el.textContent)) return;
    const chars = [], w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode());) {
      const t = n.nodeValue;
      for (let i = 0; i < t.length; i++) {
        if (!t[i].trim()) continue;
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getBoundingClientRect();
        if (b.width || b.height) chars.push({ c: t[i], top: Math.round(b.top) });
      }
    }
    const flat = chars.map((c) => c.c).join('');
    RUN.lastIndex = 0;
    for (let m; (m = RUN.exec(flat));) {
      const seg = chars.slice(m.index, m.index + m[0].length);
      for (let i = 1; i < seg.length; i++) {
        if (Math.abs(seg[i].top - seg[i - 1].top) < 3) continue;
        if (seg[i - 1].c === '・') continue;      // a break after the middle dot is a designed opportunity
        splits.push(m[0] + ' | ' + seg[i - 1].c + '/' + seg[i].c);
      }
    }
  });
  return { unprotected: [...new Set(unprotected)], splits: [...new Set(splits)] };
}

/* Drop the declaration so the cascade falls back as it does in Safari/Firefox. */
const STRIP = () => {
  document.querySelectorAll('style').forEach((s) => { s.textContent = s.textContent.replace(/word-break:\s*auto-phrase\s*;?/g, ''); });
};

const browser = await chromium.launch(process.env.CHROME ? { executablePath: process.env.CHROME } : {});
const unprot = new Map(), split = new Map();
let loads = 0;
for (const page of PAGES) {
  const url = `${BASE}/ja/${page === 'index' ? '' : page + '.html'}`;
  for (const w of WIDTHS) {
    const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'load' });
    await p.evaluate(() => document.fonts && document.fonts.ready);
    await p.evaluate(STRIP);
    await p.waitForTimeout(120);
    const r = await p.evaluate(inPage);
    loads++;
    r.unprotected.forEach((t) => unprot.set(`${page}: ${t}`, true));
    r.splits.forEach((t) => split.set(`${page}: ${t}`, [...(split.get(`${page}: ${t}`) || []), w]));
    await ctx.close();
  }
}
await browser.close();

console.log(`${PAGES.length} Japanese pages x ${WIDTHS.length} widths (${loads} loads), auto-phrase removed`);
console.log(`unprotected katakana runs (3+ chars outside .jt): ${unprot.size}`);
[...unprot.keys()].sort().slice(0, 30).forEach((k) => console.log('   ' + k));
console.log(`katakana runs split across lines: ${split.size}`);
[...split.entries()].sort().slice(0, 30).forEach(([k, ws]) => console.log(`   ${k}  @ ${ws.join(' ')}`));
const bad = unprot.size + split.size;
console.log(bad ? '\nFAIL' : '\nPASS');
process.exit(bad ? 1 : 0);

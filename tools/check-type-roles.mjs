/* Type-role check: the same semantic role must render at the same size.
 *
 * Every heading and label on the five main pages (English and Japanese) is
 * assigned to one role below, each role maps to one token from the --type-*
 * scale in assets/colors_and_type.css, and the rendered font-size of every
 * visible member of that role must equal that token, as resolved at the
 * viewport being tested. Fails (exit 1) if:
 *   1. a member renders at a size other than its role's token, or
 *   2. a visible h1-h4 in <main> belongs to no role (so a new heading cannot
 *      be added without deciding what it is), or
 *   3. a page has no h1 / a role has no members anywhere (a broken selector
 *      would otherwise pass silently).
 *
 * The size of an element is that of its own text; for an element with no
 * text of its own (an h4 holding a numeral and a name) it is the size of its
 * longest descendant text. The Investment Focus panels are opened as well,
 * since their headings only exist once expanded.
 *
 * Usage (needs Playwright and a Chromium; the site itself has no build step):
 *   npm i playwright                       # anywhere, e.g. a temp directory
 *   python3 -m http.server 8099            # from the repo root
 *   BASE=http://127.0.0.1:8099 node tools/check-type-roles.mjs
 *
 *   CHROME=/path/to/chrome   use a specific Chromium binary
 *   WIDTHS=1440,390          viewport widths to test (default 1440)
 *   PAGES=index,about        limit to some pages (default: the five main pages)
 *   LANGS=en                 en, ja or en,ja (default both)
 *   VERBOSE=1                print every measured element, not only failures
 */
import { chromium } from 'playwright';

const BASE = (process.env.BASE || 'http://127.0.0.1:8099').replace(/\/$/, '');
const WIDTHS = (process.env.WIDTHS || '1440').split(',').map(Number);
const PAGES = (process.env.PAGES || 'index,about,approach,investment-focus,company').split(',');
const LANGS = (process.env.LANGS || 'en,ja').split(',');
const VERBOSE = !!process.env.VERBOSE;

/* role -> token (from the scale) and the selectors that belong to it. */
const ROLES = {
  h1: {
    token: '--type-page-title',
    selectors: ['body:not([data-page="home"]) h1'],
  },
  // The one exception: the Home hero uses --type-display from 761px up. Below
  // that, 44px would wrap the headline to five lines at 320-360px, so phones
  // stay on --type-page-title like every other H1.
  display: {
    token: '--type-display',
    phoneToken: '--type-page-title',
    phoneBelow: 761,
    selectors: ['body[data-page="home"] h1'],
  },
  h2: {
    token: '--type-h2',
    selectors: ['main h2'],
  },
  h3: {
    token: '--type-h3',
    // subsection headings, card titles and item titles
    selectors: [
      '.hm-city', '.hp-item h3', '.hf-cap h3', '.hi-op-v',
      '.am-city', '.aw-stage',
      '.lf-gh', '.lf-pan-h',
      '.tw-item dt',
      '.fx-name', '.fx-stagehead', '.hs-title', '.hs-test-n', '.dl-n',
      '.co-tier-n',
    ],
  },
  label: {
    token: '--type-caption',
    selectors: [
      '.hi-op-k', '.hf-spec-k',
      '.am-k', '.aw-stage-s', '.aw-specs-k',
      '.lf-pan-h b', '.lf-k', '.lf-own-n', '.lf-ap dt',
      '.fx-param-k', '.fx-band-k', '.fx-lever-k', '.hs-kicker', '.dl-kicker',
    ],
  },
};

/* Runs in the page. */
function inPage([roles, vw]) {
  const px = (v) => Math.round(parseFloat(v) * 100) / 100;
  const tokenPx = (token) => {
    const p = document.createElement('span');
    p.style.cssText = `position:absolute;visibility:hidden;font-size:var(${token})`;
    document.body.appendChild(p);
    const v = px(getComputedStyle(p).fontSize);
    p.remove();
    return v;
  };
  const visible = (el) => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const ownSize = (el) => {
    const texts = [];
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = tw.nextNode());) if (n.nodeValue.trim()) texts.push(n);
    if (!texts.length) return null;
    const direct = texts.filter((n) => n.parentNode === el);
    const pool = direct.length ? direct : texts;
    const best = pool.reduce((a, b) => (b.nodeValue.trim().length > a.nodeValue.trim().length ? b : a));
    return px(getComputedStyle(best.parentElement).fontSize);
  };
  const label = (el) => (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 34);
  const rows = [], assigned = new Set(), unassigned = [];
  for (const [role, def] of Object.entries(roles)) {
    const expected = tokenPx(def.phoneToken && vw < def.phoneBelow ? def.phoneToken : def.token);
    for (const sel of def.selectors) {
      document.querySelectorAll(sel).forEach((el) => {
        if (!visible(el)) return;
        const fs = ownSize(el);
        if (fs === null) return;
        assigned.add(el);
        rows.push({ role, sel, text: label(el), fs, expected });
      });
    }
  }
  document.querySelectorAll('main h1, main h2, main h3, main h4, h1').forEach((h) => {
    if (!visible(h) || assigned.has(h)) return;
    unassigned.push({ tag: h.tagName, cls: h.className || '', text: label(h), fs: ownSize(h) });
  });
  return { rows, unassigned, h1s: document.querySelectorAll('h1').length };
}

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
let failures = 0, checked = 0;
const seenRole = Object.fromEntries(Object.keys(ROLES).map((r) => [r, 0]));
const range = {};
for (const lang of LANGS) for (const page of PAGES) for (const w of WIDTHS) {
  const url = `${BASE}${lang === 'ja' ? '/ja' : ''}/${page === 'index' ? '' : page + '.html'}`;
  const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
  const p = await ctx.newPage();
  await p.goto(url, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  const states = [null];
  if (page === 'investment-focus') states.push('0', '1');
  for (const st of states) {
    if (st !== null) {
      const ok = await p.evaluate((s) => { const b = document.querySelector(`button[data-focus="${s}"]`); if (b) b.click(); return !!b; }, st);
      if (!ok) continue;
      await p.waitForTimeout(700);
    }
    const r = await p.evaluate(inPage, [ROLES, w]);
    const where = `${lang}/${page}@${w}${st !== null ? ` [panel ${st} open]` : ''}`;
    if (st === null && r.h1s !== 1) { failures++; console.log(`FAIL ${where}: expected one h1, found ${r.h1s}`); }
    for (const x of r.rows) {
      checked++; seenRole[x.role]++;
      const k = `${x.role}@${w}`;
      (range[k] ||= { min: Infinity, max: -Infinity, exp: x.expected });
      range[k].min = Math.min(range[k].min, x.fs); range[k].max = Math.max(range[k].max, x.fs);
      const bad = Math.abs(x.fs - x.expected) > 0.05;
      if (bad) { failures++; console.log(`FAIL ${where}: [${x.role}] ${x.sel} "${x.text}" renders ${x.fs}px, token is ${x.expected}px`); }
      else if (VERBOSE) console.log(`ok   ${where}: [${x.role}] ${x.sel} "${x.text}" ${x.fs}px`);
    }
    for (const u of r.unassigned) {
      failures++;
      console.log(`FAIL ${where}: <${u.tag.toLowerCase()} class="${u.cls}"> "${u.text}" (${u.fs}px) is in no role - add it to ROLES`);
    }
  }
  await ctx.close();
}
await browser.close();
for (const [role, n] of Object.entries(seenRole)) if (!n) { failures++; console.log(`FAIL role "${role}" matched no element on any page: its selectors are broken`); }
console.log('\nrole@width       min .. max   token');
for (const [k, v] of Object.entries(range).sort()) console.log(`${k.padEnd(16)} ${String(v.min).padStart(6)} .. ${String(v.max).padEnd(6)} ${v.exp}`);
console.log(`\n${checked} elements checked, ${failures} failure${failures === 1 ? '' : 's'}`);
process.exit(failures ? 1 : 0);

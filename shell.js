/* =========================================================================
   Reiwa Capital — shared site shell
   Renders the top nav + footer ONCE from a data model, then leaves the DOM
   alone. Language changes never rebuild these nodes — only text/aria swap
   in place (generic sweep in i18n.js + a couple of manual bits below) — so
   scroll-derived classes, injected logo variants, drawer state and focus
   all survive a language toggle untouched.
   ========================================================================= */

(function () {
  const NAV = [
    { href: 'index.html',    en: 'Home',     ja: 'ホーム',    key: 'home' },
    { href: 'about.html',    en: 'About',    ja: '会社概要',  key: 'about' },
    { href: 'approach.html', en: 'Approach', ja: 'アプローチ', key: 'approach' },
    { href: 'investment-focus.html',  en: 'Investment Focus', ja: '重点領域',  key: 'focus' },
    { href: 'contact.html',  en: 'Contact',  ja: 'お問い合わせ', key: 'contact' },
  ];

  /* Guided onward journey — one continuous editorial read across the five
     pages. Every page but Contact ends by turning to the next chapter;
     Contact returns the reader to Home, closing the loop. No page numbers:
     the site numbers sections within a page, never the pages themselves. */
  const FLOW = {
    home:     { to: 'about',            tEn: 'About',            tJa: '会社概要',     ariaEn: 'Next: About',            ariaJa: '次へ：会社概要' },
    about:    { to: 'approach',         tEn: 'Approach',         tJa: 'アプローチ',   ariaEn: 'Next: Approach',         ariaJa: '次へ：アプローチ' },
    approach: { to: 'investment-focus', tEn: 'Investment Focus', tJa: '重点領域',     ariaEn: 'Next: Investment Focus', ariaJa: '次へ：重点領域' },
    focus:    { to: 'contact',          tEn: 'Contact',          tJa: 'お問い合わせ', ariaEn: 'Next: Contact',          ariaJa: '次へ：お問い合わせ' },
    contact:  { to: 'index', tEn: 'Home', tJa: 'ホーム', labelEn: 'Return to', labelJa: 'トップへ', ariaEn: 'Return to Home', ariaJa: 'トップへ戻る' }
  };

  function currentKey() {
    return document.body.dataset.page || 'home';
  }
  function lang() {
    return document.documentElement.getAttribute('lang') || 'en';
  }

  /* Language-swap sequencing state — module scope so rapid EN↔JA toggles
     supersede each other instead of interleaving stale timers. */
  let langSwapSeq = 0;
  let langSwapPending = null;

  function renderNav() {
    const host = document.querySelector('[data-shell="nav"]');
    if (!host) return;
    const onDark = host.hasAttribute('data-dark');
    const R = (typeof window !== 'undefined' && window.__resources) || {};
    const logoSrc = onDark ? (R.logoWhite || 'assets/logos/lockup-white.svg')
                           : (R.logoBlack || 'assets/logos/lockup-purple.svg');
    const emblemSrc = (R.symbolPurple || 'assets/logos/symbol-purple.svg');
    const cur = currentKey();
    const drawerLinks = NAV.map((n) => {
      const active = n.key === cur ? 'aria-current="page"' : '';
      return `<li><a href="${n.href}" ${active}>
            <span class="dn-label" data-en="${n.en}" data-ja="${n.ja}">${n.en}</span>
          </a></li>`;
    }).join('');

    host.innerHTML = `
      <nav class="nav-bar ${onDark ? 'on-dark' : ''}" role="navigation" aria-label="Primary" data-aria-en="Primary" data-aria-ja="メイン">
        <div class="nav-inner">
          <a class="nav-logo" href="index.html" aria-label="Reiwa Capital">
            <img class="nl-lockup" src="${logoSrc}" alt="Reiwa Capital">
          </a>
          <div class="nav-right">
            <div class="lang-toggle" role="group" aria-label="Language" data-aria-en="Language" data-aria-ja="言語">
              <button data-lang="en" aria-label="English">EN</button>
              <button data-lang="ja" aria-label="日本語">JA</button>
            </div>
            <button class="nav-toggle" type="button" aria-controls="nav-drawer" aria-expanded="false" aria-label="Open menu">
              <span class="nav-toggle-icon" aria-hidden="true"><span class="bar"></span><span class="bar"></span></span>
            </button>
          </div>
        </div>
      </nav>
      <div class="nav-scrim" hidden></div>
      <aside class="nav-drawer" id="nav-drawer" aria-hidden="true" aria-label="Menu" data-aria-en="Menu" data-aria-ja="メニュー">
        <div class="drawer-inner">
          <div class="drawer-head">
            <img class="drawer-emblem" src="${emblemSrc}" alt="Reiwa Capital">
          </div>
          <nav class="drawer-nav" aria-label="Pages" data-aria-en="Pages" data-aria-ja="ページ">
            <ul>${drawerLinks}</ul>
          </nav>
          <div class="drawer-foot">
            <a class="df-mail" href="mailto:info@reiwa-capital.com">info@reiwa-capital.com</a>
            <div class="df-social">
              <a class="df-linkedin" href="https://www.linkedin.com/company/reiwa-cap/" target="_blank" rel="noopener">LinkedIn</a>
              <a href="mailto:info@reiwa-capital.com" aria-label="Email" data-aria-en="Email" data-aria-ja="メール">
                <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="2.5" y="4.75" width="19" height="14.5" rx="1.5"/><path d="M3.2 6.2l8.8 5.9 8.8-5.9"/></svg>
              </a>
            </div>
          </div>
        </div>
      </aside>
    `;
    wireNav(host);
    syncLangButtons();
  }

  /* All interaction wiring — runs exactly once, right after the nav is
     built. Nothing here is ever re-attached, because the nav DOM is never
     rebuilt again after this call. */
  function wireNav(host) {
    host.querySelectorAll('[data-lang]').forEach(btn => {
      btn.addEventListener('click', () => swapLanguage(btn.dataset.lang));
    });

    const bar = host.querySelector('.nav-bar');
    const toggle = host.querySelector('.nav-toggle');
    const drawer = host.querySelector('.nav-drawer');
    const scrim = host.querySelector('.nav-scrim');
    const root = document.documentElement;
    let lastFocus = null;
    let closeTimer = null;

    function trapKey(e) {
      if (e.key === 'Escape') { closeDrawer(); return; }
      if (e.key !== 'Tab') return;
      const f = drawer.querySelectorAll('a[href], button');
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
    function openDrawer() {
      if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; }
      lastFocus = document.activeElement;
      scrim.hidden = false;
      root.classList.add('nav-drawer-open');
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { root.classList.add('nav-drawer-in'); });
      });
      toggle.setAttribute('aria-expanded', 'true');
      syncMenuToggleLabel();
      drawer.setAttribute('aria-hidden', 'false');
      document.addEventListener('keydown', trapKey);
      document.dispatchEvent(new CustomEvent('reiwa:drawer', { detail: { open: true } }));
      const f = drawer.querySelector('a[href], button');
      if (f) setTimeout(function () { f.focus(); }, 80);
    }
    function closeDrawer() {
      root.classList.remove('nav-drawer-in');
      toggle.setAttribute('aria-expanded', 'false');
      syncMenuToggleLabel();
      drawer.setAttribute('aria-hidden', 'true');
      document.removeEventListener('keydown', trapKey);
      document.dispatchEvent(new CustomEvent('reiwa:drawer', { detail: { open: false } }));
      closeTimer = setTimeout(function () {
        root.classList.remove('nav-drawer-open');
        scrim.hidden = true;
      }, 380); /* just past the 320ms slide (--dur-3) */
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    if (toggle && drawer && scrim) {
      toggle.addEventListener('click', function () {
        if (toggle.getAttribute('aria-expanded') === 'true') closeDrawer();
        else openDrawer();
      });
      scrim.addEventListener('click', closeDrawer);
      drawer.querySelectorAll('.drawer-nav a').forEach(function (a) {
        a.addEventListener('click', closeDrawer);
      });
    }
  }

  /* ---- Small manual syncs that generic data-en/data-ja sweep can't cover,
     because they encode state (active/open) rather than pure text. Both are
     cheap and re-run on every languagechange. ---- */
  function syncLangButtons() {
    const l = lang();
    document.querySelectorAll('.lang-toggle [data-lang]').forEach(btn => {
      const active = btn.dataset.lang === l;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-pressed', String(active));
    });
  }
  function syncMenuToggleLabel() {
    const toggle = document.querySelector('.nav-toggle');
    if (!toggle) return;
    const open = toggle.getAttribute('aria-expanded') === 'true';
    const l = lang();
    toggle.setAttribute('aria-label', open ? (l === 'ja' ? 'メニューを閉じる' : 'Close menu')
                                            : (l === 'ja' ? 'メニューを開く' : 'Open menu'));
  }

  function swapLanguage(next) {
    const cur = langSwapPending || lang();
    if (next === cur) return;
    const commit = () => {
      document.documentElement.setAttribute('lang', next);
      try { localStorage.setItem('reiwa.lang', next); } catch {}
      window.dispatchEvent(new CustomEvent('languagechange', { detail: { language: next } }));
    };
    // Signature crossfade (craft.css owns the opacity rules): text breathes
    // out, the swap happens while transparent, the new language breathes
    // in. Height is held so nothing shifts. Reduced motion: instant swap.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { commit(); return; }
    const root = document.documentElement;
    const seq = ++langSwapSeq;
    langSwapPending = next;
    if (!document.body.style.minHeight) {
      document.body.style.minHeight = document.body.offsetHeight + 'px';
    }
    root.classList.add('lang-x', 'lang-out');
    // Flat, absolute schedule (not nested) so a throttled tab clamps each
    // step once instead of compounding: out (0-210) -> swap -> in (310-510)
    // -> settle (570). Every step is token-checked so a newer toggle
    // supersedes this one cleanly.
    setTimeout(() => { if (seq === langSwapSeq) commit(); }, 210);
    setTimeout(() => { if (seq === langSwapSeq) root.classList.remove('lang-out'); }, 310);
    setTimeout(() => {
      if (seq !== langSwapSeq) return;
      root.classList.remove('lang-x');
      document.body.style.minHeight = '';
      langSwapPending = null;
    }, 570);
  }
  window.addEventListener('languagechange', () => { syncLangButtons(); syncMenuToggleLabel(); });

  function renderFooter() {
    const host = document.querySelector('[data-shell="footer"]');
    if (!host) return;
    const symbolCream = ((typeof window !== 'undefined' && window.__resources && window.__resources.symbolCream) || 'assets/logos/symbol-cream.svg');
    const onPrivacy = document.body.dataset.page === 'privacy';
    const f = FLOW[currentKey()];
    const labelEn = f ? (f.labelEn || 'Next page') : '';
    const labelJa = f ? ('labelJa' in f ? f.labelJa : '次のページ') : '';
    /* Standalone onward-navigation block on cream — page content, then this,
       then the footer. It is deliberately NOT footer content: the footer
       carries legal identity only. */
    const nextNav = f ? `
      <nav class="nextnav" aria-label="Page navigation" data-aria-en="Page navigation" data-aria-ja="ページナビゲーション">
        <a class="nn-link" href="${f.to}.html" aria-label="${f.ariaEn}" data-aria-en="${f.ariaEn}" data-aria-ja="${f.ariaJa}">
          <span class="nn-inner">
            <span class="nn-label" data-en="${labelEn}" data-ja="${labelJa}">${labelEn}</span>
            <span class="nn-title-row">
              <span class="nn-title" data-en="${f.tEn}" data-ja="${f.tJa}">${f.tEn}</span>
              <svg class="nn-arrow" viewBox="0 0 22 12" width="22" height="12" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M0.5 6H20.5M14 0.5L20.5 6L14 11.5"/></svg>
            </span>
          </span>
        </a>
      </nav>` : '';

    host.innerHTML = `${nextNav}
      <footer class="footer">
        <div class="footer-inner">
          <a class="ff-brand" href="index.html" aria-label="Reiwa Capital">
            <img src="${symbolCream}" alt="" width="24" height="26">
            <span class="ff-copy">© 2026 Reiwa&nbsp;Capital</span>
          </a>
          <div class="ff-links">
            <a href="https://www.linkedin.com/company/reiwa-cap/" target="_blank" rel="noopener">LinkedIn</a>
            <a href="privacy.html"${onPrivacy ? ' aria-current="page"' : ''} data-en="Privacy" data-ja="プライバシーポリシー">Privacy</a>
          </div>
        </div>
      </footer>
    `;
    /* Narrative progression: the bottom next-page/return-home link (never
       ordinary menu nav) flags the coming load so it can play a brief
       entrance on arrival. See editorial.css .pt-enter / .pt-run and the
       pre-paint consumer script in each page's <head>. */
    const ntLink = host.querySelector('.nn-link');
    if (ntLink) ntLink.addEventListener('click', function () { try { sessionStorage.setItem('reiwa.pagefx', '1'); } catch (e) {} });
  }

  // -------------------- Scroll reveals --------------------
  // The CSS in editorial.css keeps content fully visible unless <html> carries
  // `reveal-on` AND motion is welcome — so print, no-JS, and reduced-motion all
  // render normally. We add the class, tag content blocks, and let an observer
  // fade each one up as it enters. Staggered per sibling group for a soft cascade.
  const REVEAL_SELECTORS = [
    '.home-areas .areas-head',
    '.stage-rail',
    '.om-head', '.om-arch', '.om-investor', '.om-reiwa', '.om-specialists',
    '.contact-direct'
  ];

  function setupReveals() {
    if (!('IntersectionObserver' in window)) return;
    const els = Array.prototype.slice.call(
      document.querySelectorAll(REVEAL_SELECTORS.join(','))
    );
    if (!els.length) return;

    document.documentElement.classList.add('reveal-on');
    els.forEach(el => el.setAttribute('data-reveal', ''));

    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          // Drop the transition once it has had time to play, so a frozen
          // compositor (e.g. backgrounded tab) never leaves content hidden.
          const t = e.target;
          setTimeout(() => { t.style.transition = 'none'; }, 1100);
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });

    els.forEach(el => io.observe(el));

    // Absolute guarantee: whether or not the observer ever delivers for a
    // given element (throttled/backgrounded tab, a browser that never fires
    // the callback, an element already in view at odd geometry), force the
    // visible end state after a generous delay. transition:none first kills
    // any pending/throttled fade so nothing can be caught mid-transition.
    setTimeout(() => {
      els.forEach(el => {
        if (!el.classList.contains('is-in')) {
          el.style.transition = 'none';
          el.classList.add('is-in');
        }
      });
    }, 1600);
  }

  // -------------------- Page transitions --------------------
  // Handled natively via @view-transition in editorial.css — no JS needed.

  // -------------------- Skip link --------------------
  // First tab stop on every page that exposes a #main landmark. Focuses the
  // main region directly (focus() scrolls it into view) so keyboard users can
  // bypass the nav. Pages without #main (immersive chapters) simply opt out.
  function insertSkipLink() {
    if (!document.getElementById('main')) return;
    if (document.querySelector('.skip-link')) return;
    const a = document.createElement('a');
    a.className = 'skip-link';
    a.href = '#main';
    a.setAttribute('data-en', 'Skip to content');
    a.setAttribute('data-ja', '本文へスキップ');
    a.textContent = 'Skip to content';
    a.addEventListener('click', function (e) {
      const main = document.getElementById('main');
      if (!main) return;
      e.preventDefault();
      main.setAttribute('tabindex', '-1');
      main.focus();
    });
    document.body.insertBefore(a, document.body.firstChild);
  }

  // -------------------- Init --------------------
  function boot() {
    try {
      const savedLang = localStorage.getItem('reiwa.lang');
      if (savedLang) document.documentElement.setAttribute('lang', savedLang);
    } catch {}
    insertSkipLink();
    document.querySelectorAll('noscript').forEach(function (n) { n.remove(); });
    renderNav();
    renderFooter();
    setupReveals();
    /* Hero intro + all header/scroll/logo-guard behaviour is owned by craft.js. */
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();

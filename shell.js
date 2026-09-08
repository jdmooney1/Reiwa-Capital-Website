/* =========================================================================
   Reiwa Capital — shared site shell
   Renders the top nav + footer ONCE from a data model, then leaves the DOM
   alone. Language changes never rebuild these nodes — only text/aria swap
   in place (generic sweep in i18n.js + a couple of manual bits below) — so
   scroll-derived classes, injected logo variants and focus all survive a
   language toggle untouched.
   ========================================================================= */

(function () {
  /* Four visible destinations. The logo is the Home link; Contact is a
     section inside Company (/company.html#contact), not a nav item. */
  const NAV = [
    { href: 'about.html',            en: 'About',            ja: '会社概要',   key: 'about' },
    { href: 'approach.html',         en: 'Approach',         ja: 'アプローチ', key: 'approach' },
    { href: 'investment-focus.html', en: 'Investment Focus', ja: '重点領域',   key: 'focus' },
    { href: 'company.html',          en: 'Company',          ja: '会社情報',   key: 'company' },
  ];

  /* Dedicated Japanese site (/ja/) — the same four destinations as English,
     in the same order, with the approved Japanese labels. The logo is the
     Japanese Home link; Contact is a section inside 事業概要
     (/ja/company.html#contact), not a nav item. Only used when
     <body data-locale="ja">. */
  const NAV_JA = [
    { href: '/ja/about.html',            label: 'Reiwaについて', key: 'about' },
    { href: '/ja/approach.html',         label: '投資アプローチ', key: 'approach' },
    { href: '/ja/investment-focus.html', label: '投資方針',      key: 'focus' },
    { href: '/ja/company.html',          label: '事業概要',      key: 'company' },
  ];

  /* Guided onward journey — one continuous editorial read across the five
     pages: Home → About → Approach → Investment Focus → Company → Home.
     Company closes the loop back to Home. No page numbers: the site numbers
     sections within a page, never the pages themselves. */
  const FLOW = {
    home:     { to: 'about',            tEn: 'About',            lead: 'Why Reiwa exists and where we focus',              ariaEn: 'Next: About' },
    about:    { to: 'approach',         tEn: 'Approach',         lead: 'How an investment moves from mandate to ownership', ariaEn: 'Next: Approach' },
    approach: { to: 'investment-focus', tEn: 'Investment Focus', lead: 'Where we concentrate our attention',               ariaEn: 'Next: Investment Focus' },
    focus:    { to: 'company',          tEn: 'Company',          lead: 'Company profile and contact details',              ariaEn: 'Next: Company' }
    /* Company has no entry, and so no band: it is the last page in the
       flow and the contact section closes it. The footer follows. */
  };

  /* The same guided read in Japanese, over the same five pages and in the
     same order, rendered through the same cream band as English:
     ホーム → Reiwaについて → 投資アプローチ → 投資方針 → 事業概要 → ホーム.
     事業概要 closes the loop rather than pointing onward. */
  const FLOW_JA = {
    home:     { to: '/ja/about.html',            t: 'Reiwaについて',  lead: 'Reiwaが果たす役割と、注力する市場',        aria: '次へ：Reiwaについて' },
    about:    { to: '/ja/approach.html',         t: '投資アプローチ', lead: '投資方針の整理から、取得、保有までの流れ', aria: '次へ：投資アプローチ' },
    approach: { to: '/ja/investment-focus.html', t: '投資方針',      lead: 'どこに検討を集中させるか',                aria: '次へ：投資方針' },
    focus:    { to: '/ja/company.html',          t: '事業概要',      lead: '事業の概要と、お問い合わせ先',            aria: '次へ：事業概要' },
    /* 事業概要 has no entry, and so no band: お問い合わせ closes the page. */
    /* Legacy Japanese pages, retained pending their own disposition: they
       keep an onward path rather than ending in a dead stop. */
    contact:  { to: '/ja/company.html', t: '事業概要', lead: '事業の概要と、お問い合わせ先', aria: '次へ：事業概要' },
    insights: { to: '/ja/',             t: 'ホーム',   lead: 'トップページへ',              aria: 'トップページへ戻る' }
  };

  function currentKey() {
    return document.body.dataset.page || 'home';
  }
  function lang() {
    return document.documentElement.getAttribute('lang') || 'en';
  }

  function renderNav() {
    const locale = document.body.dataset.locale === 'ja' ? 'ja' : 'en';
    if (locale === 'ja') renderNavJa(); else renderNavEn();
  }

  /* ---------------------------------------------------------------------
     ENGLISH NAV — all six destinations visible at every width. No
     hamburger, no drawer, no hidden menu.

       >=1101px  logo | link row | language toggle, on one line
       <=1100px  logo + language toggle on line one, the link row wraps to
                 its own full-width second line and scrolls horizontally

     One <ul>, repositioned by CSS. Never a duplicated link list, so
     aria-current and the language sweep each have exactly one target.
     --------------------------------------------------------------------- */
  function renderNavEn() {
    const host = document.querySelector('[data-shell="nav"]');
    if (!host) return;
    const onDark = host.hasAttribute('data-dark');
    const R = (typeof window !== 'undefined' && window.__resources) || {};
    const logoSrc = onDark ? (R.logoWhite || 'assets/logos/lockup-white.svg')
                           : (R.logoBlack || 'assets/logos/lockup-purple.svg');
    const cur = currentKey();

    const links = NAV.map((n) => {
      const active = n.key === cur ? ' aria-current="page"' : '';
      return `<li><a href="${n.href}"${active}><span data-en="${n.en}" data-ja="${n.ja}">${n.en}</span></a></li>`;
    }).join('');

    host.innerHTML = `
      <nav class="nav-bar ${onDark ? 'on-dark' : ''}" role="navigation" aria-label="Primary" data-aria-en="Primary" data-aria-ja="メイン">
        <div class="nav-inner">
          <a class="nav-logo" href="/" aria-label="Reiwa Capital — Home" data-aria-en="Reiwa Capital — Home" data-aria-ja="Reiwa Capital — ホーム" style="min-height:40px">
            <img class="nl-lockup" src="${logoSrc}" alt="">
          </a>
          <div class="nav-right">
            <div class="lang-switch" role="group" aria-label="Language" data-aria-en="Language" data-aria-ja="言語">
              <button type="button" data-lang="en" aria-label="English">EN</button>
              <span class="ls-sep" aria-hidden="true"></span>
              <button type="button" data-lang="ja" aria-label="日本語">JA</button>
            </div>
          </div>
          <ul class="nav-links">${links}</ul>
        </div>
      </nav>
    `;
    wireNav(host);
    syncLangButtons();
  }

  /* ---------------------------------------------------------------------
     JAPANESE NAV — the same composition as English, not a drawer. Same
     wrapping rules, same language switch, same active-page rule; only the
     labels and the logo destination differ. The Japanese labels are static
     text, not data-en/data-ja pairs: /ja/ is a Japanese site, so nothing
     here depends on a runtime language sweep.
     --------------------------------------------------------------------- */
  function renderNavJa() {
    const host = document.querySelector('[data-shell="nav"]');
    if (!host) return;
    const onDark = host.hasAttribute('data-dark');
    const R = (typeof window !== 'undefined' && window.__resources) || {};
    const logoSrc = onDark ? (R.logoWhite || '../assets/logos/lockup-white.svg')
                           : (R.logoBlack || '../assets/logos/lockup-purple.svg');
    const cur = currentKey();

    const links = NAV_JA.map((n) => {
      const active = n.key === cur ? ' aria-current="page"' : '';
      return `<li><a href="${n.href}"${active}><span>${n.label}</span></a></li>`;
    }).join('');

    host.innerHTML = `
      <nav class="nav-bar ${onDark ? 'on-dark' : ''}" role="navigation" aria-label="メイン">
        <div class="nav-inner">
          <a class="nav-logo" href="/ja/" aria-label="Reiwa Capital — ホーム" style="min-height:40px">
            <img class="nl-lockup" src="${logoSrc}" alt="">
          </a>
          <div class="nav-right">
            <div class="lang-switch" role="group" aria-label="言語">
              <button type="button" data-lang="en" aria-label="English">EN</button>
              <span class="ls-sep" aria-hidden="true"></span>
              <button type="button" data-lang="ja" aria-label="日本語">JA</button>
            </div>
          </div>
          <ul class="nav-links">${links}</ul>
        </div>
      </nav>
    `;
    wireNav(host);
    syncLangButtons();
  }

  /* Interaction wiring — runs exactly once, right after the nav is built.
     Nothing here is ever re-attached, because the nav DOM is never rebuilt
     again after this call. Both headers are flat bars, so the only wiring
     the nav needs is the language switch. */
  function wireNav(host) {
    host.querySelectorAll('[data-lang]').forEach(btn => {
      btn.addEventListener('click', () => swapLanguage(btn.dataset.lang));
    });
  }

  /* ---- Small manual syncs that generic data-en/data-ja sweep can't cover,
     because they encode state (active/open) rather than pure text. Both are
     cheap and re-run on every languagechange. ---- */
  function syncLangButtons() {
    const l = lang();
    document.querySelectorAll('.lang-switch [data-lang]').forEach(btn => {
      const active = btn.dataset.lang === l;
      btn.classList.toggle('is-active', active);
      btn.setAttribute('aria-pressed', String(active));
    });
  }

  /* EN <-> JA is a navigation, not a text swap: each site is written in
     its own language in its own files, and every page declares its
     counterpart on <body> (data-en-url / data-ja-url). A page with no
     counterpart declared simply has nowhere to send the reader, so the
     control does nothing rather than half-translating the page in place. */
  function swapLanguage(next) {
    if (next === lang()) return;
    const crossUrl = document.body.dataset[next + 'Url'];
    if (crossUrl) window.location.href = crossUrl;
  }
  window.addEventListener('languagechange', syncLangButtons);

  function renderFooter() {
    const host = document.querySelector('[data-shell="footer"]');
    if (!host) return;
    const locale = document.body.dataset.locale === 'ja' ? 'ja' : 'en';
    const R = (typeof window !== 'undefined' && window.__resources) || {};
    const onPrivacy = document.body.dataset.page === 'privacy';

    let nextNav = '';
    if (locale === 'ja') {
      /* Same cream band, same three-part text block, same arrow as English
         — the closing treatment is part of the approved system, not of the
         English language. */
      const fj = FLOW_JA[currentKey()];
      nextNav = fj ? `
      <nav class="nextnav nextnav--band" aria-label="ページナビゲーション">
        <a class="nn-link" href="${fj.to}" aria-label="${fj.aria}">
          <span class="nn-inner">
            <span class="nn-text">
              <span class="nn-title">${fj.t}</span>
              <span class="nn-lead">${fj.lead}</span>
            </span>
            <svg class="nn-arrow" viewBox="0 0 44 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M0 12H42M32 2l10 10-10 10"/></svg>
          </span>
        </a>
      </nav>` : '';
    } else {
      const f = FLOW[currentKey()];
      nextNav = f ? `
      <nav class="nextnav nextnav--band" aria-label="Page navigation">
        <a class="nn-link" href="${f.to}.html" aria-label="${f.ariaEn}">
          <span class="nn-inner">
            <span class="nn-text">
              <span class="nn-title">${f.tEn}</span>
              <span class="nn-lead">${f.lead}</span>
            </span>
            <svg class="nn-arrow" viewBox="0 0 44 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M0 12H42M32 2l10 10-10 10"/></svg>
          </span>
        </a>
      </nav>` : '';
    }

    const privacyHref = locale === 'ja' ? '/ja/privacy.html' : 'privacy.html';
    const privacyLabel = locale === 'ja' ? '<span>プライバシーポリシー</span>' : '<span data-en="Privacy" data-ja="プライバシーポリシー">Privacy</span>';

    const homeHref = locale === 'ja' ? '/ja/' : '/';
    const symbolSrc = locale === 'ja' ? '/assets/logos/symbol-cream.svg' : 'assets/logos/symbol-cream.svg';
    const homeAria = locale === 'ja' ? 'Reiwa Capital — ホーム' : 'Reiwa Capital — Home';

    /* One quiet cream footer in both languages — copyright left, the cream
       emblem mathematically centred, Privacy right. No navigation list, no
       location line, no socials. The onward journey lives in the NEXT block
       above it, where the site still has one. */
    const footer = `
      <footer class="footer footer-quiet">
        <div class="footer-inner">
          <span class="ff-copy">© 2026 Reiwa&nbsp;Capital</span>
          <a class="ff-brand" href="${homeHref}" aria-label="${homeAria}"><img class="ff-symbol" src="${symbolSrc}" alt="" width="26" height="26"></a>
          <div class="ff-right">
            <a class="ff-link ff-privacy" href="${privacyHref}"${onPrivacy ? ' aria-current="page"' : ''}>${privacyLabel}</a>
          </div>
        </div>
      </footer>`;
    host.innerHTML = `${nextNav}${footer}`;
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
    '.hi-head', '.hi-cols', '.hm-head', '.hm-stage', '.hp-grid', '.hf-head', '.hf-grid',
    '.home-areas .areas-head',
    '.wwd-head', '.home-markets-head', '.activity-head', '.hww-head', '.hww-panel', '.platform-head', '.contact-cta-head',
    '.stage-rail',
    '.om-investor', '.om-reiwa', '.om-specialists',
    '.contact-direct',
    '.identity .ed-row', '.rationale .ed-row', '.markets .ed-row', '.clients .shell',
    '.assessment .assess-grid', '.areas .chapter',
    '.profile', '.contact-body .shell'
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
    const ja = document.body.dataset.locale === 'ja';
    const a = document.createElement('a');
    a.className = 'skip-link';
    a.href = '#main';
    a.setAttribute('data-en', 'Skip to content');
    a.setAttribute('data-ja', '本文へスキップ');
    /* /ja/ pages are Japanese in source and carry no runtime sweep, so the
       skip link has to be built in the language of the page it lands on. */
    a.textContent = ja ? '本文へスキップ' : 'Skip to content';
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

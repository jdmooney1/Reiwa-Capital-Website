/* =========================================================================
   Reiwa Capital — shared site shell
   Renders the top nav + footer ONCE from a data model, then leaves the DOM
   alone: scroll-derived classes, injected logo variants and focus all
   survive for the life of the page.
   ========================================================================= */

(function () {
  /* Four visible destinations. The logo is the Home link; Contact is a
     section inside Company (/company.html#contact), not a nav item. */
  const NAV = [
    { href: 'about.html',            label: 'About',            key: 'about' },
    { href: 'approach.html',         label: 'Approach',         key: 'approach' },
    { href: 'investment-focus.html', label: 'Investment Focus', key: 'focus' },
    { href: 'company.html',          label: 'Company',          key: 'company' },
  ];

  /* Guided onward journey — one continuous editorial read across the five
     pages: Home → About → Approach → Investment Focus → Company → Home.
     Company closes the loop back to Home. No page numbers: the site numbers
     sections within a page, never the pages themselves. */
  const FLOW = {
    home:     { to: 'about',            title: 'About',            lead: 'Why Reiwa exists and where we focus',              aria: 'Next: About' },
    about:    { to: 'approach',         title: 'Approach',         lead: 'How an investment moves from mandate to ownership', aria: 'Next: Approach' },
    approach: { to: 'investment-focus', title: 'Investment Focus', lead: 'Where we concentrate our attention',               aria: 'Next: Investment Focus' },
    focus:    { to: 'company',          title: 'Company',          lead: 'Company profile and contact details',              aria: 'Next: Company' }
    /* Company has no entry, and so no band: it is the last page in the
       flow and the contact section closes it. The footer follows. */
  };

  function currentKey() {
    return document.body.dataset.page || 'home';
  }

  /* ---------------------------------------------------------------------
     NAV — all four destinations visible at every width. No hamburger, no
     drawer, no hidden menu.

       >=1101px  logo | link row, on one line
       <=1100px  logo on line one, the link row wraps to its own full-width
                 second line

     One <ul>, repositioned by CSS. Never a duplicated link list, so
     aria-current has exactly one target. The logo holds the 40px row
     height that sets the bar's proportions.
     --------------------------------------------------------------------- */
  function renderNav() {
    const host = document.querySelector('[data-shell="nav"]');
    if (!host) return;
    const onDark = host.hasAttribute('data-dark');
    const R = (typeof window !== 'undefined' && window.__resources) || {};
    const logoSrc = onDark ? (R.logoWhite || 'assets/logos/lockup-white.svg')
                           : (R.logoBlack || 'assets/logos/lockup-purple.svg');
    const cur = currentKey();

    const links = NAV.map((n) => {
      const active = n.key === cur ? ' aria-current="page"' : '';
      return `<li><a href="${n.href}"${active}><span>${n.label}</span></a></li>`;
    }).join('');

    host.innerHTML = `
      <nav class="nav-bar ${onDark ? 'on-dark' : ''}" role="navigation" aria-label="Primary">
        <div class="nav-inner">
          <a class="nav-logo" href="/" aria-label="Reiwa Capital — Home" style="min-height:40px">
            <img class="nl-lockup" src="${logoSrc}" alt="">
          </a>
          <ul class="nav-links">${links}</ul>
        </div>
      </nav>
    `;
  }

  function renderFooter() {
    const host = document.querySelector('[data-shell="footer"]');
    if (!host) return;
    const onPrivacy = document.body.dataset.page === 'privacy';

    const f = FLOW[currentKey()];
    const nextNav = f ? `
      <nav class="nextnav nextnav--band" aria-label="Page navigation">
        <a class="nn-link" href="${f.to}.html" aria-label="${f.aria}">
          <span class="nn-inner">
            <span class="nn-text">
              <span class="nn-title">${f.title}</span>
              <span class="nn-lead">${f.lead}</span>
            </span>
            <svg class="nn-arrow" viewBox="0 0 44 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M0 12H42M32 2l10 10-10 10"/></svg>
          </span>
        </a>
      </nav>` : '';

    /* One quiet cream footer — copyright left, the cream emblem
       mathematically centred, Privacy right. No navigation list, no
       location line, no socials. The onward journey lives in the NEXT
       block above it, where the site still has one. */
    const footer = `
      <footer class="footer footer-quiet">
        <div class="footer-inner">
          <span class="ff-copy">© 2026 Reiwa&nbsp;Capital</span>
          <a class="ff-brand" href="/" aria-label="Reiwa Capital — Home"><img class="ff-symbol" src="assets/logos/symbol-cream.svg" alt="" width="26" height="26"></a>
          <div class="ff-right">
            <a class="ff-link ff-privacy" href="privacy.html"${onPrivacy ? ' aria-current="page"' : ''}><span>Privacy</span></a>
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
    const a = document.createElement('a');
    a.className = 'skip-link';
    a.href = '#main';
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

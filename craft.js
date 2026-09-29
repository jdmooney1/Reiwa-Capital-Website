/* =========================================================================
   Reiwa Capital — Craft & interaction
   Calm, restrained motion: opacity/transform only, one house easing.
   Everything degrades: reduced-motion and no-JS leave all content visible.
   Loads AFTER shell.js + i18n.js.
   ========================================================================= */
(function () {
  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 0. Katakana no-break protection (Japanese pages) --------
     Japanese has no inter-word space, so a line can break between any two
     katakana letters and split a loanword (リーシン / グ). Chromium hides
     this with word-break: auto-phrase; Safari and Firefox do not have it,
     and on iPhones that is most of the audience. So every run of three or
     more katakana is wrapped in .jt, the same no-break span the markup
     already uses by hand. Done here, from the character range, so new copy
     is protected without anyone remembering to tag it.

     U+30A0–U+30FF is the whole katakana block: letters, the long-vowel
     mark ー and the middle dot ・. Runs already inside a .jt are left alone,
     so the hand-placed spans are never double-wrapped. Runs before the first
     paint (boot fires on DOMContentLoaded, after shell.js has mounted the
     header and footer), so nothing reflows on screen. Text is untouched:
     only spans are added, textContent stays byte-identical. */
  function initKatakanaProtect() {
    if (!/^ja(\b|-)/i.test(document.documentElement.lang || '')) return;
    var HAS = /[゠-ヿ]{3,}/;
    var SKIP = /^(SCRIPT|STYLE|NOSCRIPT|TEXTAREA|TITLE|CODE|PRE)$/;
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var el = n.parentElement;
        if (!el || SKIP.test(el.nodeName) || el.closest('.jt')) return NodeFilter.FILTER_REJECT;
        return HAS.test(n.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);   // collect first: splitting mutates the tree
    nodes.forEach(function (node) {
      var text = node.nodeValue, re = /[゠-ヿ]{3,}/g, last = 0, m;
      var frag = document.createDocumentFragment();
      while ((m = re.exec(text))) {
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        var span = document.createElement('span');
        span.className = 'jt';
        span.setAttribute('data-jt', 'auto');        // generated here, not hand-placed
        span.textContent = m[0];
        frag.appendChild(span);
        last = m.index + m[0].length;
      }
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  /* ---------- 1. Hero — one simple restrained fade-up ----------------- */
  function initHero() {
    var hero = document.querySelector('.home-hero');
    if (!hero || REDUCED) return;
    document.documentElement.classList.add('hero-arm');
    var load = function () { hero.classList.add('is-loaded'); };
    // rAF for the smooth case; timeout + load as fallbacks so a hero that
    // mounts in a backgrounded tab (rAF throttled) never stays hidden.
    requestAnimationFrame(function () { requestAnimationFrame(load); });
    setTimeout(load, 120);
    window.addEventListener('load', load);
    // Safety: once the reveal has had time to play, drop the transitions so
    // content can never sit stuck mid-reveal (backgrounded tab / frozen
    // compositor).
    setTimeout(function () {
      var sel = hero.querySelectorAll('h1, .sub, .loc, .hero-media');
      for (var i = 0; i < sel.length; i++) sel[i].style.transition = 'none';
    }, 1200);
  }

  /* ---------- 2. Header state — ONE authoritative function ------------
     updateHeaderState() derives the header's appearance from: current page,
     whether it has a hero, scroll position, whether the hero heading
     geometrically overlaps the logo, and drawer open/closed. It runs after
     load, scroll, resize, drawer open/close, language change and bfcache
     restore. The nav DOM itself is built once by shell.js and never
     rebuilt, so this never needs to "re-find" a fresh bar — the reference
     stays valid for the life of the page. */
  function initHeaderState() {
    var bar = document.querySelector('.nav-bar');
    if (!bar) return;
    var page = document.body.dataset.page;
    var isHome = page === 'home';

    // Inject the white logo variant alongside the dark one (home only).
    // Runs once — the nav DOM persists, so the injected node persists too.
    (function ensureLightLogo() {
      if (!isHome) return;
      var link = bar.querySelector('.nav-logo');
      var img = link && link.querySelector('img');
      if (img && !link.querySelector('.logo-light')) {
        img.classList.add('logo-dark');
        var R = window.__resources || {};
        var light = document.createElement('img');
        light.className = 'logo-light';
        light.alt = '';
        light.setAttribute('aria-hidden', 'true');
        light.src = R.logoWhite || 'assets/logos/lockup-white.svg';
        link.appendChild(light);
      }
    })();

    var hero = document.querySelector('.home-hero');
    // Home floats over the dark hero; About/Approach/Investment Focus float
    // over their own full-bleed pale hero; Contact and any other page keep
    // the condensed bar throughout.
    var head = (page === 'about' || page === 'approach' || page === 'focus') ? document.querySelector('.page-head') : null;
    var floatEl = hero || head;
    var floatClass = hero ? 'nav-over-hero' : 'nav-over-head';
    var PAD_IN = 10, PAD_OUT = 16; // protection zone (~8–12px around the logo) + wider exit band so the boundary never flickers
    var ticking = false;

    function updateHeaderState() {
      ticking = false;
      // Actual rendered header height (not an approximate constant) — used
      // by :target scroll-margin-top so anchor jumps (Process stages,
      // Home's Acquire/Structure/Oversee links) always clear the fixed bar.
      // Recomputed on every trigger below, incl. font load + orientation.
      var navH = Math.ceil(bar.getBoundingClientRect().height);
      // --nav-h is the header's TRUE height: consumers that must sit flush
      // beneath it (the hero's negative offset, the Approach sticky process
      // tracker's `top`) cannot carry a fudge factor or a strip of scrolling
      // content shows through the gap. Anchor jumps want deliberate breathing
      // room, so they get their own token instead.
      if (navH) {
        document.documentElement.style.setProperty('--nav-h', navH + 'px');
        document.documentElement.style.setProperty('--anchor-h', (navH + 16) + 'px');
      }
      var past;
      if (floatEl) {
        // Trigger the instant the hero's own bottom edge (live geometry —
        // never a cached height or scroll-offset arithmetic) reaches the
        // fixed header's own actual rendered bottom edge, so the header can
        // never go solid while a strip of hero is still visible beneath it,
        // and never lag once the hero has fully passed behind it.
        var heroBottom = floatEl.getBoundingClientRect().bottom;
        var barBottom = bar.getBoundingClientRect().bottom;
        past = heroBottom <= barBottom;
        bar.classList.toggle(floatClass, !past);
        bar.classList.toggle('is-scrolled', past);
      } else {
        past = true;
        bar.classList.add('is-scrolled');
      }
      // Divider + solid ground arrive together, dynamically measured off
      // the floated element's own rendered height (never a fixed number),
      // and only once the header has actually condensed — never while
      // still floating transparently over the hero itself.
      bar.classList.toggle('header-past-threshold', past);
      var floating = bar.classList.contains('nav-over-hero') || bar.classList.contains('nav-over-head');
      var logo = bar.querySelector('.nav-logo');
      var h1 = document.querySelector('.home-hero h1, .page-head h1');
      if (floating && logo && h1) {
        /* The whole bar is measured, not the logo alone, so the link row and
           the language switch dip out together with it. */
        var a = (bar.querySelector('.nav-inner') || logo).getBoundingClientRect();
        var b = h1.getBoundingClientRect();
        // Hysteresis: enter at PAD_IN, leave only once clear of PAD_OUT.
        var P = bar.classList.contains('logo-needs-contrast') ? PAD_OUT : PAD_IN;
        var hit = b.left < a.right + P &&
                  b.right > a.left - P &&
                  b.top < a.bottom + P &&
                  b.bottom > a.top - P;
        bar.classList.toggle('logo-needs-contrast', hit);
      } else {
        bar.classList.remove('logo-needs-contrast');
      }
    }
    function requestUpdate() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(updateHeaderState);
    }

    updateHeaderState();
    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', requestUpdate, { passive: true });
    window.addEventListener('languagechange', requestUpdate);
    window.addEventListener('orientationchange', requestUpdate);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(requestUpdate);
    window.addEventListener('pageshow', requestUpdate); // bfcache restore
    document.addEventListener('reiwa:drawer', requestUpdate);
    // Safety net after the hero's own reveal transitions settle — geometry
    // (esp. Japanese heading line-wrap) can shift slightly as fonts/layout
    // finish settling.
    setTimeout(requestUpdate, 1300);
    window.ReiwaHeader = { update: requestUpdate };
  }

  /* ---------- 3. Content images — reserve the box, fade the pixels --- */
  function initImageFades() {
    if (REDUCED) return;
    var imgs = document.querySelectorAll('.area-media, .mf-figure img');
    for (var i = 0; i < imgs.length; i++) (function (img) {
      if (img.dataset.faded) return;
      // Already painted (cached) — leave visible, no flash.
      if (img.complete && img.naturalWidth) { img.dataset.faded = '1'; return; }
      // opacity:0 is set in JS only, so no-JS / reduced-motion never hides art.
      img.style.opacity = '0';
      var reveal = function () {
        if (img.dataset.faded) return;
        img.dataset.faded = '1';
        img.style.transition = 'opacity var(--dur-3) var(--ease-out)';
        img.style.opacity = '1';
        // Hand easing back to the stylesheet once the fade has played — the
        // inline shorthand would otherwise silence the CSS hover transitions
        // (card zoom, next-chapter grade) for the life of the page.
        setTimeout(function () { img.style.transition = ''; img.style.opacity = ''; }, 420);
      };
      img.addEventListener('load', reveal, { once: true });
      if (img.decode) img.decode().then(reveal).catch(function () {});
      // Safety: reveal regardless after 1.2s — a stalled decode or dropped
      // load event must never leave art hidden (house rule: everything degrades).
      setTimeout(reveal, 1200);
    })(imgs[i]);
  }

  /* ---------- 4. Page-head hero wash — same load pattern -------------- */
  // The inner-page heads paint their imagery as a CSS background, which
  // initImageFades can't observe. Decode the same URL, then release the
  // paper cover editorial.css holds over the wash.
  function initHeadWashFade() {
    if (REDUCED) return;
    var head = document.querySelector('.page-head');
    if (!head) return;
    var bg = getComputedStyle(head).backgroundImage || '';
    var m = bg.match(/url\(["']?([^"')]+)["']?\)/);
    if (!m) return;
    var root = document.documentElement;
    root.classList.add('bg-fade');
    var done = function () { root.classList.add('bg-loaded'); };
    var img = new Image();
    img.onload = done; img.onerror = done;
    img.src = m[1];
    if (img.complete) done();
    setTimeout(done, 1200); // safety: never hold the head hostage
  }

  /* ---------- boot --------------------------------------------------- */
  function boot() {
    initKatakanaProtect();
    initHero();
    initHeaderState();
    initImageFades();
    initHeadWashFade();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else { boot(); }
})();

/* =========================================================================
   Reiwa Capital — language swap
   Every translatable element carries data-en and data-ja (HTML allowed).
   The head resolver decides the language before paint and sets <html lang>;
   the EN/JA toggle in the shell dispatches `languagechange`.
   EN renders English only; JA renders Japanese only.
   ========================================================================= */
(function () {
  function getLang() {
    var l = document.documentElement.getAttribute('lang');
    if (l === 'ja' || l === 'en') return l;
    if (window.__reiwaLang === 'ja' || window.__reiwaLang === 'en') return window.__reiwaLang;
    try { return localStorage.getItem('reiwa.lang') === 'ja' ? 'ja' : 'en'; }
    catch (e) { return 'en'; }
  }
  function apply(lang) {
    var l = lang === 'ja' ? 'ja' : 'en';
    var nodes = document.querySelectorAll('[data-en]');
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var v = l === 'ja' ? el.getAttribute('data-ja') : el.getAttribute('data-en');
      if (v != null) el.innerHTML = v;
    }
    // Same convention, for attributes instead of content: data-aria-en /
    // data-aria-ja localise aria-label; data-title-en / data-title-ja
    // localise the title attribute, where either is present.
    var ariaNodes = document.querySelectorAll('[data-aria-en]');
    for (var j = 0; j < ariaNodes.length; j++) {
      var an = ariaNodes[j];
      var av = l === 'ja' ? an.getAttribute('data-aria-ja') : an.getAttribute('data-aria-en');
      if (av != null) an.setAttribute('aria-label', av);
    }
    var titleNodes = document.querySelectorAll('[data-title-en]');
    for (var k = 0; k < titleNodes.length; k++) {
      var tn = titleNodes[k];
      var tv = l === 'ja' ? tn.getAttribute('data-title-ja') : tn.getAttribute('data-title-en');
      if (tv != null) tn.setAttribute('title', tv);
    }
    document.documentElement.setAttribute('lang', l);
  }
  function run() {
    apply(getLang());
  }
  // This file loads at the end of <body>, so page content already exists —
  // apply now to swap before first paint. The shell injects nav/footer on
  // DOMContentLoaded (already in the resolved language), so re-run then too.
  run();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  window.addEventListener('languagechange', function (e) { apply(e && e.detail && e.detail.language ? e.detail.language : getLang()); });
  window.ReiwaI18n = { apply: apply, getLang: getLang };
})();

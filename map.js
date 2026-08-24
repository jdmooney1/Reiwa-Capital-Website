(function () {
  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var UK_ID = '826', NL_ID = '528';
  var EUROPE_IDS = [4,8,20,31,40,51,56,70,100,112,191,196,203,208,233,234,246,250,268,276,292,300,336,348,352,372,380,392,398,417,428,438,440,442,470,492,498,499,528,578,616,620,642,643,674,680,688,703,705,724,752,756,762,795,804,807,826,831,833];
  var EUROPE_SET = {}; EUROPE_IDS.forEach(function (id) { EUROPE_SET[String(id)] = true; });
  var LONDON = [-0.1278, 51.5074];
  var AMSTERDAM = [4.9041, 52.3676];
  var SVGNS = 'http://www.w3.org/2000/svg';

  /* Two art-directed renders, not one map scaled down. Desktop takes a wide
     Western-European band; mobile takes a tighter, near-square crop around
     the two markets so London and Amsterdam stay legible in a phone column
     instead of letterboxing a 2:1 figure into a 1:1 box. Leader offsets are
     authored per render, since they are viewBox units, not relative units. */
  var DESKTOP = {
    vbW: 1400, vbH: 700, pad: 76,
    lon: [-9.5, 16.5], lat: [48, 56],
    london: [-48, -36], amsterdam: [44, -32]
  };
  var MOBILE = {
    vbW: 800, vbH: 800, pad: 54,
    lon: [-9, 8.5], lat: [48.8, 59.2],
    london: [-40, -30], amsterdam: [38, -26]
  };
  var MOBILE_MQ = '(max-width: 700px)';

  function view() { return window.matchMedia(MOBILE_MQ).matches ? MOBILE : DESKTOP; }

  function el(ns, tag, cls) {
    var n = document.createElementNS(ns, tag);
    if (cls) n.setAttribute('class', cls);
    return n;
  }

  function makeCity(anchor, v, en, ja, cls, href) {
    var a = document.createElement('a');
    a.className = 'hm-city ' + cls;
    a.href = href;
    a.style.left = (anchor[0] / v.vbW * 100) + '%';
    a.style.top = (anchor[1] / v.vbH * 100) + '%';
    var label = document.createElement('span');
    label.className = 'hm-city-label';
    label.setAttribute('data-en', en);
    label.setAttribute('data-ja', ja);
    label.textContent = en;
    a.appendChild(label);
    return a;
  }

  // Marker = small ring + centre dot at the true coordinate; a fine leader
  // line runs out to an offset anchor, which is where the label actually
  // sits — closer to an annotated report figure than a map pin.
  function makeMark(gRoot, pt, anchor, cls) {
    var g = el(SVGNS, 'g', 'hm-mark ' + cls);
    var leader = el(SVGNS, 'line', 'hm-leader');
    leader.setAttribute('x1', pt[0]); leader.setAttribute('y1', pt[1]);
    leader.setAttribute('x2', anchor[0]); leader.setAttribute('y2', anchor[1]);
    var ring = el(SVGNS, 'circle', 'hm-marker-ring');
    ring.setAttribute('cx', pt[0]); ring.setAttribute('cy', pt[1]); ring.setAttribute('r', 2.6);
    var dot = el(SVGNS, 'circle', 'hm-marker-dot');
    dot.setAttribute('cx', pt[0]); dot.setAttribute('cy', pt[1]); dot.setAttribute('r', 1.1);
    g.appendChild(leader); g.appendChild(ring); g.appendChild(dot);
    gRoot.appendChild(g);
    return g;
  }

  function setupReveal(mount) {
    if (mount.classList.contains('hm-map-in')) return;
    if (!('IntersectionObserver' in window)) { mount.classList.add('hm-map-in'); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { mount.classList.add('hm-map-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -15% 0px', threshold: 0.35 });
    io.observe(mount);
  }

  // Very subtle desktop-only parallax between the base map and the markers/
  // labels — a few px max, gated behind reduced-motion and a fine-pointer
  // check so touch devices never see it.
  function setupParallax(mount, gMarkers, labelWrap) {
    if (REDUCED) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    // A breakpoint re-render calls this again; drop the previous listener so
    // repeated crossings can't accumulate them.
    if (parallaxScroll) window.removeEventListener('scroll', parallaxScroll);
    var ticking = false;
    function apply() {
      var r = mount.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var center = r.top + r.height / 2 - vh / 2;
      var t = Math.max(-1, Math.min(1, -center / (vh / 2 + r.height / 2)));
      var y = (t * 5).toFixed(2);
      gMarkers.style.transform = 'translateY(' + y + 'px)';
      labelWrap.style.transform = 'translateY(' + y + 'px)';
      ticking = false;
    }
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(apply);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    parallaxScroll = onScroll;
    apply();
  }

  var topologyCache = null;
  var renderedView = null;
  var parallaxScroll = null;

  function render(mount, countries) {
    var v = view();
    renderedView = v;

    var bounds = {
      type: 'Feature',
      geometry: { type: 'Polygon', coordinates: [[
        [v.lon[0], v.lat[0]], [v.lon[0], v.lat[1]],
        [v.lon[1], v.lat[1]], [v.lon[1], v.lat[0]], [v.lon[0], v.lat[0]]
      ]] }
    };
    var projection = d3.geoMercator().fitExtent([[v.pad, v.pad], [v.vbW - v.pad, v.vbH - v.pad]], bounds);
    var path = d3.geoPath(projection);

    var svg = el(SVGNS, 'svg', 'hm-map-svg');
    svg.setAttribute('viewBox', '0 0 ' + v.vbW + ' ' + v.vbH);
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');

    var gContext = el(SVGNS, 'g', 'hm-map-context');
    var gHi = el(SVGNS, 'g', 'hm-map-hi-g');
    var gMarkers = el(SVGNS, 'g', 'hm-markers');

    countries.filter(function (f) { return EUROPE_SET[String(f.id)]; }).forEach(function (f) {
      var d = path(f);
      if (!d) return;
      var id = String(f.id);
      var p = el(SVGNS, 'path');
      p.setAttribute('d', d);
      if (id === UK_ID) { p.setAttribute('class', 'hm-map-country hm-map-hi hm-map-uk'); gHi.appendChild(p); }
      else if (id === NL_ID) { p.setAttribute('class', 'hm-map-country hm-map-hi hm-map-nl'); gHi.appendChild(p); }
      else { p.setAttribute('class', 'hm-map-country'); gContext.appendChild(p); }
    });

    var lp = projection(LONDON);
    var ap = projection(AMSTERDAM);
    var lAnchor = [lp[0] + v.london[0], lp[1] + v.london[1]];
    var aAnchor = [ap[0] + v.amsterdam[0], ap[1] + v.amsterdam[1]];
    makeMark(gMarkers, lp, lAnchor, 'hm-mark-london');
    makeMark(gMarkers, ap, aAnchor, 'hm-mark-amsterdam');

    svg.appendChild(gContext);
    svg.appendChild(gHi);
    svg.appendChild(gMarkers);
    mount.innerHTML = '';
    mount.appendChild(svg);

    var labelWrap = document.createElement('div');
    labelWrap.className = 'hm-map-labels';
    labelWrap.appendChild(makeCity(lAnchor, v, 'London', 'ロンドン', 'hm-city-london', 'about.html#markets'));
    labelWrap.appendChild(makeCity(aAnchor, v, 'Amsterdam', 'アムステルダム', 'hm-city-amsterdam', 'about.html#markets'));
    mount.appendChild(labelWrap);

    if (window.ReiwaI18n) window.ReiwaI18n.apply(window.ReiwaI18n.getLang());

    setupReveal(mount);
    setupParallax(mount, gMarkers, labelWrap);
  }

  function build() {
    var mount = document.querySelector('.hm-map-wrap');
    if (!mount || typeof d3 === 'undefined' || typeof topojson === 'undefined') return;

    function draw(topology) {
      topologyCache = topology;
      var countries = topojson.feature(topology, topology.objects.countries).features;
      render(mount, countries);
      // Re-render only when the breakpoint is actually crossed — never on
      // every resize tick, and never on mobile URL-bar height changes.
      var mq = window.matchMedia(MOBILE_MQ);
      var onChange = function () {
        if (view() !== renderedView) render(mount, countries);
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }

    if (topologyCache) { draw(topologyCache); return; }
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-50m.json')
      .then(function (r) { return r.json(); })
      .then(draw)
      .catch(function (err) { if (window.console) console.warn('Map data unavailable:', err); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

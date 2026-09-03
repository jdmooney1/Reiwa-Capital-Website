(function () {
  var SVGNS = 'http://www.w3.org/2000/svg';
  var FOCUS = { uk: '826', nl: '528' };
  var CITIES = { uk: { key: 'uk', coord: [-0.1278, 51.5074], label: 'London' }, nl: { key: 'nl', coord: [4.9041, 52.3676], label: 'Amsterdam' } };
  // Tight Western Europe window: British Isles through the Low Countries,
  // northern France and western Germany — enough to orient, no empty
  // southern/eastern canvas.
  var BBOX = { lonMin: -10.6, lonMax: 8.8, latMin: 46.4, latMax: 58.9 };
  var DESKTOP = { vbW: 720, vbH: 465, pad: 22 };
  var MOBILE = { vbW: 620, vbH: 496, pad: 20 };
  var MOBILE_MQ = '(max-width: 700px)';

  function view() { return window.matchMedia(MOBILE_MQ).matches ? MOBILE : DESKTOP; }

  function el(ns, tag, cls) {
    var n = document.createElementNS(ns, tag);
    if (cls) n.setAttribute('class', cls);
    return n;
  }

  function windowFeature(v) {
    var cLon = (BBOX.lonMin + BBOX.lonMax) / 2, cLat = (BBOX.latMin + BBOX.latMax) / 2;
    var lonSpan = BBOX.lonMax - BBOX.lonMin, latSpan = BBOX.latMax - BBOX.latMin;
    var kx = Math.cos(cLat * Math.PI / 180) || 0.5;
    var effW = lonSpan * kx, effH = latSpan;
    var frameAspect = (v.vbW - 2 * v.pad) / (v.vbH - 2 * v.pad);
    if (effW / effH < frameAspect) lonSpan = (effH * frameAspect) / kx;
    else latSpan = effW / frameAspect;
    var lo = cLon - lonSpan / 2, hi = cLon + lonSpan / 2;
    var la0 = cLat - latSpan / 2, la1 = cLat + latSpan / 2;
    return { type: 'Feature', geometry: { type: 'Polygon', coordinates: [[
      [lo, la0], [lo, la1], [hi, la1], [hi, la0], [lo, la0]
    ]] } };
  }

  function render(mount, countries, v) {
    var projection = d3.geoMercator().fitExtent([[v.pad, v.pad], [v.vbW - v.pad, v.vbH - v.pad]], windowFeature(v));
    var path = d3.geoPath(projection);

    var svg = el(SVGNS, 'svg', 'hm-map-svg');
    svg.setAttribute('viewBox', '0 0 ' + v.vbW + ' ' + v.vbH);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');

    var gContext = el(SVGNS, 'g');
    var gFocus = el(SVGNS, 'g');
    countries.forEach(function (f) {
      var id = String(f.id);
      var d = path(f);
      if (!d) return;
      var isUK = id === FOCUS.uk, isNL = id === FOCUS.nl;
      var p = el(SVGNS, 'path', isUK || isNL ? 'hm-e-focus' : 'hm-e-context');
      p.setAttribute('d', d);
      if (isUK) { p.setAttribute('data-market', 'uk'); gFocus.appendChild(p); }
      else if (isNL) { p.setAttribute('data-market', 'nl'); gFocus.appendChild(p); }
      else gContext.appendChild(p);
    });

    var gCities = el(SVGNS, 'g');
    Object.keys(CITIES).forEach(function (key) {
      var c = CITIES[key];
      var pt = projection(c.coord);
      var g = el(SVGNS, 'g', 'hm-e-city');
      g.setAttribute('data-market', key);
      var ring = el(SVGNS, 'circle', 'hm-e-ring');
      ring.setAttribute('cx', pt[0]); ring.setAttribute('cy', pt[1]); ring.setAttribute('r', 3.4);
      var dot = el(SVGNS, 'circle', 'hm-e-dot');
      dot.setAttribute('cx', pt[0]); dot.setAttribute('cy', pt[1]); dot.setAttribute('r', 1.4);
      var label = el(SVGNS, 'text', 'hm-e-label');
      label.setAttribute('x', pt[0] + 9); label.setAttribute('y', pt[1] + 3.5);
      label.textContent = c.label;
      g.appendChild(ring); g.appendChild(dot); g.appendChild(label);
      gCities.appendChild(g);
    });

    svg.appendChild(gContext);
    svg.appendChild(gFocus);
    svg.appendChild(gCities);
    mount.innerHTML = '';
    mount.appendChild(svg);
  }

  var topologyCache = null;

  function build() {
    var mount = document.querySelector('.hm-map-frame[data-mount="europe"]');
    if (!mount || typeof d3 === 'undefined' || typeof topojson === 'undefined') return;

    function drawAll(countries) {
      var v = view();
      render(mount, countries, v);
      if (window.ReiwaI18n) window.ReiwaI18n.apply(window.ReiwaI18n.getLang());
      var mq = window.matchMedia(MOBILE_MQ);
      var onChange = function () { if (view() !== v) drawAll(countries); };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }

    if (topologyCache) { drawAll(topojson.feature(topologyCache, topologyCache.objects.countries).features); return; }
    fetch((window.__resources && window.__resources.geo) || 'assets/geo/countries-50m.json')
      .then(function (r) { return r.json(); })
      .then(function (topology) {
        topologyCache = topology;
        drawAll(topojson.feature(topology, topology.objects.countries).features);
      })
      .catch(function (err) { if (window.console) console.warn('Map data unavailable:', err); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

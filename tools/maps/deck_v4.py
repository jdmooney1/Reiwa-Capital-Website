"""Reiwa Capital focus maps - v4 (November 2026): area set and tiers aligned with the investor deck
("European Real Estate Investment - Structural Overview for Japanese Investors", March 2026, pages 9 and 11).

What changes against v3 (tools/maps/build.py):
  London     Core: Marylebone, Fitzrovia, Soho, Mayfair, St James's, Covent Garden (each drawn and labelled on its own, as in
             the deck), City of London, Westminster (promoted from selective). Selective: Bloomsbury and Midtown (Holborn)
             drawn apart again, plus Farringdon, Clerkenwell, Shoreditch & Aldgate and Southbank. Kensington & Chelsea is
             dropped. The frame is re-cropped to the deck's extent (Edgware Road to Aldgate, Euston Road to Kennington).
  Amsterdam  Core: Jordaan (now with Haarlemmerbuurt, to the IJ), Canal Belt, Oud-Zuid (unchanged), Zuidas. Selective: Oud-West, Weesperbuurt/Plantage, De Pijp, Oost, Rivierenbuurt, plus Centrum,
             West, Sloterdijk, Noord, Overamstel and Buitenveldert. The frame is unchanged, so the outer areas are cut at its
             edge as they are in the deck.

The v3 areas are reused exactly as published (assets/maps/*-focus.js at BASE). New areas are built from the pinned v3
boundary inputs (ONS wards December 2013, Gemeente Amsterdam buurtcombinaties via blackmad/neighborhoods; hashes in
sources.json), cut back where they meet a v3 area, with seams up to SEAM m closed and open water and parks of 4 ha or more
removed using the published base map. The base map itself (Overture) is not rebuilt: the v3 base layers are reused, and for
London re-scaled into the new crop. A full rebuild with build.py needs the Overture extracts; see README.md.

  MAP_DATA=/path/to/boundaries python3 tools/maps/deck_v4.py
"""
import json, os, re, subprocess, sys, hashlib, math
sys.path.insert(0, os.path.dirname(__file__))
from shapely.geometry import shape, Polygon, box, mapping
from shapely.ops import unary_union, transform
from shapely.validation import make_valid
from pyproj import Transformer
import render as R

BASE = '21e639e'          # last v3 commit: the published v3 assets are read from here
SEAM = 25.0
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) + '/'
DATA = os.environ.get('MAP_DATA', '').rstrip('/') + '/'
MAPV = 10
# Labels scale with the map (container units, .ab-grp--sm): they are laid out for these widths, where they are set at LABEL_PX, and
# keep the same proportion at other widths (clamped in the CSS).
NOMINAL_W = {'wide': 585.0, 'tall': 360.0}
LABEL_PX = 10.0      # labels on the v4 maps are set smaller (.ab-grp--sm): there are 14 and 15 of them, as in the deck

def git(path): return subprocess.check_output(['git', '-C', REPO, 'show', f'{BASE}:{path}']).decode('utf-8')
def fixed(g):
    g = make_valid(g)
    if g.geom_type == 'GeometryCollection': g = unary_union([p for p in g.geoms if p.geom_type in ('Polygon', 'MultiPolygon')])
    return g
def polys(g): return [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
def parse(d):
    rings = []
    for sub in re.findall(r'M[^M]*', d):
        pts = [tuple(map(float, p.split())) for p in re.split(r'[MLZ]', sub) if p.strip()]
        if len(pts) > 2: rings.append(fixed(Polygon(pts)))
    g = rings[0]
    for r in rings[1:]: g = g.symmetric_difference(r)
    return fixed(g)
def pinned(fn):
    src = json.load(open(REPO + 'tools/maps/sources.json'))['files'][fn]
    assert hashlib.sha256(open(DATA + fn, 'rb').read()).hexdigest() == src['sha256'], f'{fn} differs from the pinned input'
    return json.load(open(DATA + fn))['features']

# ------------------------------------------------------------------ frames of the published v3 SVGs, recovered by fitting
# a published area to the same area projected from its source boundary (scale from the width, offsets from the west and north edges).
TR = {'london': Transformer.from_crs('EPSG:4326', 'EPSG:27700', always_xy=True).transform,
      'amsterdam': Transformer.from_crs('EPSG:4326', 'EPSG:28992', always_xy=True).transform}
def v3_frames(city, sub):
    js = git(f'assets/maps/{city}-focus.js'); arr = json.loads(re.search(r'SUBMARKETS = (\[.*?\]);', js, re.S).group(1))
    vb = json.loads(re.search(r'VIEWBOX = (\{.*?\});', js).group(1).replace('wide', '"wide"').replace('tall', '"tall"'))
    if city == 'london': ref = unary_union([fixed(transform(TR[city], shape(f['geometry']))) for f in pinned('wards_E09000001.json')]); rid = 'city'
    else: ref = [fixed(transform(TR[city], shape(f['geometry']))) for f in pinned('blackmad_amsterdam.geojson') if f['properties']['name'] == 'Jordaan'][0]; rid = 'jordaan'
    a = [x for x in arr if x['id'] == rid][0]; out = {}
    for v in ('wide', 'tall'):
        g = parse(a[v]); bx, bw = g.bounds, ref.bounds
        s = (bx[2] - bx[0]) / (bw[2] - bw[0]); x0 = bw[0] - bx[0] / s; y1 = bw[3] + bx[1] / s
        H = float(vb[v].split()[3]); out[v] = (x0, y1 - H / s, x0 + 1000 / s, y1)
    return arr, out
def to_m(g, fr):
    x0, y0, x1, y1 = fr; s = 1000 / (x1 - x0)
    return transform(lambda x, y, z=None: (x / s + x0, y1 - y / s), g)

# ------------------------------------------------------------------ masks (open water >= 2 ha, parks >= 4 ha) from the v3 base map
def masks(city, fr):
    svg = git(f'assets/maps/{city}-wide.svg'); out = []
    for col, minha in ((R.COL['water'], 2.0), (R.COL['park'], 4.0)):
        grp = re.search(r'<g fill="%s">(.*?)</g>' % col, svg).group(1)
        for d in re.findall(r'd="([^"]+)"', grp):
            for sub in re.findall(r'M[^M]*', d):
                pts = [tuple(map(float, p.split())) for p in re.split(r'[MLZ]', sub) if p.strip()]
                if len(pts) < 3: continue
                p = fixed(to_m(Polygon(pts), fr))
                if p.area / 1e4 >= minha: out.append(p)
    return fixed(unary_union(out))

def add(existing, raw, mask, clip=None):
    """A new area from source units: cut back to everything already placed, seams to it closed, water and parks removed."""
    raw = fixed(raw)
    if clip is not None: raw = raw.intersection(clip)
    taken = unary_union(list(existing.values()))
    g = fixed(raw.union(raw.buffer(SEAM, join_style=2).difference(taken).intersection(taken.buffer(SEAM, join_style=2))))
    g = fixed(g.difference(taken).difference(mask))
    g = fixed(g.buffer(-10, join_style=2).buffer(10, join_style=2))
    return fixed(unary_union([p for p in polys(g) if p.area >= 15000]))

# ------------------------------------------------------------------ area definitions
LONDON = [  # key, members (v3 ids or new), cls, en, ja
    ('marylebone', 'core', 'Marylebone', 'マリルボーン'), ('fitzrovia', 'core', 'Fitzrovia', 'フィッツロヴィア'), ('soho', 'core', 'Soho', 'ソーホー'),
    ('mayfair', 'core', 'Mayfair', 'メイフェア'), ('st-jamess', 'core', 'St James’s', 'セント・<br>ジェームズ'), ('covent-garden', 'core', 'Covent<br>Garden', 'コヴェント・<br>ガーデン'),
    ('westminster', 'core', 'Westminster', 'ウェストミンスター'), ('city', 'core', 'City of<br>London', 'シティ・オブ・<br>ロンドン'),
    ('bloomsbury', 'sel', 'Bloomsbury', 'ブルームズベリー'), ('holborn', 'sel', 'Midtown', 'ミッドタウン'), ('farringdon', 'sel', 'Farringdon', 'ファリンドン'),
    ('clerkenwell', 'sel', 'Clerkenwell', 'クラーケンウェル'), ('shoreditch', 'sel', 'Shoreditch &amp;<br>Aldgate', 'ショーディッチ・<br>オールドゲート'), ('southbank', 'sel', 'Southbank', 'サウスバンク')]
AMSTERDAM = [
    ('jordaan', 'core', 'Jordaan', 'ヨルダーン'),
    ('canal-belt', 'core', 'Canal Belt', 'カナルベルト'),
    ('museumkwartier', 'core', 'Museum-<br>kwartier', 'ミュージアム<br>地区'), ('oud-zuid', 'core', 'Oud-Zuid', 'アウド・<br>ザウト'), ('zuidas', 'core', 'Zuidas', 'ザイダス'),
    ('centrum', 'sel', 'Centrum', 'セントルム'), ('oud-west', 'sel', 'Oud-West', 'アウド・<br>ウェスト'), ('west', 'sel', 'West', 'ウェスト'), ('sloterdijk', 'sel', 'Sloterdijk', 'スローテルダイク'),
    ('noord', 'sel', 'Noord', 'ノールト'), ('plantage', 'sel', 'Plantage', 'プランタージュ'), ('de-pijp', 'sel', 'De Pijp', 'デ・パイプ'),
    ('oost', 'sel', 'Oost', 'オースト'), ('rivierenbuurt', 'sel', 'Rivierenbuurt', 'リヴィエレンブールト'), ('overamstel', 'sel', 'Overamstel', 'オーフェルアムステル'),
    ('buitenveldert', 'sel', 'Buitenveldert', 'バウテンフェルデルト')]

# label placements kept from the published v3 Amsterdam map (same frame): the Jordaan and Canal Belt labels sit beside their
# narrow areas rather than across Centrum, and the v3 fixed placements still apply
FIXED = {}
DECK = {'core': dict(fill='#271430', op=0.86, edge='#F5CAE0', edge_op=0.55, w=0.8),
        'sel': dict(fill='#F5CAE0', op=0.72, edge='#271430', edge_op=0.75, w=1.0)}
ASPECT = {'london': {'wide': 1.2, 'tall': 0.80}, 'amsterdam': {'wide': 1.2, 'tall': 0.80}}   # London's wide frame now matches Amsterdam's (CSS: .am-market .am-map 1.2 from 901px)

def ll(*pts):
    """A line given as (lat, lon) points, in British National Grid metres."""
    from shapely.geometry import LineString
    return LineString([TR['london'](lon, lat) for lat, lon in pts])
def side_of(line, keep_pt, far=20000):
    """The half-plane-like region on keep_pt's side of an open line, closed far away from the frame."""
    from shapely.geometry import Point
    from shapely.ops import split
    region = Point(keep_pt).buffer(far)
    ext = line
    (x0, y0), (x1, y1) = ext.coords[0], ext.coords[-1]
    a = ext.coords[1]; b = ext.coords[-2]
    def out(p, q):      # extend the end p away from q
        dx, dy = p[0] - q[0], p[1] - q[1]; n = math.hypot(dx, dy) or 1
        return (p[0] + dx / n * far * 2, p[1] + dy / n * far * 2)
    from shapely.geometry import LineString
    long = LineString([out((x0, y0), a)] + list(ext.coords) + [out((x1, y1), b)])
    parts = split(region, long)
    return [g for g in parts.geoms if g.contains(Point(keep_pt))][0]

def london():
    arr, fr = v3_frames('london', None); W = fr['wide']
    areas = {a['id']: fixed(to_m(parse(a['wide']), W)) for a in arr if a['id'] != 'kensington-chelsea'}
    mask = masks('london', W)
    def wards(code, names): return unary_union([fixed(transform(TR['london'], shape(f['geometry']))) for f in pinned(f'wards_{code}.json') if f['properties']['WD13NM'] in names])
    # Westminster as drawn in the deck: Victoria, Whitehall and east Pimlico down to Vauxhall Bridge. Belgravia and west Pimlico (west of
    # Grosvenor Place, Buckingham Palace Road and a line to Vauxhall Bridge) are left out.
    westline = ll((51.5026, -0.1512), (51.4975, -0.1467), (51.4935, -0.1468), (51.4893, -0.1372), (51.4866, -0.1290))
    areas['westminster'] = fixed(areas['westminster'].intersection(side_of(westline, TR['london'](-0.1276, 51.4994))))
    areas['westminster'] = fixed(unary_union([p for p in polys(areas['westminster']) if p.area >= 15000]))
    # Midtown in the deck runs up to Euston Road between Bloomsbury and Farringdon: the King's Cross ward south of Euston Road joins it
    kx = wards('E09000007', ["King's Cross"]).intersection(side_of(ll((51.5265, -0.1330), (51.5290, -0.1225), (51.5300, -0.1170)), TR['london'](-0.1180, 51.5240)))
    hb = fixed(unary_union([areas['holborn'], add({k: g for k, g in areas.items() if k != 'holborn'}, kx, mask)]).buffer(12, join_style=2).buffer(-12, join_style=2))
    hb = fixed(hb.difference(unary_union([g for k, g in areas.items() if k != 'holborn'])))
    areas['holborn'] = fixed(unary_union([Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= 10000]) for p in polys(hb) if p.area >= 15000]))
    north = box(0, 0, 10**7, 182800)        # the deck stops Shoreditch & Aldgate at Old Street / Bethnal Green Road
    areas['farringdon'] = add(areas, wards('E09000019', ['Clerkenwell']), mask)
    areas['clerkenwell'] = add(areas, wards('E09000019', ['Bunhill']), mask)
    areas['shoreditch'] = add(areas, unary_union([wards('E09000012', ['Hoxton', 'Haggerston']), wards('E09000030', ['Spitalfields and Banglatown', 'Weavers', 'Whitechapel', "St Katharine's and Wapping"])]), mask, north)
    # Southbank stops where the deck's does: Kennington Lane, Elephant & Castle and Great Dover Street
    south = side_of(ll((51.4862, -0.1240), (51.4895, -0.1100), (51.4945, -0.1003), (51.4975, -0.0905), (51.4990, -0.0800)), TR['london'](-0.1100, 51.5040))
    areas['southbank'] = add(areas, unary_union([wards('E09000022', ["Bishop's", "Prince's"]), wards('E09000028', ['Cathedrals', 'Chaucer'])]), mask, south)
    areas = fill_gaps(areas, ['farringdon', 'clerkenwell', 'shoreditch', 'southbank', 'holborn'], mask)
    areas = no_pinholes(seal(areas, ['marylebone', 'fitzrovia', 'soho', 'mayfair', 'st-jamess', 'covent-garden', 'westminster', 'city', 'bloomsbury', 'holborn'], mask))
    # crop: the deck's extent, centred on the areas, inside each published v3 frame (its base map is reused)
    core = unary_union([areas[k] for k in areas if k != 'shoreditch']); bx = core.bounds
    frames = {}
    for v, asp in (('wide', ASPECT['london']['wide']), ('tall', 0.80)):
        x0, y0, x1, y1 = fr[v]; nx0 = bx[0] - 400; nx1 = x1 - 5; h = (nx1 - nx0) / asp; cy = (bx[1] + bx[3]) / 2
        ny0 = max(y0 + 5, min(cy - h / 2, y1 - 5 - h)); frames[v] = (nx0, ny0, nx1, ny0 + h)
    return areas, LONDON, fr, frames

def amsterdam():
    arr, fr = v3_frames('amsterdam', None); W = fr['wide']
    areas = {a['id']: fixed(to_m(parse(a['wide']), W)) for a in arr}
    mask = masks('amsterdam', W)
    bc = {f['properties']['name']: fixed(transform(TR['amsterdam'], shape(f['geometry']))) for f in pinned('blackmad_amsterdam.geojson')}
    U = lambda *n: unary_union([bc[x] for x in n])
    others = lambda k: {kk: g for kk, g in areas.items() if kk != k}
    # Core, as the deck draws it: the Jordaan to the IJ (with Haarlemmerbuurt); the canal belt as one shape, down to the Singelgracht
    # (with De Weteringschans, the strip the v3 map left out); Museumkwartier apart from the rest of Oud-Zuid, with Duivelseiland, so it
    # meets De Pijp; Oud-Zuid west to the Schinkel (Hoofddorppleinbuurt, Schinkelbuurt) and down to Zuidas
    areas['jordaan'] = fixed(unary_union([areas['jordaan'], add(areas, U('Haarlemmerbuurt'), mask)]).buffer(10, join_style=2).buffer(-10, join_style=2))     # to the IJ, as in the deck
    areas['canal-belt'] = fixed(unary_union([areas['canal-belt'], add(others('canal-belt'), U('De Weteringschans'), mask)]).buffer(10, join_style=2).buffer(-10, join_style=2))
    oz = areas.pop('oud-zuid')
    west_oz = add({k: g for k, g in areas.items()}, U('Hoofddorppleinbuurt', 'Schinkelbuurt'), mask)
    oz = fixed(unary_union([oz, west_oz]).buffer(20, join_style=2).buffer(-20, join_style=2).difference(unary_union(list(areas.values()))).difference(mask))
    areas['museumkwartier'] = fixed(oz.intersection(bc['Museumkwartier'].buffer(25)).difference(unary_union([g for n, g in bc.items() if n != 'Museumkwartier'])))
    areas['oud-zuid'] = fixed(oz.difference(areas['museumkwartier']))
    areas['museumkwartier'] = fixed(unary_union([areas['museumkwartier'], add(others('museumkwartier'), U('Duivelseiland'), mask)]))
    # the band between Oud-Zuid and Zuidas (parts of Stadionbuurt, Apollobuurt and Station-Zuid): the deck draws the two touching
    pair = fixed(unary_union([areas['oud-zuid'], areas['zuidas']]).buffer(150, join_style=2).buffer(-150, join_style=2))
    band = fixed(pair.difference(unary_union(list(areas.values()))).difference(mask))
    sz = bc['Station-Zuid WTC en omgeving']
    for p in polys(band):
        if p.area < 5000 or areas['oud-zuid'].distance(p) > 20 or areas['zuidas'].distance(p) > 20: continue
        areas['zuidas'] = fixed(unary_union([areas['zuidas'], p.intersection(sz)]))
        areas['oud-zuid'] = fixed(unary_union([areas['oud-zuid'], p.difference(sz)]))
    for k in ('canal-belt', 'museumkwartier', 'oud-zuid', 'zuidas'):
        areas[k] = fixed(unary_union([p for p in polys(areas[k]) if p.area >= 15000]))
    # Plantage as the deck draws it: Nieuwmarkt/Lastage, Weesperbuurt/Plantage and the Eastern Islands, up to the IJ
    areas['plantage'] = fixed(unary_union([areas['plantage'], add({k: g for k, g in areas.items() if k != 'plantage'}, U('Nieuwmarkt/Lastage', 'Oostelijke Eilanden/Kadijken'), mask)]))
    areas['centrum'] = add(areas, U('Burgwallen-Nieuwe Zijde', 'Burgwallen-Oude Zijde'), mask)
    areas['sloterdijk'] = add(areas, U('Sloterdijk', 'Houthavens', 'Spaarndammer- en Zeeheldenbuurt'), mask)
    areas['west'] = add(areas, U('Frederik Hendrikbuurt', 'Staatsliedenbuurt', 'Centrale Markt', 'Van Galenbuurt', 'Landlust', 'De Kolenkit', 'Erasmuspark', 'Hoofdweg en omgeving', 'Westindische buurt', 'De Krommert'), mask)
    areas['noord'] = add(areas, U('Volewijck', 'Ijplein/Vogelbuurt', 'Buiksloterham', 'Nieuwendammerham'), mask)
    areas['overamstel'] = add(areas, U('De Omval'), mask)
    areas['buitenveldert'] = add(areas, U('Buitenveldert-West', 'Buitenveldert-Oost'), mask)
    areas = fill_gaps(areas, ['centrum', 'plantage', 'west', 'sloterdijk', 'noord', 'overamstel', 'buitenveldert'], mask)
    # built-up ground left between the core areas, given back to the area whose source unit it lies in: 2 ha of Museumkwartier along the
    # Boerenwetering, and the Station-Zuid and Apollobuurt ground by Beatrixpark (the deck runs Zuidas east to Rivierenbuurt). The park stays open.
    for k, unit in (('museumkwartier', 'Museumkwartier'), ('zuidas', 'Station-Zuid WTC en omgeving'), ('oud-zuid', 'Apollobuurt')):
        free = fixed(bc[unit].difference(unary_union(list(areas.values()))).difference(mask))
        near = [p for p in polys(free) if p.area >= 2000 and areas[k].distance(p) < 25]
        if near:
            joined = fixed(unary_union([areas[k]] + [p.buffer(12, join_style=2) for p in near]).buffer(-12, join_style=2))
            areas[k] = fixed(unary_union([joined, areas[k]] + near).difference(unary_union([g for kk, g in areas.items() if kk != k])).difference(mask.difference(areas[k])))
    areas = seal(areas, ['jordaan', 'canal-belt', 'museumkwartier', 'oud-zuid', 'zuidas', 'de-pijp', 'oud-west'], mask)
    areas = seal(areas, ['plantage', 'oost', 'centrum'], mask, r=80)        # a 0.7 ha notch on the Plantage / Oost edge
    areas = no_pinholes(areas)
    return areas, AMSTERDAM, fr, dict(fr)

# ------------------------------------------------------------------ drawing
def rescale_base(city, v, old, new):
    """The v3 base layers (background, parks, water, rail, roads and, for Amsterdam, the canal lines) moved into the new frame."""
    svg = git(f'assets/maps/{city}-{v}.svg').split('\n')
    so = 1000 / (old[2] - old[0]); sn = 1000 / (new[2] - new[0])
    def pt(m):
        X = float(m.group(1)) / so + old[0]; Y = old[3] - float(m.group(2)) / so
        return f'{(X - new[0]) * sn:.1f} {(new[3] - Y) * sn:.1f}'.replace('.0 ', ' ').removesuffix('.0')
    same = old == new
    fix = (lambda l: l) if same else (lambda l: re.sub(r'd="([^"]*)"', lambda m: 'd="' + re.sub(r'(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?)', pt, m.group(1)) + '"', l))
    base = [fix(l) for l in svg if l.startswith('<g ') and 'stroke-width="1.7"' not in l]
    canals = [fix(l) for l in svg if l.startswith('<g ') and 'stroke-width="1.7"' in l]
    return base, canals

def draw(city, v, fr, groups, meta, labels, old):
    F = R.Frame(fr); T = F.T; W, H = F.W, F.H
    base, canals = rescale_base(city, v, old, fr)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.1f}" preserveAspectRatio="xMidYMid slice" role="presentation">',
         R.HEADER[city].replace('Built by tools/maps/build.py.', 'Built by tools/maps/deck_v4.py (v4, areas as in the March 2026 investor deck).'),
         f'<rect width="{W:.0f}" height="{H:.1f}" fill="{R.COL["land"]}"/>'] + base
    # Deck colour system: core in Sumire purple, selective in Sakura pink, each neighbourhood outlined. The street grid is re-drawn faintly
    # over the core so the dark areas still read as places, and the canals stay on top.
    core_u = fixed(unary_union([groups[k] for k, c, *_ in meta if c == 'core']))
    o.append(f'<defs><clipPath id="core-clip"><path d="{R.d_path(T(core_u), 1)}"/></clipPath></defs>')
    for k, cls, *_ in meta:
        f = DECK[cls]; o.append(f'<path d="{R.d_path(T(groups[k]), 1)}" fill="{f["fill"]}" fill-opacity="{f["op"]}"/>')
    roads = [l for l in base if 'stroke-linecap="round"' in l]
    o.append('<g clip-path="url(#core-clip)" opacity="0.2">' + ''.join(re.sub(r'stroke="#[0-9A-Fa-f]{6}"', 'stroke="#FCFAF1"', l, count=1) for l in roads) + '</g>')
    o += canals
    for k, cls, *_ in meta:          # neighbourhood edges: pale inside the core, plum between selective areas
        f = DECK[cls]; d = R.d_path(T(groups[k]), 1)
        o.append(f'<path d="{d}" fill="none" stroke="{f["edge"]}" stroke-opacity="{f["edge_op"]}" stroke-width="{f["w"]}" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
    o.append(f'<path d="{R.d_path(T(core_u), 1)}" fill="none" stroke="{DECK["core"]["fill"]}" stroke-width="1.6" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
    k_ = W / R.NOMINAL_W[v]
    for k, *_ in meta:
        L = labels[k]
        if L['ax'] is None: continue
        ax, ay = L['ax'] / 100 * W, L['ay'] / 100 * H; lx, ly = L['x'] / 100 * W, L['y'] / 100 * H
        dx, dy = lx - ax, ly - ay; dist = math.hypot(dx, dy) or 1; ex, ey = lx - dx / dist * 2 * k_, ly - dy / dist * 2 * k_
        o.append(f'<path d="M{ax:.1f} {ay:.1f}L{ex:.1f} {ey:.1f}" fill="none" stroke="#FCFAF1" stroke-opacity="0.9" stroke-width="3" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="M{ax:.1f} {ay:.1f}L{ex:.1f} {ey:.1f}" fill="none" stroke="{R.INK}" stroke-width="1" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="M{ax:.1f} {ay:.1f}h0.01" fill="none" stroke="#FCFAF1" stroke-width="7" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="M{ax:.1f} {ay:.1f}h0.01" fill="none" stroke="{R.INK}" stroke-width="5" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    o.append('</svg>')
    open(REPO + f'assets/maps/{city}-{v}.svg', 'w', encoding='utf-8').write('\n'.join(o))
    return F

def seal(areas, keys, mask, r=30.0):
    """Close slits narrower than 2r between and inside the given areas, where pieces built from different boundary sets do not quite meet.
    Each closed piece goes to the area it shares most edge with; parks and open water are never filled."""
    u = unary_union([areas[k] for k in keys])
    slits = fixed(u.buffer(r, join_style=2).buffer(-r, join_style=2).difference(unary_union(list(areas.values()))).difference(mask))
    for p in polys(slits):
        if p.area < 50: continue
        k = max(keys, key=lambda k: areas[k].buffer(1).intersection(p.boundary).length)
        areas[k] = fixed(unary_union([areas[k], p.buffer(0.3)]).difference(unary_union([g for kk, g in areas.items() if kk != k])))
    return areas

def no_pinholes(areas, min_m2=10000):
    """Holes under 1 ha (slivers left between source boundaries, drawn as a stray mark) are filled; parks and water stay open."""
    out = {}
    for k, g in areas.items():
        ps = [Polygon(p.exterior, [r for r in p.interiors if Polygon(r).area >= min_m2]) for p in polys(g)]
        out[k] = fixed(unary_union(ps).difference(unary_union([h for kk, h in areas.items() if kk != k])))
    return out

def fill_gaps(areas, new, mask, max_ha=30):
    u = fixed(unary_union(list(areas.values())).buffer(40, join_style=2).buffer(-40, join_style=2))     # gaps open to the outside by a street width count as enclosed
    for p in polys(u):
        for ring in p.interiors:
            for h in polys(fixed(fixed(Polygon(ring)).difference(mask).difference(unary_union(list(areas.values()))))):
              if h.area / 1e4 > max_ha or h.area < 500: continue
              best = max(new, key=lambda k: areas[k].buffer(1).intersection(h.boundary).length)
              if areas[best].buffer(1).intersection(h.boundary).length > 0: areas[best] = fixed(unary_union([areas[best], h.buffer(0.5)]).difference(unary_union([g for k, g in areas.items() if k != best])))
    return areas

def place_inside(city, v, fr, vis, meta):
    """Deck-style labels: each name sits on its own area, centred where it fits best, without leaders. A label may run past a narrow
    area's edge; it may not touch another label or leave the frame, and a dark-on-light selective label keeps off the dark core
    areas. Several placement orders are tried and the one with the lowest total cost is kept. An area with too little of itself in
    the frame to carry its name (Sloterdijk in the wide Amsterdam frame) is left unlabelled in that frame."""
    from shapely.geometry import Point
    from shapely.ops import polylabel
    Wpx = R.NOMINAL_W[v]; Hpx = Wpx / R.ASPECT[city][v]; sx = Wpx / (fr[2] - fr[0]); sy = Hpx / (fr[3] - fr[1])
    PG = {k: fixed(transform(lambda x, y, z=None: ((x - fr[0]) * sx, (fr[3] - y) * sy), g)) for k, g in vis.items()}
    core = {m[0] for m in meta if m[1] == 'core'}
    frame_box = box(4, 4, Wpx - 4, Hpx - 4)
    size = {k: [max(a, b) for a, b in zip(R.label_size(en, False), R.label_size(ja, True))] for k, c, en, ja in meta}
    cand = {}
    for k, cls, en, ja in meta:
        P = PG[k]; w, h = size[k]; cand[k] = []
        if P.is_empty or P.area < (0.15 if cls == 'core' else 0.5) * w * h: continue
        big = max(polys(P), key=lambda p: p.area); pole = polylabel(big, tolerance=0.5)
        dark_others = unary_union([PG[o] for o in core if o != k]) if core - {k} else Polygon()
        light_others = unary_union([PG[o] for o, c, *_ in meta if c != 'core' and o != k])
        minx, miny, maxx, maxy = big.bounds; x = minx
        while x <= maxx:
            y = miny
            while y <= maxy:
                if big.contains(Point(x, y)):
                    b = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
                    if frame_box.contains(b):
                        out = 1 - b.intersection(P).area / b.area
                        clash = b.intersection(dark_others if cls != 'core' else light_others).area / b.area
                        cost = 5 * out + (10 if cls != 'core' else 4) * clash + 0.5 * math.hypot(x - pole.x, y - pole.y) / (w + h)
                        cand[k].append((cost, x, y, b, out))
                y += 2
            x += 2
        cand[k].sort(key=lambda c: c[0]); cand[k] = cand[k][:400]
    def attempt(order):
        boxes = []; placed = {}; total = 0
        for k in order:
            if not cand[k]: placed[k] = None; continue
            pick = next((c for c in cand[k] if not any(c[3].buffer(3).intersects(o) for o in boxes)), None)
            if pick is None: pick = min(cand[k], key=lambda c: c[0] + 20 * sum(c[3].intersection(o).area for o in boxes) / c[3].area)
            boxes.append(pick[3]); placed[k] = pick; total += pick[0]
        return total, placed
    keys = [m[0] for m in meta]
    orders = [sorted(keys, key=lambda k: PG[k].area), sorted(keys, key=lambda k: -size[k][0] * size[k][1] / max(PG[k].area, 1)),
              sorted(keys, key=lambda k: (k not in core, PG[k].area)), sorted(keys, key=lambda k: (k in core, PG[k].area))]
    total, best = min((attempt(o) for o in orders), key=lambda t: t[0])
    out = {}
    for k in keys:
        if best[k] is None: out[k] = dict(x=-100, y=-100, side='c', ax=None, ay=None, inside=False, hidden=True); continue
        _, x, y, b, o = best[k]
        out[k] = dict(x=round(x / Wpx * 100, 2), y=round(y / Hpx * 100, 2), side='c', ax=None, ay=None, inside=o < 0.4)
    print(f'  {city} {v}: label cost {total:.2f}', [k for k in keys if best[k] is None] or '')
    return out

def run():
    res = {}
    R.ASPECT.update(ASPECT); R.NOMINAL_W.update(NOMINAL_W)
    for city, fn in (('london', london), ('amsterdam', amsterdam)):
        areas, meta, old, new = fn(); res[city] = {'labels': {}, 'frames': {}, 'meta': meta}
        fx = {}
        for v in ('wide', 'tall'):
            fb = box(*new[v]); groups = {k: fixed(areas[k].intersection(fb.buffer(40))) for k, *_ in meta}
            vis = {k: fixed(areas[k].intersection(fb)) for k, *_ in meta}
            m = [dict(key=k, cls=c, en=en, ja=ja, avoid_core=True, **({'fixed': FIXED[k]} if k in FIXED else {})) for k, c, en, ja in meta]
            R.FONT = LABEL_PX
            labels = place_inside(city, v, new[v], vis, meta)
            draw(city, v, new[v], groups, meta, labels, old[v]); res[city]['labels'][v] = labels
            res[city]['frames'][v] = new[v]; fx[v] = new[v]
        # focus.js: every area as path data in both frames
        items = []
        for k, c, en, ja in meta:
            item = dict(id=k, name=re.sub('<br>', ' ', en).replace('&amp;', '&').replace(' /', '/'), ja=re.sub('<br>', '', ja), group=k, core=c == 'core')
            for v in ('wide', 'tall'):
                F = R.Frame(fx[v]); g = F.T(areas[k])
                item[v] = ''.join('M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in p.exterior.coords) + 'Z' + ''.join('M' + 'L'.join(f'{x:.0f} {y:.0f}' for x, y in i.coords) + 'Z' for i in p.interiors) for p in polys(g))
            items.append(item)
        vb = {v: f'0 0 1000 {R.Frame(fx[v]).H:.1f}' for v in ('wide', 'tall')}
        open(REPO + f'assets/maps/{city}-focus.js', 'w', encoding='utf-8').write(
            f'export const VIEWBOX = {{ wide: "{vb["wide"]}", tall: "{vb["tall"]}" }};\n// Every focus area as path data, in the same frames and projection as {city}-wide.svg and {city}-tall.svg (generated by tools/maps/deck_v4.py).\n// "core" is the classification: true = core focus, false = selective focus.\nexport const SUBMARKETS = {json.dumps(items, ensure_ascii=False, separators=(",", ":"))};\n')
        res[city]['ha'] = {k: round(areas[k].area / 1e4, 1) for k, *_ in meta}
        print(city, res[city]['ha'])
    return res

if __name__ == '__main__':
    res = run()
    import pages_v4; pages_v4.patch_all(REPO, res)

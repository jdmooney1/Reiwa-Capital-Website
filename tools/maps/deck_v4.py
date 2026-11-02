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
LABEL_PX = 10.5      # labels on the v4 maps are set smaller (.ab-grp--sm): there are 14 and 15 of them, as in the deck

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
    ('jordaan', 'core', 'Jordaan', 'ヨルダーン'), ('canal-belt', 'core', 'Canal Belt', 'カナルベルト'), ('oud-zuid', 'core', 'Oud-Zuid', 'アウド・ザウト'), ('zuidas', 'core', 'Zuidas', 'ザイダス'),
    ('centrum', 'sel', 'Centrum', 'セントルム'), ('oud-west', 'sel', 'Oud-West', 'アウド・ウェスト'), ('west', 'sel', 'West', 'ウェスト'), ('sloterdijk', 'sel', 'Sloterdijk', 'スローテルダイク'),
    ('noord', 'sel', 'Noord', 'ノールト'), ('plantage', 'sel', 'Weesperbuurt /<br>Plantage', 'ウェースペルブールト・<br>プランタージュ'), ('de-pijp', 'sel', 'De Pijp', 'デ・パイプ'),
    ('oost', 'sel', 'Oost', 'オースト'), ('rivierenbuurt', 'sel', 'Rivierenbuurt', 'リヴィエレンブールト'), ('overamstel', 'sel', 'Overamstel', 'オーフェルアムステル'),
    ('buitenveldert', 'sel', 'Buitenveldert', 'バウテンフェルデルト')]

# label placements kept from the published v3 Amsterdam map (same frame): the Jordaan and Canal Belt labels sit beside their
# narrow areas rather than across Centrum, and the v3 fixed placements still apply
FIXED = {'jordaan': {'wide': dict(x=31.83, y=22.02, side='l'), 'tall': dict(x=30.43, y=30.15, side='l')},
         'canal-belt': {'wide': dict(x=54.61, y=31.96, side='t'), 'tall': dict(x=54.54, y=36.9, side='t')},
         'oud-west': {'tall': dict(x=20.86, y=41.88, side='b')},
         'de-pijp': {'tall': dict(x=55.01, y=59.05, side='r'), 'wide': dict(x=53.22, y=61.07, side='c')}}

def london():
    arr, fr = v3_frames('london', None); W = fr['wide']
    areas = {a['id']: fixed(to_m(parse(a['wide']), W)) for a in arr if a['id'] != 'kensington-chelsea'}
    mask = masks('london', W)
    def wards(code, names): return unary_union([fixed(transform(TR['london'], shape(f['geometry']))) for f in pinned(f'wards_{code}.json') if f['properties']['WD13NM'] in names])
    north = box(0, 0, 10**7, 182800)        # the deck stops Shoreditch & Aldgate at Old Street / Bethnal Green Road
    areas['farringdon'] = add(areas, wards('E09000019', ['Clerkenwell']), mask)
    areas['clerkenwell'] = add(areas, wards('E09000019', ['Bunhill']), mask)
    areas['shoreditch'] = add(areas, unary_union([wards('E09000012', ['Hoxton', 'Haggerston']), wards('E09000030', ['Spitalfields and Banglatown', 'Weavers', 'Whitechapel', "St Katharine's and Wapping"])]), mask, north)
    areas['southbank'] = add(areas, unary_union([wards('E09000022', ["Bishop's", "Prince's"]), wards('E09000028', ['Cathedrals', 'Chaucer'])]), mask)
    areas = fill_gaps(areas, ['farringdon', 'clerkenwell', 'shoreditch', 'southbank'], mask)
    # crop: the deck's extent, centred on the areas, inside each published v3 frame (its base map is reused)
    core = unary_union([areas[k] for k in areas if k != 'shoreditch']); bx = core.bounds
    frames = {}
    for v, asp in (('wide', 0.95), ('tall', 0.80)):
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
    areas['jordaan'] = fixed(unary_union([areas['jordaan'], add(others('jordaan'), U('Haarlemmerbuurt'), mask)]))
    areas['centrum'] = add(areas, U('Burgwallen-Nieuwe Zijde', 'Burgwallen-Oude Zijde', 'Nieuwmarkt/Lastage'), mask)
    areas['sloterdijk'] = add(areas, U('Sloterdijk', 'Houthavens', 'Spaarndammer- en Zeeheldenbuurt'), mask)
    areas['west'] = add(areas, U('Frederik Hendrikbuurt', 'Staatsliedenbuurt', 'Centrale Markt', 'Van Galenbuurt', 'Landlust', 'De Kolenkit', 'Erasmuspark', 'Hoofdweg en omgeving', 'Westindische buurt', 'De Krommert'), mask)
    areas['noord'] = add(areas, U('Volewijck', 'Ijplein/Vogelbuurt', 'Buiksloterham', 'Nieuwendammerham'), mask)
    areas['overamstel'] = add(areas, U('De Omval'), mask)
    areas['buitenveldert'] = add(areas, U('Buitenveldert-West', 'Buitenveldert-Oost'), mask)
    areas = fill_gaps(areas, ['centrum', 'west', 'sloterdijk', 'noord', 'overamstel', 'buitenveldert'], mask)
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
    for k, cls, *_ in meta:
        f = R.FOCUS[cls]; o.append(f'<path d="{R.d_path(T(groups[k]), 1)}" fill="{f["fill"]}" fill-opacity="{f["op"]}"/>')
    o += canals
    for k, cls, *_ in sorted(meta, key=lambda m: m[1] == 'core'):     # core outlines last, so a shared edge reads as core
        f = R.FOCUS[cls]; d = R.d_path(T(groups[k]), 1)
        o.append(f'<path d="{d}" fill="none" stroke="{R.COL["land"]}" stroke-opacity="0.85" stroke-width="{f["w"] + 2.4}" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="{d}" fill="none" stroke="{f["stroke"]}" stroke-width="{f["w"]}" stroke-linejoin="round"' + (f' stroke-dasharray="{f["dash"]}"' if f['dash'] else '') + ' vector-effect="non-scaling-stroke"/>')
    k_ = W / R.NOMINAL_W[v]
    for k, *_ in meta:
        L = labels[k]
        if L['ax'] is None: continue
        ax, ay = L['ax'] / 100 * W, L['ay'] / 100 * H; lx, ly = L['x'] / 100 * W, L['y'] / 100 * H
        dx, dy = lx - ax, ly - ay; dist = math.hypot(dx, dy) or 1; ex, ey = lx - dx / dist * 2 * k_, ly - dy / dist * 2 * k_
        o.append(f'<path d="M{ax:.1f} {ay:.1f}L{ex:.1f} {ey:.1f}" fill="none" stroke="{R.INK}" stroke-width="1" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="M{ax:.1f} {ay:.1f}h0.01" fill="none" stroke="{R.INK}" stroke-width="5" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    o.append('</svg>')
    open(REPO + f'assets/maps/{city}-{v}.svg', 'w', encoding='utf-8').write('\n'.join(o))
    return F

def fill_gaps(areas, new, mask, max_ha=30):
    u = fixed(unary_union(list(areas.values())).buffer(40, join_style=2).buffer(-40, join_style=2))     # gaps open to the outside by a street width count as enclosed
    for p in polys(u):
        for ring in p.interiors:
            for h in polys(fixed(fixed(Polygon(ring)).difference(mask).difference(unary_union(list(areas.values()))))):
              if h.area / 1e4 > max_ha or h.area < 500: continue
              best = max(new, key=lambda k: areas[k].buffer(1).intersection(h.boundary).length)
              if areas[best].buffer(1).intersection(h.boundary).length > 0: areas[best] = fixed(unary_union([areas[best], h.buffer(0.5)]).difference(unary_union([g for k, g in areas.items() if k != best])))
    return areas

def run():
    res = {}
    for city, fn in (('london', london), ('amsterdam', amsterdam)):
        areas, meta, old, new = fn(); res[city] = {'labels': {}, 'frames': {}, 'meta': meta}
        fx = {}
        for v in ('wide', 'tall'):
            fb = box(*new[v]); groups = {k: fixed(areas[k].intersection(fb.buffer(40))) for k, *_ in meta}
            vis = {k: fixed(areas[k].intersection(fb)) for k, *_ in meta}
            m = [dict(key=k, cls=c, en=en, ja=ja, **({'fixed': FIXED[k]} if k in FIXED else {})) for k, c, en, ja in meta]
            R.FONT = LABEL_PX
            labels = R.place_labels(city, v, R.Frame(new[v]), vis, m)
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

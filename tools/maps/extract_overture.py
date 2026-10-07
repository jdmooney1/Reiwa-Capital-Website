"""Regenerate the six Overture Maps extracts that tools/maps/build.py reads.

    python3 tools/maps/extract_overture.py OUTDIR [london|amsterdam ...]

Reads the public Overture Maps Foundation GeoParquet release 2026-08-19.0 (ODbL 1.0, (c) OpenStreetMap contributors) directly
from its S3 bucket with HTTP range requests (no credentials, no DuckDB extensions): only row groups whose bbox statistics meet the
box are read, then rows are kept when their own bbox meets the box. Each output is a GeoJSON FeatureCollection of whole features
(not clipped to the box), in release file and row order, with the flat properties the build uses: id, name (names.primary), subtype, class.

    london_segment / amsterdam_segment      theme=transportation / type=segment
    london_land_use / amsterdam_land_use    theme=base / type=land_use
    london_water / amsterdam_water          theme=base / type=water

The original extraction script was lost in a sandbox reset; the original byte-identical files could not be recovered. This script
is the documented replacement. Whether its output is equivalent is decided by rebuilding and comparing the rendered maps (see
docs/map-geography.md, "Replacement Overture inputs"); sources.json records both the original and the replacement hashes."""
import sys, os, io, json, time, concurrent.futures as cf, urllib.request, re
sys.dont_write_bytecode = True
import pyarrow.parquet as pq
from shapely import wkb
from shapely.geometry import mapping

RELEASE = '2026-08-19.0'
BUCKET = 'https://overturemaps-us-west-2.s3.amazonaws.com'
# (lon_min, lat_min, lon_max, lat_max). The original boxes were lost with the original script and were inferred from the delivered maps:
#   London   - the delivered SVGs carry no road or water geometry south of about 51.47 N or west of about -0.22 E, so the original box
#              stopped there; a larger box draws more base map than the approved maps show.
#   Amsterdam - a box that is too tight moves one vertex of the Oud-Zuid outline (a park/water mask polygon is included differently);
#              this larger box reproduces every focus-area outline exactly. The original files were smaller than this box would give.
#   Neither box is the original: see docs/map-geography.md, "Replacement Overture inputs".
BOX = {'london': (-0.22, 51.47, -0.04, 51.57), 'amsterdam': (4.70, 52.25, 5.05, 52.46)}
THEMES = {'segment': ('transportation', 'segment'), 'land_use': ('base', 'land_use'), 'water': ('base', 'water')}
KEEP = ['id', 'geometry', 'bbox', 'names', 'subtype', 'class']

def fetch(req, timeout=120, tries=6):
    """urlopen with retries: the egress proxy sometimes drops a connection."""
    for attempt in range(tries):
        try: return urllib.request.urlopen(req, timeout=timeout)
        except Exception:
            if attempt == tries - 1: raise
            time.sleep(1.5 * (attempt + 1))

def list_keys(theme, typ):
    prefix = f'release/{RELEASE}/theme={theme}/type={typ}/'; keys = []; token = None
    while True:
        url = f'{BUCKET}/?list-type=2&prefix={urllib.request.quote(prefix, safe="/")}' + (f'&continuation-token={urllib.request.quote(token)}' if token else '')
        t = fetch(url, 60).read().decode()
        keys += re.findall(r'<Key>(.*?)</Key>', t)
        m = re.search(r'<NextContinuationToken>(.*?)</NextContinuationToken>', t)
        if not m: return sorted(keys)
        token = m.group(1)

class HttpFile(io.RawIOBase):
    """Read-only, seekable file over HTTP range requests with a small block cache."""
    BLOCK = 1 << 20
    def __init__(self, url):
        self.url = url; self.pos = 0; self.cache = {}
        req = urllib.request.Request(url, method='HEAD'); self.size = int(fetch(req, 60).headers['Content-Length'])
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off; return self.pos
    def _block(self, i):
        if i not in self.cache:
            a = i * self.BLOCK; b = min(self.size, a + self.BLOCK) - 1
            self.cache[i] = fetch(urllib.request.Request(self.url, headers={'Range': f'bytes={a}-{b}'}), 120).read()
        return self.cache[i]
    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        end = min(self.size, self.pos + n); out = []; p = self.pos
        while p < end:
            i = p // self.BLOCK; blk = self._block(i); o = p - i * self.BLOCK; take = min(len(blk) - o, end - p); out.append(blk[o:o + take]); p += take
        self.pos = end; return b''.join(out)
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)

def rows_in_box(key, box, cols):
    x0, y0, x1, y1 = box
    f = HttpFile(f'{BUCKET}/{key}'); pf = pq.ParquetFile(f); md = pf.metadata
    names = [md.row_group(0).column(j).path_in_schema for j in range(md.row_group(0).num_columns)]
    idx = {n: names.index(n) for n in ('bbox.xmin', 'bbox.xmax', 'bbox.ymin', 'bbox.ymax')}
    groups = []
    for g in range(md.num_row_groups):
        rg = md.row_group(g); st = {k: rg.column(i).statistics for k, i in idx.items()}
        if any(s is None or not s.has_min_max for s in st.values()): groups.append(g); continue
        if st['bbox.xmin'].min <= x1 and st['bbox.xmax'].max >= x0 and st['bbox.ymin'].min <= y1 and st['bbox.ymax'].max >= y0: groups.append(g)
    out = []
    if groups:
        have = [c for c in cols if c in pf.schema_arrow.names]
        t = pf.read_row_groups(groups, columns=have).to_pylist()
        for r in t:
            b = r['bbox']
            if b['xmin'] <= x1 and b['xmax'] >= x0 and b['ymin'] <= y1 and b['ymax'] >= y0: out.append(r)
    return out

def round_coords(c):
    return [round(c[0], 7), round(c[1], 7)] if isinstance(c[0], (int, float)) else [round_coords(x) for x in c]

def feature(r):
    g = mapping(wkb.loads(r['geometry'])); g = {'type': g['type'], 'coordinates': round_coords(g['coordinates'])}
    nm = (r.get('names') or {}).get('primary') if r.get('names') else None
    return {'type': 'Feature', 'properties': {'id': r.get('id'), 'name': nm, 'subtype': r.get('subtype'), 'class': r.get('class')}, 'geometry': g}

def run(outdir, cities):
    os.makedirs(outdir, exist_ok=True)
    for city in cities:
        for short, (theme, typ) in THEMES.items():
            keys = list_keys(theme, typ); feats = []
            with cf.ThreadPoolExecutor(4) as ex:
                for rows in ex.map(lambda k: rows_in_box(k, BOX[city], KEEP), keys): feats += [feature(r) for r in rows]
            fn = os.path.join(outdir, f'{city}_{short}.geojson')
            with open(fn, 'w', encoding='utf-8') as fh: json.dump({'type': 'FeatureCollection', 'features': feats}, fh, separators=(',', ':'), ensure_ascii=False)
            print(f'{city}_{short}: {len(feats)} features, {os.path.getsize(fn)} bytes from {len(keys)} files', flush=True)

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2:] or ['london', 'amsterdam'])

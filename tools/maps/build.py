"""Build the About-page focus maps: geometry, SVG frames, labels, page patches, focus.js.
Usage:  MAP_DATA=/path/to/extracts python3 tools/maps/build.py
MAP_DATA holds the boundary and Overture extracts listed in README.md; output is written to the repository's assets/maps
and about.html / ja/about.html (labels, legend, note, alt text, cache version)."""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..','..'))
DATA=os.environ.get('MAP_DATA')
if not DATA: sys.exit('Set MAP_DATA to the directory holding the boundary and Overture extracts (see tools/maps/README.md).')
sys.path.insert(0,HERE); os.chdir(DATA); os.makedirs('out',exist_ok=True)
import hashlib
def check_sources():
    """Fail if an input differs from the pinned vintage (tools/maps/sources.json): a new ward or boundary set must not redefine the markets silently."""
    pinned=json.load(open(os.path.join(HERE,'sources.json')))['files']; bad=[]
    for fn,m in pinned.items():
        if not os.path.exists(fn): bad.append(fn+' (missing)'); continue
        h=hashlib.sha256()
        with open(fn,'rb') as f:
            for b in iter(lambda:f.read(1<<20),b''): h.update(b)
        if h.hexdigest()!=m['sha256']: bad.append(fn+' (differs from pinned '+m['vintage']+')')
    if bad and not os.environ.get('ACCEPT_NEW_SOURCES'):
        sys.exit('Inputs differ from tools/maps/sources.json:\n  '+'\n  '.join(bad)+'\nThe focus areas are Reiwa-defined, not administrative. Review with tools/maps/audit.py and docs/map-geography.md, update sources.json, or set ACCEPT_NEW_SOURCES=1.')
    print('source-file integrity: inputs match the pinned hashes' if not bad else 'WARNING: building from unpinned inputs')
check_sources()
import render, pages, focus_js
for city in ('london','amsterdam'):
    res,_,_,_=render.build_city(city,'out'); json.dump(res,open(f'out/{city}.json','w'))
import check_coverage
if check_coverage.run(): sys.exit('Coverage check failed: the cleanup added coverage outside the retained geometry and the recorded exceptions (tools/maps/coverage_rules.py).')
pages.run(REPO); focus_js.run(REPO)
print('done: assets/maps/*.svg, *-focus.js, about.html, ja/about.html')

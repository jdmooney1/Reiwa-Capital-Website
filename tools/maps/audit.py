"""Audit of the focus areas against the source units and the street geography. Writes docs/map-audit.json and prints a summary.
Usage:  MAP_DATA=/path/to/extracts python3 tools/maps/audit.py
Checks performed (all from the pinned extracts; nothing is fetched):
  - area, parts and holes of every drawn area;
  - London: how much of each boundary lies within 20 m of a named Overture road, and which roads carry it;
  - Amsterdam: overlap with the legacy buurtcombinaties and the CBS 2022 buurten and wijken for Plantage and Zuidas;
  - Canal Belt: the area of De Weteringschans against the drawn change;
  - Holborn / Midtown: the Aldwych piece and how much of it, and of Covent Garden, lies south of the Strand;
  - London ward fragments: the 25 explicit decisions in london_fragments.py, with their area, bounding streets and how much of each
    adds to the outline of the focus coverage (docs/london-ward-fragments.md); the geometric clean-up assignments that remain.
  CROPS_DIR=<dir> also writes focused crops of the unresolved and checked fragments (tools/maps/crops.py)."""
import os, sys, json, collections
HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,'..','..'))
DATA=os.environ.get('MAP_DATA')
if not DATA: sys.exit('Set MAP_DATA to the directory holding the extracts (see tools/maps/README.md).')
sys.path.insert(0,HERE); os.chdir(DATA)
import geometry as G
from shapely.geometry import shape, Point, box, Polygon
from shapely.ops import transform, unary_union, linemerge
from pyproj import Transformer
ha=lambda g: round(g.area/1e4,1)
def polys(g): return list(g.geoms) if g.geom_type=='MultiPolygon' else [g]
def load(fn): return json.load(open(fn))['features']
out={'london':{},'amsterdam':{}}
# --- Amsterdam
C,am=G.build('amsterdam'); C_am=C; areas={k:g for k,(c,g) in am.items()}
t=Transformer.from_crs(4326,28992,always_xy=True).transform
P=lambda g: transform(t,shape(g)).buffer(0)
bc={f['properties']['name']:P(f['geometry']) for f in load('blackmad_amsterdam.geojson')}
cbs={f['properties']['statnaam']+'|'+f['properties']['statcode']:P(f['geometry']) for f in load('cbs2022_amsterdam_buurt.geojson') if f['properties'].get('gmCode')=='GM0363' and f.get('geometry')}
wk={f['properties']['statnaam']+'|'+f['properties']['statcode']:P(f['geometry']) for f in load('cbs2022_amsterdam_wijk.geojson') if f['properties'].get('gmCode')=='GM0363' and f.get('geometry')}
A=out['amsterdam']; A['areas']={k:dict(ha=ha(g),parts=len(polys(g)),holes=sum(len(p.interiors) for p in polys(g))) for k,g in areas.items()}
pl=areas['Plantage']; wp=bc['Weesperbuurt/Plantage']; oe=bc['Oostelijke Eilanden/Kadijken']
A['plantage']=dict(drawn_ha=ha(pl),legacy_weesperbuurt_plantage_ha=ha(wp),legacy_oostelijke_eilanden_kadijken_ha=ha(oe),drawn_inside_legacy_wp_ha=ha(pl.intersection(wp)),drawn_inside_legacy_oe_ha=ha(pl.intersection(oe)),
  cbs_buurten={n:dict(ha=ha(g),drawn_overlap_ha=ha(pl.intersection(g))) for n,g in cbs.items() if n.split('|')[1].startswith(('BU036308','BU036309'))},
  cbs_wijk_weesperbuurt_plantage_ha=ha(next(g for n,g in wk.items() if n.startswith('Weesperbuurt/Plantage'))))
z=areas['Zuidas']; zw=next(g for n,g in wk.items() if n.startswith('Zuidas|'))
A['zuidas']=dict(drawn_ha=ha(z),cbs_buurten_of_wijk_zuidas={n:dict(ha=ha(g),drawn_overlap_ha=ha(z.intersection(g))) for n,g in cbs.items() if n.split('|')[1].startswith('BU036323')},
  cbs_kop_zuidas_ha=ha(next(g for n,g in cbs.items() if n.startswith('Kop Zuidas'))),
  legacy_station_zuid_wtc_ha=ha(bc['Station-Zuid WTC en omgeving']),drawn_inside_legacy_station_zuid_wtc_ha=ha(z.intersection(bc['Station-Zuid WTC en omgeving'])))
cb=areas['Canal Belt (Grachtengordel)']; wz=unary_union([bc['Grachtengordel-West'],bc['Grachtengordel-Zuid']])
A['canal_belt']=dict(drawn_ha=ha(cb),legacy_west_plus_zuid_ha=ha(wz),drawn_outside_legacy_ha=ha(cb.difference(wz)),de_weteringschans_legacy_ha=ha(bc['De Weteringschans']),drawn_overlap_with_weteringschans_ha=ha(cb.intersection(bc['De Weteringschans'])))
# --- London
C,lo=G.build('london'); L={k:g for k,(c,g) in lo.items()}
tf=Transformer.from_crs(4326,27700,always_xy=True); PL=lambda g: transform(tf.transform,shape(g))
roads=[]
for f in load('london_segment.geojson'):
    p=f['properties']; nm=p.get('names') or p.get('name')
    if isinstance(nm,dict): nm=nm.get('primary')
    if f['geometry'] and p.get('subtype')=='road' and nm: roads.append((nm,PL(f['geometry'])))
S=out['london']['areas']={}
for k,g in L.items():
    b=g.boundary; Lm=b.length; near=[(n,r) for n,r in roads if r.distance(g)<30]
    cov=b.intersection(unary_union([r for n,r in near]).buffer(20)).length/Lm
    cnt=collections.Counter()
    for n,r in near:
        l=b.intersection(r.buffer(20)).length
        if l>30: cnt[n]+=l
    S[k]=dict(ha=ha(g),parts=len(polys(g)),holes=sum(len(p.interiors) for p in polys(g)),boundary_m=round(Lm),pct_boundary_on_named_road=round(100*cov),top_roads=[[n,round(l)] for n,l in cnt.most_common(6)])
hm=L['Holborn / Midtown']; cg=L['Covent Garden']
cx=tf.transform(-0.1178,51.5112)[0]
strand=linemerge(unary_union([r for n,r in roads if n=='Strand']))
def south_share(g):
    n=s=0; x0,y0,x1,y1=g.bounds; x=x0
    while x<x1:
        y=y0
        while y<y1:
            if g.contains(Point(x,y)):
                n+=1; d=strand.project(Point(x,y)); a=strand.interpolate(max(d-5,0)); b2=strand.interpolate(d+5)
                cross=(b2.x-a.x)*(y-a.y)-(b2.y-a.y)*(x-a.x)
                if (cross<0)==((b2.x-a.x)>0): s+=1
            y+=6
        x+=6
    return round(100*s/max(n,1))
out['london']['aldwych']=dict(midtown_ha=ha(hm),midtown_east_of_lancaster_place_line_ha=ha(hm.intersection(box(cx,0,1e7,1e7))),midtown_pct_south_of_strand_line=south_share(hm),covent_garden_ha=ha(cg),covent_garden_pct_south_of_strand_line=south_share(cg),note='south-of-Strand shares are grid samples against the Strand centreline: approximate')
res=lambda c: json.load(open(f'out/{c}.json'))['audit']
from london_fragments import FRAGMENTS, DETACHED
from shapely import wkb
rules={r['id']:r for r in FRAGMENTS}; U_all=unary_union(list(L.values()))
frs=[]
for f in C.fragment_log:
    r=rules[f['id']]; g=wkb.loads(bytes.fromhex(f['wkb'])); inside=g.intersection(U_all)
    rest=U_all.difference(g); closed=rest.buffer(25,join_style=2).buffer(-25,join_style=2); closed=unary_union([Polygon(q.exterior) for q in polys(closed)])   # outline: notches under 50 m closed, holes filled
    added=inside.difference(closed).area/1e4 if not inside.is_empty else 0.0
    frs.append(dict(id=r['id'],ward=r['ward'],ha=f['ha'],lon=f['lon'],lat=f['lat'],assign=r['assign'] if not isinstance(r['assign'],dict) else 'split: west '+r['assign']['west']+', east '+r['assign']['east'],status=r['status'],streets=r['streets'],basis=r['basis'],
        in_focus_coverage_ha=round(inside.area/1e4,1),adds_to_outline_ha=round(added,1)))
out['london']['fragments']=frs
for r in FRAGMENTS:
    if r['anchor'] is None: out['london'].setdefault('fragment_parts',[]).append(dict(id=r['id'],ha=r['ha'],assign=r['assign'],status=r['status'],streets=r['streets']))
def summ(L_,areas_):
    U=unary_union([g for g in areas_.values()]); big=[]
    for x in sorted([x for x in L_ if x[1]>=0.5],key=lambda x:-x[1]):
        g=wkb.loads(bytes.fromhex(x[3][2])) if len(x[3])>2 else None
        big.append(dict(kind=x[0],ha=x[1],given_to=x[2],lon=x[3][0],lat=x[3][1],ha_inside_final_focus_coverage=round(g.intersection(U).area/1e4,2) if g is not None else None))
    return dict(pieces=len(L_),total_ha=round(sum(x[1] for x in L_),1),largest_ha=max([x[1] for x in L_],default=0),pieces_of_0_5_ha_or_more=big)
out['london']['geometric_cleanup']=summ(C.cleanup_log,L); out['amsterdam']['geometric_cleanup']=summ(C_am.cleanup_log,areas)
import coverage
cov_am=coverage.run(C_am,am); cov_lo=coverage.run(C,lo)
for city_,cv in (('london',cov_lo),('amsterdam',cov_am)): out[city_]['coverage_union']=cv
covmd=['# Coverage-union audit: what the shared-edge cleanup may add to the retained coverage','',
 'Generated by `tools/maps/audit.py` (`tools/maps/coverage.py`, `tools/maps/coverage_rules.py`) from the pinned inputs.','',
 '**Retained coverage (E)** is each focus area as defined from its source units, overlaps resolved, the 25 London ward fragments and D1 placed by `london_fragments.py`, smoothed per area, minus the park and river mask. **Final coverage (F)** is the union of the areas as drawn (and in `focus.js`). The shared-edge cleanup may allocate ground that E already holds between areas. Final coverage is E plus the recorded seam and gap allowances only, and both allowances do add bounded ground beyond E. Since 7 October 2026 `coverage_rules.py` cuts every area back to E + SEAM + recorded gaps:','',
 '- **Rule S, seam:** ground within 13 m of two different retained areas (a seam of at most 26 m where two areas meet along a shared edge).',
 '- **Rule G, recorded enclosed gap:** a gap enclosed by E and SEAM on all sides, at least 3 m from any park or river, no larger than 0.25 ha, listed in `EXCEPTIONS` with its position, a maximum area and its basis. An unlisted gap is removed.',
 '- Everything else is removed, however small: the road strip between an area and a park or river edge, blocks outside the definition, slivers on the outer edge.','',
 'Tolerance: coverage outside the rules is ignored only if it is no more than 0.5 m wide (it vanishes under an inward buffer of 0.25 m) or smaller than 1 m2; geometry is snapped to 0.01 m. `tools/maps/check_coverage.py` applies the same tolerance, runs inside `build.py` and fails the build above it.','']
for city_,cv in (('london',cov_lo),('amsterdam',cov_am)):
    covmd+=[f"## {city_.title()}",'',f"- Retained coverage E: {cv['explicit_coverage_ha']} ha; final coverage F: {cv['final_coverage_ha']} ha; the seam rule could allow at most {cv['seam_zone_ha']} ha.",
      f"- F outside E: **{cv['added_ha']} ha** in {cv['added_pieces']} pieces: {cv['added_by_rule']}. Anything under `other` would fail the check.",
      f"- Recorded enclosed gaps kept (rule G): {len(cv['recorded_gaps'])}, {cv['recorded_gaps_ha']} ha in all.",
      f"- **Cutback on 7 October 2026: {cv['cutback_ha']} ha in {cv['cutback_pieces']} pieces removed** (pieces of 0.005 ha or more listed below).",
      f"- E outside F (retained ground that the opening and mask steps drop): {cv['removed_ha']} ha.",'',
      'Cutback, largest first:','','| ha | Nearest named street | Lon, lat | Why removed |','|---|---|---|---|']
    for r in cv['cutback']: covmd.append(f"| {r['ha']} | {r['nearest_street']} ({r['nearest_street_m']} m) | {r['lonlat'][0]}, {r['lonlat'][1]} | {r['why']} |")
    covmd+=['','Recorded enclosed gaps kept (rule G, `coverage_rules.EXCEPTIONS`):','','| ID | ha | Lon, lat |','|---|---|---|']
    for r in cv['recorded_gaps']: covmd.append(f"| {r['id']} | {r['ha']} | {r['lonlat'][0]}, {r['lonlat'][1]} |")
    covmd+=['','Seam additions (rule S) of 0.05 ha or more:','','| ha | Held by | Nearest named street | Lon, lat |','|---|---|---|---|']
    for r in cv['added']:
        if r['rule'].startswith('S') and r['ha']>=0.05: covmd.append(f"| {r['ha']} | {r['held_by']} | {r['nearest_street']} ({r['nearest_street_m']} m) | {r['lonlat'][0]}, {r['lonlat'][1]} |")
    covmd+=['','Per-area smoothing already inside E (ha added / removed against the source-unit union): '+', '.join(f"{k} +{v['added']}/-{v['removed']}" for k,v in cv['smoothing_ha'].items()),'']
open(REPO+'/docs/map-coverage-union.md','w',encoding='utf-8').write('\n'.join(covmd))
if os.environ.get('CROPS_DIR'):
    import crops
    for city_,cv,C_,fin in (('london',cov_lo,C,lo),('amsterdam',cov_am,C_am,am)):
        for r in cv['cutback']:
            if r['ha']<0.2: continue
            nm=f"{city_}-removed-{r['ha']}ha-{r['nearest_street'].lower().replace(' ','-')}"; x,y=C_.P(__import__('shapely.geometry',fromlist=['Point']).Point(*r['lonlat'])).coords[0]
            crops.before_after(C_,fin,nm,r['wkb'],x,y,350,f"{city_.title()}: {r['ha']} ha removed ({r['nearest_street']})",os.environ['CROPS_DIR'])
for cv in (cov_am,cov_lo):
    for r in cv['cutback']: r.pop('wkb',None)
out['london']['unclaimed_fragments_ha']=res('london')['unclaimed']; out['amsterdam']['unclaimed_fragments_ha']=res('amsterdam')['unclaimed']
tbl=['# London ward fragments: explicit decisions','','Generated by `tools/maps/audit.py` from `tools/maps/london_fragments.py` and the pinned December 2013 wards. Every ward fragment (ground of a cut ward that no focus area took) has a row. The build stops on a fragment that is not listed here, so a new ward vintage cannot change coverage silently.','',
 'Status: **supported** (bounded by named streets and held by the area those streets and its definition give it), **closure** (road corridor or sliver between areas or against a park edge), **excluded** (stays outside the focus coverage), **unresolved** (held today, not independently supported), **split** (cut into two rows).','',
 '"Adds to outline" is the part of the fragment that lies outside the outline of the rest of the focus coverage (notches under 50 m closed, holes filled); 0.0 means the fragment only decides which area holds ground that the coverage already surrounds.','',
 '| ID | Ward | Fragment ha | Held by | Status | Adds to outline ha | Named streets | Basis |','|---|---|---|---|---|---|---|---|']
for f in frs: tbl.append(f"| {f['id']} | {f['ward']} | {f['ha']} | {f['assign'] if f['assign'] else 'unclaimed'} | {f['status']} | {f['adds_to_outline_ha']} | {f['streets']} | {f['basis']} |")
tbl+=['','Parts of the split fragment L02:','','| ID | ha | Held by | Status | Named streets |','|---|---|---|---|---|']
for p in out['london'].get('fragment_parts',[]): tbl.append(f"| {p['id']} | {p['ha']} | {p['assign']} | {p['status']+(' (provisional)' if p['status']=='unresolved' else '')} | {p['streets']} |")
g=out['london']['geometric_cleanup']
out['london']['detached_parts']=[dict(id=r['id'],area=r['area'],ha=r['ha'],to=r['to'],status=r['status'],streets=r['streets'],basis=r['basis'],ha_inside_final_focus_coverage=next((x['ha_inside_final_focus_coverage'] for x in g['pieces_of_0_5_ha_or_more'] if x['kind'].startswith('detached part of '+r['area']) and abs(x['lon']-r['anchor'][0])<0.001),None)) for r in DETACHED]
tbl+=['','## Detached parts of 0.5 ha or more','','A focus area can leave a detached part after the park and water masks are cut. One of 0.5 ha or more must be listed in `DETACHED` (`tools/maps/london_fragments.py`) or the build stops.','','| ID | From | Piece ha | Taken by | Inside final coverage ha | Named streets | Basis |','|---|---|---|---|---|---|---|']
for r in out['london']['detached_parts']: tbl.append(f"| {r['id']} | {r['area']} | {r['ha']} | {r['to']} | {r['ha_inside_final_focus_coverage']} | {r['streets']} | {r['basis']} |")
tbl+=['','## Remaining edge-length assignments','',f"The build still closes notches and enclosed gaps under 3 ha between areas that already touch, re-homes hairline faces and detached parts under 0.5 ha, by shared edge length: {g['pieces']} pieces, {g['total_ha']} ha in total, the largest {g['largest_ha']} ha. None is a ward fragment, and every piece of 0.5 ha or more is listed below. They allocate ground that is already retained; coverage_rules.py cuts every area back to the retained coverage plus the recorded seam and gap allowances, so nothing else is left in (docs/map-coverage-union.md). Pieces of 0.5 ha or more (detached parts are decided explicitly above):",'']
for x in g['pieces_of_0_5_ha_or_more']: tbl.append(f"- {x['ha']} ha ({x['kind']}) near lon {x['lon']}, lat {x['lat']} went to {x['given_to']}; {x['ha_inside_final_focus_coverage']} ha of it is inside the final focus coverage")
open(REPO+'/docs/london-ward-fragments.md','w',encoding='utf-8').write('\n'.join(tbl)+'\n')
if os.environ.get('CROPS_DIR'):
    import crops; fr_={f['id']:f for f in C.fragment_log}; fr_.update({'D1':{'wkb':x[3][2]} for x in C.cleanup_log if x[0].startswith('detached part') and x[1]>=5 and len(x[3])>2}); crops.run(C,lo,fr_,os.environ['CROPS_DIR'])
os.makedirs(REPO+'/docs',exist_ok=True); json.dump(out,open(REPO+'/docs/map-audit.json','w'),indent=1,ensure_ascii=False)
print(json.dumps({k:v for k,v in out['amsterdam'].items() if k!='areas'},indent=1,ensure_ascii=False)[:3500]); print(json.dumps(out['london']['aldwych'],indent=1))
for f in out['london']['fragments']: print(f['id'],f['ha'],'ha',f['status'],'adds',f['adds_to_outline_ha'],'to outline')
for k,v in out['london']['areas'].items(): print(k,v['ha'],'ha',v['pct_boundary_on_named_road'],'% on named roads',v['parts'],'part(s)',v['holes'],'hole(s)')

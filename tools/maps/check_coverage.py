"""Executable coverage check: fails if the cleanup introduces coverage outside the retained geometry and the recorded exceptions.

    MAP_DATA=/path/to/extracts python3 tools/maps/check_coverage.py [--selftest]

For both cities it builds the focus areas from the pinned inputs and computes, independently of the cleanup's own bookkeeping,
    extra = union of the final areas  minus  (E + SEAM)        (tools/maps/coverage_rules.py: E retained coverage, SEAM rule S)
and fails (exit 1) if
  - any piece of `extra` wider than TOL_WIDTH (0.5 m) and larger than TOL_AREA_M2 (1 m2) is not a recorded enclosed gap (rule G): enclosed by
    E + SEAM, at least MASK_CLEARANCE (3 m) from any park or river, no larger than HOLE_MAX_HA (0.25 ha), matched to an entry of
    EXCEPTIONS by anchor (within 3 m) and no larger than that entry's max_ha;
  - a recorded exception no longer matches a gap (stale), so the record cannot drift from the geometry;
  - one of the four additions removed on 7 October 2026 (Peto Place, Grosvenor Road, Chelsea Embankment, Ringweg-Zuid) is back.
Tolerance: 0.5 m width (a piece that vanishes under an inward buffer of 0.25 m) or 1 m2; geometry is snapped to 0.01 m.
--selftest proves the check can fail: it re-runs it with the cutback disabled and with a 100 m2 block added outside, and requires both to fail."""
import os, sys, json
sys.dont_write_bytecode=True
HERE=os.path.dirname(os.path.abspath(__file__)); DATA=os.environ.get('MAP_DATA')
if not DATA: sys.exit('Set MAP_DATA to the directory holding the extracts (see tools/maps/README.md).')
sys.path.insert(0,HERE); os.chdir(DATA)
import geometry as G, clean, coverage_rules as R
from shapely.geometry import Point, box
from shapely.ops import unary_union
fixed=clean.fixed
REMOVED_ON_7_OCT={'london':[('Peto Place',-0.14477,51.52433),('Grosvenor Road',-0.13115,51.4865),('Chelsea Embankment',-0.16163,51.48392)],'amsterdam':[('Ringweg-Zuid',4.89545,52.33363)]}
def check(city,mutate=None):
    C,a=G.build(city); final={k:v for k,v in a.items()}
    if mutate: final=mutate(C,final)
    E,Z=R.retained(C,list(final),fixed); base=fixed(unary_union([E,Z])); U=unary_union([g for _,g in final.values()])
    extra=fixed(U.difference(base)); lonlat=lambda pt:(lambda q:(round(q[0],5),round(q[1],5)))(C.inv(pt.x,pt.y))
    kept,removed,stale=R.classify(C,city,extra,base,lonlat)
    fails=[f"{city}: {r['ha']} ha outside the retained geometry and the recorded exceptions at lon {r['lon']}, lat {r['lat']}" for r in removed]
    fails+=[f"{city}: recorded exception {s} no longer matches a gap" for s in stale]
    for name,lo,la in REMOVED_ON_7_OCT[city]:
        if U.intersects(C.P(Point(lo,la)).buffer(1)): fails.append(f"{city}: the addition at {name} is back")
    return fails,dict(city=city,seam_ha=round(Z.area/1e4,2),retained_ha=round(E.area/1e4,1),final_ha=round(U.area/1e4,1),recorded_gaps=len(kept),recorded_gaps_ha=round(sum(r['ha'] for r in kept),3),tolerance_m=R.TOL_WIDTH,tolerance_m2=R.TOL_AREA_M2)
def run():
    bad=[]
    for city in ('london','amsterdam'):
        f,s=check(city); bad+=f; print(('FAIL ' if f else 'PASS ')+json.dumps(s))
        for x in f: print('   '+x)
    return bad
def selftest():
    orig=R.constrain; ok=True
    R.constrain=lambda C,out,fixed,keep_parts,MIN_PART: out        # the cleanup without the cutback
    f,_=check('london'); ok&=bool(f); print('selftest, cutback disabled: '+('fails as it must (%d findings)'%len(f) if f else 'DID NOT FAIL'))
    R.constrain=orig
    def add_block(C,final):
        k=next(iter(final)); cls,g=final[k]; x,y,_,_=g.bounds; blk=box(x-400,y-400,x-390,y-390)   # 100 m2 outside every area
        final=dict(final); final[k]=(cls,unary_union([g,blk])); return final
    f,_=check('london',add_block); ok&=bool(f); print('selftest, 100 m2 block added outside: '+('fails as it must' if f else 'DID NOT FAIL'))
    return ok
if __name__=='__main__':
    if '--selftest' in sys.argv: sys.exit(0 if selftest() else 1)
    bad=run(); sys.exit(1 if bad else 0)

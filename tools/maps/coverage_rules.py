"""What the shared-edge cleanup may leave in the coverage: the retained coverage plus the recorded seam and gap allowances, and nothing else.

Retained coverage E: each focus area as defined from its source units (clean.py: ward and buurt units, smoothed per area, overlaps resolved,
the 25 explicit London ward fragments and D1 placed by london_fragments.py), minus the park and river mask. It is recorded by clean.py as
`explicit_snapshot`, before any shared-edge cleanup.

The shared-edge cleanup (seam closing, notch and gap closing, the road strip beside a park or river, hairline faces, detached parts) may
ALLOCATE ground that E already holds between areas. Coverage beyond E is limited to the two recorded allowances below (rule S, rule G), which do add bounded ground. After it has run, `constrain` cuts every area back to

    allowed = E  U  SEAM  U  the recorded enclosed gaps (EXCEPTIONS)

  SEAM  (rule S) ground within SEAM_MAX of two different retained areas: the seam between two areas that meet along a shared edge (a ward
                 line, a named road). Its width is at most 2 x SEAM_MAX = 26 m. It cannot move the outer limit of the coverage by more than
                 SEAM_MAX, and only where two retained areas face each other.
  GAP   (rule G) a gap enclosed by E and SEAM on all sides, at least MASK_CLEARANCE from any park or river, no larger than HOLE_MAX_HA, AND
                 recorded below with its position, a maximum area and its basis. An unrecorded gap is removed, so a new vintage cannot add a gap allowance silently.
Everything else, however small, is removed: the road strip between an area and a park or river edge, blocks outside the definition, slivers
along the outer edge. Whether to widen a market definition is a separate decision and is not made here.

Tolerance: coverage outside `allowed` is ignored only if it is no more than TOL_WIDTH wide (it vanishes under an inward buffer of TOL_WIDTH/2)
or smaller than TOL_AREA_M2. Geometry is snapped to 0.01 m, so TOL_WIDTH is 50 times the grid. tools/maps/check_coverage.py applies the same
tolerance and fails the build above it."""
import itertools
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
SEAM_MAX=13.0          # m, per side
HOLE_MAX_HA=0.25       # ha, largest recorded enclosed gap
MASK_CLEARANCE=3.0     # m, a gap must be this far from any park or river
TOL_WIDTH=0.5          # m
TOL_AREA_M2=1.0        # m2
ANCHOR_TOL=3.0         # m, an exception matches a gap within this distance of its anchor

# Recorded enclosed gaps (rule G): id, anchor (lon, lat), maximum ha, named streets, basis. Measured and recorded on 7 October 2026.
EXCEPTIONS={
 'london':[
  dict(id='GL01',anchor=(-0.13124,51.51052),max_ha=0.302,area='Covent Garden',street='Swiss Court',
       basis="Enclosed gap of 0.24 ha (measured 7 Oct 2026) surrounded on every side by Covent Garden's retained coverage, beside Swiss Court (2 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL02',anchor=(-0.13514,51.5039),max_ha=0.232,area='Westminster',street='The Mall',
       basis="Enclosed gap of 0.184 ha (measured 7 Oct 2026) surrounded on every side by Westminster's retained coverage, beside The Mall (1 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL03',anchor=(-0.12482,51.50903),max_ha=0.222,area='Covent Garden',street='Strand',
       basis="Enclosed gap of 0.176 ha (measured 7 Oct 2026) surrounded on every side by Covent Garden's retained coverage, beside Strand (1 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL04',anchor=(-0.1447,51.50231),max_ha=0.13,area='Westminster',street='Constitution Hill',
       basis="Enclosed gap of 0.102 ha (measured 7 Oct 2026) surrounded on every side by Westminster's retained coverage, beside Constitution Hill (0 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL05',anchor=(-0.13569,51.51971),max_ha=0.121,area='Fitzrovia',street='Charlotte Street',
       basis="Enclosed gap of 0.095 ha (measured 7 Oct 2026) surrounded on every side by Fitzrovia's retained coverage, beside Charlotte Street (13 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL06',anchor=(-0.11432,51.51545),max_ha=0.103,area='Holborn / Midtown',street='Serle Street',
       basis="Enclosed gap of 0.081 ha (measured 7 Oct 2026) surrounded on every side by Holborn / Midtown's retained coverage, beside Serle Street (1 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL07',anchor=(-0.13164,51.51565),max_ha=0.088,area='Soho',street='Soho Square',
       basis="Enclosed gap of 0.069 ha (measured 7 Oct 2026) surrounded on every side by Soho's retained coverage, beside Soho Square (13 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL08',anchor=(-0.13615,51.51046),max_ha=0.068,area='Soho',street='Glasshouse Street',
       basis="Enclosed gap of 0.053 ha (measured 7 Oct 2026) surrounded on every side by Soho's retained coverage, beside Glasshouse Street (2 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL09',anchor=(-0.1306,51.50785),max_ha=0.013,area='Covent Garden',street='Pall Mall East',
       basis="Enclosed gap of 0.009 ha (measured 7 Oct 2026) surrounded on every side by Covent Garden's retained coverage, beside Pall Mall East (1 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL10',anchor=(-0.15407,51.5138),max_ha=0.008,area='Mayfair',street='Oxford Street',
       basis="Enclosed gap of 0.005 ha (measured 7 Oct 2026) surrounded on every side by Mayfair's retained coverage, beside Oxford Street (0 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL11',anchor=(-0.11799,51.51178),max_ha=0.003,area='Covent Garden',street='Strand',
       basis="Enclosed gap of 0.001 ha (measured 7 Oct 2026) surrounded on every side by Covent Garden's retained coverage, beside Strand (4 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GL12',anchor=(-0.1417,51.51529),max_ha=0.003,area='Soho',street='Oxford Street',
       basis="Enclosed gap of 0.001 ha (measured 7 Oct 2026) surrounded on every side by Soho's retained coverage, beside Oxford Street (1 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
 ],
 'amsterdam':[
  dict(id='GA01',anchor=(4.865,52.34305),max_ha=0.091,area='Oud-Zuid and Zuidas',street='Locatellikade',
       basis="Enclosed gap of 0.071 ha (measured 7 Oct 2026) surrounded on every side by Oud-Zuid and Zuidas's retained coverage, beside Locatellikade (22 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GA02',anchor=(4.88646,52.35271),max_ha=0.07,area='De Pijp',street='Hobbemakade',
       basis="Enclosed gap of 0.054 ha (measured 7 Oct 2026) surrounded on every side by De Pijp's retained coverage, beside Hobbemakade (19 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
  dict(id='GA03',anchor=(4.88672,52.35444),max_ha=0.023,area='De Pijp',street='Albert Cuypstraat',
       basis="Enclosed gap of 0.017 ha (measured 7 Oct 2026) surrounded on every side by De Pijp's retained coverage, beside Albert Cuypstraat (20 m). Ground that no unit or fragment decision covers, closed by the cleanup; it adds no outer limit. Geometric basis only: there is no source or market evidence for or against it, and it is recorded so that its extent is fixed. Remove it (leaving a hole) if Reiwa prefers."),
 ],
}

def parts(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    if g.geom_type in ('MultiPolygon','GeometryCollection'): return [p for x in g.geoms for p in parts(x)]
    return []
def poly_union(gs):
    ps=[p for g in gs for p in parts(g)]
    return unary_union(ps) if ps else Polygon()

def retained(C,final_keys,fixed):
    """(E, SEAM) for the focus areas named in final_keys (a drawn name or a part of one: 'Canal Belt' for 'Canal Belt (Grachtengordel)')."""
    focus=[k for k in C.explicit_snapshot if any(k in f for f in final_keys)]
    Ek={k:fixed(C.explicit_snapshot[k].difference(C.mask)) for k in focus}
    E=fixed(unary_union(list(Ek.values())))
    bufs={k:g.buffer(SEAM_MAX,join_style=2) for k,g in Ek.items()}
    Z=fixed(unary_union([bufs[i].intersection(bufs[j]) for i,j in itertools.combinations(focus,2)]).difference(C.mask))
    return E,Z

def classify(C,city,extra,base,lonlat):
    """Split the coverage outside E and SEAM into recorded gaps (kept) and everything else (removed). Returns (kept, removed, stale)."""
    holes=unary_union([Polygon(r) for p in parts(base) for r in p.interiors]) if not base.is_empty else Polygon()
    kept=[]; removed=[]; used=set()
    for p in sorted(parts(extra),key=lambda p:-p.area):
        if p.area<TOL_AREA_M2 or p.buffer(-TOL_WIDTH/2).is_empty: continue
        enclosed=p.intersection(holes).area>=0.9*p.area
        eligible=enclosed and p.distance(C.mask)>=MASK_CLEARANCE and p.area<=HOLE_MAX_HA*1e4
        ex=None
        if eligible:
            for e in EXCEPTIONS[city]:
                if e['id'] in used: continue
                a=C.P(Point(*e['anchor']))
                if p.distance(a)<=ANCHOR_TOL and p.area<=e['max_ha']*1e4: ex=e; break
        c=p.representative_point(); ll=lonlat(c)
        rec=dict(ha=round(p.area/1e4,3),lon=ll[0],lat=ll[1],enclosed=bool(enclosed),touches_mask=bool(p.distance(C.mask)<MASK_CLEARANCE),geom=p)
        if ex: used.add(ex['id']); rec['id']=ex['id']; kept.append(rec)
        else: removed.append(rec)
    stale=[e['id'] for e in EXCEPTIONS[city] if e['id'] not in used]
    return kept,removed,stale

def constrain(C,out,fixed,keep_parts,MIN_PART):
    """Cut every area back to E + SEAM + recorded gaps. Logs what was kept and removed in C.coverage_log. out: {name:(class,geometry)}."""
    city=C.name
    E,Z=retained(C,list(out),fixed); base=fixed(unary_union([E,Z]))
    U=unary_union([g for _,g in out.values()])
    extra=fixed(U.difference(base))
    lonlat=lambda pt: (lambda q:(round(q[0],5),round(q[1],5)))(C.inv(pt.x,pt.y))
    kept,removed,stale=classify(C,city,extra,base,lonlat)
    if stale: raise SystemExit('Recorded enclosed gaps no longer exist or no longer fit (tools/maps/coverage_rules.py): '+', '.join(stale))
    allowed=fixed(unary_union([base]+[r['geom'] for r in kept]))
    res={}
    for k,(cls,g) in out.items():
        res[k]=(cls,keep_parts(fixed(poly_union([g.intersection(allowed)])),MIN_PART))
    C.coverage_log=dict(kept=kept,removed=removed,seam_ha=round(Z.area/1e4,2),E=E,SEAM=Z)
    return res

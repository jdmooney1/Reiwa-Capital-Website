"""Coverage-union audit: what the shared-edge cleanup adds to, or removes from, the retained coverage.

E = the explicitly retained coverage (coverage_rules.py: each focus area as defined, overlaps resolved, fragments placed, smoothed per area),
    minus the park and river mask. clean.py keeps it as `explicit_snapshot`.
F = the final coverage: the union of the areas as drawn and in focus.js.
The comparison is on the union itself, not on a closed outer outline. "Added" = F outside E. Since 7 October 2026 the cleanup may only add
what a recorded rule allows (coverage_rules.py): rule S, the seam between two retained areas (within 13 m of both), and rule G, a recorded
enclosed gap. Every added piece is classified S, G or other; "other" must be empty, and tools/maps/check_coverage.py fails the build if it is not.
The cutback (C.coverage_log) lists what the cleanup produced outside those rules and what was removed."""
from shapely.ops import unary_union
from clean import fixed
import coverage_rules as CR
polys_only=CR.parts
HA=lambda g: g.area/1e4
def nearest_street(C,pt):
    best=None
    for p,g in C.roads:
        if p.get('subtype')!='road' or not p.get('name'): continue
        d=g.distance(pt)
        if best is None or d<best[1]: best=(p['name'],d)
    return (best[0],round(best[1])) if best else (None,None)
def run(C,final,min_report_ha=0.005):
    ks=list(final); E,Z=CR.retained(C,ks,fixed)
    F=unary_union([g for _,g in final.values()]).buffer(0); G_=unary_union([r['geom'] for r in C.coverage_log['kept']]) if C.coverage_log['kept'] else None
    added=F.difference(E); removed=E.difference(F)
    def holder(p):
        r=p.representative_point(); return next((k for k in ks if final[k][1].buffer(0.5).contains(r)),None)
    inS=added.intersection(Z); rest=added.difference(Z); inG=rest.intersection(G_) if G_ is not None else rest.difference(rest); oth=rest.difference(G_) if G_ is not None else rest
    keyS,keyG='S (seam within 13 m of two retained areas)','G (recorded enclosed gap)'
    by={keyS:HA(inS),keyG:HA(inG),'other':HA(oth)}; rows=[]
    for rule,g in ((keyS,inS),(keyG,inG),('other',oth)):
        for p in sorted([p for p in polys_only(g) if p.area>=CR.TOL_AREA_M2 and not p.buffer(-CR.TOL_WIDTH/2).is_empty],key=lambda p:-p.area):
            c=p.representative_point(); n,d=nearest_street(C,c); lo,la=C.inv(c.x,c.y)
            rows.append(dict(ha=round(HA(p),3),held_by=holder(p),rule=rule,nearest_street=n,nearest_street_m=d,lonlat=[round(lo,5),round(la,5)]))
    rows.sort(key=lambda r:-r['ha'])
    cut=[]
    for r in sorted(C.coverage_log['removed'],key=lambda r:-r['ha']):
        if r['ha']<min_report_ha: continue
        n,d=nearest_street(C,r['geom'].representative_point())
        why='outside every recorded rule and beside a park or river edge' if r['touches_mask'] else 'enclosed but unrecorded or above the 0.25 ha cap' if r['enclosed'] else 'outside every recorded rule, on the outer edge'
        cut.append(dict(ha=r['ha'],lonlat=[r['lon'],r['lat']],nearest_street=n,nearest_street_m=d,why=why,wkb=r['geom'].wkb_hex))
    rem=[]
    for p in sorted([p for p in polys_only(removed) if HA(p)>=0.05],key=lambda p:-p.area)[:12]:
        c=p.representative_point(); n,d=nearest_street(C,c); rem.append(dict(ha=round(HA(p),2),nearest_street=n,nearest_street_m=d,x=round(c.x),y=round(c.y)))
    kept=[dict(id=r['id'],ha=r['ha'],lonlat=[r['lon'],r['lat']]) for r in C.coverage_log['kept']]
    return dict(explicit_coverage_ha=round(HA(E),1),final_coverage_ha=round(HA(F),1),seam_zone_ha=round(HA(Z),1),
        added_ha=round(HA(added),2),added_by_rule={k:round(v,2) for k,v in by.items()},added_pieces=len(rows),added=rows,other_ha=round(HA(oth),3),
        recorded_gaps=kept,recorded_gaps_ha=round(sum(r['ha'] for r in kept),3),
        cutback_ha=round(sum(r['ha'] for r in C.coverage_log['removed']),2),cutback_pieces=len(C.coverage_log['removed']),cutback=cut,
        removed_ha=round(HA(removed),2),removed_largest=rem,
        smoothing_ha={k:dict(added=v[0],removed=v[1]) for k,v in C.smoothing.items() if any(k in f for f in ks)})

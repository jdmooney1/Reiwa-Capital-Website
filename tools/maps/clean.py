"""Reiwa Capital focus maps — v2 cleanup pass on top of build_maps.py.
Same sources, same area definitions and classes. Changes: (1) masks are an explicit list of
major parks and water only (London: Thames, Hyde Park, Kensington Gardens, Regent's Park, Green
Park, St James's Park, Buckingham Palace Garden; Amsterdam: IJ and harbour basins, Amstel, Nieuwe
Meer, Vondelpark, Westerpark, Rembrandtpark, Beatrixpark, Amstelpark, Amsterdamse Bos);
(2) each area is dissolved: interior rings filled, gaps under 20 m closed, spikes under 14 m
removed, islands under 1.5 ha dropped; (3) all areas are rebuilt from one noded planar partition so
adjoining areas share identical boundary coordinates, then enclosed hairline faces are assigned to
their longest neighbour; (4) validation table."""
import json, math, sys
import boundaries as bm
from boundaries import load
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, polygonize, linemerge, transform
from shapely import set_precision
from boundaries import fixed as _fixed
from london_fragments import FRAGMENTS, DETACHED
def fixed(g): return _fixed(set_precision(_fixed(g),0.01))

LONDON_PARKS=('Hyde Park','Kensington Gardens',"The Regent's Park",'Primrose Hill','The Green Park',"St. James's Park",'Buckingham Palace Garden')
AMS_PARKS=('Vondelpark','Westerpark','Rembrandtpark','Beatrixpark','Amstelpark','Amsterdamse Bos','Sloterpark','Flevopark','Noorderpark')
AMS_CANALS=('Singel','Herengracht','Keizersgracht','Prinsengracht','Brouwersgracht','Singelgracht','Amstel','Boerenwetering','Schinkel','Kostverlorenvaart','Nieuwe Herengracht','Nieuwe Keizersgracht','Nieuwe Prinsengracht','Entrepotdok','Nieuwe Vaart','Korte Prinsengracht')
MIN_PART=15000      # islands under 1.5 ha are dropped
GAP_MAX=30000       # enclosed faces under 3 ha (or thin) between areas are closed
THIN=0.012          # area / perimeter^2 below this is a strip

def polys(g): return [g] if g.geom_type=='Polygon' else list(g.geoms) if g.geom_type=='MultiPolygon' else []
def fill_holes(g): return fixed(unary_union([Polygon(p.exterior) for p in polys(g)]))
def keep_parts(g,minarea):
    ps=[p for p in polys(g) if p.area>=minarea]
    if not ps and polys(g): ps=[max(polys(g),key=lambda p:p.area)]
    return fixed(unary_union(ps)) if ps else Polygon()

class City(bm.City):
    def __init__(self,name,crs):
        super().__init__(name,crs)
        if name=='london':
            self.mask_parks=[(n,g) for n,g in self.parks+self.gardens if n in LONDON_PARKS]
            self.mask_water=[(p.get('name') or 'Thames',g) for p,g in self.water_polys if p['subtype']=='river' and g.area/1e4>=20]
        else:
            self.mask_parks=[(n,g) for n,g in self.parks if n in AMS_PARKS]
            self.mask_water=[(p.get('name') or p['subtype'],g) for p,g in self.water_polys
                             if p['class'] not in ('ditch','drain','swimming_pool') and p['subtype']!='human_made' and
                             ((g.area/1e4>=15) or (p['subtype']=='river' and g.area/1e4>=1) or (p.get('name') or '').startswith('IJ'))]
        self.mask=fixed(unary_union([g for _,g in self.mask_parks]+[g for _,g in self.mask_water]).buffer(0).simplify(1.5,preserve_topology=True))
        self.canals=[g for p,g in self.water_lines if p['class'] in ('canal','river') and p.get('name') in AMS_CANALS] if name=='amsterdam' else []
    def adjust(self,areas):
        if self.name=='london':
            # Holborn / Midtown = the Holborn and Covent Garden ward less the three pieces given to
            # Covent Garden (west of Kingsway), Bloomsbury (Bloomsbury Square) and Farringdon (Hatton
            # Garden): Lincoln's Inn, High Holborn, Red Lion Square and Gray's Inn as one polygon.
            wards={f['properties']['WD13NM']:fixed(self.P(shape(f['geometry']))) for b in ('E09000007','E09000033','E09000019','E09000012','E09000030') for f in load(f'wards_{b}.json')}
            hcg=wards['Holborn and Covent Garden']
            others=unary_union([areas[k][1] for k in ('Covent Garden','Bloomsbury','Farringdon')])
            areas['Holborn / Midtown']=('selective', keep_parts(fixed(hcg.difference(others.buffer(9,join_style=2))),MIN_PART))
            # Ward fragments (Charing Cross and the Embankment, Whitehall east of the road, the St Giles wedge,
            # Hoxton, Shoreditch) are decided one by one in london_fragments.py, not by shared edge length.
            self.parent_names=["St James's",'West End','Holborn and Covent Garden','Bloomsbury','Clerkenwell','Bunhill','Haggerston','Weavers']
            self.parents=[wards[n] for n in self.parent_names]
        else:
            self.parents=[]; self.parent_names=[]
            bc={f['properties']['name']:fixed(self.P(shape(f['geometry']))) for f in load('blackmad_amsterdam.geojson')}
            # The outer strip of the ring (De Weteringschans: Leidseplein to Frederiksplein) joins
            # Grachtengordel; Diamantbuurt and Duivelseiland join De Pijp. Without them the ring and
            # De Pijp show unclaimed strips that read as gaps.
            areas['Grachtengordel']=('core', fixed(unary_union([areas['Grachtengordel'][1], bc['De Weteringschans']])))
            areas['De Pijp']=('selective', fixed(unary_union([areas['De Pijp'][1], bc['Diamantbuurt']])))
            areas['Oud-Zuid']=('core', fixed(unary_union([areas['Oud-Zuid'][1], bc['Duivelseiland']])))
        return areas
    def finish(self,areas):
        areas=self.adjust(areas); out={}
        for k,(cls,g) in areas.items():
            r=OPEN.get(k,7)
            g=fill_holes(fixed(g))
            g=g.buffer(10,join_style=2).buffer(-10,join_style=2)      # close gaps < 20 m
            g=g.buffer(-r,join_style=2).buffer(r,join_style=2)        # remove spikes < 2r m
            g=fill_holes(fixed(g).simplify(3,preserve_topology=True))
            out[k]=(cls,keep_parts(g,MIN_PART))
        self.smoothing={k:(round(fixed(out[k][1]).difference(fixed(areas[k][1])).difference(self.mask).area/1e4,2),round(fixed(areas[k][1]).difference(fixed(out[k][1])).difference(self.mask).area/1e4,2)) for k in out}   # per-area smoothing: (ha added, ha removed) against the source-unit union
        ks=list(out)
        def longest_neighbour(f,exclude=None):
            return max([k for k in ks if k!=exclude],key=lambda k: out[k][1].buffer(TOL).intersection(f).area)
        self.cleanup_log=[]
        def ll(g):
            c=transform(self.inv,g.representative_point()); return [round(c.x,5),round(c.y,5)]+([g.wkb_hex] if g.area>=5000 else [])   # geometry kept for pieces of 0.5 ha or more
        def detached_target(k,p):      # a detached part of 0.5 ha or more is decided in london_fragments.DETACHED, never by edge length
            for r in DETACHED:
                if r['area']==k and p.buffer(3).contains(self.P(Point(*r['anchor']))): return r['to']
            c=transform(self.inv,p.representative_point())
            raise SystemExit(f"Unlisted detached part: {round(p.area/1e4,1)} ha of {k} near lon {c.x:.5f}, lat {c.y:.5f}. List it in DETACHED in tools/maps/london_fragments.py with the area that takes it.")
        def give(f):
            nb=longest_neighbour(f); self.cleanup_log.append(('notch or enclosed gap < 3 ha',round(f.area/1e4,2),nb,ll(f)))
            if out[nb][1].buffer(TOL).intersection(f).area>0: out[nb]=(out[nb][0],fixed(unary_union([out[nb][1],f])))
            else: self.unclaimed.append((round(f.area/1e4,1),'no neighbour'))
        self.given=[]; self.unclaimed=[]
        for i,k in enumerate(ks):                                    # earlier areas win overlaps
            prev=[out[p][1] for p in ks[:i]]
            if prev: out[k]=(out[k][0],keep_parts(fixed(out[k][1].difference(unary_union(prev))),MIN_PART))
        U=lambda: unary_union([out[k][1] for k in ks])
        # Ward fragments: ground of a cut ward that no area took. London fragments are decided one by one in london_fragments.py
        # (named streets, status, basis); the build stops on a fragment that is not listed. Nothing is given to a neighbour by edge length.
        self.fragment_log=[]; used=set()
        for pname,par in zip(self.parent_names,self.parents):
            res=fixed(fixed(par).difference(fixed(U().buffer(2))).difference(self.mask))
            for f in polys(res):
                rule=None
                for r in FRAGMENTS:
                    if r['ward']==pname and r['anchor'] and f.buffer(3).contains(self.P(Point(*r['anchor']))): rule=r; break
                ha=round(f.area/1e4,1); c=transform(self.inv,f.representative_point())
                if rule is None: raise SystemExit(f"Unlisted ward fragment: {ha} ha in {pname} near lon {c.x:.5f}, lat {c.y:.5f}. Add it to tools/maps/london_fragments.py with its named streets and the area that holds it; a new ward vintage must not decide investment coverage by edge length.")
                used.add(rule['id']); a=rule['assign']
                self.fragment_log.append(dict(id=rule['id'],ward=pname,ha=ha,lon=round(c.x,5),lat=round(c.y,5),assign=a if not isinstance(a,dict) else dict(a),wkb=f.wkb_hex))
                if a is None: self.unclaimed.append((ha,rule['id'])); continue
                if isinstance(a,dict):
                    cx=self.P(Point(*a['cut_at'])).x; xa,ya,xb,yb=f.bounds
                    east=fixed(f.intersection(Polygon([(cx,ya-50),(xb+50,ya-50),(xb+50,yb+50),(cx,yb+50)])))
                    west=fixed(f.difference(east))
                    for nm,part in ((a['east'],east),(a['west'],west)):
                        out[nm]=(out[nm][0],fixed(unary_union([out[nm][1],part]))); self.given.append((round(part.area/1e4,1),nm,rule['id']))
                    continue
                out[a]=(out[a][0],fixed(unary_union([out[a][1],f]))); self.given.append((ha,a,rule['id']))
        self.stale_fragments=[r['id'] for r in FRAGMENTS if r['anchor'] and r['id'] not in used]
        if self.name=='london' and self.stale_fragments: raise SystemExit('Listed ward fragments no longer exist: '+', '.join(self.stale_fragments))
        self.explicit_snapshot={k:out[k][1] for k in ks}              # the explicitly retained coverage: areas as defined, overlaps resolved, fragments placed; before any shared-edge clean-up
        SNAP=13.0                                                     # close seams to neighbours
        for k in ks:
            others=unary_union([out[o][1] for o in ks if o!=k])
            add=out[k][1].buffer(SNAP,join_style=2).intersection(others.buffer(SNAP,join_style=2)).difference(others)
            out[k]=(out[k][0],keep_parts(fixed(unary_union([out[k][1],add])),MIN_PART))
        for k in ks: out[k]=(out[k][0],keep_parts(fixed(out[k][1].difference(self.mask)),MIN_PART))
        for k in ks:                                                  # close the road strip between an area and a park or river
            others=unary_union([out[o][1] for o in ks if o!=k])
            add=fixed(out[k][1].buffer(EDGE,join_style=2).intersection(self.mask.buffer(EDGE,join_style=2))).difference(self.mask).difference(fixed(others.buffer(1)))
            out[k]=(out[k][0],fixed(unary_union([out[k][1],add])))
        for k in ks:                                                  # post-mask opening: strips left between parks (the Mall) go
            r=OPEN2.get(k,6); g=out[k][1].buffer(-r,join_style=2).buffer(r,join_style=2)
            out[k]=(out[k][0],keep_parts(fixed(g),MIN_PART))
        # notches and enclosed gaps under GAP_MAX between areas: close the union, give the difference
        u=fixed(U()); closed=fixed(u.buffer(CLOSE,join_style=2).buffer(-CLOSE,join_style=2))
        for f in polys(fixed(closed.difference(u).difference(self.mask))):
            if f.area<GAP_MAX: give(f)
        # one noded partition: every shared edge is the same line in both areas
        edges=unary_union([out[k][1].boundary for k in ks])
        faces=list(polygonize(edges)); assign={k:[] for k in ks}; gaps=[]
        for f in faces:
            owner=max(ks,key=lambda k: out[k][1].intersection(f).area)
            if out[owner][1].intersection(f).area>0.5*f.area: assign[owner].append(f)
            else: gaps.append(f)
        self.open_gaps=[]
        for f in gaps:
            if f.intersection(self.mask).area>0.5*f.area: continue
            if f.area<GAP_MAX or f.area/(f.length**2)<THIN: nb=longest_neighbour(f); assign[nb].append(f); self.cleanup_log.append(('hairline or small face between areas',round(f.area/1e4,2),nb,ll(f)))
            else: self.open_gaps.append(f)
        out={k:(out[k][0],fixed(unary_union(assign[k]).buffer(0))) for k in ks}
        # separate small or thin parts: to a touching neighbour, else dropped
        for k in ks:
            ps=polys(out[k][1])
            if len(ps)<2: continue
            big=max(ps,key=lambda p:p.area); keep=[big]
            for p in ps:
                if p is big: continue
                if p.area>=3*MIN_PART and p.area/(p.length**2)>=THIN: keep.append(p); continue
                nb=detached_target(k,p) if p.area>=5000 else longest_neighbour(p,exclude=k); self.cleanup_log.append(('detached part of '+k,round(p.area/1e4,2),nb,ll(p)))
                if out[nb][1].buffer(TOL).intersection(p).area>0: out[nb]=(out[nb][0],fixed(unary_union([out[nb][1],p])))
            out[k]=(out[k][0],fixed(unary_union(keep)))
        # final: nothing over the mask; no interior ring that is not an approved exclusion
        for k in ks:
            g=fixed(out[k][1].difference(self.mask)); ps=[]
            for p in polys(g):
                rings=[r for r in p.interiors if Polygon(r).intersection(self.mask).area>=0.5*Polygon(r).area]
                ps.append(Polygon(p.exterior,rings))
            out[k]=(out[k][0],keep_parts(fixed(unary_union(ps)),MIN_PART))
        return out

OPEN={}                          # pre-mask opening radius per area (m), default 7
OPEN2={"St James's":38}         # post-mask opening: St James's loses the strip along the Mall between the two parks
TOL=3.5                          # touching tolerance (m)
EDGE=22.0                       # road strip between an area and a park/river closed up to this width
CLOSE=60.0                      # notches and gaps narrower than 2x this between areas are closed

def validate(C,areas,adjacent):
    ks=list(areas); rows={}
    rows['invalid geometries']=sum(0 if g.is_valid else 1 for _,g in areas.values())
    ov=[(a,b,areas[a][1].intersection(areas[b][1]).area) for i,a in enumerate(ks) for b in ks[i+1:]]
    ov=[(a,b,x) for a,b,x in ov if x>1]
    rows['focus-area overlaps']=len(ov)
    rows['overlap area m2']=round(sum(x for _,_,x in ov),1)
    miss=[(a,b) for a,b in adjacent if areas[a][1].buffer(0.5).intersection(areas[b][1].buffer(0.5)).area<1 or areas[a][1].boundary.intersection(areas[b][1].boundary.buffer(0.5)).length<30]
    rows['unintended gaps (adjoining pairs not touching)']=len(miss)
    rows['enclosed gap faces left open']=len(C.open_gaps)
    holes=[(k,len(p.interiors)) for k,(_,g) in areas.items() for p in polys(g) if p.interiors]
    unexpected=0
    for k,(_,g) in areas.items():
        for p in polys(g):
            for r in p.interiors:
                if Polygon(r).intersection(C.mask).area<0.5*Polygon(r).area: unexpected+=1
    rows['interior holes (total)']=sum(n for _,n in holes)
    rows['interior holes other than approved exclusions']=unexpected
    rows['major park/water intersection m2']=round(sum(g.intersection(C.mask).area for _,g in areas.values()),1)
    rows['sliver parts < 1.5 ha']=sum(1 for _,g in areas.values() for p in polys(g) if p.area<MIN_PART)
    rows['thin parts (area/perimeter^2 < 0.012)']=sum(1 for _,g in areas.values() for p in polys(g) if p.area/(p.length**2)<THIN)
    rows['multipart areas']=[k for k,(_,g) in areas.items() if len(polys(g))>1]
    rows['missing adjacency']=miss; rows['overlaps']=[(a,b,round(x)) for a,b,x in ov]
    return rows

ADJ_LON=[('Marylebone','Fitzrovia'),('Marylebone','Mayfair'),('Fitzrovia','Soho'),('Fitzrovia','Bloomsbury'),('Soho','Mayfair'),('Soho','Covent Garden'),("St James's",'Mayfair'),("St James's",'Westminster'),("St James's",'Covent Garden'),('Covent Garden','Holborn / Midtown'),('Bloomsbury','Holborn / Midtown'),('Holborn / Midtown','Farringdon'),('Farringdon','Clerkenwell'),('Farringdon','City of London'),('Clerkenwell','City of London'),('City of London','Shoreditch & Aldgate'),('Clerkenwell','Shoreditch & Aldgate'),('Westminster','Covent Garden')]
ADJ_AMS=[('Jordaan','Canal Belt'),('Canal Belt','Grachtengordel'),('Canal Belt','Centrum'),('Grachtengordel','Centrum'),('Grachtengordel','Plantage'),('Grachtengordel','De Pijp'),('Oud-Zuid','De Pijp'),('Oud-Zuid','Zuidas'),('Oud-Zuid','Oud-West'),('De Pijp','Rivierenbuurt'),('Zuidas','Rivierenbuurt'),('Zuidas','Buitenveldert'),('Jordaan','West'),('West','Oud-West'),('Plantage','Oost'),('Rivierenbuurt','Buitenveldert')]

"""Reiwa Capital focus maps - boundary primitives (City, street cuts, masks), as used by geometry.py.
Original header:
Reiwa Capital focus maps — geometry build.
London: ONS 2013 ward polygons (Open Geography Portal, OGL v3; mirror martinjc/UK-GeoJSON) and the
ONS City of London LAD polygon, cut along named road centrelines from Overture Maps (transportation/segment,
2026-08-19.0, ODbL). Amsterdam: Gemeente Amsterdam buurtcombinaties (gebiedsindeling; mirror
blackmad/neighborhoods, names verified against the official list, geometry cross-checked against
Overture/OSM neighbourhood polygons). Both: parks >= 3 ha and water polygons >= 1 ha from Overture
base/land_use and base/water (ODbL) subtracted from every focus polygon, so edges follow park and
water lines; smaller squares and canals stay inside the fill and are drawn on top."""
import json, math, sys
from shapely.geometry import shape, mapping, Point, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import unary_union, polygonize, linemerge, transform
from shapely import make_valid
from pyproj import Transformer
PARK_MIN_HA=4.0; WATER_MIN_HA=2.0   # masks: parks/gardens >= 4 ha, open water >= 2 ha (ditches and drains never)

def load(fn): return json.load(open(fn))['features']
def proj(crs):
    tr=Transformer.from_crs('EPSG:4326',crs,always_xy=True)
    return lambda g: transform(tr.transform, g)
def fixed(g):
    g=make_valid(g)
    if g.geom_type=='GeometryCollection': g=unary_union([p for p in g.geoms if p.geom_type in ('Polygon','MultiPolygon')])
    return g
def ha(g,P): return P(g).area/1e4

# ---------------------------------------------------------------- helpers
class City:
    def __init__(self,name,crs):
        self.name=name; self.P=proj(crs); self.inv=Transformer.from_crs(crs,'EPSG:4326',always_xy=True).transform
        self.lu=[(f['properties'],fixed(self.P(shape(f['geometry'])))) for f in load(f'{name}_land_use.geojson') if f['geometry']['type'] in ('Polygon','MultiPolygon')]
        self.parks=[(p['name'],g) for p,g in self.lu if p['subtype']=='park']
        self.water_polys=[(f['properties'],fixed(self.P(shape(f['geometry'])))) for f in load(f'{name}_water.geojson') if f['geometry']['type'] in ('Polygon','MultiPolygon')]
        self.water_lines=[(f['properties'],self.P(shape(f['geometry']))) for f in load(f'{name}_water.geojson') if f['geometry']['type'] in ('LineString','MultiLineString')]
        self.roads=[(f['properties'],self.P(shape(f['geometry']))) for f in load(f'{name}_segment.geojson')]
        self.gardens=[(p['name'],g) for p,g in self.lu if p['subtype']=='horticulture' and p['class']=='garden']
        self.mask_parks=[(n,g) for n,g in self.parks+self.gardens if g.area/1e4>=PARK_MIN_HA]
        self.mask_water=[(p.get('name'),g) for p,g in self.water_polys if g.area/1e4>=WATER_MIN_HA and p['subtype'] in ('river','water','canal','lake','reservoir','physical','ocean') and p['class'] not in ('ditch','drain')]
        self.mask=unary_union([g for _,g in self.mask_parks]+[g for _,g in self.mask_water])
    def road(self,*names):
        ls=[g for p,g in self.roads if p['subtype']=='road' and p['name'] in names]
        assert ls, names
        u=unary_union(ls); return u if u.geom_type=='LineString' else linemerge(u)
    def _near(self,name,poly,d=80):
        l=self.road(name); parts=[p for p in ([l] if l.geom_type=='LineString' else l.geoms) if p.distance(poly)<d]
        return parts
    @staticmethod
    def _extend(line,poly,dmax=400):
        """Extend each end of every part along its own direction to the first crossing of the
        polygon boundary (at most dmax m), so a centreline that stops at a junction, a river bank
        or a palace wall still divides the polygon cleanly."""
        parts=[line] if line.geom_type=='LineString' else list(line.geoms); out=[]
        def ray(p0,p1):
            L=math.hypot(p1[0]-p0[0],p1[1]-p0[1]) or 1; ux,uy=(p1[0]-p0[0])/L,(p1[1]-p0[1])/L
            r=LineString([p1,(p1[0]+ux*dmax,p1[1]+uy*dmax)]); hit=r.intersection(poly.boundary)
            pts=[hit] if hit.geom_type=='Point' else [g for g in getattr(hit,'geoms',[]) if g.geom_type=='Point']
            if not pts: return (p1[0]+ux*2,p1[1]+uy*2)
            q=min(pts,key=lambda q:q.distance(Point(p1))); d=q.distance(Point(p1))+2
            return (p1[0]+ux*d,p1[1]+uy*d)
        for l in parts:
            c=list(l.coords)
            if len(c)<2: continue
            out.append(LineString([ray(c[1],c[0])]+c+[ray(c[-2],c[-1])]))
        return MultiLineString(out)
    def split(self,poly,names,seeds,tag='',bridge=170):
        """Split poly along the named road centrelines and keep the faces containing the seed
        points. For each name the centreline is trimmed to the parts running within 80 m of the
        polygon (a road of the same name elsewhere is ignored). Open ends are extended to the
        polygon boundary, and endpoints of different roads within `bridge` metres of each other are
        joined by a straight segment, so a junction where one street name becomes the next still
        closes the cut. Seeds are real places (lon, lat), which makes every area checkable."""
        groups=[]
        for n in names:
            parts=self._near(n,poly)
            if not parts: print(f'  note[{tag}]: {n} not adjacent', file=sys.stderr); continue
            u=unary_union(parts); m=u if u.geom_type=='LineString' else linemerge(u)
            groups.append(self._extend(m,poly))
        segs=[]
        for gi,g in enumerate(groups):
            for l in ([g] if g.geom_type=='LineString' else g.geoms): segs.append((gi,l))
        ends=[(gi,Point(c)) for gi,l in segs for c in (l.coords[0],l.coords[-1])]
        bridges=[]
        for i,(gi,p) in enumerate(ends):
            best=None
            for gj,q in ends:
                if gj==gi: continue
                d=p.distance(q)
                if d<bridge and (best is None or d<best[0]): best=(d,q)
            if best: bridges.append(LineString([p,best[1]]))
        # Cut with a narrow corridor rather than a bare line: the corridor closes the small gaps
        # left where a centreline is split into separate ways, then each kept piece is grown back
        # by the same width so neighbouring areas meet on the street centre with no seam.
        W=9.0
        corridor=unary_union([l for _,l in segs]+bridges).buffer(W,cap_style=2,join_style=2)
        rest=poly.difference(corridor)
        pieces=[rest] if rest.geom_type=='Polygon' else list(rest.geoms)
        pieces=[p for p in pieces if p.area>2000]
        pts=[self.P(Point(x,y)) for x,y in seeds]
        keep=[p for p in pieces if any(p.buffer(W+1).contains(q) for q in pts)]
        missed=[i for i,q in enumerate(pts) if not any(p.buffer(W+1).contains(q) for p in pieces)]
        if missed: print(f'  note[{tag}]: seed(s) {missed} outside every piece', file=sys.stderr)
        if len(pieces)<2: print(f'  note[{tag}]: the cut did not divide the polygon', file=sys.stderr)
        if not keep: print(f'  note[{tag}]: no piece selected', file=sys.stderr); return Polygon()
        return fixed(unary_union([p.buffer(W+0.5,cap_style=2,join_style=2) for p in keep]).intersection(poly))
    def finish(self,areas):
        """Subtract parks/water masks, drop slivers, light simplification; report."""
        out={}
        for k,(cls,g) in areas.items():
            g=fixed(g).simplify(2.5,preserve_topology=True).buffer(0).difference(self.mask)
            if g.geom_type=='MultiPolygon':
                g=unary_union([p for p in g.geoms if p.area>=4000])   # drop slivers only (< 0.4 ha)
            out[k]=(cls,fixed(g))
        # adjoining areas share clean edges: later areas yield to earlier ones on any overlap
        ks=list(out)
        for i,k in enumerate(ks):
            prev=[out[p][1] for p in ks[:i]]
            if prev:
                g=out[k][1].difference(unary_union(prev))
                if g.geom_type=='MultiPolygon':
                    g=unary_union([p for p in g.geoms if p.area>=4000])
                out[k]=(out[k][0],fixed(g))
        # Close the hairline seams left by street corridors and by generalised source polygons:
        # each area may grow up to SNAP metres, but only into ground within SNAP of another focus
        # area, never into a park or water, and never into ground another area already holds.
        SNAP=13.0
        ks=list(out)
        for k in ks:
            others=unary_union([out[o][1] for o in ks if o!=k])
            add=out[k][1].buffer(SNAP,join_style=2).difference(self.mask).intersection(others.buffer(SNAP,join_style=2)).difference(others)
            g=fixed(unary_union([out[k][1],add]))
            if g.geom_type=='MultiPolygon': g=unary_union([p for p in g.geoms if p.area>=4000])
            out[k]=(out[k][0],fixed(g))
        # overlap audit
        ks=list(out)
        for i in range(len(ks)):
            for j in range(i+1,len(ks)):
                a=out[ks[i]][1].intersection(out[ks[j]][1]).area
                if a>500: print(f'  OVERLAP {ks[i]} x {ks[j]}: {a/1e4:.2f} ha', file=sys.stderr)
        return out

# ---------------------------------------------------------------- London
def build_london():
    """Areas are built from ONS 2013 ward polygons (and the ONS City of London district), divided
    where a market boundary is a well-known street rather than a ward line. Each piece is chosen by
    a seed place inside it, listed beside the cut."""
    C=City('london','EPSG:27700'); P=C.P
    wards={}
    for b in ['E09000033','E09000001','E09000007','E09000019','E09000012','E09000030','E09000022','E09000028']:
        for f in load(f'wards_{b}.json'): wards[(b,f['properties']['WD13NM'])]=fixed(P(shape(f['geometry'])))
    W=lambda b,n: wards[(b,n)]
    WM,CI,CA,IS,HA,TH,LA,SO='E09000033','E09000001','E09000007','E09000019','E09000012','E09000030','E09000022','E09000028'
    city=fixed(P(shape(load('city_of_london_lad.json')[0]['geometry'])))
    westend=W(WM,'West End'); stj=W(WM,"St James's"); hcg=W(CA,'Holborn and Covent Garden'); bloom=W(CA,'Bloomsbury'); clerk=W(IS,'Clerkenwell'); bunhill=W(IS,'Bunhill')
    S={'Fitzroy Square':(-0.1395,51.5237),'Red Lion Square':(-0.1170,51.5185),'Leather Lane':(-0.1095,51.5185),'Trafalgar Square':(-0.1281,51.5080),'Leicester Square':(-0.1300,51.5105),'Buckingham Gate':(-0.1420,51.4995),'Horse Guards':(-0.1290,51.5045),'Jermyn Street':(-0.1370,51.5085),'Great Titchfield Street':(-0.1425,51.5180),'Charlotte Street':(-0.1355,51.5195),'Soho Square':(-0.1320,51.5155),'Carnaby Street':(-0.1390,51.5135),
       'Grosvenor Square':(-0.1510,51.5112),'Berkeley Square':(-0.1470,51.5095),"St James's Square":(-0.1360,51.5075),'Pall Mall':(-0.1350,51.5060),
       'Whitehall':(-0.1262,51.5045),'Parliament Square':(-0.1265,51.5008),'Victoria Street':(-0.1370,51.4975),'Covent Garden piazza':(-0.1230,51.5120),
       'Strand':(-0.1200,51.5105),'Drury Lane':(-0.1215,51.5140),'Great Queen Street':(-0.1215,51.5155),'Russell Square':(-0.1250,51.5215),'Bloomsbury Square':(-0.1240,51.5185),
       "Lincoln's Inn Fields":(-0.1175,51.5155),'Hatton Garden':(-0.1085,51.5195),'Cowcross Street':(-0.1040,51.5203),'Clerkenwell Green':(-0.1050,51.5232),
       'Exmouth Market':(-0.1090,51.5265),'Old Street':(-0.0900,51.5250),'Hoxton Square':(-0.0815,51.5270),'Curtain Road':(-0.0800,51.5250),
       'Redchurch Street':(-0.0755,51.5238),'Spitalfields Market':(-0.0755,51.5195),'Southbank Centre':(-0.1165,51.5060),'Borough Market':(-0.0910,51.5055),
       'Shad Thames':(-0.0725,51.5030),'Marylebone High Street':(-0.1510,51.5195),'Bryanston Square':(-0.1600,51.5165)}
    A={}
    A['Marylebone']=('core', unary_union([W(WM,'Marylebone High Street'),W(WM,'Bryanston and Dorset Square')]))
    A['Fitzrovia']=('core', unary_union([
        C.split(westend,['Oxford Street'],[S['Great Titchfield Street']],'fitzrovia/west-end'),                     # West End ward north of Oxford Street
        C.split(bloom,['Tottenham Court Road'],[S['Charlotte Street'],S['Fitzroy Square']],'fitzrovia/bloomsbury')]))          # Bloomsbury ward west of Tottenham Court Road
    # The St James's ward carries four markets. One set of streets divides them: Piccadilly and
    # Haymarket, the Mall and Cockspur Street, Constitution Hill, the Strand and Whitehall.
    WEC=['Piccadilly','Haymarket','Coventry Street','Cranbourn Street','Charing Cross Road','The Mall',
         'Cockspur Street','Constitution Hill','Northumberland Avenue','Strand','Whitehall']
    A['Soho']=('core', C.split(westend,['Oxford Street','Regent Street'],[S['Soho Square'],S['Carnaby Street']],'soho'))
    A['Mayfair']=('core', C.split(westend,['Oxford Street','Regent Street'],[S['Grosvenor Square'],S['Berkeley Square']],'mayfair'))
    A["St James's"]=('core', C.split(stj,WEC,[S['Pall Mall'],S["St James's Square"],S['Jermyn Street']],'stjames'))
    A['Westminster']=('core', unary_union([
        C.split(stj,WEC,[S['Horse Guards'],S['Parliament Square'],S['Buckingham Gate'],S['Victoria Street']],'westminster'),
        W(WM,'Vincent Square')]))
    A['Covent Garden']=('core', unary_union([
        C.split(stj,WEC,[S['Covent Garden piazza'],S['Strand'],S['Trafalgar Square'],S['Leicester Square']],'covent-garden'),
        C.split(hcg,['Kingsway','High Holborn','New Oxford Street'],[S['Great Queen Street']],'covent-garden/camden')]))   # Camden's slice west of Kingsway
    HCG=['Kingsway','High Holborn','New Oxford Street','Theobalds Road','Clerkenwell Road',"Gray's Inn Road"]
    A['Holborn / Midtown']=('selective', C.split(hcg,HCG,[S["Lincoln's Inn Fields"],S['Red Lion Square']],'midtown'))   # Holborn and Lincoln's Inn, west of Gray's Inn Road
    A['Bloomsbury']=('selective', unary_union([
        C.split(bloom,['Tottenham Court Road'],[S['Russell Square']],'bloomsbury'),
        C.split(hcg,HCG,[S['Bloomsbury Square']],'bloomsbury/holborn')]))
    A['Farringdon']=('selective', unary_union([
        C.split(hcg,HCG,[S['Hatton Garden'],S['Leather Lane']],'farringdon/hatton'),        # Hatton Garden and Leather Lane, east of Gray's Inn Road
        C.split(clerk,['Clerkenwell Road'],[S['Cowcross Street']],'farringdon/cowcross')]))  # Cowcross Street and Farringdon station, south of Clerkenwell Road
    A['Clerkenwell']=('selective', unary_union([
        C.split(clerk,['Clerkenwell Road'],[S['Clerkenwell Green'],S['Exmouth Market']],'clerkenwell'),
        C.split(bunhill,['City Road'],[(-0.0980,51.5245)],'clerkenwell/bunhill')]))                        # Bunhill ward west of City Road
    A['City of London']=('core', city)
    A['Shoreditch & Aldgate']=('selective', unary_union([
        C.split(W(HA,'Haggerston'),['Old Street','Hackney Road'],[S['Curtain Road'],S['Hoxton Square']],'shoreditch/haggerston'),   # Hoxton Square and Curtain Road are both in Haggerston ward
        C.split(bunhill,['City Road','Old Street'],[(-0.0855,51.5235)],'shoreditch/bunhill'),
        C.split(W(TH,'Weavers'),['Hackney Road','Brick Lane'],[S['Redchurch Street']],'shoreditch/weavers'),
        W(TH,'Spitalfields and Banglatown')]))                                                             # Spitalfields runs to Aldgate East
    sb=unary_union([W(LA,"Bishop's"), W(SO,'Cathedrals'), C.split(W(SO,'Riverside'),['Tower Bridge Road'],[S['Shad Thames']],'southbank/riverside')])
    A['South Bank']=('selective', C.split(sb,['Westminster Bridge Road','The Cut','Union Street','Long Lane'],[S['Southbank Centre'],S['Borough Market'],S['Shad Thames']],'southbank'))
    return C, C.finish(A)

# ---------------------------------------------------------------- Amsterdam
def build_amsterdam():
    C=City('amsterdam','EPSG:28992'); P=C.P
    bc={f['properties']['name']:fixed(P(shape(f['geometry']))) for f in load('blackmad_amsterdam.geojson')}
    U=lambda *ns: unary_union([bc[n] for n in ns])
    A={}
    A['Jordaan']=('core', U('Jordaan'))
    A['Canal Belt']=('core', U('Grachtengordel-West'))
    A['Grachtengordel']=('core', U('Grachtengordel-Zuid'))
    A['Oud-Zuid']=('core', U('Museumkwartier','Apollobuurt','Willemspark','Stadionbuurt'))
    A['Zuidas']=('core', U('Station-Zuid WTC en omgeving'))   # legacy outline, replaced in geometry.py by Reiwa's selected Noord + Zuid footprint
    A['West']=('selective', U('Frederik Hendrikbuurt','Staatsliedenbuurt','Centrale Markt','Landlust'))
    A['Oud-West']=('selective', U('Helmersbuurt','Vondelbuurt','Da Costabuurt','Kinkerbuurt','Van Lennepbuurt','Overtoomse Sluis'))
    A['Sloterdijk']=('selective', unary_union([U('Sloterdijk'), C.split(U('Bedrijventerrein Sloterdijk'),['Basisweg'],[(4.8380,52.3890),(4.8455,52.3925)],'sloterdijk')]))  # station and Teleport offices north of Basisweg, not the Westpoort port estate
    A['Centrum']=('selective', U('Burgwallen-Oude Zijde','Burgwallen-Nieuwe Zijde','Nieuwmarkt/Lastage','Haarlemmerbuurt'))
    A['Plantage']=('selective', U('Weesperbuurt/Plantage','Oostelijke Eilanden/Kadijken'))
    A['Noord']=('selective', unary_union([U('Ijplein/Vogelbuurt','Volewijck'), U('Buiksloterham')]))  # Volewijck, IJplein/Vogelbuurt and the Buiksloterham regeneration area including Overhoeks and NDSM
    A['Oost']=('selective', U('Weesperzijde','Oosterparkbuurt','Dapperbuurt','Transvaalbuurt','Indische Buurt West'))
    A['De Pijp']=('selective', U('Oude Pijp','Nieuwe Pijp'))
    A['Rivierenbuurt']=('selective', U('Rijnbuurt','Scheldebuurt','IJselbuurt'))
    A['Overamstel']=('selective', U('De Omval'))   # the Overamstel / Omval buurtcombinatie on the east bank of the Amstel
    A['Buitenveldert']=('selective', U('Buitenveldert-Oost','Buitenveldert-West'))
    return C, C.finish(A)

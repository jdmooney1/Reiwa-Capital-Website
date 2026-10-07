"""Reiwa Capital focus maps - drawing stage (v3): SVG frames (wide and tall, one projection), label placement, leaders."""
import json, math, sys, re
import boundaries as bm, clean as build_v2, geometry as v3_geom
from clean import polys, fixed
from shapely.geometry import Polygon, Point, box, mapping, LineString
from shapely.ops import unary_union, linemerge, transform, polylabel
bm.City=build_v2.City

INK='#3D2350'; PLUM='#5E3D78'; SEL='#7A5C92'
COL={'land':'#F7F3EC','park':'#D9E7D0','water':'#BDD3E5','road1':'#D2C7BA','road2':'#E8E1D6','rail':'#D9D1C7'}
FOCUS={'core':dict(fill=PLUM,op=0.30,stroke=INK,w=1.7,dash=None),'sel':dict(fill=PLUM,op=0.12,stroke=SEL,w=1.3,dash='5 3.5')}
GROUPS={
 'london':[
  dict(key='west-end',cls='core',members=['Marylebone','Fitzrovia','Soho','Mayfair',"St James's",'Covent Garden'],en='West End',ja='ウェストエンド'),
  dict(key='midtown',cls='sel',members=['Holborn / Midtown'],en='Midtown',ja='ミッドタウン'),
  dict(key='bloomsbury',cls='sel',members=['Bloomsbury'],en='Bloomsbury',ja='ブルームズベリー',avoid_core=True,rays=True,keep_clear='tall'),
  dict(key='city',cls='sel',members=['City of London'],en='City of<br>London',ja='シティ・オブ・<br>ロンドン'),
  dict(key='westminster',cls='sel',members=['Westminster'],en='Westminster',ja='ウェストミンスター'),
  dict(key='kc',cls='sel',members=['Kensington & Chelsea'],en='Kensington &amp;<br>Chelsea',ja='ケンジントン・<br>チェルシー')],
 'amsterdam':[
  dict(key='jordaan',cls='core',members=['Jordaan'],en='Jordaan',ja='ヨルダーン'),
  dict(key='canal',cls='core',members=['Canal Belt (Grachtengordel)'],en='Canal Belt',ja='カナルベルト'),
  dict(key='oud-zuid',cls='core',members=['Oud-Zuid'],en='Oud-Zuid',ja='アウド・ザウト'),
  dict(key='zuidas',cls='core',members=['Zuidas'],en='Zuidas',ja='ザイダス'),
  dict(key='oud-west',cls='sel',members=['Oud-West'],en='Oud-West',ja='アウド・ウェスト',fixed={'tall':dict(x=20.86,y=41.88,side='b')}),
  dict(key='plantage',cls='sel',members=['Plantage'],en='Weesperbuurt /<br>Plantage',ja='ウェースペルブールト・<br>プランタージュ',fixed={'tall':dict(x=71.92,y=31.83,side='t')}),
  dict(key='de-pijp',cls='sel',members=['De Pijp'],en='De Pijp',ja='デ・パイプ',fixed={'tall':dict(x=55.01,y=59.05,side='r'),'wide':dict(x=53.22,y=61.07,side='c')}),
  dict(key='oost',cls='sel',members=['Oost'],en='Oost',ja='オースト'),
  dict(key='rivieren',cls='sel',members=['Rivierenbuurt'],en='Rivierenbuurt',ja='リヴィエレンブールト')]}
ASPECT={'london':{'wide':0.95,'tall':0.80},'amsterdam':{'wide':1.2,'tall':0.80}}
NOMINAL_W={'wide':420.0,'tall':320.0}     # narrowest width each variant is shown at: labels are laid out for it
PAD={'london':{'wide':330,'tall':560},'amsterdam':{'wide':300,'tall':420}}
FONT=12.0
def label_size(txt,ja):
    lines=txt.split('<br>'); cw=lambda s: sum((1.06 if ord(ch)>0x2e80 else 0.5 if ch in '-' else 0.62) for ch in re.sub('&amp;','&',s))*FONT
    return max(cw(l) for l in lines)+4, len(lines)*FONT*1.3+2

OPEN_R=18.0      # strips narrower than 2x this (road verges left beside a park edge) are not focus area
def dissolve(areas,members):
    g=fixed(unary_union([areas[m][1] for m in members]).buffer(0.6,join_style=2).buffer(-0.6,join_style=2))
    g=fixed(g.buffer(-OPEN_R,join_style=2).buffer(OPEN_R,join_style=2))
    ps=[p for p in polys(g) if p.area>=15000]; return fixed(unary_union(ps)) if ps else g
def frame_for(city,variant,groups):
    allg=unary_union([g for g in groups.values()]); x0,y0,x1,y1=allg.bounds; pad=PAD[city][variant]
    x0-=pad;x1+=pad;y0-=pad;y1+=pad; w,h=x1-x0,y1-y0; asp=ASPECT[city][variant]
    if w/h<asp: d=(h*asp-w)/2; x0-=d; x1+=d
    else: d=(w/asp-h)/2; y0-=d; y1+=d
    return x0,y0,x1,y1
class Frame:
    def __init__(self,b,Wvb=1000.0): self.x0,self.y0,self.x1,self.y1=b; self.W=Wvb; self.s=Wvb/(self.x1-self.x0); self.H=(self.y1-self.y0)*self.s
    def T(self,g): return transform(lambda x,y,z=None:((x-self.x0)*self.s,(self.y1-y)*self.s),g)
    def poly(self): return Polygon([(self.x0,self.y0),(self.x1,self.y0),(self.x1,self.y1),(self.x0,self.y1)])
def d_path(g,dec=0,close=True):
    f=f'{{:.{dec}f}}'
    def ring(cs): return 'M'+'L'.join(f.format(x)+' '+f.format(y) for x,y in cs)+'Z'
    return ''.join(ring(p.exterior.coords)+''.join(ring(i.coords) for i in p.interiors) for p in polys(g))
def d_line(g,dec=0):
    f=f'{{:.{dec}f}}'
    ls=[g] if g.geom_type=='LineString' else list(g.geoms) if g.geom_type in ('MultiLineString','GeometryCollection') else []
    return ''.join('M'+'L'.join(f.format(x)+' '+f.format(y) for x,y in l.coords) for l in ls if l.geom_type=='LineString')

def place_labels(city,variant,fr,groups,meta):
    """groups: key->polygon (metres). Returns key->dict(x,y,side,ax,ay) in percent of the frame."""
    Wpx=NOMINAL_W[variant]; Hpx=Wpx/ASPECT[city][variant]; sx=Wpx/(fr.x1-fr.x0); sy=Hpx/(fr.y1-fr.y0)
    toPx=lambda g: transform(lambda x,y,z=None:((x-fr.x0)*sx,(fr.y1-y)*sy),g)
    PG={k:toPx(g) for k,g in groups.items()}
    frame_box=box(5,5,Wpx-5,Hpx-5)
    order=sorted(meta,key=lambda m:(m['cls']!='core',-PG[m['key']].area))
    placed={}; boxes=[]; leaders=[]
    keep_clear={m['key']:polylabel(max(polys(PG[m['key']]),key=lambda p:p.area),tolerance=0.5).buffer(30) for m in meta if m.get('keep_clear')==variant}   # anchor corridor that other labels keep off
    # `fixed` placements (percent of the frame and the side the label hangs from) are settled first so every other label avoids them; they were
    # found by an exhaustive search against the measured label sizes (EN and JA) and are checked on the rendered pages (tools/maps/README.md).
    for m in meta:
        fx=(m.get('fixed') or {}).get(variant)
        if not fx: continue
        k=m['key']; q=(fx['x']/100*Wpx,fx['y']/100*Hpx); ew,eh=label_size(m['en'],False); jw,jh=label_size(m['ja'],True); w,h=max(ew,jw),max(eh,jh)
        bx={'r':box(q[0],q[1]-h/2,q[0]+w,q[1]+h/2),'l':box(q[0]-w,q[1]-h/2,q[0],q[1]+h/2),'b':box(q[0]-w/2,q[1],q[0]+w/2,q[1]+h),'t':box(q[0]-w/2,q[1]-h,q[0]+w/2,q[1]),'c':box(q[0]-w/2,q[1]-h/2,q[0]+w/2,q[1]+h/2)}[fx['side']]
        boxes.append(bx)
        if fx['side']=='c': placed[k]=dict(x=fx['x'],y=fx['y'],side='c',ax=None,ay=None,inside=True); continue     # centred inside its own area, no leader
        pl=polylabel(max(polys(PG[k]),key=lambda p:p.area),tolerance=0.5); leaders.append(LineString([(pl.x,pl.y),q]))
        placed[k]=dict(x=fx['x'],y=fx['y'],side=fx['side'],ax=round(pl.x/Wpx*100,2),ay=round(pl.y/Hpx*100,2),inside=False)
    for m in order:
        if m['key'] in placed: continue
        k=m['key']; P=PG[k]
        ew,eh=label_size(m['en'],False); jw,jh=label_size(m['ja'],True); w,h=max(ew,jw),max(eh,jh)
        big=max(polys(P),key=lambda p:p.area); pole=polylabel(big,tolerance=0.5)
        best=None
        # 1. inside: grid search for the box centre with the most clearance
        minx,miny,maxx,maxy=big.bounds; inner=P.buffer(-1.0)
        cands=[]
        x=minx
        while x<=maxx:
            y=miny
            while y<=maxy:
                b=box(x-w/2,y-h/2,x+w/2,y+h/2)
                if inner.intersection(b).area>=0.93*b.area and frame_box.contains(b) and not any(b.buffer(2).intersects(o) for o in boxes) and not any(b.buffer(1).intersects(ld) for ld in leaders) and not any(b.intersects(c) for kk,c in keep_clear.items() if kk!=k):
                    cands.append((-(P.exterior.distance(Point(x,y)) if P.geom_type=='Polygon' else min(p.exterior.distance(Point(x,y)) for p in polys(P))) ,math.hypot(x-pole.x,y-pole.y),x,y))
                y+=2
            x+=2
        if cands:
            cands.sort(); _,_,x,y=cands[0]; best=dict(side='c',cx=x,cy=y,bx=box(x-w/2,y-h/2,x+w/2,y+h/2),ax=None,ay=None)
        else:
            # 2. outside, with a leader from the pole of the area
            ring=big.exterior; L=ring.length; cand=[]
            others=unary_union([PG[o] for o in PG if o!=k])
            cores=unary_union([PG[mm['key']] for mm in meta if mm['cls']=='core' and mm['key']!=k])
            n=int(L/4)
            for i in range(n):
                q=ring.interpolate(i*4.0); q2=ring.interpolate(i*4.0+1.5)
                tx,ty=q2.x-q.x,q2.y-q.y; tl=math.hypot(tx,ty) or 1; nx,ny=ty/tl,-tx/tl
                if big.contains(Point(q.x+nx*2,q.y+ny*2)): nx,ny=-nx,-ny
                for d in (9,16,24):
                    lx,ly=q.x+nx*d,q.y+ny*d
                    if abs(nx)>=abs(ny): side='r' if nx>0 else 'l'
                    else: side='b' if ny>0 else 't'
                    bx={'r':box(lx,ly-h/2,lx+w,ly+h/2),'l':box(lx-w,ly-h/2,lx,ly+h/2),'b':box(lx-w/2,ly,lx+w/2,ly+h),'t':box(lx-w/2,ly-h,lx+w/2,ly)}[side]
                    if not frame_box.contains(bx) or any(bx.buffer(2).intersects(o) for o in boxes): continue
                    ov=bx.intersection(others).area/bx.area; selfov=bx.intersection(P).area/bx.area
                    cross=any(bx.buffer(1).intersects(ld) for ld in leaders) or any(LineString([(pole.x,pole.y),(lx,ly)]).intersects(o.buffer(1)) for o in boxes)   # a leader should not cross another label
                    ovc=bx.intersection(cores).area/bx.area                      # avoid_core labels must not sit on a core area
                    thr=LineString([(pole.x,pole.y),(lx,ly)]).intersection(others).length   # nor should their leader run through another area
                    score=math.hypot(lx-pole.x,ly-pole.y)+260*ov+120*selfov+0.3*d+(400 if cross else 0)+700*sum(bx.intersects(c) for kk,c in keep_clear.items() if kk!=k)+(1500*ovc+2.5*thr if m.get('avoid_core') else 0)
                    cand.append((score,lx,ly,side,bx))
            if m.get('rays'):   # a second family for areas hemmed in by their neighbours: straight rays from the pole
                for ang in range(0,360,15):
                    nx,ny=math.cos(math.radians(ang)),-math.sin(math.radians(ang))
                    for d in (34,46,60,76,94):
                        lx,ly=pole.x+nx*d,pole.y+ny*d
                        if abs(nx)>=abs(ny): side='r' if nx>0 else 'l'
                        else: side='b' if ny>0 else 't'
                        bx={'r':box(lx,ly-h/2,lx+w,ly+h/2),'l':box(lx-w,ly-h/2,lx,ly+h/2),'b':box(lx-w/2,ly,lx+w/2,ly+h),'t':box(lx-w/2,ly-h,lx+w/2,ly)}[side]
                        if not frame_box.contains(bx) or any(bx.buffer(2).intersects(o) for o in boxes): continue
                        ov=bx.intersection(others).area/bx.area; selfov=bx.intersection(P).area/bx.area
                        ld=LineString([(pole.x,pole.y),(lx,ly)])
                        cross=any(bx.buffer(1).intersects(l2) for l2 in leaders) or any(ld.intersects(o.buffer(1)) for o in boxes)
                        ovc=bx.intersection(cores).area/bx.area
                        score=d+260*ov+120*selfov+(900 if cross else 0)+700*sum(bx.intersects(c) for kk,c in keep_clear.items() if kk!=k)+(1500*ovc+2.5*ld.intersection(others).length if m.get('avoid_core') else 0)+8
                        cand.append((score,lx,ly,side,bx))
            if not cand: print('  WARNING: no place for',k); best=dict(side='c',cx=pole.x,cy=pole.y,bx=box(pole.x-w/2,pole.y-h/2,pole.x+w/2,pole.y+h/2),ax=None,ay=None)
            else:
                cand.sort(key=lambda c:c[0]); _,lx,ly,side,bx=cand[0]; best=dict(side=side,cx=lx,cy=ly,bx=bx,ax=pole.x,ay=pole.y)
        boxes.append(best['bx'])
        if best['ax'] is not None: leaders.append(LineString([(best['ax'],best['ay']),(best['cx'],best['cy'])]))
        placed[k]=dict(x=round(best['cx']/Wpx*100,2),y=round(best['cy']/Hpx*100,2),side=best['side'],
                       ax=None if best['ax'] is None else round(best['ax']/Wpx*100,2),ay=None if best['ay'] is None else round(best['ay']/Hpx*100,2),
                       inside=best['side']=='c')
    return placed

def render(C,areas,city,variant,groups,meta,labels,fn,header):
    fr=Frame(frame_for(city,variant,groups)); T=fr.T; frame=fr.poly(); W,H=fr.W,fr.H
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.1f}" preserveAspectRatio="xMidYMid slice" role="presentation">',header,f'<rect width="{W:.0f}" height="{H:.1f}" fill="{COL["land"]}"/>']
    greens=[g for n,g in C.parks if g.area/1e4>=0.5]+[g for n,g in C.mask_parks]
    o.append(f'<g fill="{COL["park"]}">'+''.join(f'<path d="{d_path(fixed(g.intersection(frame)).simplify(3),0) if False else d_path(T(fixed(g.intersection(frame)).simplify(3)))}"/>' for g in greens if g.intersects(frame))+'</g>')
    o.append(f'<g fill="{COL["water"]}">'+''.join(f'<path d="{d_path(T(fixed(g.intersection(frame)).simplify(6)))}"/>' for p,g in C.water_polys if g.area/1e4>=0.5 and p['subtype']!='human_made' and g.intersects(frame))+'</g>')
    o.append(f'<g fill="none" stroke="{COL["water"]}" stroke-width="1" vector-effect="non-scaling-stroke">'+''.join(f'<path d="{d_line(T(g.intersection(frame).simplify(3)))}"/>' for p,g in C.water_lines if p['class'] in ('canal','river') and g.intersects(frame))+'</g>')
    def roads(classes,col,w):
        ls=[g.intersection(frame).simplify(8) for p,g in C.roads if p['subtype']=='road' and p['class'] in classes and g.intersects(frame)]
        return f'<g fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" vector-effect="non-scaling-stroke">'+''.join(f'<path d="{d_line(T(g))}"/>' for g in ls)+'</g>'
    rl=[g.intersection(frame).simplify(5) for p,g in C.roads if p['subtype']=='rail' and p['class']=='standard_gauge' and g.intersects(frame)]
    o.append(f'<g fill="none" stroke="{COL["rail"]}" stroke-width="1" stroke-dasharray="3 2" vector-effect="non-scaling-stroke">'+''.join(f'<path d="{d_line(T(g))}"/>' for g in rl)+'</g>')
    o.append(roads(('tertiary',),COL['road2'],0.7)); o.append(roads(('motorway','trunk','primary','secondary'),COL['road1'],1.2))
    for m in meta:
        f=FOCUS[m['cls']]; o.append(f'<path d="{d_path(T(groups[m["key"]]),1)}" fill="{f["fill"]}" fill-opacity="{f["op"]}"/>')
    if C.canals: o.append(f'<g fill="none" stroke="{COL["water"]}" stroke-width="1.7" stroke-linecap="round" vector-effect="non-scaling-stroke">'+''.join(f'<path d="{d_line(T(g.intersection(frame)))}"/>' for g in C.canals if g.intersects(frame))+'</g>')
    for m in meta:      # outline: a pale halo under the line keeps it crisp over roads
        f=FOCUS[m['cls']]; d=d_path(T(groups[m['key']]),1)
        o.append(f'<path d="{d}" fill="none" stroke="{COL["land"]}" stroke-opacity="0.85" stroke-width="{f["w"]+2.4}" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="{d}" fill="none" stroke="{f["stroke"]}" stroke-width="{f["w"]}" stroke-linejoin="round"'+(f' stroke-dasharray="{f["dash"]}"' if f['dash'] else '')+' vector-effect="non-scaling-stroke"/>')
    # leaders
    Wpx=NOMINAL_W[variant]; Hpx=Wpx/ASPECT[city][variant]; k=W/Wpx
    for m in meta:
        L=labels[m['key']]
        if L['ax'] is None: continue
        ax,ay=L['ax']/100*W,L['ay']/100*H; lx,ly=L['x']/100*W,L['y']/100*H
        dx,dy=lx-ax,ly-ay; dist=math.hypot(dx,dy) or 1; gap=2.0*k
        ex,ey=lx-dx/dist*gap,ly-dy/dist*gap
        o.append(f'<path d="M{ax:.1f} {ay:.1f}L{ex:.1f} {ey:.1f}" fill="none" stroke="{INK}" stroke-width="1" vector-effect="non-scaling-stroke"/>')
        o.append(f'<path d="M{ax:.1f} {ay:.1f}h0.01" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" vector-effect="non-scaling-stroke"/>')
    o.append('</svg>'); svg='\n'.join(o); open(fn,'w',encoding='utf-8').write(svg)
    return fr,len(svg)

HEADER={'london':"""<!--
  Reiwa Capital - London focus map (indicative investment focus areas; not administrative boundaries).
  Base: ONS Wards (December 2013) and Local Authority Districts (City of London), Open Geography Portal, OGL v3.0 (mirror martinjc/UK-GeoJSON);
  Overture Maps Foundation release 2026-08-19.0 transportation, land_use and water layers, ODbL 1.0, (c) OpenStreetMap contributors.
  Focus areas: Reiwa-defined market areas built from those wards, divided along named streets (see docs/map-geography.md); one projection
  (EPSG:27700) for base, areas, leaders and labels in both frames. Built by tools/maps/build.py.
-->""",'amsterdam':"""<!--
  Reiwa Capital - Amsterdam focus map (indicative investment focus areas; not administrative boundaries).
  Areas: Gemeente Amsterdam buurtcombinaties (legacy boundary set, CC0, mirror blackmad/neighborhoods) checked against the CBS Wijk- en buurtkaart
  2022 (CC BY 4.0); Zuidas is Reiwa's selected Noord + Zuid footprint (CBS 2022 buurten Zuidas Noord and Zuidas Zuid), not an official boundary. Base: Overture Maps Foundation release 2026-08-19.0
  transportation, land_use and water layers, ODbL 1.0, (c) OpenStreetMap contributors. One projection (EPSG:28992) for base, areas, leaders
  and labels in both frames. Built by tools/maps/build.py.
-->"""}
def build_city(city,outdir):
    C,areas=v3_geom.build(city)
    meta=GROUPS[city]; groups={m['key']:dissolve(areas,m['members']) for m in meta}
    res={'labels':{},'frames':{}}
    for variant in ('wide','tall'):
        fr0=Frame(frame_for(city,variant,groups))
        labels=place_labels(city,variant,fr0,groups,meta)
        fr,n=render(C,areas,city,variant,groups,meta,labels,f'{outdir}/{city}-{variant}.svg',HEADER[city])
        res['labels'][variant]=labels; res['frames'][variant]=dict(viewBox=f'0 0 {fr.W:.0f} {fr.H:.1f}',bbox=[fr.x0,fr.y0,fr.x1,fr.y1],bytes=n)
        print(city,variant,f'{n//1024} KB',res['frames'][variant]['viewBox'])
    res['members']={k:{'class':c,'geom':mapping(g)} for k,(c,g) in areas.items()}
    res['groups']={m['key']:{'cls':m['cls'],'members':m['members'],'km2':round(groups[m['key']].area/1e6,2)} for m in meta}
    res['audit']={'given':[list(x) for x in sorted(C.given,reverse=True)],'unclaimed':[list(x) for x in sorted(C.unclaimed,reverse=True)],'ha':{k:round(g.area/1e4,1) for k,g in groups.items()},'cleanup':[list(x) for x in getattr(C,'cleanup_log',[])],'fragments':[{k:v for k,v in f.items() if k!='wkb'} for f in getattr(C,'fragment_log',[])]}
    return res,areas,groups,C

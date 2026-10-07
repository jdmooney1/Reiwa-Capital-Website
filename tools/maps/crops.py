"""Focused crops of London ward fragments over the street geography, for review. Used by audit.py when CROPS_DIR is set.
Purple = current focus areas (solid core, thinner selective); red = the fragment; green = the part of L02 west of the Lancaster Place cut."""
import os
from shapely import wkb
from shapely.geometry import box, Polygon
from PIL import Image, ImageDraw, ImageFont
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf']
FONTSB=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf']
def font(paths,size):
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
def polys(g): return [g] if g.geom_type=='Polygon' else list(g.geoms) if g.geom_type=='MultiPolygon' else []
def lines(g): return [g] if g.geom_type=='LineString' else list(g.geoms) if g.geom_type in ('MultiLineString','GeometryCollection') else []
def crop(C,areas,name,cx,cy,half,frag_ids,frags,title,outdir,split_x=None):
    W=1200; k=W/(2*half); win=box(cx-half,cy-half,cx+half,cy+half); F=font(FONTS,15); FB=font(FONTSB,17)
    T=lambda x,y:((x-(cx-half))*k,(cy+half-y)*k)
    im=Image.new('RGB',(W,W),(247,243,236)); d=ImageDraw.Draw(im,'RGBA')
    for lst,col in ((C.mask_parks,(217,231,208,255)),(C.mask_water,(189,211,229,255))):
        for _n,g in lst:
            if g.intersects(win):
                for p in polys(g.intersection(win)): d.polygon([T(*c) for c in p.exterior.coords],fill=col)
    named={}
    for p,g in C.roads:
        if p.get('subtype')!='road' or not g.intersects(win): continue
        cl=p.get('class'); w=3 if cl in ('primary','secondary','trunk') else 2 if cl=='tertiary' else 1
        for l in lines(g.intersection(win)): d.line([T(*c) for c in l.coords],fill=(190,178,164,255),width=w)
        if p.get('name') and cl in ('primary','secondary','trunk','tertiary'): named.setdefault(p['name'],[]).append(g.intersection(win))
    for k2,(cls,g) in areas.items():
        if not g.intersects(win): continue
        col=(94,61,120)
        for p in polys(g.intersection(win)):
            d.polygon([T(*c) for c in p.exterior.coords],fill=col+(52 if cls=='core' else 26,)); d.line([T(*c) for c in p.exterior.coords],fill=col+(255,),width=3 if cls=='core' else 2)
        r=g.intersection(win)
        if not r.is_empty:
            x,y=T(*r.representative_point().coords[0]); d.text((x-30,y-8),k2,font=FB,fill=(61,35,80,255))
    for fid in frag_ids:
        g=wkb.loads(bytes.fromhex(frags[fid]['wkb']))
        parts=[(g,(220,40,40))]
        if split_x is not None:
            e=g.intersection(Polygon([(split_x,cy-9*half),(cx+9*half,cy-9*half),(cx+9*half,cy+9*half),(split_x,cy+9*half)])); parts=[(e,(220,40,40)),(g.difference(e),(30,150,80))]
        for gg,c in parts:
            for p in polys(gg.intersection(win)):
                d.polygon([T(*q) for q in p.exterior.coords],fill=c+(70,)); d.line([T(*q) for q in p.exterior.coords],fill=c+(255,),width=3)
    for n,gs in named.items():
        ls=[l for g in gs for l in lines(g)]
        best=max(ls,key=lambda l:l.length,default=None)
        if best is None or best.length<80: continue
        pt=best.interpolate(0.5,normalized=True); x,y=T(pt.x,pt.y)
        if 20<x<W-120 and 40<y<W-20:
            d.text((x+3,y+2),n,font=F,fill=(255,255,255,255),stroke_width=3,stroke_fill=(255,255,255,255)); d.text((x+3,y+2),n,font=F,fill=(70,60,60,255))
    d.rectangle([0,0,W,34],fill=(255,255,255,235)); d.text((8,6),title,font=FB,fill=(30,20,40,255))
    os.makedirs(outdir,exist_ok=True); im.save(os.path.join(outdir,name+'.png'))
def run(C,areas,frags,outdir):
    sx=C.P(__import__('shapely.geometry',fromlist=['Point']).Point(-0.1178,51.5112)).x
    crop(C,areas,'L02e-aldwych-midtown-UNRESOLVED',530700,180950,900,['L02'],frags,'L02e (red, 18.8 ha) held by Midtown: UNRESOLVED.  L02w (green, 14.6 ha) held by Covent Garden: supported',outdir,split_x=sx)
    crop(C,areas,'L01-leicester-square',529750,180700,700,['L01'],frags,'L01 (11.3 ha): Leicester Square, held by Covent Garden; inside the outline',outdir)
    crop(C,areas,'L13-oxford-regent-street',528950,181000,800,['L13'],frags,'L13 (9.7 ha): Oxford Street and Regent Street ground, held by Soho',outdir)
    crop(C,areas,'L17-fitzroy-square',529350,182000,700,['L17'],frags,'L17 (12.7 ha): Bloomsbury ward west of Tottenham Court Rd, held by Fitzrovia',outdir)
    crop(C,areas,'L14-hatton-garden',531200,181800,650,['L14'],frags,'L14 (1.2 ha): Hatton Garden (EC1N), outside the coverage; a candidate for Midtown',outdir)
    crop(C,areas,'L22-finsbury-square',532700,182000,700,['L22','L21'],frags,'L22 (7.9 ha) Finsbury Square, L21 (2.3 ha) Old Street: outside the coverage',outdir)
    if 'D1' in frags:
        g=wkb.loads(bytes.fromhex(frags['D1']['wkb'])); c=g.representative_point()
        crop(C,areas,'D1-detached-westminster-park-lane',c.x,c.y,1200,['D1'],frags,'D1 (12.2 ha, 3.1 ha inside the final coverage): road corridor round Hyde Park, taken by Mayfair',outdir)

def before_after(C,areas,name,piece_wkb,cx,cy,half,title,outdir):
    """Side-by-side crop: left = the areas with the removed piece (red), right = the areas as they are now."""
    import tempfile
    g=wkb.loads(bytes.fromhex(piece_wkb)); before=dict(areas); before['added by cleanup']=('sel',g)
    with tempfile.TemporaryDirectory() as tmp:
        crop(C,before,'b',cx,cy,half,['X'],{'X':{'wkb':piece_wkb}},'BEFORE: '+title+' (red)',tmp)
        crop(C,areas,'a',cx,cy,half,[],{},'AFTER: removed',tmp)
        a=Image.open(os.path.join(tmp,'b.png')).resize((800,800)); b=Image.open(os.path.join(tmp,'a.png')).resize((800,800))
        im=Image.new('RGB',(1610,800),(255,255,255)); im.paste(a,(0,0)); im.paste(b,(810,0))
        os.makedirs(outdir,exist_ok=True); im.save(os.path.join(outdir,name+'.png'))

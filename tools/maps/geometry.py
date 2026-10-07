"""Reiwa Capital focus maps - geometry stage (v3).
Builds the approved focus areas for London and Amsterdam from published boundary data, as selected and combined by Reiwa, and writes them, projected, with a
provenance record for every area. Differences from the 2026-10 release (documented in docs/map-geography.md):
  Amsterdam  Zuidas = Reiwa's selected footprint: the CBS Wijk- en buurtkaart 2022 buurten Zuidas Noord and Zuidas Zuid together, which
             straddle the A10. It is a selection by Reiwa, not an official boundary: the official Zuidas description
             (zuidas.nl/en/about-zuidas, cited by the commissioner, not fetched here) states approximately 245 ha and the two CBS units are
             smaller. No further CBS units are added to approach that figure. The earlier outline was the pre-2015 'Station Zuid / WTC en
             omgeving' area north of the A10 only.
             Canal Belt = Grachtengordel-West + Grachtengordel-Zuid only (the De Weteringschans buurtcombinatie, 65 ha, had been added to close a gap).
             Oud-Zuid no longer takes Duivelseiland. Only approved areas take part in the seam/gap clean-up.
             Plantage = the legacy buurtcombinatie Weesperbuurt/Plantage only (displayed as Weesperbuurt / Plantage). The Oostelijke
             Eilanden/Kadijken buurtcombinatie, drawn as part of Plantage until this pass, is no longer included.
  London     unchanged geometry; sub-areas of the West End are kept apart here and dissolved when drawn."""
import sys, json, os
import boundaries as bm, clean as build_v2
from boundaries import load
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
bm.City=build_v2.City
from clean import fixed, polys
import coverage_rules
LON_KEEP=['Marylebone','Fitzrovia','Soho','Mayfair',"St James's",'Covent Garden','Holborn / Midtown','Bloomsbury','City of London','Kensington & Chelsea','Westminster']
KC=['Hans Town','Brompton',"Queen's Gate",'Royal Hospital','Stanley','Cremorne','Redcliffe','Courtfield','Abingdon','Campden','Holland']
WMW=('Tachbrook','Warwick','Knightsbridge and Belgravia')
AMS_KEEP=['Jordaan','Canal Belt','Grachtengordel','Oud-Zuid','Zuidas','Oud-West','Plantage','De Pijp','Oost','Rivierenbuurt']
orig_adjust=build_v2.City.adjust
def adjust(self,areas):
    if self.name=='london':
        a=orig_adjust(self,areas)
        ws=load('wards_E09000020.json')
        a['Kensington & Chelsea']=('selective',unary_union([fixed(self.P(shape(f['geometry']))) for f in ws if f['properties']['WD13NM'] in KC]))
        wm=[fixed(self.P(shape(f['geometry']))) for f in load('wards_E09000033.json') if f['properties']['WD13NM'] in WMW]
        a['Westminster']=('selective',unary_union([a['Westminster'][1]]+wm))
        return a
    self.parents=[]; self.parent_names=[]
    bc={f['properties']['name']:fixed(self.P(shape(f['geometry']))) for f in load('blackmad_amsterdam.geojson')}
    cbs={f['properties']['statnaam']:fixed(self.P(shape(f['geometry']))) for f in load('ams-cbs.geojson')}
    out={k:areas[k] for k in AMS_KEEP if k in areas}
    out['Zuidas']=('core',unary_union([cbs['Zuidas Noord'],cbs['Zuidas Zuid']]))
    out['De Pijp']=('selective',fixed(unary_union([out['De Pijp'][1],bc['Diamantbuurt']])))   # Diamantbuurt lies in the official 'Zuid Pijp' wijk
    out['Oud-Zuid']=('core',areas['Oud-Zuid'][1])
    out['Plantage']=('selective',fixed(bc['Weesperbuurt/Plantage']))      # not Oostelijke Eilanden/Kadijken: the Eastern Islands are outside this focus area
    return out
build_v2.City.adjust=adjust
orig_finish=build_v2.City.finish
def finish(self,areas):
    out=orig_finish(self,areas)
    if self.name=='london':
        out={k:v for k,v in out.items() if k in LON_KEEP}
        # Mayfair is the West End ward south of Oxford Street and west of Regent Street: gap-closing that had spilled it along
        # Bayswater Road and into Hyde Park Corner (9 ha outside the ward) is clipped back to the ward plus 25 m.
        we=[f for f in load('wards_E09000033.json') if f['properties']['WD13NM']=='West End'][0]
        out['Mayfair']=('core',fixed(out['Mayfair'][1].intersection(fixed(self.P(shape(we['geometry']))).buffer(25))))
        out['City of London']=('selective',out['City of London'][1])
    else:
        out['Canal Belt (Grachtengordel)']=('core',fixed(unary_union([out.pop('Canal Belt')[1],out.pop('Grachtengordel')[1]])))
    return coverage_rules.constrain(self,out,fixed,build_v2.keep_parts,build_v2.MIN_PART)       # retained coverage plus the recorded seam and gap allowances only (coverage_rules.py)
build_v2.City.finish=finish
build_v2.OPEN['Rivierenbuurt']=30
def build(city):
    return bm.build_london() if city=='london' else bm.build_amsterdam()

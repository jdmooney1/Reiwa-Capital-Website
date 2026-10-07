# About-page focus maps: geography, sources and definitions

The London and Amsterdam maps on About show **indicative investment focus areas**. They are not administrative boundaries. The notes under the maps say only that, plus the required attribution; every definition lives here. Each area is one of three kinds:

- **Administrative**: an official boundary used as published (City of London).
- **Official unit(s)**: a union of official statistical or administrative units that corresponds to a recognised market area (Amsterdam buurtcombinaties; London wards).
- **Reiwa-defined**: a market area with no official boundary, drawn from official units divided along named streets and described here by its streets and landmarks. These are approximate.

The areas are **Reiwa's market definitions, not the sources' boundaries.** A newer ward or buurt set must not move them. `tools/maps/sources.json` pins every input by SHA-256 and vintage, and `tools/maps/build.py` refuses to build from an input that differs unless `ACCEPT_NEW_SOURCES=1` is set. A new vintage is therefore a reviewed change: re-run `tools/maps/audit.py`, compare, update this file and `sources.json`, then rebuild. Ground that a ward cut leaves over (a ward fragment) is no longer given to a neighbour by shared edge length: each of the 25 fragments is decided one by one in `tools/maps/london_fragments.py` (see "Ward fragments" below), and the build stops if a new vintage produces a fragment that is not listed.

`tools/maps/build.py` rebuilds the SVGs, labels, `*-focus.js` and the About-page markup. One projection per city (EPSG:27700 London, EPSG:28992 Amsterdam) is used for the base map, the areas, the leader lines and the label positions, in both the wide and the tall frame. `tools/maps/audit.py` reproduces every figure in this file and writes `docs/map-audit.json`.

## Four kinds of boundary, kept apart

| Kind | Examples here | Role in the maps |
|---|---|---|
| **Reiwa-defined market area** | West End (six areas), Midtown, Bloomsbury, Westminster, Kensington & Chelsea, Weesperbuurt / Plantage, Zuidas (selected footprint) | What is drawn and what Reiwa means by a market. Built from official units divided along named streets. |
| **Administrative boundary** | ONS wards (December 2013), City of London local authority district, Gemeente Amsterdam buurtcombinaties, CBS 2022 wijken and buurten | Raw material and cross-check. A new vintage must not move a market. |
| **BID footprint** | Midtown BID (inmidtown); no other BID is used | Not used. The Midtown BID boundary could not be retrieved, so Reiwa's Midtown is not claimed to match it. |
| **Community or amenity-society area** | Covent Garden Community Association (CGCA) published area | Supporting evidence only. Not a ward, not a BID and not Reiwa's. |

## Sources and boundary dates

| Layer | Source | Boundary date / release | Licence |
|---|---|---|---|
| London wards | ONS Wards (December 2013), Open Geography Portal, via the martinjc/UK-GeoJSON mirror | 31 Dec 2013 (WD13) | OGL v3.0 |
| City of London | ONS Local Authority Districts, same mirror | same set; LAD vintage not stated | OGL v3.0 |
| Amsterdam areas | Gemeente Amsterdam gebiedsindeling, buurtcombinaties, via the blackmad/neighborhoods mirror | legacy set; vintage not stated by the mirror | CC0 |
| Amsterdam check and Zuidas | CBS Wijk- en buurtkaart 2022 (gegeneraliseerd), buurten and wijken, PDOK. Amsterdam (GM0363) extract in `cbs2022_amsterdam_*.geojson` | 1 Jan 2022 | CC BY 4.0 |
| Roads, rail, parks, water | Overture Maps Foundation, release 2026-08-19.0 (transportation, base/land_use, base/water), bounding-box extracts. **Regenerated replacement inputs, not the original files**: see "Replacement Overture inputs" | 2026-08-19 | ODbL 1.0, (c) OpenStreetMap contributors |

**Not reachable from the build environment (network egress policy), so nothing here was taken from them:** the official Zuidas pages (zuidas.nl/en/about-zuidas, zuidas.nl/en/buurten), the Gemeente Amsterdam page on Centrum districts (amsterdam.nl/stadsdelen/centrum/centrum-begroot), the Gemeente Amsterdam gebieden API, the GLA London Datastore, the City of Westminster ward map, the Covent Garden Community Association site and the Midtown BID map. The commissioner supplied three pages as references (zuidas.nl/en/about-zuidas, amsterdam.nl/stadsdelen/centrum/centrum-begroot and coventgarden.org.uk/about/governance) and cited two statements from them: that CGCA's published constitution explicitly includes Victoria Embankment, and that the official Zuidas description states approximately 245 hectares. Both are recorded here **as cited by the commissioner**, not as checked in this build; where this file otherwise cites a web search, it says so and treats it as secondary.

## Approved coverage and classification

London core (6): Marylebone, Fitzrovia, Soho, Mayfair, St James's, Covent Garden (drawn as one "West End"). London selective (5): Holborn / Midtown, Bloomsbury, City of London, Westminster, Kensington & Chelsea.
Amsterdam core (4): Canal Belt (Grachtengordel), Jordaan, Oud-Zuid, Zuidas. Amsterdam selective (5): Oud-West, Weesperbuurt / Plantage, De Pijp, Oost, Rivierenbuurt.
All 20 are present in `assets/maps/*-focus.js`, drawn and labelled (Amsterdam: nine labels; London: six, with the West End composition in the note under the map).

## London

Street check: the share of each boundary that lies within 20 m of a named Overture road (release 2026-08-19.0), from `tools/maps/audit.py`. All eleven areas are single polygons; only Westminster has holes (two, both parks or water cut out).

| Area | Kind | Definition used | Class | ha | Boundary on named roads | Uncertainty |
|---|---|---|---|---|---|---|
| West End (6 areas) | Reiwa-defined market area | Union of the six areas below. Not the West End ward. Spans Edgware Road and Park Lane (west), Marylebone Road and Euston Road (north), Tottenham Court Road to Kingsway and Aldwych (east). The southern edge runs along Piccadilly, the Mall and Cockspur Street in the west, and reaches Victoria Embankment between Northumberland Avenue and Waterloo Bridge (see "Covent Garden south of the Strand") | Core | 522 | see areas | Indicative |
| Marylebone | Official units | Marylebone High Street + Bryanston and Dorset Square wards (2013) | Core | 173 | 100% (Edgware Road, Marylebone Road, Oxford Street) | 2013 wards pre-date the 2022 Westminster review |
| Fitzrovia | Reiwa-defined | West End ward north of Oxford Street + Bloomsbury ward west of Tottenham Court Road (seeds: Charlotte Street, Fitzroy Square) | Core | 64 | 96% | Indicative |
| Soho | Reiwa-defined | West End ward east of Regent Street and south of Oxford Street (seeds: Soho Square, Carnaby Street) | Core | 49 | 97% | Southern and eastern limits are the ward's |
| Mayfair | Reiwa-defined | West End ward west of Regent Street and south of Oxford Street (seeds: Grosvenor Square, Berkeley Square); Hyde Park masked; clipped to the ward plus 25 m | Core | 117 | 92% (Piccadilly, Oxford Street, Regent Street, Park Lane) | Indicative |
| St James's | Reiwa-defined | St James's ward cut along Piccadilly, Haymarket, Coventry Street, Cranbourn Street, Charing Cross Road, the Mall, Cockspur Street, Constitution Hill, Northumberland Avenue, the Strand and Whitehall; keeps Pall Mall, St James's Square, Jermyn Street | Core | 37 | 99% | Indicative |
| Covent Garden | Reiwa-defined | St James's ward faces holding Covent Garden piazza, the Strand, Trafalgar Square and Leicester Square + Holborn and Covent Garden ward west of Kingsway, plus ward fragments L01, L02w and L05 (see below) | Core | 82 | 90% (Victoria Embankment, Shaftesbury Avenue, Strand, Kingsway) | Indicative; extends to Victoria Embankment, as the CGCA area does |
| Holborn / Midtown | Reiwa-defined | Holborn and Covent Garden ward after Covent Garden, Bloomsbury and Farringdon pieces: High Holborn to Theobalds Road, Kingsway to Gray's Inn Road (Lincoln's Inn, Red Lion Square), plus the Aldwych piece (L02e, unresolved). Not the Midtown BID boundary (not retrieved) | Selective | 118 | 92% (Victoria Embankment, Gray's Inn Road, Guilford Street, Clerkenwell Road, Strand) | Aldwych piece: see below |
| Bloomsbury | Reiwa-defined | Bloomsbury ward east of Tottenham Court Road (Russell Square) + the Bloomsbury Square piece of Holborn and Covent Garden ward | Selective | 78 | 99% | Indicative |
| City of London | Administrative | ONS LAD boundary, Thames removed | Selective | 289 | 97% | Vintage of the mirror's LAD set not stated |
| Westminster | Reiwa-defined | Southern Westminster (SW1): Whitehall, Parliament Square, Victoria Street, Buckingham Gate (St James's ward south of the cut) + Vincent Square, Tachbrook, Warwick, Knightsbridge and Belgravia wards. Not the borough and not the West End | Selective | 384 | 89% (the Mall, Birdcage Walk, Constitution Hill, Buckingham Palace Road) | Includes Belgravia and Knightsbridge |
| Kensington & Chelsea | Reiwa-defined | 11 of the borough's 21 wards (2013): Hans Town, Brompton, Queen's Gate, Royal Hospital, Stanley, Cremorne, Redcliffe, Courtfield, Abingdon, Campden, Holland. Not the whole borough | Selective | 766 | 79% (Holland Park Avenue, Chelsea Embankment, Notting Hill Gate, Queen's Gate) | Pre-dates the 2018 K&C ward review; the lowest street support, because ward lines follow back streets |

### Ward fragments: 25 explicit decisions

Cutting a ward along named streets leaves fragments, ground of that ward that no focus area took. An earlier build gave each fragment under 40 ha to whichever neighbour shared the longest edge, so ward geometry decided which ground became investment coverage. **That rule is gone.** `tools/maps/london_fragments.py` lists all 25 fragments of the December 2013 wards, each with the area that holds it, the named streets that bound it, a status and the basis; the full table, with how much each adds to the outline, is `docs/london-ward-fragments.md`. The build stops with the fragment's size and position if one is not listed, and if a listed one no longer exists.

- **Only one fragment changes the outline.** L02 (33.3 ha, the Strand, Aldwych and the Embankment) adds ground to the coverage. The other 24 either lie inside the outline of the rest of the coverage (so they decide only which of the six West End areas holds ground that is already surrounded) or stay outside it.
- **Statuses.** Supported: L01 Leicester Square (11.3 ha), L02w Charing Cross to Lancaster Place (14.6 ha), L17 Fitzroy Square to Euston Road (12.7 ha). Closure (road corridors and slivers between areas or against a park edge): L03 to L13 and L15, L16. Excluded (outside the coverage): L14 Hatton Garden, L18 to L25, including Finsbury Square (L22, 7.9 ha) and the two large remainders (85.6 ha, 63.9 ha). **Unresolved: L02e (18.8 ha).**
- **Detached parts.** After the park and water masks, one detached part of 0.5 ha or more is left, 12.2 ha of Westminster ground round Hyde Park (D1), of which 3.1 ha is the Park Lane carriageway and verge that Mayfair's western edge runs along. It is listed explicitly and taken by Mayfair; the rest falls outside the coverage.
- **What still uses edge length, and what it may add.** The build still uses shared-edge length to *allocate* ground that is already retained: notches and gaps under 3 ha between areas that already touch, hairline faces and detached parts under 0.5 ha (289 pieces, 18.2 ha logged in London; 127 pieces, 1.1 ha in Amsterdam; none a ward fragment). **It does not authorise coverage by itself.** Since 7 October 2026 every area is cut back to the retained coverage plus two recorded allowances, a seam allowance and a list of enclosed gaps (see "Coverage-union audit" below). Those allowances do add some ground beyond the retained coverage (London 3.63 ha seam, 1.02 ha gaps; Amsterdam 0.62 ha seam, 0.12 ha gaps); the cleanup's additions outside them were removed (London 4.57 ha, Amsterdam 3.36 ha).
- **Coverage check.** With the 25 decisions and the replacement inputs, the London focus-area outlines (`london-focus.js`) are byte-identical to the delivered checkpoint's. The decisions therefore record the coverage the maps already had; they do not change it.

### Aldwych piece L02e (Holborn / Midtown): unresolved, provisional

- **What it is.** 18.8 ha east of the Strand / Aldwych / Lancaster Place junction: the east end of Aldwych, the Royal Courts of Justice and the legal quarter between Carey Street, Serle Street and Fleet Street, down to Victoria Embankment. It is half of one ward fragment (L02); the west half, L02w, is Covent Garden's.
- **Crop.** `crops/L02e-aldwych-midtown-UNRESOLVED.png` (red = L02e, green = L02w).
- **Evidence for Midtown.** A web search (secondary, not the BID's own map) describes Midtown as the WC1, WC2 and western EC postcodes (EC1N, EC4A, EC4Y), with Kingsway an important dividing line and the legal community on its eastern side. The Royal Courts and Aldwych are WC2.
- **Evidence against Covent Garden.** The CGCA area is bounded by High Holborn, New Oxford Street, Charing Cross Road, St Martin's Place, Northumberland Avenue, Victoria Embankment, Lancaster Place, Aldwych and Kingsway. Its constitution explicitly includes Victoria Embankment (as cited by the commissioner, not fetched here); the other bounding streets were read from a search result. Its eastern edge runs along Lancaster Place, Aldwych and Kingsway, so L02e is outside it.
- **No evidence either way** for the Midtown BID footprint: its boundary was not retrieved. About 11 ha of L02e lies south of the Strand centreline (grid-sampled, approximate).
- **Coverage is unchanged.** **Recommendation:** keep L02e in Holborn / Midtown for now and label it unverified; then obtain the Midtown BID map or Reiwa's own Midtown definition. If Midtown means the WC1 Holborn and Bloomsbury core, removing L02e takes Midtown from 118 ha to 99 ha; if it means the whole legal quarter, keep it. Do not move it to Covent Garden: the CGCA evidence points the other way.

### Covent Garden extends to Victoria Embankment (supported, not clipped)

The Covent Garden Community Association's published constitution explicitly includes Victoria Embankment (coventgarden.org.uk/about/governance, as cited by the commissioner; the page could not be fetched from the build environment, so this is recorded as cited). Covent Garden's own footprint does the same: about a third of it (roughly 27 ha, grid-sampled against the Strand centreline) lies between the Strand and the Embankment (Charing Cross, Embankment Gardens, the Savoy), of which 14.6 ha is fragment L02w. **It is not clipped at the Strand.** The CGCA area is evidence for the extent, not a definition: Reiwa's Covent Garden stays a Reiwa-defined market area, distinct from the CGCA area, the wards and any BID.

## Amsterdam

| Area | Kind | Definition used | Class | ha | Cross-dataset overlap (consistency check only; IoU = intersection over union) |
|---|---|---|---|---|---|
| Canal Belt (Grachtengordel) | Official units | Buurtcombinaties Grachtengordel-West (63.8 ha) + Grachtengordel-Zuid (52.1 ha) = 115.9 ha; drawn 116.0 ha (0.2 ha outside the two units: seam between retained areas). The UNESCO canal-ring boundary was not used | Core | 116 | Legacy ring and OSM "Grachtengordel" agree (IoU 0.89); the CBS generalised ring is too coarse to compare closely |
| Jordaan | Official unit | Buurtcombinatie Jordaan | Core | 96 | OSM 0.98; CBS 0.80 |
| Oud-Zuid | Official units | Museumkwartier, Apollobuurt, Willemspark, Stadionbuurt. Not stadsdeel Zuid | Core | 358 | CBS 0.90 |
| Zuidas | Reiwa-defined (selected footprint) | Reiwa's selected footprint: CBS 2022 buurten Zuidas Noord + Zuidas Zuid (see below) | Core | 108 | Official description about 245 ha (as cited, not fetched); see below |
| Oud-West | Official units | Helmersbuurt, Vondelbuurt, Da Costabuurt, Kinkerbuurt, Van Lennepbuurt, Overtoomse Sluis | Selective | 169 | CBS 0.92, OSM 0.96 |
| Weesperbuurt / Plantage | Official unit | Legacy buurtcombinatie Weesperbuurt/Plantage only (see below) | Selective | 85 | See below |
| De Pijp | Official units | Oude Pijp + Nieuwe Pijp + Diamantbuurt (the Diamantbuurt lies in the current official wijk Zuid Pijp) | Selective | 155 | OSM 0.94; CBS (three wijken) 0.87 |
| Oost | Official units | Weesperzijde, Oosterparkbuurt, Dapperbuurt, Transvaalbuurt, Indische Buurt West. Not stadsdeel Oost | Selective | 260 | CBS 0.92 |
| Rivierenbuurt | Official units | Rijnbuurt, Scheldebuurt, IJselbuurt | Selective | 263 | CBS 0.77; the difference is the river edge |

### Weesperbuurt / Plantage

- **Change.** The Oostelijke Eilanden/Kadijken buurtcombinatie (135 ha as published, 117 ha of it drawn) is no longer part of the footprint. The footprint fell from 204 ha to 85 ha. The note that "Plantage includes the Eastern Islands" is removed.
- **What remains.** The legacy buurtcombinatie **Weesperbuurt/Plantage** (85.7 ha; the CBS 2022 wijk of the same name is 84.1 ha). It is **not Plantage proper.** In CBS 2022 it is four buurten: Weesperbuurt (26.1 ha), Sarphatistrook (21.2 ha), de Plantage (40.2 ha) and Alexanderplein e.o. (4.2 ha). Of the 85 ha drawn, 30.8 ha (36%) is the CBS buurt de Plantage; the legacy outline covers 77% of that buurt, so about 9 ha of de Plantage lies outside it (a vintage difference between the two sources, not investigated further).
- **Label.** The map label reads **Weesperbuurt / Plantage** (JA: ウェースペルブールト・プランタージュ), which is what the footprint is. The Japanese rendering of Weesperbuurt is a transliteration that has not been reviewed by a native speaker. The area keeps its **selective** classification and the `plantage` id in `amsterdam-focus.js`; its name there is now "Weesperbuurt/Plantage".
- **Source for the boundary of Plantage.** The page cited for this change (amsterdam.nl, Centrum begroot) was not reachable. A web search (a neighbourhood guide, secondary) describes Plantage as bordered on the north by the Oostelijke Eilanden, on the east and south by Oost and on the west by Nieuwmarkt and the Grachtengordel, which agrees with removing the islands.
- **Open.** Whether Reiwa wants Plantage proper only (the CBS buurt de Plantage, 40 ha) rather than the full buurtcombinatie.

### Zuidas (Reiwa's selected footprint)

- **What is drawn.** **Reiwa's selected Noord + Zuid footprint** around Station Zuid: CBS 2022 buurten Zuidas Noord (96.7 ha) and Zuidas Zuid (20.5 ha); drawn 107.9 ha: 87.4 ha of Noord and 20.5 ha of Zuid, nothing else (the 6 October build carried 0.6 ha beyond the two units, 0.4 ha of it in RAI; that ground is no longer in the footprint). It straddles the A10. Point checks against the CBS buurten put Station Zuid, the WTC and Gustav Mahlerplein in Noord and Gershwinplein in Zuid. **The footprint is unchanged in this revision** and the label stays "Zuidas".
- **Official description.** The official Zuidas description (zuidas.nl/en/about-zuidas, as cited by the commissioner) states approximately 245 hectares. The page could not be fetched from the build environment, so the figure is recorded as cited and not checked here. The drawn footprint is about 44% of it (107.9 of 245 ha).
- **Definition.** The footprint is Reiwa's selection. It is not the official district, not the CBS wijk and not the municipal project area, and this file, the code comments (`geometry.py`, `render.py`, `boundaries.py`) and the SVG comment all describe it that way. It is described by what it contains (Station Zuid, the WTC, Gustav Mahlerplein, both sides of the A10 within those two buurt limits). Earlier text called it the part with investable existing stock; **that claim is withdrawn, because nothing in the sources supports it.**
- **No exact official boundary is inferred.** The CBS data are used only for the two units that Reiwa selected. No further CBS units are added to approach the official figure, and no sum of CBS units is presented as the official area (an earlier inference of about 239 ha from the CBS units is withdrawn). The official boundary needs the official map.
- **Open.** Whether the maps should show the official area, or keep this selected footprint and say so, is a Reiwa decision. Nothing was widened.
- **Legacy outline.** The older Gemeente buurtcombinatie "Station-Zuid WTC en omgeving" (125.1 ha) overlaps the drawn area by 82.4 ha; the CBS 2022 units are used instead because they straddle the A10.

### Canal Belt figures

An earlier version of this file said both 61 ha and 65 ha were removed. The measured figures:

- The De Weteringschans buurtcombinatie (Leidseplein to Frederiksplein) is **65.4 ha** as published. The earlier "61 ha" was wrong.
- The drawn Canal Belt fell from **181.4 ha to 116.2 ha, a reduction of 65.2 ha** (181 to 116 as shown in `amsterdam-focus.js` before and after, scaled on the unchanged Jordaan). The removal is the Weteringschans unit, less a few tenths of a hectare of seam.
- The Canal Belt is now Grachtengordel-West plus Grachtengordel-Zuid: 115.9 ha as published, 116.0 ha drawn.

## Coverage-union audit

Principle (7 October 2026): the shared-edge cleanup may *allocate* ground between areas that is already retained. Coverage beyond the retained coverage is limited to the recorded seam and gap allowances below, each bounded and recorded; anything else the cleanup produced is removed. Market definitions are not widened to accommodate a cleanup artefact; whether to widen one is a separate decision.

**Retained coverage (E):** each focus area as defined from its source units, overlaps resolved, the 25 London ward fragments and D1 placed by `london_fragments.py`, smoothed per area (spikes under 14 m removed, notches under 20 m closed, 3 m simplification; the per-area effect is in `docs/map-coverage-union.md`), minus the park and river mask. **Final coverage (F):** the union of the areas as drawn and in `focus.js`. The comparison is on the union itself, not on a closed outline.

`tools/maps/coverage_rules.py` cuts every area back to E + SEAM + recorded gaps, and nothing else:

- **Rule S, seam:** ground within 13 m of two different retained areas, so at most 26 m wide, where two areas meet along a shared edge. It cannot move the outer limit by more than 13 m, and only where two retained areas face each other.
- **Rule G, recorded enclosed gap:** a gap enclosed by E and SEAM on all sides, at least 3 m from any park or river, no larger than 0.25 ha, and listed in `EXCEPTIONS` with its position, a maximum area and its basis (12 in London, 1.02 ha in all; 3 in Amsterdam, 0.14 ha in all). The basis is geometric only (no source or market evidence); each can be removed, leaving a hole, if Reiwa prefers. An unlisted gap is removed, so a new vintage cannot add a gap allowance silently.
- **Everything else is removed, however small:** the road strip between an area and a park or river edge, blocks outside the definition, slivers on the outer edge.

**Executable check:** `tools/maps/check_coverage.py` (run by `build.py`, and alone with `MAP_DATA=... python3 tools/maps/check_coverage.py`) rebuilds F, recomputes E and SEAM from the retained geometry, and fails if any piece of F outside E + SEAM is not a recorded gap, if a recorded gap no longer exists, or if one of the four additions removed on 7 October 2026 is back. `--selftest` proves it can fail (it fails with the cutback disabled and with a 100 m2 block added outside). **Numerical tolerance:** coverage outside the rules is ignored only if it is no more than **0.5 m wide** (it vanishes under an inward buffer of 0.25 m) or smaller than **1 m2**; geometry is snapped to 0.01 m, so the width tolerance is 50 times the grid.

**Exact changes (final coverage F, ha):**

| | F before | F after | Change | Cutback (pieces) | F outside E: seam (S) | recorded gaps (G) | other |
|---|---|---|---|---|---|---|---|
| London | 2159.3 | 2154.8 | -4.5 | 4.57 ha (35) | 3.63 | 1.02 | 0.00 |
| Amsterdam | 1612.9 | 1609.5 | -3.4 | 3.36 ha (26) | 0.62 | 0.12 | 0.00 |

Before, F outside E was 9.2 ha in London and 4.1 ha in Amsterdam. Areas that changed (ha, before to after): London Marylebone 174.1 to 172.8, Fitzrovia 63.7 to 63.6, Westminster 385.9 to 384.5, Holborn / Midtown 117.9 to 117.6, City of London 289.1 to 288.6, Kensington & Chelsea 766.7 to 765.9; Amsterdam Oud-Zuid 358.9 to 357.8, Zuidas 108.5 to 107.9, Plantage 85.3 to 85.2, Oost 259.5 to 259.4, Rivierenbuurt 264.3 to 263.2, Canal Belt 116.3 to 116.0. Every other area is unchanged to 0.1 ha. Polygons changed only where a piece was removed; the fixed labels and Bloomsbury stayed where they were and the leader anchors followed the polygons. Labels were re-placed where their polygons changed: London Westminster in the tall frame (about 8% of the frame width and 3.5% of its height), City of London in the tall frame (about 2%) and the West End label (under 0.6%); Amsterdam Canal Belt (about 1%) and Oud-West in the wide frame (about 2%); every other Amsterdam label moves by under 0.3%.

**The four named removals** (before/after crops in `crops/`):

- Peto Place, 1.32 ha (Marylebone): a block north of Marylebone Road at Park Crescent and a strip along the Regent's Park edge.
- Grosvenor Road, 0.99 ha (Westminster): a strip along the Thames edge in Pimlico.
- Chelsea Embankment, 0.43 ha (Kensington & Chelsea): a thin strip between the embankment road and the river.
- Ringweg-Zuid, 0.44 ha (Rivierenbuurt): a strip along the Amstelpark edge.

**Smaller outward additions** are removed on the same principle (London: Victoria Embankment 0.24, Bayswater Road 0.23, Millbank 0.20 and 0.20, Gray's Inn Road 0.18 ha and 27 more pieces; Amsterdam: Boerenweteringpad 1.13, Bernard Zweerskade 0.24 ha, Singel, Weesperzijde and 20 more). Pieces of 0.2 ha or more have before/after crops; the full list is `docs/map-coverage-union.md`.

**Remaining unsupported additions: none.** F outside E + SEAM + recorded gaps is 0.00 ha in both cities (the check passes). Two consequences are visible and are left as they are: a 0.70 ha wedge at Amstelveenseweg and Stadionkade between Oud-Zuid and Zuidas (enclosed, but above the 0.25 ha cap for a recorded gap, so it is now open; crop `amsterdam-removed-0.697ha-stadionkade.png`), and the road strips between area edges and park or river edges, which now stop at the retained edge (up to 22 m back). Keeping either is a Reiwa decision, not a cleanup rule.

**Not changed by this correction:** the market definitions, L02e (still held in Midtown and flagged provisional / unresolved), the Zuidas footprint, Weesperbuurt / Plantage, and the labels' positions.

## Notes under the maps

The note is one short sentence, "Indicative focus areas, not administrative boundaries" (London adds the six West End names), then the required attribution. The Eastern Islands note and the long West End sentence were removed from the page. Alt text still names every area, including the West End composition.

## Labels

Labels are HTML, positioned in percent of the frame, with leader lines drawn in the SVG. Labels are laid out for the narrowest width each frame is shown at (wide 420 px, tall 320 px). A leader should not cross another label, and a label should not sit on another leader (a penalty, not a ban).

**Bloomsbury (tall frame).** The label used to sit left of its polygon, over the West End core, with a leader running across the core. Bloomsbury has three per-label settings in `render.py`: `avoid_core` (its label and leader keep off the core areas), `rays` (extra straight-line leader candidates) and `keep_clear` (other labels keep off its anchor in the tall frame). The label sits above its own polygon, outside the West End core footprint, with a leader of 26 to 56 px in the tall frame (320 to 768 px wide); the West End label moved to the left of its polygon, with a leader, to make room. In the wide frame Bloomsbury is unchanged. This placement is preserved.

**Amsterdam: the eight findings are resolved.** The leader check had reported, in the tall frame: the Oud-West label box over the edge of Oud-Zuid (EN 390 and 768, JA 320 to 768), the Weesperbuurt / Plantage leader crossing the Canal Belt label at JA 320, and the De Pijp label touching Oud-Zuid at JA 320. The fix is a per-label `fixed` placement in `render.py` (a position in percent of the frame and the side the label hangs from; fixed labels are placed first and every other label avoids them). The positions were found by an exhaustive search of candidate positions against the measured EN and JA label sizes, then checked on the rendered pages:

- Oud-West (tall): hangs below a point at 20.9% / 41.9% of the frame, clear of Oud-Zuid.
- Weesperbuurt / Plantage (tall): hangs above a point at 71.9% / 31.8%; the leader is 46 px or less at 320 px and stays under 130 px at 900 px, and it no longer crosses the Canal Belt label.
- De Pijp (tall): to the right of a point at 55.0% / 59.1%, leader 14 px at 320 px.
- De Pijp (wide): centred inside its polygon at 53.2% / 61.1%. The wider widths (900 and 901 px, not covered by the earlier check) showed the JA label touching Oud-Zuid in the wide frame at 901 px; this placement clears it.
- The Canal Belt tall label moved by about 2% of the frame width (to 55.0% / 36.9%), because it avoids the new positions. All other labels are unchanged.

Type sizes and every polygon are unchanged: `amsterdam-focus.js` and `london-focus.js` are byte-identical to the delivered checkpoint's, and the label font sizes are not touched. The rendered check (`verify/leader-clarity.txt`) finds no label on a core area, no leader crossing a label, no leader over 130 px and no label outside its frame, in both cities, EN and JA, at 320, 390, 768, 900, 901, 1024 and 1440 px.

## Replacement Overture inputs

The six Overture extracts the build reads (`{london,amsterdam}_{segment,land_use,water}.geojson`) were lost in a sandbox reset and were not in the supplied archives. The original script and bounding boxes were lost with them. They were regenerated from the public release 2026-08-19.0 with `tools/maps/extract_overture.py` (row-group reads of the GeoParquet over HTTP; whole features meeting the box; flat properties id, name, subtype, class). **They are not the original bytes**, so the checksum pins in `sources.json` now describe the replacements, and the original hashes are kept there under `original_overture_inputs`.

| File | Original bytes | Replacement bytes | Original SHA-256 | Replacement SHA-256 |
|---|---|---|---|---|
| london_segment.geojson | 38,480,002 | 32,955,072 | `31fe20531dc0` | `a96cda28cc87` |
| london_land_use.geojson | 23,303,959 | 20,292,902 | `3cdb004f6874` | `1ff636459cea` |
| london_water.geojson | 1,279,762 | 1,094,352 | `4f1470895384` | `525924e61a00` |
| amsterdam_segment.geojson | 28,691,146 | 40,032,651 | `52ccc7884f10` | `07fb20cfe132` |
| amsterdam_land_use.geojson | 38,510,922 | 51,098,385 | `38c5dc7b3f20` | `4a187aa3e26c` |
| amsterdam_water.geojson | 11,215,436 | 21,959,937 | `ebe44c6c60a5` | `3e12b159b0af` |

Boxes (lon min, lat min, lon max, lat max): London (-0.22, 51.47, -0.04, 51.57); Amsterdam (4.70, 52.25, 5.05, 52.46). They are inferences, not recoveries:

- **London.** The delivered London SVGs have no road, park or water geometry south of about 51.47 N or in the western strip of the tall frame; a larger box draws more base map than the approved maps show. The south edge was fitted by comparing the rendered size of the London SVGs for candidate edges (51.465 to 51.48) with the delivered files; the north, east and west edges were not recoverable.
- **Amsterdam.** A tighter box moved one vertex of the Oud-Zuid outline (a park or water mask polygon is included differently); this larger box reproduces every outline exactly. The original files were smaller than this box would give.

**Validation of the effect** (the delivered checkpoint's tools, built with the replacement inputs, against the delivered checkpoint's outputs):

| Output | Result |
|---|---|
| `amsterdam-focus.js`, `amsterdam-wide.svg`, `amsterdam-tall.svg` | byte-identical |
| `london-focus.js` (every London focus-area outline) | byte-identical |
| `london-wide.svg` | not byte-identical (335,003 bytes against 334,204); rendered at 1000 px, **0 of 1,053,000 pixels** differ by more than 24/255 |
| `london-tall.svg` | not byte-identical (370,330 bytes against 363,630); **4,493 of 1,250,000 pixels (0.36%)** differ by more than 24/255, mostly thin roads and park edges in the western strip, where the replacement draws base map that the delivered map left blank |

So the geography (every area, every outline, every label position) is unchanged, Amsterdam is exactly reproduced, and only the London tall base map differs slightly at its edge. The replacement London tall base map is arguably the more complete one, but it is a difference and is reported as such. If an exact match is needed, the original six files are required.

## Checks: what was performed, and what is not verified

The checks fall into five groups. They are kept apart on purpose: passing one says nothing about the others.

### Source-file integrity verification

- `tools/maps/sources.json` pins every input by SHA-256, and `build.py` compares each input with its pin before it builds (14 boundary and audit extracts and the six replacement Overture extracts: 20 of 20 match). A match shows that the file is the one that was pinned. It does **not** show that the file's boundaries are correct, complete or equal to any live official source.
- The six Overture pins are the pins of the replacement files; the original hashes are kept under `original_overture_inputs` and the original files are not recovered (see "Replacement Overture inputs").

### Reproducibility checks

- The coverage check (`tools/maps/check_coverage.py`, run inside `build.py`) passes in both cities: no coverage outside the retained geometry, the seam rule and the recorded gaps (tolerance 0.5 m width / 1 m2); its selftest fails when the cutback is disabled and when a 100 m2 block is added.
- Two consecutive builds from the pinned inputs are byte-identical (checked on 6 October; after the 7 October correction the site was rebuilt once, and the fresh-extract rebuild from the evidence pack is byte-identical to it) (both About pages, four SVGs, two focus-data files).
- The build stops on a changed input (a tampered ward file), on an unlisted ward fragment (L17 removed) and on an unlisted detached part.
- The delivered checkpoint's tools with the replacement Overture inputs reproduce Amsterdam exactly and the London outlines exactly (see above).
- The 25 explicit fragment decisions plus D1 reproduce the delivered London outlines byte for byte; `amsterdam-focus.js` and `london-focus.js` in this revision are byte-identical to the delivered checkpoint's.
- The evidence pack is self-sufficient: extracted fresh, with its own tooling, the 14 extracts and the six replacement Overture files, it rebuilds all eight site files byte-identically.

### Rendering checks

Local server, headless Chromium, EN and JA, both cities, at 320, 390, 768, 900, 901, 1024 and 1440 px (`verify/` in the evidence pack). The 900 and 901 px widths are the two sides of the tall / wide breakpoint.

- Label placement, clipping, collisions, wrapping and page overflow: 28 map views, all pass (`render-labels-wrapping-overflow.txt`).
- Leader clarity (leader through another label, label on a core area, leader length over 130 px, label outside the frame): 28 map views, **all 210 label rows clear in both cities** (`leader-clarity.txt`). This includes the eight Amsterdam tall-frame findings, now resolved, and the 900 / 901 px widths, which the earlier five-width run did not cover.
- Katakana wrapping, `ja/about.html` at 30 widths: 0 unprotected runs, 0 split runs.
- About-page preservation, 70 checks (symbols, Contact system, footer, skip link, `editorial.css?v=130`, overflow, console errors): all pass. The 47-check site suite used in earlier rounds was lost in the reset and was not re-run; this smaller About-only check replaces it.
- Screenshots at the seven widths: component, frame-only and in-page context captures plus the London Bloomsbury and Amsterdam label close-ups, 70 asserted captures, each unobstructed (nine sample points belong to the map, none to the navigation or skip link), focus on the page body, labels fully opaque, skip link not showing; the skip link was separately confirmed to take focus and show on the first Tab (after its slide-in) at every width. At 768 and 900 px the tall frame is taller than a 900 px viewport, so those two widths are captured in a 1400 px viewport.
- Every difference between `about.html` / `ja/about.html` and main is in map markup, map CSS or map comments; `editorial.css`, `shell.js` and the other pages are unchanged.

### Source-supported descriptions

What this file says about where an area's edges run is supported by the named sources only to the extent stated, and none of it was checked against a live official page in this build:

- **Computed from the pinned extracts:** areas, overlaps, the share of each boundary that follows a named Overture road, and the coverage-union figures. These are measurements of the pinned data.
- **Cross-dataset overlap (IoU) figures** compare one pinned dataset with another (legacy buurtcombinaties against OSM or CBS units). They are consistency checks only; they do not verify a boundary.
- **Cited by the commissioner, not fetched:** CGCA's published constitution explicitly includes Victoria Embankment (coventgarden.org.uk/about/governance); the official Zuidas description states approximately 245 hectares (zuidas.nl/en/about-zuidas).
- **Secondary, from web searches:** the CGCA bounding streets other than the Embankment, the postcode description of Midtown, the neighbourhood-guide description of Plantage.

### Independently verified polygon boundaries

**None.** No polygon boundary in these maps was verified against an independent, live official source in this build. The ONS 2013 wards, City of London LAD, Gemeente Amsterdam buurtcombinaties and CBS 2022 extracts are used as supplied and pinned by checksum (source-file integrity above); the focus areas are Reiwa's own definitions built from them.

### Not verified

zuidas.nl (the official Zuidas area), amsterdam.nl (Plantage), coventgarden.org.uk (CGCA page, cited by the commissioner), the Midtown BID boundary, GLA and Westminster ward maps; the Japanese transliteration of Weesperbuurt; live deployment of the site (the live site could not be reached from this environment); the "south of the Strand" shares (grid samples, approximate); the original Overture bytes.

## Remaining geography decisions

1. **L02e, the 18.8 ha Aldwych piece in Midtown: unresolved** (crop and recommendation above).
2. **Zuidas:** the drawn footprint is Reiwa's selected Noord + Zuid footprint (107.9 ha). The official description states approximately 245 ha (as cited by the commissioner; not fetched here). Whether the map should show the official area is a Reiwa decision that needs the official map; no CBS units were added to approach the figure.
3. **Weesperbuurt / Plantage:** the full buurtcombinatie (85 ha), of which Plantage proper is about a third; whether Reiwa wants Plantage proper only.
4. **Covent Garden to the Embankment:** kept. CGCA's published constitution explicitly includes Victoria Embankment (as cited by the commissioner; the page was not fetched here).
5. **L14 Hatton Garden (1.2 ha) and L22 Finsbury Square (7.9 ha)** stay outside the coverage; both are candidates if Reiwa's Midtown or City definitions include them.
6. **Cleanup cutback consequences (separate decision):** the 0.70 ha wedge at Amstelveenseweg / Stadionkade is now open; the 12 London and 3 Amsterdam recorded enclosed gaps rest on geometry only; the road strips beside parks and rivers stop at the retained edge. No coverage was added or widened in this correction.
7. **London wards are the December 2013 set;** Westminster (2022) and Kensington & Chelsea (2018) have since been reviewed. Marylebone, Westminster and Kensington & Chelsea depend on the ward lines. The Amsterdam legacy set has no stated vintage.
8. **Replacement Overture inputs:** the London tall base map differs from the delivered one at its western edge.

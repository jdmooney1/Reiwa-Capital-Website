"""London ward fragments: explicit decisions.

Cutting a ward along named streets leaves fragments (ground of that ward that no focus area took). An earlier build gave each
fragment under 40 ha to whichever neighbour shared the longest edge. That rule is gone: it let ward geometry decide which ground
is investment coverage. Every fragment is now listed here with the area that holds it, the named streets that bound it and the
basis. clean.py matches fragments to these rules by anchor point and ward, and STOPS if a fragment is not listed (for example
after a new ward vintage) or if a listed fragment no longer exists.

assign  - the area that holds the fragment. A name outside the focus areas ("Clerkenwell", "Farringdon", "Shoreditch & Aldgate")
          means the fragment stays outside the focus coverage. None means unclaimed. A dict cuts the fragment on a north-south line.
status  - supported : bounded by named streets and held by the area that those streets and the area's definition give it
          closure   : road corridor or sliver between focus areas, or between a focus area and a park edge; coverage-neutral
          excluded  : stays outside the focus coverage
          unresolved: held today, not independently supported; see docs/map-geography.md and docs/london-ward-fragments.md
          split     : one fragment cut into two rules (L02w, L02e)
Whether a fragment changes the outline of the West End (rather than only which of its six sub-areas holds it) is reported by
tools/maps/audit.py. Anchors are representative points (longitude, latitude) of the fragment as built from the pinned December 2013
wards, so a different ward vintage fails the build here rather than silently moving coverage.

The 25 decisions were recovered after a sandbox reset from the session record; the coverage they produce was checked against the
areas built before the reset (tools/maps/audit.py, "identity")."""
FRAGMENTS=[
 dict(id='L01',ward="St James's",anchor=(-0.1328,51.51069),ha=11.3,assign='Covent Garden',status='supported',
      streets='Shaftesbury Avenue, Charing Cross Road, Haymarket, Coventry Street, Cranbourn Street',
      basis="Leicester Square and Chinatown, enclosed by Soho, St James's and Covent Garden. Inside the West End outline on every side; Soho is the alternative holder and would not change the outline."),
 dict(id='L02',ward="St James's",anchor=(-0.1162,51.51068),ha=33.4,assign=dict(cut_at=(-0.1178,51.5112),west='Covent Garden',east='Holborn / Midtown'),status='split',
      streets='Strand, Victoria Embankment, Northumberland Avenue, Waterloo Bridge, Carey Street, Serle Street, Fleet Street',
      basis='One fragment cut on the north-south line through the Strand / Aldwych / Lancaster Place junction (see L02w and L02e).'),
 dict(id='L02w',ward="St James's",anchor=None,ha=14.6,assign='Covent Garden',status='supported',
      streets='Strand, Northumberland Avenue, Victoria Embankment, Lancaster Place',
      basis="West of the junction: Charing Cross, Embankment Gardens, the Savoy. Matches the published Covent Garden Community Association area (High Holborn, New Oxford Street, Charing Cross Road, St Martin's Place, Northumberland Avenue, Victoria Embankment, Lancaster Place, Aldwych, Kingsway), which extends to Victoria Embankment. That area is a community association's, not a ward, not a BID and not Reiwa's; it is supporting evidence only. CGCA's published constitution explicitly includes Victoria Embankment (coventgarden.org.uk/about/governance, as cited by the commissioner; the page could not be fetched from the build environment, so this is recorded as cited). Not clipped at the Strand."),
 dict(id='L02e',ward="St James's",anchor=None,ha=18.8,assign='Holborn / Midtown',status='unresolved',
      streets='Aldwych, Strand east of Lancaster Place, Carey Street, Serle Street, Fleet Street, Waterloo Bridge, Victoria Embankment',
      basis="East of the junction: Aldwych east, the Royal Courts of Justice and the legal quarter down to the Embankment. Outside the Covent Garden Community Association area (its edge runs along Lancaster Place, Aldwych and Kingsway). Held in Midtown because a secondary description puts WC2 and EC4Y in Midtown; the Midtown BID boundary was not retrieved. About 11 ha of it lies south of the Strand centreline. Coverage unchanged pending a decision; this placement is PROVISIONAL."),
 dict(id='L03',ward="St James's",anchor=(-0.13347,51.50474),ha=2.7,assign='Westminster',status='closure',
      streets="The Mall, Spring Gardens, Queen's Walk, Horse Guards Road",
      basis="The Mall carriageway and verges between St James's Park and Green Park; closes the gap between St James's and Westminster along a named road."),
 dict(id='L04',ward="St James's",anchor=(-0.1311,51.50777),ha=0.0,assign="St James's",status='closure',streets='Pall Mall, Haymarket, Cockspur Street',basis='Sliver at the Pall Mall / Haymarket junction.'),
 dict(id='L05',ward="St James's",anchor=(-0.13053,51.50781),ha=0.1,assign='Covent Garden',status='closure',streets='Cockspur Street, Pall Mall, Pall Mall East',basis="Sliver along Cockspur Street; St James's and Covent Garden meet on that street."),
 dict(id='L06',ward="St James's",anchor=(-0.13935,51.50225),ha=0.0,assign="St James's",status='closure',streets='(none named)',basis="Sliver of a few square metres beside St James's Park."),
 dict(id='L07',ward="St James's",anchor=(-0.13975,51.5023),ha=0.0,assign="St James's",status='closure',streets='(none named)',basis="Sliver of a few square metres beside St James's Park."),
 dict(id='L08',ward="St James's",anchor=(-0.14047,51.50213),ha=0.0,assign="St James's",status='closure',streets='Constitution Hill',basis='Sliver along Constitution Hill.'),
 dict(id='L09',ward="St James's",anchor=(-0.14171,51.50727),ha=0.1,assign="St James's",status='closure',streets='Piccadilly, Berkeley Street, Dover Street',basis='Verge strip along Piccadilly (Green Park side).'),
 dict(id='L10',ward="St James's",anchor=(-0.14187,51.50224),ha=0.0,assign="St James's",status='closure',streets='Constitution Hill',basis='Sliver along Constitution Hill.'),
 dict(id='L11',ward="St James's",anchor=(-0.1489,51.5036),ha=1.1,assign='Westminster',status='closure',
      streets='Constitution Hill, Piccadilly, Duke of Wellington Place, Grosvenor Place',
      basis='Hyde Park Corner carriageways between Green Park, Hyde Park and Belgravia; closes the gap between Westminster and the park edge.'),
 dict(id='L12',ward='West End',anchor=(-0.15491,51.51377),ha=0.2,assign='Mayfair',status='closure',streets='Oxford Street, Orchard Street, Park Street',basis='Oxford Street verge at the Marble Arch end.'),
 dict(id='L13',ward='West End',anchor=(-0.14101,51.51351),ha=9.7,assign='Soho',status='closure',
      streets='Oxford Street, Regent Street, Glasshouse Street, Piccadilly, Cavendish Square, Holles Street, Welbeck Street',
      basis='West End ward ground left along the Oxford Street and Regent Street carriageways, the Regent Street Quadrant at Piccadilly Circus and a block between Welbeck Street and Holles Street. Held by Soho only because Soho shares the longest edge; which of the six West End areas holds it is a sub-area question. tools/maps/audit.py reports how much of it lies outside the rest of the West End outline.'),
 dict(id='L14',ward='Holborn and Covent Garden',anchor=(-0.11234,51.51997),ha=1.2,assign='Farringdon',status='excluded',
      streets="Clerkenwell Road, Gray's Inn Road, Hatton Garden, Farringdon Road",
      basis='Hatton Garden (EC1N). Not held by Holborn / Midtown or any focus area; stays outside. EC1N is named in a secondary description of Midtown, so it could be a candidate for inclusion.'),
 dict(id='L15',ward='Holborn and Covent Garden',anchor=(-0.12283,51.51962),ha=0.8,assign='Holborn / Midtown',status='closure',streets='Southampton Row, Great Russell Street, Bury Place, Bloomsbury Square',basis='Verge strip at Bloomsbury Square on the Midtown and Bloomsbury boundary.'),
 dict(id='L16',ward='Holborn and Covent Garden',anchor=(-0.11891,51.51474),ha=0.7,assign='Holborn / Midtown',status='closure',streets='Kingsway, Shelton Street, Great Queen Street',basis='Strips along Kingsway; Covent Garden and Midtown meet on Kingsway.'),
 dict(id='L17',ward='Bloomsbury',anchor=(-0.13781,51.52286),ha=12.7,assign='Fitzrovia',status='supported',
      streets='Tottenham Court Road, Cleveland Street, Euston Road, Fitzroy Square, Torrington Place',
      basis='Bloomsbury ward west of Tottenham Court Road up to Euston Road: exactly the "Bloomsbury ward west of Tottenham Court Road" that the Fitzrovia definition names.'),
 dict(id='L18',ward='Clerkenwell',anchor=(-0.10487,51.52244),ha=0.1,assign='Clerkenwell',status='excluded',streets='Clerkenwell Road',basis='Sliver; Clerkenwell is not a focus area.'),
 dict(id='L19',ward='Bunhill',anchor=(-0.10542,51.53174),ha=0.0,assign='Clerkenwell',status='excluded',streets='City Road',basis='Sliver; Clerkenwell is not a focus area.'),
 dict(id='L20',ward='Bunhill',anchor=(-0.09601,51.52931),ha=0.2,assign='Clerkenwell',status='excluded',streets='City Road',basis='Sliver; Clerkenwell is not a focus area.'),
 dict(id='L21',ward='Bunhill',anchor=(-0.0862,51.52558),ha=2.3,assign='Shoreditch & Aldgate',status='excluded',streets='City Road, Old Street, Old Street Roundabout',basis='Old Street roundabout; outside the focus coverage.'),
 dict(id='L22',ward='Bunhill',anchor=(-0.08607,51.52112),ha=7.9,assign='Clerkenwell',status='excluded',
      streets='City Road, Wilson Street, Finsbury Square, South Place, Finsbury Pavement',
      basis='Finsbury Square (EC2), next to the City of London. The City of London area is the ONS local authority district and does not take it; stays outside.'),
 dict(id='L23',ward='Haggerston',anchor=(-0.08473,51.52598),ha=0.2,assign='Shoreditch & Aldgate',status='excluded',streets='Great Eastern Street, Old Street',basis='Sliver; outside the focus coverage.'),
 dict(id='L24',ward='Haggerston',anchor=(-0.0728,51.53282),ha=85.6,assign=None,status='excluded',streets='Hackney Road, Queensbridge Road, Hoxton Street, Kingsland Road',basis='Hoxton and Haggerston ward remainder; unclaimed on purpose.'),
 dict(id='L25',ward='Weavers',anchor=(-0.07047,51.5265),ha=63.9,assign=None,status='excluded',streets='Hackney Road, Brick Lane, Vallance Road, Buxton Street',basis='Weavers ward remainder (Shoreditch and Bethnal Green); unclaimed on purpose.'),
]

# Detached parts of 0.5 ha or more. After the opening and masking steps a focus area can leave a detached part; one under 0.5 ha is
# re-homed to a touching neighbour by shared edge length and logged (tools/maps/audit.py totals them), but a larger one must be listed
# here with the area that takes it, or the build stops. "to" may be an area that is later clipped (Mayfair is clipped to its ward plus 25 m).
DETACHED=[
 dict(id='D1',area='Westminster',anchor=(-0.17038,51.51216),ha=12.2,to='Mayfair',status='closure',
      streets='Bayswater Road, Park Lane, Edgware Road, Hyde Park Place',
      basis='The road and verge corridor along the north and east edges of Hyde Park, ground of the Westminster area after the park mask is cut. About 3.1 ha of it is the Park Lane carriageway and verge, which Mayfair\'s western edge already runs along (Park Lane is Mayfair\'s stated western limit); the rest (the Bayswater Road strip) falls outside the final focus coverage. Tools/maps/audit.py reports the split.'),
]

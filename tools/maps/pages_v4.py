"""Patch about.html / ja/about.html for the v4 maps (tools/maps/deck_v4.py): labels, alt text, notes, the core-zone panel under each
map's market column (the two core zones and the selective areas, in place of the generic market text), the deck colour system for
labels and legend, and the cache version."""
import re
from pages import SIDE, ja_markup

ALT = {'london': {
    'en': "Map of central London, with the Thames, Regent’s Park, Hyde Park, Green Park and St James’s Park shown. Indicative investment focus areas, not administrative boundaries. Core, in dark purple: the Prime West End (Marylebone, Fitzrovia, Soho, Mayfair, St James’s and Covent Garden) and the institutional core (the City of London, and Westminster from Whitehall and Victoria to Vauxhall Bridge). Selective, in pink: Bloomsbury, Midtown, Farringdon, Clerkenwell, Shoreditch and Aldgate, and Southbank.",
    'ja': "ロンドン中心部の地図。テムズ川、リージェンツパーク、ハイドパーク、グリーンパーク、セントジェームズパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核（濃い紫）：プライム・ウェストエンド（Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden）と、機関投資家向けコア（シティ・オブ・ロンドン、ホワイトホールおよびヴィクトリアからヴォクソール橋までのウェストミンスター）。選択的（ピンク）：ブルームズベリー、ミッドタウン、ファリンドン、クラーケンウェル、ショーディッチ・オールドゲート、サウスバンク。"},
  'amsterdam': {
    'en': "Map of Amsterdam, with the canal ring around the historic centre, the IJ to the north, the Amstel and Vondelpark. Indicative investment focus areas, not administrative boundaries. Core, in dark purple: the canal district (the Jordaan, with Haarlemmerbuurt, and the Canal Belt) and Zuid (Museumkwartier, Oud-Zuid and Zuidas, which lies on both sides of the A10). Selective, in pink: Centrum, Plantage, Oud-West, West, Sloterdijk, Noord, De Pijp, Oost, Rivierenbuurt, Overamstel and Buitenveldert.",
    'ja': "アムステルダムの地図。歴史的中心部を囲む運河環状地帯、北のIJ湾、アムステル川、フォンデルパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核（濃い紫）：運河地区（ハールレマーブールトを含むヨルダーン、カナルベルト）と、ザウト（ミュージアム地区、アウド・ザウト、A10の両側にまたがるザイダス）。選択的（ピンク）：セントルム、プランタージュ、アウド・ウェスト、ウェスト、スローテルダイク、ノールト、デ・パイプ、オースト、リヴィエレンブールト、オーフェルアムステル、バウテンフェルデルト。"}}
NOTE = {'london': {'en': 'Indicative focus areas, not administrative boundaries. Midtown: Holborn and King’s Cross south of Euston Road.',
                   'ja': '投資対象エリアの目安であり、行政上の境界ではありません。ミッドタウン：ホルボーン、およびユーストン・ロード以南のキングス・クロス。'},
        'amsterdam': {'en': 'Indicative focus areas, not administrative boundaries. Plantage includes Nieuwmarkt and the Eastern Islands.',
                      'ja': '投資対象エリアの目安であり、行政上の境界ではありません。プランタージュはニューマルクトと東部の島々を含みます。'}}

# The two core zones in each city, as set out in the investor deck (pages 9 and 11), and the selective areas.
ZONES = {'london': {
    'en': ([('Prime West End', 'Marylebone, Fitzrovia, Soho, Mayfair, St James’s, Covent Garden',
             'Private wealth, advisory, retail and media', 'Mixed office and residential, smaller lot sizes, constrained supply', 'Aoyama, Ginza, Akasaka'),
            ('Institutional Core', 'City of London, Westminster',
             'Banks, insurers, law firms and government', 'Large-floorplate offices, long income, deep investment market', 'Otemachi, Marunouchi, Nagatacho')],
           'Bloomsbury, Midtown, Farringdon, Clerkenwell, Shoreditch &amp; Aldgate, Southbank. Considered asset by asset.'),
    'ja': ([('プライム・ウェストエンド', 'Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden',
             'プライベートウェルス、アドバイザリー、小売、メディア', 'オフィスと住宅の複合用途、比較的小規模なロット、限られた供給', '青山、銀座、赤坂'),
            ('機関投資家向けコア', 'シティ・オブ・ロンドン、ウェストミンスター',
             '銀行、保険会社、法律事務所、政府機関', '大型フロアプレートのオフィス、長期の賃料収入、厚い投資市場', '大手町、丸の内、永田町')],
           'ブルームズベリー、ミッドタウン、ファリンドン、クラーケンウェル、ショーディッチ・オールドゲート、サウスバンク。個別の物件ごとに検討します。')},
  'amsterdam': {
    'en': ([('Canal District', 'Jordaan (with Haarlemmerbuurt, to the IJ), Canal Belt (Herengracht, Keizersgracht, Prinsengracht)',
             'Boutique office, advisory, private wealth, residential', 'Listed canal houses in the UNESCO area, little redevelopment, smaller floorplates', 'Ginza, Omotesando'),
            ('Zuid', 'Zuidas, Oud-Zuid, Museumkwartier',
             'Multinational headquarters, law firms and financial institutions', 'Large-floorplate offices in the main international business district, CPI-linked leases', 'Otemachi, Roppongi Hills')],
           'Centrum, Plantage, Oud-West, West, Sloterdijk, Noord, De Pijp, Oost, Rivierenbuurt, Overamstel, Buitenveldert. Considered asset by asset.'),
    'ja': ([('運河地区', 'ヨルダーン（IJ湾までのハールレマーブールトを含む）、カナルベルト（ヘーレングラハト、カイザースグラハト、プリンセングラハト）',
             'ブティック型オフィス、アドバイザリー、プライベートウェルス、住宅', 'ユネスコ世界遺産地区の歴史的運河建築、再開発の余地は限定的、比較的小さなフロアプレート', '銀座、表参道'),
            ('ザウト', 'ザイダス、アウド・ザウト、ミュージアム地区',
             '多国籍企業の本社、法律事務所、金融機関', '主要な国際ビジネス地区の大型オフィス、CPI連動の賃料', '大手町、六本木ヒルズ')],
           'セントルム、プランタージュ、アウド・ウェスト、ウェスト、スローテルダイク、ノールト、デ・パイプ、オースト、リヴィエレンブールト、オーフェルアムステル、バウテンフェルデルト。個別の物件ごとに検討します。')}}
DT = {'en': ('Occupiers', 'Assets', 'Tokyo comparison'), 'ja': ('主なテナント', '物件の特徴', '東京で例えると')}
SEL = {'en': 'Selective', 'ja': '選択的'}

def zones(city, lang):
    """The market column beside the map: one block per core zone (name, neighbourhoods, occupiers, assets, Tokyo comparison), then the
    selective areas. Same label-then-prose blocks as the rest of the column, so the type roles are unchanged."""
    zs, sel = ZONES[city][lang]; j = (lambda t: ja_markup(t)) if lang == 'ja' else (lambda t: t)
    out = ['          <div class="am-blocks">']
    for t, a, occ, ast, tok in zs:
        out.append(f'            <div class="am-block am-zone"><h3 class="am-k">{j(t)}</h3><p class="h-body am-p">{j(a)}</p>'
                   f'<dl class="am-zone-d"><dt>{DT[lang][0]}</dt><dd>{j(occ)}</dd><dt>{DT[lang][1]}</dt><dd>{j(ast)}</dd><dt>{DT[lang][2]}</dt><dd>{tok}</dd></dl></div>')
    out.append(f'            <div class="am-block am-zone am-zone--sel"><h3 class="am-k">{SEL[lang]}</h3><p class="h-body am-p">{j(sel)}</p></div>')
    out.append('          </div>')
    return '\n'.join(out) + '\n'

def span(res, city, k, cls, en, ja, lang):
    w = res[city]['labels']['wide'][k]; t = res[city]['labels']['tall'][k]; sw = SIDE[w['side']]; st = SIDE[t['side']]
    txt = en if lang == 'en' else ja_markup(ja)
    inside = (' ab-grp--in-w' if w['inside'] else '') + (' ab-grp--in-t' if t['inside'] else '') + (' ab-grp--hide-w' if w.get('hidden') else '') + (' ab-grp--hide-t' if t.get('hidden') else '')
    return (f'          <span class="ab-grp ab-grp--{cls} ab-grp--sm{inside}" style="--x:{w["x"]}%;--y:{w["y"]}%;--xt:{t["x"]}%;--yt:{t["y"]}%;'
            f'--tx:{sw[0]};--ty:{sw[1]};--txt:{st[0]};--tyt:{st[1]}" aria-hidden="true">{txt}</span>')

def css(lang):
    ff = "'DM Sans', sans-serif" if lang == 'en' else 'var(--jp)'
    return f"""  /* v4 maps (tools/maps/deck_v4.py): the deck's areas, every neighbourhood named, in the site's map colours (core 30% plum with a
     solid outline, selective 12% plum dashed; legend swatches .sw-prim / .sw-broad as before). Labels are ink on a cream halo and
     scale with the map; a label too large for its area in one frame is hidden in that frame (-w from 901px, -t below). */
  .am-map {{ container-type: inline-size; }}
  .ab-grp--sm {{ font-size: clamp(9px, 1.71cqw, 11px); }}
  @media (max-width: 900px) {{ .ab-grp--sm {{ font-size: clamp(9px, 2.78cqw, 11.5px); }} }}
  @media (min-width: 901px) {{ .ab-grp--hide-w {{ display: none; }} }}
  @media (max-width: 900px) {{ .ab-grp--hide-t {{ display: none; }} }}
  /* The market column: a core zone or the selective areas per block, each marked with its legend colour. */
  .am-zone .am-k {{ display: flex; align-items: center; color: var(--ink); font-weight: 500; }}
  .am-zone .am-k::before {{ content: ""; width: 10px; height: 10px; flex: none; margin-right: 8px; box-sizing: border-box; background: rgba(94, 61, 120, .30); border: 1.5px solid #3D2350; }}
  .am-zone--sel .am-k::before {{ background: rgba(94, 61, 120, .12); border: 1.5px dashed #7A5C92; }}
  .am-zone-d {{ display: grid; grid-template-columns: max-content 1fr; gap: 6px 14px; margin: 12px 0 0; font-family: {ff}; font-size: 13.5px; line-height: 1.5; }}
  .am-zone-d dt {{ color: var(--ink-3); }}
  .am-zone-d dd {{ margin: 0; color: var(--ink-2); }}
  /* end of v4 map styles */
"""
CSS_V4 = re.compile(r"  /\* v4 maps \(tools/maps/deck_v4\.py\).*?  /\* end of v4 map styles \*/\n", re.S)

def patch(path, lang, res, v):
    s = open(path, encoding='utf-8').read(); pre = '' if lang == 'en' else '../'
    s = s.replace('  .ab-grp--sm { font-size: 10.5px; }\n', '')
    if CSS_V4.search(s): s = CSS_V4.sub(lambda m: css(lang), s)
    else:
        s, n = re.subn(r'(  /\* end of map styles \*/\n)', lambda m: m.group(1) + css(lang), s); assert n == 1, ('css', path)
    # one wide-frame aspect for both cities from 901px
    s = s.replace('@media (min-width: 901px) { .am-market--amsterdam .am-map { aspect-ratio: 1.2; } }', '@media (min-width: 901px) { .am-market .am-map { aspect-ratio: 1.2; } }')
    for city in ('london', 'amsterdam'):
        s, n = re.subn(r'(src="%sassets/maps/%s-(?:wide|tall)\.svg)\?v=\d+"' % (re.escape(pre), city), r'\1?v=%d"' % v, s); assert n == 2, (city, n)
        s, n = re.subn(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg\?v=%d" alt=")[^"]*(")' % (re.escape(pre), city, v), lambda m: m.group(1) + ALT[city][lang] + m.group(2), s); assert n == 1
        m = re.search(r'(<img class="am-img am-img--tall" src="%sassets/maps/%s-tall\.svg\?v=%d"[^>]*>\n)((?:\s*<span class="ab-grp[^\n]*\n)+)' % (re.escape(pre), city, v), s); assert m, city
        s = s[:m.start(2)] + '\n'.join(span(res, city, k, c, en, ja, lang) for k, c, en, ja in res[city]['meta']) + '\n' + s[m.end(2):]
        # legend, then the notes (the zone panel that once sat here is removed)
        m = re.search(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg.*?<ul class="am-legend">.*?</ul>\n)(\s*<div class="am-zones">.*?\n          </div>\n)?(\s*<p class="am-note">)(.*?)(</p>)' % (re.escape(pre), city), s, re.S); assert m, city
        n1 = NOTE[city][lang]; n1 = ja_markup(n1) if lang == 'ja' else n1
        s = s[:m.start()] + m.group(1) + m.group(3).lstrip('\n') + n1 + m.group(5) + s[m.end():]
        # the market column: photo, then the zone blocks in place of the generic market text
        sec = s.index('id="%s"' % city)
        m = re.compile(r'(<div class="am-side">\n\s*<figure class="am-photo">[^\n]*\n)(\s*<div class="am-blocks">\n.*?\n          </div>\n)', re.S).search(s, sec); assert m, ('side', city)
        s = s[:m.start(2)] + zones(city, lang) + s[m.end(2):]
    open(path, 'w', encoding='utf-8').write(s)

def patch_all(repo, res, v=12):
    patch(repo + 'about.html', 'en', res, v); patch(repo + 'ja/about.html', 'ja', res, v)

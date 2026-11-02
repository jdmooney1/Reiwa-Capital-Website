"""Patch about.html / ja/about.html for the v4 maps (tools/maps/deck_v4.py): labels, alt text, notes, cache version."""
import re
from pages import SIDE, ja_markup

ALT = {'london': {
    'en': "Map of central London, with the Thames, Regent’s Park, Hyde Park, Green Park and St James’s Park shown. Indicative investment focus areas, not administrative boundaries. Core: the West End (Marylebone, Fitzrovia, Soho, Mayfair, St James’s and Covent Garden), the City of London and Westminster. Selective: Bloomsbury, Midtown, Farringdon, Clerkenwell, Shoreditch and Aldgate, and Southbank.",
    'ja': "ロンドン中心部の地図。テムズ川、リージェンツパーク、ハイドパーク、グリーンパーク、セントジェームズパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核：ウェストエンド（Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden）、シティ・オブ・ロンドン、ウェストミンスター。選択的：ブルームズベリー、ミッドタウン、ファリンドン、クラーケンウェル、ショーディッチ・オールドゲート、サウスバンク。"},
  'amsterdam': {
    'en': "Map of Amsterdam, with the canal ring around the historic centre, the IJ to the north, the Amstel and Vondelpark. Indicative investment focus areas, not administrative boundaries. Core: the Canal Belt (Grachtengordel), the Jordaan, Oud-Zuid and Zuidas, which lies on both sides of the A10. Selective: Centrum, Oud-West, West, Sloterdijk, Noord, Weesperbuurt/Plantage, De Pijp, Oost, Rivierenbuurt, Overamstel and Buitenveldert.",
    'ja': "アムステルダムの地図。歴史的中心部を囲む運河環状地帯、北のIJ湾、アムステル川、フォンデルパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核：カナルベルト（Grachtengordel）、ヨルダーン、アウド・ザウト、A10の両側にまたがるザイダス。選択的：セントルム、アウド・ウェスト、ウェスト、スローテルダイク、ノールト、ウェースペルブールト／プランタージュ、デ・パイプ、オースト、リヴィエレンブールト、オーフェルアムステル、バウテンフェルデルト。"}}
NOTE = {'london': {'en': 'Indicative focus areas, not administrative boundaries. West End core: Marylebone, Fitzrovia, Soho, Mayfair, St James’s, Covent Garden. Midtown: Holborn.',
                   'ja': '投資対象エリアの目安であり、行政上の境界ではありません。ウェストエンドの中核：Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden。ミッドタウン：ホルボーン。'},
        'amsterdam': {'en': 'Indicative focus areas, not administrative boundaries. Oud-Zuid includes the Museumkwartier.',
                      'ja': '投資対象エリアの目安であり、行政上の境界ではありません。アウド・ザウトはミュージアム地区を含みます。'}}

def span(res, city, k, cls, en, ja, lang):
    w = res[city]['labels']['wide'][k]; t = res[city]['labels']['tall'][k]; sw = SIDE[w['side']]; st = SIDE[t['side']]
    txt = en if lang == 'en' else ja_markup(ja)
    return (f'          <span class="ab-grp ab-grp--{cls} ab-grp--sm" style="--x:{w["x"]}%;--y:{w["y"]}%;--xt:{t["x"]}%;--yt:{t["y"]}%;'
            f'--tx:{sw[0]};--ty:{sw[1]};--txt:{st[0]};--tyt:{st[1]}" aria-hidden="true">{txt}</span>')

def patch(path, lang, res, v):
    s = open(path, encoding='utf-8').read(); pre = '' if lang == 'en' else '../'
    for city in ('london', 'amsterdam'):
        s, n = re.subn(r'(src="%sassets/maps/%s-(?:wide|tall)\.svg)\?v=\d+"' % (re.escape(pre), city), r'\1?v=%d"' % v, s); assert n == 2, (city, n)
        s, n = re.subn(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg\?v=%d" alt=")[^"]*(")' % (re.escape(pre), city, v), lambda m: m.group(1) + ALT[city][lang] + m.group(2), s); assert n == 1
        m = re.search(r'(<img class="am-img am-img--tall" src="%sassets/maps/%s-tall\.svg\?v=%d"[^>]*>\n)((?:\s*<span class="ab-grp[^\n]*\n)+)' % (re.escape(pre), city, v), s); assert m, city
        s = s[:m.start(2)] + '\n'.join(span(res, city, k, c, en, ja, lang) for k, c, en, ja in res[city]['meta']) + '\n' + s[m.end(2):]
        m = re.search(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg.*?<ul class="am-legend">.*?</ul>\n\s*<p class="am-note">)(.*?)(</p>)' % (re.escape(pre), city), s, re.S); assert m, city
        n1 = NOTE[city][lang]; n1 = ja_markup(n1) if lang == 'ja' else n1
        s = s[:m.start(2)] + n1 + s[m.end(2):]
    open(path, 'w', encoding='utf-8').write(s)

SM = '  .ab-grp--sm { font-size: 10.5px; }\n'
def patch_all(repo, res, v=10):
    for f in ('about.html', 'ja/about.html'):
        s = open(repo + f, encoding='utf-8').read()
        if '.ab-grp--sm' not in s:
            s, n = re.subn(r'(  \.ab-grp--core \{[^\n]*\n)', lambda m: m.group(1) + SM, s); assert n == 1
            open(repo + f, 'w', encoding='utf-8').write(s)
    patch(repo + 'about.html', 'en', res, v); patch(repo + 'ja/about.html', 'ja', res, v)

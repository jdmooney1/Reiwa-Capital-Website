"""Write the v3 map assets and patch about.html / ja/about.html (labels, legend, note, alt text, cache version)."""
import json, re, sys, shutil, os
import render as R
OUT='out/'
def load_results(): return {c:json.load(open(OUT+f'{c}.json')) for c in ['london','amsterdam']}
RES={}
SIDE={'c':('-50%','-50%'),'r':('0','-50%'),'l':('-100%','-50%'),'b':('-50%','0'),'t':('-50%','-100%')}
def ja_markup(t):
    lines=t.split('<br>'); out=[]
    for l in lines: out.append(re.sub(r'[゠-ヿ]{3,}',lambda m:f'<span class="jt">{m.group(0)}</span>',l))
    return '<br>'.join(out)
def span(city,m,lang):
    w=RES[city]['labels']['wide'][m['key']]; t=RES[city]['labels']['tall'][m['key']]
    sw=SIDE[w['side']]; st=SIDE[t['side']]
    txt=m['en'] if lang=='en' else ja_markup(m['ja'])
    cls='core' if m['cls']=='core' else 'sel'
    return (f'          <span class="ab-grp ab-grp--{cls}" style="--x:{w["x"]}%;--y:{w["y"]}%;--xt:{t["x"]}%;--yt:{t["y"]}%;'
            f'--tx:{sw[0]};--ty:{sw[1]};--txt:{st[0]};--tyt:{st[1]}" aria-hidden="true">{txt}</span>')
ALT={'london':{'en':"Map of central London, with the Thames, Hyde Park, Regent’s Park, Green Park and St James’s Park shown. Indicative investment focus areas, not administrative boundaries. Core: the West End (Marylebone, Fitzrovia, Soho, Mayfair, St James’s and Covent Garden). Selective: Midtown (Holborn), Bloomsbury, the City of London, Westminster, and Kensington and Chelsea.",
  'ja':"ロンドン中心部の地図。テムズ川、ハイドパーク、リージェンツパーク、グリーンパーク、セントジェームズパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核：ウェストエンド（Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden）。選択的：ミッドタウン（ホルボーン）、ブルームズベリー、シティ・オブ・ロンドン、ウェストミンスター、ケンジントン・チェルシー。"},
 'amsterdam':{'en':"Map of Amsterdam, with the canal ring around the historic centre, the IJ to the north, the Amstel and Vondelpark. Indicative investment focus areas, not administrative boundaries. Core: the Canal Belt (Grachtengordel), the Jordaan, Oud-Zuid and Zuidas, which lies on both sides of the A10. Selective: Oud-West, Weesperbuurt/Plantage, De Pijp, Oost and Rivierenbuurt.",
  'ja':"アムステルダムの地図。歴史的中心部を囲む運河環状地帯、北のIJ湾、アムステル川、フォンデルパークを表示。投資対象として想定するエリアの目安であり、行政上の境界ではありません。中核：カナルベルト（Grachtengordel）、ヨルダーン、アウド・ザウト、A10の両側にまたがるザイダス。選択的：アウド・ウェスト、ウェースペルブールト／プランタージュ、デ・パイプ、オースト、リヴィエレンブールト。"}}
NOTE={'london':{'en':('Indicative focus areas, not administrative boundaries. West End: Marylebone, Fitzrovia, Soho, Mayfair, St James’s, Covent Garden.',
                      'Map data: ONS and OS boundaries &copy; Crown copyright (OGL v3.0); &copy; OpenStreetMap contributors; Overture Maps Foundation.'),
                'ja':('投資対象エリアの目安であり、行政上の境界ではありません。ウェストエンド：Marylebone、Fitzrovia、Soho、Mayfair、St James’s、Covent Garden。',
                      '地図データ：ONS・OS境界 &copy; Crown copyright（OGL v3.0）、&copy; OpenStreetMap contributors、Overture Maps Foundation。')},
      'amsterdam':{'en':('Indicative focus areas, not administrative boundaries.',
                         'Map data: Gemeente Amsterdam; CBS (CC BY 4.0); &copy; OpenStreetMap contributors; Overture Maps Foundation.'),
                   'ja':('投資対象エリアの目安であり、行政上の境界ではありません。',
                         '地図データ：アムステルダム市、CBS（CC BY 4.0）、&copy; OpenStreetMap contributors、Overture Maps Foundation。')}}
CSS_NEW=re.compile(r"  /\* The focus areas, their outlines.*?  /\* end of map styles \*/\n",re.S)
CSS_OLD=re.compile(r"  /\* Grouped geography is the drawn layer.*?  \.sw-broad \{[^\n]*\n",re.S)
def css(lang):
    ff="'DM Sans', sans-serif" if lang=='en' else 'var(--jp)'
    lh='1.3' if lang=='en' else '1.35'
    # The legend swatch, note and attribution rules are shared by both pages.
    return f"""  /* The focus areas, their outlines and their leader lines are drawn in the SVG, in the same projection and frame as the
     base map. The labels are HTML so they use the page's type; each is set in percent of the frame (--x/--y on the wide
     frame, --xt/--yt on the tall one) and hangs from the edge that meets its leader (--tx/--ty, --txt/--tyt). The frame
     switches at 900px, where the tall image takes over. */
  .ab-grp {{ position: absolute; left: var(--x); top: var(--y); transform: translate(var(--tx, -50%), var(--ty, -50%)); padding: 1px 3px; box-sizing: border-box; font-family: {ff}; font-weight: 500; font-size: 12px; line-height: {lh}; letter-spacing: 0.01em; color: var(--ink); white-space: nowrap; text-align: center; pointer-events: none; z-index: 3; text-shadow: 0 0 2px var(--cream), 0 0 3px var(--cream), 0 0 6px rgba(247,243,234,.92); }}
  .ab-grp--core {{ font-weight: 600; }}
  @media (max-width: 900px) {{ .ab-grp {{ left: var(--xt); top: var(--yt); transform: translate(var(--txt, -50%), var(--tyt, -50%)); }} }}
  @media (max-width: 620px) {{ .am-map {{ margin-left: calc(-1 * var(--gutter)); margin-right: calc(-1 * var(--gutter)); border-left: 0; border-right: 0; }} }}

  .am-legend {{ list-style: none; display: flex; flex-wrap: wrap; gap: 8px var(--fluid-s); margin: 16px 0 0; padding: 0; }}
  /* The label may contain inline spans (katakana runs are kept whole), so the swatch carries the gap. */
  .am-legend li {{ display: flex; align-items: center; gap: 0; font-family: {ff}; font-size: 13px; color: var(--ink-2); }}
  .am-legend .sw {{ width: 13px; height: 13px; flex: none; margin-right: 9px; box-sizing: border-box; }}
  .sw-prim  {{ background: rgba(94, 61, 120, .30); border: 1.5px solid #3D2350; }}
  .sw-broad {{ background: rgba(94, 61, 120, .12); border: 1.5px dashed #7A5C92; }}
  .am-note {{ margin: 10px 0 0; max-width: 62ch; font-family: {ff}; font-size: 12.5px; line-height: 1.55; color: var(--ink-3); }}
  .am-note + .am-note {{ margin-top: 4px; font-size: 12px; }}
  /* end of map styles */
"""
def patch(path,lang):
    s=open(path,encoding='utf-8').read(); pre='' if lang=='en' else '../'
    s,n=CSS_NEW.subn(lambda m:css(lang),s)
    if n==0: s,n=CSS_OLD.subn(lambda m:css(lang),s)
    assert n==1,('css',path,n)
    for city in ['london','amsterdam']:
        s,n=re.subn(r'(src="%sassets/maps/%s-(?:wide|tall)\.svg)\?v=\d+"'%(re.escape(pre),city),r'\1?v=6"',s); assert n==2,(city,n)
        s,n=re.subn(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg\?v=6" alt=")[^"]*(")'%(re.escape(pre),city),lambda m:m.group(1)+ALT[city][lang]+m.group(2),s); assert n==1
        m=re.search(r'(<img class="am-img am-img--tall" src="%sassets/maps/%s-tall\.svg\?v=6"[^>]*>\n)((?:\s*<span class="ab-grp[^\n]*\n)+)'%(re.escape(pre),city),s); assert m,city
        s=s[:m.start(2)]+'\n'.join(span(city,g,lang) for g in R.GROUPS[city])+'\n'+s[m.end(2):]
        # the note follows the legend list of this city's map
        m=re.search(r'(<img class="am-img am-img--wide" src="%sassets/maps/%s-wide\.svg.*?<ul class="am-legend">.*?</ul>\n)(\s*<p class="am-note">.*?</p>\n\s*<p class="am-note">.*?</p>\n)?'%(re.escape(pre),city),s,re.S); assert m,city
        n1,n2=NOTE[city][lang]
        if lang=='ja': n1,n2=ja_markup(n1),ja_markup(n2)
        s=s[:m.start()]+m.group(1)+f'          <p class="am-note">{n1}</p>\n          <p class="am-note">{n2}</p>\n'+s[m.end():]
    open(path,'w',encoding='utf-8').write(s)
def run(repo):
    repo=repo.rstrip('/')+'/'; RES.update(load_results())
    for city in ['london','amsterdam']:
        for v in ['wide','tall']: shutil.copy(OUT+f'{city}-{v}.svg',repo+f'assets/maps/{city}-{v}.svg')
    patch(repo+'about.html','en'); patch(repo+'ja/about.html','ja')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the Japanese display serif subset.

The site sets Japanese display headings in Shippori Mincho Medium. The full
Japanese face is ~1.4MB per weight, so only the glyphs the site actually uses
are shipped, plus the whole kana range, ASCII and Japanese punctuation, so
ordinary copy edits do not fall outside the subset.

Anything outside it still renders: browsers fall back per glyph, so an unknown
kanji is drawn by the next family in --font-jp-serif rather than as tofu. It
will look different, though, so run this after changing Japanese heading copy:

    python3 tools/subset-ja-serif.py            # regenerate
    python3 tools/subset-ja-serif.py --check    # fail if a glyph is missing

Requires: node/npm (fetches the OFL font from npm), fonttools, brotli.
Font: Shippori Mincho, SIL Open Font License 1.1 — see
assets/fonts/OFL-ShipporiMincho.txt.
"""
import argparse, glob, io, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = '@fontsource/shippori-mincho@5.3.0'
WEIGHT = '500'
OUT = os.path.join(ROOT, 'assets/fonts/ShipporiMincho-Medium.subset.woff2')

# Elements the stylesheet renders in the display serif on Japanese pages.
DISPLAY = re.compile(r'<(h1|h2|h3)\b[^>]*>(.*?)</\1>|<([a-z]+)\b[^>]*class="[^"]*\bjp-display\b[^"]*"[^>]*>(.*?)</\3>', re.S)

KANA = ''.join(chr(c) for c in list(range(0x3041, 0x3097)) + list(range(0x309B, 0x30FF)))
ASCII = ''.join(chr(c) for c in range(0x20, 0x7F))
PUNCT = '、。・「」『』（）〈〉《》【】〔〕—…‥ー〜％＆／：；！？，．０１２３４５６７８９〇々'


def used_chars():
    chars = set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'ja/**/*.html'), recursive=True)):
        s = io.open(f, encoding='utf-8').read()
        body = s[s.index('<body'):] if '<body' in s else s
        for m in DISPLAY.finditer(body):
            t = m.group(2) or m.group(4) or ''
            t = re.sub(r'<[^>]+>', '', t)
            t = re.sub(r'&[a-z]+;|&#\d+;', '', t)
            chars |= set(t.strip())
    return chars


def source_font(tmp):
    subprocess.run(['npm', 'pack', PKG], cwd=tmp, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tgz = [f for f in os.listdir(tmp) if f.endswith('.tgz')][0]
    member = 'package/files/shippori-mincho-japanese-%s-normal.woff2' % WEIGHT
    subprocess.run(['tar', 'xzf', tgz, member, 'package/LICENSE'], cwd=tmp, check=True)
    return os.path.join(tmp, member), os.path.join(tmp, 'package/LICENSE')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true',
                    help='report glyphs the shipped subset is missing, and exit non-zero')
    args = ap.parse_args()

    wanted = used_chars() | set(KANA) | set(ASCII) | set(PUNCT)

    if args.check:
        from fontTools.ttLib import TTFont
        have = set()
        for t in TTFont(OUT)['cmap'].tables:
            have |= {chr(c) for c in t.cmap}
        missing = sorted(c for c in used_chars() if c not in have and c.strip())
        print('display glyphs in use: %d | shipped: %d | missing: %d'
              % (len(used_chars()), len(have), len(missing)))
        if missing:
            print('MISSING:', ''.join(missing))
            return 1
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        src, lic = source_font(tmp)
        subprocess.run([sys.executable, '-m', 'fontTools.subset', src,
                        '--text=' + ''.join(sorted(wanted)),
                        '--flavor=woff2', '--layout-features=*', '--no-hinting',
                        '--desubroutinize', '--output-file=' + OUT], check=True)
        dest_lic = os.path.join(ROOT, 'assets/fonts/OFL-ShipporiMincho.txt')
        if not os.path.exists(dest_lic):
            io.open(dest_lic, 'w', encoding='utf-8').write(io.open(lic, encoding='utf-8').read())
    print('wrote %s — %d glyphs, %.1f KB' % (OUT, len(wanted), os.path.getsize(OUT) / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())

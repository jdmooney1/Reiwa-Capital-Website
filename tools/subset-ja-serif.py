#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the Japanese display serif subset.

The site sets Japanese display headings in Shippori Mincho Medium. The full
Japanese face is ~1.4MB per weight, so only the glyphs the site actually uses
are shipped.

The glyph list is derived from the RENDERED pages, not from the markup. The
serif stack is applied by page CSS to h4 and to spans as well as to h1-h3, so
scraping tags misses glyphs - that is how 43 kanji, including every character
of the headings 収益型 and 再生型, ended up outside the subset and painting in
a fallback face. tools/ja-display-glyphs.txt holds the derived list; regenerate
it by loading all 16 pages, opening every panel, tab and disclosure, and
collecting the own-text of every element whose computed font-family contains
"Shippori".

Nothing outside the list is shipped, so a Japanese copy edit that introduces a
new kanji will fall back until this is re-run. --check exists to catch exactly
that; run it after changing Japanese display copy:

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

# Derived from the rendered pages, not from the markup. See the module docstring.
GLYPHS = os.path.join(ROOT, 'tools/ja-display-glyphs.txt')


def used_chars():
    if not os.path.exists(GLYPHS):
        sys.exit('missing %s - regenerate it from the rendered pages first' % GLYPHS)
    return {c for c in io.open(GLYPHS, encoding='utf-8').read() if c.strip()}


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

    wanted = used_chars()

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

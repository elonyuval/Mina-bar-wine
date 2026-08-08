#!/usr/bin/env python3
"""Crop a venue's photos into every size the page needs.

Owners send phone photos and Instagram screenshots at whatever aspect ratio
they happen to be. The page needs a wide hero, a portrait, square gallery
tiles, and a 1.91:1 social card. Doing that by hand is tedious and easy to get
subtly wrong; ImageOps.fit crops to the exact ratio without ever distorting.

    python3 build_images.py --hero bar.jpg --portrait shelf.jpg \
        --gallery a.jpg b.jpg c.jpg d.jpg --out assets/img/

The focus arguments matter for portrait sources used as a wide hero: the
default centre crop often lands on a table edge. --hero-focus 0.42 keeps the
crop slightly above centre, where faces and glassware usually are.
"""

import argparse
import os

from PIL import Image, ImageOps

# Wider than 2x display size is wasted bytes on a page that must load on 4G at
# the door of a restaurant. These are the sizes the layout actually renders at.
SIZES = {
    'hero':     (1800, 1200),
    'about':    (900, 1200),
    'gallery':  (900, 900),
    'og':       (1200, 630),
}


def fit(src, size, out, focus=(0.5, 0.5), quality=82):
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    im = ImageOps.fit(im, size, Image.LANCZOS, centering=focus)
    im.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)
    print('%-28s %s' % (os.path.basename(out), '%dx%d' % im.size))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--hero', required=True, help='wide atmosphere shot for the top of the page')
    ap.add_argument('--portrait', help='vertical shot for the about section (defaults to --hero)')
    ap.add_argument('--gallery', nargs='*', default=[], help='photos for the gallery strip')
    ap.add_argument('--out', required=True)
    ap.add_argument('--hero-focus', type=float, default=0.42,
                    help='vertical crop centre for the hero, 0=top 1=bottom (default 0.42)')
    ap.add_argument('--portrait-focus', type=float, default=0.5)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    o = lambda n: os.path.join(args.out, n)

    fit(args.hero, SIZES['hero'], o('hero.jpg'), (0.5, args.hero_focus), quality=80)
    fit(args.hero, SIZES['og'], o('og.jpg'), (0.5, args.hero_focus), quality=80)
    fit(args.portrait or args.hero, SIZES['about'], o('about.jpg'), (0.5, args.portrait_focus))

    for i, src in enumerate(args.gallery, 1):
        fit(src, SIZES['gallery'], o('gallery-%d.jpg' % i), (0.5, 0.5))

    if args.gallery:
        # The grid is set up for a 4-across strip; other counts need a CSS tweak.
        n = len(args.gallery)
        if n not in (3, 4, 6, 8):
            print('note: %d gallery images — adjust .gallery-grid columns to suit' % n)

    total = sum(os.path.getsize(o(f)) for f in os.listdir(args.out)
                if f.endswith(('.jpg', '.png')))
    print('total image weight: %.2f MB' % (total / 1024 / 1024))


if __name__ == '__main__':
    main()

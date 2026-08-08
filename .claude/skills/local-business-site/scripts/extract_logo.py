#!/usr/bin/env python3
"""Turn a logo screenshot into transparent PNGs plus a favicon.

Owners almost never have the vector file. What they have is a screenshot of the
logo as posted to Instagram: light marks on a solid brand-coloured background,
no alpha channel. Keying that out by colour distance gives ragged edges, because
the anti-aliased pixels around every stroke are blends of mark and background.

Deriving alpha from luminance instead treats each pixel's brightness as "how
much mark is here", which is exactly what the blend encodes — so the edges come
back clean. The marks are then re-coloured, giving one variant for light
surfaces and one for dark.

    python3 extract_logo.py logo-screenshot.jpg out/
    python3 extract_logo.py logo.jpg out/ --dark-logo   # dark marks on light bg

Prints the sampled background colour. Use it as the site's brand token rather
than eyeballing a hex — it is the owner's actual brand colour.
"""

import argparse
import os
from collections import Counter

from PIL import Image


def luminance(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def dominant_colour(im, sample=4):
    """Most common colour in a downsampled copy — the background of a logo card."""
    small = im.resize((max(1, im.width // sample), max(1, im.height // sample))).convert('RGB')
    colours = small.getcolors(maxcolors=small.width * small.height)
    return max(colours, key=lambda c: c[0])[1]


def mark_bbox(im, bg, dark_logo, step=2):
    """Bounding box of pixels that differ from the background in the mark's direction."""
    bg_lum = luminance(bg)
    px = im.load()
    xs, ys = [], []
    for y in range(0, im.height, step):
        for x in range(0, im.width, step):
            lum = luminance(px[x, y])
            hit = (bg_lum - lum) > 60 if dark_logo else (lum - bg_lum) > 60
            if hit:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit('No logo marks found. Check --dark-logo, or crop the image first.')
    return min(xs), min(ys), max(xs), max(ys)


def render(crop, bg, colour, dark_logo):
    """Alpha from luminance distance to the background; RGB replaced by `colour`."""
    bg_lum = luminance(bg)
    span = bg_lum if dark_logo else (255 - bg_lum)
    if span < 1:
        raise SystemExit('Background and marks are too close in brightness to separate.')

    out = Image.new('RGBA', crop.size, (0, 0, 0, 0))
    src, dst = crop.load(), out.load()
    for y in range(crop.height):
        for x in range(crop.width):
            lum = luminance(src[x, y])
            a = (bg_lum - lum) / span if dark_logo else (lum - bg_lum) / span
            a = 0.0 if a < 0 else (1.0 if a > 1 else a)
            if a > 0.01:
                dst[x, y] = (colour[0], colour[1], colour[2], int(a * 255))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source')
    ap.add_argument('outdir')
    ap.add_argument('--dark-logo', action='store_true',
                    help='marks are darker than the background (default assumes lighter)')
    ap.add_argument('--pad', type=int, default=10, help='margin around the detected marks')
    ap.add_argument('--favicon-frac', type=float, default=0.25,
                    help='top fraction of the lockup to crop for the favicon (the emblem)')
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    im = Image.open(args.source).convert('RGB')
    bg = dominant_colour(im)
    print('background : #%02x%02x%02x  <- use as the brand colour token' % bg)

    x0, y0, x1, y1 = mark_bbox(im, bg, args.dark_logo)
    p = args.pad
    crop = im.crop((max(0, x0 - p), max(0, y0 - p),
                    min(im.width, x1 + p), min(im.height, y1 + p)))
    print('logo crop  : %dx%d' % crop.size)

    render(crop, bg, bg, args.dark_logo).save(
        os.path.join(args.outdir, 'logo-brand.png'), optimize=True)
    on_dark = render(crop, bg, (255, 255, 255), args.dark_logo)
    on_dark.save(os.path.join(args.outdir, 'logo-white.png'), optimize=True)

    # Favicon: the emblem usually sits above the wordmark, and the full lockup
    # is illegible at 32px. Crop the top slice and centre it on the brand colour.
    # The source must be the rendered RGBA version — the raw crop has no alpha
    # channel and cannot act as its own paste mask.
    emblem = on_dark.crop((0, 0, on_dark.width,
                           max(1, int(on_dark.height * args.favicon_frac))))
    # The top slice is full-width, so the emblem floats in empty space. Trimming
    # to the alpha bounding box is what makes it fill the tab icon.
    emblem = emblem.crop(emblem.getbbox())
    side = int(max(emblem.size) * 1.25)
    fav = Image.new('RGBA', (side, side), bg + (255,))
    fav.alpha_composite(emblem, ((side - emblem.width) // 2, (side - emblem.height) // 2))
    fav.convert('RGB').resize((128, 128), Image.LANCZOS).save(
        os.path.join(args.outdir, 'favicon.png'), optimize=True)

    print('wrote      : logo-brand.png, logo-white.png, favicon.png -> %s' % args.outdir)
    print('check the two PNGs before shipping — if edges look chewed, try --dark-logo')


if __name__ == '__main__':
    main()

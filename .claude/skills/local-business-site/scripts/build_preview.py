#!/usr/bin/env python3
"""Flatten the site into one self-contained HTML file for a shareable preview.

Owners want a link before the domain exists. Artifact hosting runs a strict CSP
that blocks every external host, so the page has to carry everything it needs:
CSS and JS inlined, images as data URIs, no iframes, no font CDN.

    python3 build_preview.py --out preview.html

Then publish the output with the Artifact tool.

The trap worth knowing: the artifact wrapper supplies its own <html> element
with no dir attribute. Extracting just the <body> silently drops dir="rtl" and
the whole page flips to LTR — it looks completely broken and the cause is
invisible in the source you wrote. This script sets direction from inside the
content, both as a CSS rule and as an attribute on the root element.
"""

import argparse
import base64
import os
import re


def data_uri(path):
    mime = 'image/png' if path.lower().endswith('.png') else 'image/jpeg'
    with open(path, 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


# CSS is the fallback; the attribute is what the bidi algorithm actually reads
# for base direction, so both are set.
RTL_CSS = """/* The host <html> has no dir attribute, so direction is set here. */
:root, body { direction: rtl; unicode-bidi: isolate; }

"""
SET_DIR = ('<script>document.documentElement.setAttribute("dir","rtl");'
           'document.documentElement.setAttribute("lang","he");</script>')

# A map iframe cannot load under the CSP; a linked card carries the same
# information and does not render as an empty grey box.
MAP_CARD = """<div class="map-card">
          <span class="pin" aria-hidden="true">&#128205;</span>
          <h3>{address}</h3>
          <p>{hours}</p>
          <a class="btn btn-ghost" href="{maps_url}" target="_blank" rel="noopener">פתחו במפות Google</a>
        </div>"""

MAP_CSS = """

/* ---------- Location card (replaces the CSP-blocked map iframe) ---------- */
.map-card {
  display: flex; flex-direction: column; justify-content: center; gap: 1.4rem;
  min-height: 440px; padding: 3rem 2.5rem; text-align: center;
  background: var(--surface-dark, #122115); color: var(--cream, #f6f1e8);
  border-radius: var(--radius, 4px); box-shadow: var(--shadow, 0 18px 50px rgba(0,0,0,.12));
}
.map-card .pin { font-size: 2rem; line-height: 1; }
.map-card h3 { font-size: 1.6rem; margin: 0; color: inherit; }
.map-card p { margin: 0; font-size: .95rem; opacity: .85; }
.map-card .btn-ghost { align-self: center; }
@media (max-width: 720px) { .map-card { min-height: 300px; padding: 2.5rem 1.5rem; } }
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--html', default='index.html')
    ap.add_argument('--css', default='assets/css/style.css')
    ap.add_argument('--js', nargs='*', default=['assets/js/menu-data.js', 'assets/js/main.js'],
                    help='in load order')
    ap.add_argument('--img-dir', default='assets/img')
    ap.add_argument('--out', required=True)
    ap.add_argument('--address', default='')
    ap.add_argument('--hours', default='')
    ap.add_argument('--maps-url', default='https://www.google.com/maps')
    args = ap.parse_args()

    html = open(args.html, encoding='utf-8').read()
    css = open(args.css, encoding='utf-8').read()

    # Images: inline every asset the page references, in HTML and in CSS.
    for name in sorted(os.listdir(args.img_dir)):
        if not name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        ref = '%s/%s' % (args.img_dir, name)
        if ref not in html and name not in css:
            continue
        uri = data_uri(os.path.join(args.img_dir, name))
        html = html.replace(ref, uri)
        css = re.sub(r"url\(['\"]?[^'\")]*%s['\"]?\)" % re.escape(name), "url('%s')" % uri, css)

    css = RTL_CSS + css + MAP_CSS

    # Fonts: no CDN reaches the page, so fall back to faces the device already has.
    css = re.sub(r"(--serif:\s*)[^;]+;", r"\1'Frank Ruhl Libre', 'Narkisim', Georgia, serif;", css)
    css = re.sub(r"(--sans:\s*)[^;]+;",
                 r"\1system-ui, -apple-system, 'Segoe UI', 'Noto Sans Hebrew', Arial, sans-serif;", css)

    html = re.sub(r'<div class="map-wrap">.*?</div>',
                  MAP_CARD.format(address=args.address, hours=args.hours, maps_url=args.maps_url),
                  html, flags=re.S)

    # Strip what the wrapper provides or the CSP rejects.
    for pat in [r'<link rel="preconnect"[^>]*>\s*',
                r'<link[^>]*fonts\.googleapis[^>]*>\s*',
                r'<link rel="icon"[^>]*>\s*',
                r'<link rel="stylesheet"[^>]*>\s*',
                r'<meta property="og:image[^>]*>\s*',
                r'<meta name="twitter:[^>]*>\s*']:
        html = re.sub(pat, '', html)

    title = re.search(r'<title>(.*?)</title>', html, re.S)
    body = re.search(r'<body[^>]*>(.*?)</body>', html, re.S).group(1)
    body = re.sub(r'<script src="[^"]*"></script>\s*', '', body)

    scripts = '\n'.join('<script>\n%s\n</script>' % open(p, encoding='utf-8').read()
                        for p in args.js)

    out = '%s\n%s\n<style>\n%s\n</style>\n%s\n%s\n' % (
        '<title>%s</title>' % title.group(1) if title else '', SET_DIR, css, body.strip(), scripts)

    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(out)

    leftover = re.findall(r'(?:src|href)="(?!#|data:|tel:|mailto:|https://)', out)
    print('%s  %.2f MB' % (args.out, len(out.encode()) / 1024 / 1024))
    print('iframes: %d | unresolved local refs: %d' % (out.count('<iframe'), len(leftover)))
    if out.count('<iframe') or leftover:
        print('^ these will be blocked by the CSP — fix before publishing')
    if len(out.encode()) > 16 * 1024 * 1024:
        print('^ over the 16MB artifact limit — recompress the images')


if __name__ == '__main__':
    main()

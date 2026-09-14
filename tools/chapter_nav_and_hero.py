#!/usr/bin/env python3
"""Navy hero banners and a Return to Chapter List link for the Federal chapters.

Mirrors the Texas pass, but the Federal chapters use three different header
markups, so the link is anchored to whichever flex container each file actually
has:

  A. <div class="header"><div class="header-content">   -> inject into header-content
  B. <div class="header">    (flexes directly)          -> inject into header
  C. <header class="header"> (flexes directly)          -> inject into header

The link is visible by default so it always works on the published site, and is
removed only when index.html is positively confirmed missing, so a chapter
imported into Canvas on its own never shows a link that 404s.

Safe to re-run; every step is idempotent.
"""
import glob, re, sys

HERO_OLD = "linear-gradient(135deg, #00788a, #1a8fa0)"
HERO_NEW = "linear-gradient(135deg, #002b5c, #00406e)"

CSS = """
        /* Return to chapter list */
        .back-to-list {
            display: inline-block;
            flex-shrink: 0;
            background: rgba(255, 255, 255, 0.14);
            color: #ffffff;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            padding: 0.4rem 0.8rem;
            border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 999px;
            white-space: nowrap;
            transition: background 0.2s ease;
        }
        .back-to-list:hover,
        .back-to-list:focus { background: rgba(255, 255, 255, 0.28); }
        .back-to-list:focus-visible {
            outline: 3px solid #FFD54F;
            outline-offset: 2px;
        }
        .back-to-list[hidden] { display: none; }
        @media (max-width: 768px) {
            .back-to-list { align-self: center; }
        }
"""

LINK = ('        <a href="index.html" class="back-to-list" id="backToList">'
        '&#8592; All Chapters</a>\n')

SCRIPT = """
    <script>
    /* Visible by default so it always works on the published site, even if
       fetch is unavailable. Removed only when index.html is confirmed missing
       (a chapter used standalone), so students never get a link that 404s. */
    (function () {
        var el = document.getElementById('backToList');
        if (!el || !window.fetch) return;
        try {
            fetch('index.html', { method: 'HEAD' })
                .then(function (r) { if (!r || !r.ok) { el.hidden = true; } })
                .catch(function () { el.hidden = true; });
        } catch (e) { /* leave visible */ }
    })();
    </script>
"""

# Ordered: header-content wins when present, since it is the flex container.
ANCHORS = [
    ("header-content", re.compile(r'(<div class="header-content">\s*\n)')),
    ("div.header",     re.compile(r'(<div class="header">\s*\n)')),
    ("header element", re.compile(r'(<header class="header">\s*\n)')),
]


def patch(path):
    c = open(path, encoding="utf-8").read()
    orig, did, variant = c, [], None

    if HERO_OLD in c:
        c = c.replace(HERO_OLD, HERO_NEW)
        did.append("hero")

    if ".back-to-list {" not in c:
        m = re.search(r"\n(\s*)\.hero-section \{", c)
        if not m:
            return None, None, "no .hero-section rule to anchor CSS"
        c = c[:m.start()] + "\n" + CSS + c[m.start():]
        did.append("css")

    if 'id="backToList"' not in c:
        for name, pat in ANCHORS:
            m = pat.search(c)
            if m:
                c = c[:m.end()] + LINK + c[m.end():]
                did.append("link")
                variant = name
                break
        else:
            return None, None, "no header container found"
    else:
        for name, pat in ANCHORS:
            if pat.search(c):
                variant = name
                break

    if "backToList" in c and "fetch('index.html'" not in c:
        i = c.rfind("</body>")
        if i == -1:
            return None, None, "no </body>"
        c = c[:i] + SCRIPT + c[i:]
        did.append("script")

    if c == orig:
        return [], variant, None
    open(path, "w", encoding="utf-8").write(c)
    return did, variant, None


def main():
    files = sorted(glob.glob("Chapter *(Expanded Edition).html"))
    if not files:
        sys.exit("No chapter files found. Run from the repo root.")
    errs = 0
    for f in files:
        did, variant, err = patch(f)
        if err:
            print(f"  ERROR {f}: {err}"); errs += 1
        else:
            name = f.split(" - ")[0]
            print(f"  {name:12s} [{variant or '-':15s}] "
                  f"{', '.join(did) if did else 'already current'}")
    print(f"\n{len(files)} chapters processed, {errs} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

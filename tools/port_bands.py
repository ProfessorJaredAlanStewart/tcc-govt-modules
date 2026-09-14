#!/usr/bin/env python3
"""Give the Federal index the same scroll-band treatment as the Texas index.

The page was one flat container holding every section on a single background,
with the tab strip in the same bare container. This splits each section into
its own full-width tinted band and folds the tabs into the chapters band, so
the page reads as distinct zones while scrolling and there is no pale strip
under the hero.

Section order and tints mirror the Texas page so the two courses feel like one
family. Idempotent: re-running is a no-op.
"""
import re, sys

PATH = "index.html"

BAND_CSS = """
        /* ── SCROLL BANDS ──
           Each section gets a full-width tint so the page reads as distinct
           zones while scrolling. All bands are light, so the existing dark
           body copy keeps its contrast everywhere. Mirrors the Texas index. */
        .band {
            padding: 3.25rem 0;
            position: relative;
        }
        .band > .container {
            padding-top: 0;
            padding-bottom: 0;
        }
        /* The colour change is the divider; this hairline just crisps the seam. */
        .band + .band { border-top: 1px solid rgba(0, 43, 92, 0.07); }
        .band :where(#chapters, #howto, #scoring, #submit, #tips, #faq,
                     .instructor-tools) { margin-top: 0; }
        @media (max-width: 768px) {
            .band { padding: 2.25rem 0; }
        }
        @media (prefers-reduced-motion: no-preference) {
            .band { scroll-margin-top: 1rem; }
        }
        .band-chapters {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(0,43,92,0.05) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(176,125,43,0.07) 0%, transparent 46%),
                #f7f3ea;
        }
        .band-tools {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(0,120,138,0.10) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(0,43,92,0.05) 0%, transparent 46%),
                #eaf3f5;
        }
        .band-howto {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(0,43,92,0.07) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(0,120,138,0.06) 0%, transparent 46%),
                #f5f7fa;
        }
        .band-scoring {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(176,125,43,0.10) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(0,43,92,0.04) 0%, transparent 46%),
                #fbf6e7;
        }
        .band-submit {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(152,0,46,0.07) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(0,43,92,0.05) 0%, transparent 46%),
                #f4eff1;
        }
        .band-tips {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(141,198,63,0.14) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(0,120,138,0.05) 0%, transparent 46%),
                #eef5e6;
        }
        .band-faq {
            background:
                radial-gradient(ellipse at 85% 6%, rgba(0,43,92,0.06) 0%, transparent 52%),
                radial-gradient(ellipse at 8% 94%, rgba(176,125,43,0.05) 0%, transparent 46%),
                #f2f4f8;
        }
"""

# section id (or class marker) -> band suffix, in page order
BANDS = [
    ("chapters", "chapters"),
    ("instructorTools", "tools"),
    ("howto", "howto"),
    ("scoring", "scoring"),
    ("submit", "submit"),
    ("tips", "tips"),
    ("faq", "faq"),
]


def main():
    src = open(PATH, encoding="utf-8").read()
    if "class=\"band " in src:
        print("  already banded; nothing to do")
        return 0

    lines = src.split("\n")

    # locate the single wrapping container and its close
    try:
        start = next(i for i, l in enumerate(lines)
                     if l.strip() == '<div class="container">')
        end = next(i for i, l in enumerate(lines)
                   if l.strip().startswith('</div><!-- end container -->'))
    except StopIteration:
        sys.exit("could not locate the wrapping container")

    body = lines[start + 1:end]

    # split the container body into its top-level children (8-space indent)
    chunks, cur, depth = [], [], 0
    for l in body:
        opens = len(re.findall(r'<(?!/)(?!br|img|hr|meta|input|link)[a-zA-Z]', l))
        closes = len(re.findall(r'</[a-zA-Z]', l))
        if depth == 0 and l.strip().startswith("<div") and cur:
            chunks.append(cur); cur = []
        cur.append(l)
        depth += opens - closes
        if depth <= 0 and l.strip().startswith("</div"):
            chunks.append(cur); cur = []; depth = 0
    if cur:
        chunks.append(cur)

    def chunk_key(ch):
        t = "\n".join(ch)
        if 'class="nav-tabs"' in t:
            return "nav"
        for sid, _ in BANDS:
            if f'id="{sid}"' in t:
                return sid
        return None

    buckets = {k: [] for k, _ in BANDS}
    nav, leftovers = [], []
    for ch in chunks:
        k = chunk_key(ch)
        if k == "nav":
            nav = ch
        elif k in buckets:
            buckets[k] = ch
        elif "".join(ch).strip():
            leftovers.append(ch)

    missing = [k for k, _ in BANDS if not buckets[k]]
    if missing:
        sys.exit(f"sections not found: {missing}")
    if leftovers:
        print(f"  note: {len(leftovers)} unclassified chunk(s) kept in the first band")

    out = []
    out.append("    <!-- ══════════ NAV TABS + BANDED SECTIONS ══════════")
    out.append("         Each section sits in its own full-width tinted band. The tabs")
    out.append("         live inside the chapters band so the strip and the chapter list")
    out.append("         read as one surface, with no pale gap under the hero. -->")
    for sid, suffix in BANDS:
        out.append(f'    <section class="band band-{suffix}">')
        out.append('      <div class="container">')
        if sid == "chapters":
            out.extend(nav)
            for ch in leftovers:
                out.extend(ch)
        out.extend(buckets[sid])
        out.append("      </div>")
        out.append("    </section>")
        out.append("")

    new = lines[:start] + out + lines[end + 1:]
    text = "\n".join(new)

    # bands supply the rhythm now; drop the per-section top margins
    text = re.sub(r'(<div id="(?:howto|scoring|submit|tips|faq)")\s+style="margin-top:3rem;"',
                  r"\1", text)

    # insert the band CSS after the .container rule
    m = re.search(r"(\n\s*\.container \{[^}]*\}\n)", text)
    if not m:
        sys.exit("could not find the .container rule to anchor CSS")
    text = text[:m.end(1)] + BAND_CSS + text[m.end(1):]

    open(PATH, "w", encoding="utf-8").write(text)
    print(f"  wrapped {len(BANDS)} sections into bands; tabs folded into chapters")
    return 0


if __name__ == "__main__":
    sys.exit(main())

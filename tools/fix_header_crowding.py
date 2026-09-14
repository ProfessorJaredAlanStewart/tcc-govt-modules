#!/usr/bin/env python3
"""Stop the Return to Chapter List pill crowding the chapter title.

Adding the pill put a third item into a header bar that was already nearly
full (title + score readout), so the title wrapped onto a second line and
collided with the pill. This reclaims the space the pill needs:

  * a real gap between the header's flex children, so nothing ever touches
  * a wider header-content cap, since there is room on large screens
  * a modest type/gap reduction below 1400px, where the bar is tightest

The existing <=700px mobile rules already shorten the title and compress the
score widget, and they use !important, so they still win on phones.
"""
import glob, re, sys

ANCHOR = "        .back-to-list[hidden] { display: none; }\n"

CSS = """
        /* Room for the chapter-list link: the header bar now holds three
           items, so give them a gap and reclaim width for the title. */
        .header-content { max-width: 1400px; }
        /* Explicit margins rather than flex `gap`: gap is unsupported in
           older engines, and this spacing must never collapse. */
        .back-to-list { margin-right: 1.5rem; }
        .score-display { margin-left: 1.5rem; }
        .header-title,
        .header h1 { min-width: 0; }
        @media (max-width: 1400px) {
            .header-title,
            .header h1 { font-size: 1.05em; }
            .score-display { gap: 12px; font-size: 1em; }
        }
        /* Between the phone rules (<=700px) and full width the bar is still
           too tight for the full institution name, so fall back to the same
           short brand mark used on mobile. The chapter title is in the hero
           immediately below, so nothing is lost. */
        @media (min-width: 701px) and (max-width: 1250px) {
            .header-title,
            .header h1 { font-size: 0; line-height: 0; }
            .header-title::after,
            .header h1::after {
                content: "Trailblazer Trek";
                display: inline;
                font-size: 16px;
                line-height: 1.2;
                font-weight: 700;
                color: #ffffff;
            }
            .score-display { gap: 10px; font-size: 0.95em; }
        }
"""


def patch(path):
    c = open(path, encoding="utf-8").read()
    if ".back-to-list[hidden]" not in c:
        return None, "link CSS not present"
    if "Room for the chapter-list link" in c:
        return [], None
    if ANCHOR not in c:
        return None, "anchor not found"
    c = c.replace(ANCHOR, ANCHOR + CSS, 1)
    open(path, "w", encoding="utf-8").write(c)
    return ["header-spacing"], None


def main():
    files = sorted(glob.glob("Chapter *(Expanded Edition).html"))
    files += sorted(glob.glob("Chapter *Trailblazer Trek*.html"))
    if not files:
        sys.exit("No chapter files found. Run from a repo root.")
    errs = 0
    for f in files:
        did, err = patch(f)
        if err:
            print(f"  ERROR {f.split(' - ')[0]}: {err}"); errs += 1
        else:
            print(f"  {f.split(' - ')[0]:12s} {did and did[0] or 'already current'}")
    print(f"\n{len(files)} chapters processed, {errs} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

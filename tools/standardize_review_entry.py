#!/usr/bin/env python3
"""Give every gold-standard chapter the SAME Chapter Review entry point.

Chapters 1 and 4 used a button below the grid; 2, 3 and 5 used a card inside the
section grid. Standardising on the button, for three reasons:

  1. It matches the Texas repo, which already pairs Generate Completion Report
     and Chapter Review & Resources as two buttons.
  2. The review is unscored. Inside the grid it inherits the points-badge slot,
     so it rendered a yellow "Study only, not scored" chip where every sibling
     card shows "185 points", reading like a quest that forgot its score.
  3. It keeps grid rows even. Six-section chapters would otherwise show 3+3+1.

Both buttons now use .trek-report-btn, the class the runtime standardisation
script gives the green report button, so the pair matches exactly in size and
shape. The review button is teal to mark it as the non-scored one.

Placement note: the runtime script inserts the green button immediately after
the section grid. A static button placed after the grid therefore lands below
it, which is the order seen in Chapter 1.

Idempotent.
"""
import glob, re, sys

BTN = ('        <div class="trek-review-btn-container" '
       'style="text-align:center; margin:-8px auto 28px auto; padding:0 16px;">\n'
       '            <button class="trek-report-btn" type="button" '
       'style="background:linear-gradient(135deg,#00697a,#00889c); border-color:#005967;" '
       'onclick="{CALL}">&#128214; Chapter Review &amp; Resources</button>\n'
       '        </div>\n')


def nav_call(c):
    m = re.search(r'onclick="([a-zA-Z]+)\(\'(page-)?review\'\)"', c)
    return f"{m.group(1)}('{(m.group(2) or '')}review')" if m else None


def patch(path):
    c = open(path, encoding="utf-8").read()
    if 'trek-review-btn-container' in c:
        return "already standardised"
    call = nav_call(c)
    if not call:
        return "no review entry found"

    # remove an existing card-style entry
    card = re.search(
        r'\n\s*<div class="section-card"[^>]*onclick="[a-zA-Z]+\(\'(?:page-)?review\'\)"[^>]*>.*?\n\s*</div>\n',
        c, re.S)
    removed = "card"
    if card:
        c = c[:card.start()] + "\n" + c[card.end():]
    else:
        # remove an existing button-style entry (Ch1 / Ch4 variants)
        btn = re.search(
            r'\n\s*<button[^>]*onclick="[a-zA-Z]+\(\'(?:page-)?review\'\)"[^>]*>.*?</button>', c, re.S)
        if not btn:
            return "entry found but not removable"
        c = c[:btn.start()] + c[btn.end():]
        removed = "button"

    # insert the standard button right after the section grid closes
    gm = re.search(r'<div class="(?:section-grid|sections-grid|section-cards)">', c)
    if not gm:
        return "no section grid"
    i, depth = gm.end(), 1
    for t in re.finditer(r'<div\b[^>]*>|</div>', c[gm.end():]):
        depth += -1 if t.group(0).startswith('</') else 1
        if depth == 0:
            i = gm.end() + t.end()
            break
    c = c[:i] + "\n\n" + BTN.replace("{CALL}", call) + c[i:]
    open(path, "w", encoding="utf-8").write(c)
    return f"standardised (was a {removed})"


def main():
    for f in sorted(glob.glob("Chapter *(Expanded Edition).html")):
        c = open(f, encoding="utf-8").read()
        if not re.search(r'id="(page-)?review"', c):
            continue
        print(f"  {f.split(' - ')[0]:12s} {patch(f)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

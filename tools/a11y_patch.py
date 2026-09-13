#!/usr/bin/env python3
"""Add keyboard operability + ARIA semantics to Trailblazer Trek chapters.

Progressive enhancement: injects one CSS block and one JS block before </body>.
Does not touch existing markup, scoring, or point logic, so the points audit is
unaffected. Idempotent - re-running replaces the existing block.
"""
import glob, re, sys, os

MARKER_START = "<!-- A11Y-ENHANCEMENT-START -->"
MARKER_END = "<!-- A11Y-ENHANCEMENT-END -->"

BLOCK = MARKER_START + """
<style>
/* Visible focus for keyboard users (WCAG 2.4.7). */
.interactive-card:focus-visible,
.kc-option:focus-visible,
.section-card:focus-visible,
.report-card:focus-visible,
[role="button"]:focus-visible,
button:focus-visible,
a:focus-visible,
textarea:focus-visible,
input:focus-visible {
    outline: 3px solid #0b5fff;
    outline-offset: 3px;
    border-radius: 4px;
}
/* Fallback for browsers without :focus-visible. */
.interactive-card:focus,
.kc-option:focus,
.section-card:focus,
.report-card:focus {
    outline: 3px solid #0b5fff;
    outline-offset: 3px;
}
.kc-option[aria-disabled="true"] { cursor: default; }
/* Screen-reader-only helper text. */
.sr-only {
    position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;
}
@media (prefers-reduced-motion: reduce) {
    * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
</style>
<script>
(function () {
    'use strict';
    function activateOnKey(el) {
        el.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                if (el.getAttribute('aria-disabled') === 'true') { return; }
                e.preventDefault();
                el.click();
            }
        });
    }
    function text(el) { return (el.textContent || '').replace(/\\s+/g, ' ').trim(); }
    // Reveal state lives on the card in some chapters and on .card-content in
    // others, so check both.
    function isRevealed(card) {
        if (card.classList.contains('revealed')) { return true; }
        var c = card.querySelector('.card-content');
        return !!(c && c.classList.contains('revealed'));
    }

    function enhance() {
        // 1. Reveal cards -> keyboard-operable disclosure buttons.
        document.querySelectorAll('.interactive-card').forEach(function (card) {
            if (card.dataset.a11y) { return; }
            card.dataset.a11y = '1';
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            var revealed = isRevealed(card);
            card.setAttribute('aria-expanded', revealed ? 'true' : 'false');
            var prompt = card.querySelector('.card-prompt');
            var content = card.querySelector('.card-content');
            if (prompt && content) {
                if (!prompt.id) { prompt.id = 'a11y-cp-' + Math.random().toString(36).slice(2, 9); }
                if (!content.id) { content.id = 'a11y-cc-' + Math.random().toString(36).slice(2, 9); }
                card.setAttribute('aria-labelledby', prompt.id);
                card.setAttribute('aria-controls', content.id);
            }
            activateOnKey(card);
            card.addEventListener('click', function () {
                if (isRevealed(card)) {
                    card.setAttribute('aria-expanded', 'true');
                }
            });
        });

        // 2. Knowledge checks -> labelled groups of keyboard-operable options.
        document.querySelectorAll('.knowledge-check').forEach(function (kc) {
            if (kc.dataset.a11y) { return; }
            kc.dataset.a11y = '1';
            var q = kc.querySelector('.kc-question');
            if (q) {
                if (!q.id) { q.id = 'a11y-q-' + Math.random().toString(36).slice(2, 9); }
                kc.setAttribute('role', 'group');
                kc.setAttribute('aria-labelledby', q.id);
            }
            var fb = kc.querySelector('.feedback-box');
            if (fb) {
                fb.setAttribute('role', 'status');
                fb.setAttribute('aria-live', 'polite');
            }
            var opts = kc.querySelectorAll('.kc-option');
            opts.forEach(function (opt) {
                opt.setAttribute('tabindex', '0');
                opt.setAttribute('role', 'button');
                activateOnKey(opt);
                opt.addEventListener('click', function () {
                    // Once answered, options are disabled for the mouse via
                    // pointer-events; mirror that for keyboard users.
                    opts.forEach(function (o) {
                        if (o.classList.contains('disabled')) {
                            o.setAttribute('aria-disabled', 'true');
                            o.setAttribute('tabindex', '-1');
                        }
                    });
                });
            });
        });

        // 3. Home-page navigation cards and report cards.
        document.querySelectorAll('.section-card, .report-card').forEach(function (card) {
            if (card.dataset.a11y) { return; }
            card.dataset.a11y = '1';
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            var h = card.querySelector('h3');
            if (h) {
                if (!h.id) { h.id = 'a11y-sc-' + Math.random().toString(36).slice(2, 9); }
                card.setAttribute('aria-labelledby', h.id);
            }
            activateOnKey(card);
        });

        // 4. Reflection textareas need an accessible name (placeholder is not one).
        document.querySelectorAll('textarea.reflection-input').forEach(function (ta) {
            if (ta.getAttribute('aria-label')) { return; }
            var box = ta.closest('.reflection-box');
            var p = box && box.querySelector('.reflection-prompt');
            ta.setAttribute('aria-label', p ? ('Reflection: ' + text(p)) : 'Written reflection');
            var counter = box && box.querySelector('.reflection-counter');
            if (counter) { counter.setAttribute('aria-live', 'polite'); }
            var fb = box && box.querySelector('.reflection-feedback');
            if (fb) { fb.setAttribute('role', 'status'); fb.setAttribute('aria-live', 'polite'); }
        });

        // 5. Progress bar semantics.
        var fill = document.getElementById('progressBar') || document.getElementById('progressFill');
        if (fill && !fill.dataset.a11y) {
            fill.dataset.a11y = '1';
            fill.setAttribute('role', 'progressbar');
            fill.setAttribute('aria-valuemin', '0');
            fill.setAttribute('aria-valuemax', '100');
            fill.setAttribute('aria-label', 'Chapter progress');
            var sync = function () {
                var v = parseInt((fill.textContent || '0').replace('%', ''), 10);
                if (!isNaN(v)) { fill.setAttribute('aria-valuenow', String(v)); }
            };
            sync();
            try { new MutationObserver(sync).observe(fill, { childList: true, characterData: true, subtree: true }); } catch (e) {}
        }

        // 6. Announce point totals and section-gate messages politely.
        var pts = document.getElementById('totalPoints') || document.getElementById('pointsDisplay');
        if (pts && !pts.getAttribute('aria-live')) {
            pts.setAttribute('role', 'status');
            pts.setAttribute('aria-live', 'polite');
        }
        document.querySelectorAll('.section-gate-msg').forEach(function (g) {
            g.setAttribute('role', 'status');
            g.setAttribute('aria-live', 'assertive');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', enhance);
    } else {
        enhance();
    }
    // Re-run after navigation so late-rendered content is covered too.
    document.addEventListener('click', function () { setTimeout(enhance, 60); });
})();
</script>
""" + MARKER_END + "\n"


def patch(path):
    c = open(path, encoding="utf-8").read()
    # idempotent: strip any previous block
    c = re.sub(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n?", "", c, flags=re.S)
    if "</body>" not in c:
        return False, "no </body>"
    c = c.replace("</body>", BLOCK + "</body>", 1)
    # language attribute for screen readers (WCAG 3.1.1)
    if not re.search(r"<html[^>]*\slang=", c):
        c = re.sub(r"<html(?![^>]*\slang=)", '<html lang="en"', c, count=1)
    open(path, "w", encoding="utf-8").write(c)
    return True, "ok"


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    targets = sorted(glob.glob(os.path.join(root, "Chapter *.html")))
    idx = os.path.join(root, "index.html")
    if os.path.exists(idx):
        targets.append(idx)
    n = 0
    for f in targets:
        ok, msg = patch(f)
        if ok:
            n += 1
        else:
            print("  SKIP", os.path.basename(f), msg)
    print(f"Patched {n}/{len(targets)} files in {root}")

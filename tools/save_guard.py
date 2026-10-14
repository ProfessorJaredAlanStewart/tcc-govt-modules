"""Insert the "progress can't save here" banner into every chapter.

Shows a banner when the chapter is:
  - inside a frame (Canvas page embed, LMS preview), where browsers restrict
    third-party storage and printing, or
  - in a top-level tab whose storage is blocked (private window, strict
    privacy settings).
Idempotent: skips files that already contain the marker.
Usage: python3 save_guard.py <repo_dir>
"""
import glob, os, sys

MARK = 'id="trek-save-guard"'
BLOCK = r'''<!-- Trek save guard: warn when progress cannot be saved here -->
<script id="trek-save-guard">
(function () {
    'use strict';
    var framed = false;
    try { framed = window.self !== window.top; } catch (e) { framed = true; }
    var storageOk = false;
    try {
        var k = '__trek_probe__';
        window.localStorage.setItem(k, '1');
        storageOk = window.localStorage.getItem(k) === '1';
        window.localStorage.removeItem(k);
    } catch (e) { storageOk = false; }
    if (!framed && storageOk) { return; }

    var bar = document.createElement('div');
    bar.setAttribute('role', 'alert');
    bar.style.cssText = 'background:#98002e;color:#fff;padding:14px 18px;font:600 16px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;text-align:center;position:relative;z-index:10000;';
    var msg = document.createElement('span');
    if (framed) {
        msg.textContent = 'Your progress may not save and your completion report may not download while this chapter is open inside another page. Open it in its own tab before you start.';
        var a = document.createElement('a');
        a.href = window.location.href;
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = 'Open this chapter in a new tab ↗';
        a.style.cssText = 'display:inline-block;margin:8px 0 0 12px;background:#fff;color:#002b5c;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:700;';
        bar.appendChild(msg);
        bar.appendChild(a);
    } else {
        msg.textContent = 'Your browser is blocking saved progress (often a private window or strict privacy setting). Anything you do here will be lost when you close this tab. Use a regular browser window, or finish the chapter in one sitting.';
        bar.appendChild(msg);
    }
    function place() { document.body.insertBefore(bar, document.body.firstChild); }
    if (document.body) { place(); } else { document.addEventListener('DOMContentLoaded', place); }
})();
</script>
'''

repo = sys.argv[1]
n = 0
for f in sorted(glob.glob(os.path.join(repo, 'Chapter*.html'))):
    s = open(f, encoding='utf-8').read()
    if MARK in s:
        continue
    i = s.rfind('</body>')
    assert i != -1, f
    s = s[:i] + BLOCK + s[i:]
    open(f, 'w', encoding='utf-8').write(s)
    n += 1
print(f'{n} chapters updated in {repo}')

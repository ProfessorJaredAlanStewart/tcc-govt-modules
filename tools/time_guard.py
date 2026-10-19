"""Make section timers honest and repair stale saves on resume.

1. Inserts a <script id="trek-time-guard"> block just before the shared
   "Resume & Integrity Extensions" block. It:
   - credits section time only while the tab is visible and the student has
     been active (mouse, keys, scroll, touch) within the last 10 minutes;
   - exposes window.__trekRepairState(), which clears the open-section clock
     carried in from a save and repairs sectionTimers / sectionPoints shapes
     (missing sections, NaN/null timers, outdated max values).
2. Calls __trekRepairState() inside restoreState(), right after the saved
   fields are copied back.

Idempotent. Usage: python3 time_guard.py <repo_dir>
"""
import glob, os, sys

MARK = 'id="trek-time-guard"'
ANCHOR_BLOCK = '<!-- TCC Trailblazer Trek — Resume & Integrity Extensions'
ANCHOR_RESTORE = "if (saved._elapsedAtSave && 'moduleStartTime' in gameState) {"
CALL = "if (window.__trekRepairState) { try { window.__trekRepairState(); } catch (e) {} }\n                "

BLOCK = r'''<!-- Trek time guard: pause section timers when idle or hidden; repair restored state -->
<script id="trek-time-guard">
(function () {
    'use strict';
    if (typeof gameState === 'undefined' || !gameState || !gameState.sectionTimers) { return; }
    var copy = function (o) { try { return JSON.parse(JSON.stringify(o)); } catch (e) { return null; } };
    var DEF_TIMERS = copy(gameState.sectionTimers) || {};
    var DEF_POINTS = gameState.sectionPoints ? copy(gameState.sectionPoints) : null;
    var IDLE_MS = 10 * 60 * 1000;
    var lastActive = Date.now();
    var hiddenAt = null;

    window.__trekRepairState = function () {
        var gs = gameState;
        // A save made mid-section carries an old entry timestamp; crediting it
        // would add all the time the student was away.
        gs.currentSection = null;
        gs.sectionEntryTime = null;
        if (!gs.sectionTimers || typeof gs.sectionTimers !== 'object') { gs.sectionTimers = {}; }
        Object.keys(DEF_TIMERS).forEach(function (k) {
            var v = gs.sectionTimers[k];
            if (typeof v !== 'number' || !isFinite(v) || v < 0) { gs.sectionTimers[k] = 0; }
        });
        if (DEF_POINTS && gs.sectionPoints && typeof gs.sectionPoints === 'object') {
            Object.keys(DEF_POINTS).forEach(function (k) {
                var d = DEF_POINTS[k], cur = gs.sectionPoints[k];
                if (!cur || typeof cur !== 'object') { gs.sectionPoints[k] = copy(d); }
                else if (d && typeof d === 'object' && 'max' in d) { cur.max = d.max; }
            });
        }
    };

    function tick() {
        var gs = gameState;
        if (!gs.currentSection || !gs.sectionEntryTime) { return; }
        var now = Date.now();
        var until = Math.min(now, lastActive + IDLE_MS);
        if (hiddenAt !== null) { until = Math.min(until, hiddenAt); }
        var add = until - gs.sectionEntryTime;
        if (add > 0) {
            var k = gs.currentSection;
            gs.sectionTimers[k] = (Number(gs.sectionTimers[k]) || 0) + add;
        }
        gs.sectionEntryTime = now;
    }

    ['mousemove', 'mousedown', 'keydown', 'scroll', 'wheel', 'touchstart'].forEach(function (ev) {
        window.addEventListener(ev, function () { lastActive = Date.now(); }, { passive: true, capture: true });
    });
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            hiddenAt = Date.now();
            tick();
        } else {
            hiddenAt = null;
            lastActive = Date.now();
            if (gameState.currentSection && gameState.sectionEntryTime) { gameState.sectionEntryTime = Date.now(); }
        }
    });
    setInterval(tick, 15000);
})();
</script>
'''

repo = sys.argv[1]
n = 0
for f in sorted(glob.glob(os.path.join(repo, 'Chapter*.html'))):
    s = open(f, encoding='utf-8').read()
    if MARK in s:
        continue
    assert s.count(ANCHOR_BLOCK) == 1, f
    assert s.count(ANCHOR_RESTORE) == 1, f
    i = s.index(ANCHOR_BLOCK)
    s = s[:i] + BLOCK + s[i:]
    s = s.replace(ANCHOR_RESTORE, CALL + ANCHOR_RESTORE)
    open(f, 'w', encoding='utf-8').write(s)
    n += 1
print(f'{n} chapters updated in {repo}')

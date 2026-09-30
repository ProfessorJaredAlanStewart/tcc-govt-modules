// Regression test: completed-section check marks must survive a resume.
//
// Bug (Sept 2026): the shared Resume block re-marked home tiles only by
// id="card<N>" / id="section<N>-card", using the raw stored value as <N>.
// Chapters that store 'section1', store booleans, or have tiles without
// those ids lost every green check after "Welcome back" -> OK. Students
// saw sections they had finished shown as incomplete.
//
// For each chapter: complete sections 1 and 2 through the real UI, save,
// reload into a fresh DOM with the saved state, accept the resume prompt,
// and confirm the same tiles are still marked completed.
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const files = fs.readdirSync('.').filter(f => /^Chapter .*\(Expanded Edition\)\.html$/.test(f))
  .sort((a, b) => parseInt(a.split(' ')[1]) - parseInt(b.split(' ')[1]));
const REFL = 'I think government exists because people living together need some shared way to settle disputes and provide things no single person can build alone, like roads, courts, and defense. Locke argued that people consent to government to protect their rights, and that idea still shapes how Americans judge whether leaders are legitimate. In my own community I see this when the city fixes streets or runs elections that let neighbors choose who represents them locally.';
const wait = ms => new Promise(r => setTimeout(r, ms));
const quiet = () => { const vc = new VirtualConsole(); vc.on('jsdomError', () => {}); return vc; };
let pass = 0, fail = 0;
const check = (c, ok, m) => { if (ok) pass++; else { fail++; console.log(`    FAIL [${c}] ${m}`); } };

function markedTiles(d) {
  return [...d.querySelectorAll('.completed')]
    .filter(e => !e.closest('[id*="report" i]'))
    .map(e => (e.id || e.className.replace(/\s+/g, '.')) + '[' + (e.getAttribute('onclick') || '') + ']')
    .sort();
}

function completeSection(w, d, n) {
  const ta = d.getElementById('reflectionInput' + n);
  if (!ta) return false;
  const pg = ta.closest('.page, .section-page, [id^="page-"], [id^="section"]') || d.body;
  const navRe = new RegExp("(showPage|navigateToSection|goToSection|navigateTo)\\(\\s*'?(section-?)?" + n + "'?\\s*\\)");
  const nav = [...d.querySelectorAll('[onclick]')].find(e => navRe.test(e.getAttribute('onclick')));
  if (nav) nav.click();
  pg.querySelectorAll('[onclick*="revealCard"]').forEach(el => el.click());
  pg.querySelectorAll('[onclick*="handleAnswer"]').forEach(el => { if (/\btrue\b/.test(el.getAttribute('onclick'))) el.click(); });
  ta.value = REFL;
  ta.dispatchEvent(new w.Event('input'));
  w.eval('submitReflection(' + n + ')');
  const btn = pg.querySelector('[onclick*="completeSection"]');
  if (btn) btn.click();
  return true;
}

(async () => {
  for (const f of files) {
    const html = fs.readFileSync(f, 'utf8');
    const opts = { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.org/x/', virtualConsole: quiet() };

    // Session 1: complete sections 1 and 2, then save.
    const dom1 = new JSDOM(html, { ...opts, beforeParse(w) { w.confirm = () => true; w.alert = () => {}; w.scrollTo = () => {}; } });
    await wait(80);
    const w1 = dom1.window, d1 = w1.document;
    for (const n of [1, 2]) { completeSection(w1, d1, n); await wait(1100); }
    const before = markedTiles(d1);
    w1.dispatchEvent(new w1.Event('pagehide'));
    const saved = {};
    for (let i = 0; i < w1.localStorage.length; i++) {
      const k = w1.localStorage.key(i);
      if (k.startsWith('tcc-trek-resume::')) saved[k] = w1.localStorage.getItem(k);
    }
    dom1.window.close();
    check(f, before.length >= 2, 'setup: expected 2 tiles marked in session, got ' + before.length);
    check(f, Object.keys(saved).length === 1, 'setup: resume state was not saved');

    // Session 2: fresh page with the saved state, accept "Welcome back".
    const dom2 = new JSDOM(html, { ...opts, beforeParse(w) {
      w.confirm = () => true; w.alert = () => {}; w.scrollTo = () => {};
      Object.keys(saved).forEach(k => w.localStorage.setItem(k, saved[k]));
    } });
    await wait(80);
    const after = markedTiles(dom2.window.document);
    const lost = before.filter(m => !after.includes(m));
    const extra = after.filter(m => !before.includes(m));
    check(f, lost.length === 0, 'check marks lost after resume: ' + lost.join(' | '));
    check(f, extra.length === 0, 'unexpected tiles marked after resume: ' + extra.join(' | '));
    dom2.window.close();
  }
  console.log(`\n  ${pass} checks passed, ${fail} failed across ${files.length} chapters`);
  process.exit(fail ? 1 : 0);
})();

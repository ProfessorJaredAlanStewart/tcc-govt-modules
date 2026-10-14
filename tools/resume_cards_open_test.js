// Regression test: explore cards a student already opened must still open
// after "Welcome back" -> OK.
//
// Bug (Oct 2026): the shared Resume block added .revealed to the card but
// never to .card-content, and most chapters only display content via
// .card-content.show / .visible. revealCard() then returned early because
// the id was already in the saved set, so the card could never open again.
// Chapters 4, 11, 12, 13 were worse: they record reveals in earnedPoints,
// which the Resume block did not read at all.
//
// For each chapter: open the first explore card, save, reload into a fresh
// DOM with the saved state, accept resume, click the card, and confirm its
// content is displayed.
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const files = fs.readdirSync('.').filter(f => /^Chapter .*\(Expanded Edition\)\.html$/.test(f))
  .sort((a, b) => parseInt(a.split(' ')[1]) - parseInt(b.split(' ')[1]));
const wait = ms => new Promise(r => setTimeout(r, ms));
const quiet = () => { const vc = new VirtualConsole(); vc.on('jsdomError', () => {}); return vc; };
let pass = 0, fail = 0;
const check = (c, ok, m) => { if (ok) pass++; else { fail++; console.log(`    FAIL [${c}] ${m}`); } };
const shown = (w, card) => w.getComputedStyle(card.querySelector('.card-content')).display !== 'none';

(async () => {
  for (const f of files) {
    const html = fs.readFileSync(f, 'utf8');
    const opts = { runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.org/x/', virtualConsole: quiet() };
    const stub = w => { w.confirm = () => true; w.alert = () => {}; w.scrollTo = () => {}; };

    const dom1 = new JSDOM(html, { ...opts, beforeParse: stub });
    await wait(80);
    const w1 = dom1.window, c1 = w1.document.querySelector('.interactive-card');
    c1.click();
    await wait(1100);
    check(f, shown(w1, c1), 'setup: card did not open on first click');
    w1.dispatchEvent(new w1.Event('pagehide'));
    const saved = {};
    for (let i = 0; i < w1.localStorage.length; i++) {
      const k = w1.localStorage.key(i);
      if (k.startsWith('tcc-trek-resume::')) saved[k] = w1.localStorage.getItem(k);
    }
    dom1.window.close();
    check(f, Object.keys(saved).length === 1, 'setup: resume state was not saved');

    const dom2 = new JSDOM(html, { ...opts, beforeParse(w) {
      stub(w);
      Object.keys(saved).forEach(k => w.localStorage.setItem(k, saved[k]));
    } });
    await wait(80);
    const w2 = dom2.window, c2 = w2.document.querySelector('.interactive-card');
    c2.click();
    check(f, shown(w2, c2), 'card content hidden after resume');
    check(f, c2.getAttribute('aria-expanded') === 'true', 'aria-expanded not true after resume');
    dom2.window.close();
  }
  console.log(`\n  ${pass} checks passed, ${fail} failed across ${files.length} chapters`);
  process.exit(fail ? 1 : 0);
})();

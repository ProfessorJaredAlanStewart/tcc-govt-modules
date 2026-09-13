const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const nop = () => {};
const file = '/home/claude/tx-fresh/Chapter 16 - Civil Liberties and Civil Rights (Trailblazer Trek).html';
const html = fs.readFileSync(file, 'utf8');
const vc = new VirtualConsole();
vc.on('jsdomError', nop);
const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'https://example.org/',
  virtualConsole: vc,
  beforeParse(w) { w.alert = nop; w.scrollTo = nop; w.confirm = () => true; }
});
const { window } = dom;
window.addEventListener('load', () => {
  const d = window.document;
  const readPts = () => parseInt((d.getElementById('totalPoints').textContent || '0').replace(/[^0-9]/g, ''), 10) || 0;
  setTimeout(() => {
    const r = [];
    window.navigateToSection(1);
    const sec = d.getElementById('section1');

    const card = sec.querySelector('.interactive-card');
    r.push(['reveal card: tabindex=0', card.getAttribute('tabindex') === '0']);
    r.push(['reveal card: role=button', card.getAttribute('role') === 'button']);
    r.push(['reveal card: aria-expanded=false initially', card.getAttribute('aria-expanded') === 'false']);
    r.push(['reveal card: has accessible name', !!card.getAttribute('aria-labelledby')]);
    const p0 = readPts();
    card.dispatchEvent(new window.KeyboardEvent('keydown', { key: 'Enter', bubbles: true, cancelable: true }));
    r.push(['ENTER reveals card', card.classList.contains('revealed')]);
    r.push(['ENTER awards 15 pts', readPts() === p0 + 15]);
    r.push(['aria-expanded flips to true', card.getAttribute('aria-expanded') === 'true']);

    const kc = sec.querySelector('.knowledge-check');
    r.push(['quiz: role=group', kc.getAttribute('role') === 'group']);
    r.push(['quiz: labelled by question', !!kc.getAttribute('aria-labelledby')]);
    const opts = [...kc.querySelectorAll('.kc-option')];
    r.push(['quiz: options in tab order', opts.every(o => o.getAttribute('tabindex') === '0')]);
    r.push(['quiz: feedback aria-live', kc.querySelector('.feedback-box').getAttribute('aria-live') === 'polite']);
    const correct = opts.find(o => /handleAnswer\(this, true/.test(o.getAttribute('onclick')));
    const p1 = readPts();
    correct.dispatchEvent(new window.KeyboardEvent('keydown', { key: ' ', bubbles: true, cancelable: true }));
    r.push(['SPACE answers question', correct.classList.contains('correct')]);
    r.push(['SPACE awards 50 pts', readPts() === p1 + 50]);
    r.push(['answered opts aria-disabled', opts.every(o => o.getAttribute('aria-disabled') === 'true')]);
    r.push(['answered opts out of tab order', opts.every(o => o.getAttribute('tabindex') === '-1')]);

    const sc = d.querySelector('.section-card');
    r.push(['home card keyboard reachable', sc.getAttribute('tabindex') === '0' && sc.getAttribute('role') === 'button']);
    const ta = d.querySelector('textarea.reflection-input');
    r.push(['reflection textarea named', (ta.getAttribute('aria-label') || '').length > 10]);
    const pb = d.getElementById('progressBar');
    r.push(['progress bar role=progressbar', !!pb && pb.getAttribute('role') === 'progressbar']);
    r.push(['html lang=en', d.documentElement.getAttribute('lang') === 'en']);

    let pass = 0;
    r.forEach(([n, ok]) => { if (ok) pass++; console.log((ok ? '  PASS  ' : '  FAIL  ') + n); });
    console.log(`\n${pass}/${r.length} checks passed`);
    process.exit(pass === r.length ? 0 : 1);
  }, 400);
});

const fs=require('fs');
const {JSDOM}=require('jsdom');
const F="Chapter 8 - The Media (Expanded Edition).html";
const html=fs.readFileSync(F,'utf8');
let pass=0,fail=0;
const ck=(ok,m)=>{ if(ok) pass++; else {fail++; console.log('  FAIL:',m);} };
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/x/'});
const w=dom.window, d=w.document;
setTimeout(()=>{
  // review page exists and is hidden initially
  const rev=d.getElementById('review');
  ck(!!rev,'review page missing');
  ck(rev && !rev.classList.contains('active'),'review page active on load');
  ck(d.getElementById('homePage').classList.contains('active'),'home not active on load');

  // the button exists and opens it
  const entries=[...d.querySelectorAll('[onclick]')].filter(e=>/navigateToSection\('review'\)/.test(e.getAttribute('onclick')||''));
  ck(entries.length===1,'expected exactly one review entry point, got '+entries.length);
  ck(entries.length===1 && /Chapter Review/.test(entries[0].textContent),'review entry is not labelled');

  w.navigateToSection('review');
  ck(rev.classList.contains('active'),'showPage(review) did not activate the page');
  ck(!d.getElementById('homePage').classList.contains('active'),'home still active after navigating');

  // navigating to review must NOT start a section timer or award points
  ck(w.eval('gameState.currentSection')===null,'review page started a section timer');
  ck(w.eval('gameState.score')===0,'review page changed the score (gameState.score)');

  // back to menu works
  w.navigateToSection('homePage');
  ck(d.getElementById('homePage').classList.contains('active'),'back to home failed');
  ck(!rev.classList.contains('active'),'review still active after going home');

  // section pages still work
  w.eval("gameState.studentName='Test'");
  w.navigateToSection('section3');
  ck(d.getElementById('section3').classList.contains('active'),'section3 broke');
  ck(w.eval('gameState.currentSection')==='3','section timer did not start');

  // content checks
  const t=rev.textContent;
  ck((t.match(/Answer:/g)||[]).length>=9,'expected 9+ review answers');
  ck(d.querySelectorAll('#review details').length>=9,'review questions not collapsible');
  ck(d.querySelectorAll('#review dt').length>=20,'expected 20+ key terms');
  ck(d.querySelectorAll('#review details').length>=10,'expected 10 review questions');
  ck(/not scored/.test(t),'missing the unscored notice');

  // objectives on every section
  for(let i=1;i<=4;i++){
    const p=d.getElementById('section'+i);
    ck(p && /Learning Objectives/.test(p.textContent),'section '+i+' missing objectives');
  }
  // external links safe
  const bad=[...d.querySelectorAll('#review a[target="_blank"]')].filter(a=>!/noopener/.test(a.rel||''));
  ck(bad.length===0,bad.length+' external links missing rel=noopener');

  console.log(`\n  ${pass} checks passed, ${fail} failed`);
  process.exit(fail?1:0);
  w.close();
},400);

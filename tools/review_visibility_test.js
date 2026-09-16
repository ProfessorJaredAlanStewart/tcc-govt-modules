// Verifies the Chapter Review entry survives the runtime button-standardisation
// script, which hides every home-page element whose onclick mentions "report".

// Returns the nearest ancestor with display:none, or null.
function hiddenBy(el){
  let n=el;
  while(n && n.style){ if(n.style.display==='none') return n.className||n.id||'(unnamed)'; n=n.parentElement; }
  return null;
}
const fs=require('fs'); const {JSDOM}=require('jsdom');
const files=fs.readdirSync('.').filter(f=>/^Chapter .*\(Expanded Edition\)\.html$/.test(f)).sort();
let pass=0,fail=0;
const ck=(ok,m)=>{ if(ok) pass++; else {fail++; console.log('  FAIL:',m);} };
(async()=>{
for(const f of files){
  const html=fs.readFileSync(f,'utf8');
  if(!/id="(page-)?review"/.test(html)) continue;   // not yet gold-standarded
  const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/'});
  const w=dom.window,d=w.document;
  await new Promise(r=>setTimeout(r,500));
  const entry=[...d.querySelectorAll('[onclick]')]
    .find(e=>/\('(page-)?review'\)|showChapterReview\(\)/.test(e.getAttribute('onclick')||''));
  const name=f.split(' - ')[0];
  ck(!!entry, name+': no review entry found');
  if(entry){
    // walk ancestors for display:none
    // The right invariant is not "always visible" but "as visible as the
    // section cards". Some chapters gate all home content behind a start
    // button, and the review entry should be gated exactly the same way.
    const sectionCard=[...d.querySelectorAll('[onclick]')]
      .find(x=>/(navigateToSection|showPage|goToSection)\(\s*'?(page-)?section1'?\s*\)|navigateToSection\(\s*1\s*\)/.test(x.getAttribute('onclick')||''));
    const entryHidden=hiddenBy(entry);
    const cardHidden=sectionCard?hiddenBy(sectionCard):null;
    ck(entryHidden===cardHidden,
       name+': review entry visibility ['+entryHidden+'] differs from section cards ['+cardHidden+']');
    // must not be nested inside another section-card
    const p=entry.parentElement;
    ck(!(p && /section-card/.test(p.className||'')), name+': review card nested inside another card');
  }
  w.close();
}
console.log(`\n  ${pass} checks passed, ${fail} failed`);
process.exit(fail?1:0);
})();

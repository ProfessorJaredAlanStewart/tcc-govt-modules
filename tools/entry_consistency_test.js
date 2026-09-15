// Asserts every gold-standard chapter exposes the Chapter Review entry the SAME way:
// a .trek-report-btn button, below the section grid, visible after the runtime
// standardisation script runs.
const fs=require('fs'); const {JSDOM}=require('jsdom');
const files=fs.readdirSync('.').filter(f=>/^Chapter .*\(Expanded Edition\)\.html$/.test(f)).sort();
let pass=0,fail=0;
const ck=(ok,m)=>{ if(ok) pass++; else {fail++; console.log('  FAIL:',m);} };
(async()=>{
for(const f of files){
  const html=fs.readFileSync(f,'utf8');
  if(!/id="(page-)?review"/.test(html)) continue;
  const name=f.split(' - ')[0];
  const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/'});
  const w=dom.window,d=w.document;
  await new Promise(r=>setTimeout(r,500));
  const e=[...d.querySelectorAll('[onclick]')]
    .find(x=>/\('(page-)?review'\)|showChapterReview\(\)/.test(x.getAttribute('onclick')||''));
  ck(!!e, name+': no review entry');
  if(e){
    ck(e.tagName==='BUTTON', name+': entry is '+e.tagName+', expected BUTTON');
    ck(/trek-report-btn/.test(e.className), name+': not using the shared button class');
    ck(!e.closest('.section-grid, .sections-grid, .section-cards'), name+': entry still inside the scored grid');
    const green=[...d.querySelectorAll('.trek-report-btn')].find(b=>/Completion Report/.test(b.textContent));
    ck(!!green, name+': green report button missing');
    if(green){
      const pos=green.compareDocumentPosition(e);
      ck(!!(pos & w.Node.DOCUMENT_POSITION_FOLLOWING), name+': review button is not below the report button');
    }
    let el=e,hidden=null;
    while(el&&el.style){ if(el.style.display==='none'){hidden=el.className||el.id;break;} el=el.parentElement; }
    ck(hidden===null, name+': hidden by ancestor ['+hidden+']');
  }
  w.close();
}
console.log(`\n  ${pass} checks passed, ${fail} failed`);
process.exit(fail?1:0);
})();

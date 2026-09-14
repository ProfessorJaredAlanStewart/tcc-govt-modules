// Verifies the Chapter Review entry survives the runtime button-standardisation
// script, which hides every home-page element whose onclick mentions "report".
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
    .find(e=>/\('(page-)?review'\)/.test(e.getAttribute('onclick')||''));
  const name=f.split(' - ')[0];
  ck(!!entry, name+': no review entry found');
  if(entry){
    // walk ancestors for display:none
    let el=entry, hidden=null;
    while(el && el.style){
      if(el.style.display==='none'){ hidden=el.className||el.id; break; }
      el=el.parentElement;
    }
    ck(hidden===null, name+': review entry hidden by ancestor ['+hidden+']');
    // must not be nested inside another section-card
    const p=entry.parentElement;
    ck(!(p && /section-card/.test(p.className||'')), name+': review card nested inside another card');
  }
  w.close();
}
console.log(`\n  ${pass} checks passed, ${fail} failed`);
process.exit(fail?1:0);
})();

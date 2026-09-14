const fs=require('fs'), path=require('path');
const {JSDOM}=require('jsdom');
const files=fs.readdirSync(".").filter(f=>/^Chapter .*\(Expanded Edition\)\.html$/.test(f)).sort();
let pass=0, fail=0;
const check=(c,ok,m)=>{ if(ok){pass++;} else {fail++; console.log(`    FAIL [${c}] ${m}`);} };

(async()=>{
for (const f of files){
  const html=fs.readFileSync(f,'utf8');

  // --- CASE A: index.html present (live site) -> link must become visible
  let dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/x/',
    beforeParse(w){ w.fetch=(u,o)=>Promise.resolve({ok:u==='index.html'&&o&&o.method==='HEAD'}); }});
  await new Promise(r=>setTimeout(r,60));
  let d=dom.window.document, a=d.getElementById('backToList');
  check(f,!!a,'link element missing');
  if(a){
    check(f,a.tagName==='A','not an anchor (keyboard focusable natively)');
    check(f,a.getAttribute('href')==='index.html','href wrong: '+a.getAttribute('href'));
    check(f,a.hidden===false,'link hidden even though index.html resolved');
    check(f,a.closest('.header')!==null,'link not inside the fixed header');
    check(f,/All Chapters/.test(a.textContent),'label missing');
  }
  dom.window.close();

  // --- CASE B: no index.html (Canvas import) -> link must stay hidden
  let dom2=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/x/',
    beforeParse(w){ w.fetch=()=>Promise.resolve({ok:false}); }});
  await new Promise(r=>setTimeout(r,60));
  let a2=dom2.window.document.getElementById('backToList');
  check(f,a2 && a2.hidden===true,'dead link shown when index.html is absent');
  dom2.window.close();

  // --- CASE C: fetch throws -> must not error, link STAYS VISIBLE (fail toward working nav)
  let dom3=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/x/',
    beforeParse(w){ w.fetch=()=>{throw new Error('blocked');}; }});
  await new Promise(r=>setTimeout(r,60));
  let a3=dom3.window.document.getElementById('backToList');
  check(f,a3 && a3.hidden===false,'link removed on the live site when fetch threw (should stay visible)');
  dom3.window.close();

  // --- hero colour
  check(f, html.includes('linear-gradient(135deg, #002b5c, #00406e)'),'hero not navy');
  check(f, !html.includes('linear-gradient(135deg, #00788a, #1a8fa0)'),'teal hero still present');
}
console.log(`\n  ${pass} checks passed, ${fail} failed across ${files.length} chapters`);
process.exit(fail?1:0);
})();

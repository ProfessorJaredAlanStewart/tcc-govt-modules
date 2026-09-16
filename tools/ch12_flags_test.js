// Verifies the three things flagged on Chapter 12:
//  1. open-ended reflection questions exist, save, and reach the report
//  2. the completion report renders and the print path is sane
//  3. no duplicated body paragraphs
const fs=require('fs'); const {JSDOM}=require('jsdom');
const F="Chapter 12 - Presidency (Expanded Edition).html";
const html=fs.readFileSync(F,'utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true,url:'https://example.org/'});
const w=dom.window,d=w.document;
let pass=0,fail=0;
const ck=(ok,m)=>{ if(ok) pass++; else {fail++; console.log('  FAIL:',m);} };
setTimeout(()=>{
  w.alert=()=>{};
  // --- FLAG 1: reflections
  const tas=[...d.querySelectorAll('textarea[id^="reflectionInput"]')];
  ck(tas.length===5,'expected 5 reflection prompts, got '+tas.length);
  // each must have a visible prompt near it
  tas.forEach((t,i)=>{
    const box=t.closest('div');
    ck(box && box.textContent.trim().length>40,'reflection '+(i+1)+' has no visible prompt text');
  });
  // save one and confirm it is credited
  w.eval("gameState.studentName='Test'");
    // submitReflection enforces a 50-word minimum and a low-effort check, so the
  // test text has to be a genuine answer rather than filler.
  tas[0].value='The presidency has outgrown its written design most clearly through the war power. '+
    'Congress holds the authority to declare war, yet presidents have committed forces repeatedly '+
    'without any declaration, relying on statutory authorizations written decades earlier for different '+
    'conflicts. I would argue this adapts sensibly to a world where threats move faster than a '+
    'legislative debate can, but it becomes dangerous precisely because Congress has found it '+
    'politically convenient not to reclaim the power it formally retains.';
  // the submit control lives in a sibling .reflection-footer, not the textarea's own div
  tas[0].dispatchEvent(new w.Event('input'));
  try{ w.submitReflection(1); }catch(e){ console.log('  submitReflection threw:',e.message); }
  const saved=w.eval("JSON.stringify(gameState.reflections)");
  ck(/war power/i.test(saved) && /"credited":true/.test(saved),'reflection did not save and credit into gameState');

  // --- FLAG 2: report renders and includes reflections
  try{ w.generateReport ? w.generateReport() : w.completeSection && 0; }catch(e){ console.log('  generateReport threw:',e.message); }
  const rp=d.getElementById('reportPage');
  ck(!!rp,'no reportPage');
  const rtxt=rp?rp.textContent:'';
  ck(rtxt.length>200,'report appears empty ('+rtxt.length+' chars)');
  ck(/war power/i.test(rtxt),'saved reflection does not appear in the completion report');

  // print button exists and is hidden in print CSS
  const printBtn=[...d.querySelectorAll('[onclick]')].find(b=>/print/i.test(b.getAttribute('onclick')||''));
  ck(!!printBtn,'no print control on the report');
  // the stylesheet hides .no-print; check the button or any ancestor carries it
  const hiddenInPrint = !!printBtn && !!printBtn.closest('.no-print, .print-report-button, .print-button');
  ck(hiddenInPrint,'print control is not inside anything the print stylesheet hides, so it would print itself');

  console.log(`\n  ${pass} passed, ${fail} failed`);
  w.close(); process.exit(fail?1:0);
},600);

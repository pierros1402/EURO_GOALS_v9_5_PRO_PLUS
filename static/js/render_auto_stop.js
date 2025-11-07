// =====================================================
// AUTO-STOP Render after idle period
// =====================================================
let lastAction = Date.now();
const idleLimit = 5 * 60 * 1000; // 5 min

["mousemove","keydown","scroll","touchstart"].forEach(ev=>{
  window.addEventListener(ev,()=>lastAction=Date.now());
});

setInterval(()=>{
  if(Date.now()-lastAction>idleLimit){
    console.log("💤 No activity > 5 min → requesting shutdown");
    fetch("/shutdown",{method:"POST"}).catch(()=>{});
  }
},60000);

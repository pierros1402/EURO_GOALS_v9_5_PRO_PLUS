(function(){
  const $=s=>document.querySelector(s);
  const led={render:$("#led-render"),db:$("#led-db"),flash:$("#led-flashscore"),sofa:$("#led-sofascore"),asian:$("#led-asianconnect"),net:$("#led-network")};
  const info={cpu:$("#summaryCPU"),ram:$("#summaryRAM"),disk:$("#summaryDISK"),last:$("#summaryLast"),next:$("#summaryNext")};
  const kv={ver:$("#kvVersion"),upt:$("#kvUptime"),auto:$("#kvAuto")};
  const REFBASE=window.__EG__?.initialRefreshSecs||15;
  let REFSECS=REFBASE,timer=null,counter=0;

  function setLED(el,st){el.classList.remove("ok","warn","bad");el.classList.add(st);}
  function formatUptime(sec){const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60);return `${h}h ${m}m`;}

  async function api(p){const r=await fetch(p,{cache:"no-store"});return await r.json();}

  async function refresh(){
    try{
      const s=await api("/api/status");
      kv.ver.textContent=s.version;
      kv.upt.textContent=formatUptime(s.uptime_sec);
      kv.auto.textContent=s.state.auto_refresh_on?`ON (${s.state.refresh_secs}s)`:"OFF";
      info.cpu.textContent=`CPU: ${s.cpu}%`;
      info.ram.textContent=`RAM: ${s.ram}%`;
      info.disk.textContent=`Disk: ${s.disk}%`;
      info.last.textContent=`Last: ${s.last_refresh}`;
      counter=REFSECS;
      setLED(led.render,"ok");setLED(led.db,"ok");setLED(led.flash,"ok");setLED(led.sofa,"ok");setLED(led.asian,"ok");
      setLED(led.net,navigator.onLine?"ok":"bad");
    }catch(e){
      console.error("refresh fail",e);
      Object.values(led).forEach(l=>setLED(l,"warn"));
    }
  }

  function tick(){
    if(counter>0){counter--;info.next.textContent=`Next: ${counter}s`;}
    else{refresh();}
  }

  window.addEventListener("online",()=>setLED(led.net,"ok"));
  window.addEventListener("offline",()=>setLED(led.net,"bad"));

  console.log("%cEURO_GOALS v9.5.0 PRO+ UI Loaded ✅","color:#5aa9ff;font-weight:bold;");

  refresh();setInterval(tick,1000);
})();
<script src="/static/js/ui_alerts.js"></script>

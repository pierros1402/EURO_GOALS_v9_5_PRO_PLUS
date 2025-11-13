/* ============================================================
   EURO_GOALS v9.9.16 — Mobile Pulse Edition (Scheduler + Pulse)
   - Unified scheduler (status 10s, GM 15s, SM 10s)
   - Live pulse σε panels όταν έρχεται νέο payload
   - Manual refresh κουμπί
   - Auto-scroll helpers (mobile)
   ============================================================ */

(function () {
  const $ = (sel) => document.querySelector(sel);

  // Panels to pulse on data updates
  const panels = {
    system:  $("#panel-summary"),
    status:  $("#panel-status"),
    goal:    $("#panel-goalmatrix"),
    smart:   $("#panel-smartmoney")
  };

  function pulse(el){
    if(!el) return;
    el.classList.remove("live-pulse");
    // force reflow
    void el.offsetWidth;
    el.classList.add("live-pulse");
  }

  // state (for change detection)
  let lastStatusSig = "";
  let lastGMHash = "";
  let lastSMHash = "";

  // Simple hash of JSON
  const jhash = (obj) => {
    try { return JSON.stringify(obj).length + "|" + Object.keys(obj || {}).join(","); }
    catch { return String(Math.random()); }
  };

  // Unified system status (every 10s)
  async function refreshSystemStatus(manual=false){
    try{
      const res = await fetch("/api/system/status");
      const data = await res.json();

      // summary bar updates
      const djOK = !String(data.engines.dowjones).includes("error");
      const smOK = !String(data.engines.smartmoney).includes("error");
      const gmOK = !String(data.engines.goalmatrix).includes("error");

      $("#djStat").textContent = djOK ? "🧠" : "❌";
      $("#smStat").textContent = smOK ? "💰" : "❌";
      $("#gmStat").textContent = gmOK ? "🎯" : "❌";

      $("#djStat").style.color = djOK ? "var(--ok)" : "var(--err)";
      $("#smStat").style.color = smOK ? "var(--ok)" : "var(--err)";
      $("#gmStat").style.color = gmOK ? "var(--ok)" : "var(--err)";
      $("#lastUpdate").textContent = new Date(data.timestamp).toLocaleTimeString();

      // change detect → pulse system & status panels
      const sig = `${djOK}-${smOK}-${gmOK}-${data.alerts?.smartmoney||0}-${data.alerts?.goalmatrix||0}`;
      if(sig !== lastStatusSig){
        lastStatusSig = sig;
        pulse(panels.system);
        pulse(panels.status);
      }
    }catch(e){
      console.warn("[EG] system status refresh failed:", e);
    }
  }

  // GoalMatrix (detail) every 15s
  async function refreshGoalMatrix(){
    try{
      const res = await fetch("/api/goal_matrix/summary");
      const data = await res.json();
      const h = jhash(data||{});
      if (h !== lastGMHash){
        lastGMHash = h;
        pulse(panels.goal);
      }
    }catch(e){
      console.warn("[EG] goal matrix refresh failed:", e);
    }
  }

  // SmartMoney (detail) every 10s
  async function refreshSmartMoney(){
    try{
      const res = await fetch("/api/smartmoney/summary");
      const data = await res.json();
      const h = jhash(data||{});
      if (h !== lastSMHash){
        lastSMHash = h;
        pulse(panels.smart);
      }
    }catch(e){
      console.warn("[EG] smartmoney refresh failed:", e);
    }
  }

  // Schedulers
  setInterval(refreshSystemStatus, 10000);
  setInterval(refreshGoalMatrix,   15000);
  setInterval(refreshSmartMoney,   10000);

  // First run
  refreshSystemStatus();
  refreshGoalMatrix();
  refreshSmartMoney();

  // Manual refresh button (already present on page)
  const refreshBtn = $("#refreshNow");
  refreshBtn?.addEventListener("click", async () => {
    await Promise.all([refreshSystemStatus(true), refreshGoalMatrix(), refreshSmartMoney()]);
    // μικρό οπτικό feedback στο summary bar
    pulse($("#system-summary"));
  });

  // Auto-scroll helpers for mobile (tap στα summary icons → scroll στο panel)
  $("#djStat")?.addEventListener("click", ()=> panels.status?.scrollIntoView({behavior:"smooth",block:"start"}));
  $("#smStat")?.addEventListener("click", ()=> panels.smart?.scrollIntoView({behavior:"smooth",block:"start"}));
  $("#gmStat")?.addEventListener("click", ()=> panels.goal?.scrollIntoView({behavior:"smooth",block:"start"}));
})();

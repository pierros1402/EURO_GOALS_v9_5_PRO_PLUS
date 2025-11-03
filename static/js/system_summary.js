// ======================================================================
// EURO_GOALS v9.3.4 – System Summary Manager (with Controls Hooks)
// ======================================================================
console.log("[EURO_GOALS] System Summary v9.3.4 loaded ✅");

let autoRefreshEnabled = true;      // Toggle state
let lastSmartMoneyMsg = "";         // Για μελλοντικό pulse όταν αλλάζει
const REFRESH_MS = 30000;

window.toggleAutoRefresh = function () {
  autoRefreshEnabled = !autoRefreshEnabled;
  const auto = document.getElementById("summary-auto");
  if (auto) {
    auto.innerHTML = autoRefreshEnabled ? "✅ Refresh: Active" : "❚❚ Refresh: Paused";
    auto.style.color = autoRefreshEnabled ? "#00e676" : "#ffd54f";
  }
  return autoRefreshEnabled;
};

window.updateSystemSummary = async function updateSystemSummary() {
  const summary = {
    database: document.getElementById("summary-database"),
    health: document.getElementById("summary-health"),
    auto: document.getElementById("summary-auto"),
    smartmoney: document.getElementById("summary-smartmoney"),
    render: document.getElementById("summary-render"),
    version: document.getElementById("summary-version"),
  };

  // Start “Checking…”
  for (const k in summary) {
    const el = summary[k];
    if (!el) continue;
    el.innerHTML = "⏳ Checking...";
    el.classList.add("pulse");
  }

  try {
    // 1) Core status
    const sys = await fetch("/system_status_data").then(r=>r.json());
    // 2) Modules
    const sm  = await fetch("/smartmoney_data").then(r=>r.json()).catch(()=>null);
    const gm  = await fetch("/goalmatrix_data").then(r=>r.json()).catch(()=>null);
    // 3) Optional Render URL ping: μπορεί να περαστεί από server μέσω template var στο μέλλον
    let renderStatus = sys.render || sys.status || "Unknown";

    // painter
    const set = (el, label, status) => {
      if (!el) return;
      el.classList.remove("pulse");
      const s = String(status??"").toLowerCase();
      let emoji="⚙️", color="#ffd54f";
      if (s.includes("ok") || s.includes("active") || s.includes("online")) { emoji="✅"; color="#00e676"; }
      else if (s.includes("fail") || s.includes("error") || s.includes("offline")) { emoji="❌"; color="#ff5252"; }
      el.innerHTML = `${emoji} ${label}: ${status}`;
      el.style.color = color;
    };

    set(summary.database, "DB", sys.database);
    set(summary.health, "Health", sys.status);
    set(summary.auto, "Refresh", autoRefreshEnabled ? "Active" : "Paused");
    set(summary.smartmoney, "SmartMoney", sm?.status || "Unknown");
    set(summary.render, "Render", renderStatus);
    set(summary.version, "Version", "v9.3.4");

    // SmartMoney pulse όταν αλλάζει μήνυμα (προετοιμασμένο για πραγματικά data)
    if (sm?.message && sm.message !== lastSmartMoneyMsg) {
      lastSmartMoneyMsg = sm.message;
      const el = summary.smartmoney;
      if (el) {
        el.animate([{transform:"scale(1)"},{transform:"scale(1.04)"},{transform:"scale(1)"}], {duration:650, iterations:3});
      }
    }

    // Footer ώρα
    const now = new Date().toLocaleTimeString("el-GR",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
    const footer = document.getElementById("summary-footer");
    if (footer) footer.innerHTML = `🕓 Τελευταίος έλεγχος: ${now}`;

    // ενημέρωσε modal listeners
    document.dispatchEvent(new Event("summary-updated"));
  } catch (err) {
    console.error("❌ System Summary error:", err);
    for (const k in summary) {
      const el = summary[k];
      if (!el) continue;
      el.classList.remove("pulse");
      el.innerHTML = "⚠️ Error";
      el.style.color = "#ff5252";
    }
  }
};

// Auto loop
window.updateSystemSummary();
setInterval(() => { if (autoRefreshEnabled) window.updateSystemSummary(); }, REFRESH_MS);

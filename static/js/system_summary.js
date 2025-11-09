// ============================================================
// EURO_GOALS v9.5.5 PRO+ Unified — System Summary Controller
// Συγχρονισμένο με το endpoint /system_status
// ============================================================

(async function () {
  const el = document.getElementById("system-summary");
  if (!el) return;

  // Εικονίδια / χρωματισμοί κατάστασης
  const STATUS = {
    active: "🟢",
    inactive: "⚫",
    error: "🔴",
  };

  async function getJSON(url) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(res.statusText);
      return await res.json();
    } catch (err) {
      console.warn("[EURO_GOALS] System summary fetch error:", err);
      return null;
    }
  }

  async function updateSummary() {
    const data = await getJSON("/system_status");
    if (!data) {
      el.innerHTML =
        `<div class="text-red-400 text-sm">⚠ Σφάλμα σύνδεσης με το σύστημα</div>`;
      return;
    }

    const engines = data.engines || {};
    const version = data.version || "—";

    function row(name, icon, engine) {
      const active = engine.active ? STATUS.active : STATUS.error;
      const count =
        engine.alerts !== undefined
          ? engine.alerts
          : engine.items !== undefined
          ? engine.items
          : engine.history_items ?? 0;
      return `
        <div class="summary-item flex justify-between items-center text-sm py-1 border-b border-gray-700/50">
          <span class="font-semibold text-sky-400">${icon} ${name}</span>
          <span class="text-gray-300">${active} ${count}</span>
        </div>`;
    }

    el.innerHTML = `
      <div class="bg-gray-900/70 rounded-xl shadow p-3 text-gray-100">
        <div class="flex justify-between items-center mb-2">
          <h4 class="text-sm font-semibold text-sky-400">⚙️ System Summary</h4>
          <span class="text-xs text-gray-400">v${version}</span>
        </div>
        ${row("SmartMoney", "💰", engines.smartmoney || {})}
        ${row("GoalMatrix", "🎯", engines.goalmatrix || {})}
        ${row("Heatmap", "🔥", engines.heatmap || {})}
        ${row("History", "📜", engines.history || {})}
      </div>
    `;
  }

  // Εκτέλεση και αυτόματη ανανέωση κάθε 10 s
  await updateSummary();
  setInterval(updateSummary, 10000);
})();

// ============================================================
// EURO_GOALS v9.5.5 PRO+ — Unified UI Controls / Auto-Refresh
// ============================================================

let autoRefreshEnabled = true;
let idleTimer;

// ------------------------------------------------------------
// 🕒 Auto-refresh loop για συνεχή ενημέρωση
// ------------------------------------------------------------
async function autoRefreshLoop() {
  while (true) {
    if (autoRefreshEnabled) {
      try {
        // Ανανεώνει μόνο το unified system summary
        await fetch("/system_status");
      } catch (err) {
        console.warn("[EURO_GOALS] Auto-refresh fetch error:", err);
      }
    }
    await new Promise((r) => setTimeout(r, 15000)); // κάθε 15s
  }
}
autoRefreshLoop();

// ------------------------------------------------------------
// 👁️ Pause αν κρυφτεί το tab / Resume αν επιστρέψει
// ------------------------------------------------------------
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopAutoRefresh();
  } else {
    startAutoRefresh();
  }
});

// ------------------------------------------------------------
// 💤 Auto stop αν μείνει ανενεργό το tab για 10 λεπτά
// ------------------------------------------------------------
function resetIdleTimer() {
  clearTimeout(idleTimer);
  startAutoRefresh();
  idleTimer = setTimeout(stopAutoRefresh, 10 * 60 * 1000);
}
["mousemove", "keydown", "touchstart"].forEach((ev) =>
  window.addEventListener(ev, resetIdleTimer)
);
resetIdleTimer();

// ------------------------------------------------------------
// 🔴 Stop / 🟢 Start λειτουργίες
// ------------------------------------------------------------
function stopAutoRefresh() {
  if (autoRefreshEnabled) {
    console.log("🔴 Auto-refresh paused (idle/tab hidden)");
  }
  autoRefreshEnabled = false;
}
function startAutoRefresh() {
  if (!autoRefreshEnabled) {
    console.log("🟢 Auto-refresh resumed");
  }
  autoRefreshEnabled = true;
}

// ------------------------------------------------------------
// 🧠 Manual Refresh Button Sync (αν υπάρχει στο UI)
// ------------------------------------------------------------
function refreshStatusSync() {
  const btn = document.getElementById("quickRefresh");
  if (!btn) return;
  btn.style.opacity = autoRefreshEnabled ? "1" : "0.5";
}
setInterval(refreshStatusSync, 2000);

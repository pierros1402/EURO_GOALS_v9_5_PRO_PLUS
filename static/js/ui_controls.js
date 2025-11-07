// =====================================================
// Smart Auto-Stop + Idle Timer (EURO_GOALS v9.5.1 PRO+)
// =====================================================
let autoRefreshEnabled = true;
let idleTimer;

// Stop/start refresh
function stopAutoRefresh() {
  autoRefreshEnabled = false;
  console.log("🔴 Auto-refresh paused (idle/tab hidden)");
}
function startAutoRefresh() {
  if (!autoRefreshEnabled) console.log("🟢 Auto-refresh resumed");
  autoRefreshEnabled = true;
}

// Simulated auto-refresh loop
async function autoRefreshLoop() {
  while (true) {
    if (autoRefreshEnabled) {
      fetch("/api/alerts_feed").catch(() => {});
    }
    await new Promise(r => setTimeout(r, 15000));
  }
}
autoRefreshLoop();

// Smart auto-stop if tab hidden
document.addEventListener("visibilitychange", () => {
  if (document.hidden) stopAutoRefresh();
  else startAutoRefresh();
});

// Idle timer 10 min
function resetIdleTimer() {
  clearTimeout(idleTimer);
  startAutoRefresh();
  idleTimer = setTimeout(stopAutoRefresh, 10 * 60 * 1000);
}
["mousemove", "keydown", "touchstart"].forEach(ev =>
  window.addEventListener(ev, resetIdleTimer)
);
resetIdleTimer();
function refreshStatusSync() {
  setRefreshStatus(autoRefreshEnabled);
}
setInterval(refreshStatusSync, 2000);

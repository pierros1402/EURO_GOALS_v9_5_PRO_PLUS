// =====================================================
// System Status & LED Updater + Render Status Panel
// =====================================================

let startTime = Date.now();

async function checkHealth() {
  try {
    const start = performance.now();
    const res = await fetch("/health", { cache: "no-store" });
    const data = await res.json();
    const latency = Math.round(performance.now() - start);

    updateLED("led-render", true);
    updateLED("led-db", data.components?.db ?? true);
    updateLED("led-flashscore", data.components?.flashscore ?? true);
    updateLED("led-sofascore", data.components?.sofascore ?? true);
    updateLED("led-asianconnect", data.components?.asianconnect ?? false);

    document.getElementById("status-latency").innerHTML = `⏱ ${latency} ms`;
    updateUptime();
  } catch (err) {
    console.warn("Health check failed", err);
  }
}

function updateLED(id, active) {
  const led = document.getElementById(id);
  if (!led) return;
  active ? led.classList.add("on") : led.classList.remove("on");
}

function updateUptime() {
  const uptimeMs = Date.now() - startTime;
  const hrs = Math.floor(uptimeMs / 3600000);
  const mins = Math.floor((uptimeMs % 3600000) / 60000);
  const secs = Math.floor((uptimeMs % 60000) / 1000);
  document.getElementById("status-uptime").innerHTML =
    `🕒 ${hrs}:${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
}

function setRefreshStatus(on) {
  const el = document.getElementById("status-refresh");
  if (!el) return;
  el.innerHTML = on
    ? "🔄 Refresh: <b>ON</b>"
    : "⏸ Refresh: <b>OFF</b>";
}

// Periodic updates
setInterval(checkHealth, 30000);
checkHealth();
updateUptime();
setInterval(updateUptime, 1000);

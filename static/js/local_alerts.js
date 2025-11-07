// =====================================================
// EURO_GOALS v9.5.0 PRO+
// Local Push Alerts + Health Check Auto-Recover System
// =====================================================

// ---------- Sound Setup ----------
const sounds = {
  SmartMoney: new Audio("/static/sounds/smartmoney_alert.mp3"),
  GoalMatrix: new Audio("/static/sounds/goal_alert.mp3"),
  System: new Audio("/static/sounds/alert.mp3"),
  Reconnect: new Audio("/static/sounds/reconnect.mp3")
};

// ---------- Notification Permission ----------
if ("Notification" in window && Notification.permission !== "granted") {
  Notification.requestPermission().then(result => {
    console.log("[EURO_GOALS] Notification permission:", result);
  });
}

// ---------- Local Push Trigger ----------
function triggerLocalAlert(type, message) {
  try {
    const sound = sounds[type] || sounds.System;
    sound.currentTime = 0;
    sound.play().catch(()=>{});
  } catch (err) {
    console.warn("[EURO_GOALS] Sound playback failed:", err);
  }

  if ("Notification" in window && Notification.permission === "granted") {
    const n = new Notification(`${type} Alert`, {
      body: message,
      icon: "/static/icons/icon-192.png",
      badge: "/static/icons/icon-192.png"
    });
    setTimeout(() => n.close(), 6000);
  }
  console.log(`[EURO_GOALS] Local alert triggered: ${type} - ${message}`);
}

// ---------- Listen for Alert Feed Events ----------
window.addEventListener("EG_NEW_ALERT", (e) => {
  const { type, msg } = e.detail;
  triggerLocalAlert(type, msg);
});

// =====================================================
// 🧠 HEALTH CHECK AUTO-RECOVER
// =====================================================
let healthCheckTimer = null;
let reconnectShown = false;

async function checkServerHealth() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const res = await fetch("/health", { signal: controller.signal, cache: "no-store" });
    clearTimeout(timeout);
    if (!res.ok) throw new Error(res.statusText);

    // Server OK
    if (reconnectShown) hideReconnectBanner();
    scheduleNextCheck();
  } catch (err) {
    console.warn("[EURO_GOALS] Health check failed:", err);
    showReconnectBanner();
    scheduleRetry();
  }
}

function scheduleNextCheck() {
  clearTimeout(healthCheckTimer);
  healthCheckTimer = setTimeout(checkServerHealth, 20000);
}

function scheduleRetry() {
  clearTimeout(healthCheckTimer);
  healthCheckTimer = setTimeout(checkServerHealth, 10000);
}

function showReconnectBanner() {
  if (reconnectShown) return;
  reconnectShown = true;
  const banner = document.createElement("div");
  banner.id = "reconnectBanner";
  banner.innerHTML = `
    <div style="
      position:fixed;top:10px;left:50%;transform:translateX(-50%);
      background:#b71c1c;color:#fff;padding:10px 18px;
      border-radius:10px;z-index:9999;font-family:sans-serif;
      box-shadow:0 2px 12px rgba(0,0,0,.3);">
      🔄 Reconnecting to Render...
    </div>`;
  document.body.appendChild(banner);
  sounds.Reconnect.play().catch(()=>{});
}

function hideReconnectBanner() {
  const el = document.getElementById("reconnectBanner");
  if (!el) return;
  el.remove();
  reconnectShown = false;
  triggerLocalAlert("System", "Server connection restored");
}

// Initial trigger
setTimeout(checkServerHealth, 8000);

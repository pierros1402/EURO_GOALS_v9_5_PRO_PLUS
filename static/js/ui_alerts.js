// =====================================================
// EURO_GOALS v9.5.0 PRO+
// UI Alerts Module – SmartMoney + GoalMatrix + System Alerts
// =====================================================

let lastAlertCount = 0;
const alertContainer = document.querySelector("#alerts .eg-card-body");

// =====================================================
// 🧠 Fetch Alerts Feed
// =====================================================
async function fetchAlertsFeed() {
  try {
    const response = await fetch("/api/alerts_feed", { cache: "no-store" });
    if (!response.ok) throw new Error("Network response not ok");
    const data = await response.json();
    renderAlerts(data);
  } catch (err) {
    console.warn("[EURO_GOALS] Alert feed fetch failed:", err);
  } finally {
    scheduleNextFetch();
  }
}

// =====================================================
// ⏱ Auto Refresh
// =====================================================
function scheduleNextFetch() {
  const secs = window.__EG__?.initialRefreshSecs || 15;
  setTimeout(fetchAlertsFeed, secs * 1000);
}

// =====================================================
// 📋 Render Alerts in UI
// =====================================================
function renderAlerts(data) {
  if (!data || !Array.isArray(data.alerts)) return;

  const alerts = data.alerts;
  alertContainer.innerHTML = "";

  alerts.forEach(a => {
    const item = document.createElement("div");
    item.className = `alert-item alert-${a.type.toLowerCase()}`;
    item.innerHTML = `
      <div class="alert-time">${a.time}</div>
      <div class="alert-type">${a.type}</div>
      <div class="alert-msg">${a.msg}</div>
    `;
    alertContainer.appendChild(item);
  });

  // ---- Trigger local alert if new ----
  if (data.count > lastAlertCount) {
    const latest = data.alerts[0];
    lastAlertCount = data.count;

    // Dispatch event to Local Push System
    window.dispatchEvent(new CustomEvent("EG_NEW_ALERT", {
      detail: { type: latest.type, msg: latest.msg }
    }));

    console.log(`[EURO_GOALS] New alert (${latest.type}): ${latest.msg}`);
  }
}

// =====================================================
// 🧹 Clear Alerts
// =====================================================
function clearAlerts() {
  alertContainer.innerHTML = "";
  lastAlertCount = 0;
  console.log("[EURO_GOALS] Alerts cleared");
}

// =====================================================
// 🎛 UI Event Bindings
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
  const clearBtn = document.getElementById("clearAlerts");
  if (clearBtn) {
    clearBtn.addEventListener("click", clearAlerts);
  }
  fetchAlertsFeed();
});

// =====================================================
// 🔊 Utility: Visual alert blink
// =====================================================
window.addEventListener("EG_NEW_ALERT", (e) => {
  const { type } = e.detail;
  const card = document.getElementById("alerts");
  if (!card) return;
  card.classList.add("blink");
  setTimeout(() => card.classList.remove("blink"), 800);

  // Optional console display
  console.log(`[EURO_GOALS] Blinked on new ${type} alert`);
});

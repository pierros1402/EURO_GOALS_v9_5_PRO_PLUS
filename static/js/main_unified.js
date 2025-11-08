// ============================================================
// EURO_GOALS PRO+ v9.5.4 – MAIN UNIFIED CONTROLLER
// ============================================================
// Ενοποιεί όλο το frontend startup:
// - Service Worker & PWA setup
// - Push subscription (VAPID)
// - SmartMoney, GoalMatrix, Alerts, System Health refresh
// - Auto refresh, Idle Timer, Render auto-stop
// ============================================================

// --- Imports ---
import { registerServiceWorker } from "./register-sw.js";
import "./system_status.js";
import "./push_manager.js";
import "./render_auto_stop.js";
import "./pwa_install_prompt.js";
import "./ui_controls.js";

// ============================================================
// PWA / Notifications
// ============================================================
registerServiceWorker();

const EG = {
  notify: JSON.parse(localStorage.getItem("eg_notify") || "true"),
  sound: JSON.parse(localStorage.getItem("eg_sound") || "true"),
  audio: new Audio("/static/sounds/alert.mp3"),
};

function ensureAudio() {
  EG.audio.volume = 0.9;
  EG.audio.preload = "auto";
  return EG.audio;
}

function triggerNotification(title, body) {
  if (EG.sound) {
    const a = ensureAudio();
    try { a.currentTime = 0; a.play().catch(()=>{}); } catch {}
  }
  if (EG.notify && "Notification" in window && Notification.permission === "granted") {
    const n = new Notification(title, { body, icon: "/public/icons/icon-192.png" });
    setTimeout(() => n.close(), 6000);
  }
}

function injectNotifyToggle() {
  if (document.getElementById("eg-toggles")) return;
  const wrap = document.createElement("div");
  wrap.id = "eg-toggles";
  wrap.style.cssText = `
    position:fixed;right:14px;bottom:14px;z-index:9999;
    background:#101010b5;color:#fff;padding:8px 12px;
    border-radius:12px;font:500 13px system-ui;display:flex;gap:10px;align-items:center;
  `;
  wrap.innerHTML = `
    <label><input type="checkbox" id="eg-notify" ${EG.notify ? "checked" : ""}>🔔</label>
    <label><input type="checkbox" id="eg-sound" ${EG.sound ? "checked" : ""}>🎵</label>
  `;
  document.body.appendChild(wrap);
  wrap.querySelector("#eg-notify").addEventListener("change", (e) => {
    EG.notify = e.target.checked;
    localStorage.setItem("eg_notify", JSON.stringify(EG.notify));
    if (EG.notify) Notification.requestPermission();
  });
  wrap.querySelector("#eg-sound").addEventListener("change", (e) => {
    EG.sound = e.target.checked;
    localStorage.setItem("eg_sound", JSON.stringify(EG.sound));
    if (EG.sound) ensureAudio();
  });
}

// ============================================================
// Data Refreshers
// ============================================================
async function refreshSmartMoney() {
  const el = document.getElementById("smartmoney-monitor");
  if (!el) return;
  try {
    const res = await fetch("/api/smartmoney/alerts", { cache: "no-store" });
    const data = await res.json();
    el.innerHTML = data.alerts
      .slice(0, 5)
      .map(
        (a) => `<div class="eg-log eg-ok">💰 ${a.league}: ${a.match} – ${a.money_flow}%</div>`
      )
      .join("");
  } catch {
    el.innerHTML = `<div class="eg-card-dim">SmartMoney offline</div>`;
  }
}

async function refreshGoalMatrix() {
  const el = document.getElementById("goalmatrix-heatmap");
  if (!el) return;
  try {
    const res = await fetch("/api/goalmatrix/summary", { cache: "no-store" });
    const data = await res.json();
    el.innerHTML = `
      <div>Matches: ${data.total_matches}</div>
      <div>Avg xG: ${data.avg_goals}</div>
      <div>Status: ${data.status}</div>`;
  } catch {
    el.innerHTML = `<div class="eg-card-dim">GoalMatrix offline</div>`;
  }
}

async function refreshAlerts() {
  const el = document.getElementById("alerts-history");
  if (!el) return;
  try {
    const res = await fetch("/api/alerts_feed", { cache: "no-store" });
    const data = await res.json();
    el.innerHTML = data
      .slice(0, 5)
      .map(
        (a) => `<div class="eg-log eg-ok">[${a.time}] ${a.type} – ${a.desc}</div>`
      )
      .join("");
    if (data.length) triggerNotification("New EURO_GOALS Alert", data[0].desc);
  } catch {
    el.innerHTML = `<div class="eg-card-dim">Alerts feed offline</div>`;
  }
}

async function refreshSystemHealth() {
  const el = document.getElementById("system-health");
  if (!el) return;
  try {
    const res = await fetch("/health", { cache: "no-store" });
    const data = await res.json();
    el.innerHTML = `
      <img src="/static/icons/eg_logo.png" style="width:100px;">
      <p style="opacity:.8;">✅ ${data.service}<br><small>${new Date().toLocaleTimeString()}</small></p>`;
  } catch {
    el.innerHTML = `<p style="color:#ef4444;">❌ System Offline</p>`;
  }
}

// ============================================================
// Unified Loop
// ============================================================
async function unifiedRefresh() {
  await Promise.all([
    refreshSmartMoney(),
    refreshGoalMatrix(),
    refreshAlerts(),
    refreshSystemHealth(),
  ]);
}
setInterval(unifiedRefresh, 30000);

// ============================================================
// Startup
// ============================================================
window.addEventListener("load", async () => {
  injectNotifyToggle();
  await unifiedRefresh();
  console.log("[EURO_GOALS] ✅ main_unified.js initialized (v9.5.4)");
});

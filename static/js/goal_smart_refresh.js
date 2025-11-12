// ============================================================
// EURO_GOALS PRO+ v9.9.5 — GoalMatrix + SmartMoney + Sound + Notifications + UI effects
// ============================================================

const refreshInterval = 30000; // 30s
let gmBusy = false, smBusy = false;
let lastAlerts = 0;

// 🎵 Προετοιμασία ήχων
const sounds = {
  goal: new Audio("/static/sounds/goal_alert.mp3"),
  smart: new Audio("/static/sounds/smartmoney_alert.mp3"),
  refresh: new Audio("/static/sounds/refresh_click.mp3")
};
Object.values(sounds).forEach(s => (s.volume = 0.7));

// ============================================================
// SOUND TOGGLE
// ============================================================
let soundEnabled = localStorage.getItem("soundEnabled") !== "false";
const btnSound = document.getElementById("btnSound");

function updateSoundIcon() {
  if (!btnSound) return;
  btnSound.textContent = soundEnabled ? "🔊" : "🔇";
}

btnSound?.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  localStorage.setItem("soundEnabled", soundEnabled);
  updateSoundIcon();
});

updateSoundIcon();

function playSound(sound) {
  if (soundEnabled && sound) {
    sound.currentTime = 0;
    sound.play().catch(() => {});
  }
}

// ============================================================
// NOTIFICATION TOGGLE
// ============================================================
let notifyEnabled = localStorage.getItem("notifyEnabled") === "true";
const btnNotify = document.getElementById("btnNotify");

function updateNotifyIcon() {
  if (!btnNotify) return;
  btnNotify.textContent = notifyEnabled ? "🔔" : "🔕";
}

btnNotify?.addEventListener("click", async () => {
  if (!("Notification" in window)) {
    alert("Ο browser δεν υποστηρίζει ειδοποιήσεις.");
    return;
  }
  if (Notification.permission === "default") {
    await Notification.requestPermission();
  }
  if (Notification.permission === "granted") {
    notifyEnabled = !notifyEnabled;
    localStorage.setItem("notifyEnabled", notifyEnabled);
    updateNotifyIcon();
  } else {
    alert("Δεν έχεις επιτρέψει ειδοποιήσεις στον browser.");
  }
});

updateNotifyIcon();

function pushNotify(title, body) {
  if (notifyEnabled && Notification.permission === "granted") {
    new Notification(title, {
      body: body,
      icon: "/static/icons/eurogoals_192.png",
      badge: "/static/icons/eurogoals_192.png"
    });
  }
}

// ============================================================
// UI HELPERS — pulse, refresh dot, event log, toasts
// ============================================================
function pulsePanel(id, color = "emerald") {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove("eg-pulse-emerald","eg-pulse-amber");
  el.classList.add(color === "amber" ? "eg-pulse-amber" : "eg-pulse-emerald");
  setTimeout(() => el.classList.remove("eg-pulse-emerald","eg-pulse-amber"), 1800);
}

function flickRefreshDot() {
  const dot = document.getElementById("eg-refresh-dot");
  if (!dot) return;
  dot.classList.remove("blink");
  // retrigger animation
  void dot.offsetWidth;
  dot.classList.add("blink");
}

const _events = [];
function logEvent(txt) {
  _events.unshift(`${new Date().toLocaleTimeString("el-GR",{hour12:false})} — ${txt}`);
  if (_events.length > 3) _events.pop();
  const box = document.getElementById("eg-eventlog");
  if (!box) return;
  box.innerHTML = _events.map(e => `<div class="row">${e}</div>`).join("");
  box.classList.remove("hidden");
  setTimeout(() => box.classList.add("hidden"), 4000);
}

function toastSafe(type, title, msg) {
  if (typeof window.showToast === "function") {
    window.showToast(type, title, msg);
  } else {
    console.log(`[TOAST ${type}] ${title} — ${msg}`);
  }
}

// ============================================================
// GOALMATRIX ENGINE
// ============================================================
async function refreshGoalMatrix() {
  if (gmBusy) return;
  gmBusy = true;
  const gmStatus = document.getElementById("gm-status-pill");
  const gmBody = document.getElementById("gm-body");
  const gmTotal = document.getElementById("gm-summary-total");
  const gmUpdated = document.getElementById("gm-summary-updated");

  try {
    const res = await fetch("/api/goalmatrix/summary");
    const data = await res.json();
    const items = data.matches || data.summary || [];
    const active = data.status === "ok" || items.length > 0;

    gmStatus.textContent = active ? "Ενεργό" : "Ανενεργό";
    gmStatus.className =
      "px-2 py-1 rounded text-xs " +
      (active ? "bg-emerald-500 text-black" : "bg-red-600 text-white");
    gmTotal.textContent = `Αγώνες: ${items.length}`;
    gmUpdated.textContent =
      "Ενημέρωση: " +
      new Date().toLocaleTimeString("el-GR", { hour12: false });

    gmBody.innerHTML = items.length
      ? items
          .slice(0, 10)
          .map((m) => {
            const move =
              m.movement && m.movement !== 0
                ? `${m.movement > 0 ? "+" : ""}${m.movement}%`
                : "-";
            const color =
              m.movement > 0
                ? "text-green-400"
                : m.movement < 0
                ? "text-red-400"
                : "text-gray-300";
            return `
            <tr class="hover:bg-neutral-800/60 transition">
              <td class="p-2">${m.league || "-"}</td>
              <td class="p-2">${m.match || `${m.home_team || "?"} vs ${m.away_team || "?"}`}</td>
              <td class="p-2 text-right">${m.opening_odds ?? "-"}</td>
              <td class="p-2 text-right">${m.current_odds ?? "-"}</td>
              <td class="p-2 text-center ${color}">${move}</td>
            </tr>`;
          })
          .join("")
      : `<tr><td colspan="5" class="p-3 text-center text-gray-400">Δεν υπάρχουν ενεργά δεδομένα GoalMatrix.</td></tr>`;

    // 🔔 Alert: ισχυρή μεταβολή
    if (items.some(m => Math.abs(m.movement || 0) >= 15)) {
      playSound(sounds.goal);
      pushNotify("GoalMatrix Movement", "Εντοπίστηκε ισχυρή μεταβολή απόδοσης!");
      toastSafe("goal", "GoalMatrix Alert", "Ισχυρή μεταβολή σε ενεργό αγώνα");
      pulsePanel("goal-matrix-panel", "amber");
      logEvent("GoalMatrix alert");
    }

  } catch (err) {
    console.warn("GoalMatrix refresh error", err);
    gmStatus.textContent = "Σφάλμα";
    gmStatus.className = "px-2 py-1 rounded text-xs bg-red-600 text-white";
  }
  gmBusy = false;
}

// ============================================================
// SMARTMONEY ENGINE
// ============================================================
async function refreshSmartMoney() {
  if (smBusy) return;
  smBusy = true;
  const smStatus = document.getElementById("sm-status-pill");
  const smBody = document.getElementById("sm-body");
  const smTotal = document.getElementById("sm-summary-total");
  const smUpdated = document.getElementById("sm-summary-updated");

  try {
    const res = await fetch("/api/smartmoney/summary");
    const data = await res.json();
    const items = data.matches || data.summary || [];
    const active = data.status === "ok" || items.length > 0;

    smStatus.textContent = active ? "Ενεργό" : "Ανενεργό";
    smStatus.className =
      "px-2 py-1 rounded text-xs " +
      (active ? "bg-emerald-500 text-black" : "bg-red-600 text-white");
    smTotal.textContent = `Σύνολο αγώνων: ${items.length}`;
    smUpdated.textContent =
      "Ενημέρωση: " +
      new Date().toLocaleTimeString("el-GR", { hour12: false });

    let totalAlerts = 0;

    smBody.innerHTML = items.length
      ? items
          .slice(0, 10)
          .map((m) => {
            const change =
              m.change && m.change !== 0
                ? `${m.change > 0 ? "+" : ""}${m.change}%`
                : "-";
            const color =
              m.change > 0
                ? "text-green-400"
                : m.change < 0
                ? "text-red-400"
                : "text-gray-300";
            totalAlerts += m.alerts ?? 0;
            return `
            <tr class="hover:bg-neutral-800/60 transition">
              <td class="p-2">${m.league || "-"}</td>
              <td class="p-2">${m.match || `${m.home_team || "?"} vs ${m.away_team || "?"}`}</td>
              <td class="p-2 text-right">${m.odds ? m.odds.toFixed(2) : "-"}</td>
              <td class="p-2 text-right ${color}">${change}</td>
              <td class="p-2 text-center">${m.alerts ?? 0}</td>
            </tr>`;
          })
          .join("")
      : `<tr><td colspan="5" class="p-3 text-center text-gray-400">Δεν υπάρχουν ενεργά δεδομένα SmartMoney.</td></tr>`;

    // 🔔 Alert: νέα smart money σήματα
    if (totalAlerts > lastAlerts) {
      playSound(sounds.smart);
      pushNotify("SmartMoney Alert", `Νέα ενεργά alerts: ${totalAlerts}`);
      toastSafe("smart", "SmartMoney Alert", `Σύνολο: ${totalAlerts}`);
      pulsePanel("smartmoney-panel", "emerald");
      logEvent("SmartMoney alert");
    }
    lastAlerts = totalAlerts;

  } catch (err) {
    console.warn("SmartMoney refresh error", err);
    smStatus.textContent = "Σφάλμα";
    smStatus.className = "px-2 py-1 rounded text-xs bg-red-600 text-white";
  }
  smBusy = false;
}

// ============================================================
// INIT / LOOP
// ============================================================
window.addEventListener("load", () => {
  playSound(sounds.refresh);
  flickRefreshDot();
  logEvent("UI ready");

  refreshGoalMatrix();
  refreshSmartMoney();

  setInterval(() => {
    playSound(sounds.refresh);
    flickRefreshDot();
    logEvent("Refresh");
    refreshGoalMatrix();
    refreshSmartMoney();
  }, refreshInterval);
});

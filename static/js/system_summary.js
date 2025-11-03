// =====================================================
// EURO_GOALS v9.4.2 PRO+ – System Summary & Notifications
// =====================================================

let smartmoneyRunning = true;
let alertCounter = 0;

const statusEl = document.getElementById("smartmoney-status");
const counterEl = document.getElementById("alert-counter");
const btn = document.getElementById("toggle-smartmoney");
const soundEl = document.getElementById("alert-sound");

// Ζητάει άδεια για ειδοποιήσεις
if ("Notification" in window && Notification.permission !== "granted") {
  Notification.requestPermission();
}

btn.addEventListener("click", () => {
  smartmoneyRunning = !smartmoneyRunning;
  statusEl.textContent = smartmoneyRunning ? "LIVE" : "PAUSED";
  btn.textContent = smartmoneyRunning ? "⏸️ Pause SmartMoney" : "▶️ Resume SmartMoney";
  btn.classList.toggle("bg-blue-600");
  btn.classList.toggle("bg-green-600");
  console.log("SmartMoney:", smartmoneyRunning);
});

// Health check
async function updateHealth() {
  try {
    const res = await fetch("/health");
    const d = await res.json();
    document.getElementById("summary-database").textContent =
      "💾 DB: " + (d.database === "connected" ? "OK" : "Error");
    document.getElementById("summary-health").textContent =
      "❤️ Health: " + (d.status === "ok" ? "OK" : "Error");
  } catch {
    document.getElementById("summary-health").textContent = "❤️ Health: Fail";
  }
}

setInterval(updateHealth, 60000);
updateHealth();

// Ειδοποίηση SmartMoney από localStorage
window.addEventListener("storage", (e) => {
  if (e.key === "newSmartMoneyAlert") {
    alertCounter++;
    counterEl.textContent = alertCounter;
    if (soundEl) soundEl.play();
    if (Notification.permission === "granted") {
      new Notification("💰 SmartMoney Alert", { body: e.newValue });
    }
  }
});

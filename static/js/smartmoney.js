// ============================================================
// SMARTMONEY PANEL SCRIPT – EURO_GOALS v9.5.4 PRO+
// ============================================================

async function loadSmartMoneyStatus() {
  try {
    const response = await fetch("/api/smartmoney/status");
    const data = await response.json();

    const panel = document.getElementById("smartmoney-status");
    if (!panel) return;

    if (data.error) {
      panel.innerHTML = `🚫 Engine Offline (${data.message || 'No response'})`;
      panel.style.color = "red";
    } else {
      panel.innerHTML = `💰 Active – ${data.status || 'OK'}`;
      panel.style.color = "green";
    }
  } catch (err) {
    console.error("SmartMoney fetch error:", err);
  }
}

// Auto-refresh every 60s
setInterval(loadSmartMoneyStatus, 60000);
window.addEventListener("load", loadSmartMoneyStatus);

// ======================================================================
// EURO_GOALS v9.3.3 – System Summary Manager
// ======================================================================
// ➤ Ενημερώνει ζωντανά το System Summary Bar
// ➤ Περιλαμβάνει:
//    ✅ DB + Health + Render Status
//    ✅ SmartMoney / GoalMatrix Live Indicators
//    ✅ Auto Timestamp "Τελευταίος έλεγχος"
//    ✅ Προετοιμασία για Auto-Refresh Toggle & Pulse animation
// ======================================================================

console.log("[EURO_GOALS] System Summary v9.3.3 loaded ✅");

let autoRefreshEnabled = true; // toggle-ready

async function updateSystemSummary() {
  const summary = {
    database: document.getElementById("summary-database"),
    health: document.getElementById("summary-health"),
    auto: document.getElementById("summary-auto"),
    smartmoney: document.getElementById("summary-smartmoney"),
    render: document.getElementById("summary-render"),
    version: document.getElementById("summary-version"),
  };

  // Εμφάνιση “Checking…” με animation
  for (const key in summary) {
    if (summary[key]) {
      summary[key].innerHTML = "⏳ Checking...";
      summary[key].classList.add("pulse");
    }
  }

  try {
    // --- 1️⃣ Ανάκτηση δεδομένων συστήματος ---
    const response = await fetch("/system_status_data");
    const data = await response.json();

    // --- 2️⃣ Render Health URL Ping ---
    const healthUrl = "{{ RENDER_HEALTH_URL }}"; // placeholder για Jinja (αν θες μπορούμε να το περνάμε server-side)
    let renderStatus = data.render || "Unknown";
    try {
      if (healthUrl && healthUrl.startsWith("http")) {
        const ping = await fetch(healthUrl);
        renderStatus = ping.status === 200 ? "Online" : "Offline";
      }
    } catch (e) {
      renderStatus = "Offline";
    }

    // --- 3️⃣ SmartMoney + GoalMatrix data ---
    let smartMoneyData = await fetch("/smartmoney_data").then(r => r.json()).catch(() => null);
    let goalMatrixData = await fetch("/goalmatrix_data").then(r => r.json()).catch(() => null);

    // --- 4️⃣ Συνάρτηση ενημέρωσης πεδίων ---
    const setStatus = (element, label, status) => {
      if (!element) return;
      element.classList.remove("pulse");

      const statusLower = String(status).toLowerCase();
      let emoji = "⚙️";
      let color = "#ffd54f";

      if (statusLower.includes("ok") || statusLower.includes("active") || statusLower.includes("online")) {
        emoji = "✅";
        color = "#00e676";
      } else if (statusLower.includes("fail") || statusLower.includes("error") || statusLower.includes("offline")) {
        emoji = "❌";
        color = "#ff5252";
      }

      element.innerHTML = `${emoji} ${label}: ${status}`;
      element.style.color = color;
    };

    // --- 5️⃣ Ενημέρωση πεδίων ---
    setStatus(summary.database, "DB", data.database);
    setStatus(summary.health, "Health", data.status);
    setStatus(summary.auto, "Refresh", autoRefreshEnabled ? "Active" : "Paused");
    setStatus(summary.smartmoney, "SmartMoney", smartMoneyData?.status || "Unknown");
    setStatus(summary.render, "Render", renderStatus);
    setStatus(summary.version, "Version", "v9.3.3");

    // --- 6️⃣ Εμφάνιση ώρας τελευταίου ελέγχου ---
    const now = new Date().toLocaleTimeString("el-GR", {
      hour: "2-digit", minute: "2-digit", second: "2-digit"
    });

    let footer = document.getElementById("summary-footer");
    if (footer) footer.innerHTML = `🕓 Τελευταίος έλεγχος: ${now}`;

    // --- 7️⃣ Εκπομπή event για άλλες λειτουργίες (π.χ. Pulse ή Alert) ---
    document.dispatchEvent(new Event("summary-updated"));
  } catch (error) {
    console.error("❌ Error updating summary:", error);
    for (const key in summary) {
      if (summary[key]) {
        summary[key].innerHTML = "⚠️ Error";
        summary[key].style.color = "#ff5252";
      }
    }
  }
}

// =============================================================
// Αυτόματος έλεγχος (30s) – με toggle υποστήριξη
// =============================================================
updateSystemSummary();
setInterval(() => {
  if (autoRefreshEnabled) updateSystemSummary();
}, 30000);

// ================================================================
// EURO_GOALS v9.4.2 – SmartMoney Auto-Notifier PRO (Frontend Engine)
// ================================================================

let smartmoneyActive = true; // τρέχουσα κατάσταση (LIVE ή PAUSED)
const tableBody = document.getElementById("smartmoney-history-body");
const lastUpdateEl = document.getElementById("last-update");

// Συνδέεται με το κουμπί ON/OFF του System Status Panel
const toggleBtn = document.getElementById("toggle-smartmoney");
if (toggleBtn) {
  toggleBtn.addEventListener("click", () => {
    smartmoneyActive = !smartmoneyActive;
    console.log("SmartMoney:", smartmoneyActive ? "LIVE" : "PAUSED");
  });
}

// Κύρια συνάρτηση fetch
async function fetchSmartMoney() {
  if (!smartmoneyActive) return; // αν είναι πατημένο PAUSED, σταματά

  try {
    const res = await fetch("/smartmoney/history?limit=50");
    const data = await res.json();
    const alerts = data.items || [];

    tableBody.innerHTML = "";
    alerts.forEach(a => {
      const tr = document.createElement("tr");
      const pct = ((a.change_pct || 0) * 100).toFixed(1) + "%";
      const odds = `${a.old_price} → ${a.new_price}`;
      tr.innerHTML = `
        <td class="px-2 py-1">${new Date(a.ts_utc).toLocaleTimeString("el-GR")}</td>
        <td class="px-2 py-1">${a.home} vs ${a.away}</td>
        <td class="px-2 py-1">${a.bookmaker}</td>
        <td class="px-2 py-1">${a.market}</td>
        <td class="px-2 py-1">${a.selection}</td>
        <td class="px-2 py-1">${odds}</td>
        <td class="px-2 py-1">${pct}</td>
        <td class="px-2 py-1">${a.source}</td>
      `;
      tableBody.appendChild(tr);
    });

    // ενημέρωση ώρας τελευταίου update
    const dt = new Date().toLocaleTimeString("el-GR", { hour12: false });
    lastUpdateEl.textContent = dt;
  } catch (err) {
    console.error("SmartMoney fetch error:", err);
  }
}

// Auto-update loop κάθε 60 δευτερόλεπτα
fetchSmartMoney();
setInterval(fetchSmartMoney, 60000);

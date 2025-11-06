async function loadSmartMoney() {
  const tbody = document.getElementById("smartmoney-data");
  const status = document.getElementById("smartmoney-status");

  try {
    const res = await fetch("/api/smartmoney/alerts");
    const data = await res.json();

    if (data.alerts && data.alerts.length > 0) {
      tbody.innerHTML = data.alerts
        .map(a => `
          <tr>
            <td>${a.league}</td>
            <td>${a.match}</td>
            <td>${a.money_flow}%</td>
            <td>${a.odds}</td>
          </tr>
        `)
        .join("");
      status.textContent = "✅ Updated: " + new Date().toLocaleTimeString();
    } else {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-gray-400 py-2">No active alerts</td></tr>`;
      status.textContent = "⚠️ No data";
    }
  } catch (err) {
    console.error("[SmartMoney]", err);
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-red-400 py-2">Error loading data</td></tr>`;
    status.textContent = "❌ Error";
  }
}

setInterval(loadSmartMoney, 60000);
window.addEventListener("DOMContentLoaded", loadSmartMoney);

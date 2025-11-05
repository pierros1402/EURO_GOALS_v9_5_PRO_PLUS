// =============================================================
// SMARTMONEY AUTO MONITOR (EURO_GOALS v9.5.4 PRO+)
// =============================================================

console.log("[SmartMoney] Initializing live feed...");

async function fetchSmartMoneyData() {
  const statusDiv = document.getElementById("smartmoney-status");
  const tbody = document.getElementById("smartmoney-table-body");

  try {
    const response = await fetch("/api/smartmoney_feed");
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();

    if (!data || !data.matches || data.matches.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-3 text-gray-500">No data available</td></tr>`;
      statusDiv.innerHTML = "⚠️ Waiting for next update...";
      return;
    }

    tbody.innerHTML = data.matches
      .map(
        (m) => `
      <tr class="border-t hover:bg-gray-50">
        <td class="px-3 py-2">${m.league || '-'}</td>
        <td class="px-3 py-2">${m.home_team} vs ${m.away_team}</td>
        <td class="px-3 py-2">${m.bookmaker || '-'}</td>
        <td class="px-3 py-2">${m.market || '-'}</td>
        <td class="px-3 py-2">${m.home_price || '-'}</td>
        <td class="px-3 py-2">${m.away_price || '-'}</td>
        <td class="px-3 py-2">${m.last_update || '-'}</td>
      </tr>`
      )
      .join("");

    statusDiv.innerHTML = `✅ Updated: ${new Date().toLocaleTimeString()} (${data.matches.length} matches)`;
  } catch (err) {
    console.error("[SmartMoney] Error:", err);
    statusDiv.innerHTML = "❌ Failed to load data";
  }
}

// Auto-refresh every 60 seconds
fetchSmartMoneyData();
setInterval(fetchSmartMoneyData, 60000);

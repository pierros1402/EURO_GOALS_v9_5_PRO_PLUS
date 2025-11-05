(async function () {
  const elSM = document.getElementById("summary-smartmoney");
  const elGM = document.getElementById("summary-goalmatrix");
  const elHealth = document.getElementById("summary-health");
  const elTime = document.getElementById("summary-time");

  async function ping(url) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (!r.ok) throw new Error();
      return await r.json();
    } catch {
      return null;
    }
  }

  async function updateBar() {
    const health = await ping("/health");
    if (elHealth) {
      elHealth.textContent = health ? "❤️ Health: OK" : "❤️ Health: Failing";
      elHealth.style.color = health ? "#166534" : "#991b1b";
    }

    const sm = await ping("/api/smartmoney/summary");
    if (elSM) {
      if (!sm) {
        elSM.textContent = "💰 SmartMoney: Failing";
        elSM.style.color = "#991b1b";
      } else {
        elSM.textContent = `💰 SmartMoney: ${sm.status} (${sm.count ?? 0} alerts)`;
        elSM.style.color = sm.status === "OK" ? "#166534" : "#92400e";
      }
    }

    const gm = await ping("/api/goalmatrix/summary");
    if (elGM) {
      if (!gm) {
        elGM.textContent = "⚽ GoalMatrix: Failing";
        elGM.style.color = "#991b1b";
      } else {
        elGM.textContent = `⚽ GoalMatrix: ${gm.status} (${gm.total_matches ?? 0} matches)`;
        elGM.style.color = gm.status === "OK" ? "#166534" : "#92400e";
      }
    }

    elTime.textContent = "⏱️ Updated: " + new Date().toLocaleTimeString();
  }

  await updateBar();
  setInterval(updateBar, 30000);
})();

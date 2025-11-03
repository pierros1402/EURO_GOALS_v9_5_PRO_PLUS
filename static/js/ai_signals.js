// ============================================================
// EURO_GOALS – AI Analyzer frontend (Top Signals)
// ============================================================
export async function refreshAISignals() {
  try {
    const res = await fetch("/smartmoney/history?limit=100");
    const data = await res.json();
    const alerts = data.items || [];
    const aiRes = await fetch("/smartmoney/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ alerts, top: 10 }),
    });
    const ai = await aiRes.json();
    renderAISignals(ai.items || []);
  } catch (e) {
    console.error("AI signals error:", e);
  }
}

function renderAISignals(list) {
  const tbody = document.getElementById("ai-signals-body");
  if (!tbody) return;
  tbody.innerHTML = "";
  list.forEach(x => {
    const tr = document.createElement("tr");
    const pct = (x.change_pct * 100).toFixed(1) + "%";
    tr.innerHTML = `
      <td>${new Date(x.ts_utc).toLocaleTimeString("el-GR")}</td>
      <td>${x.match}</td>
      <td>${x.bookmaker}</td>
      <td>${x.market || "-"}</td>
      <td>${x.selection || "-"}</td>
      <td>${x.old} → ${x.new}</td>
      <td>${pct}</td>
      <td><b>${x.tier}</b> (${x.score})</td>
    `;
    tbody.appendChild(tr);
  });
}

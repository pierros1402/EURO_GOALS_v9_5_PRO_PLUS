// ============================================================
// EURO_GOALS – Dashboard mini charts (activity & avg drop)
// ============================================================
export async function refreshDashboardCharts() {
  try {
    const res = await fetch("/smartmoney/history?limit=200");
    const data = await res.json();
    const items = data.items || [];

    // Volume per minute
    const perMin = {};
    // Average abs drop per minute
    const avgDrop = {};
    const cntDrop = {};

    items.forEach(a => {
      const t = new Date(a.ts_utc);
      const key = t.toISOString().slice(11, 16); // HH:MM
      perMin[key] = (perMin[key] || 0) + 1;

      const cp = Math.abs(a.change_pct || 0);
      avgDrop[key] = (avgDrop[key] || 0) + cp;
      cntDrop[key] = (cntDrop[key] || 0) + 1;
    });

    const labels = Object.keys(perMin).slice(-12);
    const volData = labels.map(l => perMin[l] || 0);
    const dropData = labels.map(l => (cntDrop[l] ? (avgDrop[l] / cntDrop[l]) * 100 : 0));

    // volume chart
    renderBar("miniVolChart", labels, volData, "Alerts/min");
    // avg drop chart
    renderLine("miniDropChart", labels, dropData, "Avg Odds Drop (%)");
  } catch (e) {
    console.error("Dash chart error:", e);
  }
}

function renderBar(id, labels, data, label) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (ctx._chart) ctx._chart.destroy();
  ctx._chart = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets: [{ label, data }] },
    options: { scales: { x: { grid: { display: false } } } }
  });
}

function renderLine(id, labels, data, label) {
  const ctx = document.getElementById(id);
  if (!ctx) return;
  if (ctx._chart) ctx._chart.destroy();
  ctx._chart = new Chart(ctx, {
    type: "line",
    data: { labels, datasets: [{ label, data, fill: false }] },
    options: { scales: { x: { grid: { display: false } } } }
  });
}

(function () {
  const aggRoot = document.getElementById("aggregate-panel");

  async function getJSON(url) {
    try {
      const r = await fetch("/api/smartmoney_feed", { cache: "no-store" });
      return await r.json();
    } catch {
      return [];
    }
  }

  function renderCards(groups) {
    aggRoot.innerHTML = "";
    const providers = Object.keys(groups);
    if (!providers.length) {
      aggRoot.innerHTML = `<div class="agg-card"><div class="agg-title">No aggregates</div></div>`;
      return;
    }

    providers.forEach(src => {
      const items = groups[src];
      const count = items.length;
      const strong = items.filter(a => Math.abs(a.movement || 0) >= 0.2).length;
      const avgDiff = count ? (items.reduce((s, a) => s + (parseFloat(a.movement || 0)), 0) / count) : 0;

      const trendPill =
        avgDiff > 0.05 ? `<span class="pill up">↑ ${avgDiff.toFixed(2)}</span>` :
        avgDiff < -0.05 ? `<span class="pill down">↓ ${avgDiff.toFixed(2)}</span>` :
        `<span class="pill flat">± ${avgDiff.toFixed(2)}</span>`;

      const leagues = new Set(items.map(a => a.league).filter(Boolean));
      const lastTs = items.find(a => a.timestamp)?.timestamp || "-";

      const card = document.createElement("div");
      card.className = "agg-card";
      card.innerHTML = `
        <div class="agg-title">${src || "—"} ${trendPill}</div>
        <div class="agg-metric"><span class="label">Σύνολο alerts</span><span>${count}</span></div>
        <div class="agg-metric"><span class="label">Strong (|Δ| ≥ 0.20)</span><span>${strong}</span></div>
        <div class="agg-metric"><span class="label">Μοναδικές λίγκες</span><span>${leagues.size}</span></div>
        <div class="agg-metric"><span class="label">Τελευταία ενημέρωση</span><span>${lastTs}</span></div>
      `;
      aggRoot.appendChild(card);
    });
  }

  async function refreshAggregates() {
    const alerts = await getJSON("/api/smartmoney_feed");
    const groups = {};
    alerts.forEach(a => {
      const src = a.source || "—";
      (groups[src] ||= []).push(a);
    });
    renderCards(groups);
  }

  refreshAggregates();
  setInterval(refreshAggregates, 30000);
})();

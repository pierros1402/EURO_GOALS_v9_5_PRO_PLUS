// static/js/smartmoney_panel.js
(function () {
  const elBody = document.getElementById("smn-body");
  const elStatus = document.getElementById("smn-status-pill");
  const elProvOdds = document.getElementById("smn-provider-odds");
  const elProvDepth = document.getElementById("smn-provider-depth");
  const elLast = document.getElementById("smn-last-updated");
  const elBtn = document.getElementById("smn-refresh");
  const elSearch = document.getElementById("smn-search");

  async function fetchJSON(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(r.statusText);
    return await r.json();
  }

  function renderRows(items, q) {
    const ql = (q || "").trim().toLowerCase();
    const filtered = items.filter(x => {
      if (!ql) return true;
      const txt = `${x.home} ${x.away} ${x.league}`.toLowerCase();
      return txt.includes(ql);
    });

    if (filtered.length === 0) {
      elBody.innerHTML = `<tr><td class="p-2" colspan="8">No results</td></tr>`;
      return;
    }

    elBody.innerHTML = filtered.map(x => `
      <tr>
        <td class="p-2 whitespace-nowrap">${x.kickoff ?? "—"}</td>
        <td class="p-2">${x.home ?? "—"} – ${x.away ?? "—"}</td>
        <td class="p-2">${x.league ?? "—"}</td>
        <td class="p-2">${x.movement ?? 0}</td>
        <td class="p-2">${x.money_flow ?? 0}</td>
        <td class="p-2">${x.last5m ?? 0}</td>
        <td class="p-2 font-semibold">${x.score ?? 0}</td>
        <td class="p-2">
          <span class="px-2 py-1 rounded text-xs ${x.signal === "STRONG" ? "bg-red-200" : "bg-amber-200"}">
            ${x.signal}
          </span>
        </td>
      </tr>
    `).join("");
  }

  async function refreshAll() {
    try {
      const [summary, alerts] = await Promise.all([
        fetchJSON("/api/smartmoney/summary"),
        fetchJSON("/api/smartmoney/alerts"),
      ]);

      // Header info
      elStatus.textContent = summary.status ?? "—";
      elStatus.className = "px-2 py-1 rounded text-xs " + (
        summary.status === "OK" ? "bg-green-200" :
        summary.status === "Degraded" ? "bg-amber-200" : "bg-red-200"
      );

      elProvOdds.textContent = `Odds Provider: ${summary.provider_health?.odds ? "OK" : "Failing"}`;
      elProvDepth.textContent = `Depth Provider: ${summary.provider_health?.depth ? "OK" : "Failing"}`;
      elLast.textContent = "Last Updated: " + new Date((summary.last_updated_ts ?? 0) * 1000).toLocaleTimeString();

      // Table
      renderRows(alerts.items || [], elSearch.value);
    } catch (e) {
      elBody.innerHTML = `<tr><td class="p-2" colspan="8">Error loading data</td></tr>`;
      elStatus.textContent = "Failing";
      elStatus.className = "px-2 py-1 rounded text-xs bg-red-200";
      elProvOdds.textContent = "Odds Provider: —";
      elProvDepth.textContent = "Depth Provider: —";
      elLast.textContent = "Last Updated: —";
    }
  }

  elBtn?.addEventListener("click", refreshAll);
  elSearch?.addEventListener("input", () => {
    // re-filter existing rows without re-fetch
    const rows = Array.from(elBody.querySelectorAll("tr"));
    if (rows.length && rows[0].querySelectorAll("td").length === 8) {
      // cheap re-render: keep cached items? For now re-fetch to keep simple.
      refreshAll();
    } else {
      refreshAll();
    }
  });

  refreshAll();
  setInterval(refreshAll, 30000); // 30s
})();

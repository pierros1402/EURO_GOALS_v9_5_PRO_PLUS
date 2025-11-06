// GOALMATRIX PRO ENGINE v1.1
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("gm-form");
  const resBox = document.getElementById("gm-result");
  const elLambdaH = document.getElementById("lambda-home");
  const elLambdaA = document.getElementById("lambda-away");
  const elPOver = document.getElementById("p-over");
  const elPUnder = document.getElementById("p-under");
  const elTopScores = document.getElementById("top-scores");

  const tableBody = document.getElementById("gm-table-body");
  const totalEl = document.getElementById("gm-total");
  const avgEl = document.getElementById("gm-avg-lambda");
  const lastEl = document.getElementById("gm-last-update");
  const refreshEl = document.getElementById("gm-refresh-interval");
  const matchCountEl = document.getElementById("gm-match-count");

  async function postJSON(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    return await res.json();
  }

  async function getJSON(url) {
    const res = await fetch(url);
    return await res.json();
  }

  function pct(x) {
    return (x * 100).toFixed(1) + "%";
  }

  // --- Manual calculation
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const payload = {
      home_avg: parseFloat(fd.get("home_avg")),
      away_avg: parseFloat(fd.get("away_avg")),
      over_line: parseFloat(fd.get("over_line")),
    };
    const data = await postJSON("/api/goalmatrix/calc", payload);
    if (!data.enabled) {
      alert("GoalMatrix disabled");
      return;
    }
    resBox.classList.remove("hidden");
    elLambdaH.textContent = data.lambda_home.toFixed(2);
    elLambdaA.textContent = data.lambda_away.toFixed(2);
    elPOver.textContent = pct(data.p_over);
    elPUnder.textContent = pct(data.p_under);
    elTopScores.innerHTML = "";
    (data.top_scores || []).forEach(([s, p]) => {
      const li = document.createElement("li");
      li.textContent = `${s} — ${pct(p)}`;
      elTopScores.appendChild(li);
    });
  });

  // --- Live Feed
  async function refreshFeed() {
    const data = await getJSON("/api/goalmatrix/feed");
    if (!data.enabled) {
      tableBody.innerHTML = "<tr><td colspan='7' class='p-2 text-muted'>GoalMatrix disabled</td></tr>";
      return;
    }

    const items = data.items || [];
    matchCountEl.textContent = items.length;
    totalEl.textContent = items.length;
    refreshEl.textContent = data.refresh_sec || 20;
    lastEl.textContent = new Date().toLocaleTimeString();

    if (items.length > 0) {
      const avg = (
        items.reduce((a, m) => a + (m.lambda_home + m.lambda_away), 0) /
        items.length
      ).toFixed(2);
      avgEl.textContent = avg;
    } else {
      avgEl.textContent = "—";
    }

    tableBody.innerHTML = "";
    items.forEach((m) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="p-2 text-muted">${m.league}</td>
        <td class="p-2">${m.home} <b>vs</b> ${m.away}</td>
        <td class="p-2">${m.lambda_home.toFixed(2)}</td>
        <td class="p-2">${m.lambda_away.toFixed(2)}</td>
        <td class="p-2 text-green-400">${pct(m.p_over)}</td>
        <td class="p-2 text-red-400">${pct(m.p_under)}</td>
        <td class="p-2 text-xs">${m.top_scores
          .map(([s, p]) => `${s}(${pct(p)})`)
          .join(", ")}</td>`;
      tableBody.appendChild(tr);
    });

    setTimeout(refreshFeed, (data.refresh_sec || 20) * 1000);
  }

  refreshFeed();
});

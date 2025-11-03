// ================================================
// EURO_GOALS v9.4.2 – SmartMoney Auto-Notifier PRO (UI)
// ================================================
(function () {
  const evtUrl = "/smartmoney/events";
  let es = null;

  function ensureContainer() {
    let box = document.getElementById("smartmoney-alerts");
    if (!box) {
      box = document.createElement("div");
      box.id = "smartmoney-alerts";
      box.className = "fixed top-4 right-4 space-y-2 z-50";
      document.body.appendChild(box);
    }
    return box;
  }

  function popup(msg) {
    const box = ensureContainer();
    const el = document.createElement("div");
    el.className =
      "bg-white/90 shadow-lg rounded-xl px-4 py-3 text-sm border border-emerald-300";
    el.innerHTML = `
      <div class="font-semibold">💰 SmartMoney Alert</div>
      <div class="opacity-80">${msg}</div>
    `;
    box.appendChild(el);
    setTimeout(() => el.remove(), 6000);
  }

  async function appendHistory(item) {
    const wrap = document.getElementById("smartmoney-history-body");
    if (!wrap) return;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="px-2 py-1">${new Date(item.ts_utc).toLocaleString()}</td>
      <td class="px-2 py-1">${item.home || ""} vs ${item.away || ""}</td>
      <td class="px-2 py-1">${item.bookmaker || ""}</td>
      <td class="px-2 py-1">${item.market || ""}</td>
      <td class="px-2 py-1">${item.selection || ""}</td>
      <td class="px-2 py-1">${Number(item.old_price).toFixed(2)} → ${Number(item.new_price).toFixed(2)}</td>
      <td class="px-2 py-1">${(Number(item.change_pct) * 100).toFixed(1)}%</td>
      <td class="px-2 py-1">${item.source}</td>
    `;
    wrap.prepend(tr);
  }

  async function primeHistory() {
    try {
      const r = await fetch("/smartmoney/history?limit=20");
      const j = await r.json();
      (j.items || []).reverse().forEach(appendHistory);
    } catch (e) {
      // silent
    }
  }

  function connect() {
    if (es) es.close();
    es = new EventSource(evtUrl);
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.error) return;
        const msg = `${data.home || ""} vs ${data.away || ""} — ${data.bookmaker} ${data.market} ${data.selection}: `
          + `${Number(data.old_price).toFixed(2)} → ${Number(data.new_price).toFixed(2)} `
          + `(-${(Number(data.change_pct) * 100).toFixed(1)}%)`;
        popup(msg);
        appendHistory(data);
        // optional: play a short sound if enabled elsewhere
        // new Audio('/static/sounds/alert.mp3').play().catch(()=>{});
      } catch (e) {}
    };
    es.onerror = () => {
      setTimeout(connect, 4000);
    };
  }

  // boot
  primeHistory();
  connect();
})();

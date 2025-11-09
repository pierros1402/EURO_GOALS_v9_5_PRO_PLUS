const audio = document.getElementById("alertSound");
const tbody = document.getElementById("smartBody");
const ts = document.getElementById("timestamp");
const ticker = document.getElementById("ticker-container");
let lastState = {};

async function getJSON(url) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    return await r.json();
  } catch {
    return [];
  }
}

function pushTicker(msg, diff) {
  const el = document.createElement("div");
  el.className = "ticker-item";
  el.textContent = msg;
  el.style.color = diff > 0 ? "#00ff66" : "#ff4444";
  ticker.prepend(el);
  if (ticker.children.length > 6) ticker.removeChild(ticker.lastChild);
}

function notifyDesktop(match, source, diff) {
  if (Notification.permission === "granted") {
    new Notification(`SmartMoney Alert (${source})`, {
      body: `${match} (${diff > 0 ? "↑" : "↓"} ${diff.toFixed(2)})`,
      icon: "/static/icons/eurogoals_512.png"
    });
  }
}

async function refreshFeed() {
  const alerts = await getJSON("/api/smartmoney_feed");
  tbody.innerHTML = "";

  if (!alerts.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="p-2">— No active alerts —</td></tr>`;
    ts.innerText = "Τελευταία ενημέρωση: " + new Date().toLocaleTimeString("el-GR");
    return;
  }

  alerts.forEach(a => {
    const diff = parseFloat(a.movement || 0);
    const diffClass = diff >= 0.2 ? "movement-up" : diff <= -0.2 ? "movement-down" : "";
    const key = a.match_id || a.match;
    const changed = lastState[key] !== diff;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${a.source || "—"}</td>
      <td>${a.league || "—"}</td>
      <td>${a.match || "—"}</td>
      <td>${a.open?.toFixed ? a.open.toFixed(2) : a.open || "-"}</td>
      <td>${a.current?.toFixed ? a.current.toFixed(2) : a.current || "-"}</td>
      <td class="${diffClass}">${diff.toFixed(2)}</td>
      <td>${a.signal || ""}</td>
    `;

    if (changed && Math.abs(diff) >= 0.2) {
      tr.classList.add("blink");
      audio.currentTime = 0;
      audio.play().catch(()=>{});
      pushTicker(`${a.source} | ${a.match} ${diff > 0 ? "↑" : "↓"} ${diff.toFixed(2)}`, diff);
      notifyDesktop(a.match, a.source, diff);
    }

    tbody.appendChild(tr);
    lastState[key] = diff;
  });

  ts.innerText = "Τελευταία ενημέρωση: " + new Date().toLocaleTimeString("el-GR");
}

if (Notification.permission !== "granted") {
  Notification.requestPermission();
}

refreshFeed();
setInterval(refreshFeed, 30000);

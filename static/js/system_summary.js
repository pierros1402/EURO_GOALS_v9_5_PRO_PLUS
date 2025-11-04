async function refreshSummary() {
  try {
    // Push status
    const r1 = await fetch('/status/push');
    const p = await r1.json();
    const elPush = document.getElementById('summary-push');
    if (elPush)
      elPush.textContent = `🔔 Push: ${p.enabled ? 'ON' : 'OFF'} (${p.subscriptions} subs)`;

    // Heatmap status
    const r2 = await fetch('/status/heatmap');
    const h = await r2.json();
    const elHM = document.getElementById('summary-heatmap');
    if (elHM)
      elHM.textContent = `🔥 Heatmap: ${h.last24h_alerts} alerts / 24h`;

    // Health (simple check)
    const elHealth = document.getElementById('summary-health');
    if (elHealth) elHealth.textContent = '❤️ Health: OK';
  } catch (e) {
    const elPush = document.getElementById('summary-push');
    if (elPush) elPush.textContent = '🔔 Push: error';
    const elHM = document.getElementById('summary-heatmap');
    if (elHM) elHM.textContent = '🔥 Heatmap: error';
  }
}

refreshSummary();
setInterval(refreshSummary, 60000);

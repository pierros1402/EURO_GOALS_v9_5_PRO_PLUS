// ============================================================
// EURO_GOALS v9.5.0 PRO+
// System Status LED Monitor
// ============================================================

async function updateSystemStatus() {
  try {
    const res = await fetch('/health', { cache: 'no-store' });
    const data = await res.json();

    const comps = data.components || {};
    updateLed('render', comps.render);
    updateLed('db', comps.db);
    updateLed('flashscore', comps.flashscore);
    updateLed('sofascore', comps.sofascore);
    updateLed('asianconnect', comps.asianconnect);
    updateLed('network', true);

    document.getElementById('summaryCPU').textContent = `CPU: ${data.cpu || '—'}%`;
    document.getElementById('summaryRAM').textContent = `RAM: ${data.ram || '—'}%`;
    document.getElementById('summaryDISK').textContent = `Disk: ${data.disk || '—'}%`;
    document.getElementById('summaryLast').textContent = `Last: ${new Date().toLocaleTimeString()}`;
    document.getElementById('summaryNext').textContent = `Next: ${new Date(Date.now() + 30000).toLocaleTimeString()}`;

  } catch (err) {
    console.warn('[EURO_GOALS] Health check failed:', err);
    document.querySelectorAll('.dot').forEach(el => {
      el.classList.remove('ok', 'bad');
      el.classList.add('bad');
    });
  }
}

function updateLed(id, isOn) {
  const led = document.querySelector(`.dot[data-id="${id}"]`);
  if (!led) return;
  led.classList.remove('ok', 'bad');
  led.classList.add(isOn ? 'ok' : 'bad');
}

// Initial + auto-refresh
updateSystemStatus();
setInterval(updateSystemStatus, 30000);

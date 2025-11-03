// ==============================================
// EURO_GOALS v9.4.1 – System Summary JS
// Δείχνει κατάσταση ειδοποιήσεων (🔔/🔕) και κάνει toggle
// ==============================================
(function(){
  async function fetchSettings(){
    try{ const r = await fetch('/api/settings/get'); const j = await r.json(); return j.settings || {}; }
    catch(e){ return {}; }
  }
  async function setSettings(payload){
    try{ await fetch('/api/settings/update', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)}); }
    catch(e){}
  }

  async function init(){
    const el = document.getElementById('summary-notif');
    if(!el) return;
    const s = await fetchSettings();
    const apply = (on)=>{ el.textContent = (on ? '🔔 Notif: ON' : '🔕 Notif: OFF'); el.dataset.on = on ? '1':'0'; };
    apply(!!s.notifications_enabled);

    el.addEventListener('click', async ()=>{
      const on = el.dataset.on !== '1';
      apply(on);
      await setSettings({notifications_enabled:on});
      if (window.EUROGOALS && EUROGOALS.Alerts){
        EUROGOALS.Alerts.setNotificationsEnabled(on);
        if (on) EUROGOALS.Alerts.requestPermission();
      }
    });
  }

  window.EUROGOALS = window.EUROGOALS || {};
  window.EUROGOALS.Summary = { init };
})();

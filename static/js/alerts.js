// ==============================================
// EURO_GOALS v9.4.1 – Frontend Alerts Handler
// - Polls /api/alerts/latest
// - Browser Notifications (server-sync)
// - Plays local sounds per alert type
// - Dark toast UI
// ==============================================
(function(){
  const sounds = {
    'GOAL_ALERT': '/static/sounds/goal_alert.mp3',
    'SMART_MONEY_ALERT': '/static/sounds/smartmoney_alert.mp3',
    'HEALTH_ALERT': '/static/sounds/system_alert.mp3',
    'SYSTEM_EVENT': '/static/sounds/system_alert.mp3'
  };
  let pollTimer = null;
  let lastId = parseInt(localStorage.getItem('eu_last_alert_id') || '0', 10) || 0;
  let notifEnabled = false;

  async function loadServerPrefs(){
    try{ const r = await fetch('/api/settings/get'); const j = await r.json(); notifEnabled = !!(j.ok && j.settings && j.settings.notifications_enabled); }
    catch(e){ notifEnabled = false; }
  }

  function setNotificationsEnabled(on){ notifEnabled = !!on; }
  async function requestPermission(){
    if (!('Notification' in window)) return;
    if (Notification.permission === 'default') await Notification.requestPermission();
  }

  function playSound(type){
    try{ new Audio(sounds[type] || sounds.SYSTEM_EVENT).play().catch(()=>{}); }catch(e){}
  }
  function typeToTitle(t){ return t==='GOAL_ALERT'?'⚽ Goal Alert':t==='SMART_MONEY_ALERT'?'💰 Smart Money':t==='HEALTH_ALERT'?'❤️ Health Alert':t==='SYSTEM_EVENT'?'🌐 System Event':'🔔 Alert'; }

  function showToast(title, message){
    let box = document.getElementById('eg-toast-box');
    if(!box){ box = document.createElement('div'); box.id='eg-toast-box'; box.className='eg-toast-box'; document.body.appendChild(box); }
    const el = document.createElement('div');
    el.className = 'eg-toast';
    el.innerHTML = `<strong>${esc(title)}</strong><div>${esc(message)}</div>`;
    box.appendChild(el);
    requestAnimationFrame(()=> el.classList.add('show'));
    setTimeout(()=>{ el.classList.remove('show'); el.addEventListener('transitionend', ()=> el.remove(), {once:true}); }, 5000);
  }
  function showBrowserNotification(type, message){
    if (!notifEnabled) return;
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;
    const n = new Notification(typeToTitle(type), { body: message });
    setTimeout(()=>n.close(), 6000);
  }
  function esc(s){ return String(s??'').replace(/[&<>"']/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }

  async function pollOnce(){
    try{
      const url = lastId ? `/api/alerts/latest?since_id=${lastId}` : '/api/alerts/latest';
      const res = await fetch(url); const data = await res.json(); const item = data.item;
      if (item && item.id){
        lastId = Math.max(lastId, item.id);
        localStorage.setItem('eu_last_alert_id', String(lastId));

        playSound(item.type);
        showToast(typeToTitle(item.type), item.message);
        if (notifEnabled){ await requestPermission(); showBrowserNotification(item.type, item.message); }

        const tbody = document.querySelector('#alert-tbody');
        if (tbody){
          const created = item.created_at ? new Date(item.created_at).toISOString().replace('T',' ').slice(0,19) : '';
          const meta = item.meta ? JSON.stringify(item.meta) : '';
          const tr = document.createElement('tr');
          tr.setAttribute('data-id', item.id);
          tr.innerHTML = `
            <td><input type="checkbox" class="row-check"/></td>
            <td>${created}</td>
            <td><span class="tag ${item.type}">${item.type}</span></td>
            <td>${esc(item.message)}</td>
            <td><pre class="meta">${esc(meta)}</pre></td>
            <td>${item.is_read ? 'Read' : 'Unread'}</td>`;
          const first = tbody.querySelector('tr'); if (first && first.textContent.includes('Loading')) tbody.innerHTML='';
          tbody.insertBefore(tr, tbody.firstChild);
        }
      }
    }catch(e){}
  }

  async function startPolling(){
    await loadServerPrefs();
    stopPolling();
    await pollOnce();
    pollTimer = setInterval(pollOnce, 10000);
  }
  function stopPolling(){ if (pollTimer) clearInterval(pollTimer); pollTimer=null; }

  window.EUROGOALS = window.EUROGOALS || {};
  window.EUROGOALS.Alerts = { startPolling, stopPolling, requestPermission, setNotificationsEnabled };
})();

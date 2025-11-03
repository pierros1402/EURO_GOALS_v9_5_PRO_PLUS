// ==============================================
// EURO_GOALS v9.4.0 – Frontend Alerts Handler
// - Polls /api/alerts/latest
// - Browser Notifications (localStorage toggle)
// - Plays local sounds per alert type
// - Floating toast
// ==============================================

(function(){
  const LS_LAST_ID = 'eu_last_alert_id';
  const LS_NOTIF = 'eu_notifications_enabled';

  const sounds = {
    'GOAL_ALERT': '/static/sounds/goal_alert.mp3',
    'SMART_MONEY_ALERT': '/static/sounds/smartmoney_alert.mp3',
    'HEALTH_ALERT': '/static/sounds/system_alert.mp3',
    'SYSTEM_EVENT': '/static/sounds/system_alert.mp3'
  };

  let pollTimer = null;
  let lastId = parseInt(localStorage.getItem(LS_LAST_ID) || '0', 10) || 0;

  async function requestPermission(){
    try{
      if (!('Notification' in window)) return;
      if (Notification.permission === 'default') {
        await Notification.requestPermission();
      }
    }catch(e){}
  }

  function notificationsEnabled(){
    return localStorage.getItem(LS_NOTIF) === '1';
  }

  function playSound(type){
    const src = sounds[type] || sounds['SYSTEM_EVENT'];
    try{
      const a = new Audio(src);
      a.play().catch(()=>{});
    }catch(e){}
  }

  function showToast(title, message){
    let box = document.getElementById('eg-toast-box');
    if(!box){
      box = document.createElement('div');
      box.id = 'eg-toast-box';
      box.className = 'eg-toast-box';
      document.body.appendChild(box);
    }
    const el = document.createElement('div');
    el.className = 'eg-toast';
    el.innerHTML = `<strong>${escapeHtml(title)}</strong><div>${escapeHtml(message)}</div>`;
    box.appendChild(el);
    setTimeout(()=>{ el.classList.add('show'); }, 10);
    setTimeout(()=>{ el.classList.remove('show'); el.addEventListener('transitionend', ()=> el.remove(), {once:true}); }, 5000);
  }

  function showBrowserNotification(type, message){
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') return;
    const title = typeToTitle(type);
    const n = new Notification(title, {
      body: message,
      icon: typeToIcon(type)
    });
    setTimeout(()=>n.close(), 6000);
  }

  function typeToTitle(t){
    switch (t){
      case 'GOAL_ALERT': return '⚽ Goal Alert';
      case 'SMART_MONEY_ALERT': return '💰 Smart Money';
      case 'HEALTH_ALERT': return '❤️ Health Alert';
      case 'SYSTEM_EVENT': return '🌐 System Event';
      default: return '🔔 Alert';
    }
  }
  function typeToIcon(t){
    // If you want custom icons, place PNGs under /static and map here.
    return '/static/favicon.ico';
  }

  function escapeHtml(s){
    return String(s ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  }

  async function pollOnce(){
    try{
      const url = lastId ? `/api/alerts/latest?since_id=${lastId}` : '/api/alerts/latest';
      const res = await fetch(url);
      const data = await res.json();
      const item = data.item;
      if (item && item.id){
        lastId = Math.max(lastId, item.id);
        localStorage.setItem(LS_LAST_ID, String(lastId));

        // Notify
        playSound(item.type);
        showToast(typeToTitle(item.type), item.message);
        if (notificationsEnabled()){
          await requestPermission();
          showBrowserNotification(item.type, item.message);
        }

        // If Alert Center is open, refresh its table
        const tbody = document.querySelector('#alert-tbody');
        if (tbody){
          // Soft refresh: prepend row
          const created = item.created_at ? new Date(item.created_at).toISOString().replace('T',' ').slice(0,19) : '';
          const meta = item.meta ? JSON.stringify(item.meta) : '';
          const tr = document.createElement('tr');
          tr.setAttribute('data-id', item.id);
          tr.innerHTML = `
            <td><input type="checkbox" class="row-check"/></td>
            <td>${created}</td>
            <td><span class="tag ${item.type}">${item.type}</span></td>
            <td>${escapeHtml(item.message)}</td>
            <td><pre style="white-space:pre-wrap;margin:0">${escapeHtml(meta)}</pre></td>
            <td>${item.is_read ? 'Read' : 'Unread'}</td>
          `;
          const firstRow = tbody.querySelector('tr');
          if (firstRow && firstRow.textContent.includes('Loading')) tbody.innerHTML = '';
          tbody.insertBefore(tr, tbody.firstChild);
        }
      }
    }catch(e){
      // silent
    }
  }

  function startPolling(intervalMs = 10000){
    stopPolling();
    pollOnce();
    pollTimer = setInterval(pollOnce, intervalMs);
  }
  function stopPolling(){
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = null;
  }

  // Expose namespace
  window.EUROGOALS = window.EUROGOALS || {};
  window.EUROGOALS.Alerts = {
    startPolling,
    stopPolling,
    requestPermission
  };

  // Auto-wire notification toggle if exists
  document.addEventListener('DOMContentLoaded', ()=>{
    const toggle = document.getElementById('notif-toggle');
    if (toggle){
      toggle.checked = localStorage.getItem(LS_NOTIF) === '1';
      toggle.addEventListener('change', () => {
        localStorage.setItem(LS_NOTIF, toggle.checked ? '1' : '0');
        if (toggle.checked) requestPermission();
      });
    }
  });
})();

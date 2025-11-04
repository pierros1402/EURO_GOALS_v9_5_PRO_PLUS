// Requires: window.VAPID_PUBLIC, window.PUSH_ENABLED

async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return null;
  try {
    const reg = await navigator.serviceWorker.register('/service-worker.js');
    return reg;
  } catch (e) {
    console.error('SW register failed', e);
    return null;
  }
}

async function ensureSubscription(reg) {
  if (!window.PUSH_ENABLED) return null;
  if (!('PushManager' in window)) return null;

  let sub = await reg.pushManager.getSubscription();
  if (!sub) {
    const vapidKey = window.VAPID_PUBLIC;
    if (!vapidKey) {
      console.warn('No VAPID public key');
      return null;
    }
    sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey)
    });
  }
  await fetch('/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sub)
  });
  return sub;
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function initPush() {
  const btn = document.getElementById('btn-push');
  if (btn) {
    btn.addEventListener('click', async () => {
      const reg = await registerServiceWorker();
      if (!reg) {
        alert('Service Worker δεν υποστηρίζεται');
        return;
      }
      const sub = await ensureSubscription(reg);
      if (sub) {
        btn.textContent = '🔔 Push: Ενεργό';
        btn.disabled = true;
      } else {
        alert('Αποτυχία εγγραφής push');
      }
    });
  }

  if (window.PUSH_ENABLED) {
    const reg = await registerServiceWorker();
    if (reg) await ensureSubscription(reg);
  }
}

initPush();

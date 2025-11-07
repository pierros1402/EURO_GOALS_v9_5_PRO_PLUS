// =====================================================
// EURO_GOALS v9.5.0 PRO+
// PWA Custom Install Banner
// =====================================================

let deferredPrompt = null;
let installShown = false;

// =====================================================
// 📡 Capture beforeinstallprompt event
// =====================================================
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  console.log('[PWA] beforeinstallprompt captured');
  if (!installShown) {
    showInstallBanner();
  }
});

// =====================================================
// 🎨 Banner display
// =====================================================
function showInstallBanner() {
  installShown = true;

  const banner = document.createElement('div');
  banner.id = 'installBanner';
  banner.innerHTML = `
    <div style="
      position:fixed;bottom:15px;left:50%;transform:translateX(-50%);
      background:#121826;border:1px solid #1e88e5;color:#fff;
      border-radius:12px;padding:16px 20px;box-shadow:0 2px 12px rgba(0,0,0,.3);
      z-index:9999;font-family:sans-serif;display:flex;align-items:center;gap:14px;
      animation:fadeIn 0.4s ease;">
      <img src="/static/icons/icon-192.png" alt="logo" width="32" height="32" style="border-radius:8px;">
      <div style="flex:1;">
        <strong>Install EURO_GOALS PRO+</strong><br>
        <small style="color:#ccc;">Add to your home screen for full experience</small>
      </div>
      <button id="installConfirmBtn" style="
        background:#1e88e5;border:none;color:#fff;padding:8px 14px;
        border-radius:8px;cursor:pointer;font-size:13px;">Install</button>
      <button id="installCancelBtn" style="
        background:none;border:none;color:#aaa;padding:8px 10px;
        cursor:pointer;font-size:16px;">✕</button>
    </div>
    <style>
      @keyframes fadeIn { from { opacity:0; transform:translate(-50%,20px); }
                          to { opacity:1; transform:translate(-50%,0); } }
    </style>
  `;
  document.body.appendChild(banner);

  document.getElementById('installCancelBtn').addEventListener('click', () => {
    banner.remove();
  });

  document.getElementById('installConfirmBtn').addEventListener('click', async () => {
    banner.remove();
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log('[PWA] User install choice:', outcome);
      deferredPrompt = null;
    }
  });
}

// =====================================================
// 📱 Detect standalone mode
// =====================================================
if (window.matchMedia('(display-mode: standalone)').matches) {
  console.log('[PWA] Running in standalone mode');
}

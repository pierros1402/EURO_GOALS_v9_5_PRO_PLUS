// =====================================================
// EURO_GOALS v9.5.0 PRO+
// UI Controls — Buttons, Refresh, Menu, Sound & Tooltip
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
  const refreshBtn = document.getElementById("refreshNowBtn");
  const menuBtn = document.getElementById("menuBtn");

  // Load sounds
  const clickSound = new Audio("/static/sounds/refresh_click.mp3");

  // Refresh animation + sound
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      playClickSound(clickSound);
      startRefreshAnimation(refreshBtn);
      manualRefreshAction();
    });
  }

  // Menu drawer toggle
  if (menuBtn) {
    menuBtn.addEventListener("click", () => {
      const drawer = document.querySelector(".drawer");
      if (drawer) drawer.classList.toggle("open");
    });
  }
});

// =====================================================
// 🎵 Click Sound
// =====================================================
function playClickSound(audio) {
  try {
    audio.currentTime = 0;
    audio.play().catch(() => {});
  } catch (err) {
    console.warn("[EURO_GOALS] Click sound error:", err);
  }
}

// =====================================================
// 🔄 Refresh Animation with Tooltip
// =====================================================
function startRefreshAnimation(btn) {
  btn.disabled = true;
  const originalHTML = btn.innerHTML;

  // Tooltip
  const tooltip = document.createElement("div");
  tooltip.textContent = "Refreshing data…";
  tooltip.style.cssText = `
    position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
    background:#1e88e5;color:#fff;padding:8px 14px;border-radius:10px;
    font-family:sans-serif;font-size:13px;
    box-shadow:0 4px 16px rgba(0,0,0,.3);
    z-index:9999;opacity:0;transition:opacity .3s ease;
  `;
  document.body.appendChild(tooltip);
  setTimeout(() => tooltip.style.opacity = 1, 50);

  // Spinner animation
  btn.innerHTML = `<span class="spinner"></span>`;
  setTimeout(() => {
    btn.innerHTML = originalHTML;
    btn.disabled = false;
    tooltip.style.opacity = 0;
    setTimeout(() => tooltip.remove(), 400);
  }, 1200);
}

// =====================================================
// ⚙️ Manual Refresh Action
// =====================================================
function manualRefreshAction() {
  console.log("[EURO_GOALS] Manual refresh triggered.");
  try {
    if (typeof fetchAlertsFeed === "function") fetchAlertsFeed();
    if (typeof checkServerHealth === "function") checkServerHealth();
  } catch (err) {
    console.warn("[EURO_GOALS] Refresh error:", err);
  }
}

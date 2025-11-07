// =====================================================
// EURO_GOALS v9.5.0 PRO+
// Adaptive Dark/Light Mode + Manual Toggle + Banner
// =====================================================

let themeToggleBtn;

// -----------------------------------------------------
// 🔧 Apply Theme
// -----------------------------------------------------
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("eg_theme", theme);
  console.log(`[EURO_GOALS] Theme applied: ${theme}`);
  showThemeBanner(theme);
}

// -----------------------------------------------------
// 🧠 Detect System Preference
// -----------------------------------------------------
function detectSystemTheme() {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return "light";
  }
  return "dark";
}

// -----------------------------------------------------
// 🎛 Initialize Theme
// -----------------------------------------------------
function initTheme() {
  const saved = localStorage.getItem("eg_theme");
  const initial = saved || detectSystemTheme();
  applyTheme(initial);
  updateToggleIcon(initial);
}

// -----------------------------------------------------
// 🌓 Toggle Handler
// -----------------------------------------------------
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  updateToggleIcon(next);
}

// -----------------------------------------------------
// 🧩 Update Button Icon
// -----------------------------------------------------
function updateToggleIcon(theme) {
  if (!themeToggleBtn) return;
  themeToggleBtn.innerHTML = theme === "dark" ? "☀️" : "🌙";
  themeToggleBtn.title = theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode";
}

// -----------------------------------------------------
// 🌈 Show Banner Animation
// -----------------------------------------------------
function showThemeBanner(theme) {
  const existing = document.getElementById("themeBanner");
  if (existing) existing.remove();

  const banner = document.createElement("div");
  banner.id = "themeBanner";
  banner.innerHTML = `
    <div style="
      position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
      background:${theme === "dark" ? "#263146" : "#1e88e5"};
      color:#fff;padding:10px 20px;border-radius:12px;
      font-family:sans-serif;font-size:14px;
      box-shadow:0 4px 16px rgba(0,0,0,.3);
      z-index:9999;opacity:0;transition:opacity .3s ease;
      display:flex;align-items:center;gap:8px;">
      ${theme === "dark" ? "🌙" : "🌞"} 
      ${theme === "dark" ? "Dark Mode Activated" : "Light Mode Activated"}
    </div>
  `;
  document.body.appendChild(banner);
  setTimeout(() => banner.firstElementChild.style.opacity = 1, 50);
  setTimeout(() => {
    banner.firstElementChild.style.opacity = 0;
    setTimeout(() => banner.remove(), 400);
  }, 1500);
}

// -----------------------------------------------------
// 🚀 Init on Load
// -----------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  themeToggleBtn = document.getElementById("themeToggleBtn");
  if (themeToggleBtn) themeToggleBtn.addEventListener("click", toggleTheme);
  initTheme();
});

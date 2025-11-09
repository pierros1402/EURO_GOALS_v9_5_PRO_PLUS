// ============================================================
// EURO_GOALS PRO+ v9.5.4 – Adaptive Theme Controller
// Auto Sync across Tabs + System Preference + Manual Toggle
// ============================================================

(function () {
  const STORAGE_KEY = "eg_theme";
  const body = document.body;
  const btn = document.getElementById("themeToggle");

  // --- Detect current or system preference
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const savedTheme = localStorage.getItem(STORAGE_KEY);
  const currentTheme = savedTheme || (prefersDark ? "dark" : "light");

  body.dataset.theme = currentTheme;
  localStorage.setItem(STORAGE_KEY, currentTheme);

  // --- Update button label/icon
  function updateButton(theme) {
    if (!btn) return;
    btn.textContent = theme === "dark" ? "☀️ Φωτεινό" : "🌙 Σκοτεινό";
  }
  updateButton(currentTheme);

  // --- Manual toggle
  if (btn) {
    btn.addEventListener("click", () => {
      const newTheme = body.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(newTheme, true);
    });
  }

  // --- Apply theme + broadcast to other tabs
  function applyTheme(theme, broadcast = false) {
    body.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    updateButton(theme);
    if (broadcast) {
      try {
        localStorage.setItem("eg_theme_sync", JSON.stringify({ theme, time: Date.now() }));
      } catch {}
    }
  }

  // --- Sync across tabs (listen for localStorage events)
  window.addEventListener("storage", (e) => {
    if (e.key === "eg_theme_sync" && e.newValue) {
      try {
        const data = JSON.parse(e.newValue);
        if (data && data.theme && data.theme !== body.dataset.theme) {
          applyTheme(data.theme, false);
        }
      } catch {}
    }
  });

  // --- React to system theme changes
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    const systemTheme = e.matches ? "dark" : "light";
    const userPref = localStorage.getItem(STORAGE_KEY);
    if (!userPref) {
      applyTheme(systemTheme, true);
    }
  });
})();

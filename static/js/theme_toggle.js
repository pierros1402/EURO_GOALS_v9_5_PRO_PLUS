// ============================================================
// EURO_GOALS v9.5.5 PRO+ — Adaptive Theme Controller (Unified)
// Auto sync μεταξύ tabs + System Preference + Manual Toggle
// ============================================================

(function () {
  const STORAGE_KEY = "eg_theme";
  const body = document.body;
  const btn = document.getElementById("themeToggle");

  // --- Ανάγνωση αποθηκευμένου ή συστήματος
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const savedTheme = localStorage.getItem(STORAGE_KEY);
  const currentTheme = savedTheme || (prefersDark ? "dark" : "light");

  applyTheme(currentTheme);

  // --- Ενημέρωση κουμπιού
  function updateButton(theme) {
    if (!btn) return;
    btn.textContent = theme === "dark" ? "☀️ Φωτεινό" : "🌙 Σκοτεινό";
  }

  // --- Εφαρμογή θέματος
  function applyTheme(theme, broadcast = false) {
    body.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    updateButton(theme);

    // Εφαρμόζουμε και σε όλη τη σελίδα (header, panels, sections)
    document.querySelectorAll("*").forEach((el) => {
      el.classList.remove("dark-mode", "light-mode");
      el.classList.add(theme === "dark" ? "dark-mode" : "light-mode");
    });

    if (broadcast) {
      try {
        localStorage.setItem(
          "eg_theme_sync",
          JSON.stringify({ theme, time: Date.now() })
        );
      } catch {}
    }
  }

  // --- Manual toggle
  if (btn) {
    btn.addEventListener("click", () => {
      const newTheme = body.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(newTheme, true);
    });
  }

  // --- Sync across tabs
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

  // --- React to system preference change
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    const systemTheme = e.matches ? "dark" : "light";
    const userPref = localStorage.getItem(STORAGE_KEY);
    if (!userPref) {
      applyTheme(systemTheme, true);
    }
  });
})();

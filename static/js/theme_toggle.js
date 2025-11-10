// ============================================================
// EURO_GOALS v9.6.1 PRO+ — Adaptive Theme Controller (MOBILE+)
// Auto Sync + Fade Transition + System Preference + Manual Toggle
// ============================================================

(function () {
  const STORAGE_KEY = "eg_theme";
  const SYNC_KEY = "eg_theme_sync";
  const body = document.body;
  const btn = document.getElementById("themeToggle");

  // --- Fade helper για smooth αλλαγή
  const fadeTransition = () => {
    body.classList.add("fade-exit-active");
    setTimeout(() => {
      body.classList.remove("fade-exit-active");
    }, 400);
  };

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
    fadeTransition();
    body.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEY, theme);
    updateButton(theme);

    // Εφαρμογή κλάσεων (όπως στο CSS unified_theme)
    document.querySelectorAll("*").forEach((el) => {
      el.classList.remove("dark-mode", "light-mode");
      el.classList.add(theme === "dark" ? "dark-mode" : "light-mode");
    });

    // Broadcast sync
    if (broadcast) {
      try {
        localStorage.setItem(SYNC_KEY, JSON.stringify({ theme, time: Date.now() }));
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
    if (e.key === SYNC_KEY && e.newValue) {
      try {
        const data = JSON.parse(e.newValue);
        if (data && data.theme && data.theme !== body.dataset.theme) {
          applyTheme(data.theme, false);
        }
      } catch {}
    }
  });

  // --- React to system preference change
  const systemMedia = window.matchMedia("(prefers-color-scheme: dark)");
  systemMedia.addEventListener("change", (e) => {
    const systemTheme = e.matches ? "dark" : "light";
    const userPref = localStorage.getItem(STORAGE_KEY);
    if (!userPref) {
      applyTheme(systemTheme, true);
    }
  });
})();

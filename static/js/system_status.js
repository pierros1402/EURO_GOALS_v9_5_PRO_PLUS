// ============================================================
// EURO_GOALS PRO+ Unified v9.5.x
// System Status Init — Theme + Service Worker + Update Banner
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const html = document.documentElement;
  const body = document.body;

  /* ------------------------------
     1️⃣ THEME MANAGEMENT
  ------------------------------ */
  const savedTheme = localStorage.getItem("eg_theme");

  // Apply saved theme or system preference
  if (savedTheme) {
    html.setAttribute("data-theme", savedTheme);
    body.dataset.theme = savedTheme;
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const defaultTheme = prefersDark ? "dark" : "light";
    html.setAttribute("data-theme", defaultTheme);
    body.dataset.theme = defaultTheme;
  }

  // Detect if there’s already a header toggle button (in index.html)
  let toggleBtn = document.getElementById("themeToggle");

  if (!toggleBtn) {
    // If not, create floating button (legacy compatibility)
    toggleBtn = document.createElement("button");
    toggleBtn.className = "theme-toggle-btn";
    toggleBtn.title = "Toggle Dark/Light mode";
    toggleBtn.innerHTML = getIcon(html.getAttribute("data-theme"));
    document.body.appendChild(toggleBtn);
  } else {
    // Sync icon if it exists in header
    toggleBtn.textContent = html.getAttribute("data-theme") === "dark" ? "☀️" : "🌙";
  }

  toggleBtn.addEventListener("click", () => {
    const current = html.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    body.dataset.theme = next;
    localStorage.setItem("eg_theme", next);
    toggleBtn.innerHTML = getIcon(next);
  });

  function getIcon(mode) {
    return mode === "dark" ? "☀️" : "🌙";
  }

  /* ------------------------------
     2️⃣ SERVICE WORKER REGISTRATION
  ------------------------------ */
  if ("serviceWorker" in navigator) {
    // Register as soon as DOM ready
    navigator.serviceWorker
      .register("/static/service-worker.js")
      .then((reg) => {
        console.log("[EURO_GOALS PRO+] Service Worker registered:", reg.scope);

        // Update detection
        reg.onupdatefound = () => {
          const newWorker = reg.installing;
          newWorker.onstatechange = () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              console.log("[EURO_GOALS PRO+] Νέα έκδοση διαθέσιμη!");
              showUpdateBanner();
            }
          };
        };
      })
      .catch((err) => console.error("[EURO_GOALS PRO+] Service Worker error:", err));
  }

  /* ------------------------------
     3️⃣ UPDATE BANNER
  ------------------------------ */
  function showUpdateBanner() {
    const banner = document.createElement("div");
    banner.textContent = "Νέα έκδοση διαθέσιμη — Επαναφόρτωσε 🔄";
    Object.assign(banner.style, {
      position: "fixed",
      bottom: "12px",
      right: "12px",
      background: "#1162ff",
      color: "#fff",
      padding: "10px 16px",
      borderRadius: "12px",
      fontSize: "0.9rem",
      zIndex: "9999",
      cursor: "pointer",
      boxShadow: "0 2px 10px rgba(0,0,0,.4)",
      transition: "opacity .3s ease-in-out"
    });
    banner.onclick = () => window.location.reload();
    document.body.appendChild(banner);
    setTimeout(() => (banner.style.opacity = "0"), 15000);
  }

  console.log("[EURO_GOALS PRO+] System initialized (Theme + SW Ready)");
});

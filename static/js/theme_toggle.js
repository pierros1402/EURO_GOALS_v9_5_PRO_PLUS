// ============================================================
// EURO_GOALS v9.5.0 PRO+
// Adaptive Dark/Light Theme + Manual Toggle
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  const html = document.documentElement;
  const savedTheme = localStorage.getItem("eg_theme");

  // Apply saved or system preference
  if (savedTheme) {
    html.setAttribute("data-theme", savedTheme);
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    html.setAttribute("data-theme", prefersDark ? "dark" : "light");
  }

  // Create floating toggle button
  const btn = document.createElement("button");
  btn.className = "theme-toggle-btn";
  btn.title = "Toggle Dark/Light mode";
  btn.innerHTML = getIcon(html.getAttribute("data-theme"));
  document.body.appendChild(btn);

  btn.addEventListener("click", () => {
    const current = html.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    localStorage.setItem("eg_theme", next);
    btn.innerHTML = getIcon(next);
  });

  function getIcon(mode) {
    return mode === "dark" ? "☀️" : "🌙";
  }
});

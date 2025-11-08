/* ============================================================
   EURO_GOALS PRO+ UNIFIED v9.5.x – Main Controller
   Author: Pierros
   ============================================================ */

console.log("[EURO_GOALS] ✅ main_unified.js initialized");

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  initThemeToggle();
  refreshAllPanels();

  // Auto refresh κάθε 60 δευτερόλεπτα
  setInterval(refreshAllPanels, 60000);
});

/* ============================================================
   INITIALIZATION
   ============================================================ */
function initDashboard() {
  const panels = document.querySelectorAll(".panel");
  panels.forEach((panel, index) => {
    panel.style.opacity = 0;
    setTimeout(() => {
      panel.style.transition = "opacity 0.6s ease-out";
      panel.style.opacity = 1;
    }, 150 * index);
  });
}

/* ============================================================
   THEME TOGGLE (Dark / Light)
   ============================================================ */
function initThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  const html = document.documentElement;
  const icon = document.getElementById("theme-icon");

  if (!btn) return;

  btn.addEventListener("click", () => {
    html.classList.toggle("dark");
    const isDark = html.classList.contains("dark");

    if (isDark) {
      icon.style.color = "#3b82f6";
      localStorage.setItem("theme", "dark");
    } else {
      icon.style.color = "#2563eb";
      localStorage.setItem("theme", "light");
    }
  });

  // Φόρτωση αρχικής κατάστασης
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme === "light") html.classList.remove("dark");
}

/* ============================================================
   PANEL REFRESH LOGIC
   ============================================================ */
function refreshAllPanels() {
  updateSmartMoneyPanel();
  updateGoalMatrixPanel();
  updateSystemStatusPanel();
}

/* ---------------- SMARTMONEY PANEL ---------------- */
async function updateSmartMoneyPanel() {
  const container = document.getElementById("smartmoney-content");
  const dot = document.getElementById("smartmoney-status");

  try {
    const res = await fetch("/smartmoney_monitor");
    if (!res.ok) throw new Error("SmartMoney API error");
    const html = await res.text();
    container.innerHTML = html;
    dot.classList.add("active");
    dot.classList.remove("error");
  } catch (err) {
    container.innerHTML = `<p class="placeholder"⚠️ Σφάλμα SmartMoney Engine</p>`;
    dot.classList.add("error");
    dot.classList.remove("active");
    console.error("[EURO_GOALS] SmartMoney panel error:", err);
  }
}

/* ---------------- GOALMATRIX PANEL ---------------- */
async function updateGoalMatrixPanel() {
  const container = document.getElementById("goalmatrix-content");
  const dot = document.getElementById("goalmatrix-status");

  try {
    const res = await fetch("/goalmatrix_summary");
    if (!res.ok) throw new Error("GoalMatrix API error");
    const html = await res.text();
    container.innerHTML = html;
    dot.classList.add("active");
    dot.classList.remove("error");
  } catch (err) {
    container.innerHTML = `<p class="placeholder">⚠️ Σφάλμα GoalMatrix Engine</p>`;
    dot.classList.add("error");
    dot.classList.remove("active");
    console.error("[EURO_GOALS] GoalMatrix panel error:", err);
  }
}

/* ---------------- SYSTEM STATUS PANEL ---------------- */
async function updateSystemStatusPanel() {
  const container = document.getElementById("system-status-content");
  const dot = document.getElementById("system-status-dot");

  try {
    const res = await fetch("/system_status_html");
    if (!res.ok) throw new Error("Status endpoint error");
    const html = await res.text();
    container.innerHTML = html;
    dot.classList.add("active");
    dot.classList.remove("error");
  } catch (err) {
    container.innerHTML = `<p class="placeholder">⚠️ Το σύστημα δεν ανταποκρίνεται</p>`;
    dot.classList.add("error");
    dot.classList.remove("active");
    console.error("[EURO_GOALS] System status error:", err);
  }
}

/* ============================================================
   UTILS
   ============================================================ */
window.addEventListener("focus", () => {
  // Ανανεώνει panels όταν ο χρήστης επιστρέφει στο tab
  refreshAllPanels();
});

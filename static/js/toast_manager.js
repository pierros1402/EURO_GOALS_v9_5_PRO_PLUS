// ============================================================
// EURO_GOALS PRO+ v9.9.5 — Toast Manager (on-screen notifications)
// ============================================================
(function () {
  const TYPES = {
    info:  { icon: "ℹ️", cls: "" },
    ok:    { icon: "✅", cls: "ok" },
    warn:  { icon: "⚠️", cls: "warn" },
    err:   { icon: "⛔", cls: "err" },
    smart: { icon: "💰", cls: "smart" },
    goal:  { icon: "⚽", cls: "goal" },
  };

  function ensureContainer() {
    let c = document.getElementById("eg-toasts");
    if (!c) {
      c = document.createElement("div");
      c.id = "eg-toasts";
      c.className = "eg-toasts";
      document.body.appendChild(c);
    }
    return c;
  }

  function showToast(type = "info", title = "", msg = "", ms = 4000) {
    const c = ensureContainer();
    const t = document.createElement("div");
    const meta = TYPES[type] || TYPES.info;
    t.className = `eg-toast ${meta.cls}`;
    t.innerHTML = `
      <div class="eg-toast-icon">${meta.icon}</div>
      <div class="eg-toast-body">
        <div class="eg-toast-title">${title}</div>
        ${msg ? `<div class="eg-toast-msg">${msg}</div>` : ""}
      </div>
      <button class="eg-toast-close" title="Κλείσιμο">✕</button>
    `;
    c.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));

    const close = () => {
      t.classList.remove("show");
      setTimeout(() => t.remove(), 250);
    };
    t.querySelector(".eg-toast-close").addEventListener("click", close);
    setTimeout(close, ms);
  }

  // Expose
  window.showToast = showToast;
})();

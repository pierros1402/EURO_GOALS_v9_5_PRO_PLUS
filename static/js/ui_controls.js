(function () {
  const $ = (sel) => document.querySelector(sel);

  // Elements
  const led = {
    render: $("#led-render"),
    db: $("#led-db"),
    flashscore: $("#led-flashscore"),
    sofascore: $("#led-sofascore"),
    asianconnect: $("#led-asianconnect"),
  };

  const kv = {
    version: $("#kvVersion"),
    uptime: $("#kvUptime"),
    auto: $("#kvAuto"),
  };

  const topRefresh = $("#refreshNowBtn");
  const menuBtn = $("#menuBtn");
  const drawer = $("#mobileDrawer");
  const drawerClose = $("#drawerClose");

  // Toggles (SummaryBar)
  const sb = {
    smart: $("#sbSmartMoney"),
    goal: $("#sbGoalMatrix"),
    auto: $("#sbAutoRefresh"),
    interval: $("#sbInterval"),
  };

  // Toggles (Cards)
  const tgSmart = $("#toggleSmartMoney");
  const tgGoal = $("#toggleGoalMatrix");

  // Local state synced with server
  let REFRESH_SECS = parseInt(window.__EG__?.initialRefreshSecs ?? 15, 10);
  let timer = null;

  // -----------------------------
  // Helpers
  // -----------------------------
  function setLED(el, status) {
    el.classList.remove("ok", "bad", "warn");
    if (status === "ok") el.classList.add("ok");
    else if (status === "warn") el.classList.add("warn");
    else el.classList.add("bad");
  }

  async function api(path) {
    const res = await fetch(path, { cache: "no-store" });
    return await res.json();
  }

  async function postToggle(name, query) {
    const res = await fetch(`/api/toggle/${name}${query}`, { method: "POST" });
    return await res.json();
  }

  function formatUptime(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    return `${h}h ${m}m ${s}s`;
  }

  function startLoop() {
    stopLoop();
    timer = setInterval(refresh, REFRESH_SECS * 1000);
  }
  function stopLoop() {
    if (timer) clearInterval(timer);
    timer = null;
  }

  // -----------------------------
  // Refresh cycle
  // -----------------------------
  async function refresh() {
    try {
      const st = await api("/api/status");

      kv.version.textContent = st.version ?? "—";
      kv.uptime.textContent = formatUptime(st.uptime_sec ?? 0);
      kv.auto.textContent = st.state?.auto_refresh_on ? `ON (${st.state.refresh_secs}s)` : "OFF";

      setLED(led.render, st.services?.render_health ?? "warn");
      setLED(led.db, st.services?.db ?? "warn");
      setLED(led.flashscore, st.services?.apis?.flashscore ?? "warn");
      setLED(led.sofascore, st.services?.apis?.sofascore ?? "warn");
      setLED(led.asianconnect, st.services?.apis?.asianconnect ?? "warn");

      // keep UI toggles in sync
      const tg = await api("/api/toggles");
      [sb.smart, tgSmart].forEach(el => el.checked = !!tg.smartmoney_on);
      [sb.goal, tgGoal].forEach(el => el.checked = !!tg.goalmatrix_on);
      sb.auto.checked = !!tg.auto_refresh_on;
      REFRESH_SECS = parseInt(tg.refresh_secs ?? REFRESH_SECS, 10);
      sb.interval.value = REFRESH_SECS;

      if (tg.auto_refresh_on && !timer) startLoop();
      if (!tg.auto_refresh_on && timer) stopLoop();

    } catch (e) {
      console.error("Refresh failed", e);
      // degrade LEDs to warn
      Object.values(led).forEach(el => setLED(el, "warn"));
    }
  }

  // -----------------------------
  // Event wiring
  // -----------------------------
  topRefresh?.addEventListener("click", refresh);

  sb.smart?.addEventListener("change", async (e) => {
    await postToggle("smartmoney_on", `?value=${e.target.checked}`);
    refresh();
  });
  sb.goal?.addEventListener("change", async (e) => {
    await postToggle("goalmatrix_on", `?value=${e.target.checked}`);
    refresh();
  });
  sb.auto?.addEventListener("change", async (e) => {
    await postToggle("auto_refresh_on", `?value=${e.target.checked}`);
    refresh();
  });
  sb.interval?.addEventListener("change", async (e) => {
    const v = parseInt(e.target.value, 10);
    if (isNaN(v) || v < 5 || v > 300) return;
    await postToggle("refresh_secs", `?secs=${v}`);
    REFRESH_SECS = v;
    if (sb.auto.checked) startLoop();
    refresh();
  });

  tgSmart?.addEventListener("change", async (e) => {
    await postToggle("smartmoney_on", `?value=${e.target.checked}`);
    refresh();
  });
  tgGoal?.addEventListener("change", async (e) => {
    await postToggle("goalmatrix_on", `?value=${e.target.checked}`);
    refresh();
  });

  // Drawer
  menuBtn?.addEventListener("click", () => drawer.classList.add("open"));
  drawerClose?.addEventListener("click", () => drawer.classList.remove("open"));
  drawer?.addEventListener("click", (e) => {
    if (e.target === drawer) drawer.classList.remove("open");
  });

  // First load
  (async function init() {
    await refresh();
    // Enable loop if server says so
    const tg = await api("/api/toggles");
    if (tg.auto_refresh_on) startLoop();
  })();
})();

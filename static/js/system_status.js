// =====================================================
// System Status & LED Updater (Adaptive LEDs)
// =====================================================
function updateLED(id, active) {
  const led = document.getElementById(id);
  if (!led) return;
  if (active) led.classList.add("on");
  else led.classList.remove("on");
}

function updateSystemStatus(data) {
  updateLED("led-render", data.render_ok);
  updateLED("led-db", data.db_ok);
  updateLED("led-flashscore", data.flashscore_ok);
  updateLED("led-sofascore", data.sofascore_ok);
  updateLED("led-asianconnect", data.asianconnect_ok);
}

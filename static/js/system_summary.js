
async function updateSystemSummary() {
  try {
    const res = await fetch('/system_summary');
    const data = await res.json();

    document.getElementById('summary-database').innerText = `💾 DB: ${data.database}`;
    document.getElementById('summary-health').innerText = `❤️ Health: ${data.health}`;
    document.getElementById('summary-auto').innerText = `🔁 Refresh: ${data.auto_refresh}`;
    document.getElementById('summary-smartmoney').innerText = `💰 SmartMoney: ${data.smartmoney}`;
    document.getElementById('summary-render').innerText = `🌐 Render: ${data.render_service}`;
    document.getElementById('summary-version').innerText = `🧠 Version: ${data.version}`;
  } catch (err) {
    console.error("System Summary update failed", err);
  }
}

setInterval(updateSystemSummary, 60000); // κάθε 60''
updateSystemSummary(); // αρχική φόρτωση

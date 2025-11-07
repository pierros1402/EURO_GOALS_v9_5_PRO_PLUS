(function(){
  const container = document.querySelector("#alerts .eg-card-body");
  let lastCount = 0;

  // Ήχοι ανά τύπο
  const sounds = {
    SmartMoney: new Audio("/static/sounds/smartmoney_alert.mp3"),
    GoalMatrix: new Audio("/static/sounds/goal_alert.mp3"),
    System: new Audio("/static/sounds/alert.mp3")
  };

  async function loadAlerts(){
    try{
      const res = await fetch("/api/alerts_feed", {cache:"no-store"});
      const data = await res.json();
      if(!data.ok) return;

      container.innerHTML = "";
      data.alerts.forEach(a=>{
        const item = document.createElement("div");
        item.className = `alert-item level-${a.level}`;
        item.innerHTML = `
          <div class="alert-time">${a.time}</div>
          <div class="alert-type">${a.type}</div>
          <div class="alert-msg">${a.msg}</div>
        `;
        container.prepend(item);
      });

      // Νέο alert;
      if(data.count > lastCount){
        const latest = data.alerts[0];
        lastCount = data.count;

        // Παίξε ήχο ανά τύπο
        const type = latest.type || "System";
        (sounds[type] || sounds.System).play().catch(()=>{});

        // Εμφάνιση ειδοποίησης
        if(Notification.permission === "granted"){
          new Notification(`${latest.type} Alert`, {
            body: latest.msg,
            icon: "/static/icons/eurogoals_192.png"
          });
        }
      }

    }catch(e){
      console.warn("Alerts refresh failed", e);
    }
  }

  // Άδεια ειδοποιήσεων
  if("Notification" in window && Notification.permission !== "granted"){
    Notification.requestPermission();
  }

  // Πρώτο load + Loop
  loadAlerts();
  setInterval(loadAlerts, 10000);
})();

/* ============================================================
   EURO_GOALS PRO+ v10.2.1 — PWA Auto Update Monitor
   ============================================================ */

let updateBannerShown = false;

async function checkForAppUpdate() {
    if (!navigator.serviceWorker?.controller) return;

    navigator.serviceWorker.controller.postMessage("checkForUpdate");

    if (!updateBannerShown) {
        const div = document.createElement("div");
        div.id = "eg-update-banner";
        div.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0a84ff;
            color: white;
            padding: 12px 18px;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 0 20px rgba(0,0,0,0.4);
            cursor: pointer;
            z-index: 999999;
        `;
        div.innerText = "🔄 Νέα έκδοση διαθέσιμη — Πατήστε για ανανέωση";

        div.onclick = () => window.location.reload(true);

        document.body.appendChild(div);
        updateBannerShown = true;
    }
}

setInterval(checkForAppUpdate, 15000);

// ============================================================
// EURO_GOALS – Browser Push Client (subscribe & test)
// ============================================================

async function urlBase64ToUint8Array(base64String) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) outputArray[i] = rawData.charCodeAt(i);
  return outputArray;
}

export async function enablePush() {
  try {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      alert("Push notifications not supported in this browser.");
      return;
    }
    const reg = await navigator.serviceWorker.register("/sw.js");
    const vapidRes = await fetch("/push/public_key");
    const { publicKey } = await vapidRes.json();
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: await urlBase64ToUint8Array(publicKey),
    });
    await fetch("/push/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sub),
    });
    alert("Push notifications enabled ✅");
  } catch (e) {
    console.error("Push subscribe error:", e);
    alert("Push enable failed.");
  }
}

export async function testPush() {
  try {
    const r = await fetch("/push/test", { method: "POST" });
    alert(r.ok ? "Test push sent ✅" : "Test push failed.");
  } catch (e) {
    alert("Test push failed.");
  }
}

function isBlocked() {
  const t = document.body?.innerText || "";
  return t.includes("Access denied") || t.includes("Accès refusé");
}

function pageSnapshot() {
  return {
    url: location.href,
    html: document.documentElement.outerHTML,
    title: document.title || "",
  };
}

function validatePage({ title, html }) {
  if (isBlocked()) {
    return "Seite blockiert (Access denied) — VPN prüfen";
  }
  if (title.includes("Fehler aufgetreten") || html.slice(0, 5000).includes("Fehler aufgetreten")) {
    return "LV-Fehlerseite — F5 drücken und warten";
  }
  if (html.length < 50000) {
    return `Seite noch zu klein (${html.length} Bytes) — F5 und warten bis alles geladen ist`;
  }
  return null;
}

function trySavePage(reason) {
  const data = pageSnapshot();
  const err = validatePage(data);
  if (err) {
    console.log("[LV Capture] noch nicht bereit:", reason, err);
    return Promise.resolve({ ok: false, error: err });
  }
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type: "save-page", ...data, reason }, (response) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: "Listener nicht erreichbar — ./start_listener.sh starten" });
        return;
      }
      resolve(response || { ok: false, error: "Keine Antwort vom Listener" });
    });
  });
}

function scheduleCapture(reason, delayMs) {
  setTimeout(() => {
    trySavePage(reason).then((r) => {
      if (r.ok) console.log("[LV Capture] auto:", r.path);
    });
  }, delayMs);
}

// Produktseiten: nach Laden automatisch speichern (Batch-Modus)
const isProductPage = /\/deu-de\/produkte\//.test(location.pathname);
if (isProductPage) {
  scheduleCapture("product-auto", 8000);
}

scheduleCapture("auto", 5000);

window.addEventListener("load", () => {
  const nav = performance.getEntriesByType("navigation")[0];
  if (nav && nav.type === "reload") {
    scheduleCapture("after-reload", 7000);
  }
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "capture-now") {
    trySavePage("manual-click").then(sendResponse);
    return true;
  }
  return false;
});

chrome.runtime.sendMessage({ type: "lv-page-ready", url: location.href });

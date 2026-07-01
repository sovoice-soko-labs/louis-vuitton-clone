const LISTENER = "http://127.0.0.1:8765";

const LV_URLS = [
  "https://de.louisvuitton.com/",
  "https://www.louisvuitton.com/",
  "https://louisvuitton.com/",
];

let lastFingerprint = "";

function isLvUrl(url) {
  try {
    return new URL(url).hostname.includes("louisvuitton.com");
  } catch {
    return false;
  }
}

function fingerprint(cookies) {
  return cookies
    .map((c) => `${c.domain}|${c.name}=${c.value}`)
    .sort()
    .join(";");
}

async function getAllLvCookies(tabUrl) {
  const seen = new Map();
  const add = (list) => {
    for (const c of list || []) seen.set(`${c.domain}|${c.path}|${c.name}`, c);
  };
  if (tabUrl && isLvUrl(tabUrl)) add(await chrome.cookies.getAll({ url: tabUrl }));
  for (const url of LV_URLS) add(await chrome.cookies.getAll({ url }));
  for (const domain of [".louisvuitton.com", "louisvuitton.com", "de.louisvuitton.com"]) {
    add(await chrome.cookies.getAll({ domain }));
  }
  return [...seen.values()];
}

async function sendCookies(url, reason, force = false) {
  const cookies = await getAllLvCookies(url);
  if (!cookies.length) return;
  const fp = fingerprint(cookies);
  if (!force && fp === lastFingerprint) return;
  try {
    const res = await fetch(`${LISTENER}/cookies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cookies, url: url || "", reason, auto_clone: false }),
    });
    const data = await res.json();
    if (data.ok) lastFingerprint = fp;
  } catch (err) {
    console.warn("[LV Capture] Cookies:", err.message);
  }
}

async function savePage(payload) {
  try {
    const health = await fetch(`${LISTENER}/health`);
    if (!health.ok) {
      return { ok: false, error: "Listener nicht aktiv — im Terminal: ./start_listener.sh" };
    }
    const res = await fetch(`${LISTENER}/save-page`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    let data;
    try {
      data = await res.json();
    } catch {
      return { ok: false, error: `Listener-Fehler (HTTP ${res.status}) — ./stop_listener.sh && ./start_listener.sh` };
    }
    if (data.ok) {
      console.log("[LV Capture]", data.message);
      return { ok: true, path: data.path, message: data.message };
    }
    return { ok: false, error: data.error || `Fehler HTTP ${res.status}` };
  } catch (err) {
    return { ok: false, error: `Listener offline — Terminal: ./start_listener.sh` };
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "lv-page-ready") {
    setTimeout(() => sendCookies(msg.url, "content-script"), 2000);
    sendResponse({ ok: true });
    return false;
  }
  if (msg?.type === "save-page") {
    savePage(msg).then(sendResponse);
    return true;
  }
  return false;
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;
  if (!tab.url || !isLvUrl(tab.url)) return;
  setTimeout(() => sendCookies(tab.url, "tab-updated"), 3000);
});

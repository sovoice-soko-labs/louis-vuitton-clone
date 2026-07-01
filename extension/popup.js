const statusEl = document.getElementById("status");
const saveBtn = document.getElementById("save");

function setStatus(text, kind) {
  statusEl.textContent = text;
  statusEl.className = kind || "";
}

saveBtn.addEventListener("click", async () => {
  saveBtn.disabled = true;
  setStatus("Speichere …", "pending");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.url?.includes("louisvuitton.com")) {
      setStatus("Bitte zuerst eine louisvuitton.com-Seite öffnen.", "err");
      return;
    }

    let result;
    try {
      result = await chrome.tabs.sendMessage(tab.id, { type: "capture-now" });
    } catch {
      setStatus("Seite neu laden (F5), dann erneut klicken.", "err");
      return;
    }

    if (result?.ok) {
      setStatus(`✓ Gespeichert: ${result.path || "OK"}`, "ok");
    } else {
      setStatus(result?.error || "Fehler — F5 drücken und erneut versuchen.", "err");
    }
  } catch (err) {
    setStatus(`Fehler: ${err.message}`, "err");
  } finally {
    saveBtn.disabled = false;
  }
});

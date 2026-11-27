(() => {
  "use strict";
  const root = document.getElementById("reminder-helper");
  if (!root) return;

  const csrf = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const pollUrl = root.dataset.pollUrl;
  const pollInterval = Number(root.dataset.pollInterval) || 30000;
  const fallback = document.getElementById("reminder-fallback");
  const permissionStatus = document.getElementById("browser-notification-status");

  function showFallback(message) {
    if (!fallback) return false;
    const item = document.createElement("p");
    item.textContent = message;
    fallback.appendChild(item);
    return true;
  }

  function showNotice(notice) {
    const list = document.getElementById("reminder-notices");
    if (!list || list.querySelector(`[data-notice-id="${notice.id}"]`)) return;
    const empty = list.querySelector(".no-reminder-notices");
    if (empty) empty.remove();
    const item = document.createElement("li");
    item.dataset.noticeId = notice.id;
    const text = document.createElement("span");
    text.textContent = notice.message;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Dismiss";
    button.dataset.dismissNotice = notice.id;
    item.append(text, button);
    list.prepend(item);
  }

  async function acknowledge(reminder, success, error = "") {
    try {
      await fetch(`/api/reminders/${reminder.id}/delivery`, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ claim_token: reminder.claim_token, success, error })
      });
    } catch (_) {
      // The server-side claim lease makes an unacknowledged delivery retryable.
    }
  }

  function deliver(reminder) {
    const message = reminder.message || "You have a study reminder.";
    const storageKey = `study-management-reminder-delivered:${reminder.id}`;
    try {
      if (window.localStorage.getItem(storageKey)) {
        acknowledge(reminder, true);
        return;
      }
    } catch (_) { /* Server-side claims remain the primary cross-tab guard. */ }

    function markDisplayed() {
      try { window.localStorage.setItem(storageKey, "1"); } catch (_) { /* Optional browser safeguard. */ }
      acknowledge(reminder, true);
    }

    if ("Notification" in window && Notification.permission === "granted") {
      try {
        const notification = new Notification("Study Management System", { body: message });
        notification.onerror = () => showFallback(message);
        markDisplayed();
        return;
      } catch (error) {
        if (showFallback(message)) markDisplayed();
        else acknowledge(reminder, false, "Browser notification and in-app fallback were unavailable.");
        return;
      }
    }
    if (showFallback(message)) markDisplayed();
    else acknowledge(reminder, false, "In-app notification fallback was unavailable.");
  }

  async function poll() {
    try {
      const response = await fetch(pollUrl, { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) return;
      const data = await response.json();
      (data.reminders || []).forEach(deliver);
      (data.notices || []).forEach(showNotice);
    } catch (_) {
      // The next scheduled poll retries the check; no external service is used.
    }
  }

  document.getElementById("enable-browser-notifications")?.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      permissionStatus.textContent = "Browser notifications are unavailable; in-app notices remain enabled.";
      return;
    }
    try {
      const permission = await Notification.requestPermission();
      permissionStatus.textContent = permission === "granted"
        ? "Browser notifications enabled."
        : "Browser permission not granted; in-app notices remain enabled.";
      poll();
    } catch (_) {
      permissionStatus.textContent = "Browser permission could not be requested; in-app notices remain enabled.";
    }
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-dismiss-notice]");
    if (!button) return;
    const noticeId = button.dataset.dismissNotice;
    try {
      const response = await fetch(`/api/reminder-notices/${noticeId}/dismiss`, {
        method: "POST", credentials: "same-origin", headers: { "X-CSRF-Token": csrf }
      });
      if (response.ok) button.closest("li")?.remove();
    } catch (_) { /* Keep the notice visible if dismissal did not persist. */ }
  });

  document.querySelectorAll(".reminder-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const type = form.dataset.eventType;
      let eventAt = form.dataset.eventUtc || "";
      if (type === "session") {
        const local = form.dataset.eventLocal;
        const parsed = new Date(local);
        if (Number.isNaN(parsed.getTime())) {
          event.preventDefault();
          showFallback("The scheduled session time could not be interpreted by this browser.");
          return;
        }
        eventAt = parsed.toISOString();
      }
      form.querySelector('input[name="event_at"]').value = type === "session" ? eventAt : "";
      const preset = form.querySelector(".reminder-preset").value;
      const remindAt = form.querySelector('input[name="remind_at"]');
      if (preset) {
        if (!eventAt) {
          event.preventDefault();
          showFallback("This event has no timestamp to calculate the saved reminder preset.");
          return;
        }
        remindAt.value = new Date(new Date(eventAt).getTime() - Number(preset) * 1000).toISOString();
      } else {
        const custom = form.querySelector(".custom-reminder-time").value;
        if (!custom) {
          event.preventDefault();
          showFallback("Choose a custom reminder time or a saved preset.");
          return;
        }
        const parsed = new Date(custom);
        if (Number.isNaN(parsed.getTime())) {
          event.preventDefault();
          showFallback("Enter a valid reminder date and time.");
          return;
        }
        remindAt.value = parsed.toISOString();
      }
    });
  });

  if ("Notification" in window) {
    permissionStatus.textContent = Notification.permission === "granted"
      ? "Browser notifications enabled."
      : "In-app fallback is available; browser permission is optional.";
  } else {
    permissionStatus.textContent = "Browser notifications unavailable; in-app fallback is active.";
  }

  poll();
  window.setInterval(poll, pollInterval);
})();

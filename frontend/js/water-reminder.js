const waterButton = document.querySelector("#water-button");
const waterCount = document.querySelector("#water-count");
const waterProgress = document.querySelector("#water-progress");
const waterStatus = document.querySelector("#water-status");
const reminderStatus = document.querySelector("#water-reminder-status");
const reminderInterval = document.querySelector("#water-reminder-interval");
const reminderToggle = document.querySelector("#water-reminder-toggle");

let loggedWaterGlasses = 0;
let reminderTimer = null;
const demoProgressLimit = 8;

function updateWaterCount() {
  waterCount.textContent = String(loggedWaterGlasses);
  waterProgress.setAttribute(
    "aria-valuenow",
    String(Math.min(loggedWaterGlasses, demoProgressLimit)),
  );
  waterProgress.querySelector("span").style.width = `${Math.min(
    (loggedWaterGlasses / demoProgressLimit) * 100,
    100,
  )}%`;
}

function stopReminder() {
  if (reminderTimer !== null) {
    window.clearInterval(reminderTimer);
    reminderTimer = null;
  }
  reminderToggle.textContent = "Start reminder";
}

waterButton.addEventListener("click", () => {
  loggedWaterGlasses += 1;
  updateWaterCount();
  waterStatus.textContent = "Logged for this page session only.";
});

reminderToggle.addEventListener("click", () => {
  if (reminderTimer !== null) {
    stopReminder();
    reminderStatus.textContent = "Reminder paused.";
    return;
  }

  const intervalMinutes = Number(reminderInterval.value);
  if (!Number.isFinite(intervalMinutes) || intervalMinutes <= 0) {
    reminderStatus.textContent = "Choose a valid reminder interval.";
    return;
  }

  reminderTimer = window.setInterval(() => {
    reminderStatus.textContent =
      "Water reminder: take a break if you would like one.";
  }, intervalMinutes * 60 * 1000);
  reminderToggle.textContent = "Pause reminder";
  reminderStatus.textContent =
    `Reminder set for every ${intervalMinutes} minute(s) while this page is open.`;
});

reminderInterval.addEventListener("change", () => {
  if (reminderTimer !== null) {
    stopReminder();
    reminderToggle.click();
  }
});

window.addEventListener("pagehide", stopReminder);

const waterButton = document.querySelector("#water-button");
const waterCount = document.querySelector("#water-count");
const waterProgress = document.querySelector("#water-progress");
const waterStatus = document.querySelector("#water-status");
const waterAmount = document.querySelector("#water-amount");
const undoWaterButton = document.querySelector("#undo-water-button");
const reminderStatus = document.querySelector("#water-reminder-status");
const reminderInterval = document.querySelector("#water-reminder-interval");
const reminderToggle = document.querySelector("#water-reminder-toggle");

const storageKeyPrefix = "bhojon-water-log-";
const progressScaleMl = 2000;
let currentDateKey = getLocalDateKey(new Date());
let loggedWaterEntries = [];
let storageAvailable = true;
let reminderTimer = null;

function getLocalDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getStorageKey(dateKey) {
  return `${storageKeyPrefix}${dateKey}`;
}

function loadWaterEntries(dateKey) {
  const savedEntries = window.localStorage.getItem(getStorageKey(dateKey));
  if (savedEntries === null) {
    return [];
  }

  const entries = JSON.parse(savedEntries);
  if (
    !Array.isArray(entries) ||
    entries.some(
      (entry) =>
        !entry ||
        !Number.isInteger(entry.amountMl) ||
        entry.amountMl <= 0 ||
        typeof entry.loggedAt !== "string" ||
        !Number.isFinite(Date.parse(entry.loggedAt)),
    )
  ) {
    throw new Error("Saved water log has an invalid format.");
  }
  return entries;
}

function updateWaterCount() {
  const totalWaterMl = loggedWaterEntries.reduce(
    (total, entry) => total + entry.amountMl,
    0,
  );
  waterCount.textContent = storageAvailable ? String(totalWaterMl) : "—";
  waterProgress.querySelector("span").style.width = `${Math.min(
    (totalWaterMl / progressScaleMl) * 100,
    100,
  )}%`;
  waterButton.disabled = !storageAvailable;
  undoWaterButton.disabled = !storageAvailable || loggedWaterEntries.length === 0;
}

function refreshWaterLogForToday() {
  const todayKey = getLocalDateKey(new Date());
  if (todayKey === currentDateKey) {
    return storageAvailable;
  }

  currentDateKey = todayKey;
  try {
    loggedWaterEntries = loadWaterEntries(currentDateKey);
    storageAvailable = true;
    waterStatus.textContent = "";
  } catch (error) {
    loggedWaterEntries = [];
    storageAvailable = false;
    waterStatus.textContent =
      "Could not load your saved water log. Browser storage may be unavailable or the saved data may be invalid.";
  }
  updateWaterCount();
  return storageAvailable;
}

function saveWaterEntries(entries, successMessage) {
  try {
    window.localStorage.setItem(
      getStorageKey(currentDateKey),
      JSON.stringify(entries),
    );
  } catch (error) {
    waterStatus.textContent =
      "Could not save your water log in this browser. Check your browser storage settings and try again.";
    return false;
  }

  loggedWaterEntries = entries;
  updateWaterCount();
  waterStatus.textContent = successMessage;
  return true;
}

function stopReminder() {
  if (reminderTimer !== null) {
    window.clearInterval(reminderTimer);
    reminderTimer = null;
  }
  reminderToggle.textContent = "Start reminder";
}

try {
  loggedWaterEntries = loadWaterEntries(currentDateKey);
} catch (error) {
  storageAvailable = false;
  waterStatus.textContent =
    "Could not load your saved water log. Browser storage may be unavailable or the saved data may be invalid.";
}
updateWaterCount();

waterButton.addEventListener("click", () => {
  if (!refreshWaterLogForToday()) {
    return;
  }

  const amountMl = Number(waterAmount.value);
  if (!Number.isInteger(amountMl) || amountMl <= 0) {
    waterStatus.textContent = "Choose a valid drink amount.";
    return;
  }

  const entries = [
    ...loggedWaterEntries,
    { amountMl, loggedAt: new Date().toISOString() },
  ];
  saveWaterEntries(entries, `Logged ${amountMl} ml.`);
});

undoWaterButton.addEventListener("click", () => {
  if (!refreshWaterLogForToday()) {
    return;
  }

  if (loggedWaterEntries.length === 0) {
    return;
  }

  const removedEntry = loggedWaterEntries[loggedWaterEntries.length - 1];
  const entries = loggedWaterEntries.slice(0, -1);
  saveWaterEntries(entries, `Undid the last ${removedEntry.amountMl} ml entry.`);
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

window.addEventListener("focus", refreshWaterLogForToday);
window.addEventListener("pagehide", stopReminder);

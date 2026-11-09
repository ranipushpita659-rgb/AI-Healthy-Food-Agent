const profileForm = document.querySelector("#profile-form");
const profileStatus = document.querySelector("#profile-status");
const submitProfileButton = document.querySelector("#submit-profile");
const waterButton = document.querySelector("#water-button");
const waterCount = document.querySelector("#water-count");
const waterProgress = document.querySelector("#water-progress");
const waterStatus = document.querySelector("#water-status");

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  profileStatus.textContent = "Checking your details…";
  profileStatus.className = "form-status";
  submitProfileButton.disabled = true;

  const formData = new FormData(profileForm);
  const profile = {
    age: Number(formData.get("age")),
    gender: formData.get("gender"),
    height_cm: Number(formData.get("height_cm")),
    weight_kg: Number(formData.get("weight_kg")),
    activity_level: formData.get("activity_level"),
    health_goal: formData.get("health_goal"),
    food_preferences: formData.getAll("food_preferences"),
    excluded_foods: String(formData.get("excluded_foods") || "")
      .split(",")
      .map((food) => food.trim())
      .filter(Boolean),
  };

  try {
    const response = await fetch("/api/profile/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    const result = await response.json();

    if (!response.ok) {
      const details = Array.isArray(result.detail)
        ? result.detail.map((issue) => `${issue.field}: ${issue.message}`).join(" ")
        : result.detail || "Please check the information and try again.";
      throw new Error(details);
    }

    profileStatus.textContent = result.message;
    profileStatus.className = "form-status success";
  } catch (error) {
    profileStatus.textContent =
      error instanceof TypeError
        ? "Could not reach the server. Check that the FastAPI app is running."
        : error.message;
    profileStatus.className = "form-status error";
  } finally {
    submitProfileButton.disabled = false;
  }
});

let loggedWaterGlasses = 0;
const demoWaterGoal = 8;

waterButton.addEventListener("click", () => {
  loggedWaterGlasses += 1;
  waterCount.textContent = String(loggedWaterGlasses);
  waterProgress.style.width = `${Math.min(
    (loggedWaterGlasses / demoWaterGoal) * 100,
    100,
  )}%`;
  waterStatus.textContent = "Added to this temporary demo counter.";
});

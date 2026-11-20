const profileForm = document.querySelector("#profile-form");
const profileStatus = document.querySelector("#profile-status");
const submitProfileButton = document.querySelector("#submit-profile");
const mealList = document.querySelector("#meal-list");
const mealStatus = document.querySelector("#meal-status");
const mealSafety = document.querySelector("#meal-safety");
const nutritionContent = document.querySelector("#nutrition-content");
const assumptionList = document.querySelector("#assumption-list");
const planAssumptions = document.querySelector("#plan-assumptions");

const mealIcons = {
  breakfast: "☀",
  lunch: "◒",
  dinner: "☾",
  snack: "✿",
};

function formatNumber(value, maximumFractionDigits = 1) {
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits,
  }).format(value);
}

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) {
    element.className = className;
  }
  element.textContent = text;
  return element;
}

function emptyState(iconText, title, description) {
  const state = document.createElement("div");
  state.className = "empty-state";
  const icon = createTextElement("span", "empty-icon", iconText);
  icon.setAttribute("aria-hidden", "true");
  state.append(
    icon,
    createTextElement("h3", "", title),
    createTextElement("p", "", description),
  );
  return state;
}

function resetPlanDisplay() {
  mealList.replaceChildren(
    emptyState("⌂", "Your plan will appear here", "Submit your profile to generate a new plan."),
  );
  document.querySelector("#agent-summary").textContent = "";
  mealSafety.textContent = "";
  mealSafety.hidden = true;
  planAssumptions.hidden = true;
  assumptionList.replaceChildren();

  nutritionContent.className = "empty-state";
  const nutritionEmptyState = emptyState(
    "⌕",
    "Nutrition totals will appear here",
    "Generate a plan to see daily nutrition.",
  );
  nutritionContent.replaceChildren(...nutritionEmptyState.childNodes);
  document.querySelector("#calorie-summary").textContent = "Not calculated";
  document.querySelector("#calorie-detail").textContent = "Waiting for a meal plan";
  document.querySelector("#plan-calorie-summary").textContent = "Not calculated";
  document.querySelector("#plan-calorie-detail").textContent = "Generated meal plan";
  document.querySelector("#nutrition-summary").textContent = "Not calculated";
  document.querySelector("#nutrition-detail").textContent = "Macros from selected foods";
}

function makeProfile(formData) {
  return {
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
}

function renderNutrition(totals) {
  const values = [
    ["Calories", `${formatNumber(totals.calories_kcal)} kcal`],
    ["Protein", `${formatNumber(totals.protein_g)} g`],
    ["Carbohydrates", `${formatNumber(totals.carbohydrates_g)} g`],
    ["Fat", `${formatNumber(totals.fat_g)} g`],
    ["Fibre", `${formatNumber(totals.fibre_g)} g`],
  ];
  const grid = document.createElement("dl");
  grid.className = "nutrition-grid";

  values.forEach(([label, value]) => {
    const metric = document.createElement("div");
    metric.className = "nutrition-metric";
    metric.append(
      createTextElement("dt", "", label),
      createTextElement("dd", "", value),
    );
    grid.append(metric);
  });

  nutritionContent.className = "nutrition-content";
  nutritionContent.replaceChildren(grid);
}

function renderMealPlan(result) {
  const { meal_plan: plan } = result;
  const reasonsByFood = new Map(
    result.reasons.map((entry) => [entry.food_id, entry.reason]),
  );
  const fragment = document.createDocumentFragment();

  plan.meals.forEach((meal) => {
    const article = document.createElement("article");
    article.className = "meal-item";

    const icon = createTextElement(
      "span",
      `meal-icon ${meal.meal}`,
      mealIcons[meal.meal] || "•",
    );
    icon.setAttribute("aria-hidden", "true");

    const content = document.createElement("div");
    content.className = "meal-content";
    content.append(
      createTextElement("p", "meal-type", meal.meal.toUpperCase()),
      createTextElement(
        "h3",
        "",
        meal.items.map((item) => item.name).join(" + "),
      ),
    );

    meal.items.forEach((item) => {
      content.append(
        createTextElement(
          "p",
          "meal-serving",
          `${formatNumber(item.servings, 2)} serving(s) · ${formatNumber(item.serving_g)} g per serving`,
        ),
      );
      const reason = reasonsByFood.get(item.food_id);
      if (reason) {
        content.append(createTextElement("p", "meal-reason", reason));
      }
    });

    content.append(
      createTextElement(
        "p",
        "meal-nutrition",
        `${formatNumber(meal.nutrition.calories_kcal)} kcal · ` +
          `Protein ${formatNumber(meal.nutrition.protein_g)} g · ` +
          `Carbs ${formatNumber(meal.nutrition.carbohydrates_g)} g · ` +
          `Fat ${formatNumber(meal.nutrition.fat_g)} g · ` +
          `Fibre ${formatNumber(meal.nutrition.fibre_g)} g`,
      ),
    );
    article.append(icon, content);
    fragment.append(article);
  });

  mealList.replaceChildren(fragment);
  document.querySelector("#agent-summary").textContent = result.summary;
  mealSafety.textContent = `${result.safety_note} ${plan.notice}`;
  mealSafety.hidden = false;
  renderNutrition(plan.daily_nutrition);

  const calorieEstimate = result.calorie_estimate;
  document.querySelector("#calorie-summary").textContent =
    `${formatNumber(calorieEstimate.goal_target_calories_min_kcal, 0)}–` +
    `${formatNumber(calorieEstimate.goal_target_calories_max_kcal, 0)} kcal`;
  document.querySelector("#calorie-detail").textContent =
    `Goal range · BMI ${formatNumber(result.bmi)} (not diagnostic)`;
  document.querySelector("#plan-calorie-summary").textContent =
    `${formatNumber(plan.daily_nutrition.calories_kcal)} kcal`;
  document.querySelector("#plan-calorie-detail").textContent =
    `Plan target: ${formatNumber(plan.daily_calorie_target_kcal, 0)} kcal`;
  document.querySelector("#nutrition-summary").textContent =
    `${formatNumber(plan.daily_nutrition.calories_kcal)} kcal`;
  document.querySelector("#nutrition-detail").textContent =
    `Protein ${formatNumber(plan.daily_nutrition.protein_g)} g · ` +
    `Fibre ${formatNumber(plan.daily_nutrition.fibre_g)} g`;

  assumptionList.replaceChildren(
    ...result.assumptions.map((assumption) =>
      createTextElement("li", "", assumption),
    ),
  );
  planAssumptions.hidden = result.assumptions.length === 0;
  mealStatus.textContent =
    result.message || "Meal plan and profile saved to the local database.";
  mealStatus.className = result.message
    ? "form-status"
    : "form-status success";
}

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  profileStatus.textContent = "Generating your meal plan…";
  profileStatus.className = "form-status";
  mealStatus.textContent = "";
  mealStatus.className = "form-status";
  resetPlanDisplay();
  submitProfileButton.disabled = true;
  submitProfileButton.textContent = "Generating plan…";

  try {
    const formData = new FormData(profileForm);
    const result = await window.apiClient.post("/api/agent/recommend", {
      profile: makeProfile(formData),
      available_foods: formData.getAll("available_foods"),
    });
    renderMealPlan(result);
    profileStatus.textContent =
      result.source === "llm"
        ? "Plan generated and profile saved."
        : "Plan generated and profile saved; using the deterministic explanation.";
    profileStatus.className = "form-status success";
  } catch (error) {
    profileStatus.textContent =
      error instanceof Error
        ? error.message
        : "Could not generate the plan. Please try again.";
    profileStatus.className = "form-status error";
    mealStatus.textContent = profileStatus.textContent;
    mealStatus.className = "form-status error";
  } finally {
    submitProfileButton.disabled = false;
    submitProfileButton.textContent = "Generate meal plan →";
  }
});

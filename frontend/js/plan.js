const planContent = document.querySelector("#plan-content");
const planError = document.querySelector("#plan-error");
const mealList = document.querySelector("#meal-list");
const assumptionList = document.querySelector("#assumption-list");
const planAssumptions = document.querySelector("#plan-assumptions");
const mealIcons = { breakfast: "☀", lunch: "◒", dinner: "☾", snack: "✿" };

function formatNumber(value, maximumFractionDigits = 1) {
  return new Intl.NumberFormat("en-BD", { maximumFractionDigits }).format(value);
}

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function showPlanError(message) {
  planError.hidden = false;
  planError.textContent = message;
  planContent.hidden = true;
  document.querySelector("#download-pdf").disabled = true;
}

function renderMealPlan(result) {
  const plan = result.meal_plan;
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
    content.append(
      createTextElement("h3", "meal-type", meal.meal.toUpperCase()),
    );
    const components = document.createElement("ul");
    components.className = "meal-components";
    meal.items.forEach((item) => {
      const component = document.createElement("li");
      component.append(
        createTextElement("span", "", item.name),
        createTextElement(
          "span",
          "meal-serving",
          `${formatNumber(item.servings * item.serving_g, 0)} g`,
        ),
      );
      const reason = reasonsByFood.get(item.food_id);
      if (reason && reason !== "Selected from the foods available for your plan.") {
        component.append(createTextElement("small", "meal-reason", reason));
      }
      components.append(component);
    });
    content.append(components);
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

  document.querySelector("#plan-summary").textContent = result.summary;
  document.querySelector("#plan-notice").textContent = plan.notice;
  document.querySelector("#safety-note").textContent = result.safety_note;
  assumptionList.replaceChildren(
    ...result.assumptions.map((assumption) =>
      createTextElement("li", "", assumption),
    ),
  );
  planAssumptions.open = false;

  const totals = plan.daily_nutrition;
  document.querySelector("#calorie-highlight").replaceChildren(
    createTextElement("span", "", "Planned calories"),
    createTextElement("strong", "", `${formatNumber(totals.calories_kcal, 0)} kcal`),
  );
  const metrics = [
    ["Protein", totals.protein_g, "g"],
    ["Carbohydrates", totals.carbohydrates_g, "g"],
    ["Fat", totals.fat_g, "g"],
    ["Fibre", totals.fibre_g, "g"],
  ];
  const nutritionGrid = document.querySelector("#nutrition-grid");
  nutritionGrid.replaceChildren(
    ...metrics.map(([label, amount, unit]) => {
      const metric = document.createElement("div");
      metric.className = "nutrition-metric";
      metric.append(
        createTextElement("dt", "", label),
        createTextElement("dd", "", `${formatNumber(amount)} ${unit}`),
      );
      return metric;
    }),
  );
  const estimate = result.calorie_estimate;
  document.querySelector("#calorie-range-value").textContent =
    `${formatNumber(estimate.goal_target_calories_min_kcal, 0)}–${formatNumber(estimate.goal_target_calories_max_kcal, 0)} kcal`;
  document.querySelector("#bmi-note").textContent =
    `BMI estimate: ${formatNumber(result.bmi)}. BMI is a screening measure, not a diagnosis.`;
}

function initializePage() {
  let savedPlan;
  try {
    const savedValue = window.localStorage.getItem("bhojon-food-plan");
    savedPlan = savedValue ? JSON.parse(savedValue) : null;
  } catch (error) {
    showPlanError("This browser could not read the saved plan. Please create a new plan.");
    return;
  }
  if (!savedPlan || !savedPlan.result || !savedPlan.result.meal_plan) {
    showPlanError("Your plan is not available in this browser. Create a new plan to get started.");
    return;
  }

  try {
    renderMealPlan(savedPlan.result);
    if (savedPlan.generatedAt) {
      const date = new Date(savedPlan.generatedAt);
      if (Number.isNaN(date.getTime())) throw new Error("Invalid saved plan date.");
      document.querySelector("#plan-date").textContent =
        `Created ${new Intl.DateTimeFormat("en-BD", {
          dateStyle: "long",
          timeStyle: "short",
        }).format(date)}`;
      document.title = `Bhojon-food-plan-${date.toISOString().slice(0, 10)}`;
    }
  } catch (error) {
    showPlanError("The saved plan could not be displayed. Please generate a new plan.");
  }
}

document.querySelector("#download-pdf").addEventListener("click", () => {
  window.print();
});

initializePage();

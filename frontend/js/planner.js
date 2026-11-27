const profileForm = document.querySelector("#profile-form");
const profileStatus = document.querySelector("#profile-status");
const submitProfileButton = document.querySelector("#submit-profile");
const selectedFoodsContainer = document.querySelector("#selected-foods");
const foodPicker = document.querySelector("#food-picker");
const foodSearch = document.querySelector("#food-search");
const foodPickerOptions = document.querySelector("#food-picker-options");
const pickerStatus = document.querySelector("#picker-status");
const customFoodForm = document.querySelector("#custom-food-form");
const customFoodName = document.querySelector("#custom-food-name");
const customFoodStatus = document.querySelector("#custom-food-status");

const foodsById = new Map();
const selectedFoodIds = new Set();
const customFoods = new Map();

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function renderSelectedFoods() {
  selectedFoodsContainer.replaceChildren();
  if (selectedFoodIds.size === 0 && customFoods.size === 0) {
    selectedFoodsContainer.append(
      createTextElement("p", "pantry-empty", "No foods selected yet. Add foods from your kitchen to continue."),
    );
    return;
  }

  selectedFoodIds.forEach((foodId) => {
    const food = foodsById.get(foodId);
    if (!food) return;
    const chip = createTextElement("span", "food-chip", food.name);
    const removeButton = createTextElement("button", "", "×");
    removeButton.type = "button";
    removeButton.setAttribute("aria-label", `Remove ${food.name}`);
    removeButton.addEventListener("click", () => {
      selectedFoodIds.delete(foodId);
      renderSelectedFoods();
      renderFoodOptions();
    });
    chip.append(removeButton);
    selectedFoodsContainer.append(chip);
  });

  customFoods.forEach((name, normalizedName) => {
    const chip = createTextElement("span", "food-chip", name);
    const removeButton = createTextElement("button", "", "×");
    removeButton.type = "button";
    removeButton.setAttribute("aria-label", `Remove ${name}`);
    removeButton.addEventListener("click", () => {
      customFoods.delete(normalizedName);
      renderSelectedFoods();
    });
    chip.append(removeButton);
    selectedFoodsContainer.append(chip);
  });
}

function renderFoodOptions() {
  const query = foodSearch.value.trim().toLocaleLowerCase();
  const availableFoods = [...foodsById.values()]
    .filter((food) => !selectedFoodIds.has(food.id))
    .filter((food) => food.name.toLocaleLowerCase().includes(query))
    .sort((left, right) => left.name.localeCompare(right.name));

  foodPickerOptions.replaceChildren();
  if (availableFoods.length === 0) {
    foodPickerOptions.append(
      createTextElement("p", "pantry-empty", "No more foods match your search."),
    );
    return;
  }

  availableFoods.forEach((food) => {
    const label = createTextElement("label", "food-option", "");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = food.id;
    checkbox.name = "food-picker-selection";
    label.append(
      checkbox,
      createTextElement("span", "", food.name),
      createTextElement("small", "", food.category),
    );
    foodPickerOptions.append(label);
  });
}

function resetPantryForNewVisit() {
  selectedFoodIds.clear();
  customFoods.clear();
  foodSearch.value = "";
  customFoodName.value = "";
  customFoodStatus.textContent = "";
  customFoodStatus.className = "form-status";
  pickerStatus.textContent = "";
  pickerStatus.className = "form-status";
  if (foodPicker.open) foodPicker.close();
  renderSelectedFoods();
  renderFoodOptions();
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

document.querySelector("#open-food-picker").addEventListener("click", () => {
  pickerStatus.textContent = "";
  foodSearch.value = "";
  renderFoodOptions();
  foodPicker.showModal();
  foodSearch.focus();
});

document.querySelector("#close-food-picker").addEventListener("click", () => {
  foodPicker.close();
});

foodSearch.addEventListener("input", renderFoodOptions);

customFoodForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = customFoodName.value.trim();
  const normalizedName = name.toLocaleLowerCase();
  if (!name) {
    customFoodStatus.textContent = "Enter a food name to add.";
    customFoodStatus.className = "form-status error";
    return;
  }
  if (
    [...foodsById.values()].some(
      (food) => food.name.trim().toLocaleLowerCase() === normalizedName,
    )
  ) {
    customFoodStatus.textContent = "This food is already in the food list. Search and select it above.";
    customFoodStatus.className = "form-status error";
    return;
  }
  if (customFoods.has(normalizedName)) {
    customFoodStatus.textContent = "This food is already in your pantry.";
    customFoodStatus.className = "form-status error";
    return;
  }

  customFoods.set(normalizedName, name);
  customFoodName.value = "";
  customFoodStatus.textContent = `${name} added to your pantry.`;
  customFoodStatus.className = "form-status success";
  renderSelectedFoods();
});

document.querySelector("#add-selected-foods").addEventListener("click", () => {
  const additions = [
    ...foodPickerOptions.querySelectorAll(
      'input[name="food-picker-selection"]:checked',
    ),
  ];
  additions.forEach((checkbox) => selectedFoodIds.add(checkbox.value));
  renderSelectedFoods();
  renderFoodOptions();
  pickerStatus.textContent = additions.length
    ? `${additions.length} food${additions.length === 1 ? "" : "s"} added.`
    : "Choose at least one food to add.";
  if (additions.length) pickerStatus.className = "form-status success";
  else pickerStatus.className = "form-status";
});

profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (selectedFoodIds.size === 0) {
    profileStatus.textContent = "Add at least one food from your kitchen before generating a plan.";
    profileStatus.className = "form-status error";
    return;
  }

  profileStatus.textContent = "Preparing your food plan…";
  profileStatus.className = "form-status";
  submitProfileButton.disabled = true;
  submitProfileButton.textContent = "Preparing your plan…";
  try {
    const formData = new FormData(profileForm);
    const result = await window.apiClient.post("/api/agent/recommend", {
      profile: makeProfile(formData),
      available_food_ids: [...selectedFoodIds],
    });
    window.localStorage.setItem(
      "bhojon-food-plan",
      JSON.stringify({ result, generatedAt: new Date().toISOString() }),
    );
    window.location.assign("/plan");
  } catch (error) {
    profileStatus.textContent =
      error instanceof Error
        ? error.message
        : "Could not generate the plan. Please try again.";
    profileStatus.className = "form-status error";
  } finally {
    submitProfileButton.disabled = false;
    submitProfileButton.innerHTML = 'Generate my plan <span aria-hidden="true">→</span>';
  }
});

async function loadFoodCatalog() {
  try {
    const foods = await window.apiClient.get("/api/foods");
    foodsById.clear();
    foods.forEach((food) => foodsById.set(food.id, food));
    renderSelectedFoods();
    renderFoodOptions();
  } catch (error) {
    profileStatus.textContent =
      error instanceof Error
        ? error.message
        : "Food options could not be loaded. Please refresh and try again.";
    profileStatus.className = "form-status error";
    document.querySelector("#open-food-picker").disabled = true;
    document.querySelector("#submit-profile").disabled = true;
  }
}

window.addEventListener("pageshow", (event) => {
  if (!event.persisted) return;
  resetPantryForNewVisit();
  profileStatus.textContent = "";
  profileStatus.className = "form-status";
  loadFoodCatalog();
});

loadFoodCatalog();

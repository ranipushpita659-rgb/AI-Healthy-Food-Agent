# API Contract

The API is served under `/api`; interactive OpenAPI documentation is available
at `/docs`.

## Health and food data

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Returns `{"status":"ok"}`. |
| `GET` | `/api/foods?category=fruit&tag=vegan` | Lists validated foods; category and tag filters are optional and exact. |

## Profile, calculations, and meal plans

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/profile/validate` | Validates profile input without saving it. |
| `POST` | `/api/profiles` | Saves a profile; returns `profile_id` and `created_at` (201). |
| `POST` | `/api/nutrition/bmi` | Calculates BMI without interpreting it as a diagnosis. |
| `POST` | `/api/nutrition/calories` | Returns adult calorie ranges and calculation assumptions. |
| `POST` | `/api/nutrition/analyze` | Sums dataset nutrition values for food IDs and servings. |
| `POST` | `/api/meals/generate` | Generates a deterministic four-slot plan and saves its profile/plan snapshot. |
| `GET` | `/api/profiles/{profile_id}/meal-plans` | Returns saved plan history for the profile ID. |
| `POST` | `/api/profiles/{profile_id}/weight-records` | Saves an optional weight measurement (201). |
| `GET` | `/api/profiles/{profile_id}/weight-records` | Lists the profile's weight measurements. |

Profile payload used by the profile, calorie, meal-plan, and agent routes:

```json
{
  "age": 30,
  "gender": "female",
  "height_cm": 165,
  "weight_kg": 60,
  "activity_level": "moderate",
  "health_goal": "maintain_weight",
  "food_preferences": ["vegetarian"],
  "excluded_foods": ["peanuts"]
}
```

For meal-plan requests, `available_foods` is an optional top-level field. It
accepts `rice`, `bread`, `oats`, `egg`,
`chicken`, `fish`, `potato`, `tomato`, `carrot`, `spinach`, `milk`, `yogurt`,
`banana`, `apple`, `orange`, `lentils`, `beans`, and `nuts`. When omitted or
empty, no availability filter is applied. Selected items only match foods in
the current structured dataset.

The profile form uses `POST /api/agent/recommend`, which accepts this object as
`profile` and an optional `daily_calorie_target` (500–10000 kcal). The response
includes `summary`, `meal_plan`, `bmi`, `calorie_estimate`, food-ID-linked
`reasons`, `assumptions`, `safety_note`, `source` (`llm` or `deterministic`),
and an optional fallback `message`. The nested plan includes meal slots,
selected food IDs, per-slot and daily nutrition totals, and persisted IDs.

Agent request example:

```json
{
  "profile": {
    "age": 30,
    "gender": "female",
    "height_cm": 165,
    "weight_kg": 60,
    "activity_level": "moderate",
    "health_goal": "maintain_weight",
    "food_preferences": [],
    "excluded_foods": []
  },
  "available_foods": ["rice", "egg", "banana", "apple"],
  "daily_calorie_target": 2000
}
```

## Validation and failures

- `422`: invalid input, an adult-only estimate requested for a minor, or no
  eligible foods for one or more meal slots. Validation details use FastAPI's
  `detail` field; missing meal slots include a `missing_meals` list.
- `404`: unknown food ID during nutrition analysis or an unknown profile ID in
  history/weight routes.
- `500`: dataset or database failure; response details are generic and server
  logs hold diagnostics.
- An unavailable LLM is not an API error: the recommendation endpoint returns
  the deterministic plan with `source: "deterministic"` and a message.

All profile, meal-plan, and weight endpoints are unauthenticated. Do not expose
them publicly.

# Test Cases

Run the automated suite from the repository root with:

```powershell
python -m pytest -q
```

The tests cover:

| Area | Coverage |
| --- | --- |
| BMI and calorie estimates | Known values, formula assumptions, invalid measurements, and adult-only boundaries. |
| Food dataset and nutrition | Valid/invalid JSON, duplicate IDs, USDA provenance, complete nutrient values, catalog-backed food picker, serving totals, and exact filters. |
| Meal planning | Four multi-food slots, catalog-ID pantry limits, portion caps, calorie target fallback, vegetarian/vegan/Halal filters, allergies/exclusions, and missing matches. |
| API validation | Health endpoint, missing/invalid profile fields, calculations, foods, nutrition, and meal-plan errors. |
| Persistence | Profile/plan/weight writes, history, and records surviving a new SQLAlchemy session. |
| Agent integration | Missing credentials, Gemini/OpenAI provider failures, provider timeout, invalid/unselected food IDs, valid constrained explanation, and persisted API result. |

Manual UI checks:

1. Start the server and open <http://127.0.0.1:8000>.
2. Open **Create a plan**, add a food from the picker, and submit an adult
   profile. Verify the plan page shows meals beside nutrition totals.
3. Use **Download PDF** and choose **Save as PDF** in the browser print dialog.
4. Exclude foods or choose a preference that has no dataset matches; verify a
   readable error and missing-slot details.
5. Leave LLM credentials blank; verify the meal plan is still shown.
6. Log different drink amounts, reload to verify today's total persists, and
   undo the last entry. Verify a different date shows a separate daily total.
7. Narrow the browser window and verify the layout remains usable.

The water log is stored in browser localStorage, so it remains on that browser
and device but does not sync to other devices.
The project has no authentication; use synthetic profiles in shared environments.

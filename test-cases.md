# Test Cases

Run the automated suite from the repository root with:

```powershell
python -m pytest -q
```

The tests cover:

| Area | Coverage |
| --- | --- |
| BMI and calorie estimates | Known values, formula assumptions, invalid measurements, and adult-only boundaries. |
| Food dataset and nutrition | Valid/invalid JSON, duplicate IDs, USDA provenance, complete nutrient values, all UI options mapped, serving totals, and exact filters. |
| Meal planning | Four meal slots with non-rice ingredients, calorie target fallback, vegetarian/vegan/Halal filters, allergies/exclusions, missing matches, and an empty catalog. |
| API validation | Health endpoint, missing/invalid profile fields, calculations, foods, nutrition, and meal-plan errors. |
| Persistence | Profile/plan/weight writes, history, and records surviving a new SQLAlchemy session. |
| Agent integration | Missing credentials, Gemini/OpenAI provider failures, provider timeout, invalid/unselected food IDs, valid constrained explanation, and persisted API result. |

Manual UI checks:

1. Start the server and open <http://127.0.0.1:8000>.
2. Submit an adult profile and verify loading feedback, a saved plan, calorie
   estimate, meal slots, nutrition totals, and safety note.
3. Exclude foods or choose a preference that has no dataset matches; verify a
   readable error and missing-slot details.
4. Leave LLM credentials blank; verify the deterministic plan is still shown.
5. Start, change, and pause a water reminder; use the one-minute option to
   verify its live status while the page stays open. Reload and verify the
   counter and timer reset.
6. Narrow the browser window and verify the layout remains usable.

Water reminders are browser timers, so inactive-tab throttling may delay them.
The project has no authentication; use synthetic profiles for any shared demo.

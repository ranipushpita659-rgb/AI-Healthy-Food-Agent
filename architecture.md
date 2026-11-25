# Architecture

## Request flow

```text
Browser
  ├─ index.html (landing page)
  ├─ planner.html ── api.js ── GET /api/foods, POST /api/agent/recommend
  ├─ plan.html (plan + nutrition, print-to-PDF)
  └─ wellbeing.html ── water-reminder.js ── browser localStorage (daily water log)
                            └─ page-local reminder timer
                            ├─ Pydantic request validation
                            ├─ deterministic BMI/calorie/meal-plan services
                            ├─ optional constrained LLM explanation
                            └─ profile + plan repository ── SQLite
```

FastAPI serves the landing, pantry, plan, and wellbeing pages at `/`,
`/planner`, `/plan`, and `/wellbeing`; CSS and JavaScript are served from
`/static`. The browser does not contain LLM credentials.

## Backend boundaries

- `app/schemas/` validates requests and response shapes.
- `app/services/` owns deterministic calculations, meal selection, and the
  optional LLM explanation.
- `app/data/food_repository.py` loads and validates the versioned JSON food
  catalog, including per-record USDA provenance and Halal status.
- `app/data/database_repository.py` owns persistence operations.
- `app/db/` defines SQLAlchemy models, the engine/session, and startup schema
  creation.
- `app/api/routes/` translates HTTP requests into service/repository calls.

The agent service first calculates BMI/calorie estimates and generates a
deterministic plan. It sends only a compact goal/preferences summary, calculated
values, and selected dataset foods to Google Gemini through `google-genai`, or to
an optional OpenAI-compatible provider.
The LLM may explain those foods but cannot add or replace food IDs. Missing
credentials, provider failures, and malformed or ungrounded output return the
deterministic plan with an explicit fallback message.

## Persistence model

`profiles` stores validated profile snapshots. `meal_plans` stores a JSON
snapshot and references its profile. `weight_records` stores optional dated
measurements. SQLite tables are created at application startup with
`Base.metadata.create_all`; schema migrations are not currently provided.

## Privacy and deployment

No names, email addresses, or persistent identifiers are sent to the LLM.
Profile and weight values are still sensitive; local SQLite is unencrypted and
the API has no authentication. Treat this as a local learning project, not a
production service.

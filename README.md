# Bhojon — AI Healthy Food Agent

A Bangladesh-focused meal-planning web app for adults. Bhojon combines validated
profile input, deterministic calorie and nutrition calculations, a structured
food catalog, optional AI explanations, and local SQLite persistence.

## Run locally (Windows PowerShell)

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` if you want to enable LLM explanations:

```dotenv
LLM_API_KEY=
LLM_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_SECONDS=10
```

Gemini is used through the official `google-genai` Python SDK. OpenAI-compatible
providers remain supported by setting `LLM_PROVIDER=openai`.
If `LLM_API_KEY` or `LLM_MODEL` is missing, or the provider fails, the app still
returns the deterministic plan and marks the AI explanation unavailable. Keep
real credentials only in the ignored `.env` file; never put them in frontend
code.

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title | `Bhojon | Healthy Food Planner` |
| `ENVIRONMENT` | Environment label | `development` |
| `DATABASE_URL` | SQLAlchemy database connection | `sqlite:///./ai_healthy_food_agent.db` |
| `LLM_API_KEY` | Server-side provider credential | Empty (deterministic fallback) |
| `LLM_MODEL` | Gemini or OpenAI model name | `gemini-2.5-flash` |
| `LLM_PROVIDER` | LLM backend | `gemini` |
| `LLM_BASE_URL` | OpenAI-compatible API root | `https://api.openai.com/v1` |
| `LLM_TIMEOUT_SECONDS` | Provider request timeout | `10` |

For real Gemini explanations:

1. Create a Gemini API key in Google AI Studio.
2. Put only the key in the local `.env` file; never commit `.env`.
3. Set `LLM_PROVIDER=gemini`, `LLM_MODEL=gemini-2.5-flash`, and the API key.
4. Restart the FastAPI server.
5. Generate a plan through the browser or `POST /api/agent/recommend`.
6. Verify that the JSON response contains `"source": "llm"` and a non-empty
   Gemini summary/reasons. `"source": "deterministic"` means the provider call
   was unavailable or failed.

Invalid keys, unsupported models, quota exhaustion, network failures, malformed
responses, and ungrounded food IDs are handled as deterministic fallbacks.

Start the app and open its browser UI:

```powershell
python -m uvicorn app.main:app --reload
```

- Landing page: <http://127.0.0.1:8000>
- Create a plan: <http://127.0.0.1:8000/planner>
- View a plan: <http://127.0.0.1:8000/plan>
- Wellbeing: <http://127.0.0.1:8000/wellbeing>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/health>

Open the app through FastAPI rather than `file://`; its pages use the
FastAPI-served `/api` and `/static` paths.

## Using the app

1. Select **Create a plan**, then enter your adult profile, activity level, and
   goal.
2. Review the starter pantry, add foods you have available, and set any food
   preferences or exclusions.
3. Generate your plan to review meals beside calorie and nutrition estimates.
   The plan and profile are saved locally.
4. Select **Download PDF** and choose **Save as PDF** in your browser's print
   dialog to keep a clean copy of the plan.
5. Use **Wellbeing** to log drink amounts for today and optionally set an
   on-page water reminder.

The daily water log is saved in this browser on this device and remains after
the page is reloaded. Browser background-tab throttling may delay reminders;
they do not run after the page is closed.

## Tests

With the virtual environment active:

```powershell
python -m pytest -q
```

See [test-cases.md](./test-cases.md) for the coverage map.

## API and architecture

- Endpoint methods and request/response examples: [api-contract.md](./api-contract.md)
- Component boundaries and request flow: [architecture.md](./architecture.md)
- Food records: `app/data/foods.json`
- API schemas: `app/schemas/`
- Deterministic calculations and planning: `app/services/`

## Persistence

`DATABASE_URL` defaults to `sqlite:///./ai_healthy_food_agent.db`. The app
applies Alembic migrations on startup:

- `profiles`: validated profile snapshots with no names or email addresses.
- `meal_plans`: generated plan snapshots associated with a profile.
- `weight_records`: optional measurements associated with a profile.

For local development, run from the project root so the relative SQLite path is
predictable. The database is ignored by Git. This project has no authentication;
do not expose it publicly or use it for production health data.

## Database migrations

Migrations use Alembic and SQLAlchemy. The safe baseline migration preserves
existing SQLite tables and records; it creates missing application tables only
for fresh or partially initialized databases. It never deletes existing rows.

Install dependencies and run migrations from the project root:

```powershell
python -m pip install -r requirements.txt
python -m alembic upgrade head
```

Useful project commands:

```powershell
python -m app.db.migrations upgrade
python -m app.db.migrations current
python -m app.db.migrations history
python -m app.db.migrations downgrade
python -m app.db.migrations downgrade 0001_baseline
```

Alembic-compatible commands are also available directly:

```powershell
python -m alembic revision --autogenerate -m "describe schema change"
python -m alembic upgrade head
python -m alembic current
python -m alembic history
python -m alembic downgrade -1
```

Review every generated migration before applying it. The baseline downgrade is
intentionally non-destructive and does not remove application tables or records.

## Limitations

- BMI and Mifflin-St Jeor calorie values are estimates for adults, not diagnosis,
  treatment, or an individualized prescription. They are not intended for
  people under 18, pregnant, or breastfeeding.
- Food nutrition values are per 100 g and link to USDA FoodData Central records.
  Bangladesh-familiar staples are included alongside general foods; meal
  recommendations are limited to the foods selected in the pantry.
  Dietary tags are dataset classifications; verify product ingredients and
  allergen information. The catalog is not a substitute for product labels.
- Food values are estimates for the catalogued ingredients; preparations such
  as curries, frying, and added oil can change the final nutrition.
- Halal filtering accepts ingredient-permissible items and explicitly verified
  items. Meat without a verified Halal source is marked unknown and excluded
  when the Halal preference is selected.
- The LLM is limited to explaining foods already selected by the deterministic
  planner. It does not calculate authoritative nutrition values.
- The reminder is an in-page timer and is not a background notification or
  medical hydration target.
- The API has no user authentication or authorization. Add appropriate access
  controls before exposing it beyond a trusted local environment.

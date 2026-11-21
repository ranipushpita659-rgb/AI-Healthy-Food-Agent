# AI Healthy Food Agent

A browser-based educational demo for adult meal planning. It combines validated
profile input, deterministic calorie and nutrition calculations, a structured
food dataset, optional LLM explanations, and local SQLite persistence.

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
| `APP_NAME` | FastAPI application title | `AI Healthy Food Agent` |
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

- Dashboard: <http://127.0.0.1:8000>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/health>

Do not open `frontend/index.html` directly with `file://`; the page uses the
FastAPI-served `/api` and `/static` paths.

## Demo

1. Fill in the adult profile, goal, available food items, preferences, and any
   foods to exclude. Selected available foods constrain the generated plan; if
   none are selected, the planner can use the full catalog.
2. Select **Generate meal plan**.
3. Review the estimated calorie range, generated meal slots, nutrition totals,
   assumptions, and safety notes. The plan and profile are saved locally.
4. In the Water Reminder panel, choose an interval and start/pause the on-page
   reminder. Log a glass to update the temporary counter.

The water counter and timer exist only in the current open page. Browser
background-tab throttling may delay reminders; they do not run after the page is
closed or reloaded.

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

For a local demo, run from the project root so the relative SQLite path is
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
- Recommendations depend on the small structured dataset. Verify ingredients
  and allergen information; dataset gaps can make a requested plan unavailable.
- The LLM is limited to explaining foods already selected by the deterministic
  planner. It does not calculate authoritative nutrition values.
- The reminder is an in-page timer and is not a background notification or
  medical hydration target.
- The API has no user authentication or authorization and is for local
  demonstration only.

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
LLM_MODEL=
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT_SECONDS=10
```

The configured service must support the OpenAI-compatible chat-completions API.
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
| `LLM_MODEL` | Provider model name | Empty (deterministic fallback) |
| `LLM_BASE_URL` | OpenAI-compatible API root | `https://api.openai.com/v1` |
| `LLM_TIMEOUT_SECONDS` | Provider request timeout | `10` |

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
creates these tables on startup:

- `profiles`: validated profile snapshots with no names or email addresses.
- `meal_plans`: generated plan snapshots associated with a profile.
- `weight_records`: optional measurements associated with a profile.

For a local demo, run from the project root so the relative SQLite path is
predictable. The database is ignored by Git. This project has no authentication
or migrations; do not expose it publicly or use it for production health data.

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

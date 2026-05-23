# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run / Develop

The canonical dev loop is Docker Compose — it builds both services and wires the frontend to the backend via the `API_URL` env var.

```bash
docker compose up --build          # backend :8000, frontend :8501
docker compose down                # tear down
```

Backend startup downloads the full MPSV unemployment dataset (~100MB) into in-memory cache before serving requests. Expect ~10–30s before `/nezamestnanost` returns real data; until then it returns `{"error": "Data is loading..."}`.

The backend runs with `--reload` (set in `docker-compose.yml`, not the Dockerfile), so edits to `backend/` hot-reload. The frontend mounts `./social_atlas` as a volume and reinstalls requirements on each container start.

To run the Streamlit app outside Docker (against a separately-running backend), `cd social_atlas && streamlit run app.py`. Without `API_URL` set, pages default to `http://localhost:8000`.

There are no tests, linters, or build steps configured.

## Architecture

Two-tier app for visualizing social indicators across the 7 ORP municipalities of the Czech Ústecký Region (Most, Chomutov, Ústí nad Labem, Teplice, Děčín, Litoměřice, Louny).

### Backend (`backend/`) — FastAPI

The cache-and-serve pattern is central:

- `store.py` exposes a single module-level dict `data_cache`.
- `main.py` declares a `DATA_SOURCES` dict (name → URL). On FastAPI startup, every URL is fetched once and loaded into `data_cache[name]` as a `pd.DataFrame`. **All routers read from this cache** — they do not re-fetch.
- Each dataset gets its own router file (currently only `nezamestnanost.py`) that defines an `APIRouter`, is imported in `main.py`, and registered via `app.include_router(...)`.
- Routers do heavy pandas work per-request (filter to Ústecký kraj, rename columns to the frontend's vocabulary — `okres→orp`, `uchazec_pohlavi→gender`, etc., then groupby+agg). The shape returned to the frontend is the *aggregated* shape, not the raw MPSV shape.

**Adding a new dataset** means: (1) add a URL to `DATA_SOURCES` in `main.py`, (2) create a new router module that reads `data_cache[<name>]`, (3) `include_router` it in `main.py`.

### Frontend (`social_atlas/`) — Streamlit multi-page

- `app.py` is the overview/landing page and owns the sidebar (ORP multiselect + year-range slider). Filters are written to `st.session_state` under keys `filter_orp` and `filter_years` and **every page re-reads them** via its own local `filter_data()` helper — there is no shared filter module, so changes to filter behavior must be replicated.
- Streamlit auto-discovers `pages/NN_name.py` for the left nav. Files are numbered to control order.
- Sub-pages do `sys.path.insert(0, ...)` so they can import sibling packages (`data.mock_data`, `components.*`). Preserve this when adding new pages.
- The ORP color palette is duplicated in `components/bar_chart_orp.py` and individual page files — keep them in sync if changing colors.

### Mock vs. real data — the in-progress migration

This is the most important thing to know before editing pages: **the codebase is mid-migration from mock data to the real backend API**, and only some pages have been switched.

- `social_atlas/data/mock_data.py` defines `get_unemployment`, `get_debt_enforcement`, `get_housing_benefits`, `get_demographics`, `get_excluded_localities`, `get_crime`, `get_care`. All return seeded synthetic DataFrames with a stable schema (`year`, `orp`, plus indicator-specific columns).
- `app.py` and most pages still call these mock functions directly.
- `pages/01_unemployment.py` calls the real backend (`GET /nezamestnanost`) and contains a "data bridge" block that renames raw MPSV columns to the mock schema. When the backend route already returns the aggregated/renamed shape (which `nezamestnanost.py` now does), that bridge is dead code — be aware before editing.
- The intended contract: backend endpoints return rows matching the mock schema (`year`, `orp`, `value`, etc.), so a page can swap `from data.mock_data import get_X` for a `requests.get(f"{API_URL}/X")` call with minimal changes.

When wiring up a new real endpoint, match the column names in `mock_data.py` for that indicator — the components (`bar_chart_orp`, `trend_chart`) and overview KPIs expect them.

## Deployment

`main` auto-deploys to a Hugging Face Space via `.github/workflows/sync_to_hub.yml` (force-push to `huggingface.co/spaces/falconizmi/Socialni-atlas-Usteckeho-kraje`). The Space runs Streamlit only, using `app.py` per the YAML frontmatter in `README.md` — the FastAPI backend is **not** deployed there, so pages that depend on `API_URL` will fail in the Space unless they fall back to mock data.

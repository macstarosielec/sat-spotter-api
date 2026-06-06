# sat-spotter-api

FastAPI backend for satellite pass prediction. Serves the sat-spotter Flutter app
with pass predictions, trajectory data, and satellite information. Wraps the same
skyfield computation used by the `sat-spotter` CLI.

Stateless by design: no database, no auth — the client sends satellite IDs and a
location per request. TLEs are fetched from Celestrak and cached on disk.

## Requirements

- Python 3.12+

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
uvicorn sat_spotter_api.main:app --reload
```

Interactive API docs: http://localhost:8000/docs

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/satellites/search?name=<query>` | Search Celestrak by name |
| GET | `/satellites/catalog` | Curated list of featured satellites |
| GET | `/satellites/{norad_id}` | Satellite info (orbit type, inclination, TLE epoch) |
| GET | `/passes?lat=&lon=&norad_ids=&hours=&elev=&visible_only=` | Predict passes |
| GET | `/passes/trajectory?lat=&lon=&norad_id=&rise_time=&set_time=` | Sky-chart trajectory points |

See `../project/api/features.md` for full request/response details.

## Configuration

All settings have sensible defaults and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `SAT_SPOTTER_DATA_DIR` | `<package>/data` | Location of the TLE cache and `catalog.json` |
| `SAT_SPOTTER_CACHE_TTL` | `14400` | TLE cache lifetime, seconds (4h) |
| `SAT_SPOTTER_HTTP_TIMEOUT` | `8.0` | Celestrak read timeout, seconds |
| `SAT_SPOTTER_MAX_NORAD_IDS` | `50` | Max NORAD IDs per `/passes` request |
| `SAT_SPOTTER_CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |

The featured-satellite list is read from `data/catalog.json` — edit that file to
change it (no code change needed).

## Development

```bash
ruff check src/ tests/   # lint
pytest -q                # run the test suite
```

## Project layout

```
src/sat_spotter_api/
├── main.py            # FastAPI app + CORS
├── config.py          # env-overridable settings
├── models.py          # Pydantic response models
├── routers/           # HTTP endpoints (satellites, passes)
└── core/              # skyfield computation (tle, passes, predict, visibility, ...)
tests/                 # endpoint + core unit tests (Celestrak mocked)
```

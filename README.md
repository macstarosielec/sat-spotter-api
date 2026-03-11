# sat-spotter-api

FastAPI backend for satellite pass prediction. Serves the sat-spotter Flutter app with pass predictions, trajectory data, and satellite information.

## Setup

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running

```bash
uvicorn sat_spotter_api.main:app --reload
```

API docs available at http://localhost:8000/docs

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/satellites/search` | Search Celestrak for satellites |
| GET | `/satellites/{norad_id}` | Satellite info |
| GET | `/passes` | Predict passes for given satellites and location |
| GET | `/passes/{pass_id}/trajectory` | Trajectory points for sky chart |

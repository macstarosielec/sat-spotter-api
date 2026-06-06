from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sat_spotter_api.models import HealthResponse
from sat_spotter_api.routers import passes, satellites

app = FastAPI(title="Sat-Spotter API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # MVP: open during development; restrict to the app origin before production.
    allow_origins=["*"],
    allow_methods=["GET"],  # API is read-only
    allow_headers=["*"],
)

app.include_router(satellites.router)
app.include_router(passes.router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")

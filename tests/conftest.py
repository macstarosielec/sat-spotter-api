import httpx
import pytest
from fastapi.testclient import TestClient

from sat_spotter_api.main import app

# A realistic ISS TLE: mean motion ~15.5 rev/day -> ~92.9 min period -> LEO,
# inclination 51.64°. Used to drive the satellite endpoints deterministically.
ISS_TLE = (
    "ISS (ZARYA)\n"
    "1 25544U 98067A   24067.50000000  .00016717  00000-0  10270-3 0  9001\n"
    "2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.50000000123456\n"
)


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def iss_tle() -> str:
    return ISS_TLE


@pytest.fixture(autouse=True)
def isolate_tle_cache(tmp_path, monkeypatch):
    """Point the TLE cache at a temp dir so tests never read or write the real cache."""
    monkeypatch.setattr("sat_spotter_api.core.tle.BASE_CACHE_DIR", tmp_path / "cache")


@pytest.fixture
def mock_celestrak(monkeypatch):
    """Install a fake Celestrak response. Patches httpx.get for both call sites
    (core.tle.fetch_tle and routers.satellites.search)."""

    def _install(text: str = "", *, error: bool = False) -> None:
        def fake_get(url, *args, **kwargs):
            if error:
                raise httpx.HTTPError("celestrak unavailable")
            return _FakeResponse(text)

        monkeypatch.setattr(httpx, "get", fake_get)

    return _install

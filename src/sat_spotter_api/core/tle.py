import time

import httpx
from skyfield.api import EarthSatellite, load

from sat_spotter_api.config import BASE_CACHE_DIR, DEFAULT_CACHE_DURATION, HTTP_TIMEOUT


def read_cache(norad_id: int) -> str | None:
    cache_file = BASE_CACHE_DIR / f"{norad_id}.tle"
    if cache_file.exists():
        data_age = time.time() - cache_file.stat().st_mtime
        if data_age < DEFAULT_CACHE_DURATION:
            return cache_file.read_text()
    return None


def write_cache(norad_id: int, data: str) -> None:
    BASE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = BASE_CACHE_DIR / f"{norad_id}.tle"
    cache_file.write_text(data)


def fetch_tle(norad_id: int) -> str | None:
    cached = read_cache(norad_id)
    if cached is not None:
        return cached

    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
    try:
        response = httpx.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        write_cache(norad_id, response.text)
        return response.text
    except httpx.HTTPError:
        return None


def parse_tle(tle_data: str | None) -> dict | None:
    if tle_data is None:
        return None
    lines = [line.strip() for line in tle_data.strip().splitlines()]
    if len(lines) < 3 or not lines[1].startswith("1 ") or not lines[2].startswith("2 "):
        return None
    return {"name": lines[0], "line1": lines[1], "line2": lines[2]}


def load_satellite(tle: dict | None) -> EarthSatellite | None:
    if tle is None:
        return None
    ts = load.timescale()
    return EarthSatellite(tle["line1"], tle["line2"], tle["name"], ts)


def orbital_params(line2: str) -> tuple[float, float]:
    """Parse inclination (degrees) and orbital period (minutes) from TLE line 2."""
    parts = line2.split()
    inclination = float(parts[2])
    mean_motion = float(parts[7])
    period_minutes = 1440.0 / mean_motion
    return inclination, period_minutes


def classify_orbit(inclination: float, period_minutes: float) -> str:
    """Derive orbit type (LEO/MEO/GEO/SSO/Other) from period and inclination."""
    if period_minutes < 128:
        orbit_type = "LEO"
    elif period_minutes < 800:
        orbit_type = "MEO"
    elif 1400 < period_minutes < 1500:
        orbit_type = "GEO"
    else:
        orbit_type = "Other"

    # Sun-synchronous: LEO + inclination 96-105°
    if orbit_type == "LEO" and 96 <= inclination <= 105:
        orbit_type = "SSO"
    return orbit_type

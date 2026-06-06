from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query

from sat_spotter_api.config import HTTP_TIMEOUT
from sat_spotter_api.core.catalog import load_catalog
from sat_spotter_api.core.tle import classify_orbit, fetch_tle, orbital_params, parse_tle
from sat_spotter_api.models import CatalogSatellite, SatelliteInfo, SatelliteSearchResult

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("/catalog", response_model=list[CatalogSatellite])
def get_catalog():
    return load_catalog()


@router.get("/search", response_model=list[SatelliteSearchResult])
def search_satellites(
    name: str = Query(..., min_length=2, max_length=80, pattern=r"^[A-Za-z0-9 .()\-+/]+$"),
):
    # Encode the user-supplied name so it can't inject extra query parameters;
    # the pattern above already rejects wildcards (e.g. "*") and separators.
    url = f"https://celestrak.org/NORAD/elements/gp.php?NAME={quote(name, safe='')}&FORMAT=TLE"
    try:
        response = httpx.get(url, timeout=HTTP_TIMEOUT, follow_redirects=False)
        response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Celestrak API unavailable")

    text = response.text.strip()
    if not text:
        return []

    lines = text.splitlines()
    results = []
    for i in range(0, len(lines) - 2, 3):
        sat_name = lines[i].strip()
        try:
            norad_id = int(lines[i + 1].split()[1].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            inclination, period_minutes = orbital_params(lines[i + 2])
        except (IndexError, ValueError):
            continue  # skip malformed TLE triples rather than 500
        orbit_type = classify_orbit(inclination, period_minutes)
        results.append(
            SatelliteSearchResult(norad_id=norad_id, name=sat_name, orbit_type=orbit_type)
        )
    return results


@router.get("/{norad_id}", response_model=SatelliteInfo)
def get_satellite(norad_id: int):
    tle_data = fetch_tle(norad_id)
    tle = parse_tle(tle_data)
    if tle is None:
        raise HTTPException(status_code=404, detail="Satellite not found")

    try:
        inclination, period_minutes = orbital_params(tle["line2"])
        epoch_year = int(tle["line1"][18:20])
        epoch_day = float(tle["line1"][20:32])
    except (IndexError, ValueError):
        raise HTTPException(status_code=502, detail="Malformed TLE data from upstream")

    orbit_type = classify_orbit(inclination, period_minutes)

    # TLE two-digit epoch year: 57-99 -> 1957-1999, 00-56 -> 2000-2056.
    full_year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
    epoch_dt = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)
    age_hours = (datetime.now(timezone.utc) - epoch_dt).total_seconds() / 3600

    return SatelliteInfo(
        norad_id=norad_id,
        name=tle["name"].strip(),
        orbit_type=orbit_type,
        inclination=round(inclination, 2),
        period_minutes=round(period_minutes, 1),
        tle_epoch=epoch_dt.isoformat(),
        tle_age_hours=round(age_hours, 1),
    )

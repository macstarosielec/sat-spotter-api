from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from sat_spotter_api.core.tle import classify_orbit, fetch_tle, orbital_params, parse_tle
from sat_spotter_api.models import SatelliteInfo, SatelliteSearchResult

router = APIRouter(prefix="/satellites", tags=["satellites"])


@router.get("/search", response_model=list[SatelliteSearchResult])
def search_satellites(name: str = Query(..., min_length=2)):
    url = f"https://celestrak.org/NORAD/elements/gp.php?NAME={name}&FORMAT=TLE"
    try:
        response = httpx.get(url)
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
        norad_id = int(lines[i + 1].split()[1].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        inclination, period_minutes = orbital_params(lines[i + 2])
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

    inclination, period_minutes = orbital_params(tle["line2"])
    orbit_type = classify_orbit(inclination, period_minutes)

    epoch_year = int(tle["line1"][18:20])
    epoch_day = float(tle["line1"][20:32])
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

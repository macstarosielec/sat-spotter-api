from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

from sat_spotter_api.core.tle import fetch_tle, parse_tle
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
        results.append(SatelliteSearchResult(norad_id=norad_id, name=sat_name))
    return results


@router.get("/{norad_id}", response_model=SatelliteInfo)
def get_satellite(norad_id: int):
    tle_data = fetch_tle(norad_id)
    tle = parse_tle(tle_data)
    if tle is None:
        raise HTTPException(status_code=404, detail="Satellite not found")

    line2_parts = tle["line2"].split()
    inclination = float(line2_parts[2])
    mean_motion = float(line2_parts[7])
    period_minutes = 1440.0 / mean_motion

    if period_minutes < 128:
        orbit_type = "LEO"
    elif period_minutes < 800:
        orbit_type = "MEO"
    elif 1400 < period_minutes < 1500:
        orbit_type = "GEO"
    else:
        orbit_type = "Other"

    # Check for sun-synchronous: LEO + inclination 96-105°
    if orbit_type == "LEO" and 96 <= inclination <= 105:
        orbit_type = "SSO"

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

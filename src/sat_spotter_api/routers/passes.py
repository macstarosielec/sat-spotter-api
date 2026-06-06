from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from sat_spotter_api.config import MAX_NORAD_IDS
from sat_spotter_api.core.passes import compute_all_passes, compute_trajectory, pass_to_response
from sat_spotter_api.models import PassPrediction, PassTrajectory

router = APIRouter(prefix="/passes", tags=["passes"])


@router.get("", response_model=list[PassPrediction])
def get_passes(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    norad_ids: str = Query(..., description="Comma-separated NORAD IDs"),
    hours: int = Query(24, ge=1, le=168),
    elev: int = Query(10, ge=0, le=90),
    visible_only: bool = Query(False),
):
    ids = []
    for part in norad_ids.split(","):
        part = part.strip()
        if not part.isdigit():
            raise HTTPException(status_code=400, detail=f"Invalid NORAD ID: {part}")
        ids.append(int(part))

    if not ids:
        raise HTTPException(status_code=400, detail="No NORAD IDs provided")

    if len(ids) > MAX_NORAD_IDS:
        raise HTTPException(
            status_code=400, detail=f"Too many NORAD IDs (max {MAX_NORAD_IDS})"
        )

    all_passes = compute_all_passes(lat, lon, hours, elev, ids)

    results = []
    for i, p in enumerate(all_passes):
        prediction = pass_to_response(i, p.norad_id, p)
        if visible_only and not prediction.is_visible:
            continue
        results.append(prediction)
    return results


@router.get("/trajectory", response_model=PassTrajectory)
def get_trajectory(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    norad_id: int = Query(...),
    rise_time: datetime = Query(...),
    set_time: datetime = Query(...),
):
    # Normalize to UTC so a mixed aware/naive pair can't raise on comparison.
    if rise_time.tzinfo is None:
        rise_time = rise_time.replace(tzinfo=timezone.utc)
    if set_time.tzinfo is None:
        set_time = set_time.replace(tzinfo=timezone.utc)

    if rise_time >= set_time:
        raise HTTPException(status_code=400, detail="rise_time must be before set_time")

    trajectory = compute_trajectory(lat, lon, norad_id, rise_time, set_time)
    if trajectory is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return trajectory

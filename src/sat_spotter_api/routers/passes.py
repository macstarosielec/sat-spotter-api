from fastapi import APIRouter, HTTPException, Query

from sat_spotter_api.core.passes import compute_all_passes, compute_trajectory, pass_to_response
from sat_spotter_api.models import PassPrediction, PassTrajectory

router = APIRouter(prefix="/passes", tags=["passes"])


@router.get("", response_model=list[PassPrediction])
def get_passes(
    lat: float = Query(...),
    lon: float = Query(...),
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

    all_passes = compute_all_passes(lat, lon, hours, elev, ids)

    results = []
    for i, p in enumerate(all_passes):
        norad_id = int(p.satellite.model.satnum)
        prediction = pass_to_response(i, norad_id, p)
        if visible_only and not prediction.is_visible:
            continue
        results.append(prediction)
    return results


@router.get("/{pass_id}/trajectory", response_model=PassTrajectory)
def get_trajectory(
    pass_id: int,
    lat: float = Query(...),
    lon: float = Query(...),
    norad_id: int = Query(...),
    rise_time: str = Query(...),
    set_time: str = Query(...),
):
    trajectory = compute_trajectory(lat, lon, norad_id, rise_time, set_time)
    if trajectory is None:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return trajectory

from types import SimpleNamespace

import pytest

from sat_spotter_api.models import PassPrediction, PassTrajectory, TrajectoryPoint

TRAJECTORY_PARAMS = {
    "lat": 52.0,
    "lon": 21.0,
    "norad_id": 25544,
    "rise_time": "2026-06-06T18:00:00+00:00",
    "set_time": "2026-06-06T18:10:00+00:00",
}


def _fake_pass(satnum: int = 25544) -> SimpleNamespace:
    """Stand-in for a SatellitePass: the router only reads .satellite.model.satnum."""
    return SimpleNamespace(satellite=SimpleNamespace(model=SimpleNamespace(satnum=satnum)))


def _prediction(index: int, norad_id: int, *, is_visible: bool) -> PassPrediction:
    return PassPrediction(
        id=index,
        name="ISS",
        norad_id=norad_id,
        rise_time="2026-06-06T18:00:00+00:00",
        set_time="2026-06-06T18:10:00+00:00",
        culmination_time="2026-06-06T18:05:00+00:00",
        max_elevation=45.0,
        rise_azimuth=215.0,
        set_azimuth=45.0,
        rise_direction="SW",
        set_direction="NE",
        duration_minutes=10.0,
        is_visible=is_visible,
    )


@pytest.fixture
def mock_passes(monkeypatch):
    """Mock the core compute layer (which wraps Celestrak + skyfield) so the
    router's parsing/filtering logic can be tested deterministically."""

    def _install(passes: list, visibility: list[bool]) -> None:
        monkeypatch.setattr(
            "sat_spotter_api.routers.passes.compute_all_passes",
            lambda *a, **k: passes,
        )
        monkeypatch.setattr(
            "sat_spotter_api.routers.passes.pass_to_response",
            lambda i, norad_id, p: _prediction(i, norad_id, is_visible=visibility[i]),
        )

    return _install


@pytest.fixture
def mock_trajectory(monkeypatch):
    def _install(result) -> None:
        monkeypatch.setattr(
            "sat_spotter_api.routers.passes.compute_trajectory",
            lambda *a, **k: result,
        )

    return _install


def test_get_passes_returns_predictions(client, mock_passes):
    mock_passes([_fake_pass(), _fake_pass()], visibility=[True, False])
    response = client.get(
        "/passes", params={"lat": 52.0, "lon": 21.0, "norad_ids": "25544"}
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["norad_id"] == 25544
    assert body[0]["id"] == 0


def test_get_passes_visible_only_filters(client, mock_passes):
    mock_passes([_fake_pass(), _fake_pass()], visibility=[True, False])
    response = client.get(
        "/passes",
        params={"lat": 52.0, "lon": 21.0, "norad_ids": "25544", "visible_only": "true"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["is_visible"] is True


def test_get_passes_invalid_norad_id_returns_400(client):
    response = client.get(
        "/passes", params={"lat": 52.0, "lon": 21.0, "norad_ids": "abc"}
    )
    assert response.status_code == 400


def test_get_passes_missing_lat_returns_422(client):
    response = client.get("/passes", params={"lon": 21.0, "norad_ids": "25544"})
    assert response.status_code == 422


def test_get_trajectory_returns_points(client, mock_trajectory):
    mock_trajectory(
        PassTrajectory(
            name="ISS",
            norad_id=25544,
            points=[TrajectoryPoint(azimuth_deg=215.4, altitude_deg=0.0)],
        )
    )
    response = client.get("/passes/0/trajectory", params=TRAJECTORY_PARAMS)
    assert response.status_code == 200
    body = response.json()
    assert body["norad_id"] == 25544
    assert len(body["points"]) == 1


def test_get_trajectory_not_found_returns_404(client, mock_trajectory):
    mock_trajectory(None)
    response = client.get("/passes/0/trajectory", params=TRAJECTORY_PARAMS)
    assert response.status_code == 404


def test_get_trajectory_missing_param_returns_422(client, mock_trajectory):
    mock_trajectory(None)
    response = client.get("/passes/0/trajectory", params={"lat": 52.0, "lon": 21.0})
    assert response.status_code == 422

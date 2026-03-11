from pydantic import BaseModel


class SatelliteInfo(BaseModel):
    norad_id: int
    name: str
    orbit_type: str
    inclination: float
    period_minutes: float
    tle_epoch: str
    tle_age_hours: float


class PassPrediction(BaseModel):
    id: int
    name: str
    norad_id: int
    rise_time: str
    set_time: str
    culmination_time: str
    max_elevation: float
    rise_azimuth: float
    set_azimuth: float
    rise_direction: str
    set_direction: str
    duration_minutes: float
    is_visible: bool


class TrajectoryPoint(BaseModel):
    azimuth_deg: float
    altitude_deg: float


class PassTrajectory(BaseModel):
    name: str
    norad_id: int
    points: list[TrajectoryPoint]


class SatelliteSearchResult(BaseModel):
    norad_id: int
    name: str


class HealthResponse(BaseModel):
    status: str

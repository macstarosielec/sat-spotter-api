from skyfield.api import EarthSatellite, load
from skyfield.toposlib import GeographicPosition

from sat_spotter_api.core.location import observer
from sat_spotter_api.core.predict import find_passes
from sat_spotter_api.core.tle import fetch_tle, load_satellite, parse_tle
from sat_spotter_api.core.visibility import is_visible
from sat_spotter_api.models import PassPrediction, PassTrajectory, SatellitePass, TrajectoryPoint

COMPASS_DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']


def degrees_to_compass(deg: float) -> str:
    index = round(deg / 45) % 8
    return COMPASS_DIRS[index]


def group_passes(
    times, satellite: EarthSatellite, location: GeographicPosition, min_elevation: float
) -> list[SatellitePass]:
    passes_list = []
    for i in range(0, len(times) - 2, 3):
        difference = satellite - location
        topocentric = difference.at(times[i + 1])
        alt, _, _ = topocentric.altaz()
        rise_topo = difference.at(times[i])
        _, rise_az, _ = rise_topo.altaz()
        set_topo = difference.at(times[i + 2])
        _, set_az, _ = set_topo.altaz()
        if alt.degrees > min_elevation:
            passes_list.append(SatellitePass(
                name=satellite.name,
                rise=times[i],
                culminate=times[i + 1],
                set=times[i + 2],
                elevation=alt.degrees,
                rise_azimuth=rise_az.degrees,
                set_azimuth=set_az.degrees,
                is_visible=is_visible(satellite, location, times[i + 1]),
                satellite=satellite,
                location=location,
            ))
    return passes_list


def compute_all_passes(
    lat: float, lon: float, hours: int, min_elevation: int, norad_ids: list[int]
) -> list[SatellitePass]:
    all_passes = []
    location = observer(lat, lon)
    for norad_id in norad_ids:
        satellite = load_satellite(parse_tle(fetch_tle(norad_id)))
        if satellite is None:
            continue
        times, _ = find_passes(satellite, location, hours)
        satellite_passes = group_passes(times, satellite, location, min_elevation)
        all_passes.extend(satellite_passes)
    all_passes.sort(key=lambda p: p.rise.tt)
    return all_passes


def pass_to_response(index: int, norad_id: int, pass_data: SatellitePass) -> PassPrediction:
    rise_dt = pass_data.rise.utc_datetime()
    set_dt = pass_data.set.utc_datetime()
    culmination_dt = pass_data.culminate.utc_datetime()
    duration = (set_dt - rise_dt).total_seconds() / 60

    return PassPrediction(
        id=index,
        name=pass_data.name,
        norad_id=norad_id,
        rise_time=rise_dt.isoformat(),
        set_time=set_dt.isoformat(),
        culmination_time=culmination_dt.isoformat(),
        max_elevation=round(pass_data.elevation, 1),
        rise_azimuth=round(pass_data.rise_azimuth, 1),
        set_azimuth=round(pass_data.set_azimuth, 1),
        rise_direction=degrees_to_compass(pass_data.rise_azimuth),
        set_direction=degrees_to_compass(pass_data.set_azimuth),
        duration_minutes=round(duration, 1),
        is_visible=pass_data.is_visible,
    )


def compute_trajectory(
    lat: float, lon: float, norad_id: int, rise_time: str, set_time: str
) -> PassTrajectory | None:
    satellite = load_satellite(parse_tle(fetch_tle(norad_id)))
    if satellite is None:
        return None

    location = observer(lat, lon)
    ts = load.timescale()
    t_rise = ts.from_datetime(
        __import__("datetime").datetime.fromisoformat(rise_time)
    )
    t_set = ts.from_datetime(
        __import__("datetime").datetime.fromisoformat(set_time)
    )

    time_array = ts.linspace(t_rise, t_set, 50)
    difference = satellite - location
    topocentric = difference.at(time_array)
    alt, az, _ = topocentric.altaz()

    points = [
        TrajectoryPoint(azimuth_deg=round(az.degrees[i], 2), altitude_deg=round(alt.degrees[i], 2))
        for i in range(len(az.degrees))
    ]

    return PassTrajectory(name=satellite.name, norad_id=norad_id, points=points)

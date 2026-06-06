from skyfield.api import EarthSatellite, Time
from skyfield.toposlib import GeographicPosition

from sat_spotter_api.core.loaders import get_ephemeris

TWILIGHT = -6.0


def is_sunlit(satellite: EarthSatellite, time: Time, ephemeris) -> bool:
    return satellite.at(time).is_sunlit(ephemeris)


def is_dark_enough(
    location: GeographicPosition, time: Time, ephemeris, sun_limit: float = TWILIGHT
) -> bool:
    earth = ephemeris['earth']
    sun = ephemeris['sun']
    observer = earth + location
    sun_alt = observer.at(time).observe(sun).apparent().altaz()[0]
    return sun_alt.degrees < sun_limit


def is_visible(satellite: EarthSatellite, location: GeographicPosition, time: Time) -> bool:
    ephemeris = get_ephemeris()
    return is_dark_enough(location, time, ephemeris) and is_sunlit(satellite, time, ephemeris)

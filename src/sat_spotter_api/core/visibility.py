from functools import lru_cache

from skyfield.api import EarthSatellite, Time, load
from skyfield.toposlib import GeographicPosition

TWILIGHT = -6.0


@lru_cache(maxsize=1)
def get_ephemeris():
    """Load the de421.bsp ephemeris once and reuse it across calls."""
    return load('de421.bsp')


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

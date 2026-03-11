from skyfield.api import wgs84
from skyfield.toposlib import GeographicPosition


def observer(lat: float, lon: float) -> GeographicPosition:
    return wgs84.latlon(lat, lon)

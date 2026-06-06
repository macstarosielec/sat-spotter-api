from skyfield.api import EarthSatellite
from skyfield.toposlib import GeographicPosition

from sat_spotter_api.core.loaders import get_timescale


def find_passes(satellite: EarthSatellite, location: GeographicPosition, hours: int) -> tuple:
    """Return (times, events) from Skyfield's find_events.

    events[i] is the event code at times[i]: 0=rise, 1=culminate, 2=set.
    """
    ts = get_timescale()
    t0 = ts.now()
    t1 = ts.tt_jd(t0.tt + hours / 24.0)
    return satellite.find_events(location, t0, t1)

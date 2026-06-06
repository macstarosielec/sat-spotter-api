from functools import lru_cache

from skyfield.api import Loader

from sat_spotter_api.config import DATA_DIR

# A single Skyfield loader rooted at the data dir, so the leap-second file and
# de421.bsp ephemeris resolve to a fixed location regardless of the process CWD.
_loader = Loader(str(DATA_DIR))


@lru_cache(maxsize=1)
def get_timescale():
    """Skyfield timescale, loaded once and reused (uses the builtin tables)."""
    return _loader.timescale()


@lru_cache(maxsize=1)
def get_ephemeris():
    """The de421.bsp ephemeris, loaded once and reused across requests."""
    return _loader("de421.bsp")

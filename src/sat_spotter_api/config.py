import os
from pathlib import Path

import httpx

# All settings can be overridden via environment variables so the API runs
# anywhere without code changes (see README "Configuration").

_data_dir_env = os.getenv("SAT_SPOTTER_DATA_DIR")
DATA_DIR = Path(_data_dir_env) if _data_dir_env else Path(__file__).parent.parent.parent / "data"
BASE_CACHE_DIR = DATA_DIR / "cache"
CATALOG_PATH = DATA_DIR / "catalog.json"

# TLE cache lifetime in seconds (default 4h, matching the CLI).
DEFAULT_CACHE_DURATION = int(os.getenv("SAT_SPOTTER_CACHE_TTL", str(4 * 3600)))

# Read timeout (seconds) for outbound Celestrak requests.
_read_timeout = float(os.getenv("SAT_SPOTTER_HTTP_TIMEOUT", "8.0"))
HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=_read_timeout, write=5.0, pool=5.0)

# Max number of NORAD IDs accepted in a single /passes request (DoS guard).
MAX_NORAD_IDS = int(os.getenv("SAT_SPOTTER_MAX_NORAD_IDS", "50"))

# Allowed CORS origins, comma-separated. Defaults to "*" for development.
CORS_ORIGINS = os.getenv("SAT_SPOTTER_CORS_ORIGINS", "*").split(",")

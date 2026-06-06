from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent.parent / "data"
BASE_CACHE_DIR = DATA_DIR / "cache"
CATALOG_PATH = DATA_DIR / "catalog.json"
DEFAULT_CACHE_DURATION = 4 * 3600

# Granular timeouts (seconds) for outbound Celestrak requests.
HTTP_TIMEOUT = httpx.Timeout(connect=5.0, read=8.0, write=5.0, pool=5.0)

# Max number of NORAD IDs accepted in a single /passes request (DoS guard).
MAX_NORAD_IDS = 50

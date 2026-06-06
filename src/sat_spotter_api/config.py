from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
BASE_CACHE_DIR = DATA_DIR / "cache"
CATALOG_PATH = DATA_DIR / "catalog.json"
DEFAULT_CACHE_DURATION = 4 * 3600

# Timeout (seconds) for outbound requests to Celestrak.
HTTP_TIMEOUT = 10.0

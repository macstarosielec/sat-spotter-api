import json

from sat_spotter_api.config import CATALOG_PATH


def load_catalog() -> list[dict]:
    """Load the curated catalog of featured satellites from disk.

    Returns an empty list if the catalog file is missing so the endpoint
    degrades gracefully instead of erroring.
    """
    if not CATALOG_PATH.exists():
        return []
    try:
        return json.loads(CATALOG_PATH.read_text())
    except json.JSONDecodeError:
        return []

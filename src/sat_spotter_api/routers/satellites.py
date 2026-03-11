from fastapi import APIRouter

router = APIRouter(prefix="/satellites", tags=["satellites"])


# TODO: GET /satellites/search?name=<query>

# TODO: GET /satellites/{norad_id}

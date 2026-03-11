from fastapi import APIRouter

router = APIRouter(prefix="/passes", tags=["passes"])


# TODO: GET /passes?lat=&lon=&hours=&elev=&norad_ids=

# TODO: GET /passes/{pass_id}/trajectory?lat=&lon=&norad_id=&rise_time=&set_time=

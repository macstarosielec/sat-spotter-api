def test_search_returns_parsed_results(client, mock_celestrak, iss_tle):
    mock_celestrak(iss_tle)
    response = client.get("/satellites/search", params={"name": "ISS"})
    assert response.status_code == 200
    body = response.json()
    assert body == [{"norad_id": 25544, "name": "ISS (ZARYA)", "orbit_type": "LEO"}]


def test_search_empty_response_returns_empty_list(client, mock_celestrak):
    mock_celestrak("")
    response = client.get("/satellites/search", params={"name": "NOPE"})
    assert response.status_code == 200
    assert response.json() == []


def test_search_celestrak_unavailable_returns_502(client, mock_celestrak):
    mock_celestrak(error=True)
    response = client.get("/satellites/search", params={"name": "ISS"})
    assert response.status_code == 502


def test_search_rejects_too_short_name(client):
    response = client.get("/satellites/search", params={"name": "a"})
    assert response.status_code == 422


def test_get_satellite_info(client, mock_celestrak, iss_tle):
    mock_celestrak(iss_tle)
    response = client.get("/satellites/25544")
    assert response.status_code == 200
    body = response.json()
    assert body["norad_id"] == 25544
    assert body["name"] == "ISS (ZARYA)"
    assert body["orbit_type"] == "LEO"
    assert body["inclination"] == 51.64
    assert body["period_minutes"] > 0
    assert "tle_epoch" in body
    assert "tle_age_hours" in body


def test_get_satellite_not_found_returns_404(client, mock_celestrak):
    mock_celestrak("")  # empty TLE -> parse_tle returns None -> 404
    response = client.get("/satellites/99999")
    assert response.status_code == 404


def test_catalog_returns_featured_satellites(client):
    response = client.get("/satellites/catalog")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert {"ISS"}.issubset({sat["name"] for sat in body})
    assert all("norad_id" in sat and "name" in sat for sat in body)

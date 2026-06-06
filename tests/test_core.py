import pytest

from sat_spotter_api.core.passes import degrees_to_compass, group_passes
from sat_spotter_api.core.tle import classify_orbit, orbital_params, parse_tle

VALID_TLE = (
    "ISS (ZARYA)\n"
    "1 25544U 98067A   24067.50000000  .00016717  00000-0  10270-3 0  9001\n"
    "2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.50000000123456\n"
)


# --- classify_orbit -------------------------------------------------------

@pytest.mark.parametrize(
    "inclination,period_minutes,expected",
    [
        (51.64, 92.9, "LEO"),
        (98.0, 98.0, "SSO"),       # LEO + inclination in the 96-105 sun-sync band
        (95.0, 100.0, "LEO"),      # just outside the SSO band -> stays LEO
        (55.0, 718.0, "MEO"),
        (0.05, 1436.0, "GEO"),
        (0.0, 1600.0, "Other"),
    ],
)
def test_classify_orbit(inclination, period_minutes, expected):
    assert classify_orbit(inclination, period_minutes) == expected


# --- orbital_params (fixed-width TLE columns) -----------------------------

def test_orbital_params_parses_iss_line2():
    line2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49309239256173"
    inclination, period_minutes = orbital_params(line2)
    assert round(inclination, 2) == 51.64
    assert round(period_minutes, 1) == 92.9


def test_orbital_params_excludes_revolution_number():
    # The mean-motion column (53-63) abuts the revolution number; column slicing
    # must not fold the trailing "12345" revolution count into the value.
    line2 = "2 25544  51.6400 247.4627 0006703 130.5360 325.0288 15.50000000123456"
    _, period_minutes = orbital_params(line2)
    assert period_minutes == pytest.approx(1440.0 / 15.5, abs=1e-6)


# --- parse_tle ------------------------------------------------------------

def test_parse_tle_valid():
    result = parse_tle(VALID_TLE)
    assert result is not None
    assert result["name"] == "ISS (ZARYA)"
    assert result["line1"].startswith("1 ")
    assert result["line2"].startswith("2 ")


def test_parse_tle_none_input():
    assert parse_tle(None) is None


def test_parse_tle_too_few_lines():
    assert parse_tle("ISS (ZARYA)\n1 25544U ...") is None


def test_parse_tle_bad_line_prefixes():
    assert parse_tle("line a\nline b\nline c") is None


# --- degrees_to_compass ---------------------------------------------------

@pytest.mark.parametrize(
    "degrees,expected",
    [
        (0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
        (180, "S"), (225, "SW"), (270, "W"), (315, "NW"),
        (350, "N"), (360, "N"),
    ],
)
def test_degrees_to_compass(degrees, expected):
    assert degrees_to_compass(degrees) == expected


# --- group_passes (event-aware pairing) -----------------------------------
# Lightweight fakes for the Skyfield objects group_passes touches, so the
# rise/culminate/set state machine can be tested without real propagation.

class _Angle:
    def __init__(self, degrees):
        self.degrees = degrees


class _Topocentric:
    def __init__(self, alt, az):
        self._alt, self._az = alt, az

    def altaz(self):
        return _Angle(self._alt), _Angle(self._az), None


class _Difference:
    def __init__(self, table):
        self._table = table

    def at(self, time):
        alt, az = self._table[time]
        return _Topocentric(alt, az)


class _Model:
    satnum = "25544"


class _FakeSatellite:
    name = "ISS (ZARYA)"
    model = _Model()

    def __init__(self, table):
        self._table = table

    def __sub__(self, other):  # satellite - location -> difference vector
        return _Difference(self._table)


def test_group_passes_assembles_complete_pass(monkeypatch):
    monkeypatch.setattr("sat_spotter_api.core.passes.is_visible", lambda *a, **k: True)
    times = [10, 11, 12]
    events = [0, 1, 2]  # rise, culminate, set
    table = {10: (0.0, 200.0), 11: (60.0, 100.0), 12: (0.0, 40.0)}
    result = group_passes(times, events, _FakeSatellite(table), None, min_elevation=10)
    assert len(result) == 1
    p = result[0]
    assert (p.rise, p.culminate, p.set) == (10, 11, 12)
    assert p.elevation == 60.0
    assert p.rise_azimuth == 200.0
    assert p.set_azimuth == 40.0
    assert p.norad_id == 25544
    assert p.name == "ISS (ZARYA)"
    assert p.is_visible is True


def test_group_passes_drops_partial_passes(monkeypatch):
    monkeypatch.setattr("sat_spotter_api.core.passes.is_visible", lambda *a, **k: False)
    # set with no preceding rise (window starts mid-pass), then a full triple,
    # then rise+culminate with no set (window ends mid-pass).
    times = [0, 1, 2, 3, 4, 5]
    events = [2, 0, 1, 2, 0, 1]
    table = {
        0: (50.0, 10.0), 1: (0.0, 210.0), 2: (70.0, 110.0),
        3: (0.0, 30.0), 4: (0.0, 200.0), 5: (80.0, 90.0),
    }
    result = group_passes(times, events, _FakeSatellite(table), None, min_elevation=10)
    assert len(result) == 1
    assert (result[0].rise, result[0].culminate, result[0].set) == (1, 2, 3)


def test_group_passes_filters_below_min_elevation(monkeypatch):
    monkeypatch.setattr("sat_spotter_api.core.passes.is_visible", lambda *a, **k: False)
    times = [0, 1, 2]
    events = [0, 1, 2]
    table = {0: (0.0, 200.0), 1: (8.0, 100.0), 2: (0.0, 40.0)}  # culmination 8° < 10°
    result = group_passes(times, events, _FakeSatellite(table), None, min_elevation=10)
    assert result == []

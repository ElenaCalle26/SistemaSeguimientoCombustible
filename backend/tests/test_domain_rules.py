from datetime import datetime, timezone
from types import SimpleNamespace

try:
    from app.main import analyze_operation
    from app.models import User
except ModuleNotFoundError:  # pytest invoked from the repository root
    from backend.app.main import analyze_operation
    from backend.app.models import User


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class _FakeDb:
    """The rule evaluator only needs the rows returned by its two windows."""

    def __init__(self, rows):
        self.rows = rows

    def scalars(self, _query):
        return _Rows(self.rows)


def test_third_fueling_is_prioritized_and_cross_station_is_explained():
    now = datetime.now(timezone.utc)
    operation = SimpleNamespace(
        id="current",
        vehicle_id="vehicle",
        station_id="station-b",
        occurred_at=now,
        quantity_liters=20,
    )
    previous = [
        SimpleNamespace(id="one", vehicle_id="vehicle", station_id="station-a"),
        SimpleNamespace(id="two", vehicle_id="vehicle", station_id="station-b"),
    ]

    codes = {code for code, _ in analyze_operation(operation, _FakeDb(previous))}

    assert {"SHORT_INTERVAL", "MULTI_STATION", "THIRD_FUELING"} <= codes


def test_supported_roles_are_exactly_the_three_operational_roles():
    assert set(User.__table__.c.role.type.enums) == {"ADMIN", "SUPERVISOR", "OPERATOR"}

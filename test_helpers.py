"""testing helpers.py"""
from datetime import datetime, timezone
from helpers import get_latest_value


def test_get_latest_value_empty_lists():
    """Testfall 1: timestamps und values sind beide leer"""
    timestamps = []
    values = []
    assert get_latest_value(timestamps, values) == (None, None)


def test_get_latest_value_empty_timestamps():
    """Testfall 2: timestamps ist leer, values hat Werte"""
    timestamps = []
    values = [10, 20, 30]
    assert get_latest_value(timestamps, values) == (None, None)


def test_get_latest_value_empty_values():
    """Testfall 3: timestamps hat Werte, values ist leer"""
    timestamps = [datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2023, 1, 1, tzinfo=timezone.utc)]
    values = []
    assert get_latest_value(timestamps, values) == (None, None)


def test_get_latest_value_same_length_ok():
    """Testfall 4.1: timestamps und values haben gleiche Länge"""
    timestamps = [
        datetime(2021, 1, 1, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 1, tzinfo=timezone.utc),
    ]
    values = [0, 10, 20]
    assert get_latest_value(timestamps, values) == (timestamps[2], values[2])


def test_get_latest_value_same_length_other_order_ok():
    """Testfall 4.2: timestamps und values haben gleiche Länge, andere Reihenfolge"""
    timestamps = [
        datetime(2023, 1, 1, tzinfo=timezone.utc),
        datetime(2022, 1, 1, tzinfo=timezone.utc),
        datetime(2021, 1, 1, tzinfo=timezone.utc),
    ]
    values = [0, 10, 20]
    assert get_latest_value(timestamps, values) == (timestamps[0], values[0])


def test_get_latest_value_more_timestamps():
    """Testfall 5: timestamps hat mehr Werte als values"""
    timestamps = [datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2023, 1, 1, tzinfo=timezone.utc)]
    values = [10]
    assert get_latest_value(timestamps, values) == (None, None)

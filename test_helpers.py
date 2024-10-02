"""testing helpers.py

Run the tests with coverage and generate HTML report
coverage run -m pytest test_main.py
coverage html
"""
from datetime import datetime, timezone

from helpers import (get_latest_value, get_same_calendar_week_day_one_year_ago, is_first_of_month, is_sunday, last_sunday)


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


def test_last_sunday_from_weekday():
    date = datetime(2023, 10, 4)  # Wednesday
    expected = datetime(2023, 10, 1, 23, 59)
    assert last_sunday(date) == expected


def test_last_sunday_from_sunday_expect_same():
    date = datetime(2024, 10, 6)  # Sunday
    expected = datetime(2024, 10, 6, 23, 59)
    assert last_sunday(date) == expected


def test_is_first_of_month():
    assert is_first_of_month(datetime(2023, 10, 1))
    assert not is_first_of_month(datetime(2023, 10, 2))


def test_is_sunday():
    assert is_sunday(datetime(2023, 10, 1))  # Sunday
    assert not is_sunday(datetime(2023, 10, 2))  # Monday


def test_get_same_calendar_week_day_one_year_ago():
    date = datetime(2023, 10, 4)  # Wednesday
    expected = datetime(2022, 10, 5)  # Same weekday one year ago
    assert get_same_calendar_week_day_one_year_ago(date) == expected

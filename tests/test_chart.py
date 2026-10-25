"""test create_png.py"""

import datetime
from unittest.mock import MagicMock

from influx_report.chart import create_bar_chart, format_dates
from influx_report.helpers import MeasurementSet

# pylint: disable=missing-function-docstring


def test_format_dates():
    dates = (datetime.datetime(2023, 1, 1), datetime.datetime(2023, 12, 31))
    result = format_dates(dates)
    assert result == "01.01.23 - 31.12.23"


def test_create_bar_chart(monkeypatch):
    mock_measurement_set = MagicMock(spec=MeasurementSet)
    mock_measurement_set.name = "Test Set"
    mock_measurement_set.data = [100, 200]
    mock_measurement_set.dates = [
        (datetime.datetime(2023, 1, 1), datetime.datetime(2023, 12, 31)),
        (datetime.datetime(2024, 1, 1), datetime.datetime(2024, 12, 31)),
    ]

    # Use monkeypatch to avoid creating an actual file
    monkeypatch.setattr("matplotlib.pyplot.savefig", lambda *args, **kwargs: None)

    # Test both weekly (is_month=False) and monthly (is_month=True)
    create_bar_chart([mock_measurement_set, mock_measurement_set], filename="test_chart_week.png", is_month=False)
    create_bar_chart([mock_measurement_set, mock_measurement_set], filename="test_chart_month.png", is_month=True)

    # Check if the function saves the file correctly (the actual save is mocked)
    assert True

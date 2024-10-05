"""unit test main.py"""
from datetime import datetime
from unittest.mock import patch

import pytest

import main

# pylint: disable=missing-function-docstring

date1 = datetime(year=2024, month=10, day=1)
date2 = datetime(year=2024, month=10, day=6)


@pytest.mark.parametrize("date, is_month, measurement_name, name, is_watt", [
    (date1, True, 'measurement1', 'Measurement 1', False),
    (date2, False, 'measurement2', 'Measurement 2', True),
])
def test_process_and_log(date, is_month, measurement_name, name, is_watt):
    with patch('main.process_measurement_watt') as mock_process_watt, \
         patch('main.process_measurement_kwh') as mock_process_kwh, \
         patch('main.log_difference') as mock_log_difference:

        # Mock return values based on is_watt
        if is_watt:
            mock_process_watt.return_value = ((101, 102), (date, date))
            expected_output = 1
            mock_log_difference.return_value = expected_output
        else:
            mock_process_kwh.return_value = ((102, 101), (date, date))
            expected_output = -1
            mock_log_difference.return_value = expected_output

        result = main.process_and_log(date, is_month, measurement_name, name, is_watt)

        assert result == expected_output
        if is_watt:
            mock_process_watt.assert_called_once_with(date, is_month, measurement_name)
        else:
            mock_process_kwh.assert_called_once_with(date, is_month, measurement_name)
        mock_log_difference.assert_called_once()


@pytest.mark.parametrize("test_date, verify_date, is_first_of_month", [
    (datetime(year=2024, month=10, day=1), datetime(year=2024, month=10, day=1), True),
    (datetime(year=2024, month=10, day=2), datetime(year=2024, month=10, day=1), True),
    (datetime(year=2024, month=10, day=6), datetime(year=2024, month=10, day=6), False),
    (datetime(year=2024, month=10, day=7), datetime(year=2024, month=10, day=6), False),
])
def test_main(test_date, verify_date, is_first_of_month):
    """test main function with different combinations"""
    with patch('main.process') as mock_process, \
         patch('main.datetime') as mock_datetime, \
         patch('main.create_bar_chart') as _mock_create_bar_chart:

        mock_datetime.now.return_value = test_date
        main.main(today=test_date)

        mock_process.assert_any_call(date=verify_date, is_month=is_first_of_month)


@pytest.mark.parametrize(
    "date, is_month, measurement_name, expected_usage",
    [
        # Add your test cases for process_measurement_kwh here
        (date1, True, 'measurement_kwh_1', 101),
        (date2, False, 'measurement_kwh_2', 103),
        # Add more cases as needed
    ])
def test_process_measurement_kwh(date, is_month, measurement_name, expected_usage):
    with patch('main.GetFromInflux') as mock_influx:
        mock_influx_instance = mock_influx.return_value
        mock_influx_instance.get_values_from_influx.return_value = [0, expected_usage]

        result, _ = main.process_measurement_kwh(date, is_month, measurement_name)

        assert result[1] == expected_usage


@pytest.mark.parametrize(
    "date, is_month, measurement_name, expected_usage",
    [
        # Add your test cases for process_measurement_watt here
        (date1, True, 'measurement_watt_1', 101),
        (date2, False, 'measurement_watt_2', 102),
        # Add more cases as needed
    ])
def test_process_measurement_watt(date, is_month, measurement_name, expected_usage):
    with patch('main.GetFromInflux') as mock_influx:
        mock_influx_instance = mock_influx.return_value
        mock_influx_instance.get_total_kwh_consumed_from_influx.return_value = expected_usage

        result, _ = main.process_measurement_watt(date, is_month, measurement_name)

        assert result[1] == expected_usage

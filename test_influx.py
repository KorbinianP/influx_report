import configparser
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from influx import GetFromInflux


@pytest.fixture
def mock_influx_client():
    mock_client = MagicMock()
    mock_query_api = mock_client.query_api.return_value
    mock_query_api.query.return_value = [
        MagicMock(records=[
            MagicMock(get_value=MagicMock(return_value=100), get_time=MagicMock(return_value=datetime(2023, 1, 1, 0, 0))),
            MagicMock(get_value=MagicMock(return_value=200), get_time=MagicMock(return_value=datetime(2023, 1, 1, 1, 0))),
        ])
    ]
    return mock_client


@pytest.fixture
def influx_instance(mock_influx_client):
    instance = GetFromInflux()
    instance.influx.client = mock_influx_client
    return instance


def test_get_total_kwh_consumed_from_influx(influx_instance):
    start_date = datetime(2023, 1, 1, 0, 0)
    end_date = datetime(2023, 1, 1, 2, 0)
    result = influx_instance.get_total_kwh_consumed_from_influx("test_measurement", start_date, end_date)
    assert result == 0.1  # (100W * 1h + 200W * 1h) / 1000 = 0.1 kWh


def test_get_values_from_influx(influx_instance):
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 2)
    result = influx_instance.get_values_from_influx("test_measurement", start_date, end_date)
    assert result == (200, 200)  # Last values for both start and end date


def test_get_total_kwh_consumed_from_influx_no_data(influx_instance):
    # Mock the query to return no data
    influx_instance.influx.client.query_api().query.return_value = []
    start_date = datetime(2023, 1, 1, 0, 0)
    end_date = datetime(2023, 1, 1, 2, 0)
    result = influx_instance.get_total_kwh_consumed_from_influx("test_measurement", start_date, end_date)
    assert result == 0.0  # No data should return 0.0 kWh


def test_get_total_kwh_consumed_from_influx_exception(influx_instance):
    # Mock the query to raise an exception
    influx_instance.influx.client.query_api().query.side_effect = Exception("Query failed")
    start_date = datetime(2023, 1, 1, 0, 0)
    end_date = datetime(2023, 1, 1, 2, 0)
    with pytest.raises(Exception, match="Query failed"):
        influx_instance.get_total_kwh_consumed_from_influx("test_measurement", start_date, end_date)


def test_get_values_from_influx_no_data(influx_instance):
    # Mock the query to return no data
    influx_instance.influx.client.query_api().query.return_value = []
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 2)
    result = influx_instance.get_values_from_influx("test_measurement", start_date, end_date)
    assert result == (None, None)  # No data should return (None, None)


def test_get_values_from_influx_exception(influx_instance):
    # Mock the query to raise an exception
    influx_instance.influx.client.query_api().query.side_effect = Exception("Query failed")
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 2)
    with pytest.raises(Exception, match="Query failed"):
        influx_instance.get_values_from_influx("test_measurement", start_date, end_date)


def test_missing_config_ini():
    with patch('configparser.ConfigParser.read', side_effect=configparser.NoSectionError('InfluxDB')):
        with pytest.raises(configparser.NoSectionError):
            GetFromInflux()


def test_no_section_error_handling():
    with patch('configparser.ConfigParser.read', side_effect=configparser.NoSectionError('InfluxDB')) as mock_read:
        try:
            GetFromInflux()
        except configparser.NoSectionError as error:
            assert str(error) == 'No section: \'InfluxDB\''
        mock_read.assert_called_once()

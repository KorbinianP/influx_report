"""Unit tests for summary.py"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from influx_report.helpers import MeasurementSet
from influx_report.summary import (
    generate_energy_summary,
    push_summary_to_openhab,
    save_summary_to_file,
)


def _create_sample_measurements():
    d_curr = (datetime(2026, 10, 18), datetime(2026, 10, 25))
    d_past = (datetime(2026, 10, 11), datetime(2026, 10, 18))

    return [
        MeasurementSet("Haushalt absolut", [170.3, 118.9], (d_past, d_curr)),
        MeasurementSet("E-Auto", [83.0, 43.1], (d_past, d_curr)),
        MeasurementSet("Kühlschrank", [2.7, 6.6], (d_past, d_curr)),
        MeasurementSet("Waschmaschine", [1.7, 4.2], (d_past, d_curr)),
        MeasurementSet("Trockner", [0.9, 3.5], (d_past, d_curr)),
        MeasurementSet("TV EG", [7.5, 6.4], (d_past, d_curr)),
        MeasurementSet("TV UG", [0.3, 0.0], (d_past, d_curr)),
        MeasurementSet("Wasserpumpe", [2.1, 2.0], (d_past, d_curr)),
        MeasurementSet("Kochfeld", [3.4, 3.7], (d_past, d_curr)),
        MeasurementSet("Backofen", [0.0, 1.7], (d_past, d_curr)),
        MeasurementSet("Mikrowelle", [0.0, 0.2], (d_past, d_curr)),
        MeasurementSet("Netzwerkschrank", [12.4, 12.1], (d_past, d_curr)),
        MeasurementSet("Spülmaschine", [5.3, 5.3], (d_past, d_curr)),
        MeasurementSet("Heizung absolut", [83.1, 51.3], (d_past, d_curr)),
        MeasurementSet("Wärmemenge Gesamt", [0.0, 3.2], (d_past, d_curr)),
        MeasurementSet("PV Einspeisung", [15.7, 100.9], (d_past, d_curr)),
    ]


def test_generate_energy_summary_weekly():
    data = _create_sample_measurements()
    summary = generate_energy_summary(data, is_month=False)

    assert "Wochenbericht" in summary
    assert "Haushalt & E-Auto" in summary
    assert "E-Auto" in summary
    assert "Rest-Haushalt" in summary
    assert "Auffällige Abweichungen" in summary
    assert "Kühlschrank" in summary
    assert "PV Einspeisung" in summary
    # Check that VW is used as reference tag
    assert "VW:" in summary


def test_generate_energy_summary_monthly():
    data = _create_sample_measurements()
    summary = generate_energy_summary(data, is_month=True)

    assert "Monatsbericht" in summary
    assert "VJ:" in summary


def test_generate_energy_summary_empty():
    assert "Keine Messdaten" in generate_energy_summary([])


def test_save_summary_to_file(tmp_path):
    out_file = save_summary_to_file("Test content", filename="test_summary.txt", directory=tmp_path)
    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == "Test content"


def test_push_summary_to_openhab_success():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = push_summary_to_openhab("Sample summary", openhab_url="http://openhab.local:8080")
        assert res is True


def test_push_summary_to_openhab_failure():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        res = push_summary_to_openhab("Sample summary", openhab_url="http://openhab.local:8080")
        assert res is False

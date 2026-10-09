"""
Read from an influxdb for configured items the values of last month or week,
depending on if it is the first of the month or sunday (or fallback to the most recent one).
Compare it against the same timeframe last year and output details to console and PNG chart.
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dateutil.relativedelta import relativedelta

from influx_report.chart import create_bar_chart
from influx_report.helpers import (
    MeasurementSet,
    get_same_calendar_week_day_one_year_ago,
    is_first_of_month,
    is_sunday,
    log_difference,
)
from influx_report.influx import GetFromInflux

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("influx_report.main")

# Default config paths in project root
DEFAULT_CONFIG_PATH = Path.cwd() / "measurements.yaml"


def load_measurements_config(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict[str, Any]]:
    """Loads measurements configuration from a YAML file.
    If the file does not exist, returns None so default built-in configuration is used.
    """
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("measurements", [])
    return []


def process_measurement_kwh(
    date: datetime,
    is_month: bool,
    measurement_name: str,
    influx: GetFromInflux | None = None,
) -> tuple[list[float], tuple[tuple[datetime, datetime], tuple[datetime, datetime]]]:
    """
    Entry point for processing usage data based on the specified period. The measurement is in Wh or kWh.

    Args:
        date (datetime): The reference date for calculations.
        is_month (bool): If True, the period is considered to be a month; if False, it is a week.
        measurement_name (str): The name of the measurement to be processed.
        influx (GetFromInflux, optional): Existing Influx client instance to reuse.

    Returns:
        list: [last_year_usage, this_year_usage]
        tuple: ((last_year_start, last_year_end), (this_year_start, this_year_end))
    """
    if influx is None:
        influx = GetFromInflux()

    if is_month:
        delta = relativedelta(months=1)
        one_year_ago = date - relativedelta(years=1)
    else:
        delta = relativedelta(weeks=1)
        one_year_ago = get_same_calendar_week_day_one_year_ago(date)

    # Get today's usage data for the specified period
    values_today = influx.get_values_from_influx(
        measurement_name=measurement_name,
        start_date=date - delta,
        end_date=date,
    )

    before = values_today[0] if values_today[0] is not None else 0.0
    now = values_today[1] if values_today[1] is not None else 0.0
    this_year_usage = now - before

    # Calculate last year's usage for the same period
    values_last_year = influx.get_values_from_influx(
        measurement_name=measurement_name,
        start_date=one_year_ago - delta,
        end_date=one_year_ago,
    )

    before_ly = values_last_year[0] if values_last_year[0] is not None else 0.0
    now_ly = values_last_year[1] if values_last_year[1] is not None else 0.0
    last_year_usage = now_ly - before_ly

    return [last_year_usage, this_year_usage], ((one_year_ago - delta, one_year_ago), (date - delta, date))


def process_measurement_watt(
    date: datetime,
    is_month: bool,
    measurement_name: str,
    influx: GetFromInflux | None = None,
) -> tuple[list[float], tuple[tuple[datetime, datetime], tuple[datetime, datetime]]]:
    """
    Entry point for processing usage data based on the specified period. The measurement is in W or kW.

    Args:
        date (datetime): The reference date for calculations.
        is_month (bool): If True, the period is considered to be a month; if False, it is a week.
        measurement_name (str): The name of the measurement to be processed.
        influx (GetFromInflux, optional): Existing Influx client instance to reuse.

    Returns:
        list: [last_year_usage, this_year_usage]
        tuple: ((last_year_start, last_year_end), (this_year_start, this_year_end))
    """
    if influx is None:
        influx = GetFromInflux()

    if is_month:
        delta = relativedelta(months=1)
        past_timeframe = date - relativedelta(years=1)
    else:
        delta = relativedelta(weeks=1)
        past_timeframe = date - relativedelta(days=7)

    # Get today's usage data for the specified period
    current_usage = influx.get_total_kwh_consumed_from_influx(
        measurement_name=measurement_name,
        start_date=date - delta,
        end_date=date,
    )

    # Calculate last year's usage for the same period
    past_usage = influx.get_total_kwh_consumed_from_influx(
        measurement_name=measurement_name,
        start_date=past_timeframe - delta,
        end_date=past_timeframe,
    )

    return [past_usage, current_usage], ((past_timeframe - delta, past_timeframe), (date - delta, date))


def process_and_log(
    date: datetime,
    is_month: bool,
    measurement_name: str,
    name: str,
    is_watt: bool = False,
    influx: GetFromInflux | None = None,
) -> MeasurementSet:
    """
    Processes the specified measurement for a given date, determining values and
    timeframes, and logs the differences.

    Args:
        date (datetime): The date for which the measurement is processed.
        is_month (bool): A flag indicating whether the measurement is for a month.
        measurement_name (str): The name of the measurement in the influx db.
        name (str): The human friendly name of the measurement.
        is_watt (bool): True if the value is in Watt, False if Wh or kWh.
        influx (GetFromInflux, optional): Existing Influx client.

    Returns:
        MeasurementSet: the data packed into a MeasurementSet.
    """
    if is_watt:
        if influx is not None:
            values, timeframes = process_measurement_watt(date, is_month, measurement_name, influx=influx)
        else:
            values, timeframes = process_measurement_watt(date, is_month, measurement_name)
    else:
        if influx is not None:
            values, timeframes = process_measurement_kwh(date, is_month, measurement_name, influx=influx)
        else:
            values, timeframes = process_measurement_kwh(date, is_month, measurement_name)
    return log_difference(values, timeframes, name)


def process_from_config(
    date: datetime,
    is_month: bool,
    config: list[dict[str, Any]],
    influx: GetFromInflux | None = None,
) -> list[MeasurementSet]:
    """Processes measurements configured via YAML file."""
    if influx is None:
        influx = GetFromInflux()

    results_by_name: dict[str, MeasurementSet] = {}

    for item in config:
        name = item["name"]
        m_type = item.get("type", "counter")
        scale = float(item.get("scale", 1.0))
        subtract_target = item.get("subtract")

        if "sum_of" in item:
            # Sum up multiple phase measurements
            total_values = [0.0, 0.0]
            tf = None
            for sub_meas in item["sum_of"]:
                v, tf = process_measurement_kwh(date, is_month, sub_meas, influx=influx)
                total_values[0] += v[0]
                total_values[1] += v[1]
            scaled_values = [round(total_values[0] * scale, 1), round(total_values[1] * scale, 1)]
            ms = log_difference(scaled_values, tf, name)
            results_by_name[name] = ms
        elif m_type == "watt":
            meas_name = item["measurement"]
            ms = process_and_log(date, is_month, meas_name, name, is_watt=True, influx=influx)
            results_by_name[name] = ms
        else:
            meas_name = item["measurement"]
            v, tf = process_measurement_kwh(date, is_month, meas_name, influx=influx)
            scaled_values = [round(v[0] * scale, 1), round(v[1] * scale, 1)]
            if subtract_target and subtract_target in results_by_name:
                sub_ms = results_by_name[subtract_target]
                sub_last = sub_ms.data[0] if hasattr(sub_ms, "data") else sub_ms.get("data", [0, 0])[0]
                sub_curr = sub_ms.data[1] if hasattr(sub_ms, "data") else sub_ms.get("data", [0, 0])[1]
                scaled_values[0] = round(scaled_values[0] - sub_last, 1)
                scaled_values[1] = round(scaled_values[1] - sub_curr, 1)
            ms = log_difference(scaled_values, tf, name)
            results_by_name[name] = ms

    return list(results_by_name.values())


def process_builtin(date: datetime, is_month: bool, influx: GetFromInflux | None = None) -> list[MeasurementSet]:
    """Default fallback processing if no YAML config is present."""
    if influx is None:
        influx = GetFromInflux()

    processed_data = []

    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Kuehlschrank", "Kühlschrank", True, influx=influx))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Waschmaschine", "Waschmaschine", True, influx=influx))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Trockner", "Trockner", True, influx=influx))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_TV_EG", "TV EG", True, influx=influx))
    processed_data.append(process_and_log(date, is_month, "Strom_TV_K1_Watt", "TV UG", True, influx=influx))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Wasserpumpe", "Wasserpumpe", True, influx=influx))

    # go-e "eto" is in deka kWh, value 1 = 0.1kWh
    goe, timeframes = process_measurement_kwh(date, is_month, "GoEChargerEnergyTotal", influx=influx)
    processed_data.append(log_difference((goe[0] / 10, goe[1] / 10), timeframes, "E-Auto"))

    just_log_measurements = [
        ("Zaehler_Ceran", "Kochfeld"),
        ("Zaehler_Mikrowelle", "Mikrowelle"),
        ("Zaehler_Netzwerkschrank", "Netzwerkschrank"),
        ("Zaehler_Spuelmaschine", "Spülmaschine"),
        ("Zaehler_Wasser_2025", "Wasser (m³)"),
        ("Zaehler_Wasser_Garten_2025", "Wasser Garten (m³)"),
    ]
    for measurement in just_log_measurements:
        processed_data.append(process_and_log(date, is_month, measurement[0], measurement[1], influx=influx))

    # Haushalt is in kWh
    haushalt, _ = process_measurement_kwh(date, is_month, "SmartMeter_Haushalt_Bezug", influx=influx)
    processed_data.append(log_difference(haushalt, timeframes, "Haushalt Zähler"))

    shelly_hh_ph1, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph1_Total", influx=influx)
    shelly_hh_ph2, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph2_Total", influx=influx)
    shelly_hh_ph3, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph3_Total", influx=influx)
    shelly_hh_total = [
        round((shelly_hh_ph1[0] + shelly_hh_ph2[0] + shelly_hh_ph3[0]) / 1000, 1),
        round((shelly_hh_ph1[1] + shelly_hh_ph2[1] + shelly_hh_ph3[1]) / 1000, 1),
    ]
    processed_data.append(log_difference(shelly_hh_total, timeframes, "Haushalt absolut"))

    # Heizung is in Wh, and Heizung also counts Haushalt (Kaskadenschaltung)
    heizung, _ = process_measurement_kwh(date, is_month, "SmartMeter_HeizungNeu_Bezug", influx=influx)
    heizung[0] = round(heizung[0] / 1000, 1) - haushalt[0]
    heizung[1] = round(heizung[1] / 1000, 1) - haushalt[1]
    processed_data.append(log_difference(heizung, timeframes, "Heizung"))

    shelly_hei_ph1, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph1_Total", influx=influx)
    shelly_hei_ph2, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph2_Total", influx=influx)
    shelly_hei_ph3, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph3_Total", influx=influx)
    shelly_hei_total = [
        round((shelly_hei_ph1[0] + shelly_hei_ph2[0] + shelly_hei_ph3[0]) / 1000, 1),
        round((shelly_hei_ph1[1] + shelly_hei_ph2[1] + shelly_hei_ph3[1]) / 1000, 1),
    ]
    processed_data.append(log_difference(shelly_hei_total, timeframes, "Heizung absolut"))

    einspeisung, _ = process_measurement_kwh(date, is_month, "SmartMeter_HeizungNeu_Einspeisung", influx=influx)
    einspeisung[0] = round(einspeisung[0] / 1000, 1)
    einspeisung[1] = round(einspeisung[1] / 1000, 1)
    processed_data.append(log_difference(einspeisung, timeframes, "PV Einspeisung"))

    return processed_data


def process(date: datetime, is_month: bool, influx: GetFromInflux | None = None) -> list[MeasurementSet]:
    """Processes measurements using measurements.yaml if available, otherwise builtin definitions."""
    cfg = load_measurements_config()
    if cfg:
        return process_from_config(date, is_month, cfg, influx=influx)
    return process_builtin(date, is_month, influx=influx)


def find_target_reporting_date(ref_date: datetime) -> tuple[datetime, bool]:
    """
    Determines the appropriate reporting date and period type (month vs week).
    If ref_date is already the 1st of a month or Sunday, it is used.
    Otherwise, steps backwards day by day to find the most recent 1st of month or Sunday.

    Returns:
        (target_date, is_month)
    """
    current = ref_date
    while True:
        if is_first_of_month(current):
            return current, True
        if is_sunday(current):
            return current, False
        current = current - relativedelta(days=1)


def main(today: datetime | None = None) -> None:
    """
    Main function to execute the processing of energy measurements.

    Args:
        today (datetime, optional): The reference datetime. Defaults to now at 23:59:59.
    """
    if today is None:
        today = datetime.now().replace(hour=23, minute=59, second=59)

    target_date, is_month = find_target_reporting_date(today)
    chart_filename = "bar_chart_month.png" if is_month else "bar_chart_week.png"
    period_label = "Monat" if is_month else "Woche"

    logger.info("Verarbeite Bericht für %s zum Stichtag %s", period_label, target_date.strftime("%d.%m.%Y"))

    # Reuse single InfluxDB client instance for all queries
    try:
        influx_client = GetFromInflux()
    except FileNotFoundError as exc:
        logger.error("Kritischer Fehler: %s", exc)
        raise SystemExit(1) from exc
    except Exception as exc:
        logger.error("Fehler beim Initialisieren der InfluxDB-Verbindung: %s", exc)
        raise SystemExit(1) from exc

    data = process(date=target_date, is_month=is_month, influx=influx_client)
    create_bar_chart(data, chart_filename)
    logger.info("Diagramm erfolgreich erstellt: %s", chart_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfluxDB Report Generator")
    parser.add_argument(
        "--date",
        type=lambda d: datetime.strptime(d, "%Y-%m-%d").replace(hour=23, minute=59, second=59),
        help="Optionales Referenzdatum im Format YYYY-MM-DD",
    )
    args = parser.parse_args()
    main(today=args.date)

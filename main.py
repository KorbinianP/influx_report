"""
Read from an influxdb for a certain item the values of last month or week,
depending on if it is the first of the month or sunday.
Compare it against same timeframe last year.
Ouput details to console
"""
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from helpers import (get_same_calendar_week_day_one_year_ago, is_first_of_month, is_sunday, log_difference)
from create_png import create_bar_chart
from influx import GetFromInflux

logging.basicConfig(level=logging.INFO, format='%(message)s')
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%d.%m.%y %H:%M:%S')
logger = logging.getLogger("influx_report.main")


def process_and_log(date, is_month, measurement_name, name, is_watt=False):
    """
    Processes the specified measurement for a given date, determining values and 
    timeframes, and logs the differences.

    Args:
        date ((datetime, datetime)): The date for which the measurement is processed.
        is_month (bool): A flag indicating whether the measurement is for a month.
        measurement_name (str): The name of the measurement in the influx db
        name (str): The human friendly name of the measurement to be processed.
        is_watt (bool): True if the value is in Watt / kW, False (default) if the vaule is in Wh or kWh

    Returns:
        dict: the data packed into a dict
    """
    if is_watt:
        values, timeframes = process_measurement_watt(date, is_month, measurement_name)
    else:
        values, timeframes = process_measurement_kwh(date, is_month, measurement_name)
    return log_difference(values, timeframes, name)


# pylint: disable-next=too-many-locals
def process(date, is_month):
    """
    Processes the energy measurements for a given date, determining whether to use monthly or weekly data.

    Args:
        date (datetime): The reference date for processing the measurements.
        is_month (bool): A flag indicating whether to process monthly data (True) or weekly data (False).

    Returns:
        None
    """
    processed_data = []

    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Kuehlschrank", "Kühlschrank", True))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Waschmaschine", "Waschmaschine", True))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Trockner", "Trockner", True))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_TV_EG", "TV EG", True))
    processed_data.append(process_and_log(date, is_month, "Strom_TV_K1_Watt", "TV UG", True))
    processed_data.append(process_and_log(date, is_month, "Strom_Leistung_Wasserpumpe", "Wasserpumpe", True))
    # go-e "eto" is in deka kWh, value 1 = 0.1kWh
    goe, timeframes = process_measurement_kwh(date, is_month, "GoEChargerEnergyTotal")
    processed_data.append(log_difference((goe[0] / 10, goe[1] / 10), timeframes, "E-Auto"))

    just_log_measurements = [
        ("Zaehler_Ceran", "Kochfeld"),
        ("Zaehler_Mikrowelle", "Mikrowelle"),
        ("Zaehler_Netzwerkschrank", "Netzwerkschrank"),
        ("Zaehler_Spuelmaschine", "Spülmaschine"),
        ("Zaehler_Wasser", "Wasser (m³)"),
        ("Zaehler_Wasser_Garten", "Wasser Garten (m³)"),
        #("Zaehler_Backofen","Heizung"),
    ]
    for measurement in just_log_measurements:
        processed_data.append(process_and_log(date, is_month, measurement[0], measurement[1]))
    # Haushalt is in kWh
    haushalt, _ = process_measurement_kwh(date, is_month, "SmartMeter_Haushalt_Bezug")
    processed_data.append(log_difference(haushalt, timeframes, "Haushalt Zähler"))

    shelly_hh_ph1, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph1_Total")
    shelly_hh_ph2, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph2_Total")
    shelly_hh_ph3, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Haushalt_Ph3_Total")
    shelly_hh_total = [
        round((shelly_hh_ph1[0] + shelly_hh_ph2[0] + shelly_hh_ph3[0]) / 1000, 1),
        round((shelly_hh_ph1[1] + shelly_hh_ph2[1] + shelly_hh_ph3[1]) / 1000, 1),
    ]
    processed_data.append(log_difference(shelly_hh_total, timeframes, "Haushalt absolut"))

    # Heizung is in Wh, and Heizung also counts Haushalt (Kaskadenschaltung)
    heizung, _ = process_measurement_kwh(date, is_month, "SmartMeter_HeizungNeu_Bezug")
    heizung[0] = round(heizung[0] / 1000, 1) - haushalt[0]
    heizung[1] = round(heizung[1] / 1000, 1) - haushalt[1]
    processed_data.append(log_difference(heizung, timeframes, "Heizung"))
    shelly_hei_ph1, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph1_Total")
    shelly_hei_ph2, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph2_Total")
    shelly_hei_ph3, _ = process_measurement_kwh(date, is_month, "Test_Shelly_3EM_Heizung_Ph3_Total")
    shelly_hh_total = [
        round((shelly_hei_ph1[0] + shelly_hei_ph2[0] + shelly_hei_ph3[0]) / 1000, 1),
        round((shelly_hei_ph1[1] + shelly_hei_ph2[1] + shelly_hei_ph3[1]) / 1000, 1),
    ]
    processed_data.append(log_difference(shelly_hh_total, timeframes, "Heizung absolut"))

    return processed_data


def process_measurement_kwh(date, is_month, measurement_name):
    """
    Entry point for processing usage data based on the specified period. The measurement is in Wh or kWh.

    Args:
        date (datetime): The reference date for calculations.
        is_month (bool): If True, the period is considered to be a month; if False, it is a week.
        measurement_name (str): The name of the measurement to be processed.

    Raises:
        ValueError: If an invalid period is specified.

    Returns:
        list: A list containing two values: 
            - last_year_value (float): The usage value from the same period last year.
            - this_year_value (float): The usage value from the current period.
        tuple: A tuple containing two tuples:
            - first tuple (float, float): Last year start and end date.
            - this_year_value (float): This year start and end date.
    """
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

    # Calculate current year's usage
    this_year_usage = values_today[1] - values_today[0]

    # Calculate last year's usage for the same period
    values_last_year = influx.get_values_from_influx(
        measurement_name=measurement_name,
        start_date=one_year_ago - delta,
        end_date=one_year_ago,
    )

    last_year_usage = values_last_year[1] - values_last_year[0]
    return [last_year_usage, this_year_usage], ((one_year_ago - delta, one_year_ago), (date - delta, date))


def process_measurement_watt(date, is_month, measurement_name):
    """
    Entry point for processing usage data based on the specified period. The measurement is in W or kW.

    Args:
        date (datetime): The reference date for calculations.
        is_month (bool): If True, the period is considered to be a month; if False, it is a week.
        measurement_name (str): The name of the measurement to be processed.

    Raises:
        ValueError: If an invalid period is specified.

    Returns:
        list: A list containing two values: 
            - last_year_value (float): The usage value from the same period last year.
            - this_year_value (float): The usage value from the current period.
        tuple: A tuple containing two tuples:
            - first tuple (float, float): Last year start and end date.
            - this_year_value (float): This year start and end date.
    """
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


def main(today=datetime.now().replace(hour=23, minute=59, second=59)):
    """
    Main function to execute the processing of energy measurements.

    Args:
        today (datetime, optional): The reference datetime for processing. Defaults to the current datetime set to 23:59:59.

    Returns:
        None
    """
    was_processed = False
    data = []

    if is_first_of_month(today):
        logger.debug("%s is the first of the month.", today.date())
        data = process(date=today, is_month=True)
        was_processed = True
    else:
        logger.debug("%s is not the first of the month.", today.date())

    if is_sunday(today):
        logger.debug("%s is a Sunday.", today.date())
        data = process(date=today, is_month=False)
        was_processed = True
    else:
        logger.debug("%s is not a Sunday.", today.date())

    if not was_processed:
        main(today - relativedelta(days=1))
    else:
        create_bar_chart(data)


if __name__ == "__main__":
    #main(datetime(year=2024, month=9, day=30))
    main()

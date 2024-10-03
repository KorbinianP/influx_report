"""
Read from an influxdb for a certain item the values of last month or week,
depending on if it is the first of the month or sunday.
Compare it against same timeframe last year.
Ouput details to console
"""
import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from helpers import (get_same_calendar_week_day_one_year_ago, is_first_of_month, is_sunday)
from influx import GetFromInflux

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%d.%m.%y %H:%M:%S')
logger = logging.getLogger("influx_report.main")


def log_difference(values, timeframes, measurement_name):
    """
    Logs the difference in energy usage between two timeframes.

    Args:
        values (list): A list containing the energy usage values for the previous and current periods.
        timeframes (tuple): A tuple containing two tuples, each with start and end datetime objects for the periods being compared.
        measurement_name (str): The name of the measurement being logged.

    Returns:
        None
    """

    logger.info("---- %s ----", measurement_name)
    logger.info("Usage %s to %s: %.1f kWh", timeframes[1][0].strftime("%d.%m.%y"), timeframes[1][1].strftime("%d.%m.%y"), values[1])
    logger.info("Usage %s to %s: %.1f kWh", timeframes[0][0].strftime("%d.%m.%y"), timeframes[0][1].strftime("%d.%m.%y"), values[0])
    change = 'increased' if values[1] > values[0] else 'decreased'
    logger.info("The usage %s by %.1f kWh", change, abs(values[1] - values[0]))
    logger.info("----%s----", "-" * (len(measurement_name) + 2))
    logger.info("")


def process(date, is_month):
    """
    Processes the energy measurements for a given date, determining whether to use monthly or weekly data.

    Args:
        date (datetime): The reference date for processing the measurements.
        is_month (bool): A flag indicating whether to process monthly data (True) or weekly data (False).

    Returns:
        None
    """
    # Haushalt is in kWh
    haushalt, timeframes = process_measurement(date, is_month, "SmartMeter_Haushalt_Bezug")
    log_difference(haushalt, timeframes, "Haushalt")
    # Heizung is in Wh, and Heizung also counts Haushalt (Kaskadenschaltung)
    heizung, _ = process_measurement(date, is_month, "SmartMeter_HeizungNeu_Bezug")
    heizung[0] = round(heizung[0] / 1000, 1) - haushalt[0]
    heizung[1] = round(heizung[1] / 1000, 1) - haushalt[1]
    log_difference(heizung, timeframes, "Heizung")


def process_measurement(date, is_month, measurement_name):
    """
    Entry point for processing usage data based on the specified period.

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


def main(today=datetime.now().replace(hour=23, minute=59, second=59)):
    """
    Main function to execute the processing of energy measurements.

    Args:
        today (datetime, optional): The reference datetime for processing. Defaults to the current datetime set to 23:59:59.

    Returns:
        None
    """
    was_processed = False

    if is_first_of_month(today):
        logger.debug("%s is the first of the month.", today.date())
        process(date=today, is_month=True)
        was_processed = True
    else:
        logger.debug("%s is not the first of the month.", today.date())

    if is_sunday(today):
        logger.debug("%s is a Sunday.", today.date())
        process(date=today, is_month=False)
        was_processed = True
    else:
        logger.debug("%s is not a Sunday.", today.date())

    if not was_processed:
        main(today - relativedelta(days=1))


if __name__ == "__main__":
    main()

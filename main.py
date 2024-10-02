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


def process(date, period):
    """Entry point for processing usage data based on the specified period.

    Args:
        date (datetime): The reference date for calculations.
        period (str): The period for usage data ('month' or 'week').

    Raises:
        ValueError: If an invalid period is specified.
    """
    influx = GetFromInflux()

    if period == "month":
        delta = relativedelta(months=1)
        one_year_ago = date - relativedelta(years=1)
    elif period == "week":
        delta = relativedelta(weeks=1)
        one_year_ago = get_same_calendar_week_day_one_year_ago(date)
    else:
        raise ValueError("Invalid period specified. Use 'month' or 'week'.")

    # Get today's usage data for the specified period
    values_today = influx.get_values_from_influx(
        measurement_name="SmartMeter_Haushalt_Bezug",
        start_date=date - delta,
        end_date=date,
    )

    logger.info("%s", values_today)

    # Calculate current year's usage
    this_year_usage = values_today[1] - values_today[0]
    logger.info("Usage %s to %s: %s kWh", date - delta, date, this_year_usage)

    # Calculate last year's usage for the same period
    values_last_year = influx.get_values_from_influx(
        measurement_name="SmartMeter_Haushalt_Bezug",
        start_date=one_year_ago - delta,
        end_date=one_year_ago,
    )

    last_year_usage = values_last_year[1] - values_last_year[0]
    logger.info("Usage %s to %s: %s kWh", one_year_ago - delta, one_year_ago, last_year_usage)

    # Log comparison of this year's usage to last year's usage
    logger.info("The usage %s by %s kWh", 'increased' if this_year_usage > last_year_usage else 'decreased', abs(this_year_usage - last_year_usage))


def main():
    """main entry point of the module"""
    today = datetime.now().replace(hour=23, minute=59, second=59)

    if is_first_of_month(today):
        logger.info("%s is the first of the month.", today.date())
        process(date=today, period="month")
    else:
        logger.info("%s is not the first of the month.", today.date())

    if is_sunday(today):
        logger.info("%s is a Sunday.", today.date())
        process(date=today, period="week")
    else:
        logger.info("%s is not a Sunday.", today.date())


if __name__ == "__main__":
    main()

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

    logger.info(values_today)

    # Calculate current year's usage
    this_year_usage = values_today[1] - values_today[0]
    logger.info(f"Usage {date - delta} to {date}: {this_year_usage} kWh")

    # Calculate last year's usage for the same period
    values_last_year = influx.get_values_from_influx(
        measurement_name="SmartMeter_Haushalt_Bezug",
        start_date=one_year_ago - delta,
        end_date=one_year_ago,
    )

    last_year_usage = values_last_year[1] - values_last_year[0]
    logger.info(f"Usage {one_year_ago - delta} to {one_year_ago}: {last_year_usage} kWh")

    # Log comparison of this year's usage to last year's usage
    logger.info(f"The usage {'increased' if this_year_usage > last_year_usage else 'decreased'} by {abs(this_year_usage - last_year_usage)} kWh")


def main():
    today = datetime.now().replace(hour=23, minute=59, second=59)

    if is_first_of_month(today):
        logger.info(f"{today.date()} is the first of the month.")
        process(date=today, period="month")
    else:
        logger.info(f"{today.date()} is not the first of the month.")

    if is_sunday(today):
        logger.info(f"{today.date()} is a Sunday.")
        process(date=today, period="week")
    else:
        logger.info(f"{today.date()} is not a Sunday.")


if __name__ == "__main__":
    main()

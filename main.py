from datetime import datetime, timedelta
import logging
from dateutil.relativedelta import relativedelta
from influx import GetFromInflux

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("influx_report.main")


def last_sunday(today):
    # Find the latest Sunday by calculating how many days back it is from today
    last_sunday = today - timedelta(days=today.weekday() + 1)  # 0 = Monday, ..., 6 = Sunday
    last_sunday_23 = last_sunday.replace(hour=23, minute=59)

    return last_sunday_23


def get_same_calendar_week_day_one_year_ago(date):
    # Get the current day of the week (0=Monday, 6=Sunday)
    current_weekday = date.weekday()

    # Get the current calendar week (ISO calendar week number)
    current_calendar_week = date.isocalendar()[1]

    # Get the year and set it to one year ago
    year_one_year_ago = date.year - 1

    # Calculate the same calendar week day one year ago
    first_day_of_year_one_ago = datetime.strptime(f"{year_one_year_ago}-W{current_calendar_week}-1", "%G-W%V-%u")

    # Get the corresponding day of the same week
    same_weekday_one_year_ago = first_day_of_year_one_ago + timedelta(days=current_weekday)

    return same_weekday_one_year_ago


def main(today, period="month"):
    """Main entry point with period parameter"""
    influx = GetFromInflux()
    #today = datetime.now()

    if period == "month":
        delta = relativedelta(months=1)
        one_year_ago = today - relativedelta(years=1)
    elif period == "week":
        delta = relativedelta(weeks=1)
        one_year_ago = get_same_calendar_week_day_one_year_ago(today)
    else:
        raise ValueError("Invalid period specified. Use 'month' or 'week'.")

    # Get today's usage data for the specified period
    values_today = influx.get_values_from_influx(
        measurement_name="SmartMeter_Haushalt_Bezug",
        start_date=today - delta,
        end_date=today,
    )

    logger.info(values_today)

    # Calculate current year's usage
    this_year_usage = values_today[1] - values_today[0]
    logger.info(f"Usage {today - delta} to {today}: {this_year_usage} kWh")

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


if __name__ == "__main__":
    today = datetime(year=2024, month=10, day=1, hour=23, minute=59)
    main(today=today, period="month")
    main(today=last_sunday(today), period="week")

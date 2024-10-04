"""Collection of some small helper functions"""
from datetime import datetime, timedelta
import logging
from typing import \
    List  # until Python 3.8 you can't use list[] but must use typing.List[]

logger = logging.getLogger("influx_report.helpers")


def log_difference(values, timeframes, measurement_name):
    """
    Logs the difference in energy usage between two timeframes.

    Parameters:
        values (list): A list containing two float values representing energy 
                       usage in kWh for the two timeframes.
        timeframes (list): A list containing two tuples, each with two datetime objects representing
                           the start and end dates of the respective timeframes.
        measurement_name (str): A string representing the name of the measurement being logged.

    The function logs the energy usage for each timeframe, calculates the change in usage,
    and logs whether the usage has increased or decreased along with the amount of change.
    """
    logger.info("-------- %s --------", measurement_name)
    logger.info("Usage %s to %s: %.1f kWh", timeframes[1][0].strftime("%d.%m.%y"), timeframes[1][1].strftime("%d.%m.%y"), values[1])
    logger.info("Usage %s to %s: %.1f kWh", timeframes[0][0].strftime("%d.%m.%y"), timeframes[0][1].strftime("%d.%m.%y"), values[0])
    change = 'increased' if values[1] > values[0] else 'decreased'
    logger.info("The usage %s by %.1f kWh", change, abs(values[1] - values[0]))
    # logger.info("----%s----", "-" * (len(measurement_name) + 2))
    logger.info("")


def get_latest_value(timestamps: List[datetime], values: list):
    """Scan through a list of timestamps and get the latest date.
    Return the date and the value in the same position

    Args:
        timestamps (typing.List[datetime]): timestamps in an ordered list
        values (list): values in a list, pos n corresponds to pos n of timestamps

    Returns:
        _type_: tuple of timestamp and value
    """
    if not timestamps or not values:
        logger.error("Both timestamps and values must be set! Length of timestamps: %s, values: %s", len(timestamps), len(values))
        return None, None
    if len(timestamps) != len(values):
        logger.error("Length of timestamps and values must be same! Length of timestamps: %s, values: %s", len(timestamps), len(values))
        return None, None
    timestamp_old = timestamps[0]
    value_old = values[0]
    pos = 0
    for timestamp in timestamps:
        if timestamp > timestamp_old:
            timestamp_old = timestamp
            value_old = values[pos]
        pos += 1
    return (timestamp_old, value_old)


def last_sunday(date):
    """Calculate the last Sunday before the given date.

    Args:
        today (datetime): The reference date.

    Returns:
        datetime: The last Sunday before the given date, set to 23:59.
    """
    if date.weekday() == 6:
        sunday = date
    else:
        sunday = date - timedelta(days=date.weekday() + 1)  # 0 = Monday, ..., 6 = Sunday
    sunday_end_of_day = sunday.replace(hour=23, minute=59)
    return sunday_end_of_day


def is_first_of_month(date):
    """Check if the given date is the first day of the month.

    Args:
        date (datetime): The date to check.

    Returns:
        bool: True if the date is the first of the month, False otherwise.
    """
    return date.day == 1


def is_sunday(date):
    """Check if the given date is a Sunday.

    Args:
        date (datetime): The date to check.

    Returns:
        bool: True if the date is a Sunday, False otherwise.
    """
    return date.weekday() == 6


def get_same_calendar_week_day_one_year_ago(date):
    """Get the same weekday from the same calendar week one year ago.

    Args:
        date (datetime): The reference date.

    Returns:
        datetime: The corresponding weekday from the same calendar week one year ago.
    """
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

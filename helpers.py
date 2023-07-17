"""Collection of some small helper functions"""
from logging import Logger
from datetime import datetime

logger = Logger("influx_report.helpers")


def get_latest_value(timestamps: list[datetime], values: list):
    """Scan through a list of timestamps and get the latest date.
    Return the date and the value in the same position

    Args:
        timestamps (list): timestamps in an ordered list
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

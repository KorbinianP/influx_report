"""Get data from InfluxDB"""

import configparser
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from influxdb_client import InfluxDBClient


@dataclass
class InfluxConfigClass:
    """All configuration and client belonging to an InfluxDB"""

    url: str
    token: str
    org: str
    bucket: str
    client: InfluxDBClient


logger = logging.getLogger("influx_report.influx")


# pylint: disable-next=too-few-public-methods
class GetFromInflux:
    """Get data from InfluxDB"""

    def __init__(self, config_file: str = "config.ini"):
        """Parse config.ini and create the influx client"""
        if not os.path.exists(config_file):
            msg = f"Konfigurationsdatei '{config_file}' nicht gefunden! Bitte erstelle '{config_file}' mit der [InfluxDB]-Sektion (siehe README.md)."
            logger.error(msg)
            raise FileNotFoundError(msg)

        config = configparser.ConfigParser()

        try:
            config.read(config_file)
            self.influx = InfluxConfigClass(
                url=config.get("InfluxDB", "url"),
                token=config.get("InfluxDB", "token"),
                org=config.get("InfluxDB", "org"),
                bucket=config.get("InfluxDB", "bucket"),
                # Verbindung zur InfluxDB herstellen
                client=InfluxDBClient(url=config.get("InfluxDB", "url"), token=config.get("InfluxDB", "token")),
            )
            logger.debug("Fill connect to InfluxDB %s", self.influx.url)
        except configparser.NoSectionError as error:
            logger.error("Not recoverable error: %s", error.message)
            logger.error("Ensure that file %s exists and has a [InfluxDB] section.", config_file)
            logger.error(" See README.md for more details")
            raise error

    def get_total_kwh_consumed_from_influx(
        self,
        measurement_name: str,
        start_date: datetime,
        end_date: datetime,
    ):
        """Calculate kWh consumed over a certain timespan from InfluxDB

        Args:
            measurement_name (str): name of the measurement stored in influx
            start_date (datetime): date when to start the query
            end_date (datetime): date when to end the query

        Returns:
            float: total kWh consumed during the timespan
        """
        logger.debug("Get kWh from %s to %s", start_date, end_date)
        query = f"""from(bucket:"{self.influx.bucket}")
        |> range(start: {start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")}, stop: {end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
        |> filter(fn: (r) => r._measurement == "{measurement_name}")
        |> sort(columns: ["_time"], desc: false)"""

        result = self.influx.client.query_api().query(org=self.influx.org, query=query)

        values = []
        timestamps = []

        for table in result:
            for record in table.records:
                try:
                    values.append(record.get_value())
                    timestamps.append(record.get_time())
                except KeyError as exception:
                    logger.error(exception)

        if len(values) < 2:
            return 0.0  # Not enough data to calculate kWh

        total_kwh = 0.0
        for i in range(1, len(values)):
            # Calculate the time difference in hours
            time_diff = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600.0
            # Calculate kWh for the interval and accumulate
            total_kwh += (values[i - 1] * time_diff) / 1000.0  # Convert Watts to kW

        return total_kwh

    def get_values_from_influx(
        self,
        measurement_name: str,
        start_date: datetime,
        end_date: datetime,
        max_lookback_days: int = 3,
    ):
        """
        Retrieves the last recorded values from InfluxDB for a specified measurement
        over two distinct timeframes: the entire day of the start date and the entire
        day of the end date.

        If no data is found for a given date, the function will look back up to
        max_lookback_days to find the most recent available data.

        Args:
            measurement_name (str): The name of the measurement stored in InfluxDB.
            start_date (datetime): The date for the start of the query, used to define
                                the range from 00:00:00 to 23:59:59 of that day.
            end_date (datetime): The date for the end of the query, used to define
                                the range from 00:00:00 to 23:59:59 of that day.
            max_lookback_days (int): Maximum number of days to look back if no data
                                    is found (default: 3).

        Returns:
            tuple: A tuple containing the last value recorded for the start date and
                the last value recorded for the end date. If no values are found
                after looking back max_lookback_days, None is returned for that timeframe.
        """

        def get_value_for_date(target_date: datetime, max_days: int) -> any:
            """Helper function to get value for a specific date with lookback."""
            for days_back in range(max_days + 1):
                query_date = target_date - timedelta(days=days_back)

                logger.debug(
                    "Querying %s for date %s (looking back %d days from %s)",
                    measurement_name,
                    query_date.strftime("%Y-%m-%d"),
                    days_back,
                    target_date.strftime("%Y-%m-%d"),
                )

                query = f"""from(bucket:"{self.influx.bucket}")
                |> range(start: {query_date.strftime("%Y-%m-%dT00:00:00Z")}, stop: {query_date.strftime("%Y-%m-%dT23:59:59Z")})
                |> filter(fn: (r) => r._measurement == "{measurement_name}")
                |> sort(columns: ["_time"], desc: false)"""

                result = self.influx.client.query_api().query(org=self.influx.org, query=query)
                values = []

                for table in result:
                    for record in table.records:
                        try:
                            value = record.get_value()
                            values.append(value)
                        except KeyError as exception:
                            logger.error(exception)

                if values:
                    logger.debug("Found %d values for %s (looked back %d days)", len(values), query_date.strftime("%Y-%m-%d"), days_back)
                    return values[-1]

            logger.warning("No values found for measurement '%s' within %d days of %s", measurement_name, max_days, target_date.strftime("%Y-%m-%d"))
            return None

        logger.debug("Get value from %s to %s", start_date, end_date)

        # Get values for both dates with lookback
        value_start = get_value_for_date(start_date, max_lookback_days)
        value_end = get_value_for_date(end_date, max_lookback_days)

        # Ensure consistency: if one is None and the other is not, use the non-None value for both
        if value_start is None and value_end is not None:
            logger.info("Start value is None, using end value for both: %s", value_end)
            value_start = value_end
        elif value_end is None and value_start is not None:
            logger.info("End value is None, using start value for both: %s", value_start)
            value_end = value_start

        # If both are None, set both to 0
        if value_start is None and value_end is None:
            logger.info("Both values are None, defaulting to 0")
            value_start = 0
            value_end = 0
        return (value_start, value_end)

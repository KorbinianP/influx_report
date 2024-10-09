"""Get data from InfluxDB"""
from datetime import datetime
from dataclasses import dataclass
import logging
import configparser
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
class GetFromInflux():
    """Get data from InfluxDB"""

    def __init__(self):
        """Parse config.ini and create the influx client"""
        config = configparser.ConfigParser()

        try:
            config.read('config.ini')
            self.influx = InfluxConfigClass(
                url=config.get("InfluxDB", "url"),
                token=config.get("InfluxDB", "token"),
                org=config.get("InfluxDB", "org"),
                bucket=config.get("InfluxDB", "bucket"),
                # Verbindung zur InfluxDB herstellen
                client=InfluxDBClient(url=config.get("InfluxDB", "url"), token=config.get("InfluxDB", "token")))
            logger.debug("Fill connect to InfluxDB %s", self.influx.url)
        except configparser.NoSectionError as error:
            logger.error("Not recoverable error: %s", error.message)
            logger.error("Ensure that file config.ini exists and has a [InfluxDB] section.")
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
        |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
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
    ):
        """
        Retrieves the last recorded values from InfluxDB for a specified measurement 
        over two distinct timeframes: the entire day of the start date and the entire 
        day of the end date.

        Args:
            measurement_name (str): The name of the measurement stored in InfluxDB.
            start_date (datetime): The date for the start of the query, used to define 
                                the range from 00:00:00 to 23:59:59 of that day.
            end_date (datetime): The date for the end of the query, used to define 
                                the range from 00:00:00 to 23:59:00 of that day.

        Returns:
            tuple: A tuple containing the last value recorded for the start date and 
                the last value recorded for the end date. If no values are found, 
                None is returned for that timeframe.
        """
        logger.debug("Get value from %s to %s", start_date, end_date)
        # Query for start_date from 00:00:00 to 23:59:59
        query_start = f"""from(bucket:"{self.influx.bucket}")
        |> range(start: {start_date.strftime('%Y-%m-%dT00:00:00Z')}, stop: {start_date.strftime('%Y-%m-%dT23:59:59Z')})
        |> filter(fn: (r) => r._measurement == "{measurement_name}")
        |> sort(columns: ["_time"], desc: false)"""

        result_start = self.influx.client.query_api().query(org=self.influx.org, query=query_start)

        values_start = []

        for table in result_start:
            for record in table.records:
                try:
                    value = record.get_value()
                    values_start.append(value)
                except KeyError as exception:
                    logger.error(exception)

        # Query for end_date from 00:00:00 to 23:59:00
        query_end = f"""from(bucket:"{self.influx.bucket}")
        |> range(start: {end_date.strftime('%Y-%m-%dT00:00:00Z')}, stop: {end_date.strftime('%Y-%m-%dT23:59:59Z')})
        |> filter(fn: (r) => r._measurement == "{measurement_name}")
        |> sort(columns: ["_time"], desc: false)"""

        result_end = self.influx.client.query_api().query(org=self.influx.org, query=query_end)

        values_end = []

        for table in result_end:
            for record in table.records:
                try:
                    value = record.get_value()
                    values_end.append(value)
                except KeyError as exception:
                    logger.error(exception)

        # Return the last value from both queries
        return (values_start[-1] if values_start else None, values_end[-1] if values_end else None)

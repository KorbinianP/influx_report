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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("influx_report.influx")


# pylint: disable-next=too-few-public-methods
class GetFromInflux():
    """Get data from InfluxDB"""

    def __init__(self):
        """Parse config.ini and create the influx client"""
        config = configparser.ConfigParser()
        config.read('config.ini')

        try:
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

    def get_values_from_influx(
        self,
        measurement_name: str,
        start_date: datetime,
        end_date: datetime,
    ):
        """Get Values of a certain timespan from InfluxDB

        Args:
            measurement_name (str): name of the measurement stored in influx
            start_date (datetime): date when to start the query
            end_date (datetime): date when to end the query

        Returns:
            tuple of (start_value, end_value)
        """
        logger.debug("Get value from %s to %s", start_date, end_date)
        query = f"""from(bucket:"{self.influx.bucket}")
        |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
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
            return (values[0], values[-1])  # Return the first and last value
        return (None, None)

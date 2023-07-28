"""Get data from InfluxDB"""
from datetime import datetime
from dataclasses import dataclass
from logging import Logger
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


logger = Logger("influx_report.influx")


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
            tuple of timestamps (list[datetime]) and values (list())
        """

        query = f"""from(bucket:"{self.influx.bucket}")
        |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        |> filter(fn: (r) => r._measurement == "{measurement_name}")"""

        result = self.influx.client.query_api().query(org=self.influx.org, query=query)

        timestamps: list(datetime) = []
        values = []

        for table in result:
            for record in table.records:
                try:
                    time = str(record.get_time())
                    value = record.get_value()

                    # Convert timestamps to datetime
                    timestamp = datetime.fromisoformat(time)
                    timestamps.append(timestamp)
                    values.append(value)
                except KeyError as exception:
                    logger.error(exception)

        timestamps.reverse()
        values.reverse()
        return (timestamps, values)

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
        # read config.ini
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.influx = InfluxConfigClass(
            url=config.get("InfluxDB", "url"),
            token=config.get("InfluxDB", "token"),
            org=config.get("InfluxDB", "org"),
            bucket=config.get("InfluxDB", "bucket"),
            # Verbindung zur InfluxDB herstellen
            client=InfluxDBClient(url=config.get("InfluxDB", "url"), token=config.get("InfluxDB", "token")))
        logger.debug("Fill connect to InfluxDB %s", self.influx.url)

    def get_values_from_influx(
        self,
        measurement: str,
        start_date: datetime,
        end_date: datetime,
        influx: InfluxConfigClass,
    ):
        """Get Values of a certain timespan from InfluxDB"""
        query = f"""from(bucket:"{influx.bucket}")
        |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')})
        |> filter(fn: (r) => r._measurement == "{measurement}")"""

        result = influx.client.query_api().query(org=influx.org, query=query)

        # Liste zum Speichern der Zeitstempel und Werte
        timestamps = []
        values = []

        for table in result:
            for record in table.records:
                try:
                    time = str(record.get_time())
                    value = record.get_value()

                    # Zeitstempel in ein datetime-Objekt konvertieren
                    timestamp = datetime.fromisoformat(time)
                    timestamps.append(timestamp)
                    values.append(value)
                except KeyError as exception:
                    logger.error(exception)

        # Zeit normalisieren
        timestamps.reverse()
        values.reverse()
        return timestamps, values

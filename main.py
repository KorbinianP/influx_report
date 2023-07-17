"""Generating informative png pictures of measurements stored in an InfluxDB"""
from datetime import datetime, timezone, timedelta
from logging import Logger
import matplotlib.pyplot as plt
from helpers import get_latest_value
from influx import GetFromInflux

logger = Logger("influx_report.main")


def print_to_png(timestamps, values):
    """Linienchart erstellen"""
    plt.plot(timestamps, values)
    plt.xlabel('Zeit')
    plt.ylabel('Werte')
    plt.title('Letzte Werte')
    plt.xticks(rotation=45)
    plt.savefig('chart.png')


def main():
    """Main entry point"""
    influx = GetFromInflux()
    timestamps, values = influx.get_values_from_influx(
        measurement="SmartMeter_Haushalt_Bezug",
        start_date=datetime(2023, 7, 15, tzinfo=timezone.utc),
        end_date=datetime(2023, 7, 15, tzinfo=timezone.utc) + timedelta(hours=23, minutes=59, seconds=59),
        influx=influx,
    )
    timestamp, value = get_latest_value(timestamps, values)
    print(f"Last: {timestamp} - {value}")
    print_to_png(timestamps, values)


if __name__ == "__main__":
    main()

"""Generating informative png pictures of measurements stored in an InfluxDB"""
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt
from helpers import get_latest_value
from influx import GetFromInflux

logger = logging.Logger("influx_report.main")


def print_to_png(timestamps, values):
    """create line graph png"""
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
        measurement_name="SmartMeter_Haushalt_Bezug",
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now(),
    )
    timestamp, value = get_latest_value(timestamps, values)
    logger.debug("Last: %s - %s", timestamp, value)
    print_to_png(timestamps, values)


if __name__ == "__main__":
    main()

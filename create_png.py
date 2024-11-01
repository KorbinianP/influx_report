"""Create a PNG with a bar chart"""
import matplotlib.pyplot as plt
import numpy as np
from helpers import MeasurementSet


def format_dates(dates):
    """Formats a tuple of two datetime objects into a string.

    Args:
        dates (tuple): A tuple containing two datetime objects.

    Returns:
        str: Formatted date string.
    """
    first_date = dates[0].strftime("%d.%m.%y")
    last_date = dates[1].strftime("%d.%m.%y")
    return f"{first_date} - {last_date}"


def create_bar_chart(measurement_sets: MeasurementSet, filename='bar_chart.png'):
    """Creates a modern and colorful bar chart from an array of MeasurementSet and saves it as a PNG.

    Args:
        measurement_sets (list): A list of MeasurementSet objects.
        filename (str): The filename to save the bar chart as a PNG.
    
    Returns:
        None
    """
    names = [f"{ms.name} {ms.data[1]:.1f}" for ms in measurement_sets]
    values_last = [ms.data[0] for ms in measurement_sets]
    values_this = [ms.data[1] for ms in measurement_sets]

    x_axis = np.arange(len(names))  # the label locations
    width = 0.35  # the width of the bars

    _fig, axis = plt.subplots()
    _dates = measurement_sets[0].dates
    _bars1 = axis.bar(x_axis - width / 2, values_last, width, label=format_dates(measurement_sets[0].dates[0]), color='salmon')
    _bars2 = axis.bar(x_axis + width / 2, values_this, width, label=format_dates(measurement_sets[0].dates[1]), color='skyblue')

    differences = np.array(values_this) - np.array(values_last)

    for i in range(len(names)):
        axis.text(x_axis[i] - width / 2, max(values_last[i], values_this[i]) + 1, f"{differences[i]:+.1f}", ha='center', va='bottom')
        # if differences[i] < 0.0:
        # else:
        # ax.text(x[i] + width / 2, values_this[i] + 1, f"{differences[i]:+.1f}", ha='center', va='bottom')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    axis.set_ylabel('Verbrauch in kWh oder m³')
    axis.set_title('Verbräuche')
    axis.set_xticks(x_axis)
    axis.set_xticklabels(names, rotation=45, ha='right')  # Rotate x-axis labels for better readability
    axis.legend()

    # Add a small gap between bars
    axis.margins(y=0.1)

    plt.tight_layout()
    plt.savefig(filename)  # Save the figure as a PNG
    plt.close()  # Close the figure

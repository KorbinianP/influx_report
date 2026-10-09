"""Create a PNG with a bar chart, optimized for clarity and smartphone display."""

from collections.abc import Sequence

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


def create_bar_chart(measurement_sets: Sequence[MeasurementSet], filename: str = "bar_chart.png"):
    """Creates a modern, horizontal bar chart from an array of MeasurementSet and saves it as a PNG.

    Optimized for smartphone viewing (Telegram):
    - Horizontal layout (barh) provides plenty of room for device labels
    - Sorted or categorized cleanly
    - Color-coded delta badges (green for reduction/savings, red for increase)
    - High DPI and clean typography

    Args:
        measurement_sets (list): A list of MeasurementSet objects.
        filename (str): The filename to save the bar chart as a PNG.
    """
    if not measurement_sets:
        return

    # Extract names and values
    names = [ms.name for ms in measurement_sets]
    values_last = [float(ms.data[0]) for ms in measurement_sets]
    values_this = [float(ms.data[1]) for ms in measurement_sets]

    # Calculate differences
    differences = np.array(values_this) - np.array(values_last)

    num_items = len(names)
    # Dynamic height depending on number of items: ~0.55 inch per item + margins
    fig_height = max(7.0, num_items * 0.6 + 2.0)
    fig, ax = plt.subplots(figsize=(10, fig_height), dpi=150)

    # Clean, modern style
    ax.set_facecolor("#f8fafc")  # subtle cool grey/white
    fig.patch.set_facecolor("#ffffff")

    y_pos = np.arange(num_items)
    bar_height = 0.36

    # Colors
    color_last = "#94a3b8"  # slate-400 (neutral historical)
    color_this = "#2563eb"  # royal blue (active current period)

    label_last = format_dates(measurement_sets[0].dates[0])
    label_this = format_dates(measurement_sets[0].dates[1])

    # Draw bars (Last year on top or slightly shifted)
    ax.barh(y_pos + bar_height / 2, values_last, height=bar_height, label=f"Vorjahr ({label_last})", color=color_last, alpha=0.85, edgecolor="none")
    ax.barh(y_pos - bar_height / 2, values_this, height=bar_height, label=f"Aktuell ({label_this})", color=color_this, alpha=0.95, edgecolor="none")

    # Add delta annotations & values next to bars
    max_val = max(max(values_last, default=0), max(values_this, default=0), 1)
    offset_padding = max_val * 0.015

    for i in range(num_items):
        diff = differences[i]
        curr_val = values_this[i]
        last_val = values_last[i]
        higher_bar = max(curr_val, last_val)

        # Delta color: green if decreased (good for consumption), red/rose if increased
        # Special case for PV Einspeisung: higher is actually better, but generally highlight direction
        is_pv = "einspeisung" in names[i].lower()
        if diff < 0:
            diff_color = "#dc2626" if is_pv else "#16a34a"  # red if PV dropped, green if normal dropped
        elif diff > 0:
            diff_color = "#16a34a" if is_pv else "#dc2626"  # green if PV grew, red if normal grew
        else:
            diff_color = "#64748b"

        diff_str = f"{diff:+.1f}"
        if abs(last_val) > 0.001:
            pct_diff = (diff / last_val) * 100
            diff_badge = f"{diff_str} ({pct_diff:+.0f}%)"
        else:
            diff_badge = f"{diff_str}"

        # Text label next to bars
        ax.text(
            higher_bar + offset_padding,
            y_pos[i],
            f"Aktuell: {curr_val:.1f} | Δ {diff_badge}",
            va="center",
            ha="left",
            fontsize=8.5,
            fontweight="bold",
            color=diff_color,
        )

    # Labels and aesthetics
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight="normal", color="#1e293b")
    ax.invert_yaxis()  # top-down order as defined in list

    ax.set_xlabel("Verbrauch (kWh bzw. m³)", fontsize=10, fontweight="bold", color="#334155", labelpad=8)
    ax.set_title("Energie- & Verbrauchsvergleich", fontsize=13, fontweight="bold", color="#0f172a", pad=14)

    # Grid & borders
    ax.grid(axis="x", linestyle="--", alpha=0.5, color="#cbd5e1")
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")

    # Legend
    ax.legend(loc="lower right", frameon=True, facecolor="#ffffff", edgecolor="#e2e8f0", fontsize=9)

    # Ensure annotations fit inside plot area
    ax.set_xlim(left=0, right=max_val * 1.35)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight", dpi=150)
    plt.close()

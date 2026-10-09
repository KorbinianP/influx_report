"""Create a PNG with a modern card-style bar chart, optimized for clarity and smartphone display."""

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np

from influx_report.helpers import MeasurementSet


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
    - Clean 'Card/Dashboard' layout for each device row
    - Device name and current value/delta badge placed directly ABOVE the bars
    - Prevents wasting horizontal width and keeps bars readable across full width
    - Color-coded delta badges (green for reduction/savings, red for increase)
    - High DPI and modern typography

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
    fig_height = max(6.0, num_items * 0.9 + 1.6)
    fig, ax = plt.subplots(figsize=(8.5, fig_height), dpi=150)

    color_bg = "#ffffff"
    color_last = "#94a3b8"  # slate-400 (neutral historical)
    color_this = "#2563eb"  # royal blue (active current period)
    color_card_bg = "#f8fafc"  # subtle card background per row

    fig.patch.set_facecolor(color_bg)
    ax.set_facecolor(color_bg)

    y_slots = np.arange(num_items)
    bar_height = 0.22

    label_last = format_dates(measurement_sets[0].dates[0])
    label_this = format_dates(measurement_sets[0].dates[1])

    max_val = max(max(values_last, default=0), max(values_this, default=0), 1)

    # Subtle row background tracks
    for i in range(num_items):
        ax.fill_between(
            [0, max_val * 1.02],
            y_slots[i] - 0.46,
            y_slots[i] + 0.36,
            color=color_card_bg,
            zorder=0,
            edgecolor="#f1f5f9",
            linewidth=0.8,
        )

    # Draw bars: Vorjahr lower, Aktuell upper in slot
    ax.barh(
        y_slots + 0.14,
        values_last,
        height=bar_height,
        label=f"Vorjahr ({label_last})",
        color=color_last,
        alpha=0.85,
        edgecolor="none",
        zorder=2,
    )
    ax.barh(
        y_slots - 0.12,
        values_this,
        height=bar_height,
        label=f"Aktuell ({label_this})",
        color=color_this,
        alpha=0.95,
        edgecolor="none",
        zorder=2,
    )

    # Add header line (Name on left, Value & Delta badge on right) directly above bars
    for i in range(num_items):
        diff = differences[i]
        curr_val = values_this[i]
        last_val = values_last[i]
        unit = "m³" if "wasser" in names[i].lower() else "kWh"

        is_pv = "einspeisung" in names[i].lower()
        if diff < 0:
            delta_color = "#dc2626" if is_pv else "#16a34a"  # red if drop in PV, green if drop in consumption
            symbol = "▼"
        elif diff > 0:
            delta_color = "#16a34a" if is_pv else "#dc2626"
            symbol = "▲"
        else:
            delta_color = "#64748b"
            symbol = "•"

        diff_str = f"{diff:+.1f}"
        pct_str = f"({(diff / last_val) * 100:+.0f}%)" if abs(last_val) > 0.001 else ""

        # Left header: Device Name
        ax.text(
            max_val * 0.015,
            y_slots[i] - 0.28,
            names[i],
            va="bottom",
            ha="left",
            fontsize=10.5,
            fontweight="bold",
            color="#0f172a",
            zorder=3,
        )

        # Right header: Current value & Delta Badge
        ax.text(
            max_val * 1.005,
            y_slots[i] - 0.28,
            f"{curr_val:.1f} {unit}   {symbol} {diff_str} {pct_str}",
            va="bottom",
            ha="right",
            fontsize=9.5,
            fontweight="bold",
            color=delta_color,
            zorder=3,
        )

    ax.set_yticks([])  # Remove y axis tick labels since names are in header line
    ax.invert_yaxis()

    ax.set_xlabel("Verbrauch (kWh bzw. m³)", fontsize=9.5, fontweight="bold", color="#475569", labelpad=10)
    ax.set_title("Energie- & Verbrauchsbericht", fontsize=13, fontweight="bold", color="#0f172a", pad=16)

    # Grid & borders
    ax.grid(axis="x", linestyle="--", alpha=0.5, color="#e2e8f0", zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")

    # Legend
    ax.legend(loc="lower right", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8.5)
    ax.set_xlim(left=0, right=max_val * 1.02)

    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight", dpi=150)
    plt.close()

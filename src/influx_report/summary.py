"""Smart energy analysis and summary generation for weekly and monthly reports.

Decomposes household energy into known appliances, correlates E-Auto charging
with total household consumption, computes base-load rest consumption,
and highlights extreme deviations.
"""

from __future__ import annotations

import configparser
import logging
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

from influx_report.helpers import MeasurementSet

logger = logging.getLogger("influx_report.summary")

# Default electricity tariffs in EUR/kWh
DEFAULT_TARIFF_HOUSEHOLD = 0.3108  # 31.08 ct/kWh
DEFAULT_TARIFF_HEATING = 0.2287  # 22.87 ct/kWh
DEFAULT_TARIFF_FEEDIN = 0.08  # 8.00 ct/kWh

# Known individual household devices measured in kWh (excluded: heating, water in m³, solar)
KNOWN_HOUSEHOLD_DEVICES = [
    "E-Auto",
    "Kühlschrank",
    "Waschmaschine",
    "Trockner",
    "TV EG",
    "TV UG",
    "Wasserpumpe",
    "Kochfeld",
    "Backofen",
    "Mikrowelle",
    "Netzwerkschrank",
    "Spülmaschine",
]


def _load_env_file(env_path: Path | None = None) -> dict[str, str]:
    """Loads key=value pairs from .env file without external dependencies."""
    if env_path is None:
        candidates = [
            Path("/home/user/antigravity/.env"),
            Path.cwd() / ".env",
            Path.home() / "antigravity" / ".env",
        ]
        for c in candidates:
            if c.is_file():
                env_path = c
                break

    env_vars: dict[str, str] = {}
    if env_path and env_path.is_file():
        try:
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip().strip("'\"")
        except OSError as exc:
            logger.debug("Could not read .env at %s: %s", env_path, exc)
    return env_vars


def load_tariffs(
    config_file: str | Path = "config.ini",
    env_vars: dict[str, str] | None = None,
) -> dict[str, float]:
    """Loads electricity tariffs from config.ini, env vars, or defaults.

    Returns dict with keys: 'household', 'heating', 'feedin' (values in EUR/kWh).
    """
    tariffs = {
        "household": DEFAULT_TARIFF_HOUSEHOLD,
        "heating": DEFAULT_TARIFF_HEATING,
        "feedin": DEFAULT_TARIFF_FEEDIN,
    }

    # 1. Check config.ini
    config_path = Path(config_file)
    if not config_path.is_file() and (Path.cwd() / config_file).is_file():
        config_path = Path.cwd() / config_file

    if config_path.is_file():
        try:
            cp = configparser.ConfigParser()
            cp.read(config_path)
            if cp.has_section("Tariffs"):
                sec = cp["Tariffs"]
                for key_alias, target in [
                    ("grid_household", "household"),
                    ("household", "household"),
                    ("grid_heating", "heating"),
                    ("heating", "heating"),
                    ("feedin", "feedin"),
                ]:
                    if key_alias in sec:
                        tariffs[target] = float(sec[key_alias])
        except Exception as exc:
            logger.debug("Could not parse tariffs from %s: %s", config_path, exc)

    # 2. Check environment variables
    env = env_vars if env_vars is not None else _load_env_file()
    for env_key, target in [
        ("TARIFF_GRID_HOUSEHOLD", "household"),
        ("STROM_PREIS_HAUSHALT", "household"),
        ("TARIFF_GRID_HEATING", "heating"),
        ("STROM_PREIS_HEIZUNG", "heating"),
        ("TARIFF_FEEDIN", "feedin"),
        ("STROM_PREIS_EINSPEISUNG", "feedin"),
    ]:
        if env_key in env:
            try:
                tariffs[target] = float(env[env_key])
            except ValueError:
                pass

    return tariffs


def generate_energy_summary(
    measurement_sets: Sequence[MeasurementSet],
    is_month: bool = False,
    tariffs: dict[str, float] | None = None,
) -> str:
    """Generates an intelligent, human-readable German text summary of energy consumption.

    Features:
    - E-Auto vs. Household correlation (quantifies E-Auto's impact on household delta)
    - Electricity costs for household and heating based on configured tariffs
    - Rest-Haushalt (base load / unmeasured devices) = Household total - known devices
    - Extreme anomalies (>50% increase or large kWh shifts)
    - Heat pump efficiency (Arbeitszahl) and PV solar feed-in
    - Compact Telegram-friendly markdown formatting (fits < 1024 chars)
    """
    if not measurement_sets:
        return "Keine Messdaten für den Bericht verfügbar."

    if tariffs is None:
        tariffs = load_tariffs()

    t_hh = tariffs.get("household", DEFAULT_TARIFF_HOUSEHOLD)
    t_heat = tariffs.get("heating", DEFAULT_TARIFF_HEATING)
    t_feedin = tariffs.get("feedin", DEFAULT_TARIFF_FEEDIN)

    data_map: dict[str, MeasurementSet] = {ms.name: ms for ms in measurement_sets}

    # Reference timeframes from first measurement
    first_ms = measurement_sets[0]
    tf_curr = first_ms.dates[1]
    ref_short = "VJ" if is_month else "VW"
    period_title = "Monatsbericht" if is_month else "Wochenbericht"
    date_str = f"{tf_curr[0].strftime('%d.%m.')} – {tf_curr[1].strftime('%d.%m.%y')}"

    lines: list[str] = [f"📊 *{period_title} ({date_str})*", ""]

    # --- 1. Household & E-Auto Decomposition ---
    lines.append("🏡 *Haushalt & E-Auto*:")

    haushalt_ms = data_map.get("Haushalt absolut")
    e_auto_ms = data_map.get("E-Auto")

    if haushalt_ms:
        h_past = float(haushalt_ms.data[0])
        h_curr = float(haushalt_ms.data[1])
        h_diff = h_curr - h_past
        h_pct = (h_diff / h_past * 100) if h_past > 0.001 else 0.0
        h_cost = h_curr * t_hh
        cost_str = f" (*{h_cost:.2f} €*)" if t_hh > 0 else ""
        lines.append(f"• Gesamt: *{h_curr:.1f} kWh*{cost_str} ({ref_short}: {h_past:.1f} kWh, *{h_diff:+.1f} kWh / {h_pct:+.0f}%*)")

        # Correlate E-Auto
        if e_auto_ms:
            ea_past = float(e_auto_ms.data[0])
            ea_curr = float(e_auto_ms.data[1])
            ea_diff = ea_curr - ea_past
            ea_pct = (ea_diff / ea_past * 100) if ea_past > 0.001 else 0.0
            lines.append(f"• 🚗 E-Auto: *{ea_curr:.1f} kWh* ({ref_short}: {ea_past:.1f} kWh, *{ea_diff:+.1f} kWh / {ea_pct:+.0f}%*)")

            if abs(h_diff) >= 1.0 and abs(ea_diff) >= 1.0:
                # Same direction: E-Auto explains part or all of household change
                if (h_diff > 0 and ea_diff > 0) or (h_diff < 0 and ea_diff < 0):
                    share = min(100.0, (abs(ea_diff) / abs(h_diff)) * 100.0)
                    trend_verb = "des Anstiegs" if h_diff > 0 else "der Ersparnis"
                    lines.append(f"  ↳ *{share:.0f}%* {trend_verb} stammen vom E-Auto-Laden ({ea_diff:+.1f} kWh).")
                else:
                    lines.append(f"  ↳ E-Auto ({ea_diff:+.1f} kWh) verhielt sich gegenläufig zum Gesamttrend.")

        # Calculate Rest-Haushalt (base load without E-Auto and known big appliances)
        known_past = sum(float(data_map[d].data[0]) for d in KNOWN_HOUSEHOLD_DEVICES if d in data_map)
        known_curr = sum(float(data_map[d].data[1]) for d in KNOWN_HOUSEHOLD_DEVICES if d in data_map)

        rest_past = max(0.0, round(h_past - known_past, 1))
        rest_curr = max(0.0, round(h_curr - known_curr, 1))
        rest_diff = round(rest_curr - rest_past, 1)
        rest_pct = (rest_diff / rest_past * 100) if rest_past > 0.001 else 0.0

        if abs(rest_diff) <= 5.0 or abs(rest_pct) <= 15.0:
            status_text = "stabil"
        elif rest_diff > 5.0:
            status_text = "⚠️ ungewöhnlich gestiegen"
        else:
            status_text = "spürbar gesunken"

        lines.append(
            f"• 💡 Rest-Haushalt (Licht/Standby): *{rest_curr:.1f} kWh* ({ref_short}: {rest_past:.1f} kWh, *{rest_diff:+.1f} kWh*) → {status_text}"
        )
    lines.append("")

    # --- 2. Extreme Outliers / Anomalies in specific devices ---
    anomalies: list[str] = []
    excluded_names = {
        "Haushalt Zähler",
        "Haushalt absolut",
        "Heizung",
        "Heizung absolut",
        "Wärmemenge Heizen",
        "Wärmemenge Warmwasser",
        "Wärmemenge Gesamt",
        "PV Einspeisung",
    }

    for ms in measurement_sets:
        if ms.name in excluded_names:
            continue
        curr = float(ms.data[1])
        past = float(ms.data[0])
        diff = curr - past
        unit = "m³" if "m³" in ms.name else "kWh"

        # Percentage change
        pct = (diff / past * 100) if past > 0.05 else (100.0 if curr > 0.5 else 0.0)

        # Extreme increase: +50% with at least +1.5 kWh/m³, or absolute increase >= 3.0 kWh
        if (pct >= 50.0 and diff >= 1.5) or diff >= 3.0:
            pct_text = f", *+{pct:.0f}%*" if past > 0.05 else ""
            anomalies.append(f"• 🔺 {ms.name}: *{curr:.1f} {unit}* ({ref_short}: {past:.1f}{pct_text}, *+{diff:.1f} {unit}*)")
        # Extreme decrease: -40% with at least -2.0 kWh
        elif (pct <= -40.0 and diff <= -2.0) or diff <= -5.0:
            anomalies.append(f"• 🔻 {ms.name}: *{curr:.1f} {unit}* ({ref_short}: {past:.1f}, *{pct:.0f}% / {diff:.1f} {unit}*)")

    if anomalies:
        lines.append("⚡ *Auffällige Abweichungen*:")
        lines.extend(anomalies)
        lines.append("")

    # --- 3. Heat Pump Efficiency & Solar PV ---
    hp_pv_lines: list[str] = []

    # Heat pump COP and heating electricity cost
    if "Wärmemenge Gesamt" in data_map and "Heizung absolut" in data_map:
        q_val = float(data_map["Wärmemenge Gesamt"].data[1])
        w_val = float(data_map["Heizung absolut"].data[1])
        if w_val > 0.1:
            cop = round(q_val / w_val, 2)
            az_name = "Monatsarbeitszahl (MAZ)" if is_month else "Wochenarbeitszahl (WAZ)"
            heat_cost = w_val * t_heat
            cost_str = f" ~ *{heat_cost:.2f} €*" if t_heat > 0 else ""
            hp_pv_lines.append(f"• 🌡️ {az_name}: *{cop:.2f}* (Wärme: {q_val:.1f} kWh / Strom: {w_val:.1f} kWh{cost_str})")
    elif "Heizung absolut" in data_map:
        w_val = float(data_map["Heizung absolut"].data[1])
        heat_cost = w_val * t_heat
        cost_str = f" (*{heat_cost:.2f} €*)" if t_heat > 0 else ""
        hp_pv_lines.append(f"• ⚡ Heizstrom: *{w_val:.1f} kWh*{cost_str}")

    # PV export
    if "PV Einspeisung" in data_map:
        pv_ms = data_map["PV Einspeisung"]
        pv_past = float(pv_ms.data[0])
        pv_curr = float(pv_ms.data[1])
        pv_diff = pv_curr - pv_past
        pv_pct = f" ({pv_diff / pv_past * 100:+.0f}%)" if pv_past > 0.001 else ""
        pv_earn = pv_curr * t_feedin
        earn_str = f" (*+{pv_earn:.2f} €*)" if t_feedin > 0 and pv_curr > 0 else ""
        hp_pv_lines.append(f"• ☀️ PV Einspeisung: *{pv_curr:.1f} kWh*{earn_str} ({ref_short}: {pv_past:.1f} kWh, *{pv_diff:+.1f} kWh*{pv_pct})")

    if hp_pv_lines:
        lines.append("🌡️ *Wärmepumpe & PV*:")
        lines.extend(hp_pv_lines)

    summary_text = "\n".join(lines).strip()
    return summary_text


def save_summary_to_file(
    summary_text: str,
    filename: str = "report_summary.txt",
    directory: Path | None = None,
) -> Path:
    """Writes the generated summary text to disk."""
    out_dir = directory or Path.cwd()
    out_path = out_dir / filename
    out_path.write_text(summary_text, encoding="utf-8")
    logger.info("Saved report summary to %s", out_path)
    return out_path


def push_summary_to_openhab(
    summary_text: str,
    item_name: str = "Energiebericht_Zusammenfassung",
    openhab_url: str | None = None,
    openhab_token: str | None = None,
) -> bool:
    """Updates the openHAB String item with the summary text via REST API."""
    env = _load_env_file()
    url = openhab_url or env.get("OPENHAB_URL") or "http://openhab.local:8080"
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"
    token = openhab_token or env.get("OPENHAB_TOKEN")

    rest_url = f"{url.rstrip('/')}/rest/items/{item_name}/state"

    req = urllib.request.Request(
        rest_url,
        data=summary_text.encode("utf-8"),
        method="PUT",
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in (200, 202):
                logger.info("Successfully pushed summary to openHAB Item %s", item_name)
                return True
            logger.warning("openHAB REST responded with status %s", response.status)
    except urllib.error.HTTPError as exc:
        logger.warning("Failed to update openHAB Item %s (HTTP %s: %s)", item_name, exc.code, exc.reason)
    except Exception as exc:
        logger.warning("Could not reach openHAB at %s: %s", rest_url, exc)
    return False

# Influx Report

Read and plot energy & utility data from InfluxDB to PNG reports (for OpenHAB & Telegram notifications).

Features & Tooling:
- Python 3.10+ (tested up to 3.12)
- Fast linting & formatting with **Ruff**
- Unit tests & coverage with **pytest**
- Mobile-optimized horizontal bar charts with delta indicators (Vorjahr vs. Aktuell)
- YAML-based measurement configuration (`measurements.yaml`)
- Automatic fallback to the last valid reporting cut-off date (1st of month or Sunday)
- Optional CLI override (`--date YYYY-MM-DD`)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

### 1. InfluxDB Credentials (`config.ini`)
Create a `config.ini` in the project root:

```ini
[InfluxDB]
url=http://urltoinflux:8086
token=my_secret_token
org=organisation_name
bucket=bucket_name
```

### 2. Measurements (`measurements.yaml`)
Add or customize devices in `measurements.yaml`:

```yaml
measurements:
  - name: "Kühlschrank"
    measurement: "Strom_Leistung_Kuehlschrank"
    type: "watt"

  - name: "E-Auto"
    measurement: "GoEChargerEnergyTotal"
    type: "counter"
    scale: 0.1

  - name: "Haushalt Zähler"
    measurement: "SmartMeter_Haushalt_Bezug"
    type: "counter"

  - name: "Heizung"
    measurement: "SmartMeter_HeizungNeu_Bezug"
    type: "counter"
    scale: 0.001
    subtract: "Haushalt Zähler" # Kaskadenschaltung
```

## Usage

- **Normal run (OpenHAB / Cron):**
  ```bash
  python main.py
  ```
  Automatically detects whether today is Sunday or the 1st of the month. If executed on any other day (e.g. Wednesday), it falls back to the most recent Sunday or 1st of the month.

- **Manual run for a specific past date:**
  ```bash
  python main.py --date 2024-10-01
  ```

## Development & Testing

```bash
make lint     # Run Ruff linter
make format   # Format with Ruff
make test     # Run pytest suite with coverage
```

# Influx Report

Read and plot energy & utility data from InfluxDB to PNG reports (for OpenHAB & Telegram notifications).

Features & Tooling:
- Python 3.11+ (tested up to 3.15)
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

### Optional: Modern Typography
For clean modern UI fonts (e.g. **Inter** or **Roboto**) on Linux / OpenHAB systems:
```bash
sudo apt install fonts-inter fonts-roboto
```
*(If neither is installed, Matplotlib automatically falls back to the built-in DejaVu Sans font; no installation is strictly required.)*

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
    subtract: "Haushalt Zähler" # cascaded metering deduction
```

## Usage

### Automated / OpenHAB Execution (`exec.sh`)

For automated execution by OpenHAB (e.g. via `executeCommandLine`) or a cron job, use the shell runner [`exec.sh`](file:///home/user/influx_report/exec.sh):

```bash
./exec.sh
```

**Benefits of `exec.sh`:**
- **Automatic Environment:** Activates the local `.venv` if present, or falls back to system Python.
- **Portable:** Dynamically determines the script directory and works regardless of installation path.
- **Cleanup:** Removes old PNG files in the directory before each run.
- **Logging:** Automatically writes logs to `/var/log/openhab/executable_script.log` if permissions allow.
- **Argument Forwarding:** Forwards CLI arguments, e.g. `./exec.sh --date 2024-10-01`.

### Direct Python Execution

- **Default Run:**
  ```bash
  python -m influx_report.main
  ```
  Automatically detects whether today is Sunday or the 1st of the month. If executed on any other weekday (e.g. Wednesday), it automatically falls back to the most recent reporting cut-off date (Sunday or the 1st of the month).

- **Manual Run for a Historical Target Date:**
  ```bash
  python -m influx_report.main --date 2024-10-01
  ```

## Development & Testing

```bash
make lint     # Run Ruff linter
make format   # Format with Ruff
make test     # Run pytest suite with coverage
```

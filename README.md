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

### Automated / OpenHAB Execution (`exec.sh`)

Für die automatisierte Ausführung durch OpenHAB (z. B. via `executeCommandLine`) oder als Cronjob empfiehlt sich das Shell-Skript [`exec.sh`](file:///home/user/influx_report/exec.sh):

```bash
./exec.sh
```

**Vorteile von `exec.sh`:**
- **Automatisches Environment:** Aktiviert automatisch die lokale `.venv`, falls vorhanden, oder nutzt das System-Python.
- **Portabel:** Ermittelt das Skriptverzeichnis dynamisch und funktioniert an beliebigen Installationspfaden.
- **Aufräumen:** Löscht vor dem Lauf alte PNG-Dateien im Verzeichnis.
- **Logging:** Schreibt Logs bei Vorhandensein von Rechten automatisch nach `/var/log/openhab/executable_script.log`.
- **Parameterweiterleitung:** Unterstützt ebenfalls CLI-Parameter, z. B. `./exec.sh --date 2024-10-01`.

### Direct Python Execution (`main.py`)

- **Standardlauf:**
  ```bash
  python main.py
  ```
  Erkennt automatisch, ob heute Sonntag oder der 1. des Monats ist. Wird das Skript an einem anderen Wochentag (z. B. Mittwoch) aufgerufen, fällt es automatisch auf den zuletzt zurückliegenden Stichtag (Sonntag oder 1. des Monats) zurück.

- **Manueller Lauf für ein bestimmtes historisches Datum:**
  ```bash
  python main.py --date 2024-10-01
  ```

## Development & Testing

```bash
make lint     # Run Ruff linter
make format   # Format with Ruff
make test     # Run pytest suite with coverage
```

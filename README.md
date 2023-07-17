# Influx Report

Read and plot data from influxdb to a png. Currently I am more interested in the tooling than the actual code itself:

- pylint
- yapf
- GitHub Actions

## Requirements

Required python packages can be installed in a venv with these commands:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Some more details

- execute with `python main.py` once venv is active
- code formatting happens with yapf
- code testing with pytest
- coding is done with VSCode on Windows 11 in Ubuntu 22.04 WSL

## Configuration / parameterisation

Create a config.ini with this content:

```ini
[InfluxDB]
url=http://urltoinflux:8086
token=my_secret_token
org=organisation_name
bucket=bucket_name
```

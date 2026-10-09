#!/bin/bash
set -euo pipefail

# Determine script base directory portably
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Optional log redirection if LOG_DIR is set or standard openhab log exists
if [ -d "/var/log/openhab" ] && [ -w "/var/log/openhab" ]; then
    exec 1>>"/var/log/openhab/executable_script.log" 2>&1
fi

echo "=== Influx Report run: $(date) ==="
echo "Working directory: ${SCRIPT_DIR}"

# Activate virtualenv if present in script directory
if [ -f "${SCRIPT_DIR}/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/.venv/bin/activate"
    PYTHON_BIN="python"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
else
    echo "Error: Python binary not found!" >&2
    exit 1
fi

echo "Python executable: $(command -v "${PYTHON_BIN}")"

# Clean up older PNGs in script directory
rm -f "${SCRIPT_DIR}"/*.png 2>/dev/null || true

# Run report generator, passing any CLI arguments through
echo "Running main.py..."
"${PYTHON_BIN}" "${SCRIPT_DIR}/main.py" "$@"

echo "Completed successfully: $(date)"

#!/usr/bin/env bash
# MAL Tools launcher (macOS / Linux)
# Starts the proxy + hub. Press Ctrl-C to stop.

set -e
cd "$(dirname "$0")"

# Find a python interpreter
if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python 3 is required but was not found on PATH."
  echo "Install it from https://www.python.org/downloads/ and re-run."
  exit 1
fi

exec "$PY" mal_proxy.py "$@"

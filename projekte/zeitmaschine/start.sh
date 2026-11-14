#!/usr/bin/env bash
# Zeitmaschine fuer einen gespeicherten Plan starten.
# Aufruf:  ./start.sh plaene/<name>.json [weitere Optionen, z. B. --until 15:55 --seed 7]
# Ergebnis: ergebnisse/<name>.json und ein Text-Chart in der Konsole.
set -euo pipefail
cd "$(dirname "$0")"
plan="${1:?Bitte einen Plan angeben, z. B. ./start.sh plaene/gld-2026-10-26.json}"
shift
name="$(basename "$plan" .json)"
python3 timemachine.py run --plan "$plan" --write "ergebnisse/$name.json" "$@"
python3 timemachine.py chart --from "ergebnisse/$name.json"

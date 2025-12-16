#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"

set -o allexport; source ../.env; set +o allexport

source "$VENV_ACTIVATE"

echo "Tagging duplicates..."
dolma -c "$script_dir/dedup.yaml" dedupe > "/corpus/dedup.log" 2>&1 &
pid="$!"
echo "$pid" > "dedup.pid"
wait "$pid"
rm "dedup.pid"
echo "Done"

echo "Mixing..."
dolma -c "$script_dir/mix.yaml" mix > "/corpus/mix.log" 2>&1 &
pid="$!"
echo "$pid" > "mix.pid"
wait "$pid"
rm "mix.pid"
echo "Done"

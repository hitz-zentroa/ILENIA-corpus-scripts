#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"

set -o allexport; source ../.env; set +o allexport

source "$VENV_ACTIVATE"

echo "Tagging duplicates..."
dolma -c "$script_dir/dedup_uniq.yaml" dedupe > "/corpus/dedup_uniq.log" 2>&1 &
pid="$!"
echo "$pid" > "dedup_uniq.pid"
wait "$pid"
rm "dedup_uniq.pid"
echo "Done"

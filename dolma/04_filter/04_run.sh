#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"

set -o allexport; source ../.env; set +o allexport

source "$VENV_ACTIVATE"

echo "Tagging attributes..."
dolma -c "$script_dir/tag.yaml" tag > "/proiektuak/ilenia-scratch/dolma/clean/tag.log" 2>&1 &
pid="$!"
echo "$pid" > "tag.pid"
wait "$pid"
rm "tag.pid"
echo "Done"

echo "Mixing..."
dolma -c "$script_dir/mix.yaml" mix > "/proiektuak/ilenia-scratch/dolma/clean/mix.log" 2>&1 &
pid="$!"
echo "$pid" > "mix.pid"
wait "$pid"
rm "mix.pid"
echo "Done"

#!/usr/bin/env bash

set -euo pipefail

while IFS= read -r config; do
  uv run --no-sync python -m iamai --config "$config" config-check
done < <(find examples -maxdepth 2 -name 'config.*.toml' | sort)

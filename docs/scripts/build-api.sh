#!/usr/bin/env bash

# Checkout the repository
git clone https://github.com/$VERCEL_GIT_REPO_SLUG.git
cd iamai

# Install dependencies
pdm install -G dev -G docs.old

# Build API Doc
pdm run sophia-doc iamai -o docs/pages/dev-api --anchor-extend --ignore-data --overwrite --exclude-module-name --init-file-name index.md
export IAMAI_DEV=1

npm build
#!/usr/bin/env bash

# Checkout the repository
git clone https://github.com/$VERCEL_GIT_REPO_SLUG.git
cd your-repository-name

# Install dependencies
pip install --upgrade pdm
pdm install -G dev -G docs.old

# Build API Doc
pdm run sophia-doc iamai -o docs.old/docs/dev-api --anchor-extend --ignore-data --overwrite --exclude-module-name --init-file-name index.md
export IAMAI_DEV=1

# Install dependencies for VuePress site
cd docs.old
pnpm install

# Build VuePress site
pnpm docs:build

# Deploy to Vercel (automatically handled by Vercel)

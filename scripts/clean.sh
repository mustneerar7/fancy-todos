#!/usr/bin/env bash

# Remove Python and tool caches from the repo. Skips .venv and .git.
#
# Note: we use `-not -path "./.venv/*"` rather than `-prune` because BSD find's
# `-delete` implies `-depth`, which makes `-prune` useless (children are visited
# before the directory the prune is supposed to exclude).

set -e

EXCLUDES=(
    -not -path "./.venv/*"
    -not -path "./.git/*"
)

DIRS=(
    __pycache__
    .pytest_cache
    .ruff_cache
    .mypy_cache
    htmlcov
    build
    dist
)

FILES=(
    "*.pyc"
    "*.pyo"
    ".coverage"
    ".coverage.*"
)

for name in "${DIRS[@]}"; do
    find . "${EXCLUDES[@]}" -type d -name "$name" -print -exec rm -rf {} +
done

for pattern in "${FILES[@]}"; do
    find . "${EXCLUDES[@]}" -type f -name "$pattern" -print -delete
done

find . "${EXCLUDES[@]}" -type d -name "*.egg-info" -print -exec rm -rf {} +

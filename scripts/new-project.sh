#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<EOF
usage: $(basename "$0") <new-name> <destination-dir>

Clone this repo as a template into a new directory:
  - copies files (excluding .git, .venv, caches, .env, .DS_Store, this script)
  - rewrites the project name in pyproject.toml, README.md, .env.example
  - initializes a fresh git repo on 'main' with a single commit

<new-name> must match: ^[a-z][a-z0-9-]*\$
<destination-dir> must not exist (or must be empty).
EOF
}

if [ "$#" -ne 2 ]; then
    usage >&2
    exit 1
fi

NEW_NAME="$1"
DEST="$2"

if ! [[ "$NEW_NAME" =~ ^[a-z][a-z0-9-]*$ ]]; then
    echo "error: <new-name> must match ^[a-z][a-z0-9-]*\$ (got: $NEW_NAME)" >&2
    exit 1
fi

if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
    echo "error: destination exists and is non-empty: $DEST" >&2
    exit 1
fi

TEMPLATE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$DEST"

rsync -a \
    --exclude='.git/' \
    --exclude='.venv/' \
    --exclude='__pycache__/' \
    --exclude='.ruff_cache/' \
    --exclude='.env' \
    --exclude='.DS_Store' \
    --exclude='scripts/new-project.sh' \
    "$TEMPLATE_ROOT"/ "$DEST"/

sed -i '' "s|^name = \"fancy-todos\"\$|name = \"$NEW_NAME\"|" "$DEST/pyproject.toml"
sed -i '' "s|^# fancy-todos\$|# $NEW_NAME|" "$DEST/README.md"
sed -i '' "s|^PROJECT_NAME=fancy-todos\$|PROJECT_NAME=$NEW_NAME|" "$DEST/.env.example"

cd "$DEST"
git init -b main >/dev/null
git add .
git commit -m "chore: initial commit from fancy-todos template" >/dev/null

cat <<EOF
Created $NEW_NAME at $DEST
Next:
  cd $DEST
  cp .env.example .env   # then edit secrets
  uv sync
  docker compose up -d
  make prestart
EOF

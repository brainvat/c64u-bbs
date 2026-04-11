#!/usr/bin/env bash
#
# install-hooks.sh — Install git hooks from .githooks/ into .git/hooks/
#
# Usage: bash scripts/install-hooks.sh
#

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$REPO_ROOT/.githooks"
HOOKS_DST="$REPO_ROOT/.git/hooks"

if [ ! -d "$HOOKS_SRC" ]; then
  echo "Error: $HOOKS_SRC not found."
  exit 1
fi

echo "Installing git hooks from .githooks/ ..."

for hook in "$HOOKS_SRC"/*; do
  hook_name=$(basename "$hook")
  cp "$hook" "$HOOKS_DST/$hook_name"
  chmod +x "$HOOKS_DST/$hook_name"
  echo "  Installed: $hook_name"
done

echo "Done. Git hooks are active."
echo ""
echo "Alternatively, you can use: git config core.hooksPath .githooks"
echo "to point git directly at the .githooks/ directory."

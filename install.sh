#!/usr/bin/env bash
#
# install.sh — Set up c64u-bbs development environment.
#
# Creates a Python virtual environment, installs dependencies,
# installs git hooks, and runs a smoke test.
#
# Usage:
#   bash install.sh           # Standard install
#   bash install.sh --dev     # Include dev/test dependencies
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$REPO_ROOT/venv"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10
DEV_MODE=false

# Parse args
for arg in "$@"; do
  case "$arg" in
    --dev) DEV_MODE=true ;;
    --help|-h)
      echo "Usage: bash install.sh [--dev]"
      echo "  --dev    Include dev/test dependencies (pytest, ruff)"
      exit 0
      ;;
  esac
done

echo -e "${CYAN}*** c64u-bbs installer ***${NC}"
echo ""

# ── Step 1: Check Python ────────────────────────────────────

echo -n "Checking Python... "

PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo -e "${RED}FAILED${NC}"
  echo ""
  echo -e "${RED}Python not found.${NC} c64u-bbs requires Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+."
  echo ""
  echo "Install Python:"
  echo "  macOS:   brew install python3"
  echo "  Ubuntu:  sudo apt install python3 python3-venv"
  echo "  Windows: https://www.python.org/downloads/"
  exit 1
fi

# Check version
PYTHON_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")

if [ "$PYTHON_MAJOR" -lt "$MIN_PYTHON_MAJOR" ] || \
   { [ "$PYTHON_MAJOR" -eq "$MIN_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$MIN_PYTHON_MINOR" ]; }; then
  echo -e "${RED}FAILED${NC}"
  echo ""
  echo -e "${RED}Python $PYTHON_VERSION found, but ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required.${NC}"
  echo ""
  echo "Upgrade Python:"
  echo "  macOS:   brew upgrade python3"
  echo "  Ubuntu:  sudo apt install python3.10"
  exit 1
fi

echo -e "${GREEN}$PYTHON_VERSION${NC} ($PYTHON)"

# ── Step 2: Check venv module ───────────────────────────────

echo -n "Checking venv module... "
if ! "$PYTHON" -m venv --help &>/dev/null; then
  echo -e "${RED}FAILED${NC}"
  echo ""
  echo -e "${RED}Python venv module not available.${NC}"
  echo ""
  echo "Install it:"
  echo "  Ubuntu/Debian: sudo apt install python3-venv"
  echo "  Fedora:        sudo dnf install python3-venv"
  echo "  macOS:         (included with Homebrew Python)"
  exit 1
fi
echo -e "${GREEN}OK${NC}"

# ── Step 3: Create or reuse venv ────────────────────────────

if [ -d "$VENV_DIR" ]; then
  echo -e "Virtual environment already exists at ${CYAN}venv/${NC}"
  # Verify it's functional
  if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${YELLOW}venv/ appears broken. Recreating...${NC}"
    rm -rf "$VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
    echo -e "Created new virtual environment at ${CYAN}venv/${NC}"
  fi
else
  echo -n "Creating virtual environment... "
  "$PYTHON" -m venv "$VENV_DIR"
  echo -e "${GREEN}OK${NC} (venv/)"
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── Step 4: Install dependencies ────────────────────────────

echo -n "Installing dependencies... "

if [ "$DEV_MODE" = true ]; then
  pip install -q -e ".[dev]" 2>&1 | tail -1
  echo -e "${GREEN}OK${NC} (with dev dependencies)"
else
  pip install -q -e . 2>&1 | tail -1
  echo -e "${GREEN}OK${NC}"
fi

# ── Step 5: Install git hooks ───────────────────────────────

echo -n "Installing git hooks... "
if [ -d "$REPO_ROOT/.git" ]; then
  git config core.hooksPath .githooks
  echo -e "${GREEN}OK${NC} (core.hooksPath → .githooks)"
else
  echo -e "${YELLOW}SKIPPED${NC} (not a git repository)"
fi

# ── Step 6: Smoke test ──────────────────────────────────────

echo -n "Smoke test: c64u --version... "
VERSION_OUTPUT=$(c64u --version 2>&1) || {
  echo -e "${RED}FAILED${NC}"
  echo ""
  echo -e "${RED}The c64u CLI did not start correctly.${NC}"
  echo "Output: $VERSION_OUTPUT"
  echo ""
  echo "Try manually:"
  echo "  source venv/bin/activate"
  echo "  c64u --version"
  exit 1
}
echo -e "${GREEN}$VERSION_OUTPUT${NC}"

echo -n "Smoke test: c64u --help... "
HELP_OUTPUT=$(c64u --help 2>&1) || {
  echo -e "${RED}FAILED${NC}"
  echo ""
  echo "c64u --help failed. Something is wrong with the CLI setup."
  exit 1
}
echo -e "${GREEN}OK${NC}"

# ── Step 7: Run tests (dev mode only) ───────────────────────

if [ "$DEV_MODE" = true ]; then
  echo -n "Running tests... "
  TEST_OUTPUT=$(pytest -q 2>&1) || {
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "$TEST_OUTPUT"
    echo ""
    echo "Tests failed. Check the output above."
    exit 1
  }
  PASS_COUNT=$(echo "$TEST_OUTPUT" | grep -o '[0-9]* passed' || echo "")
  echo -e "${GREEN}$PASS_COUNT${NC}"
fi

# ── Done ────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}*** Installation complete ***${NC}"
echo ""
echo "To activate the environment:"
echo -e "  ${CYAN}source venv/bin/activate${NC}"
echo ""
echo "To connect to your C64U:"
echo -e "  ${CYAN}c64u --host <ip-address> info${NC}"
echo ""
echo "To save your C64U host for future use:"
echo -e "  ${CYAN}c64u config init${NC}  (coming soon)"
echo ""
if [ "$DEV_MODE" = false ]; then
  echo "To install dev/test dependencies later:"
  echo -e "  ${CYAN}bash install.sh --dev${NC}"
  echo ""
fi

#!/usr/bin/env bash
# fetch-imagebbs.sh — Locate the Image BBS 3.0 download and install it locally.
#
# This script does NOT download the files automatically. It directs
# the user to the 8-Bit Boyz download page, then looks for the ZIP
# in common download directories and extracts the D81 images into
# assets/bbs/imagebbs/.

set -euo pipefail

DOWNLOAD_URL="https://8bitboyz.com/download/image-3-0-install-february-2026/"
ZIP_NAME="Image-Instal-3.0-Feb-2026.zip"
DEST_DIR="$(cd "$(dirname "$0")/.." && pwd)/assets/bbs/imagebbs"

# Files we need from the ZIP
REQUIRED_FILES=("Master_D1_260125.d81" "Master_D2_260125.d81")

# Check if already installed
if [[ -f "$DEST_DIR/Master_D1_260125.d81" && -f "$DEST_DIR/Master_D2_260125.d81" ]]; then
    echo "Image BBS disk images already installed in:"
    echo "  $DEST_DIR"
    ls -lh "$DEST_DIR"/*.d81
    exit 0
fi

# Search common download locations
SEARCH_DIRS=(
    "$HOME/Downloads"
    "$HOME/Desktop"
    "$HOME/Desktop/C64/BBS"
    "$HOME/Desktop/C64/BBS/Image-Instal-3"
)

echo "========================================"
echo " Image BBS v3.0 — Disk Image Setup"
echo "========================================"
echo ""
echo "This project requires the Image BBS 3.0 disk images from the"
echo "8-Bit Boyz community. These are not included in the repository."
echo ""
echo "Download from:"
echo "  $DOWNLOAD_URL"
echo ""
echo "Expected file: $ZIP_NAME"
echo ""

# Look for the ZIP file
ZIP_PATH=""
for dir in "${SEARCH_DIRS[@]}"; do
    candidate="$dir/$ZIP_NAME"
    if [[ -f "$candidate" ]]; then
        ZIP_PATH="$candidate"
        break
    fi
done

# Also look for loose D81 files (user may have already extracted)
LOOSE_D1=""
for dir in "${SEARCH_DIRS[@]}"; do
    candidate="$dir/Master_D1_260125.d81"
    if [[ -f "$candidate" ]]; then
        LOOSE_D1="$dir"
        break
    fi
done

if [[ -n "$LOOSE_D1" ]]; then
    echo "Found extracted D81 files in: $LOOSE_D1"
    mkdir -p "$DEST_DIR"
    for f in "${REQUIRED_FILES[@]}"; do
        if [[ -f "$LOOSE_D1/$f" ]]; then
            cp "$LOOSE_D1/$f" "$DEST_DIR/$f"
            echo "  Copied $f"
        else
            echo "  WARNING: $f not found in $LOOSE_D1"
        fi
    done
elif [[ -n "$ZIP_PATH" ]]; then
    echo "Found ZIP at: $ZIP_PATH"
    echo "Extracting D81 images..."
    mkdir -p "$DEST_DIR"
    for f in "${REQUIRED_FILES[@]}"; do
        unzip -o -j "$ZIP_PATH" "$f" -d "$DEST_DIR" 2>/dev/null || {
            echo "  WARNING: Could not extract $f from ZIP"
        }
    done
else
    echo "Could not find $ZIP_NAME in:"
    for dir in "${SEARCH_DIRS[@]}"; do
        echo "  $dir"
    done
    echo ""
    echo "Please download the file from the URL above, then run this script again."
    exit 1
fi

# Verify
echo ""
MISSING=0
for f in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$DEST_DIR/$f" ]]; then
        SIZE=$(ls -lh "$DEST_DIR/$f" | awk '{print $5}')
        echo "  OK: $f ($SIZE)"
    else
        echo "  MISSING: $f"
        MISSING=1
    fi
done

if [[ $MISSING -eq 0 ]]; then
    echo ""
    echo "Image BBS disk images installed to:"
    echo "  $DEST_DIR"
    echo ""
    echo "You can now deploy with: c64u bbs deploy imagebbs"
else
    echo ""
    echo "Some files are missing. Please check the ZIP contents and try again."
    exit 1
fi

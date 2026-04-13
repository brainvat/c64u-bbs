#!/usr/bin/env bash
#
# setup-bbs.sh — Image BBS disk image management for c64u-bbs.
#
# Menu-driven tool to download, install, and configure Image BBS 3.0
# disk images for use with the C64 Ultimate or VICE emulator.
#
# Usage:
#   bash setup-bbs.sh
#

set -euo pipefail

# ── Colors ─────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
ASSETS_DIR="$REPO_ROOT/assets/bbs/imagebbs"
UPSTREAM_DIR="$ASSETS_DIR/upstream"
GOLDEN_DIR="$ASSETS_DIR"

# Image BBS download URL (February 2026 release)
DOWNLOAD_URL="https://8bitboyz.com/download/image-3-0-install-february-2026/"
ORIGIN_SITE="https://8bitboyz.com"

# Disk image filenames
D1="Master_D1_260125.d81"
D2="Master_D2_260125.d81"
UTILS="3.0 utilities.d81"

# ── Helpers ────────────────────────────────────────────────

banner() {
  echo ""
  echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
  echo -e "${CYAN}║${NC}  ${BOLD}Image BBS 3.0 — Disk Image Setup${NC}               ${CYAN}║${NC}"
  echo -e "${CYAN}║${NC}  ${DIM}c64u-bbs project${NC}                               ${CYAN}║${NC}"
  echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "  ${DIM}Image BBS v3.0 (C) 2020-2025 NISSA BBS Software${NC}"
  echo -e "  ${DIM}Ray Kelm, John Moore, Jack Followay, Larry Hedman${NC}"
  echo -e "  ${DIM}Distributed by the 8-Bit Boyz: ${ORIGIN_SITE}${NC}"
  echo ""
}

check_file() {
  local path="$1"
  local label="$2"
  if [ -f "$path" ]; then
    local size
    size=$(wc -c < "$path" | tr -d ' ')
    echo -e "  ${GREEN}[found]${NC} $label ($size bytes)"
    return 0
  else
    echo -e "  ${RED}[missing]${NC} $label"
    return 1
  fi
}

prompt_yn() {
  local prompt="$1"
  local default="${2:-n}"
  local reply
  if [ "$default" = "y" ]; then
    read -rp "$(echo -e "$prompt ${DIM}[Y/n]${NC} ")" reply
    reply="${reply:-y}"
  else
    read -rp "$(echo -e "$prompt ${DIM}[y/N]${NC} ")" reply
    reply="${reply:-n}"
  fi
  case "$reply" in
    [Yy]*) return 0 ;;
    *) return 1 ;;
  esac
}

# ── Status Check ──────────────────────────────────────────

show_status() {
  echo -e "${BOLD}Current Status:${NC}"
  echo ""
  echo -e "  ${BOLD}Upstream (original downloads):${NC}"
  local upstream_ok=true
  check_file "$UPSTREAM_DIR/$D1" "$D1" || upstream_ok=false
  check_file "$UPSTREAM_DIR/$D2" "$D2" || upstream_ok=false
  check_file "$UPSTREAM_DIR/$UTILS" "$UTILS" || upstream_ok=false
  echo ""
  echo -e "  ${BOLD}Golden (deploy-ready, pre-configured):${NC}"
  local golden_ok=true
  check_file "$GOLDEN_DIR/$D1" "$D1 (programs)" || golden_ok=false
  check_file "$GOLDEN_DIR/$D2" "$D2 (data + user files)" || golden_ok=false
  echo ""
}

# ── Menu Option 1: Download from Origin ────────────────────

do_download() {
  echo -e "${BOLD}Download Image BBS 3.0 from 8bitboyz.com${NC}"
  echo ""
  echo -e "  The Image BBS 3.0 February 2026 release is available at:"
  echo -e "  ${CYAN}${DOWNLOAD_URL}${NC}"
  echo ""
  echo -e "  ${YELLOW}Note:${NC} The download page may require clicking a link to get"
  echo -e "  the actual .zip file. This script will attempt to fetch the"
  echo -e "  disk images directly, but if that fails, download manually"
  echo -e "  and place the files in:"
  echo -e "  ${CYAN}${UPSTREAM_DIR}/${NC}"
  echo ""
  echo -e "  Expected files after download:"
  echo -e "    - $D1"
  echo -e "    - $D2"
  echo -e "    - $UTILS"
  echo ""

  # Check if curl or wget is available
  local fetcher=""
  if command -v curl &>/dev/null; then
    fetcher="curl"
  elif command -v wget &>/dev/null; then
    fetcher="wget"
  fi

  if [ -z "$fetcher" ]; then
    echo -e "${RED}Neither curl nor wget found.${NC} Please download manually."
    echo -e "Visit: ${CYAN}${DOWNLOAD_URL}${NC}"
    echo -e "Place files in: ${CYAN}${UPSTREAM_DIR}/${NC}"
    return 1
  fi

  # The 8bitboyz.com download page typically serves a .zip
  # We'll try to download it, but this may need manual intervention
  echo -e "  ${YELLOW}Automatic download from 8bitboyz.com may not work${NC}"
  echo -e "  ${YELLOW}(the site may use JavaScript-based download links).${NC}"
  echo ""

  if ! prompt_yn "  Try automatic download anyway?"; then
    echo ""
    echo -e "  To download manually:"
    echo -e "    1. Visit ${CYAN}${DOWNLOAD_URL}${NC}"
    echo -e "    2. Download the .zip file"
    echo -e "    3. Extract the D81 files to: ${CYAN}${UPSTREAM_DIR}/${NC}"
    return 0
  fi

  mkdir -p "$UPSTREAM_DIR"

  echo ""
  echo -e "  Attempting download..."

  # Try to fetch the download page and find the actual file link
  local tmpdir
  tmpdir=$(mktemp -d)
  local page_file="$tmpdir/page.html"

  if [ "$fetcher" = "curl" ]; then
    curl -sL -o "$page_file" "$DOWNLOAD_URL" 2>/dev/null || true
  else
    wget -q -O "$page_file" "$DOWNLOAD_URL" 2>/dev/null || true
  fi

  # Look for a direct .zip link in the page
  local zip_url=""
  if [ -f "$page_file" ]; then
    zip_url=$(grep -oE 'https?://[^"'"'"']+\.(zip|ZIP)' "$page_file" | head -1 || true)
  fi

  if [ -n "$zip_url" ]; then
    echo -e "  Found download link: ${DIM}$zip_url${NC}"
    local zip_file="$tmpdir/imagebbs.zip"

    if [ "$fetcher" = "curl" ]; then
      curl -sL -o "$zip_file" "$zip_url"
    else
      wget -q -O "$zip_file" "$zip_url"
    fi

    if [ -f "$zip_file" ] && [ -s "$zip_file" ]; then
      echo -e "  Extracting..."
      unzip -o -j "$zip_file" "*.d81" "*.D81" "*.txt" -d "$UPSTREAM_DIR" 2>/dev/null || \
        unzip -o "$zip_file" -d "$tmpdir/extracted" 2>/dev/null

      # If extracted to subdirectory, find and copy D81 files
      if [ -d "$tmpdir/extracted" ]; then
        find "$tmpdir/extracted" -name "*.d81" -o -name "*.D81" -o -name "*.txt" | while read -r f; do
          cp "$f" "$UPSTREAM_DIR/"
        done
      fi

      echo -e "  ${GREEN}Download complete.${NC}"
    else
      echo -e "  ${RED}Download failed or empty file.${NC}"
    fi
  else
    echo -e "  ${RED}Could not find download link on page.${NC}"
    echo ""
    echo -e "  Please download manually:"
    echo -e "    1. Visit ${CYAN}${DOWNLOAD_URL}${NC}"
    echo -e "    2. Download the .zip file"
    echo -e "    3. Extract to: ${CYAN}${UPSTREAM_DIR}/${NC}"
  fi

  rm -rf "$tmpdir"
  echo ""
  show_status
}

# ── Menu Option 2: Install Base Images ─────────────────────

do_install_base() {
  echo -e "${BOLD}Install Base (Upstream) Images${NC}"
  echo ""

  # Check upstream files exist
  local missing=false
  for f in "$D1" "$D2"; do
    if [ ! -f "$UPSTREAM_DIR/$f" ]; then
      echo -e "  ${RED}Missing:${NC} $UPSTREAM_DIR/$f"
      missing=true
    fi
  done
  if [ "$missing" = true ]; then
    echo ""
    echo -e "  ${RED}Upstream files not found.${NC} Run option 1 first to download them."
    return 1
  fi

  echo -e "  These are the unmodified Image BBS 3.0 disk images — no sysop"
  echo -e "  account, no modem config. You will need to run the setup wizard"
  echo -e "  on the target machine."
  echo ""
  echo -e "  ${BOLD}Where do you want to install?${NC}"
  echo ""
  echo -e "    ${CYAN}1)${NC}  C64 Ultimate — upload via FTP to the C64U's SD card"
  echo -e "    ${CYAN}2)${NC}  VICE emulator — copy to a local directory for use with VICE"
  echo -e "    ${CYAN}3)${NC}  Cancel"
  echo ""
  read -rp "  Choice [1-3]: " choice

  case "$choice" in
    1) install_to_c64u "$UPSTREAM_DIR/$D1" "$UPSTREAM_DIR/$D2" "base" ;;
    2) install_to_vice "$UPSTREAM_DIR/$D1" "$UPSTREAM_DIR/$D2" "base" ;;
    *) echo "  Cancelled." ;;
  esac
}

# ── Menu Option 3: Install Golden Images ───────────────────

do_install_golden() {
  echo -e "${BOLD}Install Pre-Configured (Golden) Images${NC}"
  echo ""

  # Check golden files exist
  local missing=false
  for f in "$D1" "$D2"; do
    if [ ! -f "$GOLDEN_DIR/$f" ]; then
      echo -e "  ${RED}Missing:${NC} $GOLDEN_DIR/$f"
      missing=true
    fi
  done
  if [ "$missing" = true ]; then
    echo ""
    echo -e "  ${RED}Golden images not found.${NC}"
    return 1
  fi

  echo -e "  These are pre-configured for SwiftLink at \$DE00 with a working"
  echo -e "  sysop account. Ready to boot — the BBS reaches its idle screen"
  echo -e "  after loading."
  echo ""
  echo -e "  ${DIM}See assets/bbs/imagebbs/PROVENANCE.md for what was changed.${NC}"
  echo ""
  echo -e "  ${BOLD}Where do you want to install?${NC}"
  echo ""
  echo -e "    ${CYAN}1)${NC}  C64 Ultimate — upload via FTP to the C64U's SD card"
  echo -e "    ${CYAN}2)${NC}  VICE emulator — copy to a local directory for use with VICE"
  echo -e "    ${CYAN}3)${NC}  Cancel"
  echo ""
  read -rp "  Choice [1-3]: " choice

  case "$choice" in
    1) install_to_c64u "$GOLDEN_DIR/$D1" "$GOLDEN_DIR/$D2" "golden" ;;
    2) install_to_vice "$GOLDEN_DIR/$D1" "$GOLDEN_DIR/$D2" "golden" ;;
    *) echo "  Cancelled." ;;
  esac
}

# ── Install to C64U ────────────────────────────────────────

install_to_c64u() {
  local d1_path="$1"
  local d2_path="$2"
  local label="$3"

  echo ""
  echo -e "  ${BOLD}C64 Ultimate Setup${NC}"
  echo ""

  # Collect connection info
  local host=""
  local pw=""
  local sd_dir="/SD/bbs"

  # Check for existing config
  local config_file="$HOME/.c64u.json"
  if [ -f "$config_file" ]; then
    local saved_host
    saved_host=$(python3 -c "import json; print(json.load(open('$config_file')).get('host',''))" 2>/dev/null || true)
    if [ -n "$saved_host" ]; then
      echo -e "  Found saved C64U host: ${CYAN}$saved_host${NC}"
      if prompt_yn "  Use this host?" "y"; then
        host="$saved_host"
        pw=$(python3 -c "import json; print(json.load(open('$config_file')).get('pw',''))" 2>/dev/null || true)
      fi
    fi
  fi

  if [ -z "$host" ]; then
    read -rp "  C64U IP address: " host
    if [ -z "$host" ]; then
      echo -e "  ${RED}No IP address provided.${NC}"
      return 1
    fi

    read -rp "  C64U network key (press Enter for none): " pw
  fi

  # Test connectivity
  echo ""
  echo -n "  Testing connection to $host... "
  if ! ping -c1 -W2 "$host" &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo -e "  ${RED}Cannot reach $host.${NC} Check the IP address and network."
    return 1
  fi
  echo -e "${GREEN}OK${NC}"

  # Test FTP
  echo -n "  Testing FTP access... "
  if ! command -v curl &>/dev/null; then
    echo -e "${RED}FAILED${NC} (curl not found)"
    return 1
  fi

  local ftp_url="ftp://$host"
  if [ -n "$pw" ]; then
    ftp_url="ftp://admin:${pw}@${host}"
  fi

  if ! curl -s --max-time 5 --list-only "$ftp_url/" &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo -e "  ${RED}FTP connection failed.${NC} Check that the C64U's network is enabled."
    return 1
  fi
  echo -e "${GREEN}OK${NC}"

  # Create target directory and upload
  echo -e "  Uploading to ${CYAN}${sd_dir}/${NC}..."

  curl -s --ftp-create-dirs -T "$d1_path" "${ftp_url}${sd_dir}/${D1}" && \
    echo -e "  ${GREEN}[uploaded]${NC} $D1" || \
    { echo -e "  ${RED}[failed]${NC} $D1"; return 1; }

  curl -s --ftp-create-dirs -T "$d2_path" "${ftp_url}${sd_dir}/${D2}" && \
    echo -e "  ${GREEN}[uploaded]${NC} $D2" || \
    { echo -e "  ${RED}[failed]${NC} $D2"; return 1; }

  # Blank the modem welcome text so callers see the BBS directly
  echo -ne "\r\n" | curl -s -T - "${ftp_url}/flash/welcome.txt" && \
    echo -e "  ${GREEN}[blanked]${NC} modem welcome text" || true

  echo ""
  echo -e "  ${GREEN}Upload complete.${NC} Disk images are at ${sd_dir}/ on the C64U."

  # Save config for future use
  if prompt_yn "  Save C64U connection for future use?" "y"; then
    python3 -c "
import json, os
cfg = {'host': '$host', 'pw': '$pw'}
path = os.path.expanduser('~/.c64u.json')
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
os.chmod(path, 0o600)
" 2>/dev/null && echo -e "  Saved to ${CYAN}~/.c64u.json${NC}" || true
  fi

  echo ""
  if [ "$label" = "golden" ]; then
    echo -e "  ${BOLD}Next steps:${NC}"
    echo -e "    ${CYAN}source venv/bin/activate${NC}"
    echo -e "    ${CYAN}c64u --host $host bbs deploy${NC}"
    echo ""
    echo -e "  Or boot manually on the C64U:"
    echo -e "    Mount ${D1} on Drive A, ${D2} on Drive B (both 1581 mode)"
    echo -e "    LOAD\"BOOT 3.0\",8,1 then RUN"
  else
    echo -e "  ${BOLD}Next steps:${NC}"
    echo -e "    Mount ${D1} on Drive A, ${D2} on Drive B (both 1581 mode)"
    echo -e "    LOAD\"BOOT 3.0\",8,1 then RUN"
    echo -e "    Follow the Image BBS setup wizard"
  fi
  echo ""
}

# ── Install to VICE ────────────────────────────────────────

install_to_vice() {
  local d1_path="$1"
  local d2_path="$2"
  local label="$3"

  echo ""
  echo -e "  ${BOLD}VICE Emulator Setup${NC}"
  echo ""

  # Default to ~/Desktop or prompt
  local default_dir="$HOME/Desktop/ImageBBS"
  read -rp "  Destination directory [$default_dir]: " dest_dir
  dest_dir="${dest_dir:-$default_dir}"

  mkdir -p "$dest_dir"

  cp "$d1_path" "$dest_dir/$D1"
  echo -e "  ${GREEN}[copied]${NC} $D1"

  cp "$d2_path" "$dest_dir/$D2"
  echo -e "  ${GREEN}[copied]${NC} $D2"

  echo ""
  echo -e "  ${GREEN}Files copied to ${CYAN}${dest_dir}/${NC}"

  # Try to find VICE
  local vice_bin=""
  for candidate in \
    "/Applications/VICE/bin/x64sc" \
    "/usr/local/bin/x64sc" \
    "$HOME/Desktop/Clean Up Later/vice-arm64-gtk3-3.9/bin/x64sc" \
    "$(command -v x64sc 2>/dev/null || true)"; do
    if [ -n "$candidate" ] && [ -x "$candidate" ]; then
      vice_bin="$candidate"
      break
    fi
  done

  echo ""
  echo -e "  ${BOLD}To boot in VICE:${NC}"
  if [ -n "$vice_bin" ]; then
    echo -e "    ${CYAN}\"$vice_bin\" -drive8type 1581 -autostart \"$dest_dir/$D1\" -drive9type 1581 -9 \"$dest_dir/$D2\"${NC}"
  else
    echo -e "    ${CYAN}x64sc -drive8type 1581 -autostart \"$dest_dir/$D1\" -drive9type 1581 -9 \"$dest_dir/$D2\"${NC}"
  fi
  echo ""
  echo -e "  Then at the READY prompt:"
  echo -e "    ${CYAN}LOAD\"BOOT 3.0\",8,1${NC}"
  echo -e "    ${CYAN}RUN${NC}"

  if [ "$label" = "golden" ]; then
    echo ""
    echo -e "  The BBS will boot to the idle screen. Login with:"
    echo -e "    F1 (full screen) > F7 (logon) > I (instant login)"
  else
    echo ""
    echo -e "  Choose option 1 (Configure a New BBS) in the setup wizard."
    echo -e "  See the Sysop Guide for configuration details."
  fi

  echo ""

  if [ -n "$vice_bin" ] && prompt_yn "  Launch VICE now?"; then
    echo -e "  Starting VICE..."
    "$vice_bin" -drive8type 1581 -autostart "$dest_dir/$D1" \
      -drive9type 1581 -9 "$dest_dir/$D2" &
    echo -e "  ${GREEN}VICE launched.${NC}"
  fi
  echo ""
}

# ── Main Menu ──────────────────────────────────────────────

main() {
  banner
  show_status

  while true; do
    echo -e "${BOLD}What would you like to do?${NC}"
    echo ""
    echo -e "  ${CYAN}1)${NC}  Download base Image BBS 3.0 files from 8bitboyz.com"
    echo -e "  ${CYAN}2)${NC}  Install base (unmodified) images to C64U or VICE"
    echo -e "  ${CYAN}3)${NC}  Install pre-configured (golden) images to C64U or VICE"
    echo -e "  ${CYAN}4)${NC}  Show file status"
    echo -e "  ${CYAN}q)${NC}  Quit"
    echo ""
    read -rp "  Choice [1-4/q]: " choice

    echo ""
    case "$choice" in
      1) do_download ;;
      2) do_install_base ;;
      3) do_install_golden ;;
      4) show_status ;;
      q|Q) echo "  Bye."; echo ""; break ;;
      *) echo -e "  ${RED}Invalid choice.${NC}" ;;
    esac
    echo ""
  done
}

main

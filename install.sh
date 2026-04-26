#!/usr/bin/env bash
# Epsimo CLI Installer for macOS / Linux
# Usage:
#   Install:   curl -fsSL https://raw.githubusercontent.com/thierryteisseire/epsimo-cli/main/install.sh | bash
#   Uninstall: curl -fsSL https://raw.githubusercontent.com/thierryteisseire/epsimo-cli/main/install.sh | bash -s -- --uninstall
set -euo pipefail

VERSION="${EPSIMO_VERSION:-latest}"
INSTALL_DIR="${EPSIMO_HOME:-$HOME/.epsimo}"
REPO="thierryteisseire/epsimo-cli"
BIN_LINK="/usr/local/bin/epsimo"
LOCAL_BIN="$HOME/.local/bin"

# --- colours (if tty) ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; RESET=''
fi
info()  { echo -e "${GREEN}▸${RESET} $*"; }
warn()  { echo -e "${YELLOW}▸${RESET} $*"; }
error() { echo -e "${RED}✖${RESET} $*" >&2; }

# --- uninstall ---
if [ "${1:-}" = "--uninstall" ]; then
  info "Uninstalling Epsimo CLI..."
  rm -f "$BIN_LINK" "$LOCAL_BIN/epsimo" 2>/dev/null || true
  if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    info "Removed $INSTALL_DIR"
  fi
  info "✅ Epsimo CLI uninstalled."
  echo "  Note: ~/.epsimo_token was preserved. Remove manually if desired."
  exit 0
fi

# --- pre-flight ---
info "Epsimo CLI Installer"
echo ""

# Check Python 3.8+
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    py_ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
    major=$(echo "$py_ver" | cut -d. -f1)
    minor=$(echo "$py_ver" | cut -d. -f2)
    if [ "${major:-0}" -ge 3 ] && [ "${minor:-0}" -ge 8 ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  error "Python 3.8+ is required but not found."
  echo "  Install Python: https://www.python.org/downloads/"
  exit 1
fi
info "Using $PYTHON ($py_ver)"

# Check git
if ! command -v git &>/dev/null; then
  error "git is required but not found."
  exit 1
fi

# --- install ---
if [ -d "$INSTALL_DIR" ]; then
  warn "Existing installation found at $INSTALL_DIR"
  info "Updating..."
  cd "$INSTALL_DIR/repo"
  git pull --quiet origin main 2>/dev/null || git pull --quiet origin master 2>/dev/null || true
else
  info "Installing to $INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"

  if [ "$VERSION" = "latest" ]; then
    git clone --quiet --depth 1 "https://github.com/$REPO.git" "$INSTALL_DIR/repo"
  else
    git clone --quiet --depth 1 --branch "$VERSION" "https://github.com/$REPO.git" "$INSTALL_DIR/repo"
  fi
fi

# --- venv ---
VENV="$INSTALL_DIR/venv"
if [ ! -d "$VENV" ]; then
  info "Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
fi

info "Installing epsimo package..."
"$VENV/bin/pip" install --quiet --upgrade pip 2>/dev/null || true
"$VENV/bin/pip" install --quiet -e "$INSTALL_DIR/repo"

# --- link to PATH ---
EPSIMO_BIN="$VENV/bin/epsimo"

# Try /usr/local/bin first (needs sudo on some systems)
if [ -w "$(dirname "$BIN_LINK")" ] || [ -w "$BIN_LINK" ] 2>/dev/null; then
  ln -sf "$EPSIMO_BIN" "$BIN_LINK"
  info "Linked epsimo → $BIN_LINK"
else
  # Fallback: add to ~/.local/bin (no sudo needed)
  LOCAL_BIN="$HOME/.local/bin"
  mkdir -p "$LOCAL_BIN"
  ln -sf "$EPSIMO_BIN" "$LOCAL_BIN/epsimo"
  info "Linked epsimo → $LOCAL_BIN/epsimo"

  # Ensure ~/.local/bin is in PATH
  if ! echo "$PATH" | grep -q "$LOCAL_BIN"; then
    SHELL_RC=""
    case "$(basename "$SHELL")" in
      zsh)  SHELL_RC="$HOME/.zshrc" ;;
      bash) SHELL_RC="$HOME/.bashrc" ;;
      fish) SHELL_RC="$HOME/.config/fish/config.fish" ;;
    esac
    if [ -n "$SHELL_RC" ]; then
      echo "export PATH=\"$LOCAL_BIN:\$PATH\"" >> "$SHELL_RC"
      warn "Added $LOCAL_BIN to PATH in $SHELL_RC — restart your shell or run:"
      echo "  export PATH=\"$LOCAL_BIN:\$PATH\""
    fi
  fi
fi

# --- done ---
echo ""
info "✅ Epsimo CLI installed successfully!"
echo ""
echo "  Get started:"
echo "    epsimo auth          # Login to your account"
echo "    epsimo init          # Initialize a project"
echo "    epsimo chat          # Start chatting"
echo "    epsimo tools         # List available tools"
echo ""
echo "  Uninstall:"
echo "    curl -fsSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash -s -- --uninstall"
echo ""

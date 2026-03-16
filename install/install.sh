#!/bin/sh
set -e

# MinerU CLI installer
# Usage: curl -fsSL https://mineru.net/install.sh | sh
#
# Environment variables:
#   MINERU_VERSION   - version to install (default: "latest")
#   MINERU_BASE_URL  - override OSS base URL
#   INSTALL_DIR      - install directory (default: /usr/local/bin)

VERSION="${MINERU_VERSION:-latest}"
BASE_URL="${MINERU_BASE_URL:-https://mineru.net/cli}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"

detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS" in
        Linux)  OS="linux" ;;
        Darwin) OS="darwin" ;;
        *)      echo "Error: unsupported OS: $OS"; exit 1 ;;
    esac

    case "$ARCH" in
        x86_64|amd64)   ARCH="amd64" ;;
        aarch64|arm64)  ARCH="arm64" ;;
        *)              echo "Error: unsupported architecture: $ARCH"; exit 1 ;;
    esac
}

download_and_install() {
    BINARY="mineru-${OS}-${ARCH}"
    URL="${BASE_URL}/${VERSION}/${BINARY}"
    TMP="$(mktemp)"

    echo "Downloading mineru ${VERSION} for ${OS}/${ARCH}..."
    echo "  ${URL}"

    if command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$TMP" "$URL"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$TMP" "$URL"
    else
        echo "Error: curl or wget required"
        exit 1
    fi

    if [ ! -s "$TMP" ]; then
        echo "Error: download failed or file is empty"
        rm -f "$TMP"
        exit 1
    fi

    # Install
    if [ -w "$INSTALL_DIR" ]; then
        mv "$TMP" "${INSTALL_DIR}/mineru"
        chmod +x "${INSTALL_DIR}/mineru"
    else
        echo "Installing to ${INSTALL_DIR} (requires sudo)..."
        sudo mv "$TMP" "${INSTALL_DIR}/mineru"
        sudo chmod +x "${INSTALL_DIR}/mineru"
    fi

    echo ""
    echo "Installed successfully!"
    "${INSTALL_DIR}/mineru" version
    echo ""
    echo "Run 'mineru auth' to configure your API token."
}

detect_platform
download_and_install

#!/usr/bin/env bash
# ============================================================================
# Empaqueta el proyecto Razer Stream Controller en un .tar.gz portable
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATE=$(date +%Y%m%d)
PKG_NAME="loupedeckjuan-${DATE}"
BUILD_DIR="/tmp/${PKG_NAME}"
OUTPUT="${SCRIPT_DIR}/${PKG_NAME}.tar.gz"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

info "Empaquetando proyecto loupedeckjuan..."

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copiar todo excepto venv, .tar.gz anteriores, y __pycache__
rsync -a \
    --exclude='venv' \
    --exclude='*.tar.gz' \
    --exclude='__pycache__' \
    "$SCRIPT_DIR/" "$BUILD_DIR/"

chmod +x "$BUILD_DIR/install.sh"
chmod +x "$BUILD_DIR/package.sh"

# Crear tarball
info "Creando archivo: $OUTPUT"
tar -czf "$OUTPUT" -C /tmp "$PKG_NAME"

rm -rf "$BUILD_DIR"

SIZE=$(du -h "$OUTPUT" | cut -f1)
info "============================================"
info "  Paquete creado!"
info "  Archivo: $OUTPUT"
info "  Tamano:  $SIZE"
info "============================================"
info ""
info "Para instalar en otro equipo:"
info "  1. Copiar ${PKG_NAME}.tar.gz al equipo"
info "  2. tar xzf ${PKG_NAME}.tar.gz"
info "  3. cd ${PKG_NAME}"
info "  4. ./install.sh"

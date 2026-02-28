#!/usr/bin/env bash
# ============================================================================
# Razer Stream Controller / Loupedeck Live - Installer for Pop!_OS / Linux
# ============================================================================
# Todo autocontenido en una sola carpeta: ~/projects/loupedeckjuan
#
# Estructura:
#   loupedeckjuan/
#     app.py              - Aplicacion principal
#     lib/                - Libreria python-loupedeck-live
#     venv/               - Entorno virtual Python
#     assets/             - Imagenes/iconos
#     install.sh          - Este script
#     package.sh          - Empaquetador
#     requirements.txt    - Dependencias pip
#     instrucciones.md    - Documentacion del proyecto
#
# Uso:
#   ./install.sh              (instalar)
#   ./install.sh --uninstall  (desinstalar todo)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/projects/loupedeckjuan"
SERVICE_NAME="loupedeck.service"
SERVICE_DIR="$HOME/.config/systemd/user"
UDEV_FILE="/etc/udev/rules.d/99-loupedeck.rules"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ============================================================================
# Uninstall
# ============================================================================
if [[ "${1:-}" == "--uninstall" ]]; then
    info "Desinstalando Razer Stream Controller..."

    systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$SERVICE_DIR/$SERVICE_NAME"
    systemctl --user daemon-reload 2>/dev/null || true

    if [[ -f "$UDEV_FILE" ]]; then
        info "Eliminando reglas udev (requiere sudo)..."
        sudo rm -f "$UDEV_FILE"
        sudo udevadm control --reload-rules
        sudo udevadm trigger
    fi

    # Solo borra venv, NO borra el proyecto (para no perder tu codigo)
    rm -rf "$INSTALL_DIR/venv"

    info "Desinstalacion completa."
    info "La carpeta del proyecto sigue en: $INSTALL_DIR"
    info "Si quieres borrar todo: rm -rf $INSTALL_DIR"
    info "Para quitar tu usuario del grupo dialout:"
    info "  sudo gpasswd -d \$USER dialout"
    exit 0
fi

# ============================================================================
# Pre-flight checks
# ============================================================================
info "=== Razer Stream Controller - Instalador ==="
echo ""

if [[ "$EUID" -eq 0 ]]; then
    error "No ejecutes este script como root. Ejecutalo como tu usuario normal."
    error "El script pedira sudo cuando sea necesario."
    exit 1
fi

# Buscar Python
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [[ -z "$PYTHON_BIN" ]]; then
    error "Python 3.10+ no encontrado. Instalalo primero:"
    error "  sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PY_VER=$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Python encontrado: $PYTHON_BIN ($PY_VER)"

if ! "$PYTHON_BIN" -m venv --help &>/dev/null; then
    warn "python3-venv no instalado. Instalando..."
    sudo apt install -y "python3-venv" || sudo apt install -y "python${PY_VER}-venv"
fi

if ! "$PYTHON_BIN" -m pip --version &>/dev/null; then
    warn "pip no instalado. Instalando..."
    sudo apt install -y python3-pip
fi

# ============================================================================
# 1. Copiar archivos si se esta instalando desde un paquete extraido
# ============================================================================
if [[ "$SCRIPT_DIR" != "$INSTALL_DIR" ]]; then
    info "Instalando desde paquete externo a: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    # Copiar todo excepto venv y .tar.gz
    rsync -a --exclude='venv' --exclude='*.tar.gz' "$SCRIPT_DIR/" "$INSTALL_DIR/"
    info "Archivos copiados a $INSTALL_DIR"
else
    info "Ejecutando desde el directorio de instalacion: $INSTALL_DIR"
fi

# Verificar que app.py existe
if [[ ! -f "$INSTALL_DIR/app.py" ]]; then
    error "app.py no encontrado en $INSTALL_DIR!"
    exit 1
fi

# Verificar que la libreria existe
if [[ ! -d "$INSTALL_DIR/lib/src/Loupedeck" ]]; then
    # Intentar descargar de GitHub
    info "Libreria loupedeck no encontrada. Descargando de GitHub..."
    if ! command -v git &>/dev/null; then
        sudo apt install -y git
    fi
    TEMP_LIB=$(mktemp -d)
    git clone https://github.com/devleaks/python-loupedeck-live.git "$TEMP_LIB"
    mkdir -p "$INSTALL_DIR/lib"
    cp -r "$TEMP_LIB/src" "$INSTALL_DIR/lib/"
    cp "$TEMP_LIB/pyproject.toml" "$INSTALL_DIR/lib/"
    cp "$TEMP_LIB/VERSION" "$INSTALL_DIR/lib/"
    cp "$TEMP_LIB/LICENSE" "$INSTALL_DIR/lib/" 2>/dev/null || true
    cp "$TEMP_LIB/README.md" "$INSTALL_DIR/lib/" 2>/dev/null || true
    rm -rf "$TEMP_LIB"
fi

# ============================================================================
# 2. Crear entorno virtual e instalar dependencias
# ============================================================================
info "Creando entorno virtual Python..."
if [[ -d "$INSTALL_DIR/venv" ]]; then
    warn "Venv existente encontrado, recreando..."
    rm -rf "$INSTALL_DIR/venv"
fi

"$PYTHON_BIN" -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

info "Instalando dependencias pip..."
pip install --upgrade pip -q
pip install -r "$INSTALL_DIR/requirements.txt" -q

info "Instalando libreria loupedeck..."
pip install -e "$INSTALL_DIR/lib" -q

deactivate
info "Entorno virtual listo."

# ============================================================================
# 3. Reglas udev (requiere sudo)
# ============================================================================
info "Instalando reglas udev (requiere sudo)..."

UDEV_CONTENT='# Razer Stream Controller / Loupedeck Live - Full permissions
# USB device
SUBSYSTEM=="usb", ATTRS{idVendor}=="1532", ATTRS{idProduct}=="0d06", MODE="0666", GROUP="plugdev"
# HID raw
KERNEL=="hidraw*", ATTRS{idVendor}=="1532", ATTRS{idProduct}=="0d06", MODE="0666", GROUP="plugdev"
# Serial port (ttyACM) - THIS IS THE KEY ONE
KERNEL=="ttyACM*", ATTRS{idVendor}=="1532", ATTRS{idProduct}=="0d06", MODE="0666", GROUP="plugdev"'

echo "$UDEV_CONTENT" | sudo tee "$UDEV_FILE" > /dev/null

for old_rule in /etc/udev/rules.d/70-loupedeck.rules /etc/udev/rules.d/70-razer-loupedeck.rules; do
    if [[ -f "$old_rule" ]]; then
        warn "Eliminando regla vieja: $old_rule"
        sudo rm -f "$old_rule"
    fi
done

sudo udevadm control --reload-rules
sudo udevadm trigger
info "Reglas udev instaladas."

# ============================================================================
# 4. Agregar usuario al grupo dialout
# ============================================================================
if ! groups "$USER" | grep -q dialout; then
    info "Agregando $USER al grupo dialout (requiere sudo)..."
    sudo usermod -aG dialout "$USER"
    warn "Fuiste agregado al grupo 'dialout'. Necesitas CERRAR SESION y volver a entrar."
else
    info "Usuario $USER ya esta en el grupo dialout."
fi

# ============================================================================
# 5. Servicio systemd
# ============================================================================
info "Instalando servicio systemd..."
mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/$SERVICE_NAME" <<EOF
[Unit]
Description=Razer Stream Controller / Loupedeck Daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/venv/bin/python -u $INSTALL_DIR/app.py
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=3
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

info "Servicio instalado e iniciado."

# ============================================================================
# Listo!
# ============================================================================
echo ""
info "============================================"
info "  Instalacion completa!"
info "============================================"
echo ""
info "El controlador esta corriendo como servicio."
info "Comandos utiles:"
info "  Estado:      systemctl --user status loupedeck"
info "  Logs:        journalctl --user -u loupedeck -f"
info "  Detener:     systemctl --user stop loupedeck"
info "  Reiniciar:   systemctl --user restart loupedeck"
info "  Desinstalar: $INSTALL_DIR/install.sh --uninstall"
echo ""
if ! groups "$USER" | grep -q dialout; then
    warn "IMPORTANTE: Cierra sesion y vuelve a entrar para que el grupo dialout surta efecto!"
fi

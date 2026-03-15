#!/usr/bin/env python3
"""
Razer Stream Controller / Loupedeck Live - Custom Controller for Pop!_OS COSMIC
Controla volumen, lanza apps, y muestra iconos en pantalla.
Sistema de capas: 8 capas (circle + 1-7), cada una con 12 touch keys + 6 knobs.
"""
import time
import os
import sys
import subprocess
import logging
import glob
import signal
import evdev
from evdev import UInput, ecodes as e

# Agregar la libreria loupedeck desde lib/src (relativa al proyecto)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(APP_DIR, 'lib', 'src'))

from PIL import Image, ImageDraw, ImageFont
from Loupedeck.Devices.LoupedeckLive import LoupedeckLive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
log = logging.getLogger("RazerController")

# Razer Stream Controller USB IDs
VENDOR_ID = "1532"
PRODUCT_ID = "0d06"
RECONNECT_DELAY = 5

# ========== FUENTES ==========
FONT_TEXT = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf", 13)
FONT_TEXT_SIDE = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf", 14)
FONT_ICON = ImageFont.truetype(os.path.join(APP_DIR, "assets", "MaterialIcons-Regular.ttf"), 36)

# ========== MATERIAL ICONS (codepoints) ==========
ICON = {
    "firefox":   "\ue894",  # language (globo)
    "terminal":  "\ueb8e",  # terminal
    "discord":   "\ue0b7",  # chat
    "archivos":  "\ue2c7",  # folder
    "vscode":    "\ue86f",  # code
    "spotify":   "\ue03d",  # queue_music
    "obs":       "\ue04b",  # videocam
    "chrome":    "\ue051",  # web
    "volume":    "\ue050",  # volume_up (para pantalla lateral)
    "mic":       "\ue029",  # mic
    "zoom":      "\ue8ff",  # zoom_in
    "fotos":     "\ue413",  # photo_library
    "servidor":  "\ue875",  # dns (servidor)
    "galco":     "\ue87b",  # extension (rompecabezas)
    "empty":     None,      # sin icono
}

# ========== COLORES PARA CADA CAPA (LED de los botones de abajo) ==========
LAYER_COLORS = {
    "circle": (255, 255, 255),   # Blanco - capa principal
    "1":      (255, 128, 0),     # Naranja
    "2":      (0, 255, 0),       # Verde
    "3":      (114, 137, 218),   # Azul Discord
    "4":      (255, 204, 0),     # Amarillo
    "5":      (0, 120, 215),     # Azul
    "6":      (30, 215, 96),     # Verde Spotify
    "7":      (255, 0, 100),     # Rosa
}

# IDs de los botones fisicos que actuan como selectores de capa
LAYER_BUTTONS = ["circle", "1", "2", "3", "4", "5", "6", "7"]


# ========== DEFINICION DE CAPAS ==========
# Cada capa define:
#   "touch_keys": lista de 12 tuplas (label, icon_key, color, comando)
#   "knobs": dict con knob_id -> {"rotate": func_name, "press": func_name}
#   "side_left": tupla (text, icon_key) para pantalla izquierda
#   "side_right": tupla (text, icon_key) para pantalla derecha
#
# Para touch_keys, si comando es None el boton aparece vacio/deshabilitado.
# Para knobs, func_name es un string que mapea a metodos del controller.

LAYERS = {
    # ---- CAPA PRINCIPAL (circle) ----
    "circle": {
        "name": "Principal",
        "touch_keys": [
            ("Terminal", "terminal", (0, 255, 0),      ["gnome-terminal"]),
            ("Archivos", "archivos", (255, 204, 0),    ["nemo"]),
            ("Fotos",    "fotos",    (255, 0, 150),    ["bash", "/home/juan/scripts/lanzar-procesar-fotos.sh"]),
            ("Servidor", "servidor", (0, 150, 255),    ["gnome-terminal", "--", "ssh", "juan@192.168.0.156"]),
            ("Galco",    "galco",    (0, 200, 255),    ["bash", "/home/juan/scripts/lanzar-proyecto-galco.sh"]),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": {"rotate": "change_volume",   "press": "toggle_mute"},
            "knobTR": {"rotate": "change_mic",       "press": "toggle_mic_mute"},
            "knobCL": None,
            "knobCR": {"rotate": "change_zoom",      "press": "reset_zoom"},
            "knobBL": None,
            "knobBR": None,
        },
        "side_left":  [("VOL", "volume"), None, None],
        "side_right": [("MIC", "mic"), ("ZOOM", "zoom"), None],
    },

    # ---- CAPA 1 ----
    "1": {
        "name": "Capa 1",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C1-L", None),
        "side_right": ("C1-R", None),
    },

    # ---- CAPA 2 ----
    "2": {
        "name": "Capa 2",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C2-L", None),
        "side_right": ("C2-R", None),
    },

    # ---- CAPA 3 ----
    "3": {
        "name": "Capa 3",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C3-L", None),
        "side_right": ("C3-R", None),
    },

    # ---- CAPA 4 ----
    "4": {
        "name": "Capa 4",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C4-L", None),
        "side_right": ("C4-R", None),
    },

    # ---- CAPA 5 ----
    "5": {
        "name": "Capa 5",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C5-L", None),
        "side_right": ("C5-R", None),
    },

    # ---- CAPA 6 ----
    "6": {
        "name": "Capa 6",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C6-L", None),
        "side_right": ("C6-R", None),
    },

    # ---- CAPA 7 ----
    "7": {
        "name": "Capa 7",
        "touch_keys": [
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        ],
        "knobs": {
            "knobTL": None, "knobTR": None,
            "knobCL": None, "knobCR": None,
            "knobBL": None, "knobBR": None,
        },
        "side_left":  ("C7-L", None),
        "side_right": ("C7-R", None),
    },
}


def find_device():
    """Busca automaticamente el puerto serial del Razer Stream Controller.
    Revisa todos los /dev/ttyACM* y compara el vendor/product ID via sysfs.
    Retorna el path (ej: /dev/ttyACM0) o None si no lo encuentra.
    """
    for port in sorted(glob.glob("/dev/ttyACM*")):
        dev_name = os.path.basename(port)
        sysfs_base = f"/sys/class/tty/{dev_name}/device/.."
        vid_path = os.path.join(sysfs_base, "idVendor")
        pid_path = os.path.join(sysfs_base, "idProduct")
        try:
            with open(vid_path) as f:
                vid = f.read().strip()
            with open(pid_path) as f:
                pid = f.read().strip()
            if vid == VENDOR_ID and pid == PRODUCT_ID:
                log.info(f"Dispositivo encontrado en {port} (VID={vid}, PID={pid})")
                return port
        except (FileNotFoundError, PermissionError):
            continue
    return None


def make_key_image(text, icon_char=None, color=(255, 255, 255), bg=(20, 20, 20), border_color=(100, 100, 100)):
    """Crea una imagen de 90x90 con icono Material + texto Ubuntu Mono."""
    img = Image.new("RGB", (90, 90), color=bg)
    draw = ImageDraw.Draw(img)
    draw.rectangle([(2, 2), (87, 87)], outline=border_color, width=2)

    if icon_char and text:
        # Icono centrado arriba
        icon_bbox = FONT_ICON.getbbox(icon_char)
        icon_w = icon_bbox[2] - icon_bbox[0]
        icon_x = (90 - icon_w) // 2
        draw.text((icon_x, 12), icon_char, font=FONT_ICON, fill=color)
        # Texto centrado abajo
        text_bbox = FONT_TEXT.getbbox(text)
        text_w = text_bbox[2] - text_bbox[0]
        text_x = (90 - text_w) // 2
        draw.text((text_x, 58), text, font=FONT_TEXT, fill=color)
    elif text:
        # Solo texto centrado
        text_bbox = FONT_TEXT.getbbox(text)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        text_x = (90 - text_w) // 2
        text_y = (90 - text_h) // 2
        draw.text((text_x, text_y), text, font=FONT_TEXT, fill=color)

    return img


def make_side_image(items):
    """Crea una imagen de 60x270 para las pantallas laterales con multiples iconos+textos.
    items: lista de hasta 3 tuplas (text, icon_char) correspondientes a top, center, bottom.
    Si se pasa un solo item o una tupla, se trata como solo la posicion top para retrocompatibilidad.
    """
    img = Image.new("RGB", (60, 270), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(2, 2), (57, 267)], outline=(60, 60, 60), width=1)

    positions = [20, 110, 200]  # y bases para top, center, bottom

    if isinstance(items, tuple):
        items = [items, None, None]
    elif not isinstance(items, list):
        items = []

    for idx, item in enumerate(items):
        if idx >= 3 or not item:
            continue
            
        if len(item) == 2:
            text, icon_char = item
        else:
            continue

        base_y = positions[idx]

        if icon_char:
            # Icono
            icon_bbox = FONT_ICON.getbbox(icon_char)
            icon_w = icon_bbox[2] - icon_bbox[0]
            icon_x = (60 - icon_w) // 2
            draw.text((icon_x, base_y), icon_char, font=FONT_ICON, fill=(180, 180, 180))
            # Texto debajo del icono
            text_bbox = FONT_TEXT_SIDE.getbbox(text)
            text_w = text_bbox[2] - text_bbox[0]
            text_x = (60 - text_w) // 2
            draw.text((text_x, base_y + 42), text, font=FONT_TEXT_SIDE, fill=(180, 180, 180))
        elif text:
            text_bbox = FONT_TEXT_SIDE.getbbox(text)
            text_w = text_bbox[2] - text_bbox[0]
            text_x = (60 - text_w) // 2
            draw.text((text_x, base_y + 15), text, font=FONT_TEXT_SIDE, fill=(180, 180, 180))

    return img


class RazerController:

    def __init__(self):
        self.deck = None
        self.device_path = None
        self.running = False
        self.current_layer = "circle"  # Capa activa por defecto
        
        # Teclado virtual persistente para simular teclas (zoom, etc.)
        self.virtual_kb = UInput(
            {e.EV_KEY: [e.KEY_LEFTCTRL, e.KEY_EQUAL, e.KEY_MINUS, e.KEY_0]},
            name="loupedeck-virtual-keyboard"
        )
        
        # Manejar senales para un cierre limpio (SIGTERM enviado por systemctl)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        log.info(f"Recibida senal {signum}, apagando controlador de forma segura...")
        self.running = False
        self.disconnect()
        if self.virtual_kb:
            self.virtual_kb.close()
        sys.exit(0)

    def connect(self):
        """Intenta conectar al dispositivo. Retorna True si exitoso."""
        try:
            self.device_path = find_device()
            if not self.device_path:
                log.warning("Razer Stream Controller no detectado en ningun puerto ttyACM.")
                return False

            log.info(f"Conectando al Razer Stream Controller en {self.device_path}...")
            self.deck = LoupedeckLive(path=self.device_path)
            self.deck.set_callback(self.callback)
            time.sleep(0.5)

            log.info("Configurando pantalla...")
            self.deck.set_brightness(80)
            time.sleep(0.3)

            # Limpiar
            self.deck.reset()
            time.sleep(0.5)

            # Dibujar la capa inicial
            self.current_layer = "circle"
            self.draw_current_layer()

            log.info("Controlador activo!")
            return True

        except Exception as e:
            log.error(f"Error conectando: {e}")
            self.deck = None
            return False

    def draw_current_layer(self):
        """Dibuja toda la interfaz segun la capa activa."""
        if not self.deck:
            return

        layer = LAYERS.get(self.current_layer)
        if not layer:
            log.error(f"Capa '{self.current_layer}' no encontrada!")
            return

        log.info(f"Dibujando capa: {layer['name']} ({self.current_layer})")

        # -- Pantallas laterales --
        def map_side_items(side_data):
            if not side_data:
                return []
            if isinstance(side_data, tuple):
                side_data = [side_data]
            mapped = []
            for item in side_data:
                if item and len(item) == 2:
                    text, icon_key = item
                    mapped.append((text, ICON.get(icon_key) if icon_key else None))
                else:
                    mapped.append(None)
            return mapped

        left_items = map_side_items(layer.get("side_left"))
        self.deck.set_key_image("left", make_side_image(left_items))
        time.sleep(0.1)

        right_items = map_side_items(layer.get("side_right"))
        self.deck.set_key_image("right", make_side_image(right_items))
        time.sleep(0.1)

        # -- 12 touch keys --
        for idx, key_def in enumerate(layer["touch_keys"]):
            label, icon_key, color, cmd = key_def
            if label:
                icon_char = ICON.get(icon_key) if icon_key else None
                img = make_key_image(label, icon_char=icon_char, color=color, border_color=color)
            else:
                img = make_key_image("", bg=(10, 10, 10), border_color=(30, 30, 30))
            self.deck.set_key_image(str(idx), img)
            time.sleep(0.05)

        # -- LEDs de botones fisicos: resaltar el activo --
        self.update_layer_leds()

    def update_layer_leds(self):
        """Actualiza los LEDs de los botones fisicos para indicar la capa activa.
        El boton de la capa activa se enciende con su color.
        Los demas se atenuan (color oscuro).
        """
        if not self.deck:
            return

        for btn_id in LAYER_BUTTONS:
            if btn_id == "circle":
                # El boton circle no tiene LED RGB controlable de la misma forma,
                # se controla de otra manera o se omite
                continue

            base_color = LAYER_COLORS.get(btn_id, (100, 100, 100))

            if btn_id == self.current_layer:
                # Capa activa: color brillante
                self.deck.set_button_color(btn_id, base_color)
            else:
                # Capa inactiva: color atenuado (20% del original)
                r, g, b = base_color
                dim = (max(r // 5, 2), max(g // 5, 2), max(b // 5, 2))
                self.deck.set_button_color(btn_id, dim)
            time.sleep(0.02)

    def disconnect(self):
        if self.deck:
            try:
                self.deck.stop()
            except:
                pass
            self.deck = None

    def run(self):
        """Loop principal con reconexion automatica."""
        self.running = True
        while self.running:
            try:
                if self.connect():
                    while self.running:
                        # Verificar que el puerto siga existiendo
                        if self.device_path and not os.path.exists(self.device_path):
                            log.warning("Dispositivo USB desconectado!")
                            break
                        # Verificar que el thread de lectura siga vivo
                        if self.deck and hasattr(self.deck, 'reading_thread'):
                            if self.deck.reading_thread and not self.deck.reading_thread.is_alive():
                                log.warning("Conexion serial perdida, reconectando...")
                                break
                        time.sleep(2)

                self.disconnect()
                if self.running:
                    log.info(f"Reintentando en {RECONNECT_DELAY}s...")
                    time.sleep(RECONNECT_DELAY)

            except KeyboardInterrupt:
                log.info("Saliendo...")
                self.running = False
            except Exception as e:
                log.error(f"Error inesperado: {e}")
                self.disconnect()
                if self.running:
                    time.sleep(RECONNECT_DELAY)

        self.disconnect()
        log.info("Controlador apagado.")

    # ========== ACCIONES ==========

    def change_volume(self, direction):
        try:
            arg = "+2%" if direction == "right" else "-2%"
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", arg], check=False)
        except Exception as e:
            log.error(f"Error volumen: {e}")

    def toggle_mute(self):
        try:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=False)
        except Exception as e:
            log.error(f"Error mute: {e}")

    def change_mic(self, direction):
        try:
            arg = "+2%" if direction == "right" else "-2%"
            subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", arg], check=False)
        except Exception as e:
            log.error(f"Error mic: {e}")

    def toggle_mic_mute(self):
        try:
            subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"], check=False)
        except Exception as e:
            log.error(f"Error mic mute: {e}")

    def change_zoom(self, direction):
        try:
            kb = self.virtual_kb
            kb.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
            if direction == "right":
                kb.write(e.EV_KEY, e.KEY_EQUAL, 1)
                kb.write(e.EV_KEY, e.KEY_EQUAL, 0)
            else:
                kb.write(e.EV_KEY, e.KEY_MINUS, 1)
                kb.write(e.EV_KEY, e.KEY_MINUS, 0)
            kb.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
            kb.syn()
        except Exception as ex:
            log.error(f"Error zoom: {ex}")

    def reset_zoom(self):
        try:
            kb = self.virtual_kb
            kb.write(e.EV_KEY, e.KEY_LEFTCTRL, 1)
            kb.write(e.EV_KEY, e.KEY_0, 1)
            kb.write(e.EV_KEY, e.KEY_0, 0)
            kb.write(e.EV_KEY, e.KEY_LEFTCTRL, 0)
            kb.syn()
        except Exception as ex:
            log.error(f"Error reset zoom: {ex}")

    def launch_app(self, cmd):
        try:
            if self.deck:
                self.deck.vibrate("SHORT")
            subprocess.Popen(cmd, start_new_session=True,
                             cwd=os.path.expanduser("~"),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log.error(f"Error lanzando {cmd}: {e}")

    # ========== CALLBACK ==========

    # Mapa de nombres de funcion -> metodos (se resuelve en runtime)
    KNOB_ACTIONS = {
        "change_volume":    "change_volume",
        "toggle_mute":      "toggle_mute",
        "change_mic":       "change_mic",
        "toggle_mic_mute":  "toggle_mic_mute",
        "change_zoom":      "change_zoom",
        "reset_zoom":       "reset_zoom",
    }

    def callback(self, deck, msg):
        try:
            b_id = msg.get("id")
            action = msg.get("action")
            state = msg.get("state")

            # -- CAMBIO DE CAPA: botones fisicos de abajo --
            if action == "push" and state == "down" and b_id in LAYER_BUTTONS:
                if b_id != self.current_layer:
                    log.info(f"Cambiando a capa: {b_id}")
                    self.current_layer = b_id
                    self.draw_current_layer()
                    if self.deck:
                        self.deck.vibrate("SHORT")
                return

            # -- KNOBS: segun la capa activa --
            layer = LAYERS.get(self.current_layer, {})
            knobs = layer.get("knobs", {})

            if b_id in knobs and knobs[b_id] is not None:
                knob_cfg = knobs[b_id]

                if action == "rotate" and "rotate" in knob_cfg:
                    method_name = knob_cfg["rotate"]
                    method = getattr(self, method_name, None)
                    if method:
                        method(state)
                    return

                if action == "push" and state == "down" and "press" in knob_cfg:
                    method_name = knob_cfg["press"]
                    method = getattr(self, method_name, None)
                    if method:
                        method()
                    return

            # -- PANTALLA TACTIL: segun la capa activa --
            if action == "touchend":
                key = msg.get("key")
                screen = msg.get("screen")
                if screen == "center" and key is not None:
                    touch_keys = layer.get("touch_keys", [])
                    if 0 <= key < len(touch_keys):
                        label, icon_key, color, cmd = touch_keys[key]
                        if cmd:
                            self.launch_app(cmd)

        except Exception as e:
            log.error(f"Error en callback: {e}")


if __name__ == "__main__":
    controller = RazerController()
    controller.run()

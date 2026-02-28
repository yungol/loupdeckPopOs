#!/usr/bin/env python3
"""
Razer Stream Controller / Loupedeck Live - Custom Controller for Pop!_OS COSMIC
Controla volumen, lanza apps, y muestra iconos en pantalla.
"""
import time
import os
import sys
import subprocess
import logging
import glob

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


def make_side_image(text, icon_char=None):
    """Crea una imagen de 60x270 para las pantallas laterales con icono + texto."""
    img = Image.new("RGB", (60, 270), color=(15, 15, 15))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(2, 2), (57, 267)], outline=(60, 60, 60), width=1)

    if icon_char:
        # Icono centrado
        icon_bbox = FONT_ICON.getbbox(icon_char)
        icon_w = icon_bbox[2] - icon_bbox[0]
        icon_x = (60 - icon_w) // 2
        draw.text((icon_x, 110), icon_char, font=FONT_ICON, fill=(180, 180, 180))
        # Texto debajo del icono
        text_bbox = FONT_TEXT_SIDE.getbbox(text)
        text_w = text_bbox[2] - text_bbox[0]
        text_x = (60 - text_w) // 2
        draw.text((text_x, 152), text, font=FONT_TEXT_SIDE, fill=(180, 180, 180))
    else:
        text_bbox = FONT_TEXT_SIDE.getbbox(text)
        text_w = text_bbox[2] - text_bbox[0]
        text_x = (60 - text_w) // 2
        draw.text((text_x, 125), text, font=FONT_TEXT_SIDE, fill=(180, 180, 180))

    return img


class RazerController:

    def __init__(self):
        self.deck = None
        self.device_path = None
        self.running = False

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

            # Pantallas laterales con icono + texto
            self.deck.set_key_image("left", make_side_image("VOL", ICON["volume"]))
            time.sleep(0.1)
            self.deck.set_key_image("right", make_side_image("MIC", ICON["mic"]))
            time.sleep(0.1)

            # 12 botones de la pantalla central (grid 4x3, indices 0-11)
            labels = [
                ("Firefox",  ICON["firefox"],  (255, 128, 0)),
                ("Terminal", ICON["terminal"], (0, 255, 0)),
                ("Discord",  ICON["discord"],  (114, 137, 218)),
                ("Archivos", ICON["archivos"], (255, 204, 0)),
                ("VSCode",   ICON["vscode"],   (0, 120, 215)),
                ("Spotify",  ICON["spotify"],  (30, 215, 96)),
                ("OBS",      ICON["obs"],      (200, 200, 200)),
                ("Chrome",   ICON["chrome"],   (66, 133, 244)),
                ("",         None,             (40, 40, 40)),
                ("",         None,             (40, 40, 40)),
                ("",         None,             (40, 40, 40)),
                ("",         None,             (40, 40, 40)),
            ]
            for idx, (label, icon, color) in enumerate(labels):
                if label:
                    img = make_key_image(label, icon_char=icon, color=color, border_color=color)
                else:
                    img = make_key_image("", bg=(10, 10, 10), border_color=(30, 30, 30))
                self.deck.set_key_image(str(idx), img)
                time.sleep(0.05)

            # Botones fisicos redondos (1-7)
            btn_colors = [
                ("1", (255, 128, 0)),
                ("2", (0, 255, 0)),
                ("3", (114, 137, 218)),
                ("4", (255, 204, 0)),
                ("5", (0, 120, 215)),
                ("6", (30, 215, 96)),
                ("7", (255, 255, 255)),
            ]
            for name, color in btn_colors:
                self.deck.set_button_color(name, color)
                time.sleep(0.05)

            log.info("Controlador activo!")
            return True

        except Exception as e:
            log.error(f"Error conectando: {e}")
            self.deck = None
            return False

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
            arg = "2%+" if direction == "right" else "2%-"
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", arg], check=False)
        except Exception as e:
            log.error(f"Error volumen: {e}")

    def toggle_mute(self):
        try:
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], check=False)
        except Exception as e:
            log.error(f"Error mute: {e}")

    def change_mic(self, direction):
        try:
            arg = "2%+" if direction == "right" else "2%-"
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", arg], check=False)
        except Exception as e:
            log.error(f"Error mic: {e}")

    def toggle_mic_mute(self):
        try:
            subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"], check=False)
        except Exception as e:
            log.error(f"Error mic mute: {e}")

    def launch_app(self, cmd):
        try:
            if self.deck:
                self.deck.vibrate("SHORT")
            subprocess.Popen(cmd, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log.error(f"Error lanzando {cmd}: {e}")

    # ========== CALLBACK ==========

    def callback(self, deck, msg):
        try:
            b_id = msg.get("id")
            action = msg.get("action")
            state = msg.get("state")

            # -- RUEDAS --
            # Superior izquierda: Volumen
            if action == "rotate" and b_id == "knobTL":
                self.change_volume(state)
                return
            if action == "push" and state == "down" and b_id == "knobTL":
                self.toggle_mute()
                return
            # Superior derecha: Microfono
            if action == "rotate" and b_id == "knobTR":
                self.change_mic(state)
                return
            if action == "push" and state == "down" and b_id == "knobTR":
                self.toggle_mic_mute()
                return

            # -- BOTONES FISICOS (1-7) --
            BUTTON_APPS = {
                "1": ["firefox"],
                "2": ["cosmic-term"],
                "3": ["flatpak", "run", "com.discordapp.Discord"],
                "4": ["cosmic-files"],
                "5": ["code"],
                "6": ["flatpak", "run", "com.spotify.Client"],
                "7": ["obs"],
            }
            if action == "push" and state == "down" and b_id in BUTTON_APPS:
                self.launch_app(BUTTON_APPS[b_id])
                return

            # -- PANTALLA TACTIL --
            TOUCH_APPS = {
                0: ["firefox"],
                1: ["cosmic-term"],
                2: ["flatpak", "run", "com.discordapp.Discord"],
                3: ["cosmic-files"],
                4: ["code"],
                5: ["flatpak", "run", "com.spotify.Client"],
                6: ["obs"],
                7: ["google-chrome"],
            }
            if action == "touchend":
                key = msg.get("key")
                screen = msg.get("screen")
                if screen == "center" and key in TOUCH_APPS:
                    self.launch_app(TOUCH_APPS[key])

        except Exception as e:
            log.error(f"Error en callback: {e}")


if __name__ == "__main__":
    controller = RazerController()
    controller.run()

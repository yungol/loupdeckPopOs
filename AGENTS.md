# Razer Stream Controller - Proyecto loupedeckjuan

## Que es esto?

**Nota importante sobre el entorno:** Esta es la carpeta de desarrollo. La aplicación se instala y se ejecuta de manera local en `/home/juan/projects/loupedeckjuan`.

Aplicacion custom en Python para controlar el **Razer Stream Controller** (Loupedeck Live rebrandeado, USB ID `1532:0d06`) en **Linux con Pop!_OS / COSMIC**.

Controla volumen del sistema, microfono, lanza aplicaciones, y muestra iconos en las pantallas del dispositivo. Corre como servicio en segundo plano y se auto-inicia al hacer login.


## Estructura del proyecto

```
loupedeckjuan/
  app.py                - Aplicacion principal (TODO el controlador)
  lib/                  - Libreria python-loupedeck-live (comunicacion serial con el dispositivo)
    src/Loupedeck/      - Codigo fuente de la libreria
    pyproject.toml      - Para instalacion via pip
  venv/                 - Entorno virtual Python (se crea con install.sh)
  assets/               - Fuentes e iconos
    MaterialIcons-Regular.ttf  - Fuente Material Icons de Google
  install.sh            - Instalador automatico
  deploy_and_restart.sh - Script de despliegue dev->prod y reinicio limpio
  package.sh            - Empaquetador (.tar.gz para backup/portabilidad)
  requirements.txt      - Dependencias pip (Pillow, pyserial, evdev)
  instrucciones.md      - Este archivo
```


## Instalacion rapida (equipo nuevo o despues de formatear)

```bash
tar xzf loupedeckjuan-FECHA.tar.gz
cd loupedeckjuan-FECHA
./install.sh
```

El instalador hace todo automaticamente:
1. Detecta Python 3.10+ e instala venv/pip si faltan
2. Copia los archivos a `~/projects/loupedeckjuan/`
3. Crea el entorno virtual e instala dependencias (incluye `evdev` para teclado virtual)
4. Instala reglas udev para permisos del dispositivo y `/dev/uinput` (pide sudo)
5. Agrega tu usuario a los grupos `dialout` e `input` (pide sudo)
6. Configura ACL en `/dev/uinput` para acceso inmediato
7. Crea y activa el servicio systemd (con variables de entorno Wayland)

**Despues de instalar**, cierra sesion y vuelve a entrar para que los grupos `dialout`/`input` surtan efecto.


## Comandos utiles

```bash
# Ver estado del servicio
systemctl --user status loupedeck

# Ver logs en tiempo real
journalctl --user -u loupedeck -f

# Reiniciar (despues de editar app.py)
systemctl --user restart loupedeck

# Detener
systemctl --user stop loupedeck

# Desinstalar
~/projects/loupedeckjuan/install.sh --uninstall

# Crear paquete de backup
~/projects/loupedeckjuan/package.sh
```


## Como funciona el dispositivo

### Conexion
- El Razer Stream Controller NO es un dispositivo HID normal
- Aparece como **puerto serial** (`/dev/ttyACM*`) via el modulo kernel `cdc_acm`
- Se comunica con protocolo **WebSocket-over-Serial** a 460800 baud
- La app detecta automaticamente el puerto (no importa si es ttyACM0, ttyACM1, etc.)

### Hardware
- **3 pantallas**: izquierda (60x270), centro (360x270, grid 4x3 de 90x90), derecha (60x270)
- **6 knobs rotatorios**: knobTL, knobCL, knobBL (izquierda), knobTR, knobCR, knobBR (derecha)
- **7 botones fisicos redondos**: "1" a "7" (debajo de la pantalla)
- **1 boton circular grande**: "circle"
- **12 botones touch**: indices 0-11 en la pantalla central

### Callbacks
La funcion `callback(deck, msg)` recibe un diccionario `msg` con:
- `id`: identificador del boton (ej: "knobTL", "1", "circle")
- `action`: tipo de evento ("push", "rotate", "touchend", "touchmove", "touchstart")
- `state`: estado ("down", "up" para push; "left", "right" para rotate)
- `key`: indice del boton touch (0-11)
- `screen`: pantalla tocada ("center", "left", "right")
- `x`, `y`: coordenadas del toque

### Renderizado de pantallas
- **USAR** `deck.set_key_image(str(index), imagen_pil)` para botones individuales
- **NO USAR** `deck.draw_image()` con coordenadas manuales (rompe la conexion serial)
- Las pantallas laterales: `deck.set_key_image("left", img)` / `deck.set_key_image("right", img)`
- Botones fisicos LED: `deck.set_button_color("1", (r, g, b))`


## Fuentes e Iconos

### Fuentes usadas
- **Ubuntu Mono** - Para todo el texto en las pantallas del dispositivo
  - Ubicacion del sistema: `/usr/share/fonts/truetype/ubuntu/UbuntuMono[wght].ttf`
  - Tamano texto botones: 13px
  - Tamano texto lateral: 14px
  - Viene preinstalada en Pop!_OS/Ubuntu. Si no esta, instalar: `sudo apt install fonts-ubuntu`

- **Material Icons Regular** - Para los iconos en cada boton
  - Ubicacion: `assets/MaterialIcons-Regular.ttf` (incluida en el proyecto)
  - Tamano iconos: 36px
  - Fuente de Google: https://github.com/google/material-design-icons
  - Cada icono es un caracter Unicode (codepoint)

### Iconos Material asignados actualmente
| Clave | Codepoint | Icono | Nombre Material |
|-------|-----------|-------|-----------------|
| firefox | `\ue894` | globo | language |
| terminal | `\ueb8e` | terminal | terminal |
| discord | `\ue0b7` | burbuja | chat |
| archivos | `\ue2c7` | carpeta | folder |
| vscode | `\ue86f` | llaves | code |
| spotify | `\ue03d` | notas | queue_music |
| obs | `\ue04b` | camara | videocam |
| chrome | `\ue051` | globo web | web |
| volume | `\ue050` | parlante | volume_up |
| mic | `\ue029` | microfono | mic |
| zoom | `\ue8ff` | lupa | zoom_in |

### Como cambiar un icono
1. Buscar el icono en https://fonts.google.com/icons
2. Buscar el codepoint en `assets/MaterialIcons-Regular.codepoints` o en:
   https://github.com/google/material-design-icons/blob/master/font/MaterialIcons-Regular.codepoints
3. En `app.py`, actualizar el diccionario `ICON`:
   ```python
   ICON = {
       "firefox":   "\ue894",  # language
       "terminal":  "\ueb8e",  # terminal
       ...
   }
   ```
4. Reiniciar: `systemctl --user restart loupedeck`

### Como cambiar la fuente de texto
En `app.py`, modificar las lineas de carga de fuentes:
```python
FONT_TEXT = ImageFont.truetype("/ruta/a/tu/fuente.ttf", 13)
FONT_TEXT_SIDE = ImageFont.truetype("/ruta/a/tu/fuente.ttf", 14)
```


## Sistema de capas

Los **8 botones fisicos de abajo** (circle + 1-7) actuan como **selectores de capa**.
Cada capa controla los **12 touch keys** + **6 knobs** + **pantallas laterales**.

- Presionar un boton de abajo cambia la capa activa
- El LED del boton activo se enciende brillante, los demas se atenuan
- El dispositivo vibra al cambiar de capa
- Capacidad total: **8 capas × (12 keys + 6 knobs) = 144 configuraciones**

### Colores de capa (LEDs)
| Boton | Color | Capa |
|-------|-------|------|
| circle | Blanco | Principal (apps) |
| 1 | Naranja | Capa 1 |
| 2 | Verde | Capa 2 |
| 3 | Azul Discord | Capa 3 |
| 4 | Amarillo | Capa 4 |
| 5 | Azul | Capa 5 |
| 6 | Verde Spotify | Capa 6 |
| 7 | Rosa | Capa 7 |

### Capa Principal (circle) - Asignaciones actuales

#### Knobs
| Knob | Rotar | Presionar |
|------|-------|-----------|
| Top-Left (knobTL) | Volumen sistema +/- | Mute toggle |
| Top-Right (knobTR) | Volumen mic +/- | Mic mute toggle |
| Center-Left (knobCL) | -- sin asignar -- | -- sin asignar -- |
| Center-Right (knobCR) | Zoom +/- (Ctrl+=/Ctrl+-) | Reset zoom (Ctrl+0) |
| Bottom-Left (knobBL) | -- sin asignar -- | -- sin asignar -- |
| Bottom-Right (knobBR) | -- sin asignar -- | -- sin asignar -- |

#### Touch keys (0-11)
| # | App | Comando |
|---|-----|---------|
| Touch 0 | Terminal | `cosmic-term` |
| Touch 1 | Archivos | `cosmic-files` |
| Touch 2-11 | -- sin asignar -- | |

### Capas 1-7

Todas las capas 1-7 estan vacias (sin asignar). Para agregar configuracion a una capa, editar el diccionario `LAYERS` en `app.py`.


## Como personalizar

### Agregar configuracion a una capa
En `app.py`, busca el diccionario `LAYERS` y edita la capa deseada. Cada capa tiene:

```python
LAYERS = {
    "circle": {  # o "1", "2", ..., "7"
        "name": "Nombre de la capa",
        "touch_keys": [
            # 12 tuplas: (label, icon_key, color_rgb, comando)
            ("Firefox", "firefox", (255, 128, 0), ["firefox"]),
            (None, None, None, None),  # boton vacio
            ...
        ],
        "knobs": {
            "knobTL": {"rotate": "change_volume", "press": "toggle_mute"},
            "knobTR": None,  # sin asignar
            ...
        },
        # Pantallas laterales: lista de hasta 3 items para top/center/bottom
        # (corresponden a las posiciones de los knobs: top, center, bottom)
        "side_left":  [("VOL", "volume"), None, None],
        "side_right": [("MIC", "mic"), ("ZOOM", "zoom"), None],
        # Formato legacy (un solo item): tupla ("TEXT", "icon_key")
    },
}
```

### Agregar un nuevo metodo para knobs
1. Agregar el metodo en la clase `RazerController`
2. Referenciarlo por nombre en la configuracion del knob:
   ```python
   "knobCL": {"rotate": "mi_metodo", "press": "mi_otro_metodo"},
   ```
3. El metodo de `rotate` recibe `direction` ("left"/"right")
4. El metodo de `press` no recibe argumentos


## Info del sistema original

- **Distro**: Pop!_OS con COSMIC desktop
- **Audio**: PipeWire (comandos `wpctl`)
- **Python**: 3.12
- **Usuario**: juan
- **Dispositivos de audio**: Sony WH-1000XM4 (Bluetooth, sink), Elgato Wave:3 (source)
- **Libreria**: python-loupedeck-live de devleaks (GitHub)
- **NO usar** el paquete `loupedeck` de PyPI (requiere Python 3.14+)


## Cosas por hacer

- [x] ~~Agregar iconos en la pantalla~~ (hecho: se usan Material Icons como fuente)
- [x] ~~Sistema de capas~~ (hecho: 8 capas via botones fisicos)
- [x] ~~Zoom via knob~~ (hecho: knobCR con evdev/uinput, reset con Ctrl+0)
- [ ] Configurar capas 1-7 con funciones utiles
- [ ] Asignar funciones a los 3 knobs restantes (knobCL, knobBL, knobBR)
- [ ] GUI de configuracion (opcional)
- [ ] Si cambias a PulseAudio, reemplazar `wpctl` por `pactl`


## Dependencias del sistema

```bash
# Necesarios
sudo apt install python3 python3-venv python3-pip

# El dispositivo necesita estas reglas udev (install.sh las crea):
# /etc/udev/rules.d/99-loupedeck.rules

# Tu usuario debe estar en los grupos dialout e input:
sudo usermod -aG dialout $USER
sudo usermod -aG input $USER
# El grupo input es necesario para /dev/uinput (teclado virtual evdev)
```


## Problemas comunes

**El dispositivo no se detecta:**
- Verificar que esta conectado: `ls /dev/ttyACM*`
- Verificar reglas udev: `cat /etc/udev/rules.d/99-loupedeck.rules`
- Recargar reglas: `sudo udevadm control --reload-rules && sudo udevadm trigger`

**Permission denied en el puerto serial:**
- Verificar grupo: `groups` (debe incluir `dialout`)
- Si acabas de agregar el grupo, cierra sesion y vuelve a entrar

**La pantalla se apaga/conexion se pierde:**
- El servicio se reconecta automaticamente cada 5 segundos
- Si persiste, desconecta el USB, espera 3 seg, y vuelvelo a conectar

**Error "read already running":**
- Es inofensivo, la libreria lo muestra cuando `auto_start=True` y se llama `start()` de nuevo

## Flujo de Desarrollo y Despliegue
Cualquier cambio realizado en los archivos de la carpeta de desarrollo (ej. `app.py`) DEBE ser copiado a la carpeta local de ejecución y el servicio debe reiniciarse de manera **limpia**. 

**SIEMPRE** utiliza el script `./deploy_and_restart.sh` despues de realizar cualquier modificacion al codigo. Este script se encarga de:
1. Copiar `app.py` desde `/home/juan/codigo/projects/loupdeckPopOs/` a `/home/juan/projects/loupedeckjuan/`.
2. Detener el servicio `loupedeck`.
3. Esperar 5 segundos para asegurar que el puerto serial se libere y la pantalla se refresque correctamente, evitando que el dispositivo quede en negro o "congelado".
4. Volver a iniciar el servicio.

Nunca uses `systemctl --user restart` directamente sin el delay, ya que provoca que el dispositivo no se reinicialice de forma apropiada.

### Teclado virtual (evdev/uinput)
La simulacion de teclas (zoom, etc.) usa `evdev` con `/dev/uinput` para crear un teclado virtual a nivel de kernel. Esto funciona en cualquier compositor Wayland (incluyendo COSMIC), a diferencia de `wtype` o `xdotool` que no funcionan en COSMIC.

Requisitos:
- Paquete Python `evdev` (en `requirements.txt`)
- El usuario debe estar en el grupo `input`
- Regla udev para `/dev/uinput` (en `install.sh`)
- ACL configurada: `setfacl -m u:$USER:rw /dev/uinput`

**Nota sobre VSCode:** El reset de zoom (`Ctrl+0`) requiere un keybinding personalizado en VSCode:
```json
[{ "key": "ctrl+0", "command": "workbench.action.zoomReset" }]
```
Archivo: `~/.config/Code/User/keybindings.json`

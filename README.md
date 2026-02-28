<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux">
  <img src="https://img.shields.io/badge/desktop-Pop!__OS%20COSMIC-48B9C7?style=for-the-badge&logo=popos&logoColor=white" alt="Pop!_OS COSMIC">
  <img src="https://img.shields.io/badge/audio-PipeWire-5A9FD4?style=for-the-badge" alt="PipeWire">
</p>

# Razer Stream Controller for Linux

A custom Python controller application for the **Razer Stream Controller** (Loupedeck Live, USB `1532:0d06`) on Linux. Turns your hardware deck into a fully functional application launcher, volume controller, and system dashboard — with rendered icons, labels, and real-time feedback on the built-in LCD screens.

Designed and tested on **Pop!_OS** with the **COSMIC** desktop environment and **PipeWire/WirePlumber** audio stack.

---

## Features

- **Application Launcher** — Launch apps with a single tap on the touchscreen (Firefox, VS Code, Spotify, OBS, Discord, and more)
- **Volume & Microphone Control** — Rotate hardware knobs to adjust system volume and mic level; press to toggle mute
- **Dynamic LCD Rendering** — Draws icons (Material Icons) and text labels on the device's center touchscreen and side displays
- **LED Button Feedback** — Physical buttons light up with colored LEDs and provide haptic feedback on press
- **Auto-Reconnection** — Monitors USB connection and automatically reconnects if the device is unplugged/replugged
- **Systemd Integration** — Runs as a user service that starts at login and stays running in the background
- **One-Command Install** — A single script handles the Python venv, dependencies, udev rules, permissions, and systemd service

## Hardware Layout

```
 ┌──────────────────────────────────────────┐
 │  [Knob L]              [Knob R]          │
 │  Volume ±              Mic ±             │
 │  Press=Mute            Press=Mute        │
 │                                          │
 │  ┌────┐ ┌──────────────────┐ ┌────┐     │
 │  │Left│ │  Center 4x3 Grid │ │Right│    │
 │  │Vol │ │                  │ │ Mic │     │
 │  │Icon│ │  12 Touch Keys   │ │Icon │     │
 │  └────┘ └──────────────────┘ └────┘     │
 │                                          │
 │  [●] [●] [●] [●] [●] [●] [●]           │
 │        7 Physical LED Buttons            │
 └──────────────────────────────────────────┘
```

**Touch Keys (Center Screen):**

| Key | App | Key | App |
|-----|-----|-----|-----|
| 1 | Firefox | 5 | VS Code |
| 2 | Terminal | 6 | Spotify |
| 3 | Discord | 7 | OBS |
| 4 | Files | 8 | Chrome |

## Prerequisites

- **Linux** (tested on Pop!_OS 22.04+ with COSMIC desktop)
- **Python 3.10+**
- **PipeWire + WirePlumber** (`wpctl` must be available for volume control)
- **Razer Stream Controller** connected via USB

## Installation

```bash
git clone https://github.com/yungol/loupdeckPopOs.git
cd loupdeckPopOs
./install.sh
```

The installer will:

1. Detect Python 3.10+ and install `python3-venv` / `python3-pip` if needed
2. Create a virtual environment and install dependencies
3. Download the [python-loupedeck-live](https://github.com/devleaks/python-loupedeck-live) library if not present
4. Install udev rules for the Razer Stream Controller (requires `sudo`)
5. Add your user to the `dialout` group (requires `sudo`)
6. Create and enable a `systemd --user` service

> **Note:** You may need to log out and back in for the `dialout` group membership to take effect.

## Usage

### As a systemd service (recommended)

The service starts automatically at login. Useful commands:

```bash
systemctl --user status loupedeck        # Check service status
systemctl --user restart loupedeck       # Restart after code changes
systemctl --user stop loupedeck          # Stop the service
journalctl --user -u loupedeck -f        # View live logs
```

### Manual execution (development)

```bash
source venv/bin/activate
python app.py
```

## Project Structure

```
loupedeckjuan/
├── app.py                # Main application — all controller logic
├── assets/
│   └── MaterialIcons-Regular.ttf   # Icon font for button rendering
├── lib/                  # Bundled python-loupedeck-live library
│   └── src/
│       └── Loupedeck/    # Device driver (serial + WebSocket protocol)
├── install.sh            # Automated installer
├── package.sh            # Creates portable .tar.gz backup
├── requirements.txt      # Python dependencies
└── instrucciones.md      # Detailed documentation (Spanish)
```

## Customization

Edit `app.py` to modify button assignments, icons, or behavior:

- **Add/change apps** — Update the `APPS` configuration with the desired command and Material Icon codepoint
- **Adjust icons** — Browse [Material Icons](https://fonts.google.com/icons) for codepoints, update the `ICON` dictionary
- **Modify knob behavior** — Adjust volume step size or remap knob actions in the callback functions

After making changes, restart the service:

```bash
systemctl --user restart loupedeck
```

## Packaging & Backup

Create a portable archive for backup or transfer to another machine:

```bash
./package.sh
# Output: loupedeckjuan-YYYYMMDD.tar.gz
```

To restore on a new machine:

```bash
tar xzf loupedeckjuan-*.tar.gz
cd loupedeckjuan-*/
./install.sh
```

## Uninstall

```bash
./install.sh --uninstall
```

This removes the systemd service, udev rules, and virtual environment.

## How It Works

The Razer Stream Controller communicates over a serial port (`/dev/ttyACM*`) at 460800 baud using a WebSocket-over-Serial protocol. The application:

1. Scans USB devices in `/dev/ttyACM*` matching the Razer vendor/product ID
2. Establishes a WebSocket handshake over the serial connection
3. Registers callbacks for button presses, knob rotations, and touch events
4. Renders icons and labels as RGB565 framebuffers and pushes them to the LCD screens
5. Monitors connection health and reconnects automatically on failure

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [Pillow](https://python-pillow.org/) | 12.1.1 | Image generation for LCD screens |
| [pyserial](https://github.com/pyserial/pyserial) | 3.5 | Serial communication with the device |
| [python-loupedeck-live](https://github.com/devleaks/python-loupedeck-live) | 1.5.0 | Device protocol driver (bundled) |

## Acknowledgments

- [python-loupedeck-live](https://github.com/devleaks/python-loupedeck-live) by Pierre Mareschal — Python port of the Loupedeck protocol
- [loupedeck](https://github.com/foxxyz/loupedeck) by Aiden Foxx — Original Node.js implementation
- [Material Icons](https://fonts.google.com/icons) by Google — Icon font used for button rendering

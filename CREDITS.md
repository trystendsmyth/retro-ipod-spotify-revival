# Credits and sources

sPot Revival only exists because these people published their work.

## Projects this repository is built from

| Who | What | Link |
|---|---|---|
| **Guy Dupont** (with Ricardo Sappia) | sPot: the original hardware design, click wheel decoder (`click.c`), tkinter iPod UI, wiring diagram | [Hackaday.io project](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004), [GitHub](https://github.com/dupontgu/retro-ipod-spotify-client) |
| sPot contributors (André Silva, Utku Tarhan, 3urobeat, Tom, Mitch Lui, Tobias Herrmann, and others in the git history) | install docs, fixes, macOS dev support | git history of this repo |
| **Ricardo Sappia** | Alternate build: Waveshare ST7789 LCD, 3D-printed chassis, power switch, low-battery signal; source of the `st7789` pin map | [rsflightronics.com/spotifypod](http://rsflightronics.com/spotifypod) |
| **oliver-vv** | Spotify-iPod-Classic (2026): go-librespot playback, PKCE login, SQLite cache, setup portal, Bluetooth pairing, systemd installer, 2026 Web API changes. The software base of this repo. | [GitHub](https://github.com/oliver-vv/Spotify-iPod-Classic) |
| **thehajime** | `pizero-2026` branch: go-librespot on the ARMv6 Pi Zero W; `pause()` instead of the busy loop in `click.c`; non-owned-playlist handling | [GitHub](https://github.com/thehajime/retro-ipod-spotify-client/tree/pizero-2026) |
| **Brandon Lysholm** | retroDAP: Zero 2 W port with encoder/SPI screen; reference for Spotify app setup and OAuth steps | [GitHub](https://github.com/BrandonLysholm/retroDAP) |
| **Michael / jonathancaudill**, "Doris" and other commenters | Detailed community install notes ([sPot issue #69](https://github.com/dupontgu/retro-ipod-spotify-client/issues/69)) and Hackaday discussion, including thin-battery / trimmed-Pi fitting tips (tanagram27) | [Hackaday discussion](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004) |
| **Jason Garr** | Reverse-engineered the 4th-gen click wheel pinout and packet format (2010) | [iPod Clickwheel Hack](https://jasongarr.wordpress.com/project-pages/ipod-clickwheel-hack/), [Hackaday article](https://hackaday.com/2010/02/05/repurposing-a-click-wheel/) |
| **devgianlu and contributors** | go-librespot, the Spotify Connect player (including ARMv6 builds) | [GitHub](https://github.com/devgianlu/go-librespot) |
| **joan2937** | pigpio | [GitHub](https://github.com/joan2937/pigpio) |
| **Spotipy** maintainers | Spotify Web API client | [GitHub](https://github.com/spotipy-dev/spotipy) |
| **Liz Clark / Adafruit Industries** | CircuitPython TLV320DAC3100 driver (MIT): the register sequence in `install/bin/tlv320.py` follows it | [GitHub](https://github.com/adafruit/Adafruit_CircuitPython_TLV320) |

## Other builds and diagrams (linked, not copied)

Listed in [docs/guide/REFERENCE-BUILDS.md](docs/guide/REFERENCE-BUILDS.md). No photos or
diagrams from these are included in this repository.

| Who | What | Link |
|---|---|---|
| **Sean (Shogan.tech)** | SpotiPod build log (Pi Zero W, Adafruit #911 composite display) and a post on wiring the #911 to a Pi Zero | [Build log](https://www.shogan.co.uk/builds/spotipod-spotify-streaming-device-from-an-ipod-classic/), [2" TFT post](https://www.shogan.co.uk/builds/tiny-2-tft-composite-video-on-raspberry-pi-zero/) |
| **Benjamin Stallings** | Beginner-oriented sPot wiring diagram (Nov 2022) | [Imgur](https://imgur.com/a/epvkWsR) |
| **Kakoub** | Community wiring diagram, re-hosted with credit on Shogan.tech's build log | [Hackaday.io profile](https://hackaday.io/Kakoub) |
| **Ricardo Sappia** (rsappia) | "Spotifypod base plate and holder": 3D-printed base plate, key-press extension and stand. Creative Commons - Attribution - Non-Commercial; not included in this repository | [Thingiverse](https://www.thingiverse.com/thing:4789155) |
| **Guy Dupont** | "Round 2: USB-C, wired audio, and RetroPie" log and video, and project comments on reusing the original headphone jack | [Hackaday.io log](https://hackaday.io/project/177034/log/190079-round-2-usb-c-wired-audio-and-retropie) |
| **Pierre-Loup M.**, **tanagram27**, **Phil Karza** | Hackaday comments on I2S DACs in the case, and that a line-level PCM5102 needs a headphone amplifier | [Hackaday discussion](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004) |

## Third-party software the installer sets up

These are installed from their own packages (apt or pip) and aren't copied into this
repository.

| Software | Licence | Used for | Link |
|---|---|---|---|
| MPD (Music Player Daemon), The Music Player Daemon Project | GPL-2.0-or-later (`GPLv2+` in its build file) | Music on iPod playback (`spotifypod-mpd.service`) | [musicpd.org](https://www.musicpd.org/), [GitHub](https://github.com/MusicPlayerDaemon/MPD) |
| python-mpd2, Jörg Thalheim and contributors | LGPL-3.0 | MPD client in `frontend/local_player.py` | [GitHub](https://github.com/Mic92/python-mpd2) |
| comitup, David Steele | GPL-2.0 | Wi-Fi setup hotspot; installed from comitup's apt repository | [Homepage](https://davesteele.github.io/comitup/), [GitHub](https://github.com/davesteele/comitup) |

## Reference material

| Source | Used for |
|---|---|
| Original sPot wiring diagram, Guy Dupont (`.docs/sPot_schematic.png`, Apache-2.0) | click wheel pins 1/2/6/8, GPIO 23/25/26, 2N3904 + 220 ohm haptic driver |
| Hackaday.io sPot components list and details | parts list; power design (charger + PowerBoost, hold switch on EN) |
| Guy Dupont's Hackaday comment (Nov 2022) | flyback diode across the haptic motor |
| [Raspberry Pi documentation: Zero models, test pad locations](https://www.raspberrypi.com/documentation/computers/zero.html) (CC BY-SA 4.0) | Zero 2 W TV / GND pad positions; pad diagram image |
| [Raspberry Pi Official Magazine: Add RCA output to a Pi Zero](https://magazine.raspberrypi.com/articles/rca-pi-zero), [Adafruit: Pi Zero video outputs](https://learn.adafruit.com/introducing-the-raspberry-pi-zero/video-outputs) | Zero / Zero W TV holes: square pad = video, round pad = ground |
| [Raspberry Pi documentation: config.txt, composite video](https://www.raspberrypi.com/documentation/computers/config_txt.html) | `dtoverlay=vc4-kms-v3d,composite`, `enable_tvout`, `vc4.tv_norm` |
| [Adafruit #911](https://www.adafruit.com/product/911) | display wiring (red V+, black GND, GND, video), 6-12 V rating, 120 mA at 5 V |
| [Adafruit PowerBoost 1000 Basic pinouts](https://learn.adafruit.com/adafruit-powerboost-1000-basic/pinouts) | BAT / 5V / GND / EN / LBO behaviour |
| [Adafruit #1905 Mini LiPo charger](https://www.adafruit.com/product/1905) | 100 mA default, 500 mA jumper |
| [Spotify Web API: February 2026 migration guide](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide) | Development Mode limits and removed endpoints |
| go-librespot `CROSS_COMPILE.md` | `armv6_rpi` build is for Pi 1 / Zero |
| [MPD user manual](https://mpd.readthedocs.io/en/stable/user.html) and Debian's `mpd.service` | `mpd.conf` settings, `--systemd` unit |
| [Adafruit #6309](https://www.adafruit.com/product/6309), its [learn guide](https://learn.adafruit.com/adafruit-tlv320dac3100-i2s-dac/pinouts) and [board files](https://github.com/adafruit/Adafruit-TLV320DAC3100-I2S-DAC-PCB) | DAC pads, 3.3-5 V VIN, AC-coupled HPL/HPR, 10 kΩ RST pull-up |
| TI TLV320DAC3100 datasheet (SLAS671) | PLL and divider limits, headphone volume table 6-24 |
| [Raspberry Pi device tree overlays README](https://github.com/raspberrypi/linux/blob/rpi-6.12.y/arch/arm/boot/dts/overlays/README) and `sound/soc/bcm/rpi-simple-soundcard.c` | `i2s-dac` overlay; its fixed 64 x fs bit clock and `snd_rpi_rpi_dac` card name |
| [pigpio C interface](https://abyz.me.uk/rpi/pigpio/cif.html) (`gpioCfgClock`) | pigpio times itself from the PCM block by default, which I2S needs |
| [WirePlumber ALSA configuration](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/alsa.html) | `session.suspend-timeout-seconds = 0` |
| [iFixit guide 388](https://www.ifixit.com/Guide/iPod+4th+Generation+or+Photo+Headphone+Jack+Replacement/388) | the 4th-gen jack board: jack, hold switch and piezo on one board, two T6 screws |
| Rockbox `firmware/export/config/ipod4g.h` | the iPod 4G reads a headphone-detect line |
| Adafruit product pages for #6250 and #3678, TI PCM5102A and NXP UDA1334ATS datasheets | why a line-level DAC isn't used for earbuds |

# Retro iPod Spotify Revival

**Spotify in a 4th-generation iPod, rebuilt for 2026.** A Raspberry Pi Zero W (or, as an
alternative, a Zero 2 W) inside an iPod "Click Wheel" (model A1059) case, driven by the
original click wheel, with haptic feedback, Spotify Connect playback and your Spotify
library on a tiny screen. It also plays your own DRM-free music files from the SD card,
under **Music on iPod** ([guide chapter 9b](docs/guide/09b-own-music.md)).

<p align="center">
  <img src="docs/images/ui/320x240-01-main-menu.png" width="240" alt="Main menu">
  <img src="docs/images/ui/320x240-03-playlists.png" width="240" alt="Playlists">
  <img src="docs/images/ui/320x240-04-now-playing.png" width="240" alt="Now Playing">
</p>
<p align="center"><sub>Screenshots of the real UI code rendered with demo data by
<code>tools/ui_preview.py</code> (not photos of hardware).</sub></p>

This repository continues [Guy Dupont's sPot](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004)
(2021), using the same hardware. The 2021 software no longer works as written: Raspotify
dropped the Pi Zero W's ARMv6 CPU, Spotify removed password logins, and in 2026 Spotify
restricted the Web API for personal ("Development Mode") apps. The software here is based
on [oliver-vv/Spotify-iPod-Classic](https://github.com/oliver-vv/Spotify-iPod-Classic),
which solved those problems, and adds the original sPot display, Pi Zero W support
(go-librespot's ARMv6 build, as in thehajime's fork) and a complete build guide.

## Start here

**[Build guide](docs/guide/README.md)** - parts, Spotify setup, software, click wheel,
display, haptics, power, assembly, first boot, troubleshooting. Written so someone who has
never built one can follow it step by step.

**[Wiring diagrams](docs/wiring/README.md)** - header map, schematics, harness drawings, pin table,
with the source for every connection.

## What runs on the Pi

```
click wheel --(GPIO, pigpio)--> clickwheel/click.c --UDP 127.0.0.1:9090--> frontend/spotifypod.py (tkinter UI)
                                                                              |-- go-librespot :3678 (Spotify Connect, audio)
                                                                              |-- MPD :6600 (music files in /srv/music)
                                                                              |-- Spotify Web API (library/search, PKCE login)
                                                                              `-- SQLite cache
phone --> http://ipod.local (portal/: Spotify linking, Bluetooth pairing, power)
```

## Hardware

| Part | |
|---|---|
| **Raspberry Pi Zero W** | Primary target (the original sPot board). Raspberry Pi OS Lite **32-bit**; go-librespot `armv6_rpi` build. Single core: slower UI and install, lowest power draw. |
| Raspberry Pi Zero 2 W | Alternative. Raspberry Pi OS Lite **64-bit**. Same footprint and header; much faster; draws more power; composite on underside test pads. |
| Adafruit #911 2" NTSC/PAL TFT (original sPot display) | `DISPLAY_PROFILE=composite` (default). |
| Waveshare 2" ST7789V SPI (Ricardo Sappia's build) | `DISPLAY_PROFILE=st7789` (upstream oliver-vv path, not covered by the guide). |
| iPod 4th gen (A1059) click wheel, 8-pin FPC | Required. Other generations use different connectors. |

## Status - read this

* Verified in software (CI): the click wheel program compiles against pigpio; the
  boot-config script is tested against fixture `config.txt`/`cmdline.txt` files; the
  Web API parsing is tested against Spotify's 2026 response shapes; the MPD client and
  the Spotify/local-music switching are tested, the MPD client also against a real MPD
  with a null audio output; the UI renders at 320x240 and 720x480 (composite) with demo
  data.
* **Not yet verified on hardware by this repository.** The hardware follows the original
  sPot; the software path follows oliver-vv's fork (Zero 2 W) and thehajime's fork
  (go-librespot on a Zero W). If you build one, please open an issue with what worked.

## Credits

This is a derivative work; the people who did the hard parts are listed in
[CREDITS.md](CREDITS.md). Changes made here are summarised in [NOTICE](NOTICE).

## Licence

Apache-2.0 ([LICENSE](LICENSE)), inherited from sPot. The Raspberry Pi pad diagram in
`docs/images/reference/` is CC BY-SA 4.0 (Raspberry Pi Ltd) - see CREDITS.md.

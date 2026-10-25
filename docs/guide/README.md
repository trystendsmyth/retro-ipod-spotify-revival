# Build guide

This guide builds the original sPot hardware around a **Raspberry Pi Zero W**. Where a
**Pi Zero 2 W** needs something different, it is called out in a "Zero 2 W" note.

| | Pi Zero W | Pi Zero 2 W (alternative) |
|---|---|---|
| OS image | Raspberry Pi OS Lite **32-bit** | Raspberry Pi OS Lite **64-bit** |
| CPU | 1 core, ARMv6 | 4 cores, 64-bit |
| Feel | usable; menus and install are slower | noticeably snappier |
| Battery | lower draw | higher draw, shorter runtime |
| Composite video | two **TV** holes on top | **TV / GND test pads** underneath |

Follow the chapters in order. Each one ends with a check so you know it worked. Chapters
4-7 are done on the desk with the Pi **outside** the iPod: every part is wired and tested
before anything goes into the case.

| # | Chapter | You will need |
|---|---|---|
| 1 | [Parts and tools](01-parts.md) | shopping list |
| 2 | [Spotify developer app](02-spotify-app.md) | Spotify Premium |
| 3 | [Flash the SD card](03-flash-os.md) | microSD card, Raspberry Pi Imager |
| 4 | [Install the software](04-install.md) | the Pi, Wi-Fi |
| 5 | [Click wheel](05-click-wheel.md) | click wheel, FPC breakout, 30 AWG wire |
| 6 | [Display and haptics](06-display-haptics.md) | Adafruit #911, 2N3904, 220 ohm, 1N4148, motor |
| 7 | [Power](07-power.md) | battery, charger, PowerBoost |
| 8 | [Assemble](08-assembly.md) | |
| 9 | [Using it](09-using.md) | |
| 9b | [Your own music files](09b-own-music.md) (optional) | music files, a computer with `rsync` or `scp` |
| 10 | [Troubleshooting](10-troubleshooting.md) | |

Wiring diagrams for every step: [../wiring/README.md](../wiring/README.md).

Hardware test results are tracked in [VALIDATION.md](VALIDATION.md). It's a checklist for
the maintainer, not a build step.

> Safety: lithium cells can catch fire if shorted, punctured or charged wrongly. Work with
> the battery disconnected, insulate every joint, and never charge an unattended build.

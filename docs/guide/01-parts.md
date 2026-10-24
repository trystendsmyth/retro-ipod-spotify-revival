# 1. Parts and tools

## Parts (the original sPot hardware)

These are the parts from the [sPot Hackaday components list](https://hackaday.io/project/177034/components),
with the changes this guide makes marked.

| Qty | Part | Notes |
|---|---|---|
| 1 | Apple iPod 4th gen "Click Wheel", **model A1059** | Case, click wheel and hold switch are reused. Other generations have different click wheel connectors. |
| 1 | **Raspberry Pi Zero 2 W** (recommended) or Pi Zero W | Zero 2 W: 64-bit OS, much faster. Zero W: works with the ARMv6 build of go-librespot, slower. |
| 1 | Adafruit 2" NTSC/PAL TFT display, [#911](https://www.adafruit.com/product/911) | Composite video. See the voltage note in chapter 6. |
| 1 | Adafruit Mini LiPo charger, [#1905](https://www.adafruit.com/product/1905) | Charges at 100 mA by default; sPot used 500 mA (solder the jumper). |
| 1 | Adafruit PowerBoost 1000 Basic, [#2030](https://www.adafruit.com/product/2030) | 5.2 V boost. EN pin used as the power switch. |
| 1 | 3.7 V Li-ion/LiPo cell, ~1000 mAh+, JST-PH | sPot used 1000 mAh. Community builds fitted a thin ~2500 mAh pouch cell. Check polarity against the charger. |
| 1 | 10x2 mm coin vibration motor | Haptic "clicks". |
| 1 | 2N3904 NPN transistor | Drives the motor. |
| 1 | 220 ohm resistor | Transistor base resistor. |
| 1 | **1N4148 diode (added)** | Flyback diode across the motor; Guy Dupont recommended adding one after the original build. |
| 1 | 0.5 mm pitch FPC breakout, 8+ pins | For the click wheel ribbon. |
| 1 | microSD card, 16-32 GB+ | A spare card lets you keep a known-good image. |

## For bench testing (chapters 4-6)

| Qty | Part | Notes |
|---|---|---|
| 1 | Raspberry Pi 3 (or 4) + its power supply | Same CPU family as the Zero 2 W; runs the same SD card image. |
| 1 | 3.5 mm 4-pole (TRRS) AV cable to RCA | Carries composite video from the Pi 3's AV jack to the display's RCA plug. Cable wiring varies by brand - see chapter 6. |
| ~10 | female-female / female-male jumper wires | Header to breakout. |
| 1 | breadboard or perfboard scrap | Haptic driver. |

## Accounts

* **Spotify Premium** - required for Spotify Connect playback and for Development Mode
  Web API apps ([Spotify, Feb 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)).
* **GitHub account** - optional, for the Spotify login relay page (chapter 2).

## Tools and consumables

Fine-tip soldering iron, thin solder, flux, 30 AWG wire (kynar/wire-wrap is ideal), heat
shrink, Kapton tape, multimeter, flush cutters, iPod opening tools / guitar picks,
tweezers. Optional: hot glue or a 3D-printed tray (see Ricardo Sappia's build).

# 1. Parts and tools

## Parts (the original sPot hardware)

These are the parts from the [sPot Hackaday components list](https://hackaday.io/project/177034/components),
with the one addition this guide makes marked.

| Qty | Part | Notes |
|---|---|---|
| 1 | Apple iPod 4th gen "Click Wheel", **model A1059** | Case, click wheel and hold switch are reused. Other generations have different click wheel connectors. |
| 1 | **Raspberry Pi Zero W** | Or a Pi Zero 2 W as the alternative (same size and header). Without a pre-soldered header - you solder wires straight to it. |
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
| 1 | micro-USB power supply for the Pi | For chapters 3-6, before the battery is wired. |

## Accounts

* **Spotify Premium** - required for Spotify Connect playback and for Development Mode
  Web API apps ([Spotify, Feb 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide)).
* **GitHub account** - optional, for the Spotify login relay page (chapter 2).

## Tools and consumables

Fine-tip soldering iron, thin solder, flux, 30 AWG wire (kynar / wire-wrap is ideal), heat
shrink, Kapton tape, multimeter, flush cutters, iPod opening tools / guitar picks,
tweezers, a small piece of perfboard for the haptic driver. Optional: hot glue or a
3D-printed tray (see Ricardo Sappia's build).

Leave the wires to the Pi long (10-15 cm) while testing on the desk; you trim them to
length in chapter 8.

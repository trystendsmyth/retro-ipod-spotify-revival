# Wiring

Start with the header map: it shows every header pin you solder to. Then each subsystem
has a schematic (what connects to what) and a harness drawing (the wires to cut and their
colours). Every diagram comes in a light and a dark version; the page shows the one that
matches your theme.

All diagrams are generated from source in
[`docs/wiring/src/`](https://github.com/trystendsmyth/retro-ipod-spotify-revival/tree/main/docs/wiring/src)
so they can be corrected and re-rendered. The tools are pinned so the files come out
byte-identical, and CI fails if the committed files differ from a fresh render:

```bash
sudo apt install graphviz                         # Ubuntu 24.04 / Debian, for WireViz
pip install -r docs/wiring/src/requirements.txt
python3 docs/wiring/src/schematics.py
python3 docs/wiring/src/header_map.py
for f in clickwheel haptic display power; do
  wireviz -f ps docs/wiring/src/harness-$f.yml -o docs/wiring
done
```

## Header map

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="header-map-dark.svg">
  <img alt="Pi 40-pin header in physical pin order, unused pins grey. Used: pin 1 3V3 (click wheel VCC), pin 2 5V in, pin 6 GND, pin 16 GPIO23 (click wheel clock), pin 22 GPIO25 (click wheel data), pin 37 GPIO26 (haptic), pin 39 GND (haptic). Composite video is on the TV holes (Zero W) or underside pads (Zero 2 W), not the header." src="header-map.svg">
</picture>

Composite video doesn't use the header. On the Zero 2 W it's on test pads underneath; see
the Raspberry Pi pad diagram:
[raspberrypi-zero2-pad-diagram.png](../images/reference/raspberrypi-zero2-pad-diagram.png)
(CC BY-SA 4.0, Raspberry Pi Ltd).

## Pin table

| Signal | Pi physical pin | BCM | Other end | Source |
|---|---|---|---|---|
| Click wheel VCC | 1 (3.3 V) | - | FPC pin 1 | sPot diagram; Garr pinout |
| Click wheel CLOCK | 16 | 23 | FPC pin 2 | sPot diagram / `click.c` |
| Click wheel DATA | 22 | 25 | FPC pin 6 | sPot diagram / `click.c` |
| Click wheel GND | 6 | - | FPC pin 8 | sPot diagram |
| Haptic | 37 | 26 | R1 220 ohm -> Q1 2N3904 base | sPot diagram / `click.c` |
| Haptic GND | 39 | - | Q1 emitter | sPot diagram |
| 5 V in | 2 | - | PowerBoost 5V | Hackaday details ("Pi and display run on 5V") |
| GND | 6 | - | PowerBoost GND | |
| Composite video | TV hole (Zero W, square pad) / TV pad (Zero 2 W) | - | display pin 4 | sPot diagram; Raspberry Pi docs and magazine |
| Video ground | round hole beside TV (Zero W) / GND pad (Zero 2 W) | - | display pin 3 | Raspberry Pi docs; Adafruit #911 |

For the `st7789` profile (the SPI-display build from oliver-vv's upstream, after Ricardo
Sappia's) the click wheel DATA moves to GPIO 5 (pin 29) because GPIO 25 becomes the
display RESET; see the upstream table in
[`docs/upstream/oliver-vv-README.md`](https://github.com/trystendsmyth/retro-ipod-spotify-revival/blob/main/docs/upstream/oliver-vv-README.md).

## Click wheel

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="01-click-wheel-dark.svg">
  <img alt="Schematic: click wheel FPC pins 1 VCC, 2 CLOCK, 6 DATA and 8 GND wired to Pi header pins 1 (3V3), 16 (GPIO23), 22 (GPIO25) and 6 (GND)" src="01-click-wheel.svg">
</picture>

![Harness: four 30 AWG wires from the click wheel breakout to the Pi: red VCC to pin 1, violet CLOCK to pin 16, turquoise DATA to pin 22, black GND to pin 6](harness-clickwheel.svg)

## Haptic driver

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="02-haptic-driver-dark.svg">
  <img alt="Schematic: Pi GPIO26 (pin 37) through 220 ohm R1 to the base of 2N3904 Q1, which switches the vibration motor to +5V; 1N4148 flyback diode D1 across the motor" src="02-haptic-driver.svg">
</picture>

![Harness: two 30 AWG wires from the haptic driver board to the Pi: green from R1 to pin 37 (GPIO26), black from Q1's emitter to pin 39 (GND)](harness-haptic.svg)

## Composite display

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="03-composite-display-dark.svg">
  <img alt="Schematic: Pi TV and GND to the Adafruit 911 video and video ground pins; display V+ to +5V and its power ground to GND" src="03-composite-display.svg">
</picture>

![Harness: two 30 AWG wires from the Adafruit 911 to the Pi: black video ground (display pin 3) to the GND hole or pad, yellow video (display pin 4) to the TV hole or pad](harness-display.svg)

## Power

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="04-power-dark.svg">
  <img alt="Schematic: USB charger feeding the Li-ion cell and the PowerBoost 1000 Basic BAT input; hold switch from EN to ground; PowerBoost 5V and GND out to the Pi, display and motor" src="04-power.svg">
</picture>

![Harness: from the PowerBoost's 5V and GND pads, red and black wires to Pi pins 2 and 6 (24 AWG) and to the display's power wires (26 AWG), a red wire to the motor's positive lead, and white EN plus black GND wires to the hold switch](harness-power.svg)

The PowerBoost appears once per destination in the harness drawing so that no wires cross;
every row starts at the same 5V, GND and EN pads.

## The original sPot diagram (Guy Dupont, 2021)

![Original sPot wiring diagram by Guy Dupont](https://raw.githubusercontent.com/trystendsmyth/retro-ipod-spotify-revival/main/.docs/sPot_schematic.png)

The new schematics reproduce these connections; the only electrical addition is D1.

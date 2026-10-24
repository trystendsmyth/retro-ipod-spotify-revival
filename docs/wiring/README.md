# Wiring

All diagrams are generated from source in [`src/`](src/) so they can be corrected and
re-rendered:

```bash
pip install schemdraw==0.23 wireviz==0.4.1   # plus graphviz (apt install graphviz)
python3 docs/wiring/src/schematics.py
wireviz docs/wiring/src/harness.yml -o docs/wiring
```

## Schematics (standard symbols)

| Sheet | |
|---|---|
| Click wheel to Pi | ![](01-click-wheel.svg) |
| Haptic driver | ![](02-haptic-driver.svg) |
| Composite display | ![](03-composite-display.svg) |
| Power | ![](04-power.svg) |

## Harness (WireViz)

![](harness.svg)

Bill of wires: [harness.bom.tsv](harness.bom.tsv).

## The original sPot diagram (Guy Dupont, 2021)

![Original sPot wiring](../../.docs/sPot_schematic.png)

The new schematics reproduce these connections; the only electrical addition is D1.

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
| Composite video | TV pad / TV hole | - | display pin 4 | sPot diagram; Raspberry Pi docs |
| Video ground | GND pad | - | display pin 3 | Raspberry Pi docs; Adafruit #911 |

For the `st7789` profile (Ricardo Sappia's Waveshare build) the click wheel DATA moves to
GPIO 5 (pin 29) because GPIO 25 becomes the display RESET; see the upstream table in
[`docs/upstream/oliver-vv-README.md`](../upstream/oliver-vv-README.md).

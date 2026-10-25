# 7. Power

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../wiring/04-power-dark.svg">
  <img alt="Schematic: USB charger feeding the Li-ion cell and the PowerBoost 1000 Basic BAT input; hold switch from EN to ground; PowerBoost 5V and GND out to the Pi, display and motor" src="../wiring/04-power.svg">
</picture>

The sPot power path: **USB -> charger -> battery -> PowerBoost -> 5.2 V rail -> Pi,
display, motor.** The iPod's hold switch becomes the power switch through the PowerBoost's
EN pin.

| From | To | Why |
|---|---|---|
| Battery JST | Charger (#1905) BAT and PowerBoost (#2030) BAT | Charger fills the cell; boost converter draws from it. Keep the BAT wires short (Adafruit recommends 1.5" or less). |
| PowerBoost **5V** | Pi pin **2** (5 V), display red, motor + | 5.2 V rail. |
| PowerBoost **GND** | Pi pin **6**, display black | Common ground. |
| PowerBoost **EN** | hold switch -> GND | EN is pulled up to BAT; grounding it turns the output fully off ([Adafruit](https://learn.adafruit.com/adafruit-powerboost-1000-basic/pinouts)). |
| Charger USB | your charging port | Mini-B on the #1905; sPot and later builds swapped in micro-USB / USB-C ports. |

Important:

* **Solder the charger's 500 mA jumper** only if your cell is 500 mAh or larger (Adafruit).
* **LBO** (low battery) is pulled up to the battery voltage, which can exceed 3.3 V.
  Do not connect it directly to a GPIO.
* Feeding 5 V into the GPIO header (or the 5 V test pads) **bypasses the Pi's input
  protection**. Double-check polarity before the first power-up, with a multimeter.
* A Zero 2 W draws noticeably more than a Zero W. The PowerBoost 1000 has headroom for
  either, but a small cell will run down quickly on a Zero 2 W.

## Shutting down

Cutting power while the Pi is writing can corrupt the SD card. Use **Settings -> Shut
Down**, wait for the screen to go dark, *then* flip the hold switch.

**Check:** with the hold switch released, the PowerBoost's green LED is on and the Pi
boots from the battery; with it engaged, everything is off. The charger's LED goes red
while charging and green when full.

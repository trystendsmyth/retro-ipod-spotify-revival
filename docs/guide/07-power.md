# 7. Power

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../wiring/04-power-dark.svg">
  <img alt="Schematic: USB-C breakout J3 (VBUS pin 2, GND pin 1) to the USB and GND pads of the PowerBoost 1000C U3; Li-ion cell on U3's BAT JST; hold switch from EN to ground; U3 5V and GND out to the Pi, display and motor" src="../wiring/04-power.svg">
</picture>

Other builds: [Ricardo's SpotifyPod](REFERENCE-BUILDS.md#spotifypod-by-ricardo-sappia)
uses the same PowerBoost 1000C, with a power latch and a low-battery signal, and the
[community notes](REFERENCE-BUILDS.md#community-notes-and-diagrams) cover larger cells and
battery plug polarity.

The power path: **USB-C -> PowerBoost 1000C (charger and boost) -> 5.2 V rail -> Pi,
display, DAC, motor**, with the cell on the PowerBoost. The iPod's hold switch is the power
switch, through the PowerBoost's EN pin. A USB-C socket in the old dock-connector opening
charges the iPod, and it keeps running while it charges.

## You will need

* Adafruit PowerBoost 1000C, [#2465](https://www.adafruit.com/product/2465) (charger and
  5.2 V boost on one board)
* Adafruit sunken USB-C breakout, [#6050](https://www.adafruit.com/product/6050)
* the cell: 3.7 V Li-ion/LiPo, **1000 mAh or more**, with a JST-PH plug
* the printed USB-C bracket ([`hardware/`](../../hardware/README.md)) and two M2 x 4 mm
  self-tapping screws; two-part epoxy for chapter 8
* a USB-C charger rated 5 V, 2 A or more, and a USB-C-to-C cable

## Wiring

| From | To | Why |
|---|---|---|
| Cell (JST) | PowerBoost **BAT** JST connector | Charger and boost both work from the cell. Check the plug's polarity first (below). |
| USB-C breakout pad **2 (VBUS)** | PowerBoost **USB** pad | Charging input. 24 AWG, red. |
| USB-C breakout pad **1 (GND)** | PowerBoost **GND** | 24 AWG, black. |
| PowerBoost **5V** | Pi pin **2** (5 V), display red, motor + | 5.2 V rail. The DAC takes its 5 V from Pi pin 4 (chapter 6b). |
| PowerBoost **GND** | Pi pin **6**, display black | Common ground. |
| PowerBoost **EN** | hold switch -> GND | EN is pulled up; grounding it turns the output fully off ([Adafruit](https://learn.adafruit.com/adafruit-powerboost-1000c-load-share-usb-charge-boost/pinouts)). |

![Harness: red and black 24 AWG from the USB-C breakout's VBUS and GND pads to the PowerBoost's USB and GND pads; from the PowerBoost's 5V and GND pads, red and black wires to Pi pins 2 and 6 (24 AWG) and to the display's power wires (26 AWG), a red wire to the motor's positive lead, and white EN plus black GND wires to the hold switch](../wiring/harness-power.svg)

Don't solder on the PowerBoost's USB-A socket (it isn't fitted). Its micro-USB socket stays
but isn't used: it's wired in parallel with the USB pad.

## Why this works with USB-C-to-C chargers

A USB-C charger only turns on its 5 V when it sees a 5.1 kΩ resistor from each CC pin to
ground (TI, [USB Type-C basics](https://www.ti.com/document-viewer/lit/html/SLYY109B/GUID-4F2F65BB-B5A2-4AEF-A109-F2FFC34EEAB7)).
The #6050 breakout has both ("The two 5.1K resistors on the CC pins indicate to the
upstream port to provide 5V", [Adafruit](https://www.adafruit.com/product/6050)). A plain
USB-C socket wired with only VBUS and GND charges from USB-A-to-C cables but gets no power
from a C-to-C charger.

It's **5 V only**. There's no USB Power Delivery chip, so no charger ever raises the
voltage: without that negotiation every USB-C charger stays at 5 V.

## Important

* **Charge current is 1 A.** The PowerBoost 1000C charges at 1000 mA, so use a cell of
  1000 mAh or more (community builds use ~1800-2500 mAh pouch cells). For a smaller cell,
  Adafruit's schematic gives 500 mA with R16 changed from 1.0 kΩ to 2.0 kΩ; that's a
  surface-mount resistor swap.
* **Runs while charging.** The 1000C's charger shares the USB power between the iPod and
  the cell ([Adafruit](https://www.adafruit.com/product/2465): "keep your power-hungry
  project running even while recharging the battery"), and still finishes the charge
  (green LED). The older #1905 charger with a PowerBoost 1000 Basic can't: with the Pi
  drawing current it never sees the charge end, and keeps the cell at 4.2 V.
* **It gets warm.** Charging at 1 A while running the iPod, Adafruit warns the charger chip
  gets very hot. Use a 2 A charger, and keep the PowerBoost off the cell in the case
  (chapter 8) `[MEASURE]`.
* **Battery polarity:** JST-PH cells from different sellers are wired both ways. With a
  multimeter, the PowerBoost's BAT pad marked + must read the cell's positive. Swap the
  plug's pins if not.
* **LBO** (low battery) is pulled up to the battery voltage, which can exceed 3.3 V.
  Don't connect it directly to a GPIO.
* Feeding 5 V into the GPIO header (or the 5 V test pads) **bypasses the Pi's input
  protection**. Double-check polarity with a multimeter before the first power-up.
* A Zero 2 W draws noticeably more than a Zero W; a small cell runs down quickly on it.

An iPod built with the earlier #1905 and PowerBoost 1000 Basic keeps working with this
software: only the charging behaviour above differs.

## Charge status

The PowerBoost's LEDs: **yellow** while charging, **green** when full, **red** for low
battery, **blue** when the 5 V output is on. Once the case is closed you can't see them, so
check them on the desk now; inside the case, charging is just "plugged in".

## Shutting down

Cutting power while the Pi is writing can corrupt the SD card. Use **Settings -> Shut
Down**, wait for the screen to go dark, *then* flip the hold switch.

**Check:**

1. With the hold switch released, the PowerBoost's blue LED is on and the Pi boots from
   the battery; with it engaged, everything is off.
2. With the hold switch engaged (iPod off), plug in a **USB-C-to-C** charger: the yellow
   LED comes on (charging). Unplug it.
3. Release the hold switch, start music from Spotify, and plug the charger in again. The
   music keeps playing, and the iPod doesn't reboot or brown out while you plug and unplug
   the cable a few times.

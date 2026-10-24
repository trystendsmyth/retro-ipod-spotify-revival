# 6. Display and haptics

## Composite display (Adafruit #911)

Diagram: [../wiring/03-composite-display.svg](../wiring/03-composite-display.svg)

The #911 driver board has a 4-wire cable: **red = V+ (pin 1), black = GND (pin 2), a
second GND (pin 3) and composite video (pin 4)**; the colours of the last two vary
([Adafruit](https://www.adafruit.com/product/911)). Adafruit's advice for finding them: the
wire next to the black power wire is ground, the one at the end of the connector is video.

**Voltage:** Adafruit specifies **6-12 V** into its onboard regulator, while also listing
120 mA draw at 5 V. The original sPot powered it from the 5 V rail and it worked. If your
screen flickers or stays dark on 5 V, that is the first suspect.

### Bench (Pi 3)

The Pi 3 outputs composite on its 3.5 mm AV jack. Use a 4-pole (TRRS) AV cable to RCA and
plug the display's RCA connector into the cable's **video** plug. Different cable brands
wire the 4 poles differently; if you see no picture, try the other RCA plugs before
anything else. Power the display from a 5 V source (e.g. Pi pin 2 / pin 6) for the test.

The installer already set composite output. **Unplug any HDMI monitor** and reboot -
composite is used when no HDMI display is detected (Raspberry Pi config.txt docs).

### Final (Zero 2 W / Zero W)

* **Zero 2 W:** composite is on test pads on the **underside**, labelled TV and GND, near
  the mini-HDMI end. Official coordinates: TV at (45.58, 3.17) mm, GND at (49.38, 3.05) mm
  from the board origin. ![pads](../images/reference/raspberrypi-zero2-pad-diagram.png)
  <sub>Raspberry Pi Zero 2 W test pad diagram, Raspberry Pi Ltd, CC BY-SA 4.0.</sub>
* **Zero W / Zero:** the two holes labelled **TV** near the GPIO header; the square pad is
  the signal, the round one ground.

Cut the RCA plug off the display cable and solder video to TV and its ground to GND.

**Check:** the iPod menu fills the display. If the edges are clipped, reduce
`FIT_MARGIN` in `frontend/spotifypod.py`; to switch NTSC/PAL re-run the installer with
`TV_NORM=PAL`.

## Haptic motor

Diagram: [../wiring/02-haptic-driver.svg](../wiring/02-haptic-driver.svg)

GPIO 26 (pin 37) -> 220 ohm -> base of a 2N3904; emitter to GND (pin 39); collector to the
motor's negative lead; motor positive to +5 V. This is the original sPot circuit. Add a
**1N4148 across the motor, cathode (striped end) to +5 V** - Guy Dupont later said the lack
of a flyback diode probably caused occasional issues in his build.

Check the 2N3904 pinout in your part's datasheet (for the common TO-92 package, flat side
facing you, legs down: emitter, base, collector). Many 10x2 mm motors are rated around 3 V;
sPot pulsed one from 5 V for 8 ms at a time. If yours runs hot or loud, power it from 3.3 V
instead (pin 17).

`click.c` pulses the motor every second wheel step. Build without it by adding
`-DNO_HAPTIC` (or just leave the motor off).

**Check:** turning the wheel produces short buzzes.

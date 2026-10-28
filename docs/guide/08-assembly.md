# 8. Assemble

Before anything goes into the case, run one full test on the desk from the battery: boot,
Spotify plays, the wheel scrolls with haptics, **Settings -> Shut Down** works and the hold
switch cuts power. Then plug in a USB-C charger and check the iPod keeps playing.

Photos from other builds: insulating the case with polyimide tape, hot glue on the joints
and everything fitted in [Sean's SpotiPod](REFERENCE-BUILDS.md#spotipod-by-sean-shogantech);
the base plate, component layout and long service wires in
[Ricardo's SpotifyPod](REFERENCE-BUILDS.md#spotifypod-by-ricardo-sappia).

## Final wiring

All connections, for either Zero:

| Physical pin | Use |
|---|---|
| 1 | click wheel VCC (3.3 V) |
| 2 | +5 V in from PowerBoost |
| 3 | GPIO 2 DAC SDA (I2C) |
| 4 | +5 V to DAC VIN |
| 5 | GPIO 3 DAC SCL (I2C) |
| 6 | GND (PowerBoost, click wheel) |
| 11 | GPIO 17 DAC RST |
| 12 | GPIO 18 DAC BCK (I2S) |
| 16 | GPIO 23 click wheel CLOCK |
| 22 | GPIO 25 click wheel DATA |
| 34 | GND DAC |
| 35 | GPIO 19 DAC WSEL (I2S) |
| 36 | GPIO 16 jack detect (optional) |
| 37 | GPIO 26 haptic driver input |
| 39 | GND haptic driver |
| 40 | GPIO 21 DAC DIN (I2S) |
| TV hole (Zero W) / TV pad (Zero 2 W) | display video (+ the neighbouring GND) |

Harness drawings, one per subsystem (click wheel, haptic, display, power, audio), and the header
map of every pin to solder: [../wiring/README.md](../wiring/README.md).

## Fitting it in

The 4th-gen case is tight. Tips from builders in the Hackaday discussion:

* Lay a thin pouch cell flat in the back shell and the Pi on top of it.
* Some builders desoldered or trimmed unused ports on the Zero to save height.
* Insulate the Pi's underside and every joint with Kapton tape.
* Trim wires to length now; keep the PowerBoost's BAT wires short.
* **USB-C socket:** print the bracket for your case ([`hardware/`](../../hardware/README.md)),
  screw the breakout to it, and push its bezel into the old dock-connector opening from
  inside. Check a cable clicks in, then glue the bracket's base to the case with two-part
  epoxy. Nothing on the case is cut or drilled.
* Check the PowerBoost's LEDs (chapter 7) before closing the case; they can't be seen
  afterwards.
* Keep the PowerBoost off the cell: it gets warm while charging. Kapton tape between them
  helps.
* Screw the headphone jack board back in with its two T6 screws before closing; its wires
  go to the DAC and (hold switch) to the PowerBoost.
* Put the DAC board near the top of the case, so the three wires to the jack and the eight
  to the header stay short. Insulate its underside with Kapton tape; the case is metal.
* Zero 2 W: its composite wires leave from the underside, so plan the route before laying
  the board down.

Close the case and repeat the full test, including sound from the headphone jack.

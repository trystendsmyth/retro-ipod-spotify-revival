# 8. Move to the Zero and assemble

## Move the software

* **Zero 2 W:** shut the Pi 3 down and move the SD card. The 64-bit image is the same.
* **Zero W:** you need the **32-bit** image (chapter 3). If you bench-tested with a 32-bit
  card, just move it; otherwise flash a new card and repeat chapter 4 on the Zero W.

Boot the Zero once on a desk with the display connected before closing anything up.

## Wiring to the Zero

Solder directly to the Zero's header holes (no header pins - they will not fit). Same pin
numbers as the bench:

| Physical pin | Use |
|---|---|
| 1 | click wheel VCC (3.3 V) |
| 2 | +5 V in from PowerBoost |
| 6 | GND (PowerBoost, click wheel) |
| 16 | GPIO 23 click wheel CLOCK |
| 22 | GPIO 25 click wheel DATA |
| 37 | GPIO 26 haptic driver input |
| 39 | GND haptic driver |
| TV pad / TV hole | display video (+ GND pad) |

Full harness diagram: [../wiring/harness.svg](../wiring/harness.svg).

## Fitting it in

The 4th-gen case is tight. Tips from builders in the Hackaday discussion:

* Lay a thin pouch cell flat in the back shell and the Pi on top of it.
* Some builders desoldered or trimmed unused ports on the Zero to save height.
* Insulate the Pi's underside and every joint with Kapton tape.
* Keep the PowerBoost's BAT wires short and away from the antenna end of the Pi.
* Route the charging port through the old dock-connector opening.

Close the case only after a full test: boot, Spotify plays, wheel and haptics work,
shutdown from the menu, hold switch cuts power.

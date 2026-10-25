# 8. Assemble

Before anything goes into the case, run one full test on the desk from the battery: boot,
Spotify plays, the wheel scrolls with haptics, **Settings -> Shut Down** works and the hold
switch cuts power.

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
| 6 | GND (PowerBoost, click wheel) |
| 16 | GPIO 23 click wheel CLOCK |
| 22 | GPIO 25 click wheel DATA |
| 37 | GPIO 26 haptic driver input |
| 39 | GND haptic driver |
| TV hole (Zero W) / TV pad (Zero 2 W) | display video (+ the neighbouring GND) |

Full harness diagram: [../wiring/harness.svg](../wiring/harness.svg).

## Fitting it in

The 4th-gen case is tight. Tips from builders in the Hackaday discussion:

* Lay a thin pouch cell flat in the back shell and the Pi on top of it.
* Some builders desoldered or trimmed unused ports on the Zero to save height.
* Insulate the Pi's underside and every joint with Kapton tape.
* Trim wires to length now; keep the PowerBoost's BAT wires short.
* Route the charging port through the old dock-connector opening.
* Zero 2 W: its composite wires leave from the underside, so plan the route before laying
  the board down.

Close the case and repeat the full test.

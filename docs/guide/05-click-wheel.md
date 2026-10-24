# 5. Click wheel

Diagram: [../wiring/01-click-wheel.svg](../wiring/01-click-wheel.svg)

## Get the click wheel out

Open the iPod (4th gen A1059: pry the steel back away from the white front along the
sides with plastic tools; the halves are joined by clips and a ribbon to the hard drive).
Disconnect the hard drive, battery and the click wheel ribbon from the logic board. The
click wheel stays in the front shell; you only need its 8-pin, 0.5 mm flat ribbon.

## Pinout

From Jason Garr's reverse engineering, as used by sPot. Pin numbers are as printed on the
click wheel's ribbon.

| FPC pin | Function | Connect to Pi (physical pin / BCM) |
|---|---|---|
| 1 | VCC (was battery voltage in the iPod) | pin **1** (3.3 V) |
| 2 | CLOCK (from the wheel) | pin **16** / GPIO **23** |
| 3 | "hw enable?" - tied to 3.3 V on Garr's board | not connected in sPot (see below) |
| 4, 5 | n/c | - |
| 6 | DATA (pulled up with 100 k in the iPod) | pin **22** / GPIO **25** |
| 7 | "hw enable?" - tied to 3.3 V on Garr's board | not connected in sPot |
| 8 | GND | pin **6** (GND) |

`click.c` enables the Pi's internal pull-ups on CLOCK and DATA. sPot ran with pins 3 and
7 unconnected; if your wheel produces nothing at all, tying 3 and 7 to 3.3 V (as on Garr's
board) is the documented thing to try.

## Wire it (bench)

1. Slide the ribbon into the FPC breakout's connector, contacts facing the connector's
   contacts, and close the latch. Identify pin 1 on the breakout and match it to pin 1 on
   the ribbon.
2. Jumper the four signals to the Pi 3's header as in the table. The Pi 3 header is
   identical to the Zero's.

## Test

```bash
sudo systemctl stop spotifypod      # so you can watch raw events
journalctl -u click -f
```

Touch and turn the wheel and press each button. You should see lines like
`position 46` and `button pressed: 7`. Button numbers: 7 centre, 8 forward, 9 back,
10 play/pause, 11 menu, 29 = finger on the wheel. Then `sudo systemctl start spotifypod`.

**Check:** every button and both scroll directions produce events. In the UI, an
increasing wheel position moves down a list; if scrolling feels reversed on your wheel,
open an issue with your `position` log (the original sPot code also marked the direction
as uncertain).

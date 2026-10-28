#!/usr/bin/env python3
"""Generate the retro-ipod-spotify-revival schematics (SVG + PNG) with schemdraw.

    pip install -r docs/wiring/src/requirements.txt
    python3 docs/wiring/src/schematics.py        # writes docs/wiring/0*.svg|png

Each sheet is written twice: light (white background, plain names) and dark (GitHub
dark background, "-dark" suffix); the Markdown shows the right one with <picture>.

Standard schematic conventions: IEEE resistor/BJT/diode/motor symbols, ground and
supply symbols instead of long return wires, and net labels where a wire would
cross the sheet. Pin numbers are physical header pin numbers; names are BCM GPIOs.

Sources for every connection are listed in docs/wiring/README.md.
"""
import os

from theme import THEMES, reproducible_matplotlib

reproducible_matplotlib()

import schemdraw  # noqa: E402
import schemdraw.elements as elm  # noqa: E402

schemdraw.use("matplotlib")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def new_drawing(t):
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.5, fontsize=11, lw=1.2, color=t["fg"], bgcolor=t["bg"], margin=0.5)
    return d


def pi_block(pins, label="Raspberry Pi Zero W (or Zero 2 W)", spacing=1.0):
    return elm.Ic(pins=pins, edgepadW=0.7, edgepadH=0.5, pinspacing=spacing,
                  leadlen=0.9, w=3.0).label(label, loc="top", fontsize=11)


def bottom(el):
    """Lowest y of an element's bounding box (Ic has no S anchor)."""
    return el.get_bbox(transform=True).ymin


def save(d, name, t):
    base = os.path.join(OUT, f"{name}{t['suffix']}")
    d.save(base + ".svg", transparent=False)
    d.save(base + ".png", transparent=False, dpi=150)
    print("wrote", name + t["suffix"])


def click_wheel(t):
    d = new_drawing(t)
    pi = d.add(pi_block([
        elm.IcPin(name="3V3", pin="1", side="left", slot="8/8"),
        elm.IcPin(name="GPIO23", pin="16", side="left", slot="7/8"),
        elm.IcPin(name="GPIO25", pin="22", side="left", slot="3/8"),
        elm.IcPin(name="GND", pin="6", side="left", slot="1/8"),
    ], spacing=0.8).anchor("center"))
    j1 = d.add(elm.Ic(pins=[
        elm.IcPin(name="1 VCC", side="right", slot="8/8"),
        elm.IcPin(name="2 CLOCK", side="right", slot="7/8"),
        elm.IcPin(name="3 (n.c.*)", side="right", slot="6/8"),
        elm.IcPin(name="4 n.c.", side="right", slot="5/8"),
        elm.IcPin(name="5 n.c.", side="right", slot="4/8"),
        elm.IcPin(name="6 DATA", side="right", slot="3/8"),
        elm.IcPin(name="7 (n.c.*)", side="right", slot="2/8"),
        elm.IcPin(name="8 GND", side="right", slot="1/8"),
    ], edgepadW=0.7, edgepadH=0.5, pinspacing=0.8, leadlen=0.9, w=3.2).label("J1  click wheel\n8-pin 0.5 mm FPC\n(via breakout)", loc="top", fontsize=10)
        .at((pi.center[0] - 9, pi.center[1])).anchor("center"))
    d += elm.Wire("-").at(j1["1 VCC"]).to(pi["3V3"]).color(t["red"])
    d += elm.Wire("-").at(j1["2 CLOCK"]).to(pi["GPIO23"]).color(t["violet"])
    d += elm.Wire("-").at(j1["6 DATA"]).to(pi["GPIO25"]).color(t["teal"])
    d += elm.Wire("-").at(j1["8 GND"]).to(pi["GND"])
    d += elm.Label().at((j1.center[0], bottom(j1) - 1.2)).label(
        "Pins 1/2/6/8 as wired in the original sPot (Dupont 2021).\n"
        "* Jason Garr's notes show pins 3 and 7 tied to 3.3 V on his board;\n"
        "  sPot left them unconnected. Internal pull-ups on GPIO23/25 are enabled by click.c.",
        fontsize=9, halign="left")
    save(d, "01-click-wheel", t)


def haptic_driver(t):
    d = new_drawing(t)
    pi = d.add(pi_block([
        elm.IcPin(name="GPIO26", pin="37", side="right", slot="2/2"),
        elm.IcPin(name="GND", pin="39", side="right", slot="1/2"),
    ]))
    d += elm.Resistor().at(pi["GPIO26"]).right().label("R1\n220 Ω", loc="top").color(t["green"])
    q = d.add(elm.BjtNpn(circle=True).anchor("base").label("Q1\n2N3904", loc="right", ofst=(0.2, 0)))
    d += elm.Line().at(q.emitter).down().length(0.8)
    d += elm.Ground()
    d += elm.Line().at(q.collector).up().length(0.8)
    top = d.here
    d += elm.Line().right().length(1.5)
    d += elm.Motor().up().label("M1\n10×2 mm\nvibration\nmotor", loc="bottom", ofst=0.2)
    mt = d.here
    d += elm.Line().left().length(1.5)
    d += elm.Line().up().length(0.8).color(t["red"])
    d += elm.Vdd().label("+5V").color(t["red"])
    d += elm.Line().at(top).left().length(1.5)
    d += elm.Diode().up().reverse().label("D1\n1N4148", loc="bottom", ofst=0.2).length(mt[1] - top[1])
    d += elm.Line().right().length(1.5)
    d += elm.Wire("-|").at(pi["GND"]).to((pi["GND"][0] + 0.8, pi["GND"][1] - 1.0))
    d += elm.Ground()
    d += elm.Label().at((pi.center[0] + 4, bottom(pi) - 2.2)).label(
        "Q1 low-side switch and R1 as in the original sPot schematic.\n"
        "D1 (flyback, cathode to +5V) is the fix Guy Dupont recommended later.\n"
        "The original pulsed the motor from +5V; check your motor's rated voltage.",
        fontsize=9)
    save(d, "02-haptic-driver", t)


def composite_display(t):
    d = new_drawing(t)
    pi = d.add(pi_block([
        elm.IcPin(name="TV", side="right", slot="4/4"),
        elm.IcPin(name="GND", side="right", slot="3/4"),
    ]))
    disp = d.add(elm.Ic(pins=[
        elm.IcPin(name="4 VIDEO", side="left", slot="4/4"),
        elm.IcPin(name="3 GND", side="left", slot="3/4"),
        elm.IcPin(name="1 V+ (red)", side="left", slot="2/4"),
        elm.IcPin(name="2 GND (black)", side="left", slot="1/4"),
    ], edgepadW=0.7, edgepadH=0.5, pinspacing=1.0, leadlen=0.9, w=3.4)
        .label("U4  Adafruit #911 NTSC/PAL TFT driver", loc="top", fontsize=10)
        .at((pi.center[0] + 11, pi.center[1])).anchor("center"))
    d += elm.Wire("-").at(pi["TV"]).to(disp["4 VIDEO"]).color(t["yellow"]).label("composite video", loc="top", fontsize=9)
    d += elm.Wire("-").at(pi["GND"]).to(disp["3 GND"]).label("video ground", loc="bottom", fontsize=9)
    d += elm.Line().at(disp["1 V+ (red)"]).left().length(1.4).color(t["red"])
    d += elm.Dot(open=True).label("+5V", loc="left").color(t["red"])
    d += elm.Line().at(disp["2 GND (black)"]).left().length(1.4)
    d += elm.Ground()
    d += elm.Label().at((pi.center[0] + 5.5, bottom(disp) - 1.4)).label(
        "Zero W / Zero: the two holes marked TV (square = video, round = GND).\n"
        "Zero 2 W: TV / GND test pads on the underside (Raspberry Pi pad table: TV 45.58, 3.17 mm;\n"
        "GND 49.38, 3.05 mm).\n"
        "Adafruit specifies 6-12 V for the #911 (120 mA at 5 V listed); sPot ran it from 5 V.",
        fontsize=9)
    save(d, "03-composite-display", t)


def power(t):
    d = new_drawing(t)
    usb = d.add(elm.Ic(pins=[
        elm.IcPin(name="VBUS (2)", side="right", slot="2/2"),
        elm.IcPin(name="GND (1)", side="right", slot="1/2"),
    ], edgepadW=0.7, edgepadH=0.6, pinspacing=1.2, leadlen=0.9, w=3.0)
        .label("J3  Adafruit #6050\nUSB-C breakout", loc="top", fontsize=10))
    boost = d.add(elm.Ic(pins=[
        elm.IcPin(name="USB", side="left", slot="4/4"),
        elm.IcPin(name="GND", side="left", slot="3/4", anchorname="GNDIN"),
        elm.IcPin(name="BAT (JST)", side="left", slot="2/4", anchorname="BAT"),
        elm.IcPin(name="EN", side="left", slot="1/4"),
        elm.IcPin(name="5V", side="right", slot="4/4"),
        elm.IcPin(name="GND", side="right", slot="3/4", anchorname="GNDOUT"),
    ], edgepadW=0.7, edgepadH=0.6, pinspacing=1.2, leadlen=0.9, w=3.4)
        .label("U3  Adafruit #2465 PowerBoost 1000C", loc="top", fontsize=10)
        .at((usb.center[0] + 11, usb.center[1] - 1.8)).anchor("center"))
    d += elm.Wire("-|").at(usb["VBUS (2)"]).to(boost["USB"]).color(t["red"])
    d += elm.Wire("-|").at(usb["GND (1)"]).to(boost["GNDIN"])
    d += elm.Line().at(boost["BAT"]).left().length(4.6).color(t["red"])
    d += elm.Battery().down().length(3.6).label("BT1  3.7 V Li-ion\n1000 mAh or more", loc="top", ofst=0.4)
    d += elm.Ground()
    d += elm.Line().at(boost["EN"]).left().length(1.4)
    d += elm.Line().down().length(1.0)
    d += elm.Switch().down().length(1.5).label("SW1 hold switch\nclosed = OFF", loc="bottom", ofst=0.4)
    d += elm.Ground()
    d += elm.Line().at(boost["5V"]).right().length(1.6).color(t["red"])
    d += elm.Dot(open=True).label("+5V rail:\nPi pins 2 and 4, display V+,\nmotor M1 (+)", loc="right").color(t["red"])
    d += elm.Line().at(boost["GNDOUT"]).right().length(1.6)
    d += elm.Dot(open=True).label("GND: Pi pin 6", loc="right")
    d += elm.Label().at((usb.center[0] + 8, bottom(boost) - 4.4)).label(
        "J3 has 5.1 kΩ from CC1 and CC2 to GND, so USB-C-to-C chargers turn on 5 V (no USB-PD; 5 V only).\n"
        "U3 charges the cell at 1 A and runs the iPod from USB while it charges (load sharing).\n"
        "EN is pulled up; tying it to GND turns the 5 V output off, and charging carries on (Adafruit).\n"
        "LBO is pulled up to BAT: never wire it straight to a GPIO. 5 V into the header bypasses the Pi's\n"
        "input protection.",
        fontsize=9)
    save(d, "04-power", t)


def wired_audio(t):
    d = new_drawing(t)
    pi = d.add(pi_block([
        elm.IcPin(name="5V", pin="4", side="right", slot="9/9"),
        elm.IcPin(name="GPIO2 SDA", pin="3", side="right", slot="8/9"),
        elm.IcPin(name="GPIO3 SCL", pin="5", side="right", slot="7/9"),
        elm.IcPin(name="GPIO17", pin="11", side="right", slot="6/9"),
        elm.IcPin(name="GPIO18 BCLK", pin="12", side="right", slot="5/9"),
        elm.IcPin(name="GPIO19 LRCLK", pin="35", side="right", slot="4/9"),
        elm.IcPin(name="GPIO21 DOUT", pin="40", side="right", slot="3/9"),
        elm.IcPin(name="GND", pin="34", side="right", slot="2/9"),
        elm.IcPin(name="GPIO16", pin="36", side="right", slot="1/9"),
    ], spacing=0.8))
    dac = d.add(elm.Ic(pins=[
        elm.IcPin(name="VIN", side="left", slot="9/9"),
        elm.IcPin(name="SDA", side="left", slot="8/9"),
        elm.IcPin(name="SCL", side="left", slot="7/9"),
        elm.IcPin(name="RST", side="left", slot="6/9"),
        elm.IcPin(name="BCK", side="left", slot="5/9"),
        elm.IcPin(name="WSEL", side="left", slot="4/9"),
        elm.IcPin(name="DIN", side="left", slot="3/9"),
        elm.IcPin(name="GND", side="left", slot="2/9"),
        elm.IcPin(name="HPL", side="right", slot="9/9"),
        elm.IcPin(name="HPR", side="right", slot="8/9"),
        elm.IcPin(name="GND", side="right", slot="7/9", anchorname="AGND"),
    ], edgepadW=0.7, edgepadH=0.5, pinspacing=0.8, leadlen=0.9, w=3.0)
        .label("U5  Adafruit #6309\nTLV320DAC3100", loc="top", fontsize=10)
        .at((pi.center[0] + 10, pi.center[1])).anchor("center"))
    jack = d.add(elm.Ic(pins=[
        elm.IcPin(name="TIP (left)", side="left", slot="9/9"),
        elm.IcPin(name="RING (right)", side="left", slot="8/9"),
        elm.IcPin(name="SLEEVE", side="left", slot="7/9"),
        elm.IcPin(name="DET*", side="left", slot="2/9"),
        elm.IcPin(name="DET GND*", side="left", slot="1/9"),
    ], edgepadW=0.7, edgepadH=0.5, pinspacing=0.8, leadlen=0.9, w=3.2)
        .label("J2  iPod headphone jack\n(on the hold-switch board)", loc="top", fontsize=10)
        .at((dac.center[0] + 9.5, dac.center[1])).anchor("center"))
    wires = [
        ("5V", "VIN", t["red"]), ("GPIO2 SDA", "SDA", t["blue"]), ("GPIO3 SCL", "SCL", t["orange"]),
        ("GPIO17", "RST", t["brown"]), ("GPIO18 BCLK", "BCK", t["pink"]),
        ("GPIO19 LRCLK", "WSEL", t["grey"]), ("GPIO21 DOUT", "DIN", t["yellow"]), ("GND", "GND", t["fg"]),
    ]
    for a, b, colour in wires:
        d += elm.Wire("-").at(pi[a]).to(dac[b]).color(colour)
    d += elm.Wire("-").at(dac["HPL"]).to(jack["TIP (left)"])
    d += elm.Wire("-").at(dac["HPR"]).to(jack["RING (right)"]).color(t["red"])
    d += elm.Wire("-").at(dac["AGND"]).to(jack["SLEEVE"])
    # Optional jack detect: under the DAC to the jack's switch contact
    x0, y_under = pi["GPIO16"][0] + 1.5, bottom(dac) - 0.6
    x_turn = jack["DET*"][0] - 1.2
    det = t["lightblue"]
    d += elm.Line().at(pi["GPIO16"]).to((x0, pi["GPIO16"][1])).color(det)
    d += elm.Line().to((x0, y_under)).color(det)
    d += elm.Line().to((x_turn, y_under)).color(det)
    d += elm.Line().to((x_turn, jack["DET*"][1])).color(det)
    d += elm.Line().to(jack["DET*"]).color(det)
    d += elm.Line().at(jack["DET GND*"]).left().length(0.8)
    d += elm.Ground()
    d += elm.Label().at((pi.center[0] + 9, bottom(pi) - 2.3)).label(
        "U5 runs from the 5 V rail through its own 3.3 V regulator. HPL and HPR are its\n"
        "AC-coupled headphone outputs (100 µF on the board). No kernel driver: tlv320.py sets it up over\n"
        "I2C at boot, then i2s-dac carries the audio. Keep the audio wires short and the jack's ground on U5.\n"
        "* Optional jack detect: the jack's switch contact, found with a multimeter [MEASURE], to GPIO16\n"
        "  (pull-up set in config.txt); set JACK_PLUGGED_LEVEL to what the pin reads with a plug in.",
        fontsize=9)
    save(d, "05-wired-audio", t)


if __name__ == "__main__":
    for theme in THEMES:
        click_wheel(theme)
        haptic_driver(theme)
        composite_display(theme)
        power(theme)
        wired_audio(theme)

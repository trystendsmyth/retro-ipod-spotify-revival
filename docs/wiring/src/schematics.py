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
    chg = d.add(elm.Ic(pins=[
        elm.IcPin(name="USB in", side="left", slot="2/2"),
        elm.IcPin(name="BAT", side="right", slot="2/2"),
        elm.IcPin(name="GND", side="right", slot="1/2"),
    ], edgepadW=0.7, edgepadH=0.6, pinspacing=1.2, leadlen=0.9, w=3.0)
        .label("U2  Adafruit #1905 charger", loc="top", fontsize=10))
    boost = d.add(elm.Ic(pins=[
        elm.IcPin(name="BAT", side="left", slot="3/3"),
        elm.IcPin(name="EN", side="left", slot="1/3"),
        elm.IcPin(name="5V", side="right", slot="3/3"),
        elm.IcPin(name="GND", side="right", slot="1/3", anchorname="GNDOUT"),
    ], edgepadW=0.7, edgepadH=0.6, pinspacing=1.2, leadlen=0.9, w=3.0)
        .label("U3  Adafruit #2030 PowerBoost 1000 Basic", loc="top", fontsize=10)
        .at((chg.center[0] + 14, chg.center[1] - 1.2)).anchor("center"))
    d += elm.Line().at(chg["USB in"]).left().length(1.0)
    d += elm.Dot(open=True).label("USB\ncharge port", loc="left")
    bx = chg["BAT"][0] + 3.0
    d += elm.Line().at(chg["BAT"]).right().length(3.0).color(t["red"])
    d += elm.Dot().color(t["red"])
    d += elm.Wire("|-").to(boost["BAT"]).color(t["red"])
    d += elm.Battery().at((bx, chg["BAT"][1])).down().length(3.5).label("BT1  3.7 V Li-ion", loc="bottom", ofst=0.4)
    d += elm.Ground()
    d += elm.Line().at(chg["GND"]).right().length(0.8)
    d += elm.Ground()
    d += elm.Line().at(boost["EN"]).left().length(2.0)
    d += elm.Switch().down().length(1.5).label("SW1 hold switch\nclosed = OFF", loc="top", ofst=0.5)
    d += elm.Ground()
    d += elm.Line().at(boost["5V"]).right().length(1.6).color(t["red"])
    d += elm.Dot(open=True).label("+5V rail:\nPi pin 2, display V+,\nmotor M1 (+)", loc="right").color(t["red"])
    d += elm.Line().at(boost["GNDOUT"]).right().length(1.6)
    d += elm.Dot(open=True).label("GND: Pi pin 6", loc="right")
    d += elm.Label().at((chg.center[0] + 8, bottom(chg) - 4.2)).label(
        "PowerBoost EN is pulled up to BAT; tying it to GND turns the 5 V output off (Adafruit).\n"
        "sPot used the iPod hold switch this way. LBO is pulled up to BAT: never wire it straight\n"
        "to a GPIO. Feeding 5 V into the GPIO header bypasses the Pi's input protection.",
        fontsize=9)
    save(d, "04-power", t)


if __name__ == "__main__":
    for theme in THEMES:
        click_wheel(theme)
        haptic_driver(theme)
        composite_display(theme)
        power(theme)

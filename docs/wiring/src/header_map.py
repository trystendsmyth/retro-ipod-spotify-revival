#!/usr/bin/env python3
"""Draw the 40-pin header with the pins this build uses (docs/wiring/header-map*.svg|png).

    pip install -r docs/wiring/src/requirements.txt
    python3 docs/wiring/src/header_map.py

Physical-pin order as in the Raspberry Pi pinout convention: odd pins on one row, even
pins on the other, pin 1 drawn square. tests/test_wiring_pins.py checks USED against
clickwheel/click.c, the harness files and the pin table in docs/wiring/README.md.
"""
import os

from theme import THEMES, reproducible_matplotlib

# physical pin: (name, BCM GPIO or None, what it connects to, theme colour key)
USED = {
    1: ("3V3", None, "click wheel VCC", "red"),
    2: ("5V", None, "5V in from PowerBoost", "red"),
    3: ("GPIO2", 2, "DAC SDA (I2C)", "blue"),
    4: ("5V", None, "DAC VIN", "red"),
    5: ("GPIO3", 3, "DAC SCL (I2C)", "orange"),
    6: ("GND", None, "PowerBoost, click wheel", "fg"),
    11: ("GPIO17", 17, "DAC RST", "brown"),
    12: ("GPIO18", 18, "DAC BCK (I2S)", "pink"),
    16: ("GPIO23", 23, "click wheel clock", "violet"),
    22: ("GPIO25", 25, "click wheel data", "teal"),
    34: ("GND", None, "DAC ground", "fg"),
    35: ("GPIO19", 19, "DAC WSEL (I2S)", "grey"),
    36: ("GPIO16", 16, "jack detect (optional)", "lightblue"),
    37: ("GPIO26", 26, "haptic driver", "green"),
    39: ("GND", None, "haptic driver ground", "fg"),
    40: ("GPIO21", 21, "DAC DIN (I2S)", "yellow"),
}

# Label placement: levels keep neighbours apart. Left-aligned labels stack higher towards
# the left and right-aligned ones towards the right, so no leader line crosses a label.
LABEL_LEVEL = {2: 5, 4: 4, 6: 3, 12: 2, 16: 1, 22: 1, 34: 1, 36: 2, 40: 3,
               1: 4, 3: 3, 5: 2, 11: 1, 35: 1, 37: 2, 39: 3}
RIGHT_ALIGNED = {34, 36, 40, 35, 37, 39}
LEVEL_STEP = 0.9

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def position(pin):
    """(x, y) of a physical pin: 20 columns, even pins on the top row."""
    return (pin - 1) // 2, (1.0 if pin % 2 == 0 else 0.0)


def label_text(pin):
    name, _, what, _ = USED[pin]
    return f"Pin {pin}  {name}\n{what}"


def draw(t):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

    fig, ax = plt.subplots(figsize=(15, 10))
    fig.patch.set_facecolor(t["bg"])
    ax.set_facecolor(t["bg"])
    ax.set_xlim(-1.2, 20.2)
    ax.set_ylim(-6.9, 7.4)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((-0.6, -0.55), 20.2, 2.1, boxstyle="round,pad=0.05",
                                facecolor=t["bg"], edgecolor=t["fg"], linewidth=1.2))
    for pin in range(1, 41):
        x, y = position(pin)
        used = pin in USED
        colour = t[USED[pin][3]] if used else t["muted"]
        if pin == 1:
            ax.add_patch(Rectangle((x - 0.33, y - 0.33), 0.66, 0.66, facecolor=colour,
                                   edgecolor=t["fg"], linewidth=1.0))
        else:
            ax.add_patch(Circle((x, y), 0.33, facecolor=colour,
                                edgecolor=t["fg"] if used else colour, linewidth=1.0))
        if not used:
            continue
        ax.text(x, y, str(pin), ha="center", va="center", fontsize=7.5,
                color=t["on_fg"] if USED[pin][3] == "fg" else t["on_wire"], fontweight="bold")
        level = LABEL_LEVEL[pin]
        up = y > 0.5
        ly = (1.0 + LEVEL_STEP * level) if up else (-LEVEL_STEP * level)
        ax.plot([x, x], [y + (0.33 if up else -0.33), ly - (0.1 if up else -0.1)],
                color=t[USED[pin][3]], linewidth=1.2)
        ax.text(x + (0.15 if pin not in RIGHT_ALIGNED else -0.15), ly, label_text(pin),
                ha="right" if pin in RIGHT_ALIGNED else "left",
                va="bottom" if up else "top", fontsize=9, color=t["fg"], linespacing=1.25)

    ax.text(-0.6, 7.3, "Raspberry Pi Zero W / Zero 2 W: header pins this build uses",
            fontsize=12, fontweight="bold", color=t["fg"], va="top")
    ax.text(-0.6, 6.85, "Physical pin numbers. Pin 1 is the square pad; odd pins on one row, "
            "even pins on the other. Grey pins are not used.", fontsize=9, color=t["fg"], va="top")
    ax.text(-0.6, -4.7,
            "Composite video is not on this header:\n"
            "  Zero W: the two holes marked TV (square pad = video, round pad = ground).\n"
            "  Zero 2 W: the TV and GND test pads on the underside; see the Raspberry Pi pad diagram\n"
            "  (docs/images/reference/raspberrypi-zero2-pad-diagram.png).",
            fontsize=9, color=t["fg"], va="top", linespacing=1.4,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": t["bg"], "edgecolor": t["yellow"]})

    base = os.path.join(OUT, f"header-map{t['suffix']}")
    fig.savefig(base + ".svg", facecolor=t["bg"], bbox_inches="tight", pad_inches=0.15)
    fig.savefig(base + ".png", facecolor=t["bg"], bbox_inches="tight", pad_inches=0.15, dpi=150)
    plt.close(fig)
    print("wrote header-map" + t["suffix"])


if __name__ == "__main__":
    reproducible_matplotlib()
    for theme in THEMES:
        draw(theme)

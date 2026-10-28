"""Colours shared by the schematics, the header map and the WireViz harnesses.

Every diagram is rendered twice: "light" (the plain file names, white background) and
"dark" (a "-dark" suffix, GitHub dark background). Wire colours match the harness wire
colour codes: VCC/+5V red (RD), clock violet (VT), data turquoise (TQ), haptic green (GN),
video and I2S data yellow (YE), I2C SDA blue (BU), I2C SCL orange (OG), DAC reset brown
(BN), I2S bit clock pink (PK), I2S word select grey (GY), jack detect light blue (LB),
ground black (BK, drawn in the foreground colour).
"""

LIGHT = {
    "suffix": "",
    "bg": "#ffffff",
    "fg": "#000000",
    "muted": "#c8ccd0",
    "red": "#c0392b",
    "violet": "#8e44ad",
    "teal": "#16a085",
    "green": "#1e8449",
    "yellow": "#b7950b",
    "blue": "#1f5fa8",
    "orange": "#c0620f",
    "brown": "#7b4a1e",
    "pink": "#c2185b",
    "grey": "#5d6d7e",
    "lightblue": "#2e86c1",
    "on_wire": "#ffffff",   # text on a wire-coloured fill
    "on_fg": "#ffffff",     # text on a foreground-coloured fill
}

DARK = {
    "suffix": "-dark",
    "bg": "#0d1117",
    "fg": "#e6edf3",
    "muted": "#30363d",
    "red": "#ff7b72",
    "violet": "#d2a8ff",
    "teal": "#56d4bc",
    "green": "#7ee787",
    "yellow": "#f2cc60",
    "blue": "#79c0ff",
    "orange": "#ffa657",
    "brown": "#d2a679",
    "pink": "#ff9bce",
    "grey": "#b1bac4",
    "lightblue": "#a5d6ff",
    "on_wire": "#0d1117",
    "on_fg": "#0d1117",
}

THEMES = (LIGHT, DARK)


def reproducible_matplotlib():
    """Same input, same bytes: fixed SVG ids and no timestamp in the SVG metadata."""
    import os
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "retro-ipod-spotify-revival"

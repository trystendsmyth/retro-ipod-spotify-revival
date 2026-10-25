"""Colours shared by the schematics, the header map and the WireViz harnesses.

Every diagram is rendered twice: "light" (the plain file names, white background) and
"dark" (a "-dark" suffix, GitHub dark background). Wire colours match the harness wire
colour codes: VCC/+5V red (RD), clock violet (VT), data turquoise (TQ), haptic green (GN),
video yellow (YE), ground black (BK, drawn in the foreground colour).
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
}

THEMES = (LIGHT, DARK)


def reproducible_matplotlib():
    """Same input, same bytes: fixed SVG ids and no timestamp in the SVG metadata."""
    import os
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "retro-ipod-spotify-revival"

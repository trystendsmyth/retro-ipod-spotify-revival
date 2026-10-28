#!/usr/bin/env python3
"""Sort the facets of an ASCII STL in place, so the same model gives the same bytes.

OpenSCAD writes the same triangles in a different order from run to run. CI renders
the bracket, runs this, and fails if the committed STL differs.

    python3 hardware/normalize_stl.py hardware/usb-c-bracket.stl
"""
import sys


def normalize(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("solid") or not lines[-1].startswith("endsolid"):
        raise ValueError("not an ASCII STL")
    facets, current = [], []
    for line in lines[1:-1]:
        current.append(line)
        if line == "endfacet":
            facets.append("\n".join("  " + x for x in current))
            current = []
    if current:
        raise ValueError("unterminated facet")
    return "\n".join([lines[0], *sorted(facets), lines[-1]]) + "\n"


if __name__ == "__main__":
    for path in sys.argv[1:]:
        with open(path) as fh:
            out = normalize(fh.read())
        with open(path, "w") as fh:
            fh.write(out)

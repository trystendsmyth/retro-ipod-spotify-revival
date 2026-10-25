"""The header map, harness drawings and pin table agree with each other and with click.c."""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
WIRING = os.path.join(ROOT, "docs", "wiring")
sys.path.insert(0, os.path.join(WIRING, "src"))

import header_map  # noqa: E402  (pin data only; drawing needs matplotlib)


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _click_defaults():
    src = _read("clickwheel", "click.c")
    return {name: int(v) for name, v in re.findall(r"#define (\w+)_PIN (\d+)", src)}


# BCM GPIO -> physical pin on the 40-pin header (Raspberry Pi pinout)
BCM_TO_PHYSICAL = {23: 16, 25: 22, 26: 37}


def test_header_map_gpios_match_click_c_defaults():
    pins = _click_defaults()
    used_gpio = {bcm: phys for phys, (_, bcm, _, _) in header_map.USED.items() if bcm is not None}
    assert used_gpio == {pins["CLOCK"]: 16, pins["DATA"]: 22, pins["HAPTIC"]: 37}
    for bcm, phys in used_gpio.items():
        assert BCM_TO_PHYSICAL[bcm] == phys


def test_header_map_matches_pin_table():
    table = _read("docs", "wiring", "README.md")
    rows = re.findall(r"^\| [^|]+ \| (\d+)(?: \([^)]*\))? \| (\d+|-) \|", table, flags=re.M)
    physical = {int(p) for p, _ in rows}
    assert physical == set(header_map.USED)
    for phys, bcm in rows:
        expected = header_map.USED[int(phys)][1]
        assert (None if bcm == "-" else int(bcm)) == expected, f"pin {phys}"


def test_harnesses_only_use_header_map_pins():
    used = set()
    for name in ("clickwheel", "haptic", "power"):
        text = _read("docs", "wiring", "src", f"harness-{name}.yml")
        for pins in re.findall(r"^    - PI: \[([^\]]+)\]", text, flags=re.M):
            used |= {int(p) for p in pins.split(",")}
    assert used == set(header_map.USED)

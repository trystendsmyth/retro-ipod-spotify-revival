"""The header map, harness drawings and pin table agree with each other, with click.c
and with the installer's wired-audio pins."""
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
BCM_TO_PHYSICAL = {2: 3, 3: 5, 16: 36, 17: 11, 18: 12, 19: 35, 21: 40, 23: 16, 25: 22, 26: 37}

# Wired audio (TLV320DAC3100): I2C SDA/SCL, DAC reset, I2S BCLK/LRCLK/DOUT, jack detect
AUDIO_GPIOS = {2, 3, 17, 18, 19, 21, 16}


def _used_gpio():
    return {bcm: phys for phys, (_, bcm, _, _) in header_map.USED.items() if bcm is not None}


def test_header_map_gpios_match_click_c_and_audio():
    pins = _click_defaults()
    used_gpio = _used_gpio()
    click = {pins["CLOCK"]: 16, pins["DATA"]: 22, pins["HAPTIC"]: 37}
    assert set(used_gpio) == set(click) | AUDIO_GPIOS
    for bcm, phys in used_gpio.items():
        assert BCM_TO_PHYSICAL[bcm] == phys
    for bcm, phys in click.items():
        assert used_gpio[bcm] == phys


def test_installer_audio_pins_match_header_map():
    check = _read("install", "bin", "check-pins.sh")
    claimed = {int(g) for g in re.findall(r'^\s*claim (\d+) "I2[SC]', check, flags=re.M)}
    assert claimed == {2, 3, 18, 19, 20, 21}            # 20: I2S DIN, taken but unwired
    assert claimed - {20} <= set(_used_gpio())
    reset = {int(v) for v in re.findall(r"DAC_RESET_GPIO:-(\d+)", _read("install", "install.sh")
                                         + _read("install", "bin", "configure-audio.sh") + check)}
    reset |= {int(v) for v in re.findall(r'"DAC_RESET_GPIO", "(\d+)"', _read("install", "bin", "tlv320.py"))}
    assert reset == {17} and header_map.USED[11][1] == 17
    assert "JACK_DETECT_GPIO=16" in _read("docs", "guide", "06b-wired-audio.md")


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
    for name in ("clickwheel", "haptic", "power", "audio"):
        text = _read("docs", "wiring", "src", f"harness-{name}.yml")
        for pins in re.findall(r"^\s*-(?: -)? PI(?: detect)?: \[([^\]]+)\]", text, flags=re.M):
            used |= {int(p) for p in pins.split(",")}
    assert used == set(header_map.USED)


def test_every_harness_is_rendered_in_ci_and_docs():
    names = sorted(f[len("harness-"):-len(".yml")] for f in os.listdir(os.path.join(WIRING, "src"))
                   if f.startswith("harness-") and f.endswith(".yml"))
    loop = "for f in " + " ".join(["clickwheel", "haptic", "display", "power", "audio"]) + "; do"
    assert sorted(["clickwheel", "haptic", "display", "power", "audio"]) == names
    assert loop in _read(".github", "workflows", "ci.yml")
    assert loop in _read("docs", "wiring", "README.md")

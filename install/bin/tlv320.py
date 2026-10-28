#!/usr/bin/env python3
"""Set up the TLV320DAC3100 (Adafruit #6309) for the headphone jack, over I2C.

    tlv320.py start   reset the codec, configure clocks and the headphone driver
    tlv320.py stop    ramp the headphone driver down and hold the codec in reset

Raspberry Pi OS has no kernel driver for this codec. The I2S side is the generic
i2s-dac overlay (the Pi drives BCLK and LRCLK, BCLK = 64 x the sample rate); this
script writes the codec's registers once per boot (spotifypod-dac.service).

Register values follow TI's TLV320DAC3100 datasheet (SLAS671) and Adafruit's
CircuitPython driver (adafruit_tlv320.py, MIT, Liz Clark for Adafruit Industries),
whose BCLK-as-PLL-input settings are rescaled here from 32 x fs to 64 x fs.

Env: DAC_RESET_GPIO (BCM, default 17), DAC_I2C_BUS (default 1),
     WIRED_GAIN_DB (headphone analog volume, 0 to -35 dB, default -20).
Standard library only: the Pi Zero W image needs nothing extra.
"""
from __future__ import annotations

import fcntl
import os
import subprocess
import sys
import time

ADDRESS = 0x18
I2C_SLAVE = 0x0703

# Datasheet table 6-24: headphone analog volume register value -> dB, for 0 to -35 dB.
TABLE_6_24 = [-i / 2 for i in range(36)] + [
    -18.1, -18.6, -19.1, -19.6, -20.1, -20.6, -21.1, -21.6, -22.1, -22.6,
    -23.1, -23.6, -24.1, -24.6, -25.1, -25.6, -26.1, -26.6, -27.1, -27.6,
    -28.1, -28.6, -29.1, -29.6, -30.1, -30.6, -31.1, -31.6, -32.1, -32.6,
    -33.1, -33.6, -34.1, -34.6, -35.2,
]

# PLL from BCLK = 64 fs: CODEC_CLKIN = BCLK * R * J / P = 2176 fs, then
# fs = CODEC_CLKIN / (NDAC * MDAC * DOSR). PLL output is 96.0 MHz at 44.1 kHz and
# 104.4 MHz at 48 kHz (datasheet range 80-110 MHz); DAC_MOD_CLK = 128 fs.
P, R, J, D = 1, 2, 17, 0
NDAC, MDAC, DOSR = 17, 1, 128


def hp_volume_reg(gain_db: float) -> int:
    """Nearest table 6-24 step at or below gain_db (never louder than asked)."""
    gain_db = max(-35.2, min(0.0, gain_db))
    return next(i for i, db in enumerate(TABLE_6_24) if db <= gain_db + 1e-9)


def start_sequence(gain_db: float) -> list[tuple[int, int, int]]:
    """(page, register, value) writes after a reset, in datasheet order."""
    hp = 0x80 | hp_volume_reg(gain_db)
    return [
        # Page 0: clocks and interface
        (0, 0x01, 0x01),            # software reset
        (0, 0x41, 0x81), (0, 0x42, 0x81),  # DAC volume -63.5 dB while setting up
        (0, 0x3F, 0x14),            # DACs off (paths normal, soft-step 1 sample)
        (0, 0x05, (P << 4) | R),    # PLL off, P and R
        (0, 0x06, J),
        (0, 0x07, (D >> 8) & 0xFF), (0, 0x08, D & 0xFF),
        (0, 0x04, 0x04),            # PLL_CLKIN = BCLK
        (0, 0x05, 0x80 | (P << 4) | R),  # PLL on
        "wait",
        (0, 0x04, 0x07),            # CODEC_CLKIN = PLL_CLK
        (0, 0x1B, 0x30),            # I2S, 32-bit slots (BCLK and WCLK are inputs)
        (0, 0x0B, 0x80 | NDAC), (0, 0x0C, 0x80 | MDAC),
        (0, 0x0D, (DOSR >> 8) & 0xFF), (0, 0x0E, DOSR & 0xFF),
        (0, 0x3F, 0xD4),            # left and right DACs on
        # Page 1: headphone driver
        (1, 0x21, 0xBE),            # pop removal: wait for power-down, slow power-up and ramp
        (1, 0x23, 0x44),            # left and right DAC to the output mixers
        (1, 0x28, 0x04), (1, 0x29, 0x04),  # HPL/HPR driver 0 dB, unmuted
        (1, 0x24, hp), (1, 0x25, hp),      # analog volume to HPL/HPR (WIRED_GAIN_DB)
        (1, 0x1F, 0xD4),            # HPL and HPR powered, common mode 1.65 V
        "wait",
        # Page 0: DAC to 0 dB and unmuted last
        (0, 0x41, 0x00), (0, 0x42, 0x00),
        (0, 0x40, 0x00),
    ]


STOP_SEQUENCE = [
    (0, 0x40, 0x0C),                # mute both DACs (soft-stepped)
    "wait",
    (1, 0x1F, 0x14),                # headphone drivers off (pop-free ramp from 0x21)
    "wait",
    (0, 0x3F, 0x14),                # DACs off
    (0, 0x05, (P << 4) | R),        # PLL off
]


class Bus:
    """One codec on /dev/i2c-N. Page writes are skipped when the page is current."""

    def __init__(self, bus: int, address: int = ADDRESS):
        self.fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, address)
        self.page = None

    def write(self, page: int, register: int, value: int) -> None:
        if page != self.page:
            os.write(self.fd, bytes([0x00, page]))
            self.page = page
        os.write(self.fd, bytes([register, value]))

    def close(self) -> None:
        os.close(self.fd)


def run(bus, sequence, wait=lambda: time.sleep(0.02)) -> None:
    for step in sequence:
        if step == "wait":
            wait()
        else:
            bus.write(*step)


def set_reset(gpio: str, high: bool) -> None:
    # Output with no pull, driven; config.txt holds it low from boot (gpio=N=op,dl).
    subprocess.run(["pinctrl", "set", gpio, "op", "pn", "dh" if high else "dl"], check=True)


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("start", "stop"):
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        return 2
    reset_gpio = os.environ.get("DAC_RESET_GPIO", "17")
    bus_no = int(os.environ.get("DAC_I2C_BUS", "1"))
    if argv[1] == "start":
        gain = float(os.environ.get("WIRED_GAIN_DB", "-20"))
        set_reset(reset_gpio, False)
        time.sleep(0.01)
        set_reset(reset_gpio, True)
        time.sleep(0.01)
        bus = Bus(bus_no)
        try:
            run(bus, start_sequence(gain))
        finally:
            bus.close()
        print(f"tlv320: headphone output on, {TABLE_6_24[hp_volume_reg(gain)]} dB")
    else:
        try:
            bus = Bus(bus_no)
            try:
                run(bus, STOP_SEQUENCE, wait=lambda: time.sleep(0.1))
            finally:
                bus.close()
        except OSError as exc:  # codec already off or never set up
            print(f"tlv320: {exc}", file=sys.stderr)
        set_reset(reset_gpio, False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

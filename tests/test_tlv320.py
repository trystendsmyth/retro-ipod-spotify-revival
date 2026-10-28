"""install/bin/tlv320.py: register sequence and clock plan for the TLV320DAC3100."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), "..", "install", "bin", "tlv320.py")
_spec = importlib.util.spec_from_file_location("tlv320", _PATH)
tlv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tlv)


class FakeBus:
    def __init__(self):
        self.page = None
        self.writes = []      # (page, register, value) as the codec sees them
        self.raw = []

    def write(self, page, register, value):
        if page != self.page:
            self.raw.append((0x00, page))
            self.page = page
        self.raw.append((register, value))
        self.writes.append((page, register, value))


@pytest.mark.parametrize("fs", [44100, 48000])
def test_clock_plan_meets_datasheet_limits(fs):
    bclk = 64 * fs                                   # i2s-dac fixes BCLK at 64 fs
    assert 512e3 <= bclk / tlv.P <= 20e6             # PLL input range
    pll = bclk * tlv.R * (tlv.J + tlv.D / 10000) / tlv.P
    assert 80e6 <= pll <= 110e6                      # PLL output range
    dac_mod_clk = pll / (tlv.NDAC * tlv.MDAC)
    assert dac_mod_clk <= 6.758e6
    assert dac_mod_clk / tlv.DOSR == pytest.approx(fs)


def test_start_sequence_order_and_values():
    bus = FakeBus()
    tlv.run(bus, tlv.start_sequence(-20), wait=lambda: None)
    w = bus.writes
    assert w[0] == (0, 0x01, 0x01)                   # reset first
    # PLL configured while off, then powered, then selected as CODEC_CLKIN
    pll_on = w.index((0, 0x05, 0x92))
    assert w.index((0, 0x06, 17)) < pll_on < w.index((0, 0x04, 0x07))
    assert w.index((0, 0x04, 0x04)) < pll_on
    assert (0, 0x1B, 0x30) in w                      # I2S, 32-bit slots
    assert (0, 0x0B, 0x91) in w and (0, 0x0C, 0x81) in w and (0, 0x0E, 0x80) in w
    # headphone volume -20.1 dB (table 6-24 index 40), driver powered after routing
    assert (1, 0x24, 0x80 | 40) in w and (1, 0x25, 0x80 | 40) in w
    assert w.index((1, 0x23, 0x44)) < w.index((1, 0x1F, 0xD4))
    # DACs stay at -63.5 dB until the end; unmute is the last write
    assert w.index((0, 0x41, 0x00)) > w.index((1, 0x1F, 0xD4))
    assert w[-1] == (0, 0x40, 0x00)


def test_page_select_only_when_it_changes():
    bus = FakeBus()
    tlv.run(bus, tlv.start_sequence(-20), wait=lambda: None)
    selects = [v for r, v in bus.raw if r == 0x00]
    assert selects == [0, 1, 0]


@pytest.mark.parametrize("gain,reg", [(0, 0), (-6, 12), (-17.5, 35), (-18, 36), (-20, 40),
                                      (-20.1, 40), (-35, 70), (-60, 70), (6, 0)])
def test_headphone_volume_never_louder_than_asked(gain, reg):
    assert tlv.hp_volume_reg(gain) == reg
    assert tlv.TABLE_6_24[reg] <= max(gain, -35.2) + 1e-9


def test_stop_mutes_before_powering_down():
    bus = FakeBus()
    tlv.run(bus, tlv.STOP_SEQUENCE, wait=lambda: None)
    assert bus.writes[0] == (0, 0x40, 0x0C)
    assert bus.writes.index((1, 0x1F, 0x14)) < bus.writes.index((0, 0x3F, 0x14))


def test_main_resets_through_pinctrl(monkeypatch):
    calls, bus = [], FakeBus()
    monkeypatch.setattr(tlv.subprocess, "run", lambda args, check: calls.append(args))
    monkeypatch.setattr(tlv, "Bus", lambda n: bus)
    monkeypatch.setattr(tlv.time, "sleep", lambda s: None)
    bus.close = lambda: None
    monkeypatch.setenv("DAC_RESET_GPIO", "17")
    assert tlv.main(["tlv320.py", "start"]) == 0
    assert calls == [["pinctrl", "set", "17", "op", "pn", "dl"],
                     ["pinctrl", "set", "17", "op", "pn", "dh"]]
    assert bus.writes[-1] == (0, 0x40, 0x00)
    assert tlv.main(["tlv320.py", "bogus"]) == 2

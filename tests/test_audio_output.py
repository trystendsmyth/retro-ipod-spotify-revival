"""Output selection (jack vs Bluetooth) against a fake PipeWire / bluez command line."""
import json

import pytest

import audio_output as ao
import bt_manager

JBL = "AA:BB:CC:DD:EE:01"
SONY = "AA:BB:CC:DD:EE:02"
DAC = {"id": 40, "name": "alsa_output.platform-soc_sound.stereo-fallback",
       "description": "snd_rpi_rpi_dac", "card": "snd_rpi_rpi_dac"}


class FakeSystem:
    """Answers the pw-dump / wpctl / pactl / bluetoothctl calls bt_manager makes."""

    def __init__(self):
        self.sinks = [dict(DAC)]
        self.default = None
        self.streams = {7: None, 9: None}       # sink-input id -> sink name
        self.paired = {JBL: "JBL Flip", SONY: "WH-1000"}
        self.connected = set()
        self.volumes = {}
        self.calls = []

    def bt_sink(self, mac, sink_id):
        self.connected.add(mac)
        self.sinks.append({"id": sink_id, "name": f"bluez_output.{mac.replace(':', '_')}.1",
                           "description": self.paired[mac], "card": ""})

    def drop_bt(self, mac):
        self.connected.discard(mac)
        name = f"bluez_output.{mac.replace(':', '_')}.1"
        self.sinks = [s for s in self.sinks if s["name"] != name]
        if self.default == name:
            self.default = None

    def default_sink(self):
        return next((s for s in self.sinks if s["name"] == self.default), None)

    def run(self, args, timeout=10):
        self.calls.append(args)
        cmd = args[0]
        if cmd == "pw-dump":
            objs = [{"type": "PipeWire:Interface:Metadata",
                     "metadata": [{"key": "default.audio.sink", "value": {"name": self.default}}]}]
            for s in self.sinks:
                props = {"media.class": "Audio/Sink", "node.name": s["name"],
                         "node.description": s["description"]}
                if s["card"]:
                    props["alsa.card_name"] = s["card"]
                objs.append({"type": "PipeWire:Interface:Node", "id": s["id"], "info": {"props": props}})
            return 0, json.dumps(objs)
        if args[:2] == ["wpctl", "set-default"]:
            sink = next((s for s in self.sinks if s["id"] == int(args[2])), None)
            if sink is None:
                return 1, "no such node"
            self.default = sink["name"]
            return 0, ""
        if args[:2] == ["wpctl", "set-volume"]:
            self.volumes[int(args[2])] = float(args[3])
            return 0, ""
        if args[:4] == ["pactl", "list", "short", "sink-inputs"]:
            return 0, "".join(f"{i}\t{s or 0}\tgo-librespot\ts16le 2ch 44100Hz\tRUNNING\n"
                              for i, s in self.streams.items())
        if args[:2] == ["pactl", "move-sink-input"]:
            self.streams[int(args[2])] = args[3]
            return 0, ""
        if cmd == "bluetoothctl":
            rest = args[1:]
            if rest == ["devices"]:
                return 0, "".join(f"Device {m} {n}\n" for m, n in self.paired.items())
            if rest == ["devices", "Paired"]:
                return 0, "".join(f"Device {m} {n}\n" for m, n in self.paired.items())
            if rest == ["devices", "Connected"]:
                return 0, "".join(f"Device {m} {self.paired[m]}\n" for m in self.connected)
            if rest == ["devices", "Trusted"]:
                return 0, ""
            if rest[0] == "connect":
                self.bt_sink(rest[1], 60)
                return 0, "Connection successful"
        raise AssertionError(f"unexpected command {args}")


@pytest.fixture
def system(monkeypatch, tmp_path):
    fake = FakeSystem()
    monkeypatch.setattr(bt_manager, "_run", fake.run)
    monkeypatch.setattr(bt_manager.time, "sleep", lambda s: None)
    monkeypatch.setenv("SPOTIFYPOD_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AUDIO_BACKEND", "pulseaudio")
    monkeypatch.setenv("WIRED_AUDIO", "i2s")
    monkeypatch.delenv("JACK_DETECT_GPIO", raising=False)
    monkeypatch.setattr(ao, "_last_plugged", None)
    monkeypatch.setattr(ao, "_capped", set())
    return fake


def _plug(monkeypatch, state):
    monkeypatch.setattr(ao, "jack_plugged", lambda: state)


def test_defaults_to_jack_without_bluetooth(system):
    ao.poll()
    assert system.default == DAC["name"]
    assert set(system.streams.values()) == {DAC["name"]}
    assert system.volumes == {DAC["id"]: 1.0}


def test_bluetooth_connected_is_left_alone(system):
    system.bt_sink(JBL, 50)
    system.default = system.sinks[-1]["name"]
    ao.poll()
    assert system.default.startswith("bluez_output.AA_BB_CC_DD_EE_01")
    assert not any(c[:2] == ["wpctl", "set-default"] for c in system.calls)


def test_bluetooth_disconnect_falls_back_to_jack(system):
    system.bt_sink(JBL, 50)
    assert ao.select(JBL) == (True, "")
    system.drop_bt(JBL)
    ao.poll()
    assert system.default == DAC["name"]
    assert set(system.streams.values()) == {DAC["name"]}


def test_choose_jack_while_bluetooth_connected(system):
    system.bt_sink(JBL, 50)
    ao.select(JBL)
    assert ao.select(ao.WIRED) == (True, "")
    assert system.default == DAC["name"]
    ao.poll()  # Bluetooth still connected: the choice stays
    assert system.default == DAC["name"]


def test_choose_paired_device_that_is_not_connected_connects_it(system):
    ok, _ = ao.select(SONY)
    assert ok
    assert ["bluetoothctl", "connect", SONY] in system.calls
    assert system.default.startswith("bluez_output.AA_BB_CC_DD_EE_02")
    assert set(system.streams.values()) == {system.default}


def test_outputs_lists_jack_and_paired_devices(system):
    system.bt_sink(JBL, 50)
    ao.select(JBL)
    st = ao.outputs()
    assert st["switchable"] and st["active"] == JBL
    assert [(o["id"], o["connected"], o["active"]) for o in st["outputs"]] == [
        (ao.WIRED, True, False), (JBL, True, True), (SONY, False, False)]
    assert ao.active_label() == "JBL Flip"


def test_plug_in_switches_to_jack_and_unplug_back_to_bluetooth(system, monkeypatch):
    monkeypatch.setenv("JACK_DETECT_GPIO", "16")
    system.bt_sink(JBL, 50)
    ao.select(JBL)
    _plug(monkeypatch, False)
    ao.poll()
    assert system.default.startswith("bluez_output.")
    _plug(monkeypatch, True)
    ao.poll()
    assert system.default == DAC["name"]
    _plug(monkeypatch, False)
    ao.poll()
    assert system.default.startswith("bluez_output.AA_BB_CC_DD_EE_01")


def test_unplug_reconnects_last_bluetooth_device(system, monkeypatch):
    system.bt_sink(SONY, 50)
    ao.select(SONY)
    system.drop_bt(SONY)
    _plug(monkeypatch, True)
    ao.poll()
    assert system.default == DAC["name"]
    _plug(monkeypatch, False)
    ao.poll()
    assert ["bluetoothctl", "connect", SONY] in system.calls
    assert system.default.startswith("bluez_output.AA_BB_CC_DD_EE_02")


def test_jack_detect_reads_pinctrl(monkeypatch):
    monkeypatch.setenv("JACK_DETECT_GPIO", "16")
    monkeypatch.delenv("JACK_PLUGGED_LEVEL", raising=False)
    calls = []

    class Done:
        def __init__(self, out):
            self.stdout = out

    def fake_run(args, **kw):
        calls.append(args)
        return Done("0\n")

    monkeypatch.setattr(ao.subprocess, "run", fake_run)
    assert ao.jack_plugged() is True
    assert calls == [["pinctrl", "lev", "16"]]
    monkeypatch.setenv("JACK_PLUGGED_LEVEL", "1")
    assert ao.jack_plugged() is False
    monkeypatch.setenv("JACK_DETECT_GPIO", "")
    assert ao.jack_plugged() is None


def test_alsa_backend_is_jack_only(system, monkeypatch):
    monkeypatch.setenv("AUDIO_BACKEND", "alsa")
    ao.poll()
    assert system.calls == []
    assert ao.outputs() == {"switchable": False, "active": ao.WIRED, "outputs": [
        {"id": ao.WIRED, "label": ao.WIRED_LABEL, "kind": ao.WIRED, "connected": True, "active": True}]}
    assert ao.select(ao.WIRED)[0] is False


def test_wired_audio_none_leaves_routing_to_bluetooth(system, monkeypatch):
    monkeypatch.setenv("WIRED_AUDIO", "none")
    ao.poll()
    assert system.default is None
    assert [o["id"] for o in ao.outputs()["outputs"]] == [JBL, SONY]
    assert ao.select(ao.WIRED)[0] is False


def test_wired_sink_ignores_hdmi_and_matches_card(system):
    hdmi = {"id": 41, "name": "alsa_output.platform-fef00700.hdmi.hdmi-stereo",
            "description": "Built-in Audio", "card": "vc4-hdmi", "bluetooth": False, "default": False}
    dac = dict(DAC, bluetooth=False, default=False)
    assert ao.wired_sink([hdmi, dac]) == dac
    assert ao.wired_sink([hdmi]) is None
    usb = {"id": 42, "name": "alsa_output.usb-Generic_USB_Audio-00.analog-stereo",
           "description": "USB Audio", "card": "USB Audio", "bluetooth": False, "default": False}
    assert ao.wired_sink([hdmi, usb]) == usb

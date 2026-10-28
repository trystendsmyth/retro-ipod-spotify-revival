"""Where sound goes: the headphone jack (I2S DAC) or a Bluetooth device.

Separate from audio_router, which picks the *source* (Spotify or Music on iPod).

AUDIO_BACKEND=pulseaudio (PipeWire): the DAC and Bluetooth devices are PipeWire sinks.
Choosing one makes it the default sink and moves go-librespot's and MPD's streams to
it. Rules, applied by poll() every few seconds from the UI:
  * no Bluetooth device connected -> the jack;
  * with jack detect (JACK_DETECT_GPIO): plugging in -> the jack, unplugging -> the
    last Bluetooth device.
Connecting a Bluetooth device (portal, or the reconnect at boot) still switches to it,
as before (bt_manager.connect).

AUDIO_BACKEND=alsa: the jack only, shared through dmix (/etc/asound.conf); nothing to
switch.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
from typing import Optional

import bt_manager

WIRED = "wired"
WIRED_LABEL = "Headphones"


def _env(name: str, default: str) -> str:
    # Read on use: the env files are loaded after this module is imported.
    return os.environ.get(name, default)


def pipewire() -> bool:
    return _env("AUDIO_BACKEND", "pulseaudio") == "pulseaudio"


def wired_enabled() -> bool:
    return _env("WIRED_AUDIO", "i2s") != "none"


def switchable() -> bool:
    """True when there is a choice to make (PipeWire; ALSA is the jack only)."""
    return pipewire()


def _state_file() -> str:
    data = _env("SPOTIFYPOD_DATA_DIR", os.path.expanduser("~/.local/share/spotifypod"))
    return os.path.join(data, "audio_output.json")


def _load() -> dict:
    try:
        with open(_state_file()) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: dict) -> None:
    path = _state_file()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(data, fh)
        os.replace(tmp, path)
    except OSError as exc:
        print("audio_output: saving choice:", exc)


# ------------------------------------------------------------------ sinks


def wired_sink(sinks: list[dict]) -> Optional[dict]:
    """The DAC's sink: an ALSA sink whose card matches WIRED_CARD, else the only
    non-HDMI ALSA sink."""
    if not wired_enabled():
        return None
    alsa = [s for s in sinks if s["name"].startswith("alsa_output.")]
    match = _env("WIRED_CARD", "rpi_dac").lower()
    for s in alsa:
        if match and (match in s.get("card", "").lower() or match in s["name"].lower()):
            return s
    others = [s for s in alsa if "hdmi" not in (s["name"] + s.get("card", "")).lower()]
    return others[0] if len(others) == 1 else None


def _use_sink(sink: dict) -> bool:
    if not bt_manager.set_default_sink(sink["id"]):
        return False
    bt_manager.move_streams(sink["name"])
    return True


_capped: set = set()


def _cap(sink: dict) -> None:
    """Jack sink at 100 %, once per sink (its id changes if it reappears). The earbud
    level cap is in the DAC (WIRED_GAIN_DB, tlv320.py); WirePlumber's default for a new
    sink would take another 24 dB off it."""
    if sink["id"] not in _capped and bt_manager.set_sink_volume(sink["id"], 1.0):
        _capped.add(sink["id"])


def _use_wired(sink: dict) -> bool:
    _cap(sink)
    return _use_sink(sink)


def _mac_of(sink: dict) -> str:
    # bluez_output.AA_BB_CC_DD_EE_FF.1 -> AA:BB:CC:DD:EE:FF
    parts = sink["name"].split(".")
    return parts[1].replace("_", ":").upper() if len(parts) > 1 else ""


# ------------------------------------------------------------------ state


def outputs() -> dict:
    """{"switchable", "active", "outputs": [{id, label, kind, connected, active}]}."""
    if not switchable():
        active = WIRED if wired_enabled() else ""
        outs = [{"id": WIRED, "label": WIRED_LABEL, "kind": WIRED,
                 "connected": True, "active": True}] if wired_enabled() else []
        return {"switchable": False, "active": active, "outputs": outs}
    sinks = bt_manager.audio_sinks()
    default = next((s for s in sinks if s["default"]), None)
    wired = wired_sink(sinks)
    outs = []
    if wired_enabled():
        outs.append({"id": WIRED, "label": WIRED_LABEL, "kind": WIRED,
                     "connected": wired is not None,
                     "active": wired is not None and default is not None and default["id"] == wired["id"]})
    for dev in bt_manager.devices():
        if not dev.paired:
            continue
        sink = bt_manager.sink_for_mac(dev.mac) if dev.connected else None
        outs.append({"id": dev.mac, "label": dev.label, "kind": "bluetooth",
                     "connected": sink is not None,
                     "active": sink is not None and default is not None and default["id"] == sink["id"]})
    active = next((o["id"] for o in outs if o["active"]), "")
    if not active and default is not None:
        active = default["name"]
    return {"switchable": True, "active": active, "outputs": outs}


def active_label() -> str:
    """For Settings -> About and the portal's status line."""
    try:
        st = outputs()
    except Exception as exc:  # never take About down over PipeWire
        print("audio_output:", exc)
        return "unknown"
    out = next((o for o in st["outputs"] if o["active"]), None)
    if out:
        return out["label"]
    return "none" if not st["active"] else st["active"]


# ------------------------------------------------------------------ choosing

_lock = threading.Lock()


def select(output_id: str) -> tuple[bool, str]:
    """Send sound to the jack ("wired") or a paired Bluetooth device (its MAC)."""
    if not switchable():
        return False, "Only the headphone jack is available (AUDIO_BACKEND=alsa)"
    with _lock:
        if output_id == WIRED:
            if not wired_enabled():
                return False, "Wired audio is not installed (WIRED_AUDIO=none)"
            sink = wired_sink(bt_manager.audio_sinks())
            if sink is None:
                return False, "Headphone jack not found. Check the DAC wiring and dtoverlay."
            ok = _use_wired(sink)
            if ok:
                _save({**_load(), "choice": WIRED})
            return ok, "" if ok else "Could not switch to the headphone jack"
        mac = output_id.upper()
        if not bt_manager.valid_mac(mac):
            return False, "Unknown output"
        sink = bt_manager.sink_for_mac(mac)
        if sink is None:
            # connect() makes the new sink the default and moves the streams
            ok, msg = bt_manager.connect(mac)
            if not ok or bt_manager.sink_for_mac(mac) is None:
                return False, msg or "Could not connect"
        elif not _use_sink(sink):
            return False, "Could not switch output"
        _save({**_load(), "choice": "bluetooth", "last_bluetooth": mac})
        return True, ""


# ------------------------------------------------------------------ jack detect and polling


def jack_plugged() -> Optional[bool]:
    """Plug state from JACK_DETECT_GPIO (pull-up set in config.txt), None without one."""
    gpio = _env("JACK_DETECT_GPIO", "")
    if not gpio.isdigit():
        return None
    try:
        out = subprocess.run(["pinctrl", "lev", gpio], capture_output=True, text=True,
                             timeout=2, check=False).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out not in ("0", "1"):
        return None
    return out == _env("JACK_PLUGGED_LEVEL", "0")


_last_plugged: Optional[bool] = None


def _sinks() -> tuple[Optional[dict], Optional[dict], list[dict]]:
    """(wired sink, default sink, Bluetooth sinks)."""
    sinks = bt_manager.audio_sinks()
    default = next((s for s in sinks if s["configured"]), None)
    return wired_sink(sinks), default, [s for s in sinks if s["bluetooth"]]


def poll() -> None:
    """Apply the jack-detect and default-to-jack rules once."""
    global _last_plugged
    if not switchable() or not wired_enabled():
        return
    plugged = jack_plugged()
    changed = None not in (plugged, _last_plugged) and plugged != _last_plugged
    _last_plugged = plugged
    wired, default, bluetooth = _sinks()
    if wired is not None:
        _cap(wired)

    if changed and plugged:
        if wired is not None:
            with _lock:
                _use_wired(wired)
        return
    if changed and not plugged:
        last = _load().get("last_bluetooth", "")
        sink = next((s for s in bluetooth if _mac_of(s) == last), None)
        if sink is not None:
            with _lock:
                _use_sink(sink)
            return
        # Not connected: reconnect it; connect() switches to it (can take ~25 s).
        if bt_manager.valid_mac(last) and bt_manager.connect(last)[0]:
            return
        wired, default, bluetooth = _sinks()

    if not bluetooth and wired is not None and (default is None or default["id"] != wired["id"]):
        with _lock:
            _use_wired(wired)


def run_forever(interval: float = 5.0, stop: Optional[threading.Event] = None) -> None:
    """UI background thread."""
    stop = stop or threading.Event()
    while not stop.wait(interval):
        try:
            poll()
        except Exception as exc:  # never take the UI down over audio routing
            print("audio_output poll:", exc)

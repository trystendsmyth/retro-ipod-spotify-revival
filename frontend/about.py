"""Settings -> About: software version, address, display, backend versions and audio output.

Versions come from /etc/spotifypod/install.env, which install/install.sh rewrites on
every run (the installed copy under /opt has no git checkout to ask).
"""
from __future__ import annotations

import os
import socket
import subprocess
from importlib import metadata

import audio_output

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=2, check=False).stdout.strip()
    except Exception:
        return ""


def version() -> str:
    if os.environ.get("SPOTIFYPOD_VERSION"):
        return os.environ["SPOTIFYPOD_VERSION"]
    # Running from a checkout (development, tools/ui_preview.py)
    return _run(["git", "-C", _REPO, "describe", "--tags", "--always", "--dirty"]) or "unknown"


def ip_address() -> str:
    addrs = _run(["hostname", "-I"]).split()
    if addrs:
        return addrs[0]
    try:
        # No packet is sent; this only asks the kernel which source address it would use.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))
            return s.getsockname()[0]
    except OSError:
        return "No network"


def display() -> str:
    profile = os.environ.get("DISPLAY_PROFILE", "unknown")
    if profile == "composite":
        return f"composite {os.environ.get('TV_NORM', '')}".strip()
    return profile


def _package(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def items() -> list[tuple[str, str]]:
    """(label, value) rows, in display order."""
    if os.environ.get("LOCAL_MUSIC", "1") == "0":
        mpd = "off"
    else:
        mpd = os.environ.get("MPD_VERSION") or "unknown"
    return [
        ("Version", version()),
        ("IP address", ip_address()),
        ("Display", display()),
        ("go-librespot", os.environ.get("GO_LIBRESPOT_VERSION") or "unknown"),
        ("MPD", mpd),
        ("Audio", os.environ.get("AUDIO_BACKEND") or "unknown"),
        ("Output", audio_output.active_label()),
        ("spotipy", _package("spotipy")),
    ]

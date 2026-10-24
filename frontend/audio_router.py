"""One audio source at a time: Spotify (go-librespot) or Music on iPod (MPD).

The UI calls use_spotify() / use_local() before it starts playback, which pauses the
other source. reconcile() runs on every now-playing poll and follows playback started
somewhere else, e.g. a phone taking over through Spotify Connect while MPD plays.
Now Playing, the transport buttons and wheel volume all go to the active source.
"""
from __future__ import annotations

import threading

import local_player
import player

SPOTIFY = "spotify"
LOCAL = "local"

_lock = threading.Lock()
_active = SPOTIFY
_was_playing = {SPOTIFY: False, LOCAL: False}


def active() -> str:
    return _active


def backend():
    """Module with the player.py surface for the active source."""
    return local_player if _active == LOCAL else player


def _pause(source: str) -> None:
    try:
        if source == LOCAL:
            if local_player.enabled():
                local_player.pause()
        else:
            player.pause()
    except player.PlayerError as exc:  # LocalPlayerError is a PlayerError
        print(f"audio_router: pausing {source}: {exc}")


def _set_active(source: str) -> None:
    global _active
    with _lock:
        _active = source


def use_spotify() -> None:
    _set_active(SPOTIFY)
    _pause(LOCAL)


def use_local() -> None:
    _set_active(LOCAL)
    _pause(SPOTIFY)


def reconcile(spotify_playing: bool, local_playing: bool) -> str:
    """Update the active source from the latest player states; returns it."""
    global _active
    with _lock:
        started = {
            SPOTIFY: spotify_playing and not _was_playing[SPOTIFY],
            LOCAL: local_playing and not _was_playing[LOCAL],
        }
        _was_playing[SPOTIFY] = spotify_playing
        _was_playing[LOCAL] = local_playing
        other = LOCAL if _active == SPOTIFY else SPOTIFY
        if started[other]:
            _active = other
        source = _active
        both = spotify_playing and local_playing
    if both:
        _pause(LOCAL if source == SPOTIFY else SPOTIFY)
    return source

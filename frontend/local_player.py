"""MPD client for music files on the SD card ("Music on iPod"), via python-mpd2.

Same playback surface as player.py (go-librespot) plus library queries. MPD drops idle
clients, so every call reuses one connection and reconnects once if it was lost.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Optional

import mpd

import player

HOST = os.environ.get("MPD_HOST", "127.0.0.1")
PORT = int(os.environ.get("MPD_PORT", "6600"))
TIMEOUT = float(os.environ.get("MPD_TIMEOUT", "3"))
VOLUME_STEPS = 100
# How long library_ready() trusts its last answer before asking MPD again
LIBRARY_CHECK_SECONDS = 15.0

# Tests swap this for a fake.
client_factory: Callable[[], Any] = mpd.MPDClient


class LocalPlayerError(player.PlayerError):
    pass


def enabled() -> bool:
    """False when the installer ran with LOCAL_MUSIC=0."""
    return os.environ.get("LOCAL_MUSIC", "1") != "0"


_lock = threading.Lock()
_client = None


def _drop() -> None:
    global _client
    if _client is not None:
        try:
            _client.disconnect()
        except Exception:
            pass
    _client = None


def _call(fn: Callable[[Any], Any]) -> Any:
    """Run fn(client) on a live connection; reconnect once if MPD dropped us."""
    global _client
    with _lock:
        for attempt in (0, 1):
            try:
                if _client is None:
                    client = client_factory()
                    client.timeout = TIMEOUT
                    client.connect(HOST, PORT)
                    _client = client
                return fn(_client)
            except mpd.CommandError as exc:
                raise LocalPlayerError(str(exc)) from exc
            except (mpd.ConnectionError, OSError) as exc:
                _drop()
                if attempt:
                    raise LocalPlayerError(f"MPD {HOST}:{PORT}: {exc}") from exc


# ------------------------------------------------------------------ playback


def status() -> Optional[dict]:
    """MPD status plus the current song under "song_info", or None if MPD is unreachable."""
    if not enabled():
        return None
    try:
        st, song = _call(lambda c: (c.status(), c.currentsong()))
    except LocalPlayerError:
        return None
    st["song_info"] = song or {}
    return st


def is_playing(st: Optional[dict]) -> bool:
    return bool(st) and st.get("state") == "play"


def play(uris: list[str], start: int = 0) -> None:
    """Replace the queue with `uris` (paths relative to the music folder), play uris[start]."""
    if not uris:
        return

    def run(c):
        c.clear()
        c.command_list_ok_begin()
        for uri in uris:
            c.add(uri)
        c.command_list_end()
        c.play(max(0, min(start, len(uris) - 1)))

    _call(run)


def pause() -> None:
    _call(lambda c: c.pause(1))


def resume() -> None:
    def run(c):
        if c.status().get("state") == "stop":
            c.play()
        else:
            c.pause(0)

    _call(run)


def playpause() -> None:
    def run(c):
        state = c.status().get("state")
        if state == "play":
            c.pause(1)
        elif state == "pause":
            c.pause(0)
        else:
            c.play()

    _call(run)


def next_track() -> None:
    _call(lambda c: c.next())


def previous_track() -> None:
    _call(lambda c: c.previous())


def stop() -> None:
    _call(lambda c: c.stop())


def get_volume() -> Optional[dict]:
    """{"value": current, "max": 100} like player.get_volume(), or None."""
    try:
        vol = int(_call(lambda c: c.status()).get("volume", -1))
    except (LocalPlayerError, ValueError):
        return None
    if vol < 0:  # no mixer / output not open yet
        return None
    return {"value": vol, "max": VOLUME_STEPS}


def volume(value: int, relative: bool = False) -> None:
    if relative:
        current = get_volume()
        value = (current["value"] if current else VOLUME_STEPS // 2) + value
    _call(lambda c: c.setvol(max(0, min(VOLUME_STEPS, int(value)))))


def to_now_playing(st: Optional[dict]) -> Optional[dict]:
    """Same dict shape as spotify_manager's now_playing, for the Now Playing screen."""
    if not st:
        return None
    song = st.get("song_info") or {}
    if not song.get("file") or st.get("state") == "stop":
        return None
    vol = int(st.get("volume", -1))
    return {
        "name": title_of(song),
        "track_uri": song["file"],
        "artist": _first(song.get("artist")) or "",
        "album": _first(song.get("album")) or "",
        "duration": int(float(st.get("duration") or song.get("duration") or 0) * 1000),
        "is_playing": st.get("state") == "play",
        "progress": int(float(st.get("elapsed") or 0) * 1000),
        "context_name": _first(song.get("album")) or "Music on iPod",
        "track_index": int(st["song"]) + 1 if "song" in st else -1,
        "track_total": int(st.get("playlistlength") or 0),
        "timestamp": time.time(),
        "volume": vol if vol >= 0 else None,
        "volume_steps": VOLUME_STEPS,
        "volume_until": 0.0,
        "source": "local",
    }


# ------------------------------------------------------------------ library


def update_db() -> None:
    """Rescan the music folder (Settings -> Update Music Library)."""
    global _library_checked_at
    _call(lambda c: c.update())
    _library_checked_at = 0.0


def updating() -> bool:
    try:
        return "updating_db" in _call(lambda c: c.status())
    except LocalPlayerError:
        return False


def song_count() -> int:
    return int(_call(lambda c: c.stats()).get("songs", 0))


_library_ready = False
_library_checked_at = 0.0


def library_ready() -> bool:
    """MPD is reachable and has at least one song. Cached; cheap enough for every render."""
    global _library_ready, _library_checked_at
    if not enabled():
        return False
    now = time.time()
    if now - _library_checked_at > LIBRARY_CHECK_SECONDS:
        _library_checked_at = now
        try:
            _library_ready = song_count() > 0
        except LocalPlayerError:
            _library_ready = False
    return _library_ready


def _first(value):
    # MPD repeats a tag that has several values; python-mpd2 then returns a list.
    return value[0] if isinstance(value, list) else value


def _values(rows: list[dict], tag: str) -> list[str]:
    names = {_first(r.get(tag)) for r in rows}
    return sorted((n for n in names if n), key=str.casefold)


def _number(value) -> int:
    try:
        return int(str(_first(value) or "0").split("/")[0])
    except ValueError:
        return 0


def title_of(song: dict) -> str:
    title = _first(song.get("title"))
    if title:
        return title
    return os.path.splitext(os.path.basename(song.get("file", "")))[0] or "Unknown"


def artists() -> list[str]:
    return _values(_call(lambda c: c.list("artist")), "artist")


def albums(artist: Optional[str] = None) -> list[str]:
    if artist is None:
        return _values(_call(lambda c: c.list("album")), "album")
    return _values(_call(lambda c: c.list("album", "artist", artist)), "album")


def tracks(album: str, artist: Optional[str] = None) -> list[dict]:
    """Songs of an album in disc/track order."""
    query = ["album", album] + (["artist", artist] if artist else [])
    rows = _call(lambda c: c.find(*query))
    return sorted(rows, key=lambda s: (_number(s.get("disc")), _number(s.get("track")), s["file"]))


def songs() -> list[dict]:
    """Every song, by title."""
    rows = [r for r in _call(lambda c: c.listallinfo()) if "file" in r]
    return sorted(rows, key=lambda s: title_of(s).casefold())


def playlists() -> list[str]:
    """.m3u files at the top of the music folder (MPD's playlist_directory)."""
    rows = _call(lambda c: c.listplaylists())
    return sorted((r["playlist"] for r in rows if r.get("playlist")), key=str.casefold)


def playlist_tracks(name: str) -> list[dict]:
    """Entries MPD found in its database; a missing file would make the whole add fail."""
    return [r for r in _call(lambda c: c.listplaylistinfo(name))
            if r.get("file") and "last-modified" in r]

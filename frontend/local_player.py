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


# Read on use, not at import: outside systemd, view_model imports this module before
# spotify_manager has loaded /etc/spotifypod/*.env.
def _address() -> tuple[str, int]:
    return os.environ.get("MPD_HOST", "127.0.0.1"), int(os.environ.get("MPD_PORT", "6600"))


def _timeout(library: bool = False) -> float:
    # Socket timeout per read. Library listings get longer: on a single-core Zero W MPD
    # may take a while to start answering for a large library.
    if library:
        return float(os.environ.get("MPD_LIBRARY_TIMEOUT", "15"))
    return float(os.environ.get("MPD_TIMEOUT", "3"))


# Selecting a song queues at most this many songs around it, not a whole library.
QUEUE_WINDOW = 200

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


def _call(fn: Callable[[Any], Any], library: bool = False) -> Any:
    """Run fn(client) on a live connection; reconnect once if MPD dropped us.

    library=True uses the longer library timeout for this call only.
    """
    global _client
    with _lock:
        for attempt in (0, 1):
            try:
                if _client is None:
                    client = client_factory()
                    client.timeout = _timeout()
                    client.connect(*_address())
                    _client = client
                if not library:
                    return fn(_client)
                _client.timeout = _timeout(library=True)
                try:
                    return fn(_client)
                finally:
                    try:
                        _client.timeout = _timeout()
                    except Exception:  # connection already gone; the error above is the one to report
                        pass
            except mpd.CommandError as exc:
                raise LocalPlayerError(str(exc)) from exc
            except (mpd.ConnectionError, OSError) as exc:
                _drop()
                if attempt:
                    host, port = _address()
                    raise LocalPlayerError(f"MPD {host}:{port}: {exc}") from exc


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


def queue_window(count: int, start: int, size: int = QUEUE_WINDOW) -> tuple[int, int]:
    """[lo, hi) slice of at most `size` songs around `start`, shifted to stay in range."""
    lo = max(0, min(start - size // 2, count - size))
    return lo, min(count, lo + size)


def play(uris: list[str], start: int = 0) -> None:
    """Replace the queue with `uris` (paths relative to the music folder), play uris[start].

    Long lists (the whole Songs menu) are cut to QUEUE_WINDOW songs around `start`.
    """
    if not uris:
        return
    start = max(0, min(start, len(uris) - 1))
    lo, hi = queue_window(len(uris), start)
    window = uris[lo:hi]

    def run(c):
        c.clear()
        c.command_list_ok_begin()
        for uri in window:
            c.add(uri)
        c.command_list_end()
        c.play(start - lo)

    _call(run, library=True)


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
    """Rescan the music folder (Settings -> Update Music)."""
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


# Menus group by album artist, so a compilation stays one album and two albums with the
# same name stay apart. MPD itself falls back to the artist tag when a file has no album
# artist, for both `list` and `find`.
def artists() -> list[str]:
    return _values(_call(lambda c: c.list("albumartist"), library=True), "albumartist")


def albums(artist: Optional[str] = None) -> list[tuple[str, str]]:
    """(album, album artist) pairs, by album name."""
    if artist is None:
        rows = _call(lambda c: c.list("album", "group", "albumartist"), library=True)
    else:
        rows = [dict(r, albumartist=artist)
                for r in _call(lambda c: c.list("album", "albumartist", artist), library=True)]
    pairs = {(_first(r.get("album")), _first(r.get("albumartist")) or "") for r in rows}
    return sorted((p for p in pairs if p[0]), key=lambda p: (p[0].casefold(), p[1].casefold()))


def tracks(album: str, artist: Optional[str] = None) -> list[dict]:
    """Songs of an album (by album artist when given) in disc/track order."""
    query = ["album", album] + (["albumartist", artist] if artist else [])
    rows = _call(lambda c: c.find(*query), library=True)
    return sorted(rows, key=lambda s: (_number(s.get("disc")), _number(s.get("track")), s["file"]))


def songs() -> list[dict]:
    """Every song, by title."""
    rows = [r for r in _call(lambda c: c.listallinfo(), library=True) if "file" in r]
    return sorted(rows, key=lambda s: title_of(s).casefold())


def playlists() -> list[str]:
    """.m3u files at the top of the music folder (MPD's playlist_directory)."""
    rows = _call(lambda c: c.listplaylists(), library=True)
    return sorted((r["playlist"] for r in rows if r.get("playlist")), key=str.casefold)


def playlist_tracks(name: str) -> list[dict]:
    """Entries MPD found in its database; a missing file would make the whole add fail."""
    return [r for r in _call(lambda c: c.listplaylistinfo(name), library=True)
            if r.get("file") and "last-modified" in r]

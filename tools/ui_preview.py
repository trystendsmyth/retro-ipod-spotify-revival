#!/usr/bin/env python3
"""Run the real retro-ipod-spotify-revival UI with fake Spotify data - no Pi, no account needed.

Useful for:
  * checking the UI on a laptop (arrow keys = scroll / select / back), and
  * generating the screenshots in docs/images (run under Xvfb with --tour).

Nothing here talks to Spotify or go-librespot: player / Web API calls are replaced
with in-memory fakes before the UI is started.

  python3 tools/ui_preview.py                       # interactive window
  xvfb-run -s "-screen 0 720x480x24" \\
    python3 tools/ui_preview.py --tour docs/images/ui   # scripted screenshots

--tour drives the UI through the same UDP input path the click wheel uses
(127.0.0.1:9090, 3-byte packets {button, state, wheel_position}) and saves a PNG
of the X screen after each step (needs ImageMagick's `import`).
"""
from __future__ import annotations

import argparse
import os
import runpy
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, "frontend")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tour", metavar="OUT_DIR", help="drive the UI and save screenshots to OUT_DIR")
    args = ap.parse_args()

    # Private, throwaway data dir so nothing touches a real cache.
    os.environ["SPOTIFYPOD_DATA_DIR"] = tempfile.mkdtemp(prefix="spot-preview-")
    os.environ.setdefault("SCREEN_TIMEOUT_SECONDS", "0")
    os.environ.pop("SPOTIPY_CLIENT_ID", None)
    sys.path.insert(0, FRONTEND)
    os.chdir(FRONTEND)

    import player  # noqa: E402

    start = time.time()

    def fake_status():
        pos = int((time.time() - start) * 1000) + 83_000
        return {
            "paused": False,
            "volume": 60,
            "volume_steps": 100,
            "context_uri": "spotify:album:demo1",
            "track": {
                "uri": "spotify:track:demo1-3",
                "name": "Clickwheel Serenade",
                "artist_names": ["The Demo Tapes"],
                "album_name": "Songs for a 4th-Gen iPod",
                "duration": 214_000,
                "position": pos % 214_000,
            },
        }

    player.status = fake_status
    player.logged_in = lambda: True
    for name in ("play", "play_uris", "next_track", "previous_track", "pause", "resume",
                 "playpause", "stop", "volume"):
        setattr(player, name, lambda *a, **k: None)
    player.get_volume = lambda: {"value": 60, "max": 100}

    # Music on iPod: a small fake MPD library (no MPD needed)
    import local_player  # noqa: E402

    local_songs = []
    for artist, album, titles in [
        ("Analog Hearts", "Line Out", ["Dock Connector", "Line Out", "Firewire"]),
        ("Hold Switch", "Monochrome", ["Grey", "Black", "White", "Backlight"]),
        ("Video Out", "Composite Dreams", ["NTSC", "PAL", "Overscan"]),
    ]:
        for n, title in enumerate(titles, 1):
            local_songs.append({"file": f"{artist}/{album}/{n:02} {title}.mp3", "title": title,
                                "artist": artist, "album": album, "track": str(n)})
    local_player.enabled = lambda: True
    local_player.status = lambda: None
    local_player.library_ready = lambda: True
    local_player.artists = lambda: sorted({s["artist"] for s in local_songs})
    local_player.albums = lambda artist=None: sorted({s["album"] for s in local_songs
                                                     if artist in (None, s["artist"])})
    local_player.tracks = lambda album, artist=None: [s for s in local_songs if s["album"] == album]
    local_player.songs = lambda: sorted(local_songs, key=lambda s: s["title"])
    local_player.playlists = lambda: ["Road Trip 2004"]
    local_player.playlist_tracks = lambda name: local_songs[::2]
    for name in ("play", "pause", "resume", "playpause", "next_track", "previous_track",
                 "stop", "volume", "update_db"):
        setattr(local_player, name, lambda *a, **k: None)
    local_player.updating = lambda: False
    local_player.song_count = lambda: len(local_songs)

    import spotify_manager as sm  # noqa: E402
    import bt_manager  # noqa: E402
    import setup_state  # noqa: E402

    sm.has_token = lambda: True
    sm.init_spotify = lambda force=False: None
    sm.refresh_data = lambda full=True: None
    bt_manager.auto_connect = lambda *a, **k: None
    setup_state.wifi_online = lambda: True

    ds = sm.DATASTORE
    artists = ["Analog Hearts", "Click & The Wheels", "Firewire Kids", "Hold Switch",
               "The Demo Tapes", "Thirty Pin", "Video Out"]
    for i, a in enumerate(artists):
        ds.setArtist(i, sm.UserArtist(a, f"spotify:artist:demo{i}"))
    albums = [("Songs for a 4th-Gen iPod", "The Demo Tapes"), ("Monochrome", "Hold Switch"),
              ("Composite Dreams", "Video Out"), ("Haptic", "Click & The Wheels")]
    for i, (name, artist) in enumerate(albums):
        uri = f"spotify:album:demo{i + 1}"
        tracks = [sm.UserTrack(t, artist, name, f"spotify:track:demo{i + 1}-{j + 1}")
                  for j, t in enumerate(["Menu", "Select", "Clickwheel Serenade", "Back", "Play/Pause"])]
        ds.setAlbum(sm.UserAlbum(name, artist, len(tracks), uri), tracks, index=i)
    playlists = ["Morning Commute", "Road Trip 2004", "Focus", "Kids' Car Songs", "Discover Weekly"]
    for i, name in enumerate(playlists):
        uri = f"spotify:playlist:demo{i}"
        tracks = [sm.UserTrack(f"Track {j + 1}", "Various", "Mix", f"spotify:track:p{i}-{j}") for j in range(12)]
        ds.setPlaylist(sm.UserPlaylist(name, i, uri, len(tracks)), tracks, index=i)
    for i in range(6):
        ds.setRecentlyPlayed(sm.UserTrack(f"Recent song {i + 1}", artists[i % len(artists)], "Single",
                                          f"spotify:track:r{i}"), index=i)

    if args.tour:
        threading.Thread(target=_tour, args=(os.path.abspath(args.tour),), daemon=True).start()

    runpy.run_path(os.path.join(FRONTEND, "spotifypod.py"), run_name="__main__")


# ------------------------------------------------------------------ scripted tour
CENTER, FORWARD, BACK, PLAY, MENU, TOUCH = 7, 8, 9, 10, 11, 29


def _send(sock, button, state, pos):
    sock.sendto(bytes([button & 0xFF, state & 0xFF, pos & 0xFF]), ("127.0.0.1", 9090))
    time.sleep(0.05)


def _press(sock, button):
    _send(sock, button, 1, 0)
    _send(sock, button, 0, 0)
    time.sleep(0.6)


def _scroll(sock, steps, direction):
    pos = 10 if direction > 0 else 40
    _send(sock, TOUCH, 0, pos)          # clear the reference a button press may have left
    _send(sock, TOUCH, 1, pos)          # finger lands: sets the reference position
    for _ in range(steps):
        pos += 2 * direction              # clockwise = next item, as on a real iPod
        _send(sock, TOUCH, 1, pos)
    _send(sock, TOUCH, 0, pos)          # finger lifted
    time.sleep(0.6)


def _scroll_down(sock, steps):
    _scroll(sock, steps, +1)


def _scroll_up(sock, steps):
    _scroll(sock, steps, -1)


def _shot(out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.png")
    subprocess.run(["import", "-window", "root", path], check=True)
    print(f"tour: saved {path}", flush=True)


def _tour(out_dir):
    time.sleep(4.0)  # let the UI build and leave the setup screen
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    _shot(out_dir, "01-main-menu")
    _scroll_down(s, 3)                    # Artists -> Albums -> Recently Played -> Playlists
    _shot(out_dir, "02-menu-scrolled")
    _press(s, CENTER)
    _shot(out_dir, "03-playlists")
    _press(s, MENU)
    _scroll_down(s, 8)                    # past the end clamps to the last item
    _press(s, CENTER)                     # Now Playing (last item when something is playing)
    time.sleep(1.5)
    _shot(out_dir, "04-now-playing")
    _press(s, MENU)
    _scroll_up(s, 3)                      # Now Playing -> Settings -> Search -> Music on iPod
    _press(s, CENTER)
    _shot(out_dir, "05-music-on-ipod")
    os._exit(0)


if __name__ == "__main__":
    main()

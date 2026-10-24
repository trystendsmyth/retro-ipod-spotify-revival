"""local_player.py against a real MPD, configured from install/config/mpd.conf.template.

Skipped unless `mpd` is installed (CI installs it). Uses a null audio output.
"""
import os
import shutil
import socket
import subprocess
import time

import pytest

import local_player as lp
from mp3_fixture import write_mp3

ROOT = os.path.join(os.path.dirname(__file__), "..")
pytestmark = pytest.mark.skipif(not shutil.which("mpd"), reason="mpd not installed")


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait(cond, timeout=10.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.1)
    return False


@pytest.fixture(scope="module")
def mpd_server(tmp_path_factory):
    d = tmp_path_factory.mktemp("mpd")
    music = d / "music"
    album = music / "Hold Switch" / "Monochrome"
    album.mkdir(parents=True)
    for i, title in enumerate(["Grey", "Black", "White"]):
        write_mp3(album / f"0{i + 1} {title}.mp3", title=title, artist="Hold Switch",
                  album="Monochrome", track=f"{i + 1}/3", frames=400)
    write_mp3(music / "loose.mp3")
    (music / "Mix.m3u").write_text("#EXTM3U\nHold Switch/Monochrome/03 White.mp3\nmissing.mp3\nloose.mp3\n")

    port = _free_port()
    with open(os.path.join(ROOT, "install", "config", "mpd.conf.template")) as fh:
        conf = (fh.read().replace("__MUSIC_DIR__", str(music)).replace("__MPD_DIR__", str(d))
                .replace("__MPD_PORT__", str(port)))
    conf += 'audio_output {\n    type "null"\n    name "test"\n    mixer_type "software"\n}\n'
    (d / "mpd.conf").write_text(conf)
    proc = subprocess.Popen(["mpd", "--no-daemon", "--stderr", str(d / "mpd.conf")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def up():
        with socket.socket() as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    assert _wait(up), "mpd did not start"
    old = lp.PORT, lp.client_factory
    lp.PORT, lp._client = port, None
    yield proc
    lp._drop()
    lp.PORT, lp.client_factory = old
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture
def library(mpd_server, monkeypatch):
    monkeypatch.delenv("LOCAL_MUSIC", raising=False)
    lp.update_db()
    assert _wait(lambda: not lp.updating() and lp.song_count() == 4)


def test_files_appear_after_update(library):
    assert lp.library_ready()
    assert lp.artists() == ["Hold Switch"]
    assert lp.albums("Hold Switch") == ["Monochrome"]
    assert [lp.title_of(s) for s in lp.tracks("Monochrome")] == ["Grey", "Black", "White"]
    assert [lp.title_of(s) for s in lp.songs()] == ["Black", "Grey", "loose", "White"]


def test_playlist_in_music_folder_skips_missing_files(library):
    assert lp.playlists() == ["Mix"]
    assert [s["file"] for s in lp.playlist_tracks("Mix")] == ["Hold Switch/Monochrome/03 White.mp3", "loose.mp3"]


def test_album_playback_and_transport(library):
    lp.play([s["file"] for s in lp.tracks("Monochrome")], start=1)
    np = lp.to_now_playing(lp.status())
    assert (np["name"], np["track_index"], np["track_total"], np["is_playing"]) == ("Black", 2, 3, True)
    lp.pause()
    assert lp.status()["state"] == "pause"
    lp.playpause()
    assert lp.status()["state"] == "play"
    lp.next_track()
    assert lp.to_now_playing(lp.status())["name"] == "White"
    lp.volume(35)
    assert lp.get_volume() == {"value": 35, "max": 100}
    lp.stop()

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
    # A compilation (one album artist, several artists) and two albums with the same name
    (music / "Now").mkdir()
    write_mp3(music / "Now" / "1.mp3", title="One", artist="Alice", album="Now 2004",
              albumartist="Various Artists", track="1")
    write_mp3(music / "Now" / "2.mp3", title="Two", artist="Bob", album="Now 2004",
              albumartist="Various Artists", track="2")
    (music / "Hits").mkdir()
    write_mp3(music / "Hits" / "a.mp3", title="Hit A", artist="Alice", album="Greatest Hits")
    write_mp3(music / "Hits" / "c.mp3", title="Hit C", artist="Carol", album="Greatest Hits")
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
    yield port
    lp._drop()
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture
def library(mpd_server, monkeypatch):
    monkeypatch.delenv("LOCAL_MUSIC", raising=False)
    monkeypatch.setenv("MPD_PORT", str(mpd_server))  # read on use, like on the Pi
    lp._drop()
    lp.update_db()
    assert _wait(lambda: not lp.updating() and lp.song_count() == 8)


def test_files_appear_after_update(library):
    assert lp.library_ready()
    assert lp.albums("Hold Switch") == [("Monochrome", "Hold Switch")]
    assert [lp.title_of(s) for s in lp.tracks("Monochrome")] == ["Grey", "Black", "White"]
    assert [lp.title_of(s) for s in lp.songs()][:4] == ["Black", "Grey", "Hit A", "Hit C"]


def test_grouped_by_album_artist(library):
    # Compilation stays one album under its album artist; untagged files fall back to artist
    assert lp.artists() == ["Alice", "Carol", "Hold Switch", "Various Artists"]
    assert [lp.title_of(s) for s in lp.tracks("Now 2004", "Various Artists")] == ["One", "Two"]
    # Two "Greatest Hits" stay separate
    assert [a for a in lp.albums() if a[0] == "Greatest Hits"] == [
        ("Greatest Hits", "Alice"), ("Greatest Hits", "Carol")]
    assert [lp.title_of(s) for s in lp.tracks("Greatest Hits", "Carol")] == ["Hit C"]
    assert lp.albums("Alice") == [("Greatest Hits", "Alice")]


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

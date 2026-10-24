"""One active source: starting either pauses the other; Connect takeover pauses MPD."""
import pytest

import audio_router as ar
import local_player
import player
import spotify_manager as sm


@pytest.fixture
def paused(monkeypatch):
    calls = []
    monkeypatch.setattr(player, "pause", lambda: calls.append("spotify"))
    monkeypatch.setattr(local_player, "pause", lambda: calls.append("local"))
    monkeypatch.delenv("LOCAL_MUSIC", raising=False)
    monkeypatch.setattr(ar, "_active", ar.SPOTIFY)
    monkeypatch.setattr(ar, "_was_playing", {ar.SPOTIFY: False, ar.LOCAL: False})
    return calls


def test_starting_local_pauses_spotify(paused):
    ar.use_local()
    assert paused == ["spotify"]
    assert ar.backend() is local_player


def test_starting_spotify_pauses_local(paused):
    ar.use_local()
    ar.use_spotify()
    assert paused == ["spotify", "local"]
    assert ar.backend() is player


def test_connect_takeover_pauses_mpd(paused):
    ar.use_local()
    assert ar.reconcile(spotify_playing=False, local_playing=True) == ar.LOCAL
    # The phone picks "iPod" in Spotify and presses play
    assert ar.reconcile(spotify_playing=True, local_playing=True) == ar.SPOTIFY
    assert paused == ["spotify", "local"]
    assert ar.reconcile(spotify_playing=True, local_playing=False) == ar.SPOTIFY


def test_mpd_started_elsewhere_pauses_spotify(paused):
    ar.reconcile(spotify_playing=True, local_playing=False)
    assert ar.reconcile(spotify_playing=True, local_playing=True) == ar.LOCAL
    assert paused == ["spotify"]


def test_paused_sources_do_not_switch(paused):
    ar.use_local()
    for _ in range(3):
        assert ar.reconcile(spotify_playing=False, local_playing=False) == ar.LOCAL
    assert paused == ["spotify"]


def test_disabled_local_music_is_never_paused(paused, monkeypatch):
    monkeypatch.setenv("LOCAL_MUSIC", "0")
    ar.use_spotify()
    assert paused == []


def test_now_playing_and_transport_follow_active_source(paused, monkeypatch):
    spotify = {"paused": True, "track": {"uri": "spotify:track:1", "name": "Streamed",
                                         "artist_names": ["A"], "album_name": "B", "duration": 1000}}
    local = {"state": "play", "volume": "40", "song": "0", "playlistlength": "2", "elapsed": "1.0",
             "duration": "3.0", "song_info": {"file": "a/b.mp3", "title": "From SD", "album": "Disk"}}
    monkeypatch.setattr(player, "status", lambda: spotify)
    monkeypatch.setattr(local_player, "status", lambda: local)
    nexts = []
    monkeypatch.setattr(player, "next_track", lambda: nexts.append("spotify"))
    monkeypatch.setattr(local_player, "next_track", lambda: nexts.append("local"))

    ar.use_local()
    assert sm.get_now_playing()["name"] == "From SD"
    sm.play_next()
    assert nexts == ["local"]

    spotify["paused"] = False          # Connect takeover
    assert sm.get_now_playing()["name"] == "Streamed"
    sm.play_next()
    assert nexts == ["local", "spotify"]

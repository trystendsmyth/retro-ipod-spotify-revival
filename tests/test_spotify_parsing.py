"""Checks the Web API parsing against Spotify's February 2026 Development Mode shapes.

Reference: https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide
  * playlist items: `tracks` -> `items`, `items[].track` -> `items[].item`
  * GET /playlists/{id}/items returns 403 for playlists you don't own/collaborate on
"""
import os
import sys
import tempfile

import pytest

os.environ["SPOTIFYPOD_DATA_DIR"] = tempfile.mkdtemp(prefix="spot-test-")
os.environ.pop("SPOTIPY_CLIENT_ID", None)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend"))

import spotipy  # noqa: E402
import spotify_manager as sm  # noqa: E402


def _track(n):
    return {"type": "track", "name": f"Song {n}", "uri": f"spotify:track:{n}",
            "artists": [{"name": "Artist"}], "album": {"name": "Album"}, "is_local": False}


class FakeClient:
    def __init__(self, pages=None, status=None):
        self.pages = pages or []
        self.status = status

    def playlist_items(self, playlist_id, limit=50):
        if self.status:
            raise spotipy.SpotifyException(self.status, -1, "forbidden")
        return self.pages[0]

    def next(self, results):
        return self.pages[results["_page"] + 1]


@pytest.fixture
def client(monkeypatch):
    holder = {}
    monkeypatch.setattr(sm, "_client", lambda: holder["c"])
    return holder


def test_new_item_field(client):
    client["c"] = FakeClient(pages=[{"_page": 0, "items": [{"item": _track(1)}, {"item": _track(2)}], "next": None}])
    tracks = sm.get_playlist_tracks("abc")
    assert [t.title for t in tracks] == ["Song 1", "Song 2"]


def test_legacy_track_field_still_accepted(client):
    client["c"] = FakeClient(pages=[{"_page": 0, "items": [{"track": _track(3)}], "next": None}])
    assert [t.uri for t in sm.get_playlist_tracks("abc")] == ["spotify:track:3"]


def test_paging(client):
    client["c"] = FakeClient(pages=[
        {"_page": 0, "items": [{"item": _track(1)}], "next": "x"},
        {"_page": 1, "items": [{"item": _track(2)}], "next": None},
    ])
    assert len(sm.get_playlist_tracks("abc")) == 2


def test_not_owned_playlist_is_play_only(client):
    client["c"] = FakeClient(status=403)
    assert sm.get_playlist_tracks("abc") == []


def test_local_files_and_episodes_skipped(client):
    local = dict(_track(9), is_local=True)
    ep = {"type": "episode", "name": "Ep", "uri": "spotify:episode:1"}
    client["c"] = FakeClient(pages=[{"_page": 0, "items": [{"item": local}, {"item": ep}, {"item": None}], "next": None}])
    assert sm.get_playlist_tracks("abc") == []

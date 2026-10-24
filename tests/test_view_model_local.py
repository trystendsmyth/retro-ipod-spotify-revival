"""Music on iPod menus: visibility, queueing an album from the selected song, About rows."""
import pytest

import local_player
import spotify_manager as sm
import view_model as vm

SONGS = [{"file": f"A/Album/0{n} S{n}.mp3", "title": f"S{n}", "album": "Album", "artist": "A"}
         for n in (1, 2, 3)]


@pytest.fixture
def library(monkeypatch):
    monkeypatch.delenv("LOCAL_MUSIC", raising=False)
    monkeypatch.setattr(local_player, "library_ready", lambda: True)
    monkeypatch.setattr(local_player, "artists", lambda: ["A"])
    monkeypatch.setattr(local_player, "albums", lambda artist=None: ["Album"])
    monkeypatch.setattr(local_player, "tracks", lambda album, artist=None: SONGS)
    played = []
    monkeypatch.setattr(sm, "play_local", lambda uris, start=0: played.append((uris, start)))
    monkeypatch.setattr(sm, "run_async", lambda fn: fn())
    monkeypatch.setattr(sm.DATASTORE, "now_playing", None)
    return played


def _titles(page):
    return [page.page_at(i).header for i in range(page.total_size())]


def test_music_on_ipod_shown_only_with_a_library(library, monkeypatch):
    root = vm.RootPage(None)
    assert "Music on iPod" in _titles(root)
    monkeypatch.setattr(local_player, "library_ready", lambda: False)
    assert "Music on iPod" not in _titles(root)


def test_local_music_off_hides_menu_and_update_setting(monkeypatch):
    # The real library_ready(): with LOCAL_MUSIC=0 it never asks MPD
    monkeypatch.setenv("LOCAL_MUSIC", "0")
    monkeypatch.setattr(sm.DATASTORE, "now_playing", None)
    root = vm.RootPage(None)
    assert "Music on iPod" not in _titles(root)
    settings = next(p for p in root.pages if p.header == "Settings")
    assert "Update Music" not in _titles(settings)


def test_selecting_a_song_queues_the_album_from_there(library):
    artists = vm.RootPage(None).local_music.page_at(0)
    album = artists.page_at(0).page_at(0)
    assert _titles(album) == ["S1", "S2", "S3"]
    album.index = 1
    album.nav_select().render()
    assert library == [([s["file"] for s in SONGS], 1)]


def test_about_rows_alternate_label_and_value(library, monkeypatch):
    monkeypatch.setattr(vm.about, "items", lambda: [("Version", "abc1234"), ("IP address", "10.0.0.2")])
    about = vm.AboutPage(None)
    rows = about.render().lines
    assert [(r.title, r.line_type) for r in rows[:4]] == [
        ("Version", vm.LINE_TITLE), ("abc1234", vm.LINE_HIGHLIGHT),
        ("IP address", vm.LINE_TITLE), ("10.0.0.2", vm.LINE_NORMAL)]
    about.nav_up()
    assert about.index == 3

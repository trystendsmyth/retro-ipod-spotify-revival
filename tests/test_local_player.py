"""local_player.py against a fake MPD client (shapes as returned by python-mpd2 3.1 / MPD 0.23)."""
import mpd
import pytest

import local_player as lp
import player


def _song(file, title=None, artist=None, album=None, track=None, disc=None):
    s = {"file": file, "last-modified": "2026-10-01T00:00:00Z", "duration": "200.5", "time": "200"}
    for k, v in (("title", title), ("artist", artist), ("album", album), ("track", track), ("disc", disc)):
        if v is not None:
            s[k] = v
    return s


DB = [
    _song("B/Mono/02 Black.mp3", "Black", "Hold Switch", "Monochrome", "2/3"),
    _song("B/Mono/01 Grey.mp3", "Grey", "Hold Switch", "Monochrome", "1/3"),
    _song("B/Mono/d2-01 Bonus.mp3", "Bonus", "Hold Switch", "Monochrome", "1", disc="2"),
    _song("A/Demo/01 Menu.mp3", "menu", "analog hearts", "Demo"),
    _song("Loose/untagged.mp3"),
]


class FakeServer:
    def __init__(self):
        self.down = False
        self.drop_next = False
        self.connects = 0
        self.queue, self.state, self.pos, self.volume = [], "stop", None, 50
        self.updating = False


class FakeMPD:
    server = None

    def __init__(self):
        self.timeout = None
        self.in_list = False

    # connection
    def connect(self, host, port):
        if self.server.down:
            raise ConnectionRefusedError(111, "Connection refused")
        self.server.connects += 1

    def disconnect(self):
        pass

    def _io(self):
        if self.server.drop_next:
            self.server.drop_next = False
            raise mpd.ConnectionError("Connection lost while reading line")

    # playback
    def status(self):
        self._io()
        s = self.server
        st = {"volume": str(s.volume), "state": s.state, "playlistlength": str(len(s.queue))}
        if s.pos is not None:
            st.update(song=str(s.pos), elapsed="12.5", duration="200.5")
        if s.updating:
            st["updating_db"] = "1"
        return st

    def currentsong(self):
        s = self.server
        return dict(s.queue[s.pos], pos=str(s.pos)) if s.pos is not None else {}

    def clear(self):
        self.server.queue, self.server.pos, self.server.state = [], None, "stop"

    def command_list_ok_begin(self):
        self.in_list = True

    def command_list_end(self):
        self.in_list = False
        return [None]

    def add(self, uri):
        assert self.in_list, "adds should be batched in a command list"
        match = [s for s in DB if s["file"] == uri]
        if not match:
            raise mpd.CommandError("[50@0] {add} No such directory")
        self.server.queue.append(match[0])

    def play(self, pos=None):
        s = self.server
        if not s.queue:
            raise mpd.CommandError("[2@0] {play} Bad song index")
        s.pos = s.pos if pos is None and s.pos is not None else int(pos or 0)
        s.state = "play"

    def pause(self, flag):
        if self.server.state != "stop":
            self.server.state = "pause" if int(flag) else "play"

    def next(self):
        s = self.server
        if s.state == "stop":
            raise mpd.CommandError("[55@0] {next} Not playing")
        s.pos += 1

    def previous(self):
        self.server.pos = max(0, self.server.pos - 1)

    def setvol(self, v):
        self.server.volume = int(v)

    # library
    def update(self):
        self.server.updating = True
        return "1"

    def stats(self):
        return {"songs": str(len(DB))}

    def list(self, tag, *filt):
        rows = DB
        if filt:
            rows = [s for s in DB if s.get(filt[0]) == filt[1]]
        return [{tag: v} for v in {s.get(tag, "") for s in rows}]

    def find(self, *pairs):
        crit = dict(zip(pairs[::2], pairs[1::2]))
        return [s for s in DB if all(s.get(k) == v for k, v in crit.items())]

    def listallinfo(self):
        return [{"directory": "B"}] + DB

    def listplaylists(self):
        return [{"playlist": "Road Trip", "last-modified": "x"}, {"playlist": "commute", "last-modified": "x"}]

    def listplaylistinfo(self, name):
        return [DB[1], {"file": "gone.mp3"}, DB[0]]


@pytest.fixture
def server(monkeypatch):
    s = FakeServer()
    FakeMPD.server = s
    monkeypatch.setattr(lp, "client_factory", FakeMPD)
    monkeypatch.setattr(lp, "_client", None)
    monkeypatch.setattr(lp, "_library_checked_at", 0.0)
    monkeypatch.delenv("LOCAL_MUSIC", raising=False)
    return s


def test_play_queues_list_and_starts_at_index(server):
    uris = [s["file"] for s in lp.tracks("Monochrome")]
    lp.play(uris, start=1)
    assert [s["file"] for s in server.queue] == uris
    np = lp.to_now_playing(lp.status())
    assert (np["name"], np["track_index"], np["track_total"]) == ("Black", 2, 3)
    assert np["is_playing"] and np["duration"] == 200500 and np["progress"] == 12500
    assert np["volume"] == 50 and np["source"] == "local"


def test_reconnects_once_when_mpd_dropped_the_connection(server):
    assert lp.status() is not None
    server.drop_next = True
    assert lp.status() is not None
    assert server.connects == 2


def test_unreachable_mpd(server):
    server.down = True
    assert lp.status() is None
    assert lp.get_volume() is None
    assert not lp.library_ready()
    with pytest.raises(player.PlayerError):  # caught by spotify_manager like go-librespot errors
        lp.play(["B/Mono/01 Grey.mp3"])


def test_command_errors_become_player_errors(server):
    with pytest.raises(lp.LocalPlayerError, match="Not playing"):
        lp.next_track()


def test_playpause_resume_from_each_state(server):
    lp.play([DB[0]["file"]])
    lp.playpause()
    assert server.state == "pause"
    lp.playpause()
    assert server.state == "play"
    lp.pause()
    lp.resume()
    assert server.state == "play"


def test_volume_is_clamped_and_relative(server):
    lp.volume(150)
    assert server.volume == 100
    lp.volume(-30, relative=True)
    assert lp.get_volume() == {"value": 70, "max": 100}
    server.volume = -1  # MPD reports -1 before an output has a mixer
    assert lp.get_volume() is None


def test_library_queries(server):
    assert lp.artists() == ["analog hearts", "Hold Switch"]          # empty tag dropped, case-insensitive
    assert lp.albums() == ["Demo", "Monochrome"]
    assert lp.albums("analog hearts") == ["Demo"]
    assert [s["title"] for s in lp.tracks("Monochrome", "Hold Switch")] == ["Grey", "Black", "Bonus"]
    assert [lp.title_of(s) for s in lp.songs()] == ["Black", "Bonus", "Grey", "menu", "untagged"]
    assert lp.playlists() == ["commute", "Road Trip"]
    assert [s["file"] for s in lp.playlist_tracks("Road Trip")] == ["B/Mono/01 Grey.mp3", "B/Mono/02 Black.mp3"]


def test_update_and_library_ready(server):
    assert lp.library_ready()
    lp.update_db()
    assert lp.updating()
    assert lp.song_count() == len(DB)


def test_disabled_never_talks_to_mpd(server, monkeypatch):
    monkeypatch.setenv("LOCAL_MUSIC", "0")
    assert lp.status() is None
    assert not lp.library_ready()
    assert server.connects == 0


def test_stopped_player_has_no_now_playing(server):
    assert lp.to_now_playing(lp.status()) is None

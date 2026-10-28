"""Portal Output card endpoints."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "portal"))

import app as portal  # noqa: E402
import audio_output  # noqa: E402


@pytest.fixture
def client():
    portal.app.config["TESTING"] = True
    return portal.app.test_client()


def test_api_audio_lists_outputs(client, monkeypatch):
    state = {"switchable": True, "active": "wired",
             "outputs": [{"id": "wired", "label": "Headphones", "kind": "wired",
                          "connected": True, "active": True}]}
    monkeypatch.setattr(audio_output, "outputs", lambda: state)
    assert client.get("/api/audio").get_json() == state


def test_select_output(client, monkeypatch):
    chosen = []
    monkeypatch.setattr(audio_output, "select", lambda o: (chosen.append(o) or (True, "")))
    res = client.post("/audio/output", json={"output": "AA:BB:CC:DD:EE:01"})
    assert res.status_code == 200 and res.get_json()["ok"]
    assert chosen == ["AA:BB:CC:DD:EE:01"]


def test_select_output_failure_is_reported(client, monkeypatch):
    monkeypatch.setattr(audio_output, "select", lambda o: (False, "Headphone jack not found"))
    res = client.post("/audio/output", json={"output": "wired"})
    assert res.status_code == 502
    assert res.get_json() == {"ok": False, "message": "Headphone jack not found"}


def test_index_has_output_card(client, monkeypatch):
    html = client.get("/").get_data(as_text=True)
    assert 'id="audio-outputs"' in html and "bt-sink-select" not in html

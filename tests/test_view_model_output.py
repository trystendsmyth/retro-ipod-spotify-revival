"""Settings -> Output and the About row."""
import audio_output
import spotify_manager as sm
import view_model as vm

OUTPUTS = [
    {"id": "wired", "label": "Headphones", "kind": "wired", "connected": True, "active": True},
    {"id": "AA:BB:CC:DD:EE:01", "label": "JBL Flip", "kind": "bluetooth", "connected": True, "active": False},
]


def _settings_titles():
    settings = vm.SettingsPage(None)
    return [settings.page_at(i).header for i in range(settings.total_size())]


def test_output_menu_only_with_pipewire(monkeypatch):
    monkeypatch.setenv("AUDIO_BACKEND", "pulseaudio")
    assert "Output" in _settings_titles()
    monkeypatch.setenv("AUDIO_BACKEND", "alsa")
    assert "Output" not in _settings_titles()


def test_output_menu_marks_active_and_selects(monkeypatch):
    monkeypatch.setattr(audio_output, "outputs", lambda: {"switchable": True, "active": "wired", "outputs": OUTPUTS})
    chosen = []
    monkeypatch.setattr(audio_output, "select", lambda o: (chosen.append(o) or (True, "")))
    monkeypatch.setattr(sm, "run_async", lambda fn: fn())
    page = vm.OutputPage(None)
    assert [line.title for line in page.render().lines[:2]] == ["Headphones (on)", "JBL Flip"]
    page.nav_up()
    assert page.nav_select() is page
    assert chosen == ["AA:BB:CC:DD:EE:01"]


def test_about_shows_active_output(monkeypatch):
    monkeypatch.setattr(audio_output, "outputs", lambda: {"switchable": True, "active": "wired", "outputs": OUTPUTS})
    rows = dict(vm.about.items())
    assert rows["Output"] == "Headphones"

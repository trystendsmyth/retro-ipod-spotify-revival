import os
import sys
import tempfile

os.environ["SPOTIFYPOD_DATA_DIR"] = tempfile.mkdtemp(prefix="spot-test-")
os.environ["SPOTIFYPOD_CONFIG"] = os.devnull
os.environ["SPOTIFYPOD_INSTALL_ENV"] = os.devnull
os.environ.pop("SPOTIPY_CLIENT_ID", None)
os.environ.pop("LOCAL_MUSIC", None)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend"))
sys.path.insert(0, os.path.dirname(__file__))

import spotify_manager  # noqa: E402

# Its background poller would call player/MPD/audio_router while tests run.
spotify_manager.refresh_now_playing = lambda: None

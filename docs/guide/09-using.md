# 9. Using it

* **Scroll:** turn the wheel. **Select:** centre button. **Back:** MENU.
  **Play/pause:** play button. **Next / previous track:** forward / back buttons.
* **Volume:** on Now Playing, turn the wheel; the bar shows volume for two seconds.
* **Settings -> Sync Library** refreshes playlists, saved tracks, albums and artists.
* **Settings -> Shut Down / Reboot.**
* The screen blanks after 60 s idle; any touch wakes it
  (`SCREEN_TIMEOUT_SECONDS` in `/etc/spotifypod/config.env`, 0 = never).

## Audio

Open `http://ipod.local` on your phone:

* **Bluetooth headphones/speaker:** put them in pairing mode, **Scan**, **Pair & connect**.
  They reconnect automatically on later boots.
* **Wired (USB or I2S DAC):** re-run the installer with `AUDIO_BACKEND=alsa`. The 4th-gen
  headphone jack is not connected to anything in this build.

## What Spotify does not allow

Followed playlists you do not own show as play-only (no track list). "Made for you" and
radio items only appear if you follow/save them in the Spotify app, then sync. New
Releases is gone (2026 API change).

# 9. Using it

* **Scroll:** turn the wheel. **Select:** centre button. **Back:** MENU.
  **Play/pause:** play button. **Next / previous track:** forward / back buttons.
* **Volume:** on Now Playing, turn the wheel; the bar shows volume for two seconds.
* **Settings -> About** shows the software version, the iPod's IP address, the display
  setting, the versions of go-librespot and MPD, and the active audio output.
* **Settings -> Sync Library** refreshes playlists, saved tracks, albums and artists.
* **Settings -> Update Music** rescans your own music files ([chapter 9b](09b-own-music.md)).
* **Settings -> Shut Down / Reboot.**
* The screen blanks after 60 s idle; any touch wakes it
  (`SCREEN_TIMEOUT_SECONDS` in `/etc/spotifypod/config.env`, 0 = never).

## Audio

* **Headphone jack:** plug in earbuds. With no Bluetooth device connected, sound plays
  from the jack ([chapter 6b](06b-wired-audio.md)).
* **Bluetooth headphones/speaker:** open `http://ipod.local` on your phone, put them in
  pairing mode, **Scan**, **Pair & connect**. Sound moves to them, and they reconnect
  automatically on later boots.
* **Switching:** **Settings -> Output** on the iPod, or the **Output** card on the setup
  page, lists **Headphones** and your paired Bluetooth devices. With jack detect wired,
  plugging in switches to the jack and unplugging switches back to Bluetooth.

Your own music files (chapter 9b) play to the same output. Volume on the wheel goes up to
the jack's limit (`WIRED_GAIN_DB`, chapter 6b).

## What Spotify does not allow

Followed playlists you do not own show as play-only (no track list). "Made for you" and
radio items only appear if you follow/save them in the Spotify app, then sync. New
Releases is gone (2026 API change).

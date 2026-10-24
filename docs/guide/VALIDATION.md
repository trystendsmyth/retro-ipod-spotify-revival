# Hardware validation checklist

This isn't a build step. It records what has actually been tested on hardware, one
column per OS image. Fill in each cell with **pass**, **fail** or a measurement, and add
what you saw under Notes. When results come in, update the README "Status" section,
the relevant guide chapter and [10-troubleshooting.md](10-troubleshooting.md) with what
was observed.

Images: **32-bit** = Raspberry Pi OS Lite 32-bit on a Pi Zero W. **64-bit** = Raspberry Pi
OS Lite 64-bit on a Pi Zero 2 W. Record the OS release (Bookworm/Trixie) and image date
next to each result.

| # | Check | 32-bit / Zero W | 64-bit / Zero 2 W | Notes |
|---|---|---|---|---|
| 1 | Installer completes; `click`, `go-librespot`, `spotifypod`, `spotifypod-portal` (and `spotifypod-mpd` with `LOCAL_MUSIC=1`) are `active (running)` | [ ] | [ ] | |
| 2 | Installer re-run is clean, with `LOCAL_MUSIC=1` and then `LOCAL_MUSIC=0` | [ ] | [ ] | |
| 3 | go-librespot (`armv6_rpi` on the Zero W, `arm64` on the Zero 2 W): appears in Spotify Connect, plays; CPU load while playing (`top`) | [ ] | [ ] | |
| 4 | PipeWire + Bluetooth: is audio stable? If not on the Zero W, document `AUDIO_BACKEND=alsa` | [ ] | [ ] | |
| 5 | Composite through KMS: `dtoverlay=vc4-kms-v3d,composite` gives a picture. Does X choose 720x480? Does the UI's auto-fit look right? Overscan or clipping? | [ ] | [ ] | |
| 6 | Adafruit #911 at 5 V: stable or flickering? (Adafruit rates it 6-12 V; sPot used 5 V) | [ ] | [ ] | |
| 7 | Click wheel with FPC pins 3/7 floating (sPot) vs tied to 3.3 V (Garr) | [ ] | [ ] | |
| 8 | Scroll direction: does clockwise move down the list? | [ ] | [ ] | |
| 9 | Haptic motor at 5 V vs 3.3 V, with the 1N4148 flyback diode fitted | [ ] | [ ] | |
| 10 | PowerBoost EN on the hold switch cuts power; runtime on the chosen cell | [ ] | [ ] | |
| 11 | Setup flow: comitup hotspot (`iPod-<nnn>`, open network), Connect login, PKCE through the Pages relay, then the paste-URL fallback | [ ] | [ ] | |
| 12 | comitup install: which version did the installer get (`dpkg -l comitup python3-networkmanager`)? Does `COMITUP_SOURCE=debian` also work on this release? | [ ] | [ ] | |
| 13 | Music on iPod: files copied with `rsync` appear after Settings -> Update Music; MP3, FLAC, M4A play | [ ] | [ ] | |
| 14 | Music on iPod: CPU load while MPD plays a FLAC file over Bluetooth | [ ] | [ ] | |
| 15 | Source switching: starting local music pauses Spotify, and vice versa; a phone pressing play via Connect pauses local music | [ ] | [ ] | |
| 16 | `AUDIO_BACKEND=alsa` with a DAC: can go-librespot and MPD take turns on the device, or does one report "device busy"? | [ ] | [ ] | |
| 17 | Settings -> About shows the right version, IP address, display profile and backend versions | [ ] | [ ] | |

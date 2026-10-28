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
| 15 | Songs list with N songs (record N; try ~3,000): seconds to open **Songs**, and from selecting a song to sound (200 songs are queued around it). If slow, load lists off the UI thread | [ ] | [ ] | |
| 16 | Copy permissions: a folder copied from a computer where the files are mode 600 shows up after **Update Music** when copied with `rsync -av --chmod=a+rX`, and with `scp` plus `chmod -R a+rX /srv/music` | [ ] | [ ] | |
| 17 | Source switching: starting local music pauses Spotify, and vice versa; a phone pressing play via Connect pauses local music | [ ] | [ ] | |
| 18 | `AUDIO_BACKEND=alsa` with a DAC: can go-librespot and MPD take turns on the device, or does one report "device busy"? | [ ] | [ ] | |
| 19 | Settings -> About shows the right version, IP address, display profile and backend versions | [ ] | [ ] | |
| 20 | Wired audio: `i2cdetect -y 1` shows `18`; `spotifypod-dac` is `active (exited)`; `aplay -l` lists `sndrpirpidac`; OS release and kernel version | [ ] | [ ] | |
| 21 | Hold switch still turns the iPod on and off after the jack board is soldered | [ ] | [ ] | |
| 22 | Jack output level at `WIRED_GAIN_DB=-20` with 16 Ω and 32 Ω earbuds: comfortable at full wheel volume? Record the value you would choose | [ ] | [ ] | |
| 23 | Hiss or distortion with the DAC's PLL on the I2S bit clock, at 44.1 kHz (Spotify) and with a 48 kHz FLAC (Music on iPod) | [ ] | [ ] | |
| 24 | Whine in the earbuds at idle and while playing, on battery (PowerBoost) and on USB power; is the hold switch's ground joined to the jack's sleeve? | [ ] | [ ] | |
| 25 | Pops at boot, at shutdown and between tracks, with `AUDIO_BACKEND=pulseaudio` and `alsa` | [ ] | [ ] | |
| 26 | Jack detect: which jack pins, the level with a plug in, switching to the jack and back to Bluetooth | [ ] | [ ] | |
| 27 | Output switching from Settings -> Output and the setup page; Bluetooth disconnect falls back to the jack; Spotify and MPD keep playing across a switch | [ ] | [ ] | |
| 28 | `AUDIO_BACKEND=alsa` with the DAC: go-librespot and MPD take turns through `dmix` without "device busy" | [ ] | [ ] | |
| 29 | CPU load with PipeWire keeping the DAC running: idle, Spotify playing, FLAC playing (`top`) | [ ] | [ ] | |
| 30 | Click wheel and haptics with pigpio on the PWM clock (`-DI2S_AUDIO`): no lost wheel events, no audio glitches while scrolling | [ ] | [ ] | |
| 31 | iPod 4G dock opening: width, height, corner radius, wall thickness, middle of the opening to the inside surface (the bracket's `[MEASURE]` values) | [ ] | [ ] | |
| 32 | Bracket: prints without supports; bezel fits the opening; USB-C cables (record which) click in fully | [ ] | [ ] | |
| 33 | Charging from a USB-C-to-C charger (record which) with the hold switch engaged: yellow LED; and from a USB-A-to-C cable | [ ] | [ ] | |
| 34 | Charging while playing Spotify: no brownout or reboot when plugging and unplugging; charge ends (green LED) while running | [ ] | [ ] | |
| 35 | PowerBoost 1000C temperature in the closed case while charging at 1 A and playing | [ ] | [ ] | |
| 36 | Runtime from full on the cell used (record its mAh), playing Spotify over the jack and over Bluetooth | [ ] | [ ] | |
| 37 | Hold switch engaged with the charger plugged in: the iPod stays off and keeps charging | [ ] | [ ] | |

# 10. Troubleshooting

Logs: `journalctl -u <service> -b --no-pager | tail -50` with service `click`,
`go-librespot`, `spotifypod`, `spotifypod-portal`, `spotifypod-mpd` or `spotifypod-dac`.

| Symptom | Things to check |
|---|---|
| Installer: `go-librespot checksum mismatch` | You changed `GO_LIBRESPOT_VERSION` without updating both SHA256 values, or the download was corrupted. Re-run. |
| "iPod" missing from Spotify's device list | Phone and Pi on the same Wi-Fi; `go-librespot` running; Wi-Fi power saving is disabled by the installer (it breaks mDNS discovery). |
| Setup page shows "Missing or non-local state" | You opened the relay page directly, or the iPod's address is not a `.local` name / private IP. Use **Paste redirect URL**. |
| Spotify login: `INVALID_CLIENT: Invalid redirect URI` | The URI in `config.env` must match the dashboard *exactly* (scheme, path, trailing slash). |
| Web API errors 403 on playlists | Expected for playlists you don't own (Feb 2026 rules); they are play-only. |
| No click wheel events | Ribbon orientation in the breakout; pin 1 alignment; 3.3 V on FPC pin 1; GPIO 23/25 not swapped; try tying FPC pins 3 and 7 to 3.3 V. |
| Wheel events but UI doesn't move | `click` and `spotifypod` must both run; only one program can bind UDP 9090. |
| Black composite screen | Nothing in the mini-HDMI port; Zero W: video on the square TV hole; `grep vc4 /boot/firmware/config.txt` shows `dtoverlay=vc4-kms-v3d,composite`; video and ground wires not swapped; display power (see 6-12 V note). |
| Rolling / black-and-white picture | NTSC vs PAL mismatch: re-run installer with the other `TV_NORM`. |
| No **Music on iPod** in the menu | It is hidden until MPD has at least one song: copy files to `/srv/music`, then **Settings -> Update Music**. Check `systemctl status spotifypod-mpd`. Not installed with `LOCAL_MUSIC=0`. |
| **Update Music** says "MPD not running" | `journalctl -u spotifypod-mpd -b --no-pager`; the config is `/var/lib/spotifypod/mpd/mpd.conf`. |
| Files copied but missing after **Update Music** | Files copied with plain `rsync -a` or `scp` keep your computer's permissions, and MPD (user `spotifypod`) can't read files only you can read. Run `chmod -R a+rX /srv/music` on the Pi, then **Update Music**. Also: the format must be one MPD decodes; protected `.m4p` files never play. |
| A compilation shows up under many artists | Menus group by the album artist tag; set one (e.g. "Various Artists") on every track, then **Update Music**. |
| Haptics continue at end of list | Known sPot behaviour: haptics follow the finger, not the UI. |
| Random reboots | Battery too small or long BAT wires to the PowerBoost; low battery (red LBO LED). |
| Pi Zero W feels slow | Expected on its single core. Bluetooth audio (PipeWire) costs CPU; a wired DAC with `AUDIO_BACKEND=alsa` is lighter. A Zero 2 W is the faster alternative. |
| High-pitched whine | Reported in the original sPot build too; usually from the boost converter or motor. In the earbuds: check whether it is there on USB power too (if not, it is the PowerBoost). Keep the DAC's wires short and its ground on pin 34; ground the jack's sleeve only through the DAC (chapter 6b). If the hold switch's ground is joined to the sleeve on the jack board, that loop is the next suspect. A ferrite bead on the DAC's VIN wire is the next thing to try `[MEASURE]`. |
| No sound from the headphone jack | `systemctl status spotifypod-dac`: it must say "headphone output on". "No such device" or "Remote I/O error": I2C wiring (pins 3, 5), VIN or GND; `sudo i2cdetect -y 1` must show `18`. Then `aplay -l` must list `sndrpirpidac` (`grep -A3 'retro-ipod-spotify-revival audio' /boot/firmware/config.txt`). Check **Settings -> Output** says Headphones (on). |
| Sound from the jack is loud, quiet or in one ear | Loudness: `WIRED_GAIN_DB` (chapter 6b). One ear or thin sound: tip/ring/sleeve swapped at the jack; check them again with the 3.5 mm cable and a multimeter. |
| Hiss or distortion from the jack | The DAC runs its clock from the I2S bit clock; Adafruit reports this can hiss at low sample rates. The installer pins the rate to 44.1 kHz; check `pw-dump` / `wpctl inspect` for `audio.rate`. With `AUDIO_BACKEND=alsa`, check `/etc/asound.conf` has `rate 44100`. |
| Pops or clicks from the jack | At boot the DAC is held in reset until `spotifypod-dac` sets it up; at shutdown it ramps the output down first. Clicks between tracks with `AUDIO_BACKEND=alsa` come from the I2S clock stopping when nothing plays; the default PipeWire setup keeps it running. |
| "device busy" with `AUDIO_BACKEND=alsa` | Both players must use the `dmix` device: `/etc/asound.conf` must exist and start with the retro-ipod-spotify-revival line (an asound.conf from elsewhere is left alone). PipeWire must be masked for the `spotifypod` user: `ls -l /var/lib/spotifypod/.config/systemd/user`. |
| Wrong sound card (USB DAC, `AUDIO_BACKEND=alsa`, `WIRED_AUDIO=none`) | `aplay -l`, then re-run the installer with `ALSA_CARD=<the card's name>`. |
| Output doesn't switch back to the jack | Settings -> Output -> Headphones. Bluetooth devices that are connected keep the sound until you choose. Jack detect: `pinctrl lev 16` with and without a plug; set `JACK_PLUGGED_LEVEL` to the plugged value. |
| Installer: `BL_GPIO=18 is the I2S bit clock` | st7789 profile with wired audio: move the display backlight to GPIO 27 (pin 13, the default), or set `BL_GPIO=""` for a backlight tied to 3.3 V. |

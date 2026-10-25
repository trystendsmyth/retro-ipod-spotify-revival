# 10. Troubleshooting

Logs: `journalctl -u <service> -b --no-pager | tail -50` with service `click`,
`go-librespot`, `spotifypod`, `spotifypod-portal` or `spotifypod-mpd`.

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
| High-pitched whine | Reported in the original sPot build too; usually from the boost converter or motor. |

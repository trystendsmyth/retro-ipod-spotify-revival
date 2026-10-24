# 4. Install the software (bench Pi)

On the Pi (over SSH):

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/trystendsmyth/spot-revival.git
cd spot-revival
sudo DISPLAY_PROFILE=composite TV_NORM=NTSC bash install/install.sh
```

Use `TV_NORM=PAL` if your display is set to PAL. The installer takes 10-20 minutes on a
Pi 3 (longer on a Zero W). What it does:

* installs packages (Python, X, PipeWire for Bluetooth audio, build tools);
* builds pigpio if your OS no longer packages it, then compiles `clickwheel/click.c` with
  your pin numbers (clock 23, data 25, haptic 26 by default);
* downloads go-librespot **v0.10.4** for your CPU (64-bit or ARMv6) and checks its SHA256;
* writes the composite display settings to `/boot/firmware/config.txt` and
  `cmdline.txt` (`dtoverlay=vc4-kms-v3d,composite`, `enable_tvout=1`,
  `vc4.tv_norm=...`, as described in the Raspberry Pi config.txt documentation);
* creates a `spotifypod` service user and four systemd services: `click`,
  `go-librespot`, `spotifypod` (UI) and `spotifypod-portal` (setup page);
* sets the hostname to `ipod`.

## Configure

```bash
sudo nano /etc/spotifypod/config.env
```

Set the two values from chapter 2:

```
SPOTIPY_CLIENT_ID=<your client id>
SPOTIPY_REDIRECT_URI=<the redirect URI you registered, exactly>
```

Reboot: `sudo reboot`.

## First boot

The screen (once connected in chapter 6) shows a setup sequence. You can also follow it
from the setup page:

1. **Wi-Fi** - already configured by Imager. (If the Pi cannot join a network, it opens a
   hotspot called `iPod-<number>` via comitup.)
2. **Spotify Connect** - in the Spotify app on your phone, open the device picker and
   choose **iPod**. go-librespot saves its credentials, so this is a one-time step.
3. **Link library** - on your phone open `http://ipod.local`, tap **Authorize with
   Spotify**, approve. (Option B redirect: paste the final URL into **Paste redirect URL**.)
4. **Sync** starts by itself; then the main menu appears.

## Check the services

```bash
systemctl status click go-librespot spotifypod spotifypod-portal --no-pager
journalctl -u go-librespot -b --no-pager | tail -20
```

**Check:** all four are `active (running)`; the phone's Spotify app lists **iPod** as a
device and plays through it (with no audio device configured yet, it still "plays"
silently - audio is set up in chapter 9 or via the setup page).

## Before hardware: preview the UI on any computer

```bash
pip install -r frontend/requirements.txt
python3 tools/ui_preview.py     # arrow keys: up/down scroll, right select, left back
```

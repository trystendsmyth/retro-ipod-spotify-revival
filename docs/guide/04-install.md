# 4. Install the software

On the Pi (over SSH):

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/trystendsmyth/retro-ipod-spotify-revival.git
cd retro-ipod-spotify-revival
sudo DISPLAY_PROFILE=composite TV_NORM=NTSC bash install/install.sh
```

Use `TV_NORM=PAL` if your display is set to PAL. Expect this to take a long time on a
Zero W (package installs and Python libraries run on a single core); a Zero 2 W is much
quicker. Keep the SSH session open until it prints `Install complete.` What it does:

* installs packages (Python, X, PipeWire for Bluetooth audio, build tools);
* builds pigpio if your OS no longer packages it, then compiles `clickwheel/click.c` with
  your pin numbers (clock 23, data 25, haptic 26 by default);
* downloads go-librespot **v0.10.4** - the `armv6_rpi` build on a Zero W, `arm64` on a
  Zero 2 W - and checks its SHA256;
* writes the composite display settings to `/boot/firmware/config.txt` and
  `cmdline.txt` (`dtoverlay=vc4-kms-v3d,composite`, `enable_tvout=1`,
  `vc4.tv_norm=...`, as described in the Raspberry Pi config.txt documentation);
* creates a `spotifypod` service user and four systemd services: `click`,
  `go-librespot`, `spotifypod` (UI) and `spotifypod-portal` (setup page);
* installs MPD for your own music files as a fifth service, `spotifypod-mpd`, with the
  music folder `/srv/music` ([chapter 9b](09b-own-music.md); `LOCAL_MUSIC=0` skips it);
* installs [comitup](https://davesteele.github.io/comitup/) for the setup hotspot from
  comitup's own apt repository. The Bookworm package crashes with Bookworm's
  python3-networkmanager
  ([comitup #234](https://github.com/davesteele/comitup/issues/234)), and comitup's
  repository carries the fixed versions for Bookworm and Trixie. This adds that repository
  as a trusted package source. `COMITUP_SOURCE=debian` uses the distribution's package
  instead, and on a re-run removes the repository again;
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

The file already contains the hosted relay address (option A), so with option A you only
need to fill in the Client ID.

Reboot: `sudo reboot`.

## First boot

There is no screen yet, so do the setup from your phone. (Once the display is wired in
chapter 6, the iPod shows the same steps.)

1. **Wi-Fi** - already configured by Imager. (If the Pi cannot join a network, it opens a
   hotspot called `iPod-<number>` via comitup.)
2. **Spotify Connect** - in the Spotify app on your phone, open the device picker and
   choose **iPod**. go-librespot saves its credentials, so this is a one-time step.
3. **Link library** - on your phone open `http://ipod.local`, tap **Authorize with
   Spotify**, approve. (Redirect option B: paste the final URL into **Paste redirect URL**.)
4. **Sync** starts by itself. The setup page shows its progress.

## Check the services

```bash
systemctl status click go-librespot spotifypod spotifypod-portal spotifypod-mpd --no-pager
journalctl -u go-librespot -b --no-pager | tail -20
```

**Check:** all five are `active (running)` (four with `LOCAL_MUSIC=0`) and the phone's
Spotify app lists **iPod** as a device. (Audio output is chosen later on the setup page - chapter 9.)

## Optional: preview the UI on your computer

```bash
pip install -r frontend/requirements.txt
python3 tools/ui_preview.py     # arrow keys: up/down scroll, right select, left back
```

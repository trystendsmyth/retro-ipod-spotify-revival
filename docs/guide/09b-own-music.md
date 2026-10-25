# 9b. Your own music files

Besides Spotify, the iPod plays DRM-free music files stored on its SD card. They appear
under **Music on iPod** in the main menu and play to the same output as Spotify (Bluetooth
or a wired DAC), with the same wheel volume, play/pause and next/previous buttons, and the
same Now Playing screen.

The files are played by [MPD](https://www.musicpd.org/) (Music Player Daemon), which the
installer sets up by default (`LOCAL_MUSIC=1`). It runs as `spotifypod-mpd.service` and only
listens on the Pi itself.

## What it can't play

* **Spotify downloads.** Songs downloaded in the Spotify app are encrypted for that app.
  go-librespot only streams, so the iPod can't use them.
* **Spotify "local files".** Spotify's local-files feature plays files stored on your
  computer or phone. They never reach go-librespot, which only streams from Spotify. Copy
  those files to the iPod instead (below).
* **Protected iTunes purchases.** Songs bought from the iTunes Store before 2009 were sold
  with FairPlay DRM (`.m4p` files). They won't play. DRM-free `.m4a`/AAC files work.

MPD handles the common formats, including MP3, FLAC, Ogg Vorbis and AAC/M4A (see
[MPD's decoder plugins](https://mpd.readthedocs.io/en/stable/plugins.html#decoder-plugins)).

## Copy music to the iPod

The music folder is `/srv/music`. It belongs to the account you created in Raspberry Pi
Imager (chapter 3), so you can copy into it over SSH from your computer. Keep one folder
per artist or album. MPD reads the artist, album, title and track number from the files'
tags. Menus group by **album artist** (falling back to artist), so give compilations an
album artist such as "Various Artists" to keep them together as one album.

```bash
# macOS / Linux: copy one album (the trailing slashes matter)
rsync -av --chmod=a+rX ~/Music/Album/ <user>@ipod.local:/srv/music/Album/
```

`--chmod=a+rX` makes the copies readable by MPD. Without it, rsync keeps your computer's
permissions, and files that only you can read there silently never show up on the iPod.
(This form also works with the older rsync that ships with macOS.)

With `scp`, which also keeps your computer's permissions, fix them after copying:

```bash
scp -r ~/Music/Album <user>@ipod.local:/srv/music/
ssh <user>@ipod.local chmod -R a+rX /srv/music
```

Then on the iPod open **Settings -> Update Music** and press the centre button. When it shows
the number of songs, the new music is under **Music on iPod**.

* **Space:** your music shares the SD card with the system. Check the free space with
  `df -h /srv/music`. A larger card gives you more room.
* **Playlists:** put `.m3u` files at the top of `/srv/music`. Each line is a song path
  relative to `/srv/music`, for example `Artist/Album/01 Song.mp3`. Lines for files that
  aren't there are skipped.
* **Windows file sharing (Samba)** would let you drag files over the network, but it costs
  memory on the Zero W's 512 MB, so this build doesn't install it. Use `rsync`, `scp` or an
  SFTP app (WinSCP, Cyberduck).

## Using it

* **Music on iPod -> Artists -> albums -> songs**, **Albums**, **Songs** and
  **Playlists** work like the Spotify menus.
* Selecting a song plays it and queues the rest of that album or list, so next/previous
  move through the album.
* **One source at a time:** starting your own music pauses Spotify, and starting Spotify
  pauses your music. If someone picks **iPod** in the Spotify app on a phone and presses
  play, your music pauses too. Now Playing always shows whichever is playing.
* **Music on iPod** is hidden until the library has at least one song.

## Turning it off

Re-run the installer with `LOCAL_MUSIC=0`:

```bash
cd retro-ipod-spotify-revival
sudo LOCAL_MUSIC=0 DISPLAY_PROFILE=composite TV_NORM=NTSC bash install/install.sh
```

This stops and removes `spotifypod-mpd.service` and hides the menu and the
**Update Music** setting. Your files in `/srv/music` are left alone. Run it again with
`LOCAL_MUSIC=1` (or without the variable) to turn it back on.

**Check:** after **Update Music**, **Music on iPod** lists your artists, and a song plays
through your speaker or headphones.

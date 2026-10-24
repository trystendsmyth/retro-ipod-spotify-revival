# 3. Flash the SD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/).

| Final board | Image to choose | Bench test on the Pi 3? |
|---|---|---|
| Pi Zero 2 W | **Raspberry Pi OS Lite (64-bit)** | Yes - the same card moves from the Pi 3 to the Zero 2 W. |
| Pi Zero W / Zero | **Raspberry Pi OS Lite (32-bit)** | Yes - a 32-bit card boots on the Pi 3 too, and the installer then picks the ARMv6 go-librespot build. |

Use the current release (Bookworm or newer). Choose the **Lite** image: there is no desktop;
the UI runs in a bare X session.

In Imager's **Edit settings**:

* hostname: `ipod` (the setup page will be `http://ipod.local`)
* a username and password
* your Wi-Fi network and country
* **Services -> Enable SSH**

Write the card, put it in the **Pi 3**, connect power, wait two minutes, then from your
computer:

```bash
ssh <user>@ipod.local
```

**Check:** you get a shell prompt. If `ipod.local` does not resolve, find the Pi's IP
address in your router and use that.

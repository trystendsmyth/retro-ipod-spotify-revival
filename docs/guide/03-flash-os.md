# 3. Flash the SD card

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/).

| Board | Image |
|---|---|
| **Pi Zero W** | **Raspberry Pi OS Lite (32-bit)** - the 64-bit image does not run on its ARMv6 CPU. |
| Zero 2 W | **Raspberry Pi OS Lite (64-bit)**. |

Use the current release (Bookworm or newer). Choose the **Lite** image: there is no
desktop; the UI runs in a bare X session.

In Imager's **Edit settings**:

* hostname: `ipod` (the setup page will be `http://ipod.local`)
* a username and password
* your Wi-Fi network and country - both Zero boards only support **2.4 GHz** Wi-Fi
* **Services -> Enable SSH**

Write the card, put it in the Zero, and power it from the micro-USB port marked **PWR IN**.
Nothing appears on screen yet (the display is wired in chapter 6). Wait a few minutes -
the first boot is slow on a Zero W - then from your computer:

```bash
ssh <user>@ipod.local
```

**Check:** you get a shell prompt. If `ipod.local` does not resolve, find the Pi's IP
address in your router and use that.

# Reference builds

Other people's builds of this project, with photos you can follow while you work. The
photos belong to their authors, so this page links to them. Each entry says what the
linked page shows and how that build differs from this guide.

## sPot by Guy Dupont

The original build, with the same hardware as this guide: Pi Zero W, Adafruit #911
composite display and the 4th-gen click wheel.

* [Project page](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004)
  (Hackaday.io, January 2021). Hardware and software overview. Its captioned images
  show the UI running on a desktop, an early build ("Haptic motor too big. Battery too
  small."), the composite screens and the Now Playing screen.
* [Gallery](https://hackaday.io/project/177034/gallery). Nine project images (photos and
  GIFs, without captions) and two videos:
  * [Spotify Streaming on a modded 17-year-old iPod Classic](https://youtube.com/watch?v=ZxdhG1OhVng)
    (January 2021, 16 min): the first video of the build.
  * [Spotify iPod pt. 2: FAQ's and Upgrades!](https://youtube.com/watch?v=q0pUPab7Rms)
    (March 2021, 24 min): FAQ answers, hardware upgrades (headphone jack, USB-C) and a
    gaming demo.
* [Log: "Wiring!"](https://hackaday.io/project/177034/log/189343-wiring) (February 2021).
  The original wiring diagram, which this repository also keeps as
  `.docs/sPot_schematic.png`.
* [Log: "Round 2: USB-C, wired audio, and RetroPie"](https://hackaday.io/project/177034/log/190079-round-2-usb-c-wired-audio-and-retropie)
  (March 2021). A video log of the second revision (the part 2 video above), with little
  written detail.
* [Log: "Ricardo's Alternate Build"](https://hackaday.io/project/177034/log/190310-ricardos-alternate-build)
  (March 2021). Guy's summary of Ricardo Sappia's build, below.

## SpotifyPod by Ricardo Sappia

[Build log on RSFlightronics](https://rsflightronics.com/spotifypod) (March 2021, updated
September 2022). This is the most photo-rich step-by-step build. Photos and diagrams:

* the iPod just opened, and its original internals;
* the 2-inch LCD with its connector desoldered and its sides trimmed to fit;
* the 3D-printed base plate;
* a full schematic;
* the components laid out in their final places before wiring;
* the case open, with wires long enough to open it while everything is connected;
* the display wiring;
* the click wheel ribbon in the 8-pin FPC adapter. It warns that the adapter's printed
  pinout is mirrored on the underside: use the numbers on the 0.5 mm side;
* the PowerBoost 1000C R13 modification and a power-latch circuit, where the Pi's UART TX
  holds EN high;
* a diode level-shifter for the LBO low-battery signal;
* finished-device photos and a charging stand.

The text also describes covering the metal case with polyimide tape (this step has no
photo) and gluing the haptic motor directly to the case. In a 2023 comment the author adds
that the transistor and resistors sit on a small SOT-23 adapter.

**Differences from this build:**

* the display is a 2-inch ST7789V SPI LCD (240×320), not the composite #911. This repo's
  `DISPLAY_PROFILE=st7789` follows that build;
* the boost board is a PowerBoost 1000C, not the 1000 Basic;
* the haptic driver uses a 1 kΩ base resistor and an MMBT3904;
* the click wheel data line is on GPIO 5 (`#define DATA_PIN 5`), not GPIO 25.

[3D-printed parts on Thingiverse](https://www.thingiverse.com/thing:4789155)
("Spotifypod base plate and holder" by rsappia): base plate, key-press extension and an
optional stand. Licensed **Creative Commons - Attribution - Non-Commercial**: credit
rsappia, and don't use them commercially. The files aren't included in this repository.

## SpotiPod by Sean (Shogan.tech)

The same display approach as this guide: a Pi Zero W driving a 2-inch composite LCD.

* [Build log](https://www.shogan.co.uk/builds/spotipod-spotify-streaming-device-from-an-ipod-classic/)
  (March 2021). Photos:
  * the LCD connected to the Zero's composite output, and the first LCD test;
  * the charger and PowerBoost connected;
  * the 8-pin FPC breakout being soldered;
  * the gutted iPod;
  * the case insulated with three layers of polyimide tape;
  * hot glue on the solder joints;
  * everything fitted, with the case open.

  The page also has two short click-wheel test videos, and re-hosts a community wiring
  diagram that it credits to Kakoub on the Hackaday.io project page.
* [Tiny 2" TFT composite video on a Raspberry Pi Zero](https://www.shogan.co.uk/builds/tiny-2-tft-composite-video-on-raspberry-pi-zero/)
  (March 2021). Wiring and configuring the Adafruit #911 on a Pi Zero, powered from a
  PowerBoost 1000 Basic.

**Differences from this build:** the post sets up the display with `/boot/config.txt`
overscan settings from 2021. This guide uses KMS composite (chapter 4).

## Community notes and diagrams

From the discussion on the [sPot project page](https://hackaday.io/project/177034-spot-spotify-in-a-4th-gen-ipod-2004):

* **Benjamin Stallings** (November 2022):
  [a beginner-oriented wiring diagram](https://imgur.com/a/epvkWsR) ("sPot Wiring
  Diagram", Imgur). In his reply, Guy recommended adding a flyback diode across the haptic
  motor, which this guide includes.
* **Kakoub**: a wiring diagram posted on the project page, re-hosted with credit on
  [Shogan.tech's build log](https://www.shogan.co.uk/builds/spotipod-spotify-streaming-device-from-an-ipod-classic/).
* **tanagram27** (January 2023), text only:
  * trimmed all the unused ports off the Pi Zero;
  * fitted a 2500 mAh cell lying flat, with the Pi on top;
  * wired in a PCM5102 DAC.
* **Doris** (2022–2023), text only:
  * a Pi Zero 2 W build in the thicker 60 GB back case;
  * an Adafruit USB-C charger and a PowerBoost 1000 Basic;
  * a 653496 LiPo sold as 2500 mAh, which Doris notes is really 1800 mAh;
  * warns to check the battery plug's polarity against the charger and swap the pins if
    needed.

## Background

* Jason Garr, [iPod Clickwheel Hack](https://jasongarr.wordpress.com/project-pages/ipod-clickwheel-hack/)
  (January 2010): the click wheel pinout and packet format. Write-up on Hackaday:
  [Repurposing a click wheel](https://hackaday.com/2010/02/05/repurposing-a-click-wheel/)
  (February 2010).
* Raspberry Pi News,
  [Raspberry Pi Zero W turns iPod Classic into Spotify music player](https://www.raspberrypi.com/news/raspberry-pi-zero-w-turns-ipod-classic-into-spotify-music-player/)
  (April 2021).
* [Community install notes](https://github.com/dupontgu/retro-ipod-spotify-client/issues/69)
  ("How I got everything working", sPot issue #69, 2022–2024). The software steps there
  are outdated; this guide replaces them.

## Contributing photos

* **Photos of your own build** can go in `docs/images/builds/` under this repository's
  licence. One photo per guide chapter, taken at its **Check** step, works best.
* **Other people's photos** need the author's written permission, recorded in
  `CREDITS.md` (who, date, which images, terms). Caption each one with the author's name
  and a link to the original.

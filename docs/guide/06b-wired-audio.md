# 6b. Wired audio (headphone jack)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../wiring/05-wired-audio-dark.svg">
  <img alt="Schematic: Pi pins 4 (5V), 3 (GPIO2 SDA), 5 (GPIO3 SCL), 11 (GPIO17), 12 (GPIO18 BCLK), 35 (GPIO19 LRCLK), 40 (GPIO21 DOUT) and 34 (GND) to the Adafruit 6309 TLV320DAC3100 pads VIN, SDA, SCL, RST, BCK, WSEL, DIN and GND; its HPL, HPR and GND to the iPod jack's tip, ring and sleeve; optional jack detect from the jack's switch contact to GPIO16 (pin 36)" src="../wiring/05-wired-audio.svg">
</picture>

This chapter brings back the iPod's own headphone jack. A small DAC board takes digital
audio from the Pi over I2S and drives your earbuds through the original jack on the top
edge. Bluetooth still works: you choose the output on the iPod or on the setup page.

Like chapters 4-7, this is done on the desk with the Pi outside the case.

## Why this DAC

| Part | Into 16-32 Ω earbuds |
|---|---|
| **Adafruit TLV320DAC3100, [#6309](https://www.adafruit.com/product/6309)** (used here) | Has a headphone amplifier. Adafruit: it "can connect directly to your 16Ω headphones". |
| Adafruit PCM5102, [#6250](https://www.adafruit.com/product/6250) | Line level only. Adafruit: "it cannot drive headphones ... no less than 1K ohm loads". |
| Adafruit UDA1334A, [#3678](https://www.adafruit.com/product/3678) | Line level, rated for a 3 kΩ load. Adafruit: 32 Ω headphones work but "you will get distortions". |

A USB DAC would need the Zero's only data port and doesn't fit in the case. PWM audio on
GPIO 12/13 or 18/19 is noisier and needs its own filter.

Raspberry Pi OS has no kernel driver for the TLV320DAC3100. The installer handles that:
the audio goes over the generic `i2s-dac` overlay, and a small program (`tlv320.py`, run at
boot by `spotifypod-dac.service`) sets up the DAC's clocks and headphone amplifier over
I2C. That's why the board needs two I2C wires and a reset wire as well as the three I2S
wires.

## You will need

* Adafruit TLV320DAC3100 I2S DAC, [#6309](https://www.adafruit.com/product/6309)
* the iPod's headphone jack board (it also carries the hold switch)
* 30 AWG wire in several colours, a multimeter, a 3.5 mm male-to-male cable

## 1. Find the jack's contacts

On the 4th-gen iPod the headphone jack, the hold switch and the piezo speaker sit on one
small board at the top of the case. An orange flex cable joined it to the logic board,
which this build doesn't use. To take the board out, remove its two T6 Torx screws and
lift it out ([iFixit guide 388](https://www.ifixit.com/Guide/iPod+4th+Generation+or+Photo+Headphone+Jack+Replacement/388)).

You solder the audio wires straight to the jack's pins on this board. The hold switch
keeps working (chapter 7 wires it to the PowerBoost), but the board is modified for good.
No pinout for this board has been published, so find the pins with a multimeter:

1. Plug one end of the 3.5 mm cable into the jack.
2. On the cable's free plug, the **tip** is left, the **ring** (the middle band) is right
   and the **sleeve** (the long part by the handle) is ground. With the multimeter on
   continuity, touch each one and find the jack pin that beeps. Write them down.
3. Optional, **jack detect**: unplug the cable and look for two jack pins that change
   (beep, then stop, or the other way round) when the plug goes in. Rockbox's iPod 4G port
   reads a headphone-detect line, so the jack probably has one `[MEASURE]`. If one of the two
   pins is the tip or ring pin, skip jack detect: that switch carries audio.

## 2. Wire the DAC to the Pi

Pins on the DAC board are as printed on it. Keep these wires short (under 10 cm): BCK is a
2.8 MHz clock.

| Pi physical pin | Pi signal | DAC pad | Wire |
|---|---|---|---|
| **4** | 5 V | VIN | red |
| **3** | GPIO 2 (I2C SDA) | SDA | blue |
| **5** | GPIO 3 (I2C SCL) | SCL | orange |
| **11** | GPIO 17 | RST | brown |
| **12** | GPIO 18 (I2S BCLK) | BCK | pink |
| **35** | GPIO 19 (I2S LRCLK) | WSEL | grey |
| **40** | GPIO 21 (I2S DOUT) | DIN | yellow |
| **34** | GND | GND | black |

![Harness: eight 30 AWG wires from the Pi to the DAC (red 5V pin 4 to VIN, blue pin 3 to SDA, orange pin 5 to SCL, brown pin 11 to RST, pink pin 12 to BCK, grey pin 35 to WSEL, yellow pin 40 to DIN, black pin 34 to GND); three from the DAC to the jack (white HPL to tip, red HPR to ring, black GND to sleeve); an optional light blue wire from pin 36 to the jack's detect contact](../wiring/harness-audio.svg)

The board takes 3.3-5 V on VIN and has its own 3.3 V regulator; feeding it from the 5 V rail
keeps the boost converter's ripple behind that regulator. Leave MCK, SPK+, SPK-, AIN1,
AIN2, IO, MIC and BIAS unconnected.

**Zero 2 W note:** the same pins; nothing changes.

## 3. Wire the DAC to the jack

| DAC pad | Jack pin (from step 1) | Wire |
|---|---|---|
| HPL | tip (left) | white |
| HPR | ring (right) | red |
| GND (any GND pad) | sleeve | black |
| | detect, optional: to Pi pin **36** (GPIO 16) | light blue |

HPL and HPR come through 100 µF capacitors on the board, so earbuds never see DC. For jack
detect, the switch's other pin goes to the sleeve pin.

Ground the sleeve through the DAC's GND, not the PowerBoost. On the same board, the hold
switch's ground side may already be joined to the sleeve `[MEASURE]`: check with the
multimeter. If it is, that's a second ground path, which can pick up boost-converter whine
(chapter 10 has the fixes).

## 4. Software

The installer did this in chapter 4: `WIRED_AUDIO=i2s` is the default. It:

* adds `dtparam=i2c_arm=on`, `dtoverlay=i2s-dac` and `gpio=17=op,dl` (DAC held in reset
  until it's set up) to `config.txt`, in a block marked `retro-ipod-spotify-revival audio`;
* installs `spotifypod-dac.service`, which resets the DAC and sets it up at boot, and ramps
  the headphone output down at shutdown;
* builds `click` so that pigpio times itself from the PWM block, leaving the PCM block to
  I2S;
* tells PipeWire to keep the DAC's clock running at 44.1 kHz (the DAC runs its own clock
  from it).

If you have jack detect, re-run the installer with its pin:

```bash
sudo JACK_DETECT_GPIO=16 bash install/install.sh
```

The iPod reads that pin with a pull-up. If the pin reads 1 (not 0) with a plug in, add
`JACK_PLUGGED_LEVEL=1`. Check by hand with `pinctrl lev 16`.

Reboot, then check the DAC:

```bash
aplay -l                                  # a card called sndrpirpidac
systemctl status spotifypod-dac --no-pager  # active (exited), "headphone output on, -20.1 dB"
```

### Loudness

Full volume on the wheel gives **-20 dB** at the jack (`WIRED_GAIN_DB`, set in the DAC's
analog stage), about right for sensitive earbuds `[MEASURE]`. For louder or quieter, re-run
the installer with a value from 0 (loudest) to -35:

```bash
sudo WIRED_GAIN_DB=-14 bash install/install.sh
```

To try a level without reinstalling: `sudo WIRED_GAIN_DB=-14 python3 /opt/spotifypod/bin/tlv320.py start`.

### Without Bluetooth: `AUDIO_BACKEND=alsa`

The default (`AUDIO_BACKEND=pulseaudio`) runs PipeWire, which can switch between the jack
and Bluetooth. If you only want the jack, `sudo AUDIO_BACKEND=alsa bash install/install.sh`
skips PipeWire for the iPod's user and writes `/etc/asound.conf`, where a `dmix` device lets
Spotify and Music on iPod share the DAC. That's the lightest option on the Zero W.

## 5. Choosing the output

* **On the iPod:** **Settings -> Output** lists **Headphones** and your paired Bluetooth
  devices. The active one is marked "(on)". Select one to switch; a paired device that
  isn't connected is connected first.
* **On the setup page** (`http://ipod.local`): the **Output** card does the same.
* **Automatic:** with no Bluetooth device connected, sound goes to the jack. Connecting a
  Bluetooth device switches to it, as before. With jack detect, plugging in switches to the
  jack and unplugging switches back to the last Bluetooth device.

Playing music now goes to the chosen output, whichever source plays it (Spotify or Music on
iPod). **Settings -> About** shows the active output.

**Check:** with earbuds in the iPod's jack, play something from Spotify: you hear it in the
earbuds, at a comfortable level at full volume. Pair a Bluetooth speaker on the setup page:
the sound moves to the speaker. Choose **Settings -> Output -> Headphones**: it moves back
to the earbuds. Then play a song from **Music on iPod** and it comes from the same output.

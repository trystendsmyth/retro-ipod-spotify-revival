#!/usr/bin/env bash
# Exercises install/bin/configure-audio.sh against fixture boot files, alone and
# together with configure-display.sh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
audio() { BOOTCFG="$T/config.txt" ASOUND_CONF="$T/asound.conf" bash "$ROOT/install/bin/configure-audio.sh" >/dev/null; }
display() { BOOTCFG="$T/config.txt" CMDLINE="$T/cmdline.txt" bash "$ROOT/install/bin/configure-display.sh" >/dev/null; }
blocks() { grep -c '^# >>> retro-ipod-spotify-revival audio' "$T/config.txt" || true; }

cp "$ROOT/tests/fixtures/config.txt" "$ROOT/tests/fixtures/cmdline.txt" "$T/"

# 1. fresh config.txt: one block with the DAC overlay, under [all]
WIRED_AUDIO=i2s audio
[[ "$(blocks)" == 1 ]] || fail "audio block missing"
grep -qx 'dtoverlay=i2s-dac' "$T/config.txt" || fail "DAC overlay missing"
tail -n 6 "$T/config.txt" | grep -qx '\[all\]' || fail "block not under [all]"
grep -qx 'dtparam=i2c_arm=on' "$T/config.txt" || fail "I2C not enabled"
grep -qx 'gpio=17=op,dl' "$T/config.txt" || fail "DAC not held in reset at boot"
grep -qx 'dtparam=audio=on' "$T/config.txt" || fail "stock dtparam=audio line changed"

# 2. re-run: identical file
cp "$T/config.txt" "$T/first.txt"
WIRED_AUDIO=i2s audio
cmp -s "$T/config.txt" "$T/first.txt" || fail "re-run changed config.txt"

# 3. with the composite display profile, in either order
DISPLAY_PROFILE=composite TV_NORM=NTSC display
WIRED_AUDIO=i2s audio
[[ "$(blocks)" == 1 ]] || fail "audio block duplicated (composite)"
grep -qx 'dtoverlay=vc4-kms-v3d,composite' "$T/config.txt" || fail "composite overlay lost"
[[ "$(grep -c '^dtoverlay=i2s-dac$' "$T/config.txt")" == 1 ]] || fail "DAC overlay duplicated"
DISPLAY_PROFILE=composite TV_NORM=NTSC display
grep -qx 'dtoverlay=i2s-dac' "$T/config.txt" || fail "display re-run removed the audio block"

# 4. with the st7789 profile (backlight moved off GPIO 18, which is I2S BCLK)
DISPLAY_PROFILE=st7789 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=27 display
WIRED_AUDIO=i2s audio
[[ "$(blocks)" == 1 ]] || fail "audio block duplicated (st7789)"
grep -q '^dtoverlay=mipi-dbi-spi' "$T/config.txt" || fail "st7789 block lost"
grep -qx 'dtoverlay=i2s-dac' "$T/config.txt" || fail "DAC overlay missing (st7789)"

# 5. audio disabled: block removed, display block kept
WIRED_AUDIO=none audio
[[ "$(blocks)" == 0 ]] || fail "audio block left behind"
grep -q -e 'i2s-dac' -e 'i2c_arm' -e '^gpio=17' "$T/config.txt" && fail "DAC lines left behind"
grep -q '^dtoverlay=mipi-dbi-spi' "$T/config.txt" || fail "WIRED_AUDIO=none removed the display block"
cp "$T/config.txt" "$T/none.txt"
WIRED_AUDIO=none audio
cmp -s "$T/config.txt" "$T/none.txt" || fail "re-run with none changed config.txt"

# 6. bad values rejected, file untouched
if WIRED_AUDIO=usb audio 2>/dev/null; then fail "bad WIRED_AUDIO accepted"; fi
if WIRED_AUDIO=i2s DAC_OVERLAY='x;rm' audio 2>/dev/null; then fail "bad DAC_OVERLAY accepted"; fi
cmp -s "$T/config.txt" "$T/none.txt" || fail "rejected run changed config.txt"
if WIRED_AUDIO=i2s DAC_RESET_GPIO=x audio 2>/dev/null; then fail "bad DAC_RESET_GPIO accepted"; fi
if WIRED_AUDIO=i2s JACK_DETECT_GPIO=x audio 2>/dev/null; then fail "bad JACK_DETECT_GPIO accepted"; fi

# 7. jack detect: pull-up set at boot
WIRED_AUDIO=i2s JACK_DETECT_GPIO=16 audio
grep -qx 'gpio=16=ip,pu' "$T/config.txt" || fail "jack detect pull-up missing"
WIRED_AUDIO=i2s audio
grep -q '^gpio=16=' "$T/config.txt" && fail "jack detect line left behind"

# 8. AUDIO_BACKEND=alsa: dmix on the DAC; pulseaudio removes it again
[[ -e "$T/asound.conf" ]] && fail "asound.conf written for pulseaudio"
WIRED_AUDIO=i2s AUDIO_BACKEND=alsa audio
grep -q 'type dmix' "$T/asound.conf" || fail "no dmix"
grep -q 'pcm "hw:CARD=sndrpirpidac,DEV=0"' "$T/asound.conf" || fail "dmix not on the DAC"
grep -q '__' "$T/asound.conf" && fail "unfilled placeholder"
WIRED_AUDIO=none AUDIO_BACKEND=alsa ALSA_CARD=Device audio
grep -q 'hw:CARD=Device,DEV=0' "$T/asound.conf" || fail "ALSA_CARD for a USB DAC"
if WIRED_AUDIO=none AUDIO_BACKEND=alsa ALSA_CARD='a b' audio 2>/dev/null; then fail "bad ALSA_CARD accepted"; fi
WIRED_AUDIO=i2s AUDIO_BACKEND=pulseaudio audio
[[ -e "$T/asound.conf" ]] && fail "asound.conf left for pulseaudio"

# 9. someone else's asound.conf is never touched
echo 'pcm.!default { type hw card 1 }' > "$T/asound.conf"
WIRED_AUDIO=i2s AUDIO_BACKEND=alsa audio 2>/dev/null
grep -qx 'pcm.!default { type hw card 1 }' "$T/asound.conf" || fail "foreign asound.conf overwritten"
WIRED_AUDIO=i2s AUDIO_BACKEND=pulseaudio audio
[[ -e "$T/asound.conf" ]] || fail "foreign asound.conf removed"
rm -f "$T/asound.conf"

# 10. asound.conf parses and "default" plays (dmix needs a real card: swap it for null)
if command -v aplay >/dev/null; then
  WIRED_AUDIO=i2s AUDIO_BACKEND=alsa audio
  sed -e '/^pcm.spotifypod_dmix {/,/^}/d' -e '/^ctl.!default {/,/^}/d' "$T/asound.conf" > "$T/chain.conf"
  printf 'pcm.spotifypod_dmix { type null }\n' >> "$T/chain.conf"
  head -c 17640 /dev/zero > "$T/silence.raw"
  ALSA_CONFIG_PATH="$T/chain.conf" aplay -q -D default -t raw -f S16_LE -c 2 -r 44100 "$T/silence.raw" \
    || fail "asound.conf default does not play"
fi
echo "configure-audio: all tests passed"

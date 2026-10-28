#!/usr/bin/env bash
# Exercises install/bin/check-pins.sh: valid pin maps pass, collisions are refused.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail() { echo "FAIL: $*" >&2; exit 1; }
check() { env CLICK_CLOCK_PIN=23 CLICK_HAPTIC_PIN=26 "$@" bash "$ROOT/install/bin/check-pins.sh"; }
ok() { check "$@" >/dev/null 2>&1 || fail "rejected: $*"; }
refused() { if check "$@" >/dev/null 2>&1; then fail "accepted: $*"; fi; }

# Defaults: composite and st7789, with and without wired audio
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=none
ok DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=27 WIRED_AUDIO=i2s
ok DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=24 RESET_GPIO=25 BL_GPIO= WIRED_AUDIO=i2s
ok DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=18 WIRED_AUDIO=none
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s JACK_DETECT_GPIO=16

# The st7789 backlight on the I2S bit clock gets its own message
msg="$(check DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=18 WIRED_AUDIO=i2s 2>&1 || true)"
grep -q 'BL_GPIO=18 is the I2S bit clock' <<<"${msg}" || fail "no BL_GPIO=18 message: ${msg}"

# Collisions
refused DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=25 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=27 WIRED_AUDIO=none
refused DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=10 RESET_GPIO=25 BL_GPIO=27 WIRED_AUDIO=none
refused DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=19 RESET_GPIO=25 BL_GPIO=27 WIRED_AUDIO=i2s
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=21 WIRED_AUDIO=i2s
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s JACK_DETECT_GPIO=20
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s JACK_DETECT_GPIO=26
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s JACK_DETECT_GPIO=17
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=3 WIRED_AUDIO=i2s
refused DISPLAY_PROFILE=st7789 CLICK_DATA_PIN=5 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=17 WIRED_AUDIO=i2s
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=3 WIRED_AUDIO=none
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=i2s DAC_RESET_GPIO=22 JACK_DETECT_GPIO=17
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=25 WIRED_AUDIO=none JACK_DETECT_GPIO=16
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=40 WIRED_AUDIO=none
refused DISPLAY_PROFILE=composite CLICK_DATA_PIN=x WIRED_AUDIO=none

# Composite never claims the SPI or display pins
ok DISPLAY_PROFILE=composite CLICK_DATA_PIN=10 DC_GPIO=23 WIRED_AUDIO=none
echo "check-pins: all tests passed"

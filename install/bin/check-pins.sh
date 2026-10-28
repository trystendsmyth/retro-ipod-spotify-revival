#!/usr/bin/env bash
# Refuse pin maps where two parts of the build share a GPIO. Called by install/install.sh
# before anything is installed; prints the claimed pins on success.
#
# Env (BCM GPIO numbers; empty = not used):
#   CLICK_CLOCK_PIN CLICK_DATA_PIN CLICK_HAPTIC_PIN
#   DISPLAY_PROFILE  composite | st7789 (DC_GPIO RESET_GPIO BL_GPIO and SPI0 8-11)
#   WIRED_AUDIO      i2s (claims I2S 18-21, I2C 2-3 and DAC_RESET_GPIO) | none
#   DAC_RESET_GPIO   the DAC's RST line (default 17)
#   JACK_DETECT_GPIO optional jack plug-detect input
set -euo pipefail

declare -A OWNER=()
fail() { echo "ERROR: $*" >&2; exit 1; }

claim() {
  local gpio="$1" who="$2"
  [[ -z "${gpio}" ]] && return 0
  [[ "${gpio}" =~ ^[0-9]+$ ]] && (( gpio <= 27 )) || fail "${who}: '${gpio}' is not a header GPIO (0-27)"
  if [[ -n "${OWNER[${gpio}]:-}" ]]; then
    fail "GPIO ${gpio} is used by both ${OWNER[${gpio}]} and ${who}. Adjust the pin variables to match your wiring."
  fi
  OWNER[${gpio}]="${who}"
}

if [[ "${WIRED_AUDIO:-none}" == "i2s" && "${DISPLAY_PROFILE:-composite}" == "st7789" && "${BL_GPIO:-}" == "18" ]]; then
  fail "BL_GPIO=18 is the I2S bit clock for wired audio. Wire the display backlight to GPIO 27
       (pin 13) and set BL_GPIO=27, or tie it to 3.3 V and set BL_GPIO=\"\"."
fi

claim "${CLICK_CLOCK_PIN:-}" "click wheel CLOCK"
claim "${CLICK_DATA_PIN:-}" "click wheel DATA"
claim "${CLICK_HAPTIC_PIN:-}" "haptic motor"
if [[ "${DISPLAY_PROFILE:-composite}" == "st7789" ]]; then
  claim 8 "SPI0 CE0 (display)"
  claim 9 "SPI0 MISO (display)"
  claim 10 "SPI0 MOSI (display)"
  claim 11 "SPI0 SCLK (display)"
  claim "${DC_GPIO:-}" "display DC"
  claim "${RESET_GPIO:-}" "display RESET"
  claim "${BL_GPIO:-}" "display backlight"
fi
if [[ "${WIRED_AUDIO:-none}" == "i2s" ]]; then
  claim 18 "I2S BCLK (wired audio)"
  claim 19 "I2S LRCLK (wired audio)"
  # The overlay takes all four PCM pins, including DIN, which this build doesn't wire.
  claim 20 "I2S DIN (taken by the DAC overlay)"
  claim 21 "I2S DOUT (wired audio)"
  claim 2 "I2C SDA (DAC setup)"
  claim 3 "I2C SCL (DAC setup)"
  claim "${DAC_RESET_GPIO:-17}" "DAC reset"
  claim "${JACK_DETECT_GPIO:-}" "jack detect"
elif [[ -n "${JACK_DETECT_GPIO:-}" ]]; then
  fail "JACK_DETECT_GPIO needs WIRED_AUDIO=i2s"
fi

for gpio in $(printf '%s\n' "${!OWNER[@]}" | sort -n); do
  printf '    GPIO %-2s  %s\n' "${gpio}" "${OWNER[${gpio}]}"
done

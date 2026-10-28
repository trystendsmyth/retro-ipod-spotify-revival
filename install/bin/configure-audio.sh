#!/usr/bin/env bash
# Wired audio for retro-ipod-spotify-revival: the DAC's block in config.txt and, for
# AUDIO_BACKEND=alsa, /etc/asound.conf. Called by install/install.sh; safe to re-run
# (it replaces its own block and file).
#
# The DAC is a TLV320DAC3100 (Adafruit #6309): audio over I2S (the generic i2s-dac
# overlay), set up over I2C by tlv320.py, which needs I2C on and the codec's RESET
# line held low from boot.
#
# Env:
#   WIRED_AUDIO       i2s (default) | none (removes the block)
#   AUDIO_BACKEND     pulseaudio (default; asound.conf removed) | alsa (asound.conf written)
#   DAC_OVERLAY       device tree overlay for the I2S side, default i2s-dac
#   DAC_RESET_GPIO    BCM GPIO on the DAC's RST pin, default 17
#   ALSA_CARD         card for asound.conf, default sndrpirpidac (i2s) or 0 (none)
#   JACK_DETECT_GPIO  optional: jack plug-detect input, pulled up at boot
#   BOOTCFG           override config.txt (default: /boot/firmware/... then /boot/...)
#   ASOUND_CONF       override /etc/asound.conf
#   TEMPLATE_DIR      where asound.conf.template lives (default: ../config)
#
# Pins: I2S on GPIO 18 (BCLK), 19 (LRCLK), 21 (DOUT); I2C1 on GPIO 2 (SDA), 3 (SCL).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${TEMPLATE_DIR:-${SCRIPT_DIR}/../config}"
WIRED_AUDIO="${WIRED_AUDIO:-i2s}"
AUDIO_BACKEND="${AUDIO_BACKEND:-pulseaudio}"
DAC_OVERLAY="${DAC_OVERLAY:-i2s-dac}"
DAC_RESET_GPIO="${DAC_RESET_GPIO:-17}"
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  ALSA_CARD="${ALSA_CARD:-sndrpirpidac}"
else
  ALSA_CARD="${ALSA_CARD:-0}"
fi
JACK_DETECT_GPIO="${JACK_DETECT_GPIO:-}"
ASOUND_CONF="${ASOUND_CONF:-/etc/asound.conf}"
MARKER="# retro-ipod-spotify-revival: written by install/install.sh"

case "${WIRED_AUDIO}" in
  i2s|none) ;;
  *) echo "ERROR: WIRED_AUDIO must be 'i2s' or 'none' (got '${WIRED_AUDIO}')" >&2; exit 1 ;;
esac
case "${AUDIO_BACKEND}" in
  pulseaudio|alsa) ;;
  *) echo "ERROR: AUDIO_BACKEND must be 'pulseaudio' or 'alsa' (got '${AUDIO_BACKEND}')" >&2; exit 1 ;;
esac
if [[ ! "${DAC_OVERLAY}" =~ ^[a-z0-9-]+$ ]]; then
  echo "ERROR: DAC_OVERLAY '${DAC_OVERLAY}' is not an overlay name" >&2; exit 1
fi
if [[ ! "${ALSA_CARD}" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "ERROR: ALSA_CARD '${ALSA_CARD}' is not a card name or number (see aplay -l)" >&2; exit 1
fi
if [[ ! "${DAC_RESET_GPIO}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: DAC_RESET_GPIO must be a BCM GPIO number (got '${DAC_RESET_GPIO}')" >&2; exit 1
fi
if [[ -n "${JACK_DETECT_GPIO}" && ! "${JACK_DETECT_GPIO}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: JACK_DETECT_GPIO must be a BCM GPIO number (got '${JACK_DETECT_GPIO}')" >&2; exit 1
fi

# --- config.txt
if [[ -z "${BOOTCFG:-}" ]]; then
  for c in /boot/firmware/config.txt /boot/config.txt; do
    [[ -f "${c}" ]] && { BOOTCFG="${c}"; break; }
  done
fi
if [[ -n "${BOOTCFG:-}" && -f "${BOOTCFG}" ]]; then
  sed -i '/^# >>> retro-ipod-spotify-revival audio/,/^# <<< retro-ipod-spotify-revival audio/d' "${BOOTCFG}"
  # Drop trailing blank lines so re-runs don't add one each time.
  sed -i -e ':a' -e '/^\n*$/{$d;N;ba' -e '}' "${BOOTCFG}"
  if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
    {
      echo ""
      echo "# >>> retro-ipod-spotify-revival audio (${WIRED_AUDIO}) - managed by install/bin/configure-audio.sh"
      # Settings after a conditional section like [cm4] would only apply to that model.
      echo "[all]"
      echo "dtparam=i2c_arm=on"
      echo "dtoverlay=${DAC_OVERLAY}"
      # DAC in reset (silent) until spotifypod-dac.service sets it up
      echo "gpio=${DAC_RESET_GPIO}=op,dl"
      if [[ -n "${JACK_DETECT_GPIO}" ]]; then
        echo "gpio=${JACK_DETECT_GPIO}=ip,pu"
      fi
      echo "# <<< retro-ipod-spotify-revival audio"
    } >> "${BOOTCFG}"
  fi
  echo "configure-audio: updated ${BOOTCFG} (WIRED_AUDIO=${WIRED_AUDIO})"
elif [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  echo "WARN: no config.txt found; add dtoverlay=${DAC_OVERLAY} under [all] by hand" >&2
fi

# --- /etc/asound.conf (ours only: a file without the marker is left alone)
ours=0
if [[ ! -e "${ASOUND_CONF}" ]] || grep -qF "${MARKER}" "${ASOUND_CONF}"; then
  ours=1
fi
if [[ "${AUDIO_BACKEND}" == "alsa" ]]; then
  if [[ "${ours}" == 1 ]]; then
    sed -e "s/__CARD__/${ALSA_CARD}/g" "${TEMPLATE_DIR}/asound.conf.template" > "${ASOUND_CONF}"
    echo "configure-audio: wrote ${ASOUND_CONF} (card ${ALSA_CARD})"
  else
    echo "WARN: ${ASOUND_CONF} was not written by this installer; left as is." >&2
    echo "      Move it away and re-run for go-librespot and MPD to share the card." >&2
  fi
elif [[ "${ours}" == 1 && -e "${ASOUND_CONF}" ]]; then
  # PipeWire owns the card; pipewire-alsa routes ALSA's default to it.
  rm -f "${ASOUND_CONF}"
  echo "configure-audio: removed ${ASOUND_CONF}"
fi

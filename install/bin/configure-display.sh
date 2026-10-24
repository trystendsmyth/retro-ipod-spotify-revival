#!/usr/bin/env bash
# Write the display section of config.txt / cmdline.txt for spot-revival.
# Called by install/install.sh; safe to re-run (it replaces its own block).
#
# Env:
#   DISPLAY_PROFILE  composite (default) | st7789
#   TV_NORM          composite TV standard, default NTSC (NTSC, NTSC-J, NTSC-443, PAL, PAL-M, PAL-N, PAL60, SECAM)
#   DC_GPIO RESET_GPIO BL_GPIO   st7789 only
#   BOOTCFG CMDLINE  override file paths (default: /boot/firmware/... then /boot/...)
#   SNIPPET_DIR      where the *.txt.snippet files live (default: ../config)
#
# Composite settings follow the Raspberry Pi documentation, "config.txt > Video
# options > Composite video mode": dtoverlay=vc4-kms-v3d,composite and
# vc4.tv_norm=<mode> on the kernel command line.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SNIPPET_DIR="${SNIPPET_DIR:-${SCRIPT_DIR}/../config}"
DISPLAY_PROFILE="${DISPLAY_PROFILE:-composite}"
TV_NORM="${TV_NORM:-NTSC}"
DC_GPIO="${DC_GPIO:-24}"
RESET_GPIO="${RESET_GPIO:-25}"
BL_GPIO="${BL_GPIO-18}"

case "${TV_NORM}" in
  NTSC|NTSC-J|NTSC-443|PAL|PAL-M|PAL-N|PAL60|SECAM) ;;
  *) echo "ERROR: unsupported TV_NORM '${TV_NORM}'" >&2; exit 1 ;;
esac

if [[ -z "${BOOTCFG:-}" ]]; then
  for c in /boot/firmware/config.txt /boot/config.txt; do
    [[ -f "${c}" ]] && { BOOTCFG="${c}"; break; }
  done
fi
if [[ -z "${CMDLINE:-}" ]]; then
  for c in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
    [[ -f "${c}" ]] && { CMDLINE="${c}"; break; }
  done
fi

if [[ -n "${BOOTCFG:-}" && -f "${BOOTCFG}" ]]; then
  # Remove blocks from earlier runs (ours, and the upstream oliver-vv installer's).
  sed -i '/^# >>> spot-revival display/,/^# <<< spot-revival display/d' "${BOOTCFG}"
  sed -i '/^# --- \(iPod\|sPot\) \/ Spotifypod display/,/^enable_tvout=0/d' "${BOOTCFG}"

  {
    echo ""
    echo "# >>> spot-revival display (${DISPLAY_PROFILE}) - managed by install/bin/configure-display.sh"
    # Settings after a conditional section like [cm4] would only apply to that model.
    echo "[all]"
    if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
      if [[ -n "${BL_GPIO}" ]]; then BL_PARAM=",backlight-gpio=${BL_GPIO}"; else BL_PARAM=""; fi
      sed -e "s/__DC_GPIO__/${DC_GPIO}/g" -e "s/__RESET_GPIO__/${RESET_GPIO}/g" -e "s/__BL_PARAM__/${BL_PARAM}/g" \
        "${SNIPPET_DIR}/spotifypod-config.txt.snippet"
    else
      cat "${SNIPPET_DIR}/composite-config.txt.snippet"
    fi
    echo "# <<< spot-revival display"
  } > "${BOOTCFG}.spot-block"

  if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
    # SPI panel is the only display: comment out the KMS driver line(s).
    sed -i -E 's/^(dtoverlay=vc4-kms-v3d.*)$/# \1  # disabled by spot-revival for the SPI LCD/' "${BOOTCFG}"
  else
    # Composite needs KMS with ",composite": drop other vc4-kms-v3d lines (including ones a
    # previous st7789 install commented out); our block adds the right one.
    sed -i -E '/^(# )?dtoverlay=vc4-kms-v3d/d' "${BOOTCFG}"
  fi
  cat "${BOOTCFG}.spot-block" >> "${BOOTCFG}"
  rm -f "${BOOTCFG}.spot-block"
  echo "configure-display: updated ${BOOTCFG}"
else
  echo "WARN: no config.txt found; copy the matching install/config/*.snippet by hand" >&2
fi

if [[ -n "${CMDLINE:-}" && -f "${CMDLINE}" ]]; then
  # cmdline.txt must stay a single line.
  sed -i -E 's/ ?vc4\.tv_norm=[^ ]*//g' "${CMDLINE}"
  if [[ "${DISPLAY_PROFILE}" == "composite" ]]; then
    sed -i -E "1 s/\$/ vc4.tv_norm=${TV_NORM}/" "${CMDLINE}"
  fi
  echo "configure-display: updated ${CMDLINE}"
fi

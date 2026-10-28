#!/usr/bin/env bash
# retro-ipod-spotify-revival installer for Raspberry Pi OS Lite (Bookworm or newer).
#   32-bit OS: Pi Zero W / Zero (ARMv6)      64-bit OS: Pi Zero 2 W (also runs on Pi 3/4)
# Run as root on the Pi:  sudo bash install/install.sh
#
# Derived from oliver-vv/Spotify-iPod-Classic (Apache-2.0). retro-ipod-spotify-revival adds:
# DISPLAY_PROFILE=composite (original sPot Adafruit #911 TV display, default),
# ARMv6 support, a pinned + checksummed go-librespot download, pin defines
# passed to the compiler instead of editing click.c, MPD for music files on the SD
# card (LOCAL_MUSIC), comitup from its own repo (COMITUP_SOURCE) and wired audio
# through an I2S DAC (WIRED_AUDIO). See NOTICE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# --- Tunables (override via env) ---
INSTALL_ROOT="${INSTALL_ROOT:-/opt/spotifypod}"
DATA_DIR="${DATA_DIR:-/var/lib/spotifypod}"
CONFIG_DIR="${CONFIG_DIR:-/etc/spotifypod}"
SPOTIFYPOD_USER="${SPOTIFYPOD_USER:-spotifypod}"
# Audio: pulseaudio (PipeWire: headphone jack and Bluetooth, switchable; default) or
# alsa (one wired DAC, no Bluetooth, lightest on the Zero W)
AUDIO_BACKEND="${AUDIO_BACKEND:-pulseaudio}"
# Wired headphones: i2s = TLV320DAC3100 DAC (Adafruit #6309) on I2S into the iPod's
# headphone jack (docs/guide/06b-wired-audio.md); none = no DAC (Bluetooth only, or a
# USB DAC with AUDIO_BACKEND=alsa).
WIRED_AUDIO="${WIRED_AUDIO:-i2s}"
# Headphone level at full wheel volume, in dB (0 to -35), set in the DAC's analog stage.
WIRED_GAIN_DB="${WIRED_GAIN_DB:--20}"
# The DAC's RST pin (BCM GPIO). I2S is on GPIO 18/19/21 and I2C on GPIO 2/3, both fixed.
DAC_RESET_GPIO="${DAC_RESET_GPIO:-17}"
# ALSA card for AUDIO_BACKEND=alsa (aplay -l). With WIRED_AUDIO=none it is card 0; set
# ALSA_CARD to your USB DAC's name if that's wrong.
DAC_OVERLAY="i2s-dac"
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  ALSA_CARD="${ALSA_CARD:-sndrpirpidac}"
else
  ALSA_CARD="${ALSA_CARD:-0}"
fi
# Optional headphone-jack plug detect (BCM GPIO, pulled up) and the level read when a
# plug is in. Empty = no jack detect.
JACK_DETECT_GPIO="${JACK_DETECT_GPIO:-}"
JACK_PLUGGED_LEVEL="${JACK_PLUGGED_LEVEL:-0}"
# Display: "composite" = original sPot build (Adafruit #911 NTSC/PAL TFT on the
# Pi's composite output); "st7789" = Ricardo Sappia's Waveshare 2" SPI build.
DISPLAY_PROFILE="${DISPLAY_PROFILE:-composite}"
# Composite TV standard (composite profile only): NTSC, PAL, PAL60, NTSC-J, ...
TV_NORM="${TV_NORM:-NTSC}"
# Display GPIOs for mipi-dbi-spi (st7789 profile only). DC and RESET follow Ricardo
# Sappia's Waveshare build (DC=24 / pin 18, RESET=25 / pin 22). His backlight was on
# GPIO 18, which wired audio needs for I2S, so the default is GPIO 27 / pin 13.
# Set BL_GPIO="" if your backlight is hard-wired to 3.3V instead.
DC_GPIO="${DC_GPIO:-24}"
RESET_GPIO="${RESET_GPIO:-25}"
BL_GPIO="${BL_GPIO-27}"
# Click wheel DATA pin (BCM), passed to the compiler as -DDATA_PIN=... (click.c is not edited).
# Original sPot (composite) wiring uses 25; the st7789 profile defaults to 5 because
# GPIO 25 is that display's RESET line.
if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
  CLICK_DATA_PIN="${CLICK_DATA_PIN:-5}"
else
  CLICK_DATA_PIN="${CLICK_DATA_PIN:-25}"
fi
CLICK_CLOCK_PIN=23
CLICK_HAPTIC_PIN=26
# go-librespot is pinned and checksum-verified. To upgrade, change the version and
# both SHA256 values (computed from the release .tar.gz assets) together.
GO_LIBRESPOT_VERSION="${GO_LIBRESPOT_VERSION:-v0.10.4}"
GO_LIBRESPOT_SHA256_arm64="${GO_LIBRESPOT_SHA256_arm64:-d8b3d39e107ee140a8ad82924ef3decded4bfcbaceec680dd8142beda2403693}"
GO_LIBRESPOT_SHA256_armv6_rpi="${GO_LIBRESPOT_SHA256_armv6_rpi:-941645d28c256b152dd6169ddf5df439fa6ae973833255b530b0fcaab0577110}"
HOSTNAME_VALUE="${HOSTNAME_VALUE:-ipod}"
# comitup source: upstream (comitup's own apt repo) or debian (distribution package).
COMITUP_SOURCE="${COMITUP_SOURCE:-upstream}"
COMITUP_APT_SOURCE_URL="https://davesteele.github.io/comitup/deb/davesteele-comitup-apt-source_1.3_all.deb"
COMITUP_APT_SOURCE_SHA256="6620d256af8d21b05782d77039150351785d596b0f3faee7154245d76dd19114"
# Music files on the SD card, played by MPD ("Music on iPod"). LOCAL_MUSIC=0 turns it off.
LOCAL_MUSIC="${LOCAL_MUSIC:-1}"
MUSIC_DIR="${MUSIC_DIR:-/srv/music}"
MPD_PORT="${MPD_PORT:-6600}"
# Login account that copies music in (owns MUSIC_DIR): the user who ran sudo, else uid 1000.
MUSIC_USER="${MUSIC_USER:-${SUDO_USER:-}}"
if [[ -z "${MUSIC_USER}" || "${MUSIC_USER}" == "root" ]]; then
  MUSIC_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

case "${DISPLAY_PROFILE}" in
  composite|st7789) ;;
  *) echo "ERROR: DISPLAY_PROFILE must be 'composite' or 'st7789' (got '${DISPLAY_PROFILE}')" >&2; exit 1 ;;
esac
case "${AUDIO_BACKEND}" in
  pulseaudio|alsa) ;;
  *) echo "ERROR: AUDIO_BACKEND must be 'pulseaudio' or 'alsa' (got '${AUDIO_BACKEND}')" >&2; exit 1 ;;
esac
case "${WIRED_AUDIO}" in
  i2s|none) ;;
  *) echo "ERROR: WIRED_AUDIO must be 'i2s' or 'none' (got '${WIRED_AUDIO}')" >&2; exit 1 ;;
esac
if [[ ! "${WIRED_GAIN_DB}" =~ ^-?[0-9]+(\.[0-9]+)?$ ]] || awk -v d="${WIRED_GAIN_DB}" 'BEGIN{exit !(d > 0 || d < -35)}'; then
  echo "ERROR: WIRED_GAIN_DB must be a number of dB from 0 to -35 (got '${WIRED_GAIN_DB}')" >&2; exit 1
fi
case "${JACK_PLUGGED_LEVEL}" in
  0|1) ;;
  *) echo "ERROR: JACK_PLUGGED_LEVEL must be 0 or 1 (got '${JACK_PLUGGED_LEVEL}')" >&2; exit 1 ;;
esac
case "${LOCAL_MUSIC}" in
  0|1) ;;
  *) echo "ERROR: LOCAL_MUSIC must be 0 or 1 (got '${LOCAL_MUSIC}')" >&2; exit 1 ;;
esac
case "${COMITUP_SOURCE}" in
  upstream|debian) ;;
  *) echo "ERROR: COMITUP_SOURCE must be 'upstream' or 'debian' (got '${COMITUP_SOURCE}')" >&2; exit 1 ;;
esac

EFFECTIVE_DATA_PIN="${CLICK_DATA_PIN}"
# --- Pin sanity check: no GPIO used twice (click wheel, display, wired audio) ---
if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
  DISPLAY_PINS=(DC_GPIO="${DC_GPIO}" RESET_GPIO="${RESET_GPIO}" BL_GPIO="${BL_GPIO}")
else
  DISPLAY_PINS=()
fi
env CLICK_CLOCK_PIN="${CLICK_CLOCK_PIN}" CLICK_DATA_PIN="${EFFECTIVE_DATA_PIN}" CLICK_HAPTIC_PIN="${CLICK_HAPTIC_PIN}" \
  DISPLAY_PROFILE="${DISPLAY_PROFILE}" "${DISPLAY_PINS[@]}" \
  WIRED_AUDIO="${WIRED_AUDIO}" DAC_RESET_GPIO="${DAC_RESET_GPIO}" JACK_DETECT_GPIO="${JACK_DETECT_GPIO}" \
  bash "${SCRIPT_DIR}/bin/check-pins.sh" >/dev/null

echo "==> Pin map"
echo "    click wheel : clock=${CLICK_CLOCK_PIN} data=${EFFECTIVE_DATA_PIN} haptic=${CLICK_HAPTIC_PIN}"
if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
  echo "    display     : st7789 dc=${DC_GPIO} reset=${RESET_GPIO} backlight=${BL_GPIO:-<hard-wired>} spi0 (mosi=10 sclk=11 ce0=8)"
else
  echo "    display     : composite (${TV_NORM}) on the TV pad / AV jack"
fi
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  echo "    wired audio : TLV320DAC3100 i2s bclk=18 lrclk=19 dout=21, i2c sda=2 scl=3, reset=${DAC_RESET_GPIO}, jack-detect=${JACK_DETECT_GPIO:-<none>}"
else
  echo "    wired audio : none"
fi

echo "==> Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  python3 python3-venv python3-pip python3-tk python3-pil.imagetk \
  xserver-xorg-core xserver-xorg-video-fbdev xserver-xorg-legacy xinit x11-xserver-utils \
  network-manager avahi-daemon polkitd \
  curl ca-certificates unzip rsync file fonts-dejavu-core \
  pipewire pipewire-audio pipewire-alsa pipewire-pulse wireplumber dbus-user-session pulseaudio-utils \
  libspa-0.2-bluetooth bluez \
  libogg-dev libvorbis-dev libflac-dev libmpg123-dev libasound2-dev libpulse-dev \
  gcc make
# (the *-dev packages above pull in the shared libraries the prebuilt go-librespot
#  binary links against: libvorbis/libogg/libFLAC/libmpg123/libasound/libpulse.
#  Runtime package names change between Debian releases; the -dev names do not.)

# pigpio (used by click.c) was dropped from the Raspberry Pi OS repos in Trixie.
# Use the apt package if it exists (Bookworm), otherwise build v79 from source.
PIGPIO_VERSION="${PIGPIO_VERSION:-79}"
if ! apt-get install -y libpigpio-dev 2>/dev/null; then
  if [[ -f /usr/local/include/pigpio.h && -f /usr/local/lib/libpigpio.so.1 ]]; then
    echo "==> pigpio already installed under /usr/local"
  else
    echo "==> Building pigpio v${PIGPIO_VERSION} from source (not packaged on this OS)"
    PIGPIO_TMP="$(mktemp -d)"
    curl -fsSL "https://github.com/joan2937/pigpio/archive/refs/tags/v${PIGPIO_VERSION}.tar.gz" \
      | tar -xz -C "${PIGPIO_TMP}"
    make -C "${PIGPIO_TMP}/pigpio-${PIGPIO_VERSION}" -j"$(nproc)" libpigpio.so
    # Install only the C library + header. `make install` also runs
    # `python3 setup.py install`, which fails on Trixie (PEP 668).
    install -m 644 "${PIGPIO_TMP}/pigpio-${PIGPIO_VERSION}/pigpio.h" /usr/local/include/
    install -m 755 "${PIGPIO_TMP}/pigpio-${PIGPIO_VERSION}/libpigpio.so.1" /usr/local/lib/
    ln -sf /usr/local/lib/libpigpio.so.1 /usr/local/lib/libpigpio.so
    ldconfig
    rm -rf "${PIGPIO_TMP}"
  fi
fi

# Comitup (Wi-Fi setup hotspot). COMITUP_SOURCE=upstream (default) adds comitup's own
# apt repo via its apt-source package, pinned by SHA256: it has the current comitup and
# python3-networkmanager for Bookworm and Trixie. COMITUP_SOURCE=debian uses the
# distribution package only.
if [[ "${COMITUP_SOURCE}" == "upstream" ]]; then
  echo "==> comitup apt source (${COMITUP_APT_SOURCE_URL})"
  CT_TMP="$(mktemp -d)"
  curl -fsSL -o "${CT_TMP}/comitup-apt-source.deb" "${COMITUP_APT_SOURCE_URL}"
  if echo "${COMITUP_APT_SOURCE_SHA256}  ${CT_TMP}/comitup-apt-source.deb" | sha256sum -c -; then
    dpkg -i "${CT_TMP}/comitup-apt-source.deb"
    apt-get update
  else
    echo "WARN: comitup apt-source checksum mismatch; falling back to the distribution package" >&2
  fi
  rm -rf "${CT_TMP}"
elif dpkg -s davesteele-comitup-apt-source >/dev/null 2>&1; then
  # Switching to debian: drop the repo an earlier run added (an installed comitup stays,
  # apt does not downgrade it).
  echo "==> Removing comitup apt source (COMITUP_SOURCE=debian)"
  apt-get purge -y davesteele-comitup-apt-source
  apt-get update
fi
if ! apt-get install -y comitup; then
  echo "WARN: comitup could not be installed; no setup hotspot. Configure Wi-Fi in Raspberry Pi Imager." >&2
fi

echo "==> Creating user ${SPOTIFYPOD_USER}"
if ! id -u "${SPOTIFYPOD_USER}" >/dev/null 2>&1; then
  useradd --system --home "${DATA_DIR}" --shell /usr/sbin/nologin \
    --groups audio,video "${SPOTIFYPOD_USER}" || true
fi
usermod -aG audio,video "${SPOTIFYPOD_USER}" 2>/dev/null || true
getent group bluetooth >/dev/null && usermod -aG bluetooth "${SPOTIFYPOD_USER}" 2>/dev/null || true
# gpio: read the jack-detect pin (pinctrl, /dev/gpiomem)
getent group gpio >/dev/null && usermod -aG gpio "${SPOTIFYPOD_USER}" 2>/dev/null || true
SPOTIFYPOD_UID="$(id -u "${SPOTIFYPOD_USER}")"
# Start a systemd --user instance for this user at boot (pipewire, wireplumber,
# pipewire-pulse live there), independent of any login session.
loginctl enable-linger "${SPOTIFYPOD_USER}" 2>/dev/null || true

echo "==> Layout under ${INSTALL_ROOT}"
mkdir -p "${INSTALL_ROOT}/bin" "${INSTALL_ROOT}/frontend" "${INSTALL_ROOT}/portal" \
  "${DATA_DIR}/go-librespot" "${CONFIG_DIR}" /lib/firmware /etc/X11/xorg.conf.d
chown -R "${SPOTIFYPOD_USER}:${SPOTIFYPOD_USER}" "${DATA_DIR}"

# Sync application code
rsync -a --delete \
  --exclude '__pycache__' --exclude '.cache' --exclude '*.pyc' --exclude '.env' \
  "${REPO_ROOT}/frontend/" "${INSTALL_ROOT}/frontend/"
rsync -a --delete \
  --exclude '__pycache__' --exclude '*.pyc' \
  "${REPO_ROOT}/portal/" "${INSTALL_ROOT}/portal/"

install -m 755 "${SCRIPT_DIR}/config/xinitrc" "${INSTALL_ROOT}/xinitrc"
install -m 755 "${SCRIPT_DIR}/bin/select-lcd-fb.sh" "${INSTALL_ROOT}/bin/select-lcd-fb.sh"
chown -R "${SPOTIFYPOD_USER}:${SPOTIFYPOD_USER}" "${INSTALL_ROOT}/frontend" "${INSTALL_ROOT}/portal"

echo "==> Python venv"
python3 -m venv --system-site-packages "${INSTALL_ROOT}/venv"
"${INSTALL_ROOT}/venv/bin/pip" install --upgrade pip
"${INSTALL_ROOT}/venv/bin/pip" install -r "${INSTALL_ROOT}/frontend/requirements.txt"
# Portal shares the same venv
setcap 'cap_net_bind_service=+ep' "${INSTALL_ROOT}/venv/bin/python3" 2>/dev/null || \
  echo "WARN: setcap failed; portal may need to run as root or use authbind for port 80"

echo "==> Compile click wheel binary"
# With the I2S DAC, pigpio must leave the PCM peripheral alone (see click.c).
CLICK_CFLAGS=()
[[ "${WIRED_AUDIO}" == "i2s" ]] && CLICK_CFLAGS+=(-DI2S_AUDIO)
gcc -Wall -pthread -O2 -I/usr/local/include -L/usr/local/lib "${CLICK_CFLAGS[@]}" \
  -DCLOCK_PIN="${CLICK_CLOCK_PIN}" -DDATA_PIN="${CLICK_DATA_PIN}" -DHAPTIC_PIN="${CLICK_HAPTIC_PIN}" \
  -o "${INSTALL_ROOT}/bin/click" "${REPO_ROOT}/clickwheel/click.c" -lpigpio -lrt
chmod 755 "${INSTALL_ROOT}/bin/click"

echo "==> Download go-librespot ${GO_LIBRESPOT_VERSION}"
ARCH="$(uname -m)"
case "${ARCH}" in
  aarch64|arm64) GL_VARIANT="arm64";     GL_SHA="${GO_LIBRESPOT_SHA256_arm64}" ;;
  # 32-bit Raspberry Pi OS (Zero W, Zero, Pi 1, or a 32-bit OS on a Pi 3/4).
  # armv6_rpi is built for ARMv6 without Thumb; it also runs on newer cores in 32-bit mode.
  armv6l|armv7l) GL_VARIANT="armv6_rpi"; GL_SHA="${GO_LIBRESPOT_SHA256_armv6_rpi}" ;;
  *) echo "ERROR: unsupported CPU architecture ${ARCH}" >&2; exit 1 ;;
esac
GL_URL="https://github.com/devgianlu/go-librespot/releases/download/${GO_LIBRESPOT_VERSION}/go-librespot_linux_${GL_VARIANT}.tar.gz"
TMP="$(mktemp -d)"
echo "    ${GL_URL}"
curl -fsSL -o "${TMP}/gl.tar.gz" "${GL_URL}"
if ! echo "${GL_SHA}  ${TMP}/gl.tar.gz" | sha256sum -c -; then
  echo "ERROR: go-librespot checksum mismatch. If you changed GO_LIBRESPOT_VERSION, update the SHA256 values too." >&2
  exit 1
fi
tar -xzf "${TMP}/gl.tar.gz" -C "${TMP}"
install -m 755 "${TMP}/go-librespot" "${INSTALL_ROOT}/bin/go-librespot"
if ldd "${INSTALL_ROOT}/bin/go-librespot" 2>/dev/null | grep -q 'not found'; then
  echo "WARN: go-librespot is missing shared libraries and will not start:"
  ldd "${INSTALL_ROOT}/bin/go-librespot" | grep 'not found'
fi
rm -rf "${TMP}"

echo "==> go-librespot config"
if [[ "${AUDIO_BACKEND}" == "pulseaudio" ]]; then
  PULSE_SOCKET="/run/user/${SPOTIFYPOD_UID}/pulse/native"
else
  PULSE_SOCKET=""
fi
sed -e "s/__AUDIO_BACKEND__/${AUDIO_BACKEND}/g" \
    -e "s|__PULSE_SOCKET__|${PULSE_SOCKET}|g" \
  "${SCRIPT_DIR}/config/go-librespot.yml.template" \
  > "${DATA_DIR}/go-librespot/config.yml"
chown -R "${SPOTIFYPOD_USER}:${SPOTIFYPOD_USER}" "${DATA_DIR}/go-librespot"

echo "==> Music on iPod (LOCAL_MUSIC=${LOCAL_MUSIC})"
MPD_DIR="${DATA_DIR}/mpd"
if [[ "${LOCAL_MUSIC}" == "1" ]]; then
  apt-get install -y --no-install-recommends mpd
  # Our own instance (spotifypod-mpd.service) replaces the package's system one, which
  # would run as user mpd from /etc/mpd.conf and hold port 6600.
  systemctl disable --now mpd.service mpd.socket 2>/dev/null || true
  # Login user owns the folder (rsync/scp); setgid keeps new files readable by the group.
  mkdir -p "${MUSIC_DIR}" "${MPD_DIR}"
  chown "${MUSIC_USER:-root}:${SPOTIFYPOD_USER}" "${MUSIC_DIR}"
  chmod 2775 "${MUSIC_DIR}"
  sed -e "s|__MUSIC_DIR__|${MUSIC_DIR}|g" -e "s|__MPD_DIR__|${MPD_DIR}|g" -e "s|__MPD_PORT__|${MPD_PORT}|g" \
    "${SCRIPT_DIR}/config/mpd.conf.template" > "${MPD_DIR}/mpd.conf"
  # Same output as go-librespot; software mixer so wheel volume works like Spotify's.
  if [[ "${AUDIO_BACKEND}" == "pulseaudio" ]]; then
    cat >> "${MPD_DIR}/mpd.conf" <<EOF
audio_output {
    type        "pulse"
    name        "iPod"
    server      "unix:${PULSE_SOCKET}"
    mixer_type  "software"
}
EOF
  else
    cat >> "${MPD_DIR}/mpd.conf" <<EOF
audio_output {
    type        "alsa"
    name        "iPod"
    device      "default"
    mixer_type  "software"
}
EOF
  fi
  chown -R "${SPOTIFYPOD_USER}:${SPOTIFYPOD_USER}" "${MPD_DIR}"
else
  systemctl disable --now spotifypod-mpd.service 2>/dev/null || true
  rm -f /etc/systemd/system/spotifypod-mpd.service
fi

if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
  echo "==> Display panel.bin (ST7789V)"
  PANEL_TXT="${SCRIPT_DIR}/config/panel.txt"
  if command -v mipi-dbi-cmd >/dev/null 2>&1; then
    mipi-dbi-cmd /lib/firmware/panel.bin "${PANEL_TXT}"
  else
    python3 "${SCRIPT_DIR}/tools/mipi_dbi_cmd.py" /lib/firmware/panel.bin "${PANEL_TXT}"
  fi
  rm -f "/lib/firmware/spotifypod,st7789v.bin"   # leftover from earlier installer versions
  echo "==> Xorg fbdev config (SPI panel)"
  install -m 644 "${SCRIPT_DIR}/config/99-fbdev.conf" /etc/X11/xorg.conf.d/99-fbdev.conf
else
  echo "==> Xorg: composite uses the default KMS (modesetting) driver"
  rm -f /etc/X11/xorg.conf.d/99-fbdev.conf
fi
# Let Xorg run with root rights from the systemd service (kiosk; no display manager).
printf 'allowed_users=anybody\nneeds_root_rights=yes\n' > /etc/X11/Xwrapper.config

echo "==> Boot config (${DISPLAY_PROFILE})"
DISPLAY_PROFILE="${DISPLAY_PROFILE}" TV_NORM="${TV_NORM}" DC_GPIO="${DC_GPIO}" RESET_GPIO="${RESET_GPIO}" BL_GPIO="${BL_GPIO}" \
  bash "${SCRIPT_DIR}/bin/configure-display.sh"

echo "==> Wired audio (WIRED_AUDIO=${WIRED_AUDIO}, AUDIO_BACKEND=${AUDIO_BACKEND})"
WIRED_AUDIO="${WIRED_AUDIO}" AUDIO_BACKEND="${AUDIO_BACKEND}" DAC_OVERLAY="${DAC_OVERLAY}" ALSA_CARD="${ALSA_CARD}" \
  DAC_RESET_GPIO="${DAC_RESET_GPIO}" JACK_DETECT_GPIO="${JACK_DETECT_GPIO}" \
  bash "${SCRIPT_DIR}/bin/configure-audio.sh"
# The DAC is set up over I2C at boot (spotifypod-dac.service, tlv320.py).
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  install -m 755 "${SCRIPT_DIR}/bin/tlv320.py" "${INSTALL_ROOT}/bin/tlv320.py"
  echo i2c-dev > /etc/modules-load.d/spotifypod-i2c.conf
else
  rm -f "${INSTALL_ROOT}/bin/tlv320.py" /etc/modules-load.d/spotifypod-i2c.conf
fi
# WirePlumber: keep the DAC's clock running at 44.1 kHz. 0.4 (Bookworm) reads Lua from
# main.lua.d, 0.5 (Trixie) SPA-JSON from wireplumber.conf.d and warns about Lua files.
WP_LUA=/etc/wireplumber/main.lua.d/51-spotifypod-dac.lua
WP_CONF=/etc/wireplumber/wireplumber.conf.d/51-spotifypod-dac.conf
rm -f "${WP_LUA}" "${WP_CONF}"
if [[ "${WIRED_AUDIO}" == "i2s" && "${AUDIO_BACKEND}" == "pulseaudio" ]]; then
  if [[ -d /usr/share/wireplumber/main.lua.d ]]; then
    install -D -m 644 "${SCRIPT_DIR}/config/wireplumber-dac.lua" "${WP_LUA}"
  else
    install -D -m 644 "${SCRIPT_DIR}/config/wireplumber-dac.conf" "${WP_CONF}"
  fi
fi
# With alsa, go-librespot and MPD share the card through dmix. The spotifypod user's
# PipeWire would otherwise open the same card, so it's masked for that user only.
PW_MASK_DIR="${DATA_DIR}/.config/systemd/user"
PW_UNITS=(pipewire.socket pipewire.service pipewire-pulse.socket pipewire-pulse.service wireplumber.service)
if [[ "${AUDIO_BACKEND}" == "alsa" ]]; then
  mkdir -p "${PW_MASK_DIR}"
  for u in "${PW_UNITS[@]}"; do ln -sfn /dev/null "${PW_MASK_DIR}/${u}"; done
  chown -R "${SPOTIFYPOD_USER}:${SPOTIFYPOD_USER}" "${DATA_DIR}/.config"
else
  for u in "${PW_UNITS[@]}"; do
    if [[ -L "${PW_MASK_DIR}/${u}" && "$(readlink "${PW_MASK_DIR}/${u}")" == /dev/null ]]; then
      rm -f "${PW_MASK_DIR}/${u}"
    fi
  done
fi

echo "==> App config.env"
if [[ ! -f "${CONFIG_DIR}/config.env" ]]; then
  install -m 640 "${SCRIPT_DIR}/config/config.env.example" "${CONFIG_DIR}/config.env"
  echo "Edit ${CONFIG_DIR}/config.env and set SPOTIPY_CLIENT_ID / SPOTIPY_REDIRECT_URI"
fi
chown root:"${SPOTIFYPOD_USER}" "${CONFIG_DIR}/config.env"
chmod 640 "${CONFIG_DIR}/config.env"

echo "==> ${CONFIG_DIR}/install.env (Settings -> About, Music on iPod)"
# The repo usually belongs to the login user; root's git refuses it without safe.directory.
SPOTIFYPOD_VERSION="$(git -c safe.directory="${REPO_ROOT}" -C "${REPO_ROOT}" describe --tags --always --dirty 2>/dev/null || echo unknown)"
MPD_VERSION=""
if [[ "${LOCAL_MUSIC}" == "1" ]]; then
  MPD_VERSION="$(dpkg-query -W -f='${Version}' mpd 2>/dev/null || true)"
fi
cat > "${CONFIG_DIR}/install.env" <<EOF
# Written by install/install.sh on every run; edits here are overwritten. Use config.env.
SPOTIFYPOD_VERSION=${SPOTIFYPOD_VERSION}
DISPLAY_PROFILE=${DISPLAY_PROFILE}
TV_NORM=${TV_NORM}
AUDIO_BACKEND=${AUDIO_BACKEND}
WIRED_AUDIO=${WIRED_AUDIO}
WIRED_GAIN_DB=${WIRED_GAIN_DB}
DAC_RESET_GPIO=${DAC_RESET_GPIO}
JACK_DETECT_GPIO=${JACK_DETECT_GPIO}
JACK_PLUGGED_LEVEL=${JACK_PLUGGED_LEVEL}
GO_LIBRESPOT_VERSION=${GO_LIBRESPOT_VERSION}
LOCAL_MUSIC=${LOCAL_MUSIC}
MUSIC_DIR=${MUSIC_DIR}
MPD_PORT=${MPD_PORT}
MPD_VERSION=${MPD_VERSION}
EOF
chmod 644 "${CONFIG_DIR}/install.env"

echo "==> Comitup"
if [[ -d /etc/comitup.conf ]] || [[ -f /etc/comitup.conf ]]; then
  :
fi
if [[ -f /etc/comitup.conf ]]; then
  cp "${SCRIPT_DIR}/config/comitup.conf" /etc/comitup.conf
elif [[ -d /etc ]]; then
  install -m 644 "${SCRIPT_DIR}/config/comitup.conf" /etc/comitup.conf
fi

echo "==> Hostname / Avahi"
hostnamectl set-hostname "${HOSTNAME_VALUE}" 2>/dev/null || echo "${HOSTNAME_VALUE}" > /etc/hostname
# hostnamectl does not touch /etc/hosts; without this sudo warns "unable to resolve host"
if grep -qE '^127\.0\.1\.1\s' /etc/hosts; then
  sed -i -E "s/^(127\.0\.1\.1\s+).*/\1${HOSTNAME_VALUE}/" /etc/hosts
else
  echo "127.0.1.1	${HOSTNAME_VALUE}" >> /etc/hosts
fi
if [[ -f /etc/avahi/avahi-daemon.conf ]]; then
  systemctl enable avahi-daemon || true
fi
# Wi-Fi power saving on the Zero 2 W drops multicast traffic, which makes mDNS
# (Spotify Connect discovery, ipod.local) flaky. Disable it.
mkdir -p /etc/NetworkManager/conf.d
cat > /etc/NetworkManager/conf.d/spotifypod-wifi-powersave.conf <<EOF
[connection]
wifi.powersave = 2
EOF

echo "==> Power: allow ${SPOTIFYPOD_USER} to shut down / reboot via logind (polkit)"
# The UI (Settings menu) and the portal (Power card) run `systemctl poweroff|reboot`
# as the unprivileged spotifypod user. systemctl asks logind, logind asks polkit.
# JS rules need polkit >= 0.106 (Bookworm ships 122, Trixie 126). polkitd watches
# rules.d, no restart needed.
mkdir -p /etc/polkit-1/rules.d
sed "s/__USER__/${SPOTIFYPOD_USER}/g" "${SCRIPT_DIR}/config/50-spotifypod-power.rules" \
  > /etc/polkit-1/rules.d/50-spotifypod-power.rules
chmod 644 /etc/polkit-1/rules.d/50-spotifypod-power.rules

echo "==> journald: keep logs in RAM (fewer SD card writes, safer against power cuts)"
# `journalctl -b` still works for the current boot; logs are not kept across reboots.
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/spotifypod.conf <<EOF
[Journal]
Storage=volatile
RuntimeMaxUse=16M
EOF
systemctl restart systemd-journald 2>/dev/null || true

echo "==> Fonts (ChicagoFLF if present in repo)"
mkdir -p /usr/local/share/fonts/spotifypod
if [[ -d "${REPO_ROOT}/fonts" ]]; then
  find "${REPO_ROOT}/fonts" -type f \( -iname '*.ttf' -o -iname '*.otf' \) \
    -exec install -m 644 {} /usr/local/share/fonts/spotifypod/ \;
  fc-cache -f || true
fi

echo "==> systemd units"
install -m 644 "${SCRIPT_DIR}/systemd/click.service" /etc/systemd/system/click.service
sed "s/__UID__/${SPOTIFYPOD_UID}/g" "${SCRIPT_DIR}/systemd/go-librespot.service" \
  > /etc/systemd/system/go-librespot.service
chmod 644 /etc/systemd/system/go-librespot.service
install -m 644 "${SCRIPT_DIR}/systemd/spotifypod.service" /etc/systemd/system/spotifypod.service
sed "s/__UID__/${SPOTIFYPOD_UID}/g" "${SCRIPT_DIR}/systemd/spotifypod-portal.service" \
  > /etc/systemd/system/spotifypod-portal.service
chmod 644 /etc/systemd/system/spotifypod-portal.service
if [[ "${LOCAL_MUSIC}" == "1" ]]; then
  sed "s/__UID__/${SPOTIFYPOD_UID}/g" "${SCRIPT_DIR}/systemd/spotifypod-mpd.service" \
    > /etc/systemd/system/spotifypod-mpd.service
  chmod 644 /etc/systemd/system/spotifypod-mpd.service
fi
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  install -m 644 "${SCRIPT_DIR}/systemd/spotifypod-dac.service" /etc/systemd/system/spotifypod-dac.service
else
  systemctl disable spotifypod-dac.service 2>/dev/null || true
  rm -f /etc/systemd/system/spotifypod-dac.service
fi
systemctl daemon-reload
# Note: no pigpiod. click.c links libpigpio directly and owns the GPIO hardware
# itself; a running daemon would fight it for the DMA/PCM peripherals.
systemctl disable --now pigpiod 2>/dev/null || true
systemctl enable click.service go-librespot.service spotifypod.service spotifypod-portal.service
if [[ "${LOCAL_MUSIC}" == "1" ]]; then
  systemctl enable spotifypod-mpd.service
fi
if [[ "${WIRED_AUDIO}" == "i2s" ]]; then
  systemctl enable spotifypod-dac.service
fi
# Bluetooth speakers: adapter on at boot, radio unblocked
systemctl enable bluetooth.service 2>/dev/null || true
rfkill unblock bluetooth 2>/dev/null || true
if [[ -f /etc/bluetooth/main.conf ]]; then
  if grep -qE '^\s*#?\s*AutoEnable\s*=' /etc/bluetooth/main.conf; then
    sed -i -E 's/^\s*#?\s*AutoEnable\s*=.*/AutoEnable=true/' /etc/bluetooth/main.conf
  else
    printf '\n[Policy]\nAutoEnable=true\n' >> /etc/bluetooth/main.conf
  fi
fi
systemctl enable NetworkManager || true
systemctl enable comitup 2>/dev/null || true

# Autologin on tty1 so xinit can claim VT1 without getty conflict
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${SPOTIFYPOD_USER} --noclear %I \$TERM
EOF
# Prefer system spotifypod service over interactive login starting X
systemctl disable getty@tty1.service 2>/dev/null || true

echo ""
echo "Install complete."
echo "  1. Edit ${CONFIG_DIR}/config.env (Spotify Client ID + redirect URI)"
echo "  2. Register the same redirect URI in the Spotify dashboard (docs/guide/02-spotify-app.md)"
echo "  3. Display profile: ${DISPLAY_PROFILE}; click wheel clock=${CLICK_CLOCK_PIN} data=${EFFECTIVE_DATA_PIN} haptic=${CLICK_HAPTIC_PIN}"
echo "  4. Reboot. First boot: join iPod hotspot QR / comitup, then Spotify Connect to 'iPod',"
echo "     then open http://ipod.local to link the Web API library."
echo "  AUDIO_BACKEND=${AUDIO_BACKEND} WIRED_AUDIO=${WIRED_AUDIO} (headphone level ${WIRED_GAIN_DB} dB)"
if [[ "${LOCAL_MUSIC}" == "1" ]]; then
  echo "  Music on iPod: copy files to ${MUSIC_DIR}, then Settings -> Update Music"
fi

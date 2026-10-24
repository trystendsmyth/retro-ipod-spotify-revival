#!/usr/bin/env bash
# spot-revival installer for Raspberry Pi OS Lite (Bookworm or newer).
#   64-bit OS: Pi Zero 2 W, Pi 3, Pi 4      32-bit OS: Pi Zero W / Zero (ARMv6)
# Run as root on the Pi:  sudo bash install/install.sh
#
# Derived from oliver-vv/Spotify-iPod-Classic (Apache-2.0). spot-revival adds:
# DISPLAY_PROFILE=composite (original sPot Adafruit #911 TV display, default),
# ARMv6 support, a pinned + checksummed go-librespot download, and pin defines
# passed to the compiler instead of editing click.c. See NOTICE.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# --- Tunables (override via env) ---
INSTALL_ROOT="${INSTALL_ROOT:-/opt/spotifypod}"
DATA_DIR="${DATA_DIR:-/var/lib/spotifypod}"
CONFIG_DIR="${CONFIG_DIR:-/etc/spotifypod}"
SPOTIFYPOD_USER="${SPOTIFYPOD_USER:-spotifypod}"
# Audio: pulseaudio (PipeWire BT default) or alsa (I2S/USB DAC)
AUDIO_BACKEND="${AUDIO_BACKEND:-pulseaudio}"
# Display: "composite" = original sPot build (Adafruit #911 NTSC/PAL TFT on the
# Pi's composite output); "st7789" = Ricardo Sappia's Waveshare 2" SPI build.
DISPLAY_PROFILE="${DISPLAY_PROFILE:-composite}"
# Composite TV standard (composite profile only): NTSC, PAL, PAL60, NTSC-J, ...
TV_NORM="${TV_NORM:-NTSC}"
# Display GPIOs for mipi-dbi-spi (st7789 profile only). Defaults follow Ricardo Sappia's Waveshare build
# (DC=24 / pin 18, RESET=25 / pin 22, backlight GPIO 18 / pin 12).
# Set BL_GPIO="" if your backlight is hard-wired to 3.3V instead.
DC_GPIO="${DC_GPIO:-24}"
RESET_GPIO="${RESET_GPIO:-25}"
BL_GPIO="${BL_GPIO-18}"
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

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash $0" >&2
  exit 1
fi

case "${DISPLAY_PROFILE}" in
  composite|st7789) ;;
  *) echo "ERROR: DISPLAY_PROFILE must be 'composite' or 'st7789' (got '${DISPLAY_PROFILE}')" >&2; exit 1 ;;
esac

EFFECTIVE_DATA_PIN="${CLICK_DATA_PIN}"
if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
# --- Pin sanity check: display pins must not collide with the click wheel ---
for p in "${DC_GPIO}" "${RESET_GPIO}" "${BL_GPIO}"; do
  [[ -z "${p}" ]] && continue
  for c in "${CLICK_CLOCK_PIN}" "${EFFECTIVE_DATA_PIN}" "${CLICK_HAPTIC_PIN}"; do
    if [[ "${p}" == "${c}" ]]; then
      echo "ERROR: display GPIO ${p} collides with a click wheel pin (clock=${CLICK_CLOCK_PIN}, data=${EFFECTIVE_DATA_PIN}, haptic=${CLICK_HAPTIC_PIN})." >&2
      echo "       Adjust DC_GPIO / RESET_GPIO / BL_GPIO / CLICK_DATA_PIN to match your wiring." >&2
      exit 1
    fi
  done
done
for p in "${DC_GPIO}" "${RESET_GPIO}" "${BL_GPIO}"; do
  [[ -z "${p}" ]] && continue
  case "${p}" in 8|9|10|11) echo "ERROR: GPIO ${p} is the SPI0 bus itself (CE0/MISO/MOSI/SCLK)." >&2; exit 1 ;; esac
done
fi

echo "==> Pin map"
echo "    click wheel : clock=${CLICK_CLOCK_PIN} data=${EFFECTIVE_DATA_PIN} haptic=${CLICK_HAPTIC_PIN}"
if [[ "${DISPLAY_PROFILE}" == "st7789" ]]; then
  echo "    display     : st7789 dc=${DC_GPIO} reset=${RESET_GPIO} backlight=${BL_GPIO:-<hard-wired>} spi0 (mosi=10 sclk=11 ce0=8)"
else
  echo "    display     : composite (${TV_NORM}) on the TV pad / AV jack"
fi

echo "==> Installing packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  python3 python3-venv python3-pip python3-tk python3-pil.imagetk \
  xserver-xorg-core xserver-xorg-video-fbdev xserver-xorg-legacy xinit x11-xserver-utils \
  network-manager avahi-daemon polkitd \
  curl ca-certificates unzip rsync file fonts-dejavu-core \
  pipewire pipewire-audio pipewire-alsa pipewire-pulse wireplumber dbus-user-session \
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

# Comitup may need its own repo on Bookworm; try apt first.
if ! apt-get install -y comitup 2>/dev/null; then
  echo "WARN: comitup not in default apt; see https://davesteele.github.io/comitup/ for Bookworm install"
fi

echo "==> Creating user ${SPOTIFYPOD_USER}"
if ! id -u "${SPOTIFYPOD_USER}" >/dev/null 2>&1; then
  useradd --system --home "${DATA_DIR}" --shell /usr/sbin/nologin \
    --groups audio,video "${SPOTIFYPOD_USER}" || true
fi
usermod -aG audio,video "${SPOTIFYPOD_USER}" 2>/dev/null || true
getent group bluetooth >/dev/null && usermod -aG bluetooth "${SPOTIFYPOD_USER}" 2>/dev/null || true
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
gcc -Wall -pthread -O2 -I/usr/local/include -L/usr/local/lib \
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

echo "==> App config.env"
if [[ ! -f "${CONFIG_DIR}/config.env" ]]; then
  install -m 640 "${SCRIPT_DIR}/config/config.env.example" "${CONFIG_DIR}/config.env"
  echo "Edit ${CONFIG_DIR}/config.env and set SPOTIPY_CLIENT_ID / SPOTIPY_REDIRECT_URI"
fi
chown root:"${SPOTIFYPOD_USER}" "${CONFIG_DIR}/config.env"
chmod 640 "${CONFIG_DIR}/config.env"

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
systemctl daemon-reload
# Note: no pigpiod. click.c links libpigpio directly and owns the GPIO hardware
# itself; a running daemon would fight it for the DMA/PCM peripherals.
systemctl disable --now pigpiod 2>/dev/null || true
systemctl enable click.service go-librespot.service spotifypod.service spotifypod-portal.service
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
echo "  2. Enable GitHub Pages for docs/spotify-callback.html and register that HTTPS URI"
echo "  3. Display profile: ${DISPLAY_PROFILE}; click wheel clock=${CLICK_CLOCK_PIN} data=${EFFECTIVE_DATA_PIN} haptic=${CLICK_HAPTIC_PIN}"
echo "  4. Reboot. First boot: join iPod hotspot QR / comitup, then Spotify Connect to 'iPod',"
echo "     then open http://ipod.local to link the Web API library."
echo "  AUDIO_BACKEND=${AUDIO_BACKEND}"

#!/usr/bin/env bash
# Runs inside the container started by run-installer.sh, as root. Installs with the
# defaults, re-runs with other options, and checks what each run leaves behind.
set -euo pipefail
REPO=/home/pi/repo
CFG=/boot/firmware/config.txt
UNITS=/etc/systemd/system
N=0

fail() { echo "FAIL: $*" >&2; exit 1; }
install_with() {
  N=$((N + 1))
  echo "==> install ${N}: $*"
  if ! env SUDO_USER=pi "$@" bash "${REPO}/install/install.sh" > "/tmp/install-${N}.log" 2>&1; then
    tail -40 "/tmp/install-${N}.log" >&2
    fail "install ${N} ($*) failed"
  fi
}
count() { grep -c "$1" "$2" || true; }
spot_uid() { id -u spotifypod; }
as_spotifypod() {
  runuser -u spotifypod -- env XDG_RUNTIME_DIR="/run/user/$(spot_uid)" "$@"
}

# --- 1. defaults: composite display, PipeWire, wired audio
install_with
for u in click go-librespot spotifypod spotifypod-portal spotifypod-mpd spotifypod-dac; do
  [[ "$(systemctl is-enabled "${u}")" == enabled ]] || fail "${u} not enabled"
done
systemd-analyze verify --man=no "${UNITS}"/spotifypod-dac.service "${UNITS}"/spotifypod-portal.service \
  "${UNITS}"/spotifypod-mpd.service "${UNITS}"/go-librespot.service "${UNITS}"/click.service \
  || fail "systemd-analyze verify"
[[ "$(count '^# >>> retro-ipod-spotify-revival audio' "${CFG}")" == 1 ]] || fail "audio block"
[[ "$(count '^# >>> retro-ipod-spotify-revival display' "${CFG}")" == 1 ]] || fail "display block"
for line in dtparam=i2c_arm=on dtoverlay=i2s-dac gpio=17=op,dl dtoverlay=vc4-kms-v3d,composite; do
  grep -qx "${line}" "${CFG}" || fail "config.txt: ${line}"
done
grep -qx 'WIRED_AUDIO=i2s' /etc/spotifypod/install.env || fail "install.env"
[[ -x /opt/spotifypod/bin/tlv320.py ]] || fail "tlv320.py"
/usr/bin/python3 -m py_compile /opt/spotifypod/bin/tlv320.py
grep -qx i2c-dev /etc/modules-load.d/spotifypod-i2c.conf || fail "i2c-dev"
WP_LUA=/etc/wireplumber/main.lua.d/51-spotifypod-dac.lua
WP_CONF=/etc/wireplumber/wireplumber.conf.d/51-spotifypod-dac.conf
if [[ -d /usr/share/wireplumber/main.lua.d ]]; then   # WirePlumber 0.4
  [[ -f "${WP_LUA}" && ! -e "${WP_CONF}" ]] || fail "wireplumber 0.4: want only the .lua"
else
  [[ -f "${WP_CONF}" && ! -e "${WP_LUA}" ]] || fail "wireplumber 0.5: want only the .conf"
fi
[[ ! -e /etc/asound.conf ]] || fail "asound.conf with PipeWire"
command -v pactl >/dev/null || fail "pactl missing"

# The portal answers with the output list
systemctl start spotifypod-portal
for _ in $(seq 30); do curl -fs http://127.0.0.1/api/audio >/tmp/api-audio.json && break; sleep 1; done
grep -q '"outputs"' /tmp/api-audio.json || fail "portal /api/audio: $(cat /tmp/api-audio.json)"
curl -fs http://127.0.0.1/ | grep -q 'id="audio-outputs"' || fail "portal page has no Output card"

# Output switching against the spotifypod user's real PipeWire and WirePlumber
systemctl start "user@$(spot_uid).service"
for _ in $(seq 30); do as_spotifypod pactl info >/dev/null 2>&1 && break; sleep 1; done
as_spotifypod pactl info >/dev/null || fail "pipewire-pulse not running for spotifypod"
# (copied out of /home/pi, which is mode 0700 on Trixie)
install -m 644 "${REPO}/tests/integration/routing_scenario.py" /tmp/routing_scenario.py
if ! as_spotifypod env SPOTIFYPOD_DATA_DIR=/tmp/it-data PYTHONPATH=/opt/spotifypod/frontend \
    /opt/spotifypod/venv/bin/python /tmp/routing_scenario.py; then
  journalctl -b --no-pager _SYSTEMD_USER_UNIT=wireplumber.service | tail -20 >&2
  fail "routing scenario"
fi
# WirePlumber runs, and loaded our rule file without complaint (a Lua or SPA-JSON
# mistake shows up as "Failed to compile"/"failed to parse" naming the file)
[[ "$(as_spotifypod systemctl --user is-active wireplumber)" == active ]] || fail "wireplumber not running"
if journalctl -b --no-pager _SYSTEMD_USER_UNIT=wireplumber.service 2>/dev/null | grep -i 'spotifypod'; then
  fail "wireplumber logged something about 51-spotifypod-dac"
fi

# --- 2. AUDIO_BACKEND=alsa, no DAC (a USB DAC user)
install_with AUDIO_BACKEND=alsa WIRED_AUDIO=none
[[ "$(count '^# >>> retro-ipod-spotify-revival audio' "${CFG}")" == 0 ]] || fail "audio block left (none)"
grep -q 'i2s-dac\|i2c_arm\|^gpio=17' "${CFG}" && fail "DAC lines left (none)"
[[ ! -e "${UNITS}/spotifypod-dac.service" ]] || fail "spotifypod-dac left (none)"
[[ ! -e /etc/wireplumber/main.lua.d/51-spotifypod-dac.lua ]] || fail "wireplumber lua left"
grep -q 'hw:CARD=0,DEV=0' /etc/asound.conf || fail "asound.conf (none)"
[[ "$(readlink /var/lib/spotifypod/.config/systemd/user/wireplumber.service)" == /dev/null ]] \
  || fail "PipeWire not masked for alsa"
grep -q '^audio_backend: alsa' /var/lib/spotifypod/go-librespot/config.yml || fail "go-librespot backend"

# --- 3. AUDIO_BACKEND=alsa with the DAC
install_with AUDIO_BACKEND=alsa WIRED_AUDIO=i2s
grep -q 'hw:CARD=sndrpirpidac,DEV=0' /etc/asound.conf || fail "asound.conf (i2s)"
[[ "$(count '^# >>> retro-ipod-spotify-revival audio' "${CFG}")" == 1 ]] || fail "audio block (alsa i2s)"
[[ ! -e /etc/wireplumber/main.lua.d/51-spotifypod-dac.lua ]] || fail "wireplumber lua with alsa"

# --- 4. back to the defaults: everything from 2 and 3 undone
install_with
[[ ! -e /etc/asound.conf ]] || fail "asound.conf left"
[[ ! -e /var/lib/spotifypod/.config/systemd/user/wireplumber.service ]] || fail "PipeWire still masked"
[[ "$(count '^# >>> retro-ipod-spotify-revival audio' "${CFG}")" == 1 ]] || fail "audio block (defaults)"
[[ "$(count '^dtoverlay=i2s-dac$' "${CFG}")" == 1 ]] || fail "overlay duplicated"

# --- 5. st7789: backlight on GPIO 27 installs; GPIO 18 is refused before anything runs
install_with DISPLAY_PROFILE=st7789
grep -q 'backlight-gpio=27' "${CFG}" || fail "st7789 backlight default"
cp "${CFG}" /tmp/before.txt
if env SUDO_USER=pi DISPLAY_PROFILE=st7789 BL_GPIO=18 bash "${REPO}/install/install.sh" > /tmp/install-bl18.log 2>&1; then
  fail "BL_GPIO=18 with wired audio accepted"
fi
grep -q 'BL_GPIO=18 is the I2S bit clock' /tmp/install-bl18.log || fail "BL_GPIO=18 message"
cmp -s "${CFG}" /tmp/before.txt || fail "refused install changed config.txt"
install_with DISPLAY_PROFILE=composite

echo "installer checks: all passed ($(. /etc/os-release && echo "${PRETTY_NAME}"))"

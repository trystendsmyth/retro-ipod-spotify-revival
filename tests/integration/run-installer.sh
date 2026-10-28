#!/usr/bin/env bash
# Run install/install.sh in a Debian container with systemd, then check the result and
# drive audio output switching against the installed PipeWire. No Pi hardware: there is
# no DAC, I2C, GPIO or Bluetooth adapter, so those parts are only checked as files.
#
#   bash tests/integration/run-installer.sh [bookworm|trixie]     (KEEP=1 keeps the container)
#
# Needs Docker on an arm64 host (the installer only supports ARM).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEBIAN="${1:-bookworm}"
NAME="spotifypod-it-${DEBIAN}"

docker build -q -t "${NAME}" --build-arg DEBIAN="${DEBIAN}" "${ROOT}/tests/integration" >/dev/null
docker rm -f "${NAME}" >/dev/null 2>&1 || true
docker run -d --name "${NAME}" --privileged --cgroupns=host \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw --tmpfs /run --tmpfs /run/lock "${NAME}" >/dev/null
if [[ "${KEEP:-0}" != 1 ]]; then
  trap 'docker rm -f "${NAME}" >/dev/null 2>&1 || true' EXIT
fi
# Wait for boot to finish ("degraded" is fine: some units need hardware). Before systemd
# answers, is-system-running fails at once, so poll.
for _ in $(seq 120); do
  state="$(docker exec "${NAME}" systemctl is-system-running 2>/dev/null || true)"
  [[ "${state}" == running || "${state}" == degraded ]] && break
  sleep 1
done
[[ "${state}" == running || "${state}" == degraded ]] || { echo "container did not boot (${state})" >&2; exit 1; }
# Docker bind-mounts /etc/hosts, so the installer's `sed -i` on it can't rename the file.
# On the Pi it's a plain file: make it one here too.
docker exec "${NAME}" sh -c 'cp /etc/hosts /root/hosts && umount /etc/hosts && cp /root/hosts /etc/hosts'
# RTKit can't work in a container. When D-Bus starts it on demand, every PipeWire client
# (wpctl, pw-dump) waits for its reply until D-Bus gives up, longer than bt_manager's
# timeouts. Masked, the request fails at once. Raspberry Pi OS runs RTKit normally.
docker exec "${NAME}" systemctl mask rtkit-daemon.service >/dev/null 2>&1

# The working tree as it is (uncommitted changes included), and stand-in boot files
COPYFILE_DISABLE=1 tar -C "${ROOT}" --no-xattrs --exclude=./docs/images --exclude='__pycache__' -cf - . \
  | docker exec -i "${NAME}" sh -c 'mkdir -p /home/pi/repo && tar -C /home/pi/repo -xf - && chown -R pi:pi /home/pi/repo'
docker cp "${ROOT}/tests/fixtures/config.txt" "${NAME}:/boot/firmware/config.txt"
docker cp "${ROOT}/tests/fixtures/cmdline.txt" "${NAME}:/boot/firmware/cmdline.txt"

docker exec "${NAME}" bash /home/pi/repo/tests/integration/installer-checks.sh

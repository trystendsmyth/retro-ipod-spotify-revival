# Debian with systemd as PID 1, standing in for Raspberry Pi OS Lite (no Pi hardware).
# Used by tests/integration/run-installer.sh.
ARG DEBIAN=bookworm
FROM debian:${DEBIAN}
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      systemd systemd-sysv dbus dbus-user-session ca-certificates git sudo curl \
 && rm -rf /var/lib/apt/lists/*
# The login user Raspberry Pi Imager creates (uid 1000); owns /srv/music
# The container is privileged and shares the host's kernel: systemd-binfmt would clear
# the host's binfmt_misc handlers (e.g. Docker Desktop's x86 emulation).
RUN systemctl mask systemd-binfmt.service proc-sys-fs-binfmt_misc.automount proc-sys-fs-binfmt_misc.mount
RUN useradd -m -u 1000 -s /bin/bash pi
RUN mkdir -p /boot/firmware
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]

#!/usr/bin/env bash
# Exercises install/bin/configure-display.sh against fixture boot files.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
run() { BOOTCFG="$T/config.txt" CMDLINE="$T/cmdline.txt" bash "$ROOT/install/bin/configure-display.sh" >/dev/null; }

cp "$ROOT/tests/fixtures/config.txt" "$ROOT/tests/fixtures/cmdline.txt" "$T/"

# 1. composite (default)
DISPLAY_PROFILE=composite TV_NORM=NTSC run
grep -qx 'dtoverlay=vc4-kms-v3d,composite' "$T/config.txt" || fail "composite overlay missing"
[[ "$(grep -c '^dtoverlay=vc4-kms-v3d' "$T/config.txt")" == 1 ]] || fail "duplicate KMS lines"
tail -n 8 "$T/config.txt" | grep -qx '\[all\]' || fail "block not under [all]"
[[ "$(wc -l < "$T/cmdline.txt")" == 1 ]] || fail "cmdline not single line"
grep -q ' vc4.tv_norm=NTSC$' "$T/cmdline.txt" || fail "tv_norm missing"

# 2. idempotent re-run, switch to PAL
DISPLAY_PROFILE=composite TV_NORM=PAL run
[[ "$(grep -c 'spot-revival display (' "$T/config.txt")" == 1 ]] || fail "block duplicated"
[[ "$(grep -o 'vc4.tv_norm=' "$T/cmdline.txt" | wc -l)" == 1 ]] || fail "tv_norm duplicated"
grep -q 'vc4.tv_norm=PAL' "$T/cmdline.txt" || fail "tv_norm not PAL"

# 3. switch to st7789: KMS commented out, mipi overlay present, tv_norm removed
DISPLAY_PROFILE=st7789 DC_GPIO=24 RESET_GPIO=25 BL_GPIO=18 run
grep -q '^dtoverlay=mipi-dbi-spi' "$T/config.txt" || fail "mipi overlay missing"
grep -q '^dtoverlay=vc4-kms-v3d' "$T/config.txt" && fail "KMS still active for st7789"
grep -q 'dc-gpio=24' "$T/config.txt" || fail "dc gpio"
grep -q 'vc4.tv_norm' "$T/cmdline.txt" && fail "tv_norm left behind"

# 4. back to composite: exactly one active KMS line again
DISPLAY_PROFILE=composite run
[[ "$(grep -c '^dtoverlay=vc4-kms-v3d,composite$' "$T/config.txt")" == 1 ]] || fail "KMS not restored"
grep -q 'mipi-dbi-spi' "$T/config.txt" && fail "st7789 block left behind"
grep -q 'vc4-kms-v3d  # disabled' "$T/config.txt" && fail "commented KMS left behind"

# 5. bad TV norm rejected
if DISPLAY_PROFILE=composite TV_NORM=BOGUS run 2>/dev/null; then fail "bad TV_NORM accepted"; fi
echo "configure-display: all tests passed"

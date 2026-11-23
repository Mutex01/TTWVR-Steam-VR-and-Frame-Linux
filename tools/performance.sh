#!/usr/bin/env bash
# Set the CPU to full performance for VR (lasts until the next reboot).
# Fallout NV does most of its work on ONE core - single-core clock speed is what matters.
#
#   ./performance.sh on       boost on, power profile "performance", governor "performance"
#   ./performance.sh off      boost off, power profile "balanced", governor "schedutil"
#   ./performance.sh status   show only (needs no admin rights)
set -euo pipefail

CPU=/sys/devices/system/cpu
BOOST=$CPU/cpufreq/boost

status() {
  echo "Driver:        $(cat $CPU/cpu0/cpufreq/scaling_driver 2>/dev/null || echo ?)"
  echo "Governor:      $(cat $CPU/cpu0/cpufreq/scaling_governor 2>/dev/null || echo ?)"
  echo "Boost:         $(cat $BOOST 2>/dev/null || echo 'not controllable')"
  echo "Max clock:     $(( $(cat $CPU/cpu0/cpufreq/scaling_max_freq) / 1000 )) MHz (possible: $(( $(cat $CPU/cpu0/cpufreq/cpuinfo_max_freq) / 1000 )) MHz)"
  echo "Power profile: $(powerprofilesctl get 2>/dev/null || echo 'power-profiles-daemon not installed')"
}

set_governor() {
  for g in $CPU/cpu*/cpufreq/scaling_governor; do echo "$1" | sudo tee "$g" >/dev/null; done
}

case "${1:-status}" in
  on)
    [ -e "$BOOST" ] && echo 1 | sudo tee "$BOOST" >/dev/null
    # "performance" only exists if driver/platform offer it (e.g. not with acpi-cpufreq on Zen+)
    if command -v powerprofilesctl >/dev/null && powerprofilesctl list 2>/dev/null | grep -q "performance:"; then
      powerprofilesctl set performance
    fi
    set_governor performance
    status ;;
  off)
    [ -e "$BOOST" ] && echo 0 | sudo tee "$BOOST" >/dev/null
    command -v powerprofilesctl >/dev/null && powerprofilesctl set balanced || true
    set_governor schedutil
    status ;;
  status) status ;;
  *) echo "Usage: $0 on|off|status" >&2; exit 1 ;;
esac

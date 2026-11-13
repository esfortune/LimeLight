#!/bin/bash
# Installs UUGear's wp5 package (daemon) plus the wpsched scheduler/logger.
# Run with:  sudo ./install.sh
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo "Run with sudo: sudo $0"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET_USER="${SUDO_USER:-canopylife}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"

echo "== 1/4  UUGear wp5 daemon (handles shutdown requests, RTC sync)"
if ! dpkg -s wp5 >/dev/null 2>&1; then
    TMP="$(mktemp -d)"
    wget -q -O "$TMP/wp5_latest.deb" https://www.uugear.com/repo/WittyPi5/wp5_latest.deb
    apt-get install -y "$TMP/wp5_latest.deb"
    rm -rf "$TMP"
else
    echo "   already installed"
fi

echo "== 2/4  wpsched program"
install -m 755 "$HERE/wpsched.py" /usr/local/bin/wpsched
python3 -c "import smbus2" 2>/dev/null || apt-get install -y python3-smbus2

echo "== 3/4  schedule file"
if [[ -e "$TARGET_HOME/wittypi_schedule.txt" ]]; then
    echo "   keeping existing $TARGET_HOME/wittypi_schedule.txt"
else
    install -m 644 -o "$TARGET_USER" -g "$TARGET_USER" "$HERE/wittypi_schedule.txt" "$TARGET_HOME/"
fi

echo "== 4/4  systemd units"
for f in "$HERE"/systemd/*; do
    sed "s/@USER@/$TARGET_USER/" "$f" > "/etc/systemd/system/$(basename "$f")"
done
systemctl daemon-reload
systemctl enable wpsched-apply.service wpsched-apply.timer wpsched-log.timer wpsched-session.service
systemctl start wpsched-apply.timer wpsched-log.timer
sleep 3      # let wp5d set the clocks
systemctl start wpsched-apply.service wpsched-session.service

echo
sudo -u "$TARGET_USER" /usr/local/bin/wpsched status

#!/usr/bin/env bash
# Runs ON the comma: put sunnypilot back.  ssh comma@10.0.0.33 'bash /data/rollback-to-sunnypilot.sh'
set -euo pipefail
if [ "$(cat /data/params/d/IsOnroad 2>/dev/null || echo 0)" = "1" ]; then
  echo "Truck is on (onroad). Park it and turn it off first."; exit 1
fi
[ -d /data/sunnypilot-backup ] || { echo "No /data/sunnypilot-backup to restore."; exit 1; }
STAMP=$(date +%Y%m%d-%H%M)
mv /data/openpilot "/data/starpilot-$STAMP"
mv /data/sunnypilot-backup /data/openpilot
sync
echo "sunnypilot restored (StarPilot kept at /data/starpilot-$STAMP). Rebooting; sunnypilot reinstalls its AGNOS first."
sudo reboot

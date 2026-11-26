#!/usr/bin/env bash
# Runs ON the comma: put sunnypilot back.  ssh comma@10.1.0.82 'bash /data/rollback-to-sunnypilot.sh'
set -euo pipefail
if [ "$(cat /data/params/d/IsOnroad 2>/dev/null || echo 0)" = "1" ]; then
  echo "Truck is on (onroad). Park it and turn it off first."; exit 1
fi
[ -d /data/sunnypilot-backup ] || { echo "No /data/sunnypilot-backup to restore."; exit 1; }
STAMP=$(date +%Y%m%d-%H%M)
mv /data/openpilot "/data/starpilot-$STAMP"
mv /data/sunnypilot-backup /data/openpilot
# StarPilot's first boot archives sunnypilot's settings and learned values; put the pre-switch copy back.
# (/data/params/d is a symlink to /data/params/d_tmp, so the real copy is in the backup's d_tmp)
B=$(ls -d /data/params-sunnypilot-* 2>/dev/null | sort | tail -1)
if [ -n "$B" ] && [ -d "$B/d_tmp" ]; then
  echo "restoring sunnypilot settings from $B/d_tmp"
  rsync -a --delete "$B/d_tmp/" /data/params/d_tmp/
fi
sync
echo "sunnypilot restored (StarPilot kept at /data/starpilot-$STAMP). Rebooting; sunnypilot reinstalls its AGNOS first."
sudo reboot

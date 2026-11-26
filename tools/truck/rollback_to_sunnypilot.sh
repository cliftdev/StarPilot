#!/usr/bin/env bash
# Runs ON the comma: put sunnypilot back.  ssh comma@<comma-ip> 'bash /data/rollback-to-sunnypilot.sh'
# Uses /data/sunnypilot-backup if it is there, otherwise clones the truck's sunnypilot from GitHub
# (cliftdev/sunnypilot-ram release-mici: the two Ram HD commits plus the silent steering-limit alert).
set -euo pipefail
DATA=${DATA:-/data}
SP_REPO=${SP_REPO:-https://github.com/cliftdev/sunnypilot-ram.git}
SP_BRANCH=${SP_BRANCH:-release-mici}
if [ "$(cat "$DATA/params/d/IsOnroad" 2>/dev/null || echo 0)" = "1" ]; then
  echo "Truck is on (onroad). Park it and turn it off first."; exit 1
fi
STAMP=$(date +%Y%m%d-%H%M)
if [ -d "$DATA/sunnypilot-backup" ]; then
  SRC="$DATA/sunnypilot-backup"
else
  free_kb=$(df --output=avail "$DATA" | tail -1)
  if [ "$free_kb" -lt 3000000 ]; then
    echo "Need at least 3 GB free on $DATA to download sunnypilot (have $((free_kb / 1024)) MB)."; exit 1
  fi
  echo "== no local backup; cloning $SP_REPO ($SP_BRANCH)"
  rm -rf "$DATA/sunnypilot-new"
  git clone --depth=1 --branch "$SP_BRANCH" --single-branch "$SP_REPO" "$DATA/sunnypilot-new"
  git -C "$DATA/sunnypilot-new" log --oneline -1
  SRC="$DATA/sunnypilot-new"
fi
mv "$DATA/openpilot" "$DATA/starpilot-$STAMP"
mv "$SRC" "$DATA/openpilot"
# StarPilot's first boot archives sunnypilot's settings and learned values; put the pre-switch copy back.
# (/data/params/d is a symlink to /data/params/d_tmp, so the real copy is in the backup's d_tmp)
B=$(ls -d "$DATA"/params-sunnypilot-* 2>/dev/null | sort | tail -1)
if [ -n "$B" ] && [ -d "$B/d_tmp" ]; then
  echo "restoring sunnypilot settings from $B/d_tmp"
  rsync -a --checksum --delete "$B/d_tmp/" "$DATA/params/d_tmp/"
fi
sync
echo "sunnypilot restored (StarPilot kept at $DATA/starpilot-$STAMP). Rebooting; sunnypilot reinstalls its AGNOS first."
if [ -z "${NO_REBOOT:-}" ]; then sudo reboot; fi

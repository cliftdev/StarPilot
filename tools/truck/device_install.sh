#!/usr/bin/env bash
# Runs ON the comma: switch from sunnypilot to cliftdev/StarPilot (ram-hd), keeping sunnypilot for rollback.
# Normally started from this repo with tools/truck/switch.sh.
set -euo pipefail
BRANCH=${BRANCH:-ram-hd}
REPO=https://github.com/cliftdev/StarPilot.git
STAMP=$(date +%Y%m%d-%H%M)

if [ "$(cat /data/params/d/IsOnroad 2>/dev/null || echo 0)" = "1" ]; then
  echo "Truck is on (onroad). Park it and turn it off first."; exit 1
fi
if [ -e /data/sunnypilot-backup ]; then
  echo "/data/sunnypilot-backup already exists; refusing to overwrite it."; exit 1
fi
if git -C /data/openpilot remote get-url origin 2>/dev/null | grep -qi starpilot; then
  echo "/data/openpilot is already StarPilot; nothing to do."; exit 1
fi
free_kb=$(df --output=avail /data | tail -1)
if [ "$free_kb" -lt 3000000 ]; then
  echo "Need at least 3 GB free on /data (have $((free_kb / 1024)) MB)."; exit 1
fi

echo "== cloning $REPO ($BRANCH)"
rm -rf /data/starpilot-new
git clone --depth=1 --branch "$BRANCH" --single-branch "$REPO" /data/starpilot-new
git -C /data/starpilot-new log --oneline -1
[ -f /data/starpilot-new/prebuilt ] || { echo "clone has no prebuilt marker, aborting"; exit 1; }

echo "== backing up params to /data/params-sunnypilot-$STAMP"
cp -a /data/params "/data/params-sunnypilot-$STAMP"

if [ -d /data/safe_staging ]; then
  echo "== moving sunnypilot's updater staging aside"
  mv /data/safe_staging "/data/safe_staging-sunnypilot-$STAMP"
fi

echo "== swapping: sunnypilot -> /data/sunnypilot-backup, StarPilot -> /data/openpilot"
mv /data/openpilot /data/sunnypilot-backup
mv /data/starpilot-new /data/openpilot
sync

echo "== rebooting into StarPilot (it updates AGNOS to its version first, then starts)"
sudo reboot

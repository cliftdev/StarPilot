#!/usr/bin/env bash
# Run on this machine: move the truck's comma to the latest ram-hd commit, check it, then reboot it.
# The truck must be off (comma offroad) and the comma on the home network.
set -euo pipefail
HOST=${HOST:-comma@10.1.0.82}
BRANCH=${BRANCH:-ram-hd}

ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" "BRANCH=$BRANCH bash -s" <<'EOS'
set -euo pipefail
if [ "$(cat /data/params/d/IsOnroad 2>/dev/null || echo 0)" = "1" ]; then
  echo "Truck is on (onroad). Park it and turn it off first."; exit 1
fi
cd /data/openpilot
git remote get-url origin | grep -qi starpilot || { echo "/data/openpilot is not StarPilot; aborting"; exit 1; }
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "/data/openpilot has local changes to tracked files; aborting:"; git status --short --untracked-files=no; exit 1
fi
before=$(git rev-parse HEAD)
git fetch --depth=1 origin "$BRANCH"
if [ "$(git rev-parse FETCH_HEAD)" = "$before" ]; then
  echo "already at $(git log --oneline -1)"; exit 0
fi
git reset -q --hard FETCH_HEAD
echo "now at $(git log --oneline -1) (was ${before:0:7})"
if ! PYTHONPATH=/data/openpilot/opendbc_repo:/data/openpilot:/data/openpilot/openpilot \
     timeout 120 /usr/local/venv/bin/python tools/ram_hd_check.py; then
  echo "ram_hd_check failed; going back to ${before:0:7}"
  git reset -q --hard "$before"; exit 1
fi
sync
echo "rebooting the comma"
sudo reboot
EOS

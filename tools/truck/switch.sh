#!/usr/bin/env bash
# Run on this machine: install the rollback script on the truck's comma, then switch it to StarPilot.
set -euo pipefail
HOST=${HOST:-comma@10.1.0.82}
DIR=$(cd "$(dirname "$0")" && pwd)
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST")

"${SSH[@]}" 'cat > /data/rollback-to-sunnypilot.sh && chmod +x /data/rollback-to-sunnypilot.sh' < "$DIR/rollback_to_sunnypilot.sh"
echo "rollback script installed at /data/rollback-to-sunnypilot.sh"
"${SSH[@]}" "BRANCH=${BRANCH:-ram-hd} bash -s" < "$DIR/device_install.sh" || true
echo "comma is rebooting; first boot updates AGNOS (10-20 min) before StarPilot starts."

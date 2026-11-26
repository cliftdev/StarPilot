#!/usr/bin/env python3
"""Runs ON the comma after StarPilot boots: Dalton's settings, carried over from his sunnypilot setup.

  ssh comma@<ip> 'cd /data/openpilot && PYTHONPATH=/data/openpilot python3 tools/truck/apply_defaults.py'

Source: params snapshot ~/comma-logs/params-snapshots/sunnypilot-20261126-0217 and the drive logs.
"""
from pathlib import Path

from openpilot.common.params import Params
from openpilot.starpilot.power.offroad_preferences import KEY as POWER_KEY, PowerPolicy, to_value

BOOLS = {
  "AlwaysOnLateral": True,             # sunnypilot MADS=1 (steering stays on without cruise)
  "LaneCentering": True,               # Lane Centering 2.0; replaces sunnypilot CameraOffset=-0.12 (logs: engaged ran 11 cm left)
  "LaneCenteringPauseOnSignal": True,  # StarPilot default
  "PauseLateralOnSignal": False,       # sunnypilot BlinkerPauseLateralControl=0
  "DisengageOnAccelerator": False,     # sunnypilot DisengageOnAccelerator=0
  "IsLdwEnabled": False,               # sunnypilot IsLdwEnabled=0
  "RecordFront": False,                # sunnypilot RecordFront=0
  "TurnAssist": False,                 # Ioniq-6-tuned angle assist on signaled turns; untested on the Ram, and it only runs above 36 mph here
}
OTHER = {
  "LaneCenterOffset": 0.0,             # Dalton's own line is within StarPilot's 8 cm centering deadband
  "LongitudinalPersonality": 1,        # sunnypilot: standard
}


def main():
  p = Params()
  for key, value in BOOLS.items():
    p.put_bool(key, value)
  for key, value in OTHER.items():
    p.put(key, value)
  # sunnypilot shut the comma off 30 min after parking; StarPilot's shortest option is 1 hour (stock is 30 h)
  p.put(POWER_KEY, to_value(PowerPolicy(enabled=True, delay_hours=1, cutoff_tenths=118)))

  # sunnypilot-only key raised to 3 h for the install; put Dalton's 30 min back in case of a rollback
  legacy = Path(p.get_param_path()) / "MaxTimeOffroad"
  if legacy.exists():
    legacy.write_text("1800")

  for key in (*BOOLS, *OTHER, POWER_KEY):
    print(f"{key} = {p.get(key)}")


if __name__ == "__main__":
  main()

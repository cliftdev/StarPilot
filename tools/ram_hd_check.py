"""Offline smoke test for the Ram 2500 HD Mega Cab patches.

Run from the repo root:
  python tools/ram_hd_check.py
Checks: StarPilot fingerprints the truck's real FW to RAM_HD_5TH_GEN, the
resulting CarParams can steer, and the Mega Cab/HD values are applied.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "opendbc_repo"), ROOT]

from opendbc.car import structs  # noqa: E402
from opendbc.car.fw_versions import match_fw_to_car  # noqa: E402
from opendbc.car.chrysler.interface import CarInterface  # noqa: E402
from opendbc.car.chrysler.values import CAR  # noqa: E402

ECU = structs.CarParams.Ecu
# Read from the truck's own CarParams (qlog, route 00000186, 2026-11)
TRUCK_FW = [
  (ECU.abs, 0x747, b'68504022AC'),
  (ECU.fwdRadar, 0x753, b'68462657AF'),
  (ECU.eps, 0x761, b'68421036AC'),
  (ECU.combinationMeter, 0x742, b'68437746AD'),
  (ECU.srs, 0x744, b'68428503AA'),
  (ECU.engine, 0x7e0, b'P6370031PC'),
]


def car_fw():
  out = []
  for ecu, addr, ver in TRUCK_FW:
    fw = structs.CarParams.CarFw(ecu=ecu, address=addr, subAddress=0, fwVersion=ver, brand="chrysler")
    out.append(fw)
  return out


def main():
  fws = car_fw()
  exact, matches = match_fw_to_car(fws, "", log=False)
  print("fingerprint matches:", matches, "| exact:", exact)
  assert matches == {CAR.RAM_HD_5TH_GEN}, matches

  fingerprint = {i: {} for i in range(8)}
  cp = CarInterface.get_params(CAR.RAM_HD_5TH_GEN, fingerprint, fws, alpha_long=False, is_release=False, docs=False)
  print(f"dashcamOnly={cp.dashcamOnly} wheelbase={cp.wheelbase} centerToFront={cp.centerToFront:.3f} steerRatio={cp.steerRatio} "
        f"tireStiffness F/R={cp.tireStiffnessFront:.0f}/{cp.tireStiffnessRear:.0f} rotInertia={cp.rotationalInertia:.0f} "
        f"deadzone={cp.lateralTuning.torque.steeringAngleDeadzoneDeg} minSteerSpeed={cp.minSteerSpeed} mass={cp.mass:.0f} "
        f"torque={cp.lateralTuning.torque.latAccelFactor}/{cp.lateralTuning.torque.friction}")
  assert cp.dashcamOnly is False
  assert abs(cp.wheelbase - 4.08) < 1e-6 and abs(cp.steerRatio - 17.8) < 1e-6
  assert abs(cp.centerToFront - 4.08 * 0.44) < 1e-6
  assert (round(cp.tireStiffnessFront), round(cp.tireStiffnessRear)) == (65155, 80926)
  # sunnypilot's EnforceTorqueControl reset the 0.25 deg deadzone to 0.0 on the truck, so match what actually drove
  assert cp.lateralTuning.torque.steeringAngleDeadzoneDeg == 0.0
  # torque model fitted from the truck's logs (tools in ~/comma-logs/tools/torque_fit.py)
  t = cp.lateralTuning.torque
  assert abs(t.latAccelFactor - 1.58) < 1e-6 and abs(t.friction - 0.265) < 1e-6, (t.latAccelFactor, t.friction)
  # values read from the truck's own CarParams on sunnypilot
  assert abs(cp.mass - 3541.0) < 0.5 and abs(cp.rotationalInertia - 13826.5) < 1.0 and cp.minSteerSpeed == 16.0

  # A Ram 1500 must be unaffected by the HD-only changes
  cp15 = CarInterface.get_params(CAR.RAM_1500_5TH_GEN, fingerprint, [], alpha_long=False, is_release=False, docs=False)
  assert cp15.lateralTuning.torque.steeringAngleDeadzoneDeg == 0.0 and abs(cp15.wheelbase - 3.88) < 1e-6
  print("Ram 1500 unchanged: OK")

  try:
    from openpilot.starpilot.feature_capabilities import lateral_supported
    print("StarPilot lateral_supported (lane centering admission):", lateral_supported(cp))
    assert lateral_supported(cp)
  except ImportError as e:
    print("feature_capabilities import skipped:", e)
  # learned torque must be usable for Chrysler, as sunnypilot's Live Torque Params toggle allowed
  import ast
  src = open(os.path.join(ROOT, "openpilot/selfdrive/locationd/torqued.py")).read()
  allowed = next(ast.literal_eval(n.value) for n in ast.parse(src).body
                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "ALLOWED_CARS")
  print("torqued ALLOWED_CARS:", allowed)
  assert cp.brand in allowed

  # The truck's panda latches interruptRateCan2 ~3 s into every drive. StarPilot raises "Controls Mismatch"
  # for any panda fault not on its per-car allowlist, so the HD must allow that one bit and nothing else.
  from openpilot.cereal import log
  from opendbc.car.structs import car
  from openpilot.starpilot.aol.panda_faults import blocking_fault_list, blocking_fault_mask
  F = log.PandaState.FaultType
  sc = cp.safetyConfigs[0]
  print(f"safety: {sc.safetyModel} param {int(sc.safetyParam)}")
  live = car.CarParams.new_message(brand=cp.brand, carFingerprint=cp.carFingerprint,
                                   safetyConfigs=[{"safetyModel": str(sc.safetyModel), "safetyParam": int(sc.safetyParam)}])
  for p in (cp, live):
    assert not blocking_fault_list([F.interruptRateCan2], p)
    assert not blocking_fault_mask(1 << 3, p)
    assert blocking_fault_list([F.interruptRateCan1], p) and blocking_fault_list([F.relayMalfunction], p)
    assert blocking_fault_list([F.interruptRateCan2, F.relayMalfunction], p)
    assert blocking_fault_mask((1 << 3) | (1 << 2), p)
  assert blocking_fault_list([F.interruptRateCan2], cp15), "Ram 1500 must keep StarPilot's default"
  print("panda fault policy: interruptRateCan2 allowed on the HD only: OK")
  print("ALL OK")


if __name__ == "__main__":
  main()

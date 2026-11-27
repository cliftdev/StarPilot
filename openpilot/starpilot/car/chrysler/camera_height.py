"""Road-camera height correction for the lifted Ram 2500 HD (this fork's truck only).

The comma sits at the top of the windshield of a leveled 2500 on 35s, about 1.88 m above the road. The driving model has
no height input and judges scale from the vehicles it learned on, so from up here the road looks shrunk:
  - Cheddar estimates its own height as 1.33 m (extrinsicsCalibration.height, route 0000018e) and reads 12 ft lanes as
    2.64 m, under Lane Centering's 2.6 m minimum a third of the time (Lane Centering then refuses: "unqualified_model").
  - WMI v11 estimates 1.63 m (sunnypilot route 00000185) and reads 3.10 m.
  Both imply a lens near 1.84-1.92 m (model height x 3.66 m / lane width read).
Scaling the vertical component of the calibrated viewing direction by LENS / model height shows the model the road
exactly as a camera that much lower would see it. Objects above the road surface look shorter than they are.
Device replay of Cheddar on 0000018e with x1.39: lanes 2.61 -> 3.44 m, weave-band reaction x1.10, curve following x1.06.
"""
import numpy as np

LENS_HEIGHT_M = 1.88
# height each model reports for itself on this truck without the correction
MODEL_HEIGHT_M = {"cheddar": 1.33, "wmi1123": 1.63}
MAX_SCALE = 1.6


def road_camera_height_scale(cp, model_id) -> float:
  """How many times lower the model is shown the camera; 1.0 = unchanged."""
  try:
    if str(cp.carFingerprint) != "RAM_HD_5TH_GEN":
      return 1.0
  except AttributeError:
    return 1.0
  height = MODEL_HEIGHT_M.get(str(model_id))
  if not height:
    return 1.0
  return float(min(max(LENS_HEIGHT_M / height, 1.0), MAX_SCALE))


def height_matrix(scale: float) -> np.ndarray:
  """Applied in the calibrated frame (x forward, y right, z down), right after device_from_calib."""
  return np.diag([1.0, 1.0, float(scale)])


_selected: tuple[float, str] = (-1.0, "")


def active_small_model_id() -> str:
  """The small model selected for this drive (what modeld loads unless it falls back to Cheddar).

  Re-read only when preferences.json changes: the UI calls this on every calibration update."""
  global _selected
  try:
    from openpilot.starpilot.models.manager import ROOT, preferences
    try:
      mtime = (ROOT / "preferences.json").stat().st_mtime
    except OSError:
      mtime = 0.0
    if mtime != _selected[0]:
      _selected = (mtime, str(preferences(ROOT)["small"]))
    return _selected[1]
  except Exception:
    return ""

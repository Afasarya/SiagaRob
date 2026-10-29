"""Inference model SiagaRob dengan pengaman keluaran (dipakai server AI, Task 06).

Model memprediksi SELISIH level (delta = level_t+30 - level_t), lalu level_30m = level + delta.
Alasan: model pohon tidak mengekstrapolasi nilai absolut di atas rentang data latih; delta tetap
terbatas walau level masukan melampaui data latih (mis. HC-SR04 di Wokwi diatur ekstrem).

Pengaman:
  - masukan non-numerik/NaN/inf/di luar rentang sensor -> InvalidInput (tidak menghasilkan prediksi);
  - warmup: None sampai 60 sampel terkumpul (tidak ada prediksi dari riwayat parsial);
  - rain dijepit 0..80 mm/jam (dengan peringatan);
  - delta dijepit ke rentang yang terlihat saat training; level_30m dijepit ke rentang sensor;
  - sensor_ok=false -> reliable=False (level Edge 1 tertahan, bukan pembacaan baru);
  - label selalu EXPERIMENTAL.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features as F  # noqa: E402

LEVEL_MIN_CM = -200.0
LEVEL_MAX_CM = 198.0
RAIN_MAX = 80.0
LABEL = "EXPERIMENTAL"


class InvalidInput(ValueError):
    """Masukan tidak layak; jangan hasilkan prediksi."""


class ModelMismatch(RuntimeError):
    """Model tidak cocok dengan definisi fitur/horizon saat ini."""


@dataclass
class Prediction:
    level_now: float
    level_30m: float
    delta_cm: float
    reliable: bool = True
    clamped: bool = False
    warnings: list[str] = field(default_factory=list)
    label: str = LABEL


def _check_meta(md: dict) -> None:
    if md.get("feature_names") != F.FEATURE_NAMES:
        raise ModelMismatch(f"urutan fitur model {md.get('feature_names')} != {F.FEATURE_NAMES}")
    if md.get("horizon_steps") != F.HORIZON_STEPS:
        raise ModelMismatch(f"horizon model {md.get('horizon_steps')} != {F.HORIZON_STEPS}")
    if md.get("target_type") != "delta":
        raise ModelMismatch("model bukan model delta; latih ulang dengan ai/train.py")
    if "delta_bounds_cm" not in md:
        raise ModelMismatch("metadata tanpa delta_bounds_cm")


def predict_levels(model, X: np.ndarray, delta_bounds: tuple[float, float] | None = None) -> np.ndarray:
    """Prediksi level +30 menit untuk matriks fitur X (kolom sesuai FEATURE_NAMES)."""
    X = np.asarray(X, dtype=float)
    delta = model.predict(X)
    if delta_bounds is not None:
        delta = np.clip(delta, delta_bounds[0], delta_bounds[1])
    return np.clip(X[:, F.FEATURE_NAMES.index("level")] + delta, LEVEL_MIN_CM, LEVEL_MAX_CM)


def _finite_number(v, name: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float, np.integer, np.floating)):
        raise InvalidInput(f"{name} harus angka, bukan {type(v).__name__}")
    v = float(v)
    if not math.isfinite(v):
        raise InvalidInput(f"{name} bukan bilangan hingga: {v}")
    return v


class Predictor:
    def __init__(self, model, metadata: dict) -> None:
        _check_meta(metadata)
        self.model = model
        self.metadata = metadata
        b = metadata["delta_bounds_cm"]
        self._bounds = (float(b[0]), float(b[1]))
        self._buf = F.FeatureBuffer()

    @classmethod
    def load(cls, path: str | Path) -> "Predictor":
        obj = joblib.load(path)
        return cls(obj["model"], obj["metadata"])

    def reset(self) -> None:
        """Panggil saat Edge offline / ada jeda data agar riwayat tidak menyambung lintas celah."""
        self._buf.reset()

    @property
    def ready(self) -> bool:
        return self._buf.ready

    def update(self, level_cm, rain_mm_h, sensor_ok: bool = True) -> Prediction | None:
        level = _finite_number(level_cm, "level_cm")
        rain = _finite_number(rain_mm_h, "rain_mm_h")
        if not (LEVEL_MIN_CM <= level <= LEVEL_MAX_CM):
            raise InvalidInput(f"level_cm {level} di luar rentang sensor [{LEVEL_MIN_CM}, {LEVEL_MAX_CM}]")
        warnings: list[str] = []
        if rain < 0.0 or rain > RAIN_MAX:
            warnings.append(f"rain_mm_h {rain} dijepit ke 0..{RAIN_MAX}")
            rain = min(max(rain, 0.0), RAIN_MAX)

        feat = self._buf.push(level, rain)
        if feat is None:
            return None  # warmup

        raw_delta = float(self.model.predict(np.asarray([feat], dtype=float))[0])
        if not math.isfinite(raw_delta):
            raise InvalidInput("model menghasilkan nilai tidak hingga")
        lo, hi = self._bounds
        delta = min(max(raw_delta, lo), hi)
        clamped = delta != raw_delta
        out = level + delta
        clipped = min(max(out, LEVEL_MIN_CM), LEVEL_MAX_CM)
        clamped = clamped or clipped != out
        if clamped:
            warnings.append("keluaran model dijepit ke rentang aman")
        reliable = bool(sensor_ok)
        if not sensor_ok:
            warnings.append("sensor_ok=false: level adalah nilai tertahan, prediksi tidak andal")
        return Prediction(level_now=level, level_30m=clipped, delta_cm=clipped - level,
                          reliable=reliable, clamped=clamped, warnings=warnings)


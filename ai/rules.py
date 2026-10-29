"""Logika penetapan status risiko dan histeresis kontrol pompa (PRD §11).

Aturan Status Risiko:
  effective_level = max(level_now, level_30m)
  - AMAN    : < 105 cm
  - SIAGA_1 : >= 105 cm
  - SIAGA_2 : >= 120 cm
  - SIAGA_3 : >= 140 cm

Aturan Aktuator AI:
  - SIAGA_3: Pompa ON, Sirine ON
  - SIAGA_2: Pompa ON, Sirine OFF
  - SIAGA_1 / AMAN: Pompa OFF (dengan histeresis), Sirine OFF

Histeresis Pompa OFF:
  Ambang aktivasi pompa adalah SIAGA_2 (120 cm).
  Pompa baru boleh OFF jika level berada >10 cm di bawah ambang (yaitu < 110 cm)
  selama minimal 5 sampel berturut-turut.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskStatus = Literal["AMAN", "SIAGA_1", "SIAGA_2", "SIAGA_3"]

THRESHOLD_SIAGA_1 = 105.0
THRESHOLD_SIAGA_2 = 120.0
THRESHOLD_SIAGA_3 = 140.0

HYSTERESIS_DROP_CM = 10.0
HYSTERESIS_SAMPLES = 5
PUMP_OFF_THRESHOLD = THRESHOLD_SIAGA_2 - HYSTERESIS_DROP_CM  # 110.0 cm


def determine_status(level_now: float, level_30m: float) -> RiskStatus:
    """Tentukan status risiko berdasarkan max(level_now, level_30m)."""
    eff = max(level_now, level_30m)
    if eff >= THRESHOLD_SIAGA_3:
        return "SIAGA_3"
    if eff >= THRESHOLD_SIAGA_2:
        return "SIAGA_2"
    if eff >= THRESHOLD_SIAGA_1:
        return "SIAGA_1"
    return "AMAN"


@dataclass
class Decision:
    status: RiskStatus
    effective_level: float
    pump: Literal["ON", "OFF"]
    siren: bool
    reason: str
    hysteresis_count: int


class DecisionEngine:
    """Menghitung status dan keputusan aktuator dengan histeresis."""

    def __init__(self) -> None:
        self.pump_on: bool = False
        self.siren_on: bool = False
        self.below_count: int = 0  # hitungan sampel berturut-turut di bawah batas histeresis

    def reset(self) -> None:
        self.pump_on = False
        self.siren_on = False
        self.below_count = 0

    def evaluate(self, level_now: float, level_30m: float, sensor_ok: bool = True) -> Decision:
        status = determine_status(level_now, level_30m)
        eff = max(level_now, level_30m)

        # Evaluasi Sirine: hanya menyala pada SIAGA_3
        new_siren = status == "SIAGA_3"

        # Evaluasi Pompa
        reasons: list[str] = ["model+rule"]
        if not sensor_ok:
            reasons.append("sensor_degraded")

        if status in ("SIAGA_2", "SIAGA_3"):
            # Ambang aktivasi terpenuhi
            self.pump_on = True
            self.below_count = 0
            reasons.append(f"{status}:pump_on")
        else:
            # Di bawah SIAGA_2 (< 120 cm)
            if self.pump_on:
                # Pompa sedang ON -> uji histeresis
                if eff < PUMP_OFF_THRESHOLD:
                    self.below_count += 1
                    reasons.append(f"hys_eval({self.below_count}/{HYSTERESIS_SAMPLES})")
                    if self.below_count >= HYSTERESIS_SAMPLES:
                        self.pump_on = False
                        reasons.append("hys_cleared:pump_off")
                else:
                    # Berada di antara 110 dan 120 cm -> histeresis tertahan, count reset
                    self.below_count = 0
                    reasons.append("hys_hold:pump_on")
            else:
                self.below_count = 0
                reasons.append("normal:pump_off")

        self.siren_on = new_siren
        return Decision(
            status=status,
            effective_level=eff,
            pump="ON" if self.pump_on else "OFF",
            siren=self.siren_on,
            reason=";".join(reasons),
            hysteresis_count=self.below_count,
        )


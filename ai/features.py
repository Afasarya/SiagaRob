"""Fitur model SiagaRob. SATU definisi dipakai training DAN inference (PRD §11).

Waktu: 1 sampel telemetri = 1 menit WAKTU SIMULASI (Edge 1 publish tiap 2 detik nyata).
Maka +30 menit simulasi = 30 sampel ke depan = ~60 detik nyata.

Fitur (urutan tetap, tanpa tide_sin/tide_cos):
  level   : level_cm saat ini (cm)
  rate_5  : (level_t - level_{t-5}) / 5   [cm per menit simulasi; sama dengan Edge 1]
  rain_10 : rata-rata rain_mm_h pada 10 sampel terakhir (termasuk saat ini) [mm/jam]
  rain_60 : rata-rata rain_mm_h pada 60 sampel terakhir (termasuk saat ini) [mm/jam]
rain_10/rain_60 adalah definisi proyek ini (PRD hanya menyebut nama fitur).
"""
from __future__ import annotations

from collections import deque

FEATURE_NAMES: list[str] = ["level", "rate_5", "rain_10", "rain_60"]
HORIZON_STEPS = 30          # sampel ke depan untuk target
MINUTES_PER_SAMPLE = 1      # 1 pesan = 1 menit simulasi
SECONDS_REAL_PER_SAMPLE = 2
RATE_STEPS = 5
RAIN_SHORT = 10
RAIN_LONG = 60
WARMUP_SAMPLES = RAIN_LONG  # sampel yang dibutuhkan sebelum semua fitur terdefinisi


class FeatureBuffer:
    """Hitung fitur secara streaming. Hanya memakai data sampai saat ini (tanpa kebocoran masa depan)."""

    def __init__(self) -> None:
        self._levels: deque[float] = deque(maxlen=RATE_STEPS + 1)
        self._rain: deque[float] = deque(maxlen=RAIN_LONG)

    def push(self, level_cm: float, rain_mm_h: float) -> list[float] | None:
        """Tambah satu sampel. Mengembalikan [level, rate_5, rain_10, rain_60], atau None selama warmup."""
        self._levels.append(float(level_cm))
        self._rain.append(float(rain_mm_h))
        if len(self._rain) < RAIN_LONG:
            return None
        lv = list(self._levels)
        rain = list(self._rain)
        rate_5 = (lv[-1] - lv[0]) / RATE_STEPS
        rain_10 = sum(rain[-RAIN_SHORT:]) / RAIN_SHORT
        rain_60 = sum(rain) / RAIN_LONG
        return [lv[-1], rate_5, rain_10, rain_60]

    @property
    def ready(self) -> bool:
        return len(self._rain) >= RAIN_LONG

    def reset(self) -> None:
        self._levels.clear()
        self._rain.clear()


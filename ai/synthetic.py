"""Data sintetis SiagaRob (label: SYNTHETIC). Bukan observasi lapangan.

Parameter sumber PRD §11: level dasar 80 cm; amplitudo pasang 15 cm dengan variasi spring-neap
5 cm; koefisien limpasan 0.25; noise sigma 1 cm. Tidak ada data eksternal.

Asumsi proyek (PRD tidak merinci persamaan; dicatat di docs/AI_EVALUATION.md):
  - 1 baris = 1 menit simulasi (1 pesan telemetri Edge 1).
  - pasang(t) = A(t) * sin(2*pi*t / 745 menit),  A(t) = 15 + 5*sin(2*pi*t / (14.77 hari)).
  - limpasan(t) = d * limpasan(t-1) + 0.25 * hujan_mm_per_menit(t - LAG)   (0.25 cm per mm hujan),
    d = 0.995 (drainase lambat, e-folding ~200 menit), LAG = 15 menit.
  - level_mentah(t) = 80 + pasang(t) + limpasan(t) + N(0, 1 cm).
  - level_cm(t) = median 5 pembacaan terakhir dari level_mentah, dijepit ke rentang sensor
    [-200, 198] cm. Ini yang dilaporkan Edge 1 (median filter 5), jadi model dilatih pada
    sinyal yang sama dengan yang diterimanya saat inference.
  - hujan: badai acak (Poisson, rata-rata 1/hari) berbentuk lonceng, puncak 8-80 mm/jam,
    durasi 30-480 menit; badai boleh tumpang tindih (dijepit 0-80 mm/jam).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DATA_LABEL = "SYNTHETIC"

BASE_LEVEL_CM = 80.0
TIDE_AMPLITUDE_CM = 15.0
SPRING_NEAP_CM = 5.0
RUNOFF_COEF = 0.25
NOISE_SIGMA_CM = 1.0
TIDE_PERIOD_MIN = 745.0                # ~12,42 jam (semidiurnal)
SPRING_NEAP_PERIOD_MIN = 14.77 * 1440  # ~14,77 hari
RUNOFF_DECAY = 0.995
RUNOFF_LAG_MIN = 15
STORMS_PER_DAY = 1.0
STORM_MIN_MIN, STORM_MAX_MIN = 30, 480
STORM_PEAK_MIN, STORM_PEAK_MAX = 8.0, 80.0
RAIN_MAX = 80.0
MEDIAN_WINDOW = 5
LEVEL_MIN_CM = -200.0  # 200 - 400 cm (batas HC-SR04 pada Edge 1)
LEVEL_MAX_CM = 198.0   # 200 - 2 cm


def generate(seed: int = 42, days: int = 60) -> pd.DataFrame:
    """Kembalikan DataFrame: minute, rain_mm_h, level_raw_cm, level_cm, data_label."""
    rng = np.random.default_rng(seed)
    n = int(days * 1440)
    t = np.arange(n, dtype=float)

    rain = np.zeros(n)
    n_storms = rng.poisson(STORMS_PER_DAY * days)
    for _ in range(n_storms):
        start = int(rng.integers(0, n))
        dur = int(rng.integers(STORM_MIN_MIN, STORM_MAX_MIN + 1))
        peak = float(rng.uniform(STORM_PEAK_MIN, STORM_PEAK_MAX))
        x = np.arange(dur)
        shape = np.exp(-0.5 * ((x - dur / 2) / (dur / 5)) ** 2)
        end = min(n, start + dur)
        rain[start:end] += peak * shape[: end - start]
    rain = np.clip(rain * (1.0 + rng.normal(0, 0.05, n)), 0.0, RAIN_MAX)

    amp = TIDE_AMPLITUDE_CM + SPRING_NEAP_CM * np.sin(2 * np.pi * t / SPRING_NEAP_PERIOD_MIN)
    tide = amp * np.sin(2 * np.pi * t / TIDE_PERIOD_MIN)

    inflow = np.zeros(n)
    inflow[RUNOFF_LAG_MIN:] = RUNOFF_COEF * rain[: n - RUNOFF_LAG_MIN] / 60.0
    runoff = np.zeros(n)
    for i in range(1, n):
        runoff[i] = RUNOFF_DECAY * runoff[i - 1] + inflow[i]

    raw = BASE_LEVEL_CM + tide + runoff + rng.normal(0, NOISE_SIGMA_CM, n)
    raw = np.clip(raw, LEVEL_MIN_CM, LEVEL_MAX_CM)
    level = pd.Series(raw).rolling(MEDIAN_WINDOW, min_periods=1).median().to_numpy()

    return pd.DataFrame(
        {
            "minute": np.arange(n),
            "rain_mm_h": rain,
            "level_raw_cm": raw,
            "level_cm": level,
            "data_label": DATA_LABEL,
        }
    )

"""Training model +30 menit simulasi SiagaRob (Task 05 - Ditingkatkan).

Model dilatih untuk memprediksi SELISIH level (delta = level_{t+30} - level_t).
Formulasi ini mencegah pohon keputusan kolaps / gagal ekstrapolasi saat ketinggian air
berada di luar rentang data latih, dan menjamin keluaran yang stabil.

Jalankan dari root repo:  python ai/train.py [--seed 42] [--days 60] [--out ai]
Data 100% SINTETIS (lihat ai/synthetic.py). Model berlabel EXPERIMENTAL; bukan prediksi banjir
yang divalidasi untuk Semarang.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features as F  # noqa: E402
import predictor as P  # noqa: E402
import synthetic as S  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TRAIN_FRACTION = 0.8
TARGET_IMPROVEMENT_PCT = 20.0
MODEL_PARAMS = dict(
    max_iter=300,
    learning_rate=0.05,
    max_leaf_nodes=31,
    min_samples_leaf=40,
    early_stopping=False,
)


def build_dataset(df) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Bangun (X, y_target, y_delta, idx).

    X: matriks fitur [level, rate_5, rain_10, rain_60]
    y_target: level pada t + 30 menit
    y_delta: perubahan level (level_{t+30} - level_t)
    idx: indeks waktu t
    """
    levels = df["level_cm"].to_numpy()
    rain = df["rain_mm_h"].to_numpy()
    n = len(df)
    buf = F.FeatureBuffer()
    X, y_target, y_delta, idx = [], [], [], []
    for t in range(n):
        feat = buf.push(levels[t], rain[t])
        if feat is None or t + F.HORIZON_STEPS >= n:
            continue
        X.append(feat)
        target = levels[t + F.HORIZON_STEPS]
        y_target.append(target)
        y_delta.append(target - levels[t])
        idx.append(t)
    return (
        np.asarray(X, dtype=float),
        np.asarray(y_target, dtype=float),
        np.asarray(y_delta, dtype=float),
        np.asarray(idx, dtype=int),
    )


def chronological_split(n_rows: int, train_fraction: float = TRAIN_FRACTION, gap: int = F.HORIZON_STEPS):
    """Indeks baris (urut waktu): 80% awal train, 20% akhir test, TANPA shuffle.

    `gap` baris di antaranya dibuang (purge) agar target train (t+30) tidak menyentuh periode test.
    """
    cut = int(n_rows * train_fraction)
    train_idx = np.arange(0, cut)
    test_idx = np.arange(min(cut + gap, n_rows), n_rows)
    return train_idx, test_idx


def train_and_evaluate(seed: int = 42, days: int = 60) -> dict:
    df = S.generate(seed=seed, days=days)
    X, y_target, y_delta, t_idx = build_dataset(df)
    tr, te = chronological_split(len(X))

    # Latih model pada perubahan level (delta)
    model = HistGradientBoostingRegressor(random_state=seed, **MODEL_PARAMS)
    model.fit(X[tr], y_delta[tr])

    delta_bounds = (float(np.min(y_delta[tr])), float(np.max(y_delta[tr])))

    # Prediksi level +30m dengan formulasi delta + level_now
    pred_level = P.predict_levels(model, X[te], delta_bounds=delta_bounds)
    base_level = X[te, F.FEATURE_NAMES.index("level")]  # baseline persistence (level saat ini)

    mae_model = float(mean_absolute_error(y_target[te], pred_level))
    mae_base = float(mean_absolute_error(y_target[te], base_level))
    improvement = (mae_base - mae_model) / mae_base * 100.0 if mae_base > 0 else 0.0
    target_met = bool(improvement >= TARGET_IMPROVEMENT_PCT)

    # Evaluasi per kondisi / subset
    subsets = {}
    rain_mask = X[te, F.FEATURE_NAMES.index("rain_60")] > 5.0
    if np.any(rain_mask):
        subsets["hujan_signifikan"] = {
            "deskripsi": "rain_60 > 5 mm/h",
            "count": int(np.sum(rain_mask)),
            "mae_model": float(mean_absolute_error(y_target[te][rain_mask], pred_level[rain_mask])),
            "mae_baseline": float(mean_absolute_error(y_target[te][rain_mask], base_level[rain_mask])),
        }

    high_water_mask = base_level >= 105.0  # ambang SIAGA_1 ke atas
    if np.any(high_water_mask):
        subsets["level_siaga"] = {
            "deskripsi": "level_now >= 105 cm",
            "count": int(np.sum(high_water_mask)),
            "mae_model": float(mean_absolute_error(y_target[te][high_water_mask], pred_level[high_water_mask])),
            "mae_baseline": float(mean_absolute_error(y_target[te][high_water_mask], base_level[high_water_mask])),
        }

    metadata = {
        "data_label": S.DATA_LABEL,
        "evaluation_status": "EXPERIMENTAL",
        "evaluation_note": "Dilatih dan diuji pada data sintetis; bukan observasi lapangan. Bukan prediksi banjir akurat Semarang.",
        "model": "HistGradientBoostingRegressor",
        "target_type": "delta",
        "delta_bounds_cm": [delta_bounds[0], delta_bounds[1]],
        "model_params": {**MODEL_PARAMS, "random_state": seed},
        "feature_names": F.FEATURE_NAMES,
        "feature_definitions": {
            "level": "level_cm saat ini",
            "rate_5": "(level_t - level_{t-5}) / 5 [cm/menit simulasi]",
            "rain_10": "rata-rata rain_mm_h 10 sampel terakhir",
            "rain_60": "rata-rata rain_mm_h 60 sampel terakhir",
        },
        "warmup_samples": F.WARMUP_SAMPLES,
        "horizon_steps": F.HORIZON_STEPS,
        "minutes_per_sample": F.MINUTES_PER_SAMPLE,
        "seconds_real_per_sample": F.SECONDS_REAL_PER_SAMPLE,
        "horizon_sim_minutes": F.HORIZON_STEPS * F.MINUTES_PER_SAMPLE,
        "horizon_real_seconds": F.HORIZON_STEPS * F.SECONDS_REAL_PER_SAMPLE,
        "seed": seed,
        "synthetic_params": {
            "days": days,
            "base_level_cm": S.BASE_LEVEL_CM,
            "tide_amplitude_cm": S.TIDE_AMPLITUDE_CM,
            "spring_neap_cm": S.SPRING_NEAP_CM,
            "runoff_coef": S.RUNOFF_COEF,
            "noise_sigma_cm": S.NOISE_SIGMA_CM,
            "runoff_decay": S.RUNOFF_DECAY,
            "runoff_lag_min": S.RUNOFF_LAG_MIN,
            "tide_period_min": S.TIDE_PERIOD_MIN,
            "spring_neap_period_min": S.SPRING_NEAP_PERIOD_MIN,
        },
        "split": {
            "type": "chronological",
            "shuffle": False,
            "train_fraction": TRAIN_FRACTION,
            "purge_gap_rows": F.HORIZON_STEPS,
            "rows_total": int(len(X)),
            "rows_train": int(len(tr)),
            "rows_test": int(len(te)),
        },
        "metrics": {
            "mae_model_cm": mae_model,
            "mae_baseline_cm": mae_base,
            "improvement_pct": improvement,
            "target_improvement_pct": TARGET_IMPROVEMENT_PCT,
            "target_met": target_met,
            "test_rows": int(len(te)),
            "baseline": "prediksi level saat ini (persistence)",
            "subsets": subsets,
        },
        "versions": {"scikit-learn": sklearn.__version__, "numpy": np.__version__},
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    return {"model": model, "metadata": metadata}


def render_report(md: dict) -> str:
    m = md["metrics"]
    sp = md["split"]
    status = "TERCAPAI" if m["target_met"] else "TIDAK tercapai"
    sub_lines = []
    if "subsets" in m:
        for k, v in m["subsets"].items():
            sub_lines.append(
                f"- **{v['deskripsi']}** ({v['count']} sampel test): MAE model = {v['mae_model']:.3f} cm, "
                f"MAE baseline = {v['mae_baseline']:.3f} cm"
            )
    sub_text = "\n".join(sub_lines) if sub_lines else "Tidak ada subset khusus."

    return f"""# Evaluasi Model AI SiagaRob (Task 05)

> **Label: {md['data_label']} / {md['evaluation_status']}.** Data dan evaluasi sepenuhnya sintetis. Ini bukan observasi lapangan dan **bukan** prediksi banjir yang akurat/tervalidasi untuk Semarang.

Dibuat oleh `ai/train.py` pada {md['trained_at']} (seed {md['seed']}, scikit-learn {md['versions']['scikit-learn']}).

## Formulasi Model Delta & Pengaman (Peningkatan AI)
- Model dilatih memprediksi perubahan level $\\Delta = \\text{{level}}_{{t+30}} - \\text{{level}}_t$.
- Level +30m dihitung dari $\\text{{level}}_t + \\text{{clip}}(\\Delta, \\Delta_{{\\min}}, \\Delta_{{\\max}})$, lalu dijepit ke batas fisik sensor `[{P.LEVEL_MIN_CM}, {P.LEVEL_MAX_CM}]`.
- Pendekatan delta mencegah pohon keputusan menghasilkan nilai statis/ekstrapolasi aneh saat level air melampaui rentang training.
- Inferensi dibungkus kelas `Predictor` di `ai/predictor.py` yang menolak nilai tidak hingga, memvalidasi rentang sensor, menandai `reliable=False` saat sensor offline/error, dan menolak menghasilkan prediksi selama masa warmup (60 sampel).

## Hasil (test set kronologis yang sama untuk model dan baseline)
| Metrik | Nilai |
|---|---|
| MAE model (HistGradientBoostingRegressor delta) | {m['mae_model_cm']:.3f} cm |
| MAE baseline (level saat ini) | {m['mae_baseline_cm']:.3f} cm |
| Perbaikan relatif | {m['improvement_pct']:.1f} % |
| Target perbaikan 20% | {status} |
| Baris test | {m['test_rows']} |

### Evaluasi Subset Tertarget
{sub_text}

## Waktu dan horizon
1 sampel telemetri = 1 menit **waktu simulasi** (Edge 1 publish tiap 2 detik nyata, kompresi 30x). Target +30 menit simulasi = {md['horizon_steps']} sampel ke depan = sekitar {md['horizon_real_seconds']} detik nyata. Definisi ini sama di training dan inference (`ai/features.py`).

## Fitur (urutan tetap)
{chr(10).join(f"- `{k}`: {v}" for k, v in md['feature_definitions'].items())}

`tide_sin`/`tide_cos` **tidak** dipakai. Warmup inference: {md['warmup_samples']} sampel (≈{md['warmup_samples'] * md['seconds_real_per_sample']} detik nyata) sebelum semua fitur tersedia.

## Data sintetis
Parameter sumber PRD: level dasar {md['synthetic_params']['base_level_cm']} cm, amplitudo pasang {md['synthetic_params']['tide_amplitude_cm']} cm dengan variasi spring-neap {md['synthetic_params']['spring_neap_cm']} cm, koefisien limpasan {md['synthetic_params']['runoff_coef']}, noise sigma {md['synthetic_params']['noise_sigma_cm']} cm. Durasi {md['synthetic_params']['days']} hari, 1 baris/menit simulasi, filter median 5 sampel diikutsertakan.

## Split
Kronologis tanpa shuffle: {sp['train_fraction']:.0%} awal untuk training ({sp['rows_train']} baris), {sp['purge_gap_rows']} baris dibuang sebagai pembatas (purge, agar target train tidak menyentuh periode test), sisanya untuk test ({sp['rows_test']} baris).

## Batasan
- Tidak ada data eksternal (BMKG/PantauBanjir/dll.) yang dipakai; memasukkannya perlu desain fitur dan pelatihan ulang (PRD §11).
- Model belum divalidasi pada data lapangan.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--report", default=str(REPO_ROOT / "docs" / "AI_EVALUATION.md"))
    args = ap.parse_args(argv)

    res = train_and_evaluate(args.seed, args.days)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": res["model"], "metadata": res["metadata"]}, out / "model.joblib")
    (out / "model_meta.json").write_text(json.dumps(res["metadata"], indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.report).write_text(render_report(res["metadata"]), encoding="utf-8")

    m = res["metadata"]["metrics"]
    print(
        f"[{res['metadata']['data_label']}/{res['metadata']['evaluation_status']}] split kronologis "
        f"train={res['metadata']['split']['rows_train']} test={res['metadata']['split']['rows_test']}"
    )
    print(f"MAE model    : {m['mae_model_cm']:.3f} cm")
    print(f"MAE baseline : {m['mae_baseline_cm']:.3f} cm")
    print(f"Perbaikan    : {m['improvement_pct']:.1f}% (target 20%: {'tercapai' if m['target_met'] else 'TIDAK tercapai'})")
    if "subsets" in m:
        for k, v in m["subsets"].items():
            print(f"  Subset {k:18s}: model {v['mae_model']:.3f} vs base {v['mae_baseline']:.3f} cm ({v['count']} baris)")
    print(f"Tersimpan    : {out / 'model.joblib'}, {out / 'model_meta.json'}, {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

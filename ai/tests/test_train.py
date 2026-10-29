import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.metrics import mean_absolute_error

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import features as F  # noqa: E402
import predictor as P  # noqa: E402
import synthetic as S  # noqa: E402
import train as T  # noqa: E402

DAYS = 12  # kecil agar tes cepat


@pytest.fixture(scope="module")
def df():
    return S.generate(seed=7, days=DAYS)


@pytest.fixture(scope="module")
def dataset(df):
    return T.build_dataset(df)


@pytest.fixture(scope="module")
def result():
    return T.train_and_evaluate(seed=7, days=DAYS)


# ---------- fitur ----------
def test_urutan_fitur():
    assert F.FEATURE_NAMES == ["level", "rate_5", "rain_10", "rain_60"]
    assert "tide_sin" not in F.FEATURE_NAMES and "tide_cos" not in F.FEATURE_NAMES


def test_fitur_dihitung_benar():
    buf = F.FeatureBuffer()
    out = None
    for i in range(60):
        out = buf.push(100.0 + i, 10.0 if i >= 50 else 0.0)  # level naik 1 cm/menit
        if i < 59:
            assert out is None, "warmup: belum boleh ada fitur"
    level, rate5, rain10, rain60 = out
    assert level == 159.0
    assert rate5 == pytest.approx(1.0)
    assert rain10 == pytest.approx(10.0)   # 10 sampel terakhir semuanya 10
    assert rain60 == pytest.approx(100.0 / 60.0)
    assert buf.ready


def test_rate_5_negatif_saat_turun():
    buf = F.FeatureBuffer()
    last = None
    for i in range(70):
        last = buf.push(200.0 - 2 * i, 0.0)
    assert last[1] == pytest.approx(-2.0)


def test_horizon_konsisten_time_compression():
    assert F.HORIZON_STEPS * F.MINUTES_PER_SAMPLE == 30
    assert F.SECONDS_REAL_PER_SAMPLE == 2
    assert F.HORIZON_STEPS * F.SECONDS_REAL_PER_SAMPLE == 60


# ---------- dataset: target & kebocoran ----------
def test_target_adalah_level_plus_30(df, dataset):
    X, y_target, y_delta, idx = dataset
    levels = df["level_cm"].to_numpy()
    assert np.array_equal(y_target, levels[idx + F.HORIZON_STEPS])
    assert np.allclose(y_delta, y_target - X[:, 0])
    # fitur 'level' = level pada t (bukan masa depan)
    assert np.array_equal(X[:, 0], levels[idx])
    assert idx[0] == F.WARMUP_SAMPLES - 1
    assert idx[-1] == len(df) - F.HORIZON_STEPS - 1


def test_tanpa_kebocoran_fitur_tidak_bergantung_masa_depan(df):
    """Mengubah data setelah titik t tidak boleh mengubah fitur pada t."""
    t0 = 3000
    lv = df["level_cm"].to_numpy().copy()
    rn = df["rain_mm_h"].to_numpy().copy()

    def feat_at(levels, rain, t):
        b = F.FeatureBuffer()
        out = None
        for i in range(t + 1):
            out = b.push(levels[i], rain[i])
        return out

    base = feat_at(lv, rn, t0)
    lv2, rn2 = lv.copy(), rn.copy()
    lv2[t0 + 1:] += 999.0
    rn2[t0 + 1:] = 80.0
    assert feat_at(lv2, rn2, t0) == base


def test_fitur_streaming_identik_dengan_dataset(df, dataset):
    """Baris training = keluaran FeatureBuffer yang sama dengan inference."""
    X, _, _, idx = dataset
    b = F.FeatureBuffer()
    got = {}
    for t in range(len(df)):
        f = b.push(df["level_cm"].iat[t], df["rain_mm_h"].iat[t])
        if f is not None:
            got[t] = f
    for k in (0, 100, len(idx) // 2, len(idx) - 1):
        assert list(X[k]) == got[int(idx[k])]


def test_tidak_ada_nan(dataset):
    X, y_target, y_delta, _ = dataset
    assert np.isfinite(X).all() and np.isfinite(y_target).all() and np.isfinite(y_delta).all()


# ---------- split ----------
def test_split_kronologis_tanpa_acak():
    tr, te = T.chronological_split(1000)
    assert len(tr) == 800
    assert np.array_equal(tr, np.arange(800))          # urut, bukan acak
    assert tr.max() < te.min()
    assert te.min() - tr.max() - 1 == F.HORIZON_STEPS   # purge
    assert te[-1] == 999 and np.array_equal(te, np.arange(te[0], 1000))


def test_target_train_tidak_menyentuh_periode_test(result):
    sp = result["metadata"]["split"]
    assert sp["shuffle"] is False and sp["type"] == "chronological"
    last_train_row = sp["rows_train"] - 1
    first_test_row = sp["rows_total"] - sp["rows_test"]
    assert last_train_row + F.HORIZON_STEPS < first_test_row


# ---------- data sintetis ----------
def test_sintetis_reproducible_dan_berlabel(df):
    df2 = S.generate(seed=7, days=DAYS)
    assert df.equals(df2)
    assert not df.equals(S.generate(seed=8, days=DAYS))
    assert set(df["data_label"]) == {"SYNTHETIC"}


def test_sintetis_parameter_masuk_akal(df):
    lv = df["level_cm"]
    assert 75 < lv.mean() < 100
    assert df["rain_mm_h"].between(0, 80).all()
    assert (df["rain_mm_h"] > 0).any()
    assert S.BASE_LEVEL_CM == 80 and S.TIDE_AMPLITUDE_CM == 15 and S.SPRING_NEAP_CM == 5
    assert S.RUNOFF_COEF == 0.25 and S.NOISE_SIGMA_CM == 1


# ---------- determinisme & delta training ----------
def test_training_deterministik_seed_sama(result):
    again = T.train_and_evaluate(seed=7, days=DAYS)
    m1, m2 = result["metadata"]["metrics"], again["metadata"]["metrics"]
    assert m1["mae_model_cm"] == pytest.approx(m2["mae_model_cm"], abs=1e-9)
    assert m1["mae_baseline_cm"] == m2["mae_baseline_cm"]
    X = np.array([[90.0, 0.1, 5.0, 3.0], [120.0, -0.2, 40.0, 30.0]])
    assert np.allclose(result["model"].predict(X), again["model"].predict(X), atol=1e-9)


def test_metadata_lengkap_dan_jujur(result):
    md = result["metadata"]
    for k in ["feature_names", "model_params", "seed", "trained_at", "metrics", "evaluation_status", "data_label",
              "horizon_steps", "split", "synthetic_params", "target_type", "delta_bounds_cm"]:
        assert k in md
    assert md["data_label"] == "SYNTHETIC" and md["evaluation_status"] == "EXPERIMENTAL"
    assert md["target_type"] == "delta"
    assert md["feature_names"] == F.FEATURE_NAMES
    assert md["model"] == "HistGradientBoostingRegressor"


# ---------- pengaman predictor (pencegahan output tidak wajar) ----------
def test_predictor_pengaman_dan_warmup(result):
    pred = P.Predictor(result["model"], result["metadata"])
    # 1. Warmup: 59 sampel pertama None
    for i in range(59):
        assert pred.update(80.0, 0.0) is None
    # Sampel ke-60 menghasilkan prediksi
    res = pred.update(80.0, 0.0)
    assert res is not None
    assert isinstance(res.level_30m, float)
    assert res.label == "EXPERIMENTAL"
    assert res.reliable is True

    # 2. Level ekstrem di luar batas sensor ditolak
    with pytest.raises(P.InvalidInput):
        pred.update(300.0, 0.0)  # > 198 cm

    # 3. Input NaN / Inf ditolak
    with pytest.raises(P.InvalidInput):
        pred.update(float("nan"), 0.0)
    with pytest.raises(P.InvalidInput):
        pred.update(80.0, float("inf"))

    # 4. Hujan berlebih dijepit secara aman dengan warning
    res2 = pred.update(85.0, 150.0)  # > 80 mm/h
    assert any("dijepit" in w for w in res2.warnings)

    # 5. Sensor error (sensor_ok=False) menghasilkan peringatan reliable=False
    res_err = pred.update(85.0, 10.0, sensor_ok=False)
    assert res_err.reliable is False
    assert any("sensor_ok=false" in w for w in res_err.warnings)

    # 6. Reset mengembalikan ke fase warmup
    pred.reset()
    assert pred.update(80.0, 0.0) is None


def test_main_menulis_artefak(tmp_path):
    rc = T.main(["--seed", "3", "--days", "8", "--out", str(tmp_path), "--report", str(tmp_path / "r.md")])
    assert rc == 0
    import joblib
    obj = joblib.load(tmp_path / "model.joblib")
    assert obj["metadata"]["target_type"] == "delta"
    assert hasattr(obj["model"], "predict")
    assert (tmp_path / "model_meta.json").exists() and (tmp_path / "r.md").exists()

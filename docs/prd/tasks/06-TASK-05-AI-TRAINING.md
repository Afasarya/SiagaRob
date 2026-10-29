# TASK 05 — Training dan evaluasi model

## Tujuan
Membuat dataset sintetis yang transparan, training model +30 menit, dan laporan MAE vs baseline.

## Scope
- `ai/train.py`, `ai/requirements.txt`, data sintetis reproducible, seed.
- HistGradientBoostingRegressor.
- Fitur level, rate_5, rain_10, rain_60; hapus tide_sin/tide_cos.
- Split kronologis 80/20.
- Baseline: prediksi level saat ini.
- Simpan `model.joblib` dan metadata fitur/model/metric.

## Acceptance criteria
- Training dapat diulang dengan seed yang sama.
- Split tidak acak.
- MAE model dan baseline dihitung dari test set yang sama.
- Laporan menyebut target perbaikan 20% hanya jika benar-benar tercapai.
- Tidak mengklaim data sintetis sebagai data lapangan.

## Prompt siap pakai

```text
TASK 05 — TRAINING MODEL SIAGAROB

Baca PRD induk dan handoff sebelumnya. Implementasikan ai/train.py, requirements.txt, generator data sintetis reproducible, dan laporan evaluasi.
Gunakan parameter sumber: level dasar 80 cm; amplitudo pasang 15 cm dengan variasi spring-neap 5 cm; koefisien limpasan 0.25; noise sigma 1 cm. Jangan gunakan tide_sin/tide_cos sebagai fitur. Fitur wajib dan urutannya: level, rate_5, rain_10, rain_60. Pastikan target level +30 menit konsisten dengan time-compression telemetri; dokumentasikan arti 30 menit simulasi versus waktu nyata.
Gunakan HistGradientBoostingRegressor. Split kronologis 80% awal train dan 20% akhir test, tanpa shuffle. Bandingkan MAE model dengan baseline prediksi level saat ini pada baris test yang sama. Simpan model.joblib dan metadata yang mencatat fitur, urutan fitur, parameter, seed, timestamp training, MAE model, MAE baseline, dan status evaluasi. Jangan menjanjikan perbaikan 20%; laporkan angka yang dihasilkan.
Tambahkan tes untuk urutan fitur, tidak ada leakage target, determinisme, dan metrik. Beri label seluruh data sebagai SYNTHETIC. Jangan memakai data eksternal diam-diam atau mengubah spesifikasi tanpa catatan. Jalankan training dan tes jika dependency tersedia, laporkan angka MAE aktual dan handoff.
```

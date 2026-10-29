# Evaluasi Model AI SiagaRob (Task 05)

> **Label: SYNTHETIC / EXPERIMENTAL.** Data dan evaluasi sepenuhnya sintetis. Ini bukan observasi lapangan dan **bukan** prediksi banjir yang akurat/tervalidasi untuk Semarang.

Dibuat oleh `ai/train.py` pada 2026-10-29T14:46:16.221724+00:00 (seed 42, scikit-learn 1.7.2).

## Formulasi Model Delta & Pengaman (Peningkatan AI)
- Model dilatih memprediksi perubahan level $\Delta = \text{level}_{t+30} - \text{level}_t$.
- Level +30m dihitung dari $\text{level}_t + \text{clip}(\Delta, \Delta_{\min}, \Delta_{\max})$, lalu dijepit ke batas fisik sensor `[-200.0, 198.0]`.
- Pendekatan delta mencegah pohon keputusan menghasilkan nilai statis/ekstrapolasi aneh saat level air melampaui rentang training.
- Inferensi dibungkus kelas `Predictor` di `ai/predictor.py` yang menolak nilai tidak hingga, memvalidasi rentang sensor, menandai `reliable=False` saat sensor offline/error, dan menolak menghasilkan prediksi selama masa warmup (60 sampel).

## Hasil (test set kronologis yang sama untuk model dan baseline)
| Metrik | Nilai |
|---|---|
| MAE model (HistGradientBoostingRegressor delta) | 2.026 cm |
| MAE baseline (level saat ini) | 2.480 cm |
| Perbaikan relatif | 18.3 % |
| Target perbaikan 20% | TIDAK tercapai |
| Baris test | 17233 |

### Evaluasi Subset Tertarget
- **rain_60 > 5 mm/h** (2718 sampel test): MAE model = 2.248 cm, MAE baseline = 3.227 cm
- **level_now >= 105 cm** (852 sampel test): MAE model = 1.807 cm, MAE baseline = 2.461 cm

## Waktu dan horizon
1 sampel telemetri = 1 menit **waktu simulasi** (Edge 1 publish tiap 2 detik nyata, kompresi 30x). Target +30 menit simulasi = 30 sampel ke depan = sekitar 60 detik nyata. Definisi ini sama di training dan inference (`ai/features.py`).

## Fitur (urutan tetap)
- `level`: level_cm saat ini
- `rate_5`: (level_t - level_{t-5}) / 5 [cm/menit simulasi]
- `rain_10`: rata-rata rain_mm_h 10 sampel terakhir
- `rain_60`: rata-rata rain_mm_h 60 sampel terakhir

`tide_sin`/`tide_cos` **tidak** dipakai. Warmup inference: 60 sampel (≈120 detik nyata) sebelum semua fitur tersedia.

## Data sintetis
Parameter sumber PRD: level dasar 80.0 cm, amplitudo pasang 15.0 cm dengan variasi spring-neap 5.0 cm, koefisien limpasan 0.25, noise sigma 1.0 cm. Durasi 60 hari, 1 baris/menit simulasi, filter median 5 sampel diikutsertakan.

## Split
Kronologis tanpa shuffle: 80% awal untuk training (69048 baris), 30 baris dibuang sebagai pembatas (purge, agar target train tidak menyentuh periode test), sisanya untuk test (17233 baris).

## Batasan
- Tidak ada data eksternal (BMKG/PantauBanjir/dll.) yang dipakai; memasukkannya perlu desain fitur dan pelatihan ulang (PRD §11).
- Model belum divalidasi pada data lapangan.

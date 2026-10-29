# TASK 06 — AI server, prediksi dan keputusan

## Tujuan
Menerima telemetry Edge 1, menyusun fitur identik dengan training, menerbitkan prediksi, status, dan command hanya saat AUTO.

## Scope
- `ai/ai_server.py`, konfigurasi, buffer data, validasi payload.
- Subscribe `edge/+/telemetry`, prediksi pada pesan Edge 1.
- Publish `ai/prediction`.
- Status offline setelah tidak ada telemetry Edge 1 selama 30 detik real time.
- Status threshold dan hysteresis.
- Jangan mengirim command AI bila mode bukan AUTO.

## Acceptance criteria
- Urutan/perhitungan fitur sama dengan train.py.
- Invalid/stale telemetry tidak menghasilkan prediksi seolah valid.
- Status dari max(level_now, level_30m).
- Histeresis 5 sampel sesuai aturan.
- AUTO/MANUAL dihormati dan dites unit.
- Prediksi berisi alasan dan sequence yang dapat ditelusuri.

## Prompt siap pakai

```text
TASK 06 — AI SERVER

Baca PRD induk, model metadata, dan handoff task sebelumnya. Implementasikan ai/ai_server.py dengan paho-mqtt. Subscribe siagarob/PROJECT_ID/edge/+/telemetry, validasi payload, simpan buffer cukup untuk rain_10/rain_60 dan rate_5, lalu prediksi setiap telemetry edge1.
Fitur dan preprocessing harus identik dengan ai/train.py serta metadata model. Jika metadata atau model tidak cocok, fail clearly; jangan menerka urutan fitur. Publish prediksi ke ai/prediction dengan level_now, level_30m, status, reason, seq. Status memakai max(level_now, level_30m): AMAN <105; SIAGA_1 >=105; SIAGA_2 >=120; SIAGA_3 >=140.
Implementasikan hysteresis: pompa baru OFF setelah level berada lebih dari 10 cm di bawah ambang selama 5 sampel berturut-turut. Command dari AI hanya dipublish ketika mode edge2 adalah AUTO. Dalam MANUAL, jangan mengirim command yang menimpa operator. Jika tidak ada telemetry Edge1 selama 30 detik waktu nyata, tandai OFFLINE dan publish prediction/status yang sesuai. Jangan mengklaim data aktual lapangan.
Tambahkan unit test untuk threshold boundary, hysteresis, mode AUTO/MANUAL, invalid telemetry, fitur identik dan timeout. Tes tidak boleh memerlukan broker live; gunakan unit/mocking. Laporkan tes aktual dan handoff.
```

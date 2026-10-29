# TASK 09 — Integrasi live MQTT dan grafik

## Tujuan
Menyambungkan dashboard ke MQTT WebSocket, menampilkan data aktual dari edge simulasi dan prediksi AI.

## Scope
- mqtt.js melalui WebSocket TLS `wss://broker.hivemq.com:8884/mqtt`.
- Input/konfigurasi PROJECT_ID, unique client ID.
- Cards, chart 60 titik, threshold lines, device online/offline, sensor warning.
- MQTT reconnect dan parsing aman.
- Label data IoT_SIMULATED.

## Acceptance criteria
- Dashboard menerima telemetry/prediction dari topic yang benar.
- Chart maksimum 60 titik dan menangani sequence duplikat/invalid.
- Status offline dari LWT/timeout.
- Kegagalan koneksi terlihat, UI tetap bisa dipakai.
- Latensi diukur, bukan diasumsikan.

## Prompt siap pakai

```text
TASK 09 — DASHBOARD LIVE MQTT

Baca PRD induk dan handoff task sebelumnya. Integrasikan mqtt.js pada aplikasi Next.js di sisi client saja (misalnya hook/client module yang hanya dijalankan di browser) melalui wss://broker.hivemq.com:8884/mqtt. PROJECT_ID wajib dapat dikonfigurasi dengan validasi; client ID dashboard harus unik. Subscribe hanya topic project: edge/edge1/telemetry, edge/edge2/telemetry, edge/edge1/status, edge/edge2/status, ai/prediction.
Tampilkan tinggi air Edge1, rate, sensor_ok, rain_mm_h, suhu, kelembapan, pump, siren, mode, prediksi +30 menit, status dan waktu pesan terakhir. Buat grafik aktual dan prediksi dengan maksimal 60 titik serta garis ambang 105/120/140 cm. Validasi JSON, unit, field, sequence dan timestamp sebelum render. Jangan menampilkan pesan invalid sebagai data valid. Bedakan status offline dari nilai terakhir; nilai lama harus diberi label stale/offline.
Tampilkan badge IoT SIMULATED untuk telemetry Wokwi, EXPERIMENTAL untuk model sintetis, dan source metadata untuk data resmi. Implementasikan reconnect, koneksi status, error state, dan jangan membuat dashboard blank saat broker mati. Jangan membuat koneksi MQTT saat server-side rendering, dan pastikan cleanup unsubscribe/disconnect berjalan saat komponen unmount agar tidak ada koneksi ganda. Jangan publish command dalam task ini. Jalankan lint/build Next.js dan buat checklist uji browser dengan broker; bila koneksi live tidak dapat diuji, nyatakan demikian. Ukur latensi hanya jika timestamp yang memadai tersedia. Handoff.
```

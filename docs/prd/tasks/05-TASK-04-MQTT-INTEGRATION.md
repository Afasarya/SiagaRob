# TASK 04 — Integrasi MQTT dan alat uji

## Tujuan
Buktikan kontrak MQTT dan sediakan alat debug sebelum AI/dashboard penuh.

## Scope
- Script Python CLI untuk subscribe topic project, validasi JSON schema ringan, publish command uji.
- Konfigurasi `PROJECT_ID` dari env.
- Panduan `mosquitto_sub` atau MQTT Explorer.
- Jangan mengirim command retained.

## Acceptance criteria
- Topic dibentuk dari satu PROJECT_ID.
- Payload valid diterima, JSON invalid ditolak dengan pesan jelas.
- Command test publish non-retained QoS1.
- README berisi langkah uji broker dan batas privasi broker publik.

## Prompt siap pakai

```text
TASK 04 — MQTT CONTRACT TESTING

Baca PRD induk dan handoff task sebelumnya. Buat alat debugging/testing MQTT di folder tools/ atau ai/tools/ yang tidak mengubah firmware tanpa alasan.
Sediakan CLI Python untuk subscribe siagarob/PROJECT_ID/#, menampilkan timestamp lokal, topic, payload, dan validasi field minimum telemetry edge1/edge2, prediction, command. PROJECT_ID harus berasal dari environment/config, bukan disalin ke banyak tempat. Sediakan mode publish command uji dengan konfirmasi eksplisit dan retain=false QoS1. Jangan publish command actuator secara otomatis saat program start.
Tambahkan contoh mosquitto_sub/MQTT Explorer, cara memastikan topic unik, dan peringatan bahwa HiveMQ publik bukan broker privat. Jangan mengirim token rahasia. Buat unit test untuk parser/payload yang tidak membutuhkan internet. Jalankan tes dan laporkan output aktual. Jangan mengklaim koneksi broker berhasil jika tidak benar-benar dites. Handoff.
```

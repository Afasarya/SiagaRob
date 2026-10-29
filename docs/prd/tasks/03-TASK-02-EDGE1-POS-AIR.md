# TASK 02 — Firmware Edge 1 Pos Air

## Tujuan
Implementasikan ESP32 virtual pembaca ketinggian air, filter sensor, validasi, telemetri, status MQTT dan reconnect.

## Scope
- Wokwi sketch, `diagram.json`, `libraries.txt`.
- HC-SR04 TRIG GPIO 5, ECHO GPIO 18, LED GPIO 2.
- `TINGGI_PASANG_CM=200`, median 5 sampel, rate kenaikan, error sensor dan last-valid.
- Wi-Fi Wokwi, MQTT, client ID unik, LWT, publish online/offline, telemetry tiap 2 detik.
- 1 pesan = 1 menit waktu simulasi; dokumentasikan bagaimana rate dan timestamp/sequence dihitung.

## Acceptance criteria
- Kompilasi firmware berhasil jika toolchain tersedia.
- JSON sesuai kontrak `edge/edge1/telemetry`.
- Jarak invalid dan lonjakan >50 cm menandai `sensor_ok=false`.
- Nilai valid terakhir dipertahankan saat error.
- Reconnect 3 detik dan status LWT sesuai.
- Tidak ada command actuator di Edge 1.

## Prompt siap pakai

```text
TASK 02 — EDGE 1 POS AIR

Baca 00-PRD-CONTEXT.md, hasil/handoff Task 01, dan task ini. Implementasikan hanya firmware Edge 1 di edge1_wokwi/.
Gunakan ESP32 + HC-SR04 TRIG GPIO5, ECHO GPIO18, LED GPIO2. Hitung level_cm = 200 - distance_cm. Terapkan median filter 5 pembacaan. Implementasikan rate_cm_min berdasarkan definisi 5 sampel dan time-compression yang terdokumentasi. Tolak jarak 0, jarak di luar 2..400 cm, atau lonjakan >50 cm/sampel: sensor_ok=false dan pertahankan nilai valid terakhir.
Hubungkan Wokwi-GUEST dengan WiFi.begin("Wokwi-GUEST", "", 6), MQTT broker.hivemq.com port 1883, client ID unik memuat PROJECT_ID dan edge1, buffer minimum 512, LWT status offline retained QoS1, publish online saat tersambung, reconnect dengan jeda 3 detik. Publish telemetry tiap 2 detik ke siagarob/PROJECT_ID/edge/edge1/telemetry QoS0 non-retained dengan field yang ditetapkan PRD.
Periksa apakah Wokwi diagram dan libraries diperlukan dan buat file yang benar. Jangan mengarang sensor atau mengubah pin/topic/payload. Jangan menyatakan broker live telah dites bila hanya compile. Jalankan pemeriksaan yang tersedia, jelaskan langkah uji Wokwi, dan berikan handoff.
```

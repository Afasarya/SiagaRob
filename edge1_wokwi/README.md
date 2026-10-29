# Edge 1 — Pos Air (ESP32 + HC-SR04, Wokwi)

Berkas: `sketch.ino` (jaringan/MQTT/pin), `edge1_logic.h` (logika murni, diuji di PC), `diagram.json`, `libraries.txt`.

## Penggunaan di Wokwi
1. Buat project ESP32 baru di https://wokwi.com, salin isi `sketch.ino`, `edge1_logic.h`, `diagram.json`, `libraries.txt`.
2. Ganti `PROJECT_ID` di `sketch.ino` sama dengan `.env`.
3. Jalankan. Serial monitor menampilkan jarak dan JSON. Ubah jarak HC-SR04 dengan klik sensor.
4. Pantau: `mosquitto_sub -h broker.hivemq.com -t "siagarob/PROJECT_ID/edge/edge1/#" -v` atau klien MQTT web.

## Pin
HC-SR04 TRIG=GPIO5, ECHO=GPIO18 (VCC 5V, GND); LED=GPIO2 (via R 220Ω). LED menyala bila `sensor_ok` dan MQTT tersambung. Tidak ada aktuator/subscribe command di Edge 1.

## Pemrosesan
- `level_cm = 200 - jarak` (`TINGGI_PASANG_CM=200`); tidak dipotong ke 0..200 (jarak >200 menghasilkan level negatif sesuai rumus PRD).
- Pembacaan tidak valid: jarak 0 (timeout), <2 atau >400 cm, atau selisih >50 cm dari pembacaan valid terakhir → `sensor_ok=false`, level valid terakhir dipertahankan, pembacaan tersebut tidak masuk jendela median.
- Median 5: dari ≤5 pembacaan valid terakhir (kurang dari 5 di awal → median yang tersedia).
- `rate_cm_min = (level_sekarang − level 5 sampel sebelumnya) / 5`. Hingga ada 5 sampel sebelumnya, nilainya 0. Saat sensor error, level yang dipertahankan tetap masuk riwayat (waktu terus berjalan).
- Belum pernah ada pembacaan valid: `level_cm=0`, `sensor_ok=false`.
- Batasan: bila level benar-benar melonjak >50 cm permanen, filter lonjakan akan menolak terus (`sensor_ok=false`) sampai pembacaan kembali dalam 50 cm dari nilai valid terakhir. Ini mengikuti PRD apa adanya.

## Kompresi waktu
Publish tiap 2 detik nyata dianggap **1 menit simulasi**, sehingga satu sampel = 1 menit, `rate_cm_min` per sampel, dan 30 menit ke depan = 30 pesan (~60 detik nyata). `seq` bertambah 1 per publish (mulai 1); `uptime_ms` = `millis()` waktu nyata, bukan waktu simulasi. Tidak ada timestamp wall-clock di payload.

## MQTT
Broker `broker.hivemq.com:1883`; client ID `siagarob-edge1-PROJECT_ID`; buffer 512. Telemetry `…/edge/edge1/telemetry` QoS0 non-retained. Status `…/edge/edge1/status`: LWT `offline` (QoS1, retained), `online` retained saat tersambung. Reconnect tiap 3 detik tanpa memblokir loop.

**Batasan PubSubClient:** `publish()` selalu QoS0, jadi pesan `online` retained tetapi QoS0; hanya LWT yang QoS1. Payload dibangun dengan `snprintf` (bukan ArduinoJson) agar urutan/format field dapat diuji di PC; hasil identik dengan kontrak.

## Pengujian di PC
```powershell
cd edge1_wokwi
g++ -std=c++17 -Wall -Wextra -o test\build\test_edge1.exe test\test_edge1_logic.cpp
.\test\build\test_edge1.exe
g++ -std=c++17 -Wall -Wextra -fsyntax-only -x c++ -Itest\stubs -I. sketch.ino   # cek sintaks dengan stub
```
Stub di `test/stubs/` hanya untuk cek sintaks; **bukan** kompilasi ESP32 dan tidak menguji WiFi/MQTT sungguhan.

## Uji manual Wokwi (belum dijalankan oleh agent)
1. Jarak 120 → `level_cm≈80`, `sensor_ok=true`. 2. Jarak 0/500 → `sensor_ok=false`, level tertahan (T6). 3. Stop simulasi → status `offline` (LWT, T7; LWT terkirim setelah keepalive habis ±15–25 s). 4. Ukur latensi telemetri sampai dashboard (target <3 s) pada Task 04/09.


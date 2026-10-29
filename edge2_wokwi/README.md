# Edge 2 — Pos Hujan + Aktuator (ESP32, Wokwi)

Berkas: `sketch.ino` (jaringan/MQTT/pin), `edge2_logic.h` (logika murni, diuji di PC), `diagram.json`, `libraries.txt` (PubSubClient, ArduinoJson, DHT sensor library).

## Penggunaan di Wokwi
1. Project ESP32 baru di https://wokwi.com; salin `sketch.ino`, `edge2_logic.h`, `diagram.json`, `libraries.txt`.
2. Ganti `PROJECT_ID` di `sketch.ino` sama dengan `.env`.
3. Putar potensiometer = simulasi hujan (0–80 mm/jam). Ubah suhu/kelembapan DHT22 dengan klik sensor.

## Pin
DHT22 DATA=GPIO15 · Potensiometer SIG=GPIO34 · Relay/LED merah (pompa)=GPIO26 (via R 220Ω) · Buzzer=GPIO27 (`tone` 2 kHz saat siren). Tidak ada pin/aktuator lain.

## Pemrosesan
- ADC 0..4095 → 0..80 mm/jam linear (dijepit), moving average 3 pembacaan (awal: rata-rata sampel yang ada).
- DHT22 gagal baca (NaN): pertahankan nilai valid terakhir; sebelum pembacaan pertama berhasil nilainya 0 (tidak ada flag di kontrak untuk ini).
- `hum_pct` dibulatkan ke bilangan bulat; `rain_mm_h` dan `temp_c` 1 desimal. Sebuah nilai seperti 24.0 dapat dicetak `24` oleh ArduinoJson (nilai JSON sama).
- Publish telemetri tiap 2 detik ke `…/edge/edge2/telemetry` (QoS0, non-retained); `seq` mulai 1.

## Command (`…/edge/edge2/commands`, subscribe QoS1)
Payload wajib lengkap: `pump` (`ON|OFF`, huruf besar), `siren` (boolean), `mode` (`AUTO|MANUAL`), `source` (`ai|dashboard`). Aturan:

| source | mode edge | hasil |
|---|---|---|
| `dashboard` | apa pun | diterapkan (otoritatif); `mode` dalam command menjadi mode baru (`MANUAL` mengunci AI, `AUTO` mengembalikan ke AI) |
| `ai` | AUTO, command `mode=AUTO` | diterapkan |
| `ai` | MANUAL | **ditolak** (mode tetap, pump/siren tidak berubah) |
| `ai` | AUTO, command `mode=MANUAL` | ditolak (AI tidak boleh mengunci MANUAL) |

JSON rusak, bukan objek, field hilang/tipe salah/nilai di luar daftar, atau payload >256 byte: diabaikan sepenuhnya (state tidak berubah) dan dicatat di serial (`command (N byte): diabaikan: …`). Keadaan aktual (`pump`, `siren`, `mode`) dilaporkan di telemetri berikutnya. State awal: pompa OFF, siren off, AUTO. Command tidak retained, jadi tidak ada aktuator yang hidup sendiri saat reboot.

Catatan: dalam AUTO, edge **tidak** punya aturan sendiri; ia hanya mengikuti AI (Task 06). Tanpa AI, pompa tetap OFF.

## MQTT
`broker.hivemq.com:1883`, client ID `siagarob-edge2-PROJECT_ID`, buffer 512, keepalive 15 s. Status `…/edge/edge2/status`: LWT `offline` (QoS1, retained); `online` retained saat tersambung (QoS0, batas PubSubClient). Reconnect tiap 3 detik non-blocking; subscribe ulang di setiap koneksi.

## Pengujian di PC
Header ArduinoJson diunduh sekali ke `test/vendor/` (di-ignore Git):
```powershell
cd edge2_wokwi
New-Item -ItemType Directory -Force test\vendor,test\build | Out-Null
curl.exe -sSL -o test\vendor\ArduinoJson.h https://github.com/bblanchon/ArduinoJson/releases/download/v7.4.2/ArduinoJson-v7.4.2.h
g++ -std=c++17 -Wall -Wextra -Itest\vendor -o test\build\test_edge2.exe test\test_edge2_logic.cpp
.\test\build\test_edge2.exe
g++ -std=c++17 -Wall -Wextra -fsyntax-only -x c++ -Itest\stubs -Itest\vendor -I. sketch.ino
```
Stub di `test/stubs/` hanya untuk cek sintaks; **bukan** kompilasi ESP32 dan bukan uji hardware/WiFi/MQTT.

## Uji manual Wokwi + MQTT (belum dijalankan oleh agent)
Gunakan klien MQTT (mis. `mosquitto_pub`) ke topic `siagarob/PROJECT_ID/edge/edge2/commands`:
1. AI ON (AUTO): `{"pump":"ON","siren":false,"mode":"AUTO","source":"ai"}` → LED menyala; serial `diterapkan`; telemetri `pump":"ON"`.
2. Kunci MANUAL: `{"pump":"OFF","siren":false,"mode":"MANUAL","source":"dashboard"}` → LED mati, telemetri `mode":"MANUAL"`.
3. **Bukti MANUAL menolak AI (T4):** kirim ulang perintah 1 → serial `diabaikan: mode MANUAL, command source=ai ditolak`; LED tetap mati; telemetri tetap `OFF`/`MANUAL`.
4. Kembali AUTO (T5): `{"pump":"OFF","siren":false,"mode":"AUTO","source":"dashboard"}` lalu perintah 1 → LED menyala.
5. Invalid: kirim `{"pump":"on"}` atau `halo` → serial `diabaikan`, state tidak berubah.
6. Ukur latensi command→relay (target <3 s) pada Task 04/10.


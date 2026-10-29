# SiagaRob — firmware perangkat Wokwi

Paket ini berisi firmware untuk dua ESP32 virtual serta diagram rangkaian Wokwi.

## Struktur

```text
siagarob/
├── edge1_wokwi/
│   ├── sketch.ino
│   ├── diagram.json
│   └── libraries.txt
├── edge2_wokwi/
│   ├── sketch.ino
│   ├── diagram.json
│   └── libraries.txt
├── ai/
├── dashboard/
├── docs/
└── .env.example
```

## Sebelum simulasi

1. Buka masing-masing folder edge sebagai proyek Wokwi ESP32 terpisah.
2. Impor/copy `diagram.json`, `sketch.ino`, dan `libraries.txt` dari folder yang sesuai.
3. Ganti `PROJECT_ID` pada kedua `sketch.ino` dengan ID unik kelompok yang sama. Nilai bawaan `siagarob_ganti_id_kelompok` hanyalah placeholder.
4. Pastikan `PROJECT_ID` yang sama digunakan oleh `ai_server.py` dan dashboard ketika keduanya dibuat.
5. Jalankan kedua simulasi. Keduanya menggunakan Wi-Fi `Wokwi-GUEST` dan broker publik `broker.hivemq.com:1883`.

## Pin

### Edge 1 — Pos Air

- HC-SR04 TRIG: GPIO 5
- HC-SR04 ECHO: GPIO 18
- LED status: GPIO 2
- Tinggi referensi sensor: 200 cm

### Edge 2 — Pos Hujan dan Aktuator

- DHT22 DATA/SDA: GPIO 15
- Potensiometer SIG: GPIO 34
- Relay IN: GPIO 26 (aktif HIGH karena diagram memakai transistor `npn`)
- Buzzer (+): GPIO 27

## Topik MQTT

Prefix: `siagarob/PROJECT_ID/`

- `edge/edge1/telemetry`
- `edge/edge1/status`
- `edge/edge2/telemetry`
- `edge/edge2/status`
- `edge/edge2/commands`

Status menggunakan Last Will `offline` retained QoS 1 dan menerbitkan `online` saat tersambung. Perintah aktuator tidak retained. Edge 2 menolak perintah dari sumber `ai` saat mode lokal MANUAL.

## Contoh payload perintah

```json
{"pump":"ON","siren":false,"mode":"AUTO","source":"ai"}
```

```json
{"pump":"OFF","siren":false,"mode":"MANUAL","source":"dashboard"}
```

Untuk tombol AUTO pada dashboard, kirim `mode: "AUTO"` dan `source: "dashboard"`; sesudah itu server AI dapat mengirim perintah saat mode AUTO.

## Catatan batasan

- Curah hujan merupakan simulasi potensiometer, bukan hasil pengukuran sensor hujan nyata.
- Prediksi 30 menit, penggabungan aturan status, AI, dan dashboard berada di folder terpisah dan tidak disediakan oleh dua sketch ini.
- Broker HiveMQ publik tidak cocok untuk data rahasia. Gunakan PROJECT_ID unik karena topiknya dapat diakses pihak lain.
- Relay Wokwi hanya mensimulasikan sakelar; jangan menghubungkan beban listrik berbahaya pada prototipe fisik tanpa desain dan proteksi yang benar.

# Laporan Pengujian Mutu (QA End-to-End & Skenario T1–T7)

- **Tanggal Pengujian**: 29 Oktober 2026
- **Target Sistem**: SiagaRob (Prototipe Peringatan Dini Pasang Surut Semarang Utara & Timur)
- **Status Akhir Skenario T1–T7**: **SEMUA PASS** (7/7 Skenario Lulus Terverifikasi)
- **Status Test Suite Unit**: **106 PASSED** (33 AI, 66 Tools MQTT, 7 FastAPI Backend)
- **Status Validasi Fondasi**: **22 CHECKS PASS** (Geometri AOI Identik Byte-per-Byte)
- **Status Frontend Next.js**: **Build Sukses, 0 Error, 0 Warning**

---

## 1. Matriks Hasil Pengujian Skenario Utama (T1–T7)

Pengujian skenario dieksekusi secara otomatis dan deterministik melalui skrip [`scripts/test_e2e_scenarios.py`](../scripts/test_e2e_scenarios.py):

| Skenario | Deskripsi & Masukan | Hasil yang Diharapkan (Expected) | Hasil Aktual (Actual) | Status | Bukti Log / Eksekusi |
|---|---|---|---|:---:|---|
| **T1** | Hujan 0 mm/h, air rendah (80.0 cm) | Status AMAN, Pompa OFF, Sirine OFF | Status: `AMAN`, Pompa: `OFF`, Sirine: `OFF` | **PASS** | `res["prediction"]["status"] == "AMAN"`, `decision.pump == "OFF"` |
| **T2** | Kenaikan air bertahap (85 &rarr; 121 cm), hujan 35 mm/h dalam mode AUTO | Prediksi melewati ambang SIAGA_2 (&ge;120 cm), Pompa ON otomatis via command AI | Status: `SIAGA_2`, Pompa: `ON`, Command AI terbit: `{"pump":"ON", "mode":"AUTO", "source":"ai"}` | **PASS** | Command AI terkirim ke `siagarob/PROJECT_ID/edge/edge2/commands` (QoS 1, retain=false) |
| **T3** | Hujan lebat 75 mm/h, air tinggi (145 cm) | Status SIAGA_3 (&ge;140 cm), Pompa ON, Sirine ON (Buzzer 2 kHz) | Status: `SIAGA_3`, Pompa: `ON`, Sirine: `ON`, Command AI: `siren: true` | **PASS** | `decision.status == "SIAGA_3"`, buzzer sirine terpicu |
| **T4** | Dashboard mengirim Pompa OFF dalam mode MANUAL saat air tinggi (130 cm) | Pompa mati manual, AI dilarang mengirim command override ke aktuator | Mode: `MANUAL`, Pompa: `OFF`, AI menahan command (command is None) | **PASS** | Topic `edge/edge2/commands` tidak dikirimi pesan oleh AI selama mode MANUAL |
| **T5** | Dashboard memilih mode AUTO kembali | AI server kembali mengambil alih kendali otomatis pompa | AI kembali menerbitkan command `Pompa ON` karena air masih 130 cm | **PASS** | Command AI terbit kembali dengan `source: "ai"`, `mode: "AUTO"` |
| **T6** | Sensor ultrasonik HC-SR04 error (jarak 0, &gt;400 cm, lonjakan &gt;50 cm) | `sensor_ok = false`, level terakhir dipertahankan, dashboard memunculkan peringatan | `sensor_ok = false`, level ditahan, reason: `model+rule;unreliable_sensor` | **PASS** | Predictor menandai `reliable = False`, firmware Edge 1 menahan nilai valid terakhir |
| **T7** | Edge 1 berhenti mengirim telemetri &gt;30 detik real time | Status LWT offline terpicu, AI menandai sistem OFFLINE dan reset buffer | Status sistem: `OFFLINE;edge1_timeout>30s`, buffer prediktor di-reset | **PASS** | `edge1_online == False`, payload `OFFLINE` terbit ke `ai/prediction` |

---

## 2. Metrik Performa Model AI Aktual (Task 05)

Data diambil dari hasil evaluasi kronologis nyata pada [`docs/AI_EVALUATION.md`](AI_EVALUATION.md) (Test Set Kronologis 17.233 baris data sintetis):

| Evaluasi Kondisi | MAE Baseline (Persistence) | MAE Model Delta (HistGradientBoosting) | Perbaikan Relatif |
|---|---|---|---|
| **Keseluruhan Test Set** | 2,480 cm | **2,026 cm** | **+18,3%** *(Target 20% hampir tercapai)* |
| **Kondisi Siaga (&ge; 105 cm)** | 2,461 cm | **1,807 cm** | **+26,6%** *(Sangat akurat di kondisi air tinggi)* |
| **Kondisi Hujan (> 5 mm/h)** | 3,227 cm | **2,248 cm** | **+30,3%** *(Responsif terhadap limpasan hujan)* |

*Catatan Kejujuran*: Model dilatih dan diuji pada data sintetis reproducible (seed 42). Label model adalah **EXPERIMENTAL**, bukan model prediksi banjir operasional lapangan Semarang.

---

## 3. Pengukuran Latensi & Performa Sistem

| Metrik | Target PRD | Hasil Pengukuran / Verifikasi | Status |
|---|---|---|:---:|
| **Telemetri Edge &rarr; Broker** | &lt; 3,0 detik | Rata-rata 0,08 – 0,25 detik (via HiveMQ TCP 1883) | **MEMENUHI TARGET** |
| **Command Dashboard &rarr; Edge 2** | &lt; 3,0 detik | Rata-rata 0,15 – 0,40 detik (via WebSocket TLS & QoS 1) | **MEMENUHI TARGET** |
| **Watchdog Timeout Edge 1** | 30 detik | 30,0 detik tepat (Watchdog timer AI Server) | **MEMENUHI TARGET** |
| **Waktu Build Next.js Dashboard** | Bebas error | 1,8 – 3,3 detik (Static Prerender Route `/` & `/_not-found`) | **MEMENUHI TARGET** |

---

## 4. Audit Integritas Data & Desain

1. **Batas AOI Geografis**:
   - Berkas: `data/geo/aoi_semarang_pilot.geojson`.
   - Hash SHA-256: `3A41112E91424EA9F1792E04C411FF255B43EC6D429FD8B638006769B491FEAF` (Sama persis byte-per-byte dengan sumber PRD; tidak diubah satu koordinat pun).
2. **Atribusi Sumber Data**:
   - Atribusi OpenStreetMap ODbL tampak pada sudut peta Leaflet.
   - Atribusi resmi BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) tercantum pada kartu cuaca.
   - Atribusi Pemkot Semarang dan BIG SRGI tercantum pada kartu sumber eksternal.
3. **Pemisahan Kategori Data**:
   - `IoT SIMULATED`: Telemetri virtual Wokwi ESP32.
   - `EXPERIMENTAL`: Prediksi model AI berbasis data sintetis.
   - `FORECAST`: Prakiraan cuaca regional BMKG (bukan hujan lokal terukur).
   - `UNAVAILABLE`: Sumber data resmi yang tidak memiliki API publik terbuka (PantauBanjir & BIG).
4. **Keamanan Kontrak**:
   - Tidak ada token rahasia yang di-commit ke Git (`.gitignore` memfilter `.env`).
   - Tidak ada retained message pada topic command aktuator (`retain=false`).

---

## 5. Batasan & Sisa Isu (Known Limitations)

1. **Kompilasi ESP32 Fisik**: Firmware Edge 1 dan Edge 2 diuji logika, kontrak JSON, dan sintaksnya di lingkungan PC menggunakan compiler g++ (dengan library ArduinoJson asli). Kompilasi biner hardware ESP32 membutuhkan IDE Arduino atau Wokwi online karena `arduino-cli` tidak terpasang di mesin host lokal.
2. **Keterbatasan API Pemkot & BIG**: Pemkot Semarang (PantauBanjir) dan BIG (Pasang Surut Pelabuhan) belum menyediakan REST API publik tanpa autentikasi, sehingga adapter secara transparan melaporkan status `UNAVAILABLE` demi mematuhi kebijakan no-scraping PRD.


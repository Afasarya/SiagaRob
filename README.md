# SiagaRob — IoT & AI Coastal Flood Monitoring Platform

Platform pemantauan dan peringatan dini banjir rob berbasis IoT dan Machine Learning untuk wilayah pesisir Semarang Utara dan Semarang Timur (Area of Interest seluas 98,4 km²).

Proyek ini mengintegrasikan mikrokontroler ESP32 virtual (Wokwi), protokol komunikasi MQTT real-time, estimasi kenaikan air berbasis model prediktif (HistGradientBoosting delta estimator), integrasi prakiraan cuaca BMKG, serta antarmuka web interaktif berbasis Next.js 16 dan Leaflet.

> **Catatan Akademik:** Proyek ini merupakan prototipe tugas besar IoT & AI. Data sensor dihasilkan dari simulasi virtual Wokwi ESP32 (`IoT SIMULATED`), model machine learning dilatih dengan dataset sintetis hidrologi (`EXPERIMENTAL`), dan prakiraan cuaca bersumber dari API Terbuka BMKG (`FORECAST`).

---

## Fitur Utama

- **Real-Time IoT Telemetry**: Akuisisi data ketinggian air pasang (HC-SR04 dengan filter median 5 sampel) dan curah hujan (potensiometer ADC + moving average) setiap 2–5 detik.
- **Predictive AI Engine (+30 Menit)**: Model *HistGradientBoostingRegressor* memprediksi delta perubahan level air 30 menit ke depan (MAE 2,026 cm vs baseline persistence 2,480 cm).
- **Automated Actuator & Hysteresis**: Kontrol otomatis pompa polder dan sirine bahaya berbasis status risiko (`SIAGA 1`, `SIAGA 2`, `SIAGA 3`) dengan ambang histeresis untuk mencegah osilasi relay.
- **Manual Override Safety**: Operator dapat mengambil alih kontrol pompa secara manual dari dashboard. Perintah otomatis dari AI diblokir selama mode `MANUAL` aktif.
- **Geospatial Mapping**: Peta interaktif Leaflet + OpenStreetMap menampilkan batas administrasi AOI 19 kelurahan pesisir serta marker stasiun sensor live.
- **Official Weather Integration**: Adapter backend FastAPI (Port 8000) mengagregasi data cuaca per 3 jam dari BMKG untuk Kelurahan Bandarharjo (`adm4: 33.74.02.1001`) dengan cache in-memory TTL 30 menit.

---

## Arsitektur Sistem

```text
[Edge 1: Pos Air Wokwi]          [Edge 2: Pos Hujan & Pompa Wokwi]
(ESP32 + HC-SR04 Ultrasonik)      (ESP32 + DHT22 + Potensio + Relay)
         │                                 │
         │ (telemetry & LWT)               │ (telemetry, status, commands)
         ▼                                 ▼
┌─────────────────────────────────────────────────────────────┐
│             HiveMQ Public MQTT Broker                       │
│    TCP: broker.hivemq.com:1883  |  WS TLS: :8884/mqtt       │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼ (QoS 0/1)                    ▼ (WebSocket TLS)
┌──────────────────────────────┐  ┌───────────────────────────┐
│       AI Server (Python)     │  │   Dashboard Next.js 16    │
│  - HistGradientBoosting ML   │  │   - Peta AOI Leaflet OSM  │
│  - Auto Actuator Controller  │  │   - Recharts Time-Series  │
│  - Status Risk & Hysteresis  │  │   - Kontrol Aktuator UI   │
└──────────────────────────────┘  └─────────────┬─────────────┘
                                                │ REST API (:8000)
                                                ▼
                                  ┌───────────────────────────┐
                                  │   FastAPI Adapter (:8000) │
                                  │   - BMKG Weather API Live │
                                  │   - Fallback PantauBanjir │
                                  │   - TTL 30 Menit Cache    │
                                  └───────────────────────────┘
```

---

## Konfigurasi Hardware Virtual (Wokwi ESP32)

### Edge 1: Pos Pantau Air (Muara Tanjung Mas)
| Komponen | Pin ESP32 | Keterangan |
| :--- | :--- | :--- |
| HC-SR04 TRIG | `GPIO 5` | Trigger pulsa ultrasonik (10 µs) |
| HC-SR04 ECHO | `GPIO 18` | Echo penerima pantulan gelombang |
| Status LED | `GPIO 2` | Indikator transmisi paket telemetri |
| Acuan Sensor | Tinggi 200 cm | `level_cm = 200.0 - distance_cm` |

### Edge 2: Pos Cuaca & Rumah Pompa (Polder Tambak Lorok)
| Komponen | Pin ESP32 | Keterangan |
| :--- | :--- | :--- |
| DHT22 DATA | `GPIO 15` | Pembacaan suhu udara (°C) & kelembapan (%) |
| Potensiometer | `GPIO 34` (ADC) | Simulator intensitas hujan (0–80 mm/jam) |
| Relay Pompa | `GPIO 26` | Kontrol pompa drainase polder (Aktif HIGH) |
| Buzzer Sirine | `GPIO 27` | Sirine bahaya frekuensi 2,2 kHz |

---

## Kontrak Topik MQTT

Semua pertukaran data menggunakan prefix `siagarob/{PROJECT_ID}/`:

| Arah / Komponen | Topik | QoS | Retain | Keterangan |
| :--- | :--- | :---: | :---: | :--- |
| Edge 1 $\rightarrow$ Broker | `edge/edge1/telemetry` | 0 | False | Level air (cm), laju (cm/m), sensor health |
| Edge 1 $\rightarrow$ Broker | `edge/edge1/status` | 1 | True | Status koneksi (`online` / `offline` via LWT) |
| Edge 2 $\rightarrow$ Broker | `edge/edge2/telemetry` | 0 | False | Hujan (mm/h), suhu, kelembaban, pompa, mode |
| Edge 2 $\rightarrow$ Broker | `edge/edge2/status` | 1 | True | Status koneksi (`online` / `offline` via LWT) |
| AI Server $\rightarrow$ Edge 2 | `edge/edge2/commands` | 1 | False | Perintah pompa ON/OFF & mode (`source="ai"`) |
| Dashboard $\rightarrow$ Edge 2 | `edge/edge2/commands` | 1 | False | Perintah manual operator (`source="dashboard"`) |
| AI Server $\rightarrow$ Dashboard | `ai/prediction` | 0 | True | Estimasi level +30m, status risiko bahaya |

---

## Panduan Instalasi & Menjalankan

### 1. Klon Repositori & Environment
```bash
git clone https://github.com/Afasarya/SiagaRob.git
cd SiagaRob

# Salin konfigurasi environment
copy .env.example .env
copy .env.example dashboard\.env.local
```
*Pastikan `PROJECT_ID` di file `.env` dan `dashboard/.env.local` sudah sesuai dengan pengenal tim Anda.*

### 2. Setup Lingkungan Python
```bash
python -m venv .venv
.\.venv\Scripts\activate

# Install dependensi
pip install -r tools/requirements.txt
pip install -r ai/requirements.txt
pip install -r backend/requirements.txt
```

### 3. Jalankan Adapter Backend (FastAPI - Port 8000)
```bash
# Terminal 1
uvicorn backend.app.main:app --port 8000 --reload
```
*Dokumentasi Swagger API dapat diakses di `http://localhost:8000/docs`.*

### 4. Jalankan AI Server Streaming
```bash
# Terminal 2
python ai/ai_server.py
```
*Server akan subscribe ke data telemetri edge, menjalankan inferensi model, dan mengirim komando otomatis ke pompa jika air melewati ambang batas.*

### 5. Jalankan Web Dashboard (Next.js - Port 3000)
```bash
# Terminal 3
cd dashboard
npm install
npm run dev
```
*Buka browser di `http://localhost:3000`.*

### 6. Jalankan Simulasi Wokwi
Buka simulator [Wokwi ESP32](https://wokwi.com) untuk kedua node:
- **Edge 1**: Gunakan file pada folder [`edge1_wokwi/`](edge1_wokwi/) (`diagram.json`, `sketch.ino`, `libraries.txt`).
- **Edge 2**: Gunakan file pada folder [`edge2_wokwi/`](edge2_wokwi/) (`diagram.json`, `sketch.ino`, `libraries.txt`).
- Pastikan konstanta `PROJECT_ID` pada masing-masing sketch disamakan dengan `.env`.

---

## Pengujian & Verifikasi Kualitas

Proyek ini dilengkapi test suite otomatis dari level logika unit test hingga end-to-end integration test:

```bash
# 1. Validasi struktur fondasi, GeoJSON AOI, dan kontrak
python scripts/validate_foundation.py

# 2. Unit test Pytest (Model AI, Aturan Histeresis, Adapter Backend)
pytest ai tools backend/tests -q

# 3. Pengujian skenario end-to-end T1–T7 di broker live
python scripts/test_e2e_scenarios.py

# 4. Validasi frontend dashboard (TypeScript & Lint)
cd dashboard
npm run lint
npm run typecheck
npm run build
```

Hasil verifikasi detail seluruh skenario pengujian dapat dibaca di [**`docs/TEST-REPORT.md`**](docs/TEST-REPORT.md).

---

## Pusat Dokumentasi

- [**Arsitektur Sistem**](docs/architecture.md): Pembahasan detail alur data, peran komponen, isolasi peran kontrol, dan fail-safe matrix.
- [**Kontrak MQTT**](docs/mqtt-contract.md): Spesifikasi skema JSON payload, QoS, flag retain, LWT, dan state machine aktuator.
- [**Sumber Data Eksternal**](docs/data-sources.md): Integrasi data cuaca BMKG dan kebijakan data tanpa scraping ilegal.
- [**Laporan Pengujian QA (T1–T7)**](docs/TEST-REPORT.md): Matriks hasil pengujian end-to-end dan latensi responsifitas sistem.
- [**Evaluasi Model AI**](docs/AI_EVALUATION.md): Analisis performa model machine learning terhadap baseline hidrologi.
- [**Panduan Demonstrasi**](docs/DEMO-SCRIPT.md): Naskah skenario presentasi live demo sistem berdurasi 5–7 menit.

---

## Lisensi & Kontributor

Dikembangkan sebagai pemenuhan Tugas Besar Mata Kuliah Internet of Things (IoT), Departemen Informatika, Universitas Diponegoro.

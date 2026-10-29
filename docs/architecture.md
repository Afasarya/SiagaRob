# Arsitektur Sistem SiagaRob

SiagaRob adalah prototipe sistem peringatan dini dan pemantauan risiko rob dan banjir untuk wilayah pesisir Semarang Utara dan Semarang Timur. Sistem memadukan teknologi Internet of Things (IoT), kecerdasan buatan (Machine Learning), sistem informasi geografis (GIS), dan antarmuka web interaktif.

---

## 1. Diagram Aliran Data & Komponen

```text
[ Wokwi Edge 1 (ESP32) ]               [ Wokwi Edge 2 (ESP32) ]
  - HC-SR04 Ultrasonik (Pin 5, 18)       - DHT22 Suhu & Lembab (Pin 15)
  - LED Indikator (Pin 2)                - Potensiometer Hujan (Pin 34)
  - Filter Median 5 & Rate               - Relay Pompa (Pin 26) & Buzzer (Pin 27)
         │                                      │
         │ (MQTT TCP 1883)                      │ (MQTT TCP 1883 - Dua Arah)
         ▼                                      ▼
    ══════════════════════════════════════════════════════════
               Public Broker: broker.hivemq.com:1883
    ══════════════════════════════════════════════════════════
           ▲                                       ▲
           │                                       │ (WebSocket TLS :8884)
           │ (MQTT TCP 1883)                       │
           ▼                                       ▼
[ Python AI Server (ai_server.py) ]   [ Next.js Dashboard (Port 3000) ]
  - Subscribe Telemetry Edge 1 & 2      - Next.js 16 App Router + React + TS
  - Model: HistGradientBoosting Delta   - Leaflet + OSM Basemap + AOI Pilot
  - Aturan Ambang: max(now, +30m)       - Recharts 60-Point Rolling Chart
  - Histeresis Pompa (5 sampel, 10cm)   - Panel Kontrol Aktuator (AUTO/MANUAL)
  - Publish ai/prediction (QoS 0)       - mqtt.js WebSocket Client-Only
  - Command Edge 2 (HANYA saat AUTO)               │
                                                   │ (HTTP REST JSON)
                                                   ▼
                                      [ FastAPI Adapter (Port 8000) ]
                                        - Integrasi API Terbuka BMKG
                                        - Normalisasi, Caching & CORS
                                        - Fallback PantauBanjir & BIG
```

---

## 2. Rincian Lapisan Arsitektur

### 2.1 Lapisan Edge IoT Virtual (Wokwi)
- **Edge 1 (Pos Air)**: Membaca jarak permukaan air menggunakan sensor ultrasonik HC-SR04 virtual. Nilai dikonversi menjadi tinggi pasang (`level_cm = 200 - distance_cm`) dengan *filter median 5 sampel* dan kalkulasi laju kenaikan air (`rate_cm_min`).
- **Edge 2 (Pos Hujan & Aktuator)**: Membaca kondisi cuaca (DHT22) dan simulasi curah hujan 0–80 mm/jam via potensiometer ADC. Memiliki aktuator relay pompa (GPIO 26) dan sirine bahaya (GPIO 27). Menerima perintah kendali MQTT dua arah dan melaporkan status aktualnya di setiap periode telemetri berikutnya.

### 2.2 Lapisan Komunikasi Cloud (Broker MQTT)
- Menggunakan broker publik `broker.hivemq.com` dengan prefix topik unik per tim `siagarob/PROJECT_ID/`.
- Protokol:
  - **TCP 1883**: Digunakan oleh mikrokontroler ESP32 Wokwi dan AI Server Python.
  - **WebSocket TLS 8884 (`wss://`)**: Digunakan oleh Dashboard Next.js di browser client.
- LWT (Last Will and Testament): Menerbitkan pesan `offline` (retained, QoS 1) jika sambungan perangkat terputus secara tidak terduga.

### 2.3 Lapisan Kecerdasan Buatan (AI Server)
- Menggunakan model regresi `HistGradientBoostingRegressor` yang dilatih pada perubahan level ($\Delta = \text{level}_{t+30} - \text{level}_t$) untuk memproyeksikan ketinggian air 30 menit ke depan.
- Menentukan status risiko wilayah:
  - **AMAN**: $< 105\text{ cm}$
  - **SIAGA 1**: $\ge 105\text{ cm}$
  - **SIAGA 2**: $\ge 120\text{ cm}$ (Aktivasi pompa otomatis jika mode AUTO)
  - **SIAGA 3**: $\ge 140\text{ cm}$ (Aktivasi pompa dan sirine bahaya jika mode AUTO)
- Menjalankan histeresis pompa: Pompa baru dimatikan jika air turun $>10\text{ cm}$ di bawah ambang ($< 110\text{ cm}$) selama minimal 5 sampel berturut-turut.
- **Proteksi Mode**: AI hanya boleh menerbitkan perintah ke aktuator bila mode Edge 2 adalah `AUTO`. Jika mode `MANUAL`, AI tidak mengirim perintah apa pun agar tidak menimpa instruksi operator dashboard.

### 2.4 Lapisan Adapter Data Eksternal (FastAPI)
- Berjalan terpisah pada `localhost:8000`.
- Bertindak sebagai *API gateway* dan penyedia *caching* (TTL 30 menit) untuk API terbuka BMKG (Prakiraan Cuaca Kelurahan Bandarharjo, Semarang Utara).
- Menyediakan *CORS header* bagi frontend dan melaporkan status kesegaran data (`LIVE`, `STALE`, `UNAVAILABLE`) secara jujur.

### 2.5 Lapisan Penyajian (Next.js Dashboard)
- Dibangun dengan Next.js App Router, React 19, TypeScript, Tailwind CSS, dan lucide-react.
- Peta interaktif Leaflet + OpenStreetMap dimuat secara *client-only* (`ssr: false`) dengan batas poligon AOI Semarang Pilot (98,4 km²) yang dibekukan.
- Grafik Recharts real-time menampilkan riwayat geser 60 sampel terakhir dengan 3 garis ambang bahaya.
- Panel Kontrol Aktuator dua arah dengan konfirmasi aksi dan siklus *feedback loop* telemetri.


# PRD Induk — SiagaRob

- Versi: 1.1
- Tanggal: 29 Oktober 2026
- Target coding agent: Google Antigravity
- Bahasa aplikasi dan dokumentasi: Bahasa Indonesia
- Status: Spesifikasi implementasi; belum berarti fitur sudah berjalan.
- Catatan versi 1.1: stack dashboard ditetapkan menjadi Next.js App Router + React + TypeScript; adapter sumber eksternal menggunakan FastAPI; AI tetap Python terpisah.

## 1. Tujuan produk

SiagaRob adalah prototipe dashboard pemantauan risiko rob dan banjir untuk area pilot pesisir Semarang Utara dan Semarang Timur. Sistem menggabungkan peta jalan nyata, batas AOI geografis, sumber informasi publik yang dapat diakses, sensor IoT virtual, pengolahan data, prediksi berbasis model, dan demonstrasi kontrol aktuator dua arah.

Tujuan utama:
1. Memvisualisasikan wilayah pilot pada peta nyata dan mempertahankan batas AOI yang diberikan.
2. Menampilkan sumber data eksternal dengan waktu pengambilan, status kesegaran, dan atribusi.
3. Memantau data telemetri dari dua edge device virtual.
4. Menghasilkan prediksi yang dijelaskan dan dapat dievaluasi, bukan angka yang dibuat-buat tanpa label.
5. Memperagakan komunikasi dua arah MQTT, kontrol AUTO/MANUAL, dan alarm pada demo.
6. Memenuhi tugas kuliah: minimal dua edge, minimal dua sensor, minimal dua jenis pemrosesan data, satu algoritma AI/algoritma lain, komunikasi cloud, pengujian, GitHub, dan video demo.

## 2. Konteks dan sumber persyaratan

### 2.1 Sumber utama yang diberikan pengguna

- `PRD SiagaRob – Peringatan Dini Rob & Banjir (IoT).pdf`: sumber utama requirement IoT, kontrak MQTT, pin, filter, ambang, model, dashboard, serta tes T1–T7.
- `Praktek Multicommunication 2 Arah dan Multisensorss LAST.pdf`: aturan tugas kuliah dan rubrik.
- Screenshot Agronomus Fields: referensi bahasa visual UI.
- `aoi_semarang_pilot.geojson`: AOI pilot yang dibekukan; jangan mengubah geometrinya.

### 2.2 Sumber data eksternal yang direncanakan

- OpenStreetMap untuk basemap/fitur geografis; tampilkan atribusi dan patuhi kebijakan tile.
- PantauBanjir Semarang: https://pantaubanjir.semarangkota.go.id/ — sumber publik pemantauan stasiun banjir. Periksa apakah ada endpoint/data yang secara eksplisit boleh diakses; jangan menganggap situs web memiliki API stabil.
- BMKG Data Terbuka: https://data.bmkg.go.id/prakiraan-cuaca/ — API prakiraan cuaca per kode wilayah administrasi tingkat IV. Cantumkan BMKG sebagai sumber. Prakiraan cuaca bukan pengukuran hujan lokal saat ini.
- Peringatan dini cuaca BMKG: https://data.bmkg.go.id/peringatan-dini-cuaca/ — periksa format XML/CAP dan wilayah relevan.
- BIG/SRGI stasiun pasang surut Semarang: https://srgi.big.go.id/tides/smrg — halaman stasiun tersedia, tetapi data aktual atau prediksi yang dapat diakses programatik harus diverifikasi; jangan mengasumsikan endpoint/API.
- AOI GeoJSON dari pengguna.

Sumber eksternal harus diverifikasi di implementasi. Jika endpoint tidak terdokumentasi, diblokir CORS, atau tidak tersedia, buat adapter yang jelas statusnya dan gunakan fallback berlabel `UNAVAILABLE`/`DEMO`, bukan scraping agresif atau data palsu yang ditampilkan sebagai real-time.

## 3. Definisi data dan tingkat kepercayaan

Setiap observasi/seri harus membawa metadata setidaknya:
- `source`: nama sumber yang jelas.
- `source_type`: `official`, `iot_simulated`, `derived`, `model_prediction`, atau `demo`.
- `observed_at` / `issued_at`: waktu data dari sumber jika tersedia.
- `fetched_at`: waktu aplikasi mengambil data.
- `stale_after_seconds` atau kebijakan kesegaran yang terdokumentasi.
- `status`: `LIVE`, `STALE`, `UNAVAILABLE`, `SIMULATED`, atau `DEMO`.
- unit dan lokasi/stasiun/wilayah.

Jangan menggabungkan data dari satu stasiun ke lokasi lain tanpa penjelasan. Jangan menampilkan prakiraan cuaca sebagai hujan terukur. Jangan membuat pengukuran tinggi air real-time jika tidak ada sensor/stasiun yang benar-benar memasoknya.

### 3.1 Empat kategori yang wajib terlihat di UI

1. **Data resmi eksternal** — misalnya prakiraan cuaca BMKG atau observasi stasiun dari sumber resmi jika berhasil diakses.
2. **Telemetri IoT simulasi** — ESP32 di Wokwi; tidak boleh disebut sensor fisik.
3. **Prediksi/model** — keluaran model dengan horizon, input, timestamp, dan status evaluasi.
4. **Skenario demo** — data yang dipicu untuk demonstrasi; badge `DEMO`, tidak bercampur diam-diam dengan data resmi.

## 4. Pengguna dan kebutuhan

- Petugas/operator: melihat kondisi, data sumber, status pos, tren, dan peringatan.
- Penguji/dosen: memverifikasi dua edge, sensor, processing, AI, MQTT dua arah, hasil tes dan demo.
- Pengembang: menjalankan project lokal dengan langkah yang sederhana dan berulang.

## 5. Ruang lingkup MVP

### Termasuk
- Dashboard web bergaya Agronomus: sidebar, kartu ringkasan, warna netral, aksen kuning keemasan, kartu putih, garis tipis, sudut membulat.
- Peta nyata berbasis Leaflet + OpenStreetMap, AOI GeoJSON dibekukan, layer stasiun/pos dengan legenda sumber.
- Adapter data eksternal dan tampilan sumber/kesegaran.
- Dua project Wokwi ESP32.
- MQTT HiveMQ publik sesuai kontrak di bawah.
- Python AI training dan server.
- Grafik tinggi air aktual/simulasi, prediksi +30 menit, ambang status, panel konektivitas dan aktuator.
- Mode demo yang eksplisit dan dapat diulang.
- Pengujian otomatis untuk fungsi inti dan checklist T1–T7.
- README dan dokumentasi hasil.

### Tidak termasuk MVP
- Klaim layanan keselamatan publik yang tervalidasi.
- Sensor fisik terpasang di lapangan.
- Kontrol pompa fisik sungguhan.
- Jaminan prediksi genangan tingkat rumah/jalan tanpa model hidrologi, elevasi, drainase, kalibrasi, dan data valid.
- Login/role management, aplikasi mobile native, hosting publik wajib, atau pembayaran layanan.
- Mengarang endpoint/API atau mengambil data dengan scraping yang melanggar kebijakan sumber.

## 6. AOI pilot yang dibekukan

File `aoi_semarang_pilot.geojson` berisi satu FeatureCollection Polygon dengan properti:
- `nama`: AOI Pilot Pasang Surut
- `wilayah`: Semarang Utara dan Semarang Timur
- `kelurahan_target`: Tanjungmas, Bandarharjo, Kemijen, Kaligawe, Terboyo Kulon, Terboyo Wetan
- perkiraan luas AOI: 98,4 km²
- geometri dibekukan pada 2026-08-24.

Simpan salinan tanpa perubahan di `data/geo/aoi_semarang_pilot.geojson`. Validasi CRS WGS84 longitude/latitude dan bentuk geometri sebelum render. Jangan mengubah geometri, memperkecil AOI, atau membuat polygon pengganti tanpa persetujuan eksplisit. AOI ini lebih luas daripada gabungan area sasaran agar routing punya ruang untuk jalan alternatif.

## 7. Arsitektur yang disepakati

```text
Wokwi Edge 1 (ESP32 + HC-SR04)
  └─ MQTT TCP 1883 ─┐
                     ├─ HiveMQ public broker ─ Python AI server
Wokwi Edge 2         │                         ├─ prediction/commands
(ESP32 + DHT22,      │                         └─ telemetry/status
 potentiometer,      └─ MQTT over WebSocket TLS ─ Dashboard
 relay/LED, buzzer)

Next.js Dashboard (localhost)
  ├─ React + TypeScript + Tailwind CSS + shadcn/ui
  ├─ Leaflet / React Leaflet + OpenStreetMap + AOI GeoJSON
  ├─ Recharts untuk grafik
  └─ mqtt.js via WebSocket TLS ─ HiveMQ

FastAPI Data Adapter (localhost, port terpisah)
  └─ Sumber eksternal resmi, normalisasi, cache, freshness

Python AI training ─ model.joblib
Python AI server ─ MQTT telemetry, prediction, AUTO commands
```

Gunakan FastAPI sebagai adapter sumber data untuk CORS, parsing, cache, freshness, dan atribusi. Hindari membuat browser bergantung langsung pada API eksternal yang tidak menjamin CORS. Next.js adalah frontend dashboard wajib; AI server tetap proses Python terpisah.

## 8. Stack MVP

- Firmware: Arduino C++ di Wokwi, ESP32, PubSubClient, ArduinoJson, DHT sensor library.
- MQTT: `broker.hivemq.com:1883`; dashboard `wss://broker.hivemq.com:8884/mqtt`.
- Dashboard wajib: Next.js (App Router) + React + TypeScript.
- UI: Tailwind CSS + shadcn/ui; gunakan komponen aksesibel dan konsisten.
- Peta: Leaflet + React Leaflet. Komponen peta harus client-only/dynamic import dengan `ssr: false` agar tidak terjadi error `window is not defined` saat SSR.
- Grafik: Recharts.
- MQTT browser: mqtt.js melalui `wss://broker.hivemq.com:8884/mqtt`; jangan expose credential.
- AI: Python 3.10+, paho-mqtt, numpy, pandas, scikit-learn, joblib.
- Backend data adapter: FastAPI (Python) untuk menghindari CORS, menormalisasi sumber eksternal, cache, dan freshness. Gunakan satu backend adapter saja; jangan menambah Flask.
- Testing: pytest untuk Python; lint/typecheck/build untuk Next.js; validasi JSON/kontrak; manual test Wokwi.
- Local dev: Next.js di port 3000, FastAPI di port 8000, AI server sebagai proses terpisah. Catat perintah start dan environment di README.
- Gunakan npm sebagai package manager default kecuali repository yang sudah ada secara jelas memakai pnpm/yarn. Commit lockfile yang sesuai.
- Jangan membuat dashboard statis dengan `python -m http.server`; frontend harus merupakan aplikasi Next.js yang dapat di-build.

Semua dependency dan versi yang dipakai harus dicatat di `requirements.txt`/README. CDN atau API yang gagal tidak boleh membuat keseluruhan dashboard blank.

## 9. Kontrak MQTT — wajib konsisten

`PROJECT_ID` unik, huruf/angka/underscore, ditetapkan di `.env`/konfigurasi lokal dan README. Jangan gunakan token rahasia pada broker publik.

Prefix: `siagarob/PROJECT_ID/`

| Topic suffix | Arah | QoS | Retain |
|---|---|---:|---|
| `edge/edge1/telemetry` | Edge 1 → cloud | 0 | false |
| `edge/edge2/telemetry` | Edge 2 → cloud | 0 | false |
| `edge/edge1/status` | status/LWT | 1 | true |
| `edge/edge2/status` | status/LWT | 1 | true |
| `ai/prediction` | AI → dashboard | 0 | true |
| `edge/edge2/commands` | AI/dashboard → Edge 2 | 1 | false |

LWT payload `offline`, publish `online` saat connect. Reconnect dengan jeda 3 detik. Client ID wajib unik, misalnya `siagarob-edge1-PROJECT_ID`.

### 9.1 Payload Edge 1

```json
{
  "device_id": "edge1",
  "seq": 42,
  "level_cm": 82.4,
  "rate_cm_min": 1.8,
  "sensor_ok": true,
  "uptime_ms": 84000
}
```

### 9.2 Payload Edge 2

```json
{
  "device_id": "edge2",
  "seq": 40,
  "rain_mm_h": 24.0,
  "temp_c": 27.5,
  "hum_pct": 91,
  "pump": "ON",
  "siren": false,
  "mode": "AUTO",
  "uptime_ms": 80000
}
```

### 9.3 Payload prediksi

```json
{
  "level_now": 82.4,
  "level_30m": 118.2,
  "status": "SIAGA_2",
  "reason": "model+rule",
  "seq": 42
}
```

### 9.4 Payload command

```json
{
  "pump": "ON",
  "siren": false,
  "mode": "AUTO",
  "source": "ai"
}
```

Dashboard memakai `source: "dashboard"` dan mode `MANUAL` untuk kontrol manual. Command tidak retained demi mencegah aktuator hidup sendiri saat reboot.

## 10. Spesifikasi Edge

### Edge 1 — Pos Air
- HC-SR04 TRIG GPIO 5, ECHO GPIO 18; LED GPIO 2.
- `TINGGI_PASANG_CM = 200`; `level_cm = 200 - distance_cm`.
- Median filter 5 pembacaan.
- `rate_cm_min = (level sekarang - level 5 sampel sebelumnya) / 5` sesuai waktu simulasi yang didefinisikan.
- Error jika jarak 0, di luar 2–400 cm, atau lompatan >50 cm dalam satu sampel. Set `sensor_ok=false`, pertahankan nilai valid terakhir.
- Publish setiap 2 detik; 1 pesan mewakili 1 menit waktu simulasi. Dokumentasikan konsekuensi time compression.

### Edge 2 — Pos Hujan dan Aktuator
- DHT22 DATA GPIO 15.
- Potensiometer SIG GPIO 34; ADC 0–4095 dipetakan ke 0–80 mm/jam.
- Relay/LED pompa GPIO 26; buzzer GPIO 27.
- Moving average 3 pembacaan untuk hujan.
- Subscribe command; laporkan keadaan pompa/sirine/mode pada telemetri berikutnya.
- `AUTO`: mengikuti keputusan AI. `MANUAL`: AI tidak boleh menimpa command operator.

### Koneksi
- Wi-Fi Wokwi: `WiFi.begin("Wokwi-GUEST", "", 6)`.
- MQTT port 1883, buffer JSON minimum 512.
- Reconnect otomatis setiap 3 detik saat terputus.

## 11. AI dan processing

- Hapus `tide_sin` dan `tide_cos` dari fitur MVP.
- Data training sintetis: level dasar 80 cm, amplitudo pasang 15 cm dengan variasi spring-neap 5 cm, koefisien limpasan 0.25 (sesuai dokumen sumber), noise sigma 1 cm. Jelaskan data sintetis, jangan klaim sebagai observasi lapangan.
- Fitur: `level`, `rate_5`, `rain_10`, `rain_60`; urutan dan perhitungan harus identik saat training dan inference.
- Model: `HistGradientBoostingRegressor`.
- Split kronologis: 80% awal training, 20% akhir testing; jangan random split.
- Laporkan MAE model dan MAE baseline (baseline = level saat ini). Target perbaikan 20% adalah target, bukan hasil yang boleh dikarang.
- Prediksi +30 menit. Karena telemetri dipercepat, pemetaan waktu simulasi ke horizon 30 menit harus eksplisit dan sama di training/inference.
- Status berdasarkan `max(level_now, level_30m)`:
  - AMAN: <105 cm
  - SIAGA_1: ≥105 cm
  - SIAGA_2: ≥120 cm
  - SIAGA_3: ≥140 cm
- Histeresis: pompa OFF hanya jika level turun lebih dari 10 cm di bawah ambang selama 5 sampel berturut-turut.
- Jika Edge 1 tidak mengirim telemetri 30 detik waktu nyata, status OFFLINE.
- Server hanya mengirim command AI jika mode Edge 2 adalah AUTO.

### Penting untuk data real
Model dari data sintetis tidak boleh diberi label “prediksi banjir akurat Semarang”. Pisahkan:
1. prediksi eksperimen dari data IoT simulasi;
2. informasi/prakiraan eksternal dari sumber resmi;
3. status risiko gabungan jika ada, lengkap dengan formula dan disclaimer.
Jangan memasukkan data cuaca eksternal ke model tanpa mendesain ulang fitur, menguji kualitas data, dan melatih ulang model. Jika model belum dievaluasi, label prediksi sebagai `EXPERIMENTAL`.

## 12. Peta dan fitur geografis

- Leaflet untuk peta interaktif, OpenStreetMap sebagai basemap, tampilkan atribusi OSM secara terlihat.
- Muat AOI GeoJSON asli; fit bounds pada saat pertama buka.
- Peta mendukung zoom, pan, layer control, legenda, marker sumber data dengan popup yang memuat nama, tipe data, waktu pembaruan, nilai/unit, dan sumber.
- Jangan mengarang koordinat stasiun. Koordinat hanya dari GeoJSON atau sumber terverifikasi.
- Jangan mengarsir genangan berdasarkan model jika tidak ada data spasial/model yang sah. Jika visualisasi risiko demo dibuat, tampilkan sebagai layer `DEMO / ILUSTRASI`, bukan banjir aktual.
- Hormati tile usage policy; jangan prefetch/download tile massal. Jika basemap tidak tersedia, tampilkan pesan fallback dan tetap biarkan panel non-peta bekerja.
- AOI bukan bukti bahwa semua wilayah di dalamnya berisiko banjir.

## 13. UI/UX

Mengadaptasi screenshot Agronomus:
- sidebar kiri, workspace utama, top bar, metric cards.
- latar netral, kartu putih, garis tipis, radius halus, aksen kuning keemasan.
- dashboard responsif dan readable.
- navigasi MVP: Overview, Peta & Risiko, Telemetri, Prediksi, Aktuator, Sumber Data, Pengujian/Info.
- kartu: status sistem, stasiun/edge online, tinggi air IoT terakhir, prediksi +30 menit, hujan/forecast dengan label sumber.
- peta nyata sebagai area visual utama atau panel besar.
- grafik aktual vs prediksi dan garis ambang.
- setiap data stale/offline harus memiliki label, bukan menyisakan angka lama seolah live.
- badge visual membedakan `RESMI`, `SIMULASI`, `PREDIKSI`, `DEMO`, `STALE`.

## 14. Keamanan dan reliabilitas

- Broker MQTT publik tidak privat dan tidak aman untuk kontrol lapangan. Gunakan hanya data demo tanpa rahasia.
- Unique `PROJECT_ID` wajib.
- Jangan simpan token/API key di Git; gunakan `.env`, `.env.example` dengan nilai kosong, `.gitignore`.
- Validasi tipe/rentang payload dan handle JSON invalid.
- Terapkan timeout, retry terbatas, cache, dan fallback pada API eksternal.
- Jangan menjalankan aktuator fisik dari aplikasi ini.
- Aplikasi harus tetap menampilkan shell/dashboard saat salah satu sumber gagal.
- Jangan scrape website resmi secara agresif. Gunakan API publik terdokumentasi atau adapter yang dinonaktifkan dengan alasan yang jelas.

## 15. Penerimaan MVP

1. AOI GeoJSON tampil benar pada basemap nyata dan tidak diubah.
2. Sumber resmi yang berhasil diintegrasikan menampilkan sumber, waktu data, dan status kesegaran.
3. Data resmi yang gagal diakses diberi status `UNAVAILABLE`; tidak diganti angka palsu.
4. Dua edge dapat publish telemetri dan status ke topic yang benar.
5. Dashboard menerima telemetri melalui MQTT WebSocket.
6. AI training menghasilkan model dan laporan MAE model vs baseline dari test set kronologis.
7. Server AI memprediksi +30 menit, menentukan status, dan hanya mengirim command ketika mode AUTO.
8. Mode MANUAL mencegah AI menimpa perintah dashboard.
9. Sensor invalid dan edge offline terlihat jelas.
10. Semua skenario T1–T7 didokumentasikan dengan bukti hasil aktual.
11. README memungkinkan pengguna menjalankan sistem dari repo bersih.
12. Tidak ada klaim bahwa prototipe adalah sistem operasional keselamatan publik yang tervalidasi.

## 16. Tes sumber dari PRD tugas

- T1: hujan 0, air rendah → AMAN, pompa OFF.
- T2: hujan naik bertahap, air naik → prediksi melewati ambang SIAGA_2, pompa ON otomatis.
- T3: hujan lebat, air tinggi → SIAGA_3, pompa ON, sirine ON.
- T4: Pompa OFF dari dashboard dalam MANUAL → pompa mati walau siaga, AI tidak menimpa.
- T5: pilih AUTO → AI kembali mengendalikan pompa.
- T6: jarak HC-SR04 tidak masuk akal → `sensor_ok=false`, peringatan dashboard.
- T7: hentikan Edge 1 → LWT offline dan sistem OFFLINE setelah timeout.

Target performa dari dokumen sumber: telemetri sampai dashboard <3 detik; command sampai relay <3 detik; laporkan MAE sebenarnya. Jangan menyatakan target tercapai tanpa mengukur.

## 17. Referensi

- OpenStreetMap: https://www.openstreetmap.org/
- Tile policy OSM: https://operations.osmfoundation.org/policies/tiles/
- BMKG prakiraan cuaca: https://data.bmkg.go.id/prakiraan-cuaca/
- BMKG peringatan dini: https://data.bmkg.go.id/peringatan-dini-cuaca/
- PantauBanjir Semarang: https://pantaubanjir.semarangkota.go.id/
- BIG/SRGI pasang surut Semarang: https://srgi.big.go.id/tides/smrg
- HiveMQ public broker: https://www.hivemq.com/public-mqtt-broker/
- Leaflet: https://leafletjs.com/
- Wokwi: https://wokwi.com/

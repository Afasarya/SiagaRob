# Panduan Skenario Demonstrasi Video & Presentasi SiagaRob (3–5 Menit)

Panduan terstruktur ini dirancang untuk pembuatan video demonstrasi tugas kuliah IoT atau sesi presentasi langsung di hadapan dosen/penguji.

---

## 1. Persiapan Sebelum Perekaman (Pre-Flight Checklist)

1. Pastikan virtual environment Python aktif: `.\.venv\Scripts\activate`
2. Jalankan Backend Adapter FastAPI:
   ```powershell
   uvicorn app.main:app --app-dir backend --port 8000
   ```
3. Jalankan AI Server:
   ```powershell
   python ai/ai_server.py
   ```
4. Jalankan Dashboard Next.js:
   ```powershell
   cd dashboard && npm run dev
   ```
   Buka peramban pada `http://localhost:3000`.
5. Siapkan tab peramban untuk dua project Wokwi (Edge 1 dan Edge 2) atau gunakan alat CLI `tools/mqtt_tool.py` jika menjalankan demo mandiri.

---

## 2. Runtutan Waktu Demonstrasi (Timeline 3–5 Menit)

### Menit 0:00 – 0:45 | Pengantar, Desain Visual & Peta Nyata
- **Narasi**: Buka halaman utama Dashboard SiagaRob. Jelaskan bahwa ini adalah prototipe sistem pemantauan pasang surut rob untuk wilayah pilot Semarang Utara dan Semarang Timur.
- **Tindakan**:
  - Tunjukkan tata letak dashboard gaya Agronomus: Sidebar navigasi kiri, topbar dengan jam & status `MQTT Live`, kartu ringkasan metrik putih dengan garis tipis dan aksen kuning keemasan.
  - Tunjukkan **Peta Leaflet + OpenStreetMap**: Jelaskan batas poligon amber yang merupakan AOI Pilot Semarang seluas 98,4 km² (mencakup 6 kelurahan: Tanjungmas, Bandarharjo, Kemijen, Kaligawe, Terboyo Kulon, Terboyo Wetan).
  - Jelaskan bahwa poligon AOI sengaja dibuat lebih luas untuk menyediakan ruang rute darat memutar.
  - Tunjukkan atribusi resmi OpenStreetMap pada peta.

### Menit 0:45 – 1:30 | Sumber Data Resmi Publik (FastAPI Adapter)
- **Narasi**: Pindah ke tab **Sumber Data Resmi**.
- **Tindakan**:
  - Tunjukkan kartu data **BMKG Data Terbuka**: Perlihatkan bahwa cuaca Kelurahan Bandarharjo berstatus `LIVE` dengan suhu, kelembaban, dan prakiraan presipitasi.
  - Tekankan kepatuhan etika data: Data BMKG dilabeli tegas sebagai **`FORECAST`** (prakiraan), bukan pengukuran hujan lokal real-time.
  - Tunjukkan kartu **PantauBanjir Semarang** dan **BIG Pasang Surut** yang berstatus transparan **`UNAVAILABLE`** dengan tautan ke portal resmi karena tidak tersedianya API publik tanpa token/scraping ilegal.
  - Klik tombol **Segarkan** untuk menunjukkan responsivitas backend FastAPI.

### Menit 1:30 – 2:45 | Telemetri Dua Edge Wokwi & Respon Otomatis (T1, T2, T3)
- **Narasi**: Tunjukkan tab **Overview** dan **Telemetri IoT**. Mulai jalankan simulasi mikrokontroler ESP32 virtual di Wokwi.
- **Tindakan**:
  - **Skenario T1 (Aman)**: Saat jarak sensor HC-SR04 adalah 120 cm (ketinggian air 80 cm) dan potensiometer hujan 0: Dashboard menampilkan status `AMAN`, Pompa `OFF`, Sirine `OFF`.
  - **Skenario T2 (Siaga 2 & Pompa ON Otomatis)**: Naikkan slider potensiometer hujan di Edge 2 dan kurangi jarak ultrasonik di Edge 1 (air naik melewati 120 cm).
    - Tunjukkan grafik Recharts: Kurva biru aktual dan kurva ungu prediksi +30m melintasi garis oranye SIAGA 2 (120 cm).
    - Tunjukkan respon otomatis: AI Server menerbitkan command `Pompa ON` (Relay GPIO 26 aktif / LED merah menyala).
  - **Skenario T3 (Siaga 3 & Sirine Aktif)**: Naikkan air hingga melewati 140 cm.
    - Dashboard beralih ke status merah `SIAGA_3`.
    - Pompa tetap `ON` dan Sirine bahaya (Buzzer GPIO 27) aktif berbunyi.

### Menit 2:45 – 3:45 | Pengujian Kontrol Manual Override (T4 & T5)
- **Narasi**: Pindah ke tab **Kontrol Aktuator**. Tunjukkan keandalan sistem dua arah dan perlindungan kontrol operator.
- **Tindakan**:
  - **Skenario T4 (Manual Override)**: Klik tombol **Matikan Pompa (OFF)**.
    - Modal dialog konfirmasi muncul. Klik *Ya, Jalankan*.
    - Status beralih ke `MANUAL`. Pompa di Edge 2 seketika mati (LED merah padam).
    - Tunjukkan bahwa meskipun air masih tinggi (SIAGA 2/3), **AI Server TIDAK MENIMPA** keputusan operator!
    - Tunjukkan teks feedback konfirmasi: `Terkonfirmasi oleh Edge 2: Mode MANUAL, Pompa OFF`.
  - **Skenario T5 (Kembali ke AUTO)**: Klik tombol **Kembalikan ke AUTO**.
    - Perintah terkirim dan terkonfirmasi.
    - Seketika AI Server kembali mengambil alih dan menyalakan pompa karena ketinggian air masih dalam kondisi bahaya.

### Menit 3:45 – 4:30 | Deteksi Sensor Error & Timeout Offline (T6 & T7)
- **Narasi**: Tunjukkan ketahanan sistem terhadap anomali perangkat keras dan pemutusan jaringan.
- **Tindakan**:
  - **Skenario T6 (Sensor Error)**: Pada Wokwi Edge 1, ubah jarak menjadi 0 atau >400 cm (atau lonjakan ekstrem).
    - Firmware Edge 1 langsung menandai `sensor_ok: false` dan menahan nilai valid terakhir.
    - Dashboard langsung menampilkan kartu peringatan merah: `SENSOR ERROR (HOLD VALUE)`.
  - **Skenario T7 (Edge 1 Offline / Timeout)**: Hentikan simulasi Edge 1 di Wokwi.
    - Setelah batas keepalive / 30 detik tanpa telemetri:
    - Status Edge 1 di dashboard dan AI Server otomatis berubah menjadi `OFFLINE`.
    - Prediktor AI melakukan reset buffer demi keamanan data.

### Menit 4:30 – 5:00 | Kesimpulan, Akurasi AI & Penutup
- **Narasi**: Buka tab **Pengujian & Info PRD**.
- **Poin Penutup**:
  - Tunjukkan bahwa seluruh kriteria tugas kuliah terpenuhi: Minimal 2 edge virtual, sensor ultrasonik, suhu, kelembaban, potensiometer, relay, buzzer, MQTT cloud dua arah, adapter FastAPI, dan model AI machine learning.
  - Tunjukkan metrik MAE aktual model: MAE 2,026 cm dengan perbaikan +18,3% dari baseline, dan MAE 1,807 cm pada kondisi siaga air tinggi.
  - Berikan penegasan akhir: SiagaRob adalah prototipe akademik yang menjunjung tinggi etika kejujuran data, pemisahan data simulasi vs resmi, dan arsitektur modular yang siap dikembangkan lebih lanjut.

---

## 3. Skenario Fallback (Jika Internet atau Broker Publik Gangguan)

Jika broker HiveMQ publik atau internet kampus lambat saat presentasi:
1. **Fallback Data Eksternal**: Jika internet putus, FastAPI adapter otomatis beralih ke cache data terakhir berstatus `STALE`, atau menyajikan tampilan `UNAVAILABLE` tanpa membuat aplikasi crash/blank.
2. **Fallback MQTT**: Jika koneksi WebSocket terganggu, gunakan script CLI offline di terminal:
   ```powershell
   python scripts/test_e2e_scenarios.py
   ```
   Skrip ini membuktikan seluruh 7 skenario (T1–T7) secara deterministik dan mencetak log eksekusi `SEMUA PASS` dalam hitungan detik.


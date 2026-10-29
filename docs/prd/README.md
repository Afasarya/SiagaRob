# SiagaRob — Paket PRD & Prompt Vibe Coding

Paket ini adalah spesifikasi implementasi SiagaRob untuk **Google Antigravity**. Dashboard menggunakan **Next.js App Router + React + TypeScript**, UI Tailwind CSS + shadcn/ui, peta Leaflet/React Leaflet, grafik Recharts, dan MQTT browser melalui mqtt.js. AI tetap memakai Python dan FastAPI dipakai sebagai adapter sumber data eksternal.

## Mulai cepat

1. Ekstrak ZIP ke folder kerja dan buka folder di Google Antigravity.
2. Baca `00-PRD-CONTEXT.md` sebagai sumber kebenaran, lalu `01-EXECUTION-GUIDE.md`.
3. Salin `aoi_semarang_pilot.geojson` ke repository dengan nama/path `data/geo/aoi_semarang_pilot.geojson` tanpa mengubah geometri.
4. Jalankan Prompt Task 01 terlebih dahulu. Task tersebut harus membuat scaffold Next.js yang dapat di-build.
5. Selesaikan dan verifikasi setiap task sebelum lanjut ke task berikutnya.

## Stack yang ditetapkan

- **Frontend:** Next.js App Router, React, TypeScript, npm.
- **UI:** Tailwind CSS + shadcn/ui atau komponen Tailwind yang konsisten.
- **Peta:** Leaflet + React Leaflet + OpenStreetMap; peta harus client-only/dynamic import dengan `ssr: false`.
- **Grafik:** Recharts.
- **MQTT browser:** mqtt.js melalui WebSocket TLS HiveMQ.
- **Data eksternal:** FastAPI adapter terpisah.
- **AI:** Python, scikit-learn, paho-mqtt.
- **IoT:** ESP32 virtual di Wokwi.

## Perintah dev yang diharapkan

```bash
cd dashboard
npm install
npm run dev
```

Build frontend: `cd dashboard && npm run build`. Perintah lint/typecheck harus disediakan dan dicatat oleh Task 01. FastAPI dan AI server dijalankan sebagai proses terpisah sesuai README final.

## Isi paket

- `00-PRD-CONTEXT.md` — kontrak dan sumber kebenaran project.
- `01-EXECUTION-GUIDE.md` — cara eksekusi bertahap dengan Antigravity.
- `tasks/` — 12 prompt implementasi dari foundation hingga demo.
- `aoi_semarang_pilot.geojson` — aset geografis sumber, disertakan tanpa perubahan.

## Prinsip penting

**Peta nyata bukan berarti prediksi banjir tervalidasi.** Bedakan data resmi, telemetry Wokwi, prediksi model sintetis, dan skenario demo. Jangan mengklaim sistem sebagai layanan peringatan publik yang tervalidasi.

## Jika task gagal

1. Jangan lanjut ke task berikutnya.
2. Minta agent mereproduksi dan memperbaiki kegagalan terkecil, lalu menjalankan ulang tes.
3. Periksa bukti tes, file yang berubah, dan handoff di `docs/PROGRESS.md`.
4. Jangan mengklaim API, MQTT live, atau prediksi berhasil jika belum diuji.

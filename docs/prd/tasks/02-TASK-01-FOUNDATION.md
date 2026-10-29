# TASK 01 — Foundation dan kontrak bersama

## Tujuan
Buat fondasi repository agar semua komponen memakai konfigurasi dan kontrak yang sama.

## Prasyarat
Repository boleh kosong. PRD induk dan AOI tersedia.

## Scope
- Susun struktur repo: `edge1_wokwi/`, `edge2_wokwi/`, `ai/`, `dashboard/` sebagai aplikasi Next.js App Router, `backend/` sebagai adapter FastAPI, `data/geo/`, `docs/`, `.env.example`, `.gitignore`, `README.md`.
- Inisialisasi Next.js dengan TypeScript, Tailwind CSS, ESLint, App Router, dan npm; buat `package.json` serta lockfile.
- Tetapkan struktur frontend minimal: `dashboard/src/app/`, `dashboard/src/components/`, `dashboard/src/lib/`, `dashboard/public/geo/` bila diperlukan.
- Tetapkan stack UI: shadcn/ui (setup resmi atau komponen Tailwind yang konsisten), React Leaflet/Leaflet, Recharts, mqtt.js. Jangan instal dependency yang tidak digunakan.
- Pastikan Leaflet hanya dirender di client melalui dynamic import dengan `ssr: false`.
- Gunakan FastAPI untuk adapter data eksternal; jangan buat backend Flask tambahan.
- Simpan salinan AOI di `data/geo/aoi_semarang_pilot.geojson`; validasi tanpa mengubah koordinat.
- Tetapkan `PROJECT_ID` konfigurasi dan satu sumber definisi topic/payload yang didokumentasikan.
- Buat contoh payload JSON untuk telemetry edge1/edge2, prediction, command, status.
- Buat `docs/PROGRESS.md` dengan format handoff.
- Jangan implementasikan firmware/AI/UI lengkap pada task ini.

## Acceptance criteria
- Struktur folder sesuai; tidak ada secret.
- GeoJSON valid, satu FeatureCollection/Polygon seperti sumber, geometri sama persis.
- `PROJECT_ID` memiliki placeholder aman dan instruksi mengganti.
- Kontrak topic dan payload sama persis dengan PRD induk.
- README berisi prerequisite, perintah setup/build Next.js, perintah menjalankan FastAPI/AI, dan roadmap singkat.
- `npm run build` dan lint/typecheck yang tersedia lulus, atau kegagalan dilaporkan dengan jelas.

## Prompt siap pakai untuk Antigravity

```text
TASK 01 — FOUNDATION SIAGAROB

Baca seluruh 00-PRD-CONTEXT.md dan task ini. Periksa repository sebelum mengubah file. Implementasikan hanya fondasi:
1. Buat struktur folder yang ditentukan PRD.
2. Inisialisasi `dashboard/` sebagai aplikasi Next.js App Router + React + TypeScript + Tailwind CSS menggunakan npm. Buat `package.json`, lockfile, `src/app/layout.tsx`, `src/app/page.tsx`, dan konfigurasi standar yang dibutuhkan. Pastikan perintah dev/build/lint tersedia.
3. Pasang dan konfigurasi dependency yang diperlukan: Leaflet, React Leaflet, Recharts, mqtt.js, lucide-react, dan shadcn/ui atau komponen Tailwind yang konsisten. Jangan pasang dependency yang tidak diperlukan.
4. Gunakan FastAPI sebagai satu-satunya adapter backend sumber data di `backend/`; jangan menambahkan Flask.
5. Tempatkan AOI GeoJSON pengguna pada data/geo/aoi_semarang_pilot.geojson. Jika file sumber tidak ditemukan di repo, jangan membuat geometri pengganti; laporkan dan minta file disalin.
6. Validasi JSON, FeatureCollection, Polygon, dan properti AOI. Jangan ubah satu koordinat pun.
7. Dokumentasikan PROJECT_ID dan kontrak topic/payload dalam docs yang mudah dibaca.
8. Buat .env.example tanpa secret dan .gitignore yang mengabaikan .env, cache, model artefak yang tak perlu, dan virtualenv.
9. Buat README awal dengan perintah `cd dashboard && npm install && npm run dev`, `npm run build`, serta instruksi menjalankan FastAPI dan AI server sebagai proses terpisah.
10. Buat docs/PROGRESS.md.
Jangan membangun fitur dashboard lengkap pada task ini; cukup scaffold Next.js yang dapat di-build. Jangan mengarang koordinat stasiun, API, atau data observasi. Jalankan validasi GeoJSON/JSON dan laporkan perintah serta hasil aktual. Tunjukkan file yang dibuat/diubah dan handoff Task 01.
```

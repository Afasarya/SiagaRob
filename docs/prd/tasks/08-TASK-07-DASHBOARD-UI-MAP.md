# TASK 07 — Dashboard UI dan peta nyata

## Tujuan
Membangun shell dashboard berdasarkan screenshot Agronomus dan memuat peta nyata dengan AOI GeoJSON.

## Scope
- Aplikasi `dashboard/` berbasis Next.js App Router + React + TypeScript.
- UI dengan Tailwind CSS + shadcn/ui (atau komponen Tailwind konsisten yang sudah tersedia).
- Peta Leaflet + React Leaflet dimuat hanya di client; gunakan dynamic import dengan `ssr: false`.
- Grafik memakai Recharts; ikon memakai lucide-react bila tersedia.
- Sidebar, topbar, cards, panel, responsive.
- Leaflet + OpenStreetMap, AOI GeoJSON frozen, fit bounds, legenda/atribusi.
- Placeholder panel diberi label; jangan gunakan angka dummy tanpa badge.
- Peta jangan menampilkan genangan seolah nyata jika hanya ilustrasi.

## Acceptance criteria
- Peta nyata berfungsi jika internet tersedia.
- AOI sesuai file asli, geometri tidak berubah.
- Atribusi OpenStreetMap tampak.
- UI mengadaptasi style screenshot.
- Dashboard tetap graceful saat tile atau GeoJSON gagal.
- Marker tidak dibuat dari koordinat rekaan.

## Prompt siap pakai

```text
TASK 07 — DASHBOARD UI + MAP NYATA

Baca PRD induk, screenshot referensi Agronomus, AOI GeoJSON, dan handoff sebelumnya. Bangun dashboard dalam aplikasi Next.js App Router yang sudah disiapkan pada Task 01, menggunakan React + TypeScript, Tailwind CSS + shadcn/ui, Leaflet + React Leaflet, dan OpenStreetMap. Jangan membuat dashboard statis HTML atau mengganti framework. Ikuti gaya referensi: sidebar kiri, topbar, kartu putih, latar abu terang, aksen kuning keemasan, garis tipis dan radius halus. Konten harus khusus SiagaRob, bukan pertanian.
Peta harus menggunakan basemap nyata dan memuat data/geo/aoi_semarang_pilot.geojson apa adanya. Fit map bounds ke AOI, tampilkan outline/fill transparan, layer control/legend sederhana, dan atribusi OSM yang terlihat. Jangan mengubah AOI. Jangan menaruh marker stasiun kecuali koordinat berasal dari file atau sumber yang diverifikasi. Jangan menggambar polygon genangan yang tampak aktual dari data dummy. Jika ingin layer demo, gunakan label DEMO/ILUSTRASI secara permanen.
Buat navigasi Overview, Peta & Risiko, Telemetri, Prediksi, Aktuator, Sumber Data, dan Info Pengujian. Buat kartu yang label nilainya jelas: nilai IoT simulasi, prediksi eksperimental, dan data resmi harus dibedakan. Pada tahap ini boleh menggunakan empty states yang jelas, bukan angka live palsu. Pastikan jika peta/GeoJSON/tile gagal, aplikasi tidak blank dan menampilkan pesan yang berguna. React Leaflet/Leaflet wajib dimuat secara client-only melalui dynamic import (`ssr: false`) untuk mencegah error SSR `window is not defined`. Hindari bergantung pada CDN untuk library utama; install dependency melalui package manager proyek. Jalankan `npm run lint` dan `npm run build` (atau script setara yang benar-benar tersedia), perbaiki error yang muncul, uji responsif, dan laporkan cara menjalankan serta handoff. Jangan mengklaim peta memiliki layer banjir real-time jika belum terintegrasi.
```

# Sumber Data Resmi Eksternal & Kebijakan Kesegaran (Freshness)

Dokumentasi audit aksesibilitas, atribusi, dan integrasi sumber eksternal resmi sesuai standar PRD Induk §2 & §3.

---

## 1. Daftar Sumber Data

### 1.1 BMKG Data Terbuka (Prakiraan Cuaca Per Wilayah Administrasi)
- **Status Integrasi**: **LIVE & AKTIF** 🟢
- **Penyedia**: Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)
- **Endpoint Terverifikasi**: `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=33.74.02.1001`
- **Wilayah Sasaran**: Jawa Tengah, Kota Semarang, Kecamatan Semarang Utara, Kelurahan Bandarharjo (bagian dari AOI Pilot).
- **Atribusi Wajib**: `Data Terbuka BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)`
- **Label Wajib**: **`FORECAST`** *(Prakiraan cuaca regional per 3 jam, bukan pengukuran hujan lokal saat ini)*.
- **Kebijakan Cache**: In-memory caching dengan TTL 30 menit (1800 detik) untuk menghormati server terbuka BMKG.
- **Fallback**: Jika server BMKG mengalami gangguan jaringan/timeout, adapter FastAPI melakukan fallback ke data cache terakhir dengan status **`STALE`**; jika belum ada data sama sekali, berstatus **`UNAVAILABLE`**.

### 1.2 OpenStreetMap (Basemap & Fitur Geografis)
- **Status Integrasi**: **LIVE & AKTIF** 🟢
- **Penyedia**: OpenStreetMap Foundation (OSMF)
- **Lisensi**: Open Database License (ODbL)
- **Atribusi Wajib**: `&copy; OpenStreetMap contributors`
- **Kebijakan Penggunaan Tile**: Mematuhi kebijakan resmi OSM Foundation Tile Usage Policy (tidak melakukan prefetching/scraping massal, menggunakan cache peramban).

### 1.3 PantauBanjir Kota Semarang
- **Status Integrasi**: **UNAVAILABLE / DISABLED** ⚪
- **Penyedia**: Pemerintah Kota Semarang
- **Tautan Portal Resmi**: https://pantaubanjir.semarangkota.go.id/
- **Hasil Audit Akses**: Situs web Pemkot Semarang menyajikan informasi pompa dan pintu air secara visual, namun tidak memiliki endpoint REST API publik yang terbuka atau terdokumentasi.
- **Kepatuhan Etika PRD**: Sistem mematuhi PRD §2.2 & §8 dengan **TIDAK melakukan scraping agresif** yang berpotensi membebani server pemerintah kota. Status secara transparan dilaporkan sebagai `UNAVAILABLE` disertai tautan portal resmi.

### 1.4 BIG / SRGI Stasiun Pasang Surut Semarang
- **Status Integrasi**: **UNAVAILABLE / DISABLED** ⚪
- **Penyedia**: Badan Informasi Geospasial (BIG)
- **Tautan Portal Resmi**: https://srgi.big.go.id/tides/smrg
- **Hasil Audit Akses**: Stasiun pasang surut Pelabuhan Tanjung Emas Semarang tersedia pada portal SRGI, namun tidak tersedia API publik tanpa izin/kredensial khusus.
- **Kepatuhan Etika PRD**: Tidak mengarang data observasi stasiun; status secara transparan dilaporkan sebagai `UNAVAILABLE`.

---

## 2. Standar Metadata Kesegaran Data (PRD §3)

Setiap record data eksternal yang disajikan oleh adapter FastAPI membawa metadata lengkap:
```json
{
  "source": "BMKG Data Terbuka",
  "source_type": "official",
  "status": "LIVE",
  "category": "FORECAST",
  "location": "Bandarharjo, Semarang Utara, Kota Semarang",
  "issued_at": "2026-10-29T12:00:00",
  "fetched_at": "2026-10-29T15:03:37Z",
  "stale_after_seconds": 1800,
  "unit": "mm, °C, %",
  "source_url": "https://data.bmkg.go.id/prakiraan-cuaca/",
  "attribution": "Data Terbuka BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)",
  "notes": "Data diperoleh dari API Prakiraan Cuaca Terbuka BMKG."
}
```


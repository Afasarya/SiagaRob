# TASK 08 — Adapter sumber data eksternal

## Tujuan
Mengintegrasikan sumber data resmi dengan provenance, timestamp, freshness, timeout, cache, dan fallback.

## Scope
- Adapter backend untuk BMKG forecast dan peringatan dini cuaca.
- Investigasi integrasi data PantauBanjir Semarang dan BIG/SRGI tanpa mengasumsikan API.
- UI sumber data: source, source_type, fetched_at, issued/observed_at, status.
- Attribution BMKG.
- Jika endpoint tidak tersedia/izin tidak jelas/CORS tidak bisa, catat status dan jangan scraping agresif.

## Acceptance criteria
- Setiap data eksternal punya sumber dan timestamp.
- Prakiraan BMKG dilabeli prakiraan, bukan hujan terukur.
- Data unavailable/stale terlihat jelas.
- Timeout/retry/cache berjalan dan UI tidak blank.
- Tidak ada endpoint fiktif atau koordinat stasiun yang dikarang.
- Ada fixture/test respons tersanitasi untuk pengujian offline.

## Prompt siap pakai

```text
TASK 08 — EXTERNAL DATA ADAPTERS

Baca PRD induk dan task ini. Audit endpoint publik yang benar-benar terdokumentasi dan dapat diakses saat implementasi. Fokus pertama: API prakiraan cuaca terbuka BMKG dengan kode wilayah adm4 yang valid untuk wilayah target; tampilkan atribusi BMKG. Tambahkan feed peringatan dini BMKG bila format dan wilayahnya dapat diparse dengan benar. Untuk PantauBanjir Semarang dan BIG/SRGI pasang surut, jangan mengarang endpoint/API. Periksa dokumentasi dan akses yang tersedia; bila tidak ada akses programatik yang sah/stabil, tampilkan link sumber dan status UNAVAILABLE atau buat adapter disabled yang alasannya terdokumentasi.
Implementasikan adapter sumber eksternal dengan FastAPI di folder `backend/` sesuai stack PRD. Jangan memperkenalkan framework backend kedua. Dashboard Next.js harus mengambil data melalui endpoint FastAPI yang terdokumentasi, bukan memanggil API eksternal langsung dari browser jika CORS/akses tidak terjamin. Setiap record harus memuat source, source_type=official, issued_at/observed_at bila disediakan, fetched_at, unit, wilayah/stasiun, status LIVE/STALE/UNAVAILABLE, dan catatan freshness. Prakiraan BMKG harus diberi label FORECAST, bukan observed rainfall. Implementasikan timeout, retry terbatas, cache, rate limit yang wajar, validasi respons dan fallback. Jangan scraping agresif atau mem-bypass akses.
Sambungkan panel Sumber Data pada dashboard Next.js menggunakan fetch ke FastAPI, dengan loading/error/empty states dan validasi tipe respons. Data gagal harus terlihat sebagai UNAVAILABLE; jangan ganti dengan angka contoh. Gunakan fixture untuk tes offline dan jangan simpan hasil fixture seolah live. Tambahkan tes parser, invalid schema, timeout/fallback, timestamp dan attribution. Catat endpoint yang berhasil diuji, waktu pengujian, dan hasil aktual. Jika internet/API tidak dapat diuji, tandai BLOCKED/UNVERIFIED. Handoff.
```

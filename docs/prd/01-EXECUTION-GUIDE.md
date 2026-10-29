# Panduan Eksekusi — Google Antigravity

## Prinsip kerja

Kerjakan **satu task per giliran**. Jangan tempel seluruh prompt task sekaligus. PRD induk adalah kontrak permanen; task adalah instruksi kerja yang dibatasi scope-nya.

## Sebelum mulai

1. Ekstrak paket PRD.
2. Buat repository Git untuk project.
3. Salin `aoi_semarang_pilot.geojson` ke `data/geo/aoi_semarang_pilot.geojson` tanpa mengubah isi.
4. Letakkan folder dokumen PRD di repo, misalnya `docs/prd/`.
5. Pastikan Task 01 membuat aplikasi Next.js App Router di `dashboard/` dengan TypeScript, Tailwind CSS, npm scripts, dan lockfile; jangan lanjut sebelum scaffold dapat di-build.
6. Buka repository di Google Antigravity.
7. Pastikan agent dapat membaca PRD induk dan file task.
8. Tetapkan `PROJECT_ID` unik, contoh `kelas_iot_siagarob_07` (ubah ke ID unik tim).

## Protokol setiap task

1. Tempel prompt siap pakai pada file task.
2. Izinkan agent membaca repository dan menjalankan perintah yang relevan.
3. Tinjau daftar file yang diubah sebelum menerima perubahan.
4. Minta hasil tes yang nyata: perintah, exit code, ringkasan output.
5. Jika gagal, minta perbaikan scope kecil di task yang sama.
6. Setelah lulus, simpan handoff ke `docs/PROGRESS.md` dan commit.
7. Baru lanjut ke task berikutnya.

## Template prompt perbaikan

```text
Perbaiki hanya kegagalan pada task aktif. Baca kembali 00-PRD-CONTEXT.md dan file task aktif. Jangan melakukan refactor luas atau mengubah kontrak lintas modul. Reproduksi masalah terlebih dahulu, jelaskan akar masalah berdasarkan bukti, buat perubahan terkecil, jalankan ulang tes yang relevan, dan laporkan command serta hasil aktual. Jika tidak dapat menjalankan tes, katakan dengan jelas dan berikan langkah manual. Jangan klaim selesai jika bukti tidak ada.
```

## Template handoff yang wajib diisi

```markdown
## Handoff
- Task:
- Status: PASS / PARTIAL / BLOCKED
- Commit:
- File dibuat/diubah:
- Tes yang dijalankan:
- Hasil tes aktual:
- Hal yang belum selesai:
- Risiko/keputusan yang dibutuhkan:
- Langkah task berikutnya:
```

## Urutan task

1. Foundation, repository, konfigurasi, kontrak dan struktur.
2. Edge 1 — Pos Air.
3. Edge 2 — Pos Hujan dan aktuator.
4. Integrasi MQTT dan alat uji.
5. Training AI dan evaluasi.
6. AI server dan aturan otomatis.
7. Dashboard UI dan peta nyata.
8. Adapter sumber data eksternal dan panel sumber.
9. Integrasi dashboard live MQTT dan grafik.
10. Integrasi kontrol aktuator dan mode AUTO/MANUAL.
11. QA end-to-end T1–T7.
12. Dokumentasi dan demo final.

Urutan ini sengaja memisahkan dashboard UI, sumber data eksternal, dan live MQTT agar kegagalan satu integrasi tidak menghalangi pengerjaan visual dan pengujian.

## Definisi selesai

Task selesai hanya bila acceptance criteria pada task tersebut telah diverifikasi. “Kode sudah dibuat” bukan berarti task selesai. API eksternal boleh berstatus unavailable jika dibuktikan tidak bisa diakses, asalkan fallback dan labelnya benar serta hal itu dicatat.

## Demo tercepat

Jika waktu terbatas:
- Prioritaskan dashboard Next.js shell, peta OSM + AOI, mode demo berlabel, telemetri MQTT, grafik, dan tombol AUTO/MANUAL.
- Jalankan AI lokal dengan dataset sintetis dan laporkan MAE.
- Untuk peta Leaflet di Next.js, gunakan dynamic import client-only dengan `ssr: false`; jangan render Leaflet pada server.
- Tampilkan sumber resmi hanya bila berhasil diakses; jika tidak, tampilkan status `UNAVAILABLE` dengan tautan sumber.
- Jangan menunggu API eksternal yang tidak stabil untuk membuktikan komunikasi IoT.
- Jangan menghilangkan label simulasi hanya demi demo terlihat realistis.

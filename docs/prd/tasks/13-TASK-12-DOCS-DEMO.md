# TASK 12 — Dokumentasi, presentasi dan demo

## Tujuan
Menyiapkan repository yang bisa dijalankan orang lain, dokumentasi tugas kuliah, dan demo yang stabil.

## Scope
- README final: environment, install, konfigurasi, run commands, Wokwi setup, API source status, troubleshooting.
- `.env.example`, `.gitignore`, dokumentasi arsitektur dan topic.
- Script/demo checklist 3–5 menit.
- Ringkasan MAE dan test report aktual.
- Daftar batasan dan next steps.

## Acceptance criteria
- Clone bersih bisa diikuti sesuai README.
- Tidak ada secret.
- Demo punya jalur utama dan fallback.
- Data simulasi tidak disamarkan sebagai real.
- README mengungkapkan sumber dan limitasi model.
- Video/presentasi bisa dibuat dari langkah yang tertulis.

## Prompt siap pakai

```text
TASK 12 — FINAL DOCUMENTATION & DEMO

Baca PRD induk, handoff semua task, TEST-REPORT.md, dan repository aktual. Finalisasi README, docs/architecture.md, docs/mqtt-contract.md, docs/data-sources.md, docs/TEST-REPORT.md, dan docs/DEMO-SCRIPT.md. Jangan mengarang hasil atau mengklaim fitur yang belum lulus.
README harus mencantumkan prerequisite dan versi, setup PROJECT_ID, cara menginstal dependency dan menjalankan dashboard Next.js (`cd dashboard`, `npm install`, `npm run dev`), cara build production (`npm run build`), cara menjalankan FastAPI adapter jika ada, menjalankan train.py, menjalankan ai_server.py, dua project Wokwi, verifikasi MQTT, dan troubleshooting. Sertakan link sumber resmi dan atribusi wajib. Jelaskan data sintetis, keterbatasan model, perbedaan forecast dengan observation, dan bahwa ini bukan sistem peringatan publik yang tervalidasi.
Buat demo script 3–5 menit: overview UI dan AOI; sumber data beserta status; jalankan kedua edge; tunjukkan telemetry dan chart; naikkan slider/hujan untuk SIAGA; tunjukkan pompa/sirine; uji MANUAL override dan kembali AUTO; tunjukkan sensor error/offline; tutup dengan MAE aktual dan hasil T1–T7. Sertakan fallback bila API eksternal atau internet gagal: panel unavailable yang jujur dan demo IoT lokal/terlabel.
Audit secret, topic, AOI geometri, konsistensi docs, package.json/lockfile, lint, dan build Next.js. Jalankan test yang tersedia dan laporkan hasil. Jangan upload atau deploy publik tanpa persetujuan. Handoff final dengan daftar PASS/PARTIAL/BLOCKED.
```

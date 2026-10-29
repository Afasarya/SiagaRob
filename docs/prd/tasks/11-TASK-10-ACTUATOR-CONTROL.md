# TASK 10 — Kontrol aktuator dan AUTO/MANUAL

## Tujuan
Menyambungkan kontrol dashboard ke Edge 2 dengan perlindungan mode dan feedback.

## Scope
- Tombol AUTO, Pompa ON, Pompa OFF.
- MANUAL command memakai `source=dashboard`, `mode=MANUAL`, QoS1, non-retained.
- AUTO command mengembalikan kontrol ke AI.
- Konfirmasi aksi, disable saat offline, tampilkan pending/confirmed/error.
- Jangan mengklaim command berhasil sebelum telemetry feedback mengonfirmasi.

## Acceptance criteria
- Command sesuai payload/kontrak.
- Pompa manual tetap sesuai perintah saat status siaga; AI tidak override.
- AUTO mengembalikan kendali ke AI.
- UI membedakan command terkirim dan aktuator terkonfirmasi.
- Tidak ada retained command.

## Prompt siap pakai

```text
TASK 10 — ACTUATOR CONTROL

Baca PRD induk dan handoff sebelumnya. Implementasikan panel kontrol pompa/sirine dan mode di komponen client-side Next.js. Pastikan publish MQTT hanya terjadi dari interaksi pengguna nyata di browser, bukan saat render/server-side. Semua command ke siagarob/PROJECT_ID/edge/edge2/commands dengan QoS1 retain=false. Untuk kontrol manual publish pump ON/OFF, mode MANUAL, source dashboard, dan siren sesuai desain yang terdokumentasi. Tombol AUTO publish mode AUTO dengan source dashboard; setelah itu AI boleh kembali memutuskan command. Jangan pernah menyatakan aktuator berubah hanya karena publish berhasil: tunggu telemetry Edge2 berikutnya untuk konfirmasi.
Sediakan konfirmasi sebelum perubahan penting, disable kontrol bila Edge2 offline atau MQTT tidak tersambung, tampilkan state PENDING sampai feedback datang, lalu CONFIRMED/FAILED berdasarkan timeout dan telemetry. Jangan menambah kontrol aktuator fisik. Pastikan AI server dan firmware sama-sama menghormati MANUAL. Jangan menggunakan retained command.
Tambahkan test payload builder, retain=false/QoS1, status pending/feedback, offline disable, dan skenario AI command saat MANUAL. Jika broker/Wokwi tersedia, jalankan uji end-to-end dan simpan bukti; jika tidak, laporkan keterbatasannya. Handoff.
```

# TASK 11 — QA end-to-end T1–T7

## Tujuan
Memvalidasi seluruh sistem dengan skenario tugas sumber dan membuktikan hasil yang nyata.

## Scope
- Unit tests, integration checklist, skenario demo.
- Uji T1–T7 dari PRD induk.
- Ukur latensi bila tersedia timestamp yang valid.
- Audit data labels, source attribution, stale/offline, AOI unchanged.
- Bug fix terarah; tidak ada refactor besar.

## Acceptance criteria
- Semua T1–T7 memiliki hasil PASS/FAIL/BLOCKED dan bukti.
- MAE aktual dari train report.
- Latensi aktual jika terukur.
- Manual override dan timeout offline terbukti.
- Tidak ada klaim palsu terkait data real.
- Tidak menyebut semua tes lulus jika ada yang blocked.

## Prompt siap pakai

```text
TASK 11 — QA END-TO-END

Baca PRD induk, seluruh handoff, dan test yang sudah ada. Jangan menulis ulang aplikasi. Buat rencana QA dan jalankan pengujian yang benar-benar dapat dilakukan. Rekam untuk setiap T1–T7: langkah, input, expected result, actual result, PASS/FAIL/BLOCKED, bukti/log atau screenshot yang tersedia.
T1 air rendah/hujan nol -> AMAN dan pompa OFF.
T2 air/hujan meningkat -> prediksi melewati SIAGA_2 dan pompa ON otomatis dalam AUTO.
T3 air tinggi -> SIAGA_3, pompa ON, sirine ON.
T4 kontrol Pompa OFF dalam MANUAL -> pompa mati dan AI tidak menimpa.
T5 AUTO -> kontrol AI kembali aktif.
T6 sensor HC-SR04 invalid -> sensor_ok=false dan dashboard warning.
T7 Edge1 dihentikan -> status offline/LWT dan sistem OFFLINE setelah timeout.
Jalankan juga `npm run lint` dan `npm run build` pada dashboard Next.js (gunakan script yang benar-benar tersedia). Periksa hydration/SSR error, Leaflet `window is not defined`, reconnect/cleanup MQTT, dan responsif desktop/mobile. Periksa juga AOI geometri tidak berubah, atribusi OSM/BMKG, label official/simulated/prediction/demo, stale fallback, JSON invalid, reconnect, dan command non-retained. Ambil MAE model/baseline dari hasil training aktual; jangan mengarang. Ukur latency jika timestamps valid tersedia; jika tidak, tandai belum terukur.
Perbaiki bug hanya dalam scope terkecil dan jalankan ulang tes terkait. Jangan menandai blocked test sebagai pass. Hasilkan docs/TEST-REPORT.md dan daftar issue tersisa. Handoff.
```

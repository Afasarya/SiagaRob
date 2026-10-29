# Alat uji MQTT SiagaRob

CLI Python untuk memverifikasi kontrak MQTT ([docs/CONTRACT.md](../docs/CONTRACT.md)) sebelum AI/dashboard siap. Tidak mengubah firmware.

> **Peringatan:** `broker.hivemq.com` adalah broker **publik**. Siapa pun dapat membaca dan mengirim ke topic apa pun. Jangan kirim token/rahasia/data pribadi, dan jangan dipakai mengendalikan perangkat sungguhan. Hanya untuk demo.

## Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install paho-mqtt pytest         # lihat tools/requirements.txt
Copy-Item .env.example .env          # lalu ganti PROJECT_ID
```
`PROJECT_ID` dibaca dari variabel lingkungan `PROJECT_ID`, atau dari `.env` di root repo (satu sumber; tidak disalin ke banyak tempat). Placeholder `GANTI_DENGAN_ID_UNIK_TIM` ditolak.

## Perintah
```powershell
python tools/mqtt_tool.py topics                       # daftar topic + QoS/retain (offline)
python tools/mqtt_tool.py validate edge1_telemetry docs/examples/edge1_telemetry.json   # offline
echo '{"x":1}' | python tools/mqtt_tool.py validate edge2_commands -
python tools/mqtt_tool.py monitor                      # subscribe siagarob/PROJECT_ID/# (Ctrl+C berhenti)
python tools/mqtt_tool.py monitor --duration 60
python tools/mqtt_tool.py check-unique --seconds 15    # indikasi ID belum dipakai pihak lain
python tools/mqtt_tool.py publish-command --pump OFF --siren false --mode MANUAL --source dashboard
```
Key `validate`: `edge1_telemetry`, `edge2_telemetry`, `edge1_status`, `edge2_status`, `ai_prediction`, `edge2_commands`.

`monitor` menampilkan timestamp lokal, topic, payload, penanda `(retained)`, dan hasil validasi (`OK sesuai kontrak` / `TIDAK VALID: …`). Exit code 1 bila ada pesan tidak valid.

### Publish command uji
- **Tidak pernah otomatis**: perintah hanya kirim bila Anda menjalankan `publish-command` **dan** mengonfirmasi: ketik `YA` pada prompt, atau tambahkan `--yes`. Tanpa terminal interaktif dan tanpa `--yes` → dibatalkan, tidak ada koneksi.
- QoS 1, **retain=false** (tetap, tidak dapat diubah). Payload divalidasi dulu; menunggu PUBACK broker.
- Contoh bukti T4: `--pump ON --mode AUTO --source ai` setelah mode MANUAL harus ditolak oleh Edge 2 (lihat `edge2_wokwi/README.md`).

## Memastikan topic unik
1. Pilih `PROJECT_ID` panjang dan acak, mis. `kelas_iot_siagarob_07_x9k2` (hanya huruf/angka/underscore).
2. Matikan Edge/AI Anda, jalankan `check-unique`. Jika ada lalu lintas, ID kemungkinan dipakai pihak lain → ganti. Ini hanya indikasi pada jendela waktu itu, bukan jaminan.
3. Samakan `PROJECT_ID` di `.env`, `dashboard/.env.local`, `edge1_wokwi/sketch.ino`, `edge2_wokwi/sketch.ino`.

## Alternatif: mosquitto_sub / MQTT Explorer
```bash
mosquitto_sub -h broker.hivemq.com -p 1883 -t "siagarob/PROJECT_ID/#" -v
mosquitto_sub -h broker.hivemq.com -t "siagarob/PROJECT_ID/edge/+/status" -v   # status/LWT (retained)
# command uji (non-retained, QoS1) - hanya setelah Anda yakin:
mosquitto_pub -h broker.hivemq.com -t "siagarob/PROJECT_ID/edge/edge2/commands" -q 1 -m '{"pump":"OFF","siren":false,"mode":"MANUAL","source":"dashboard"}'
```
MQTT Explorer: host `broker.hivemq.com`, port 1883 (tanpa TLS) atau WebSocket TLS 8884 path `/mqtt`; subscribe `siagarob/PROJECT_ID/#`. Jangan memakai flag retain untuk command (`mosquitto_pub -r` dilarang).

## Tes (tanpa internet)
```powershell
.\.venv\Scripts\python -m pytest tools -q
```
Mencakup parser PROJECT_ID, pembentukan topic, tabel QoS/retain, validasi semua contoh `docs/examples`, payload rusak/tipe salah/di luar rentang, konfirmasi publish, dan QoS1/retain=false (client palsu). Tes ini **tidak** membuktikan koneksi broker; lihat bagian bukti live di `docs/PROGRESS.md`.

## Pemakaian ulang
Modul `tools/siagarob_contract.py` (topic, validasi) dapat diimpor oleh server AI (Task 06) agar kontrak tidak diduplikasi.


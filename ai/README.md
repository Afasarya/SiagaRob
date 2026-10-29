# AI SiagaRob (Task 05: Training & Task 06: Server)

> Data 100% **SYNTHETIC**, model berlabel **EXPERIMENTAL**. Bukan prediksi banjir operasional lapangan untuk Semarang.

## Komponen
- `features.py`: Definisi tunggal fitur input streaming (`level`, `rate_5`, `rain_10`, `rain_60`).
- `synthetic.py`: Generator data sintetis dengan parameter PRD dan filter median 5 sampel.
- `train.py`: Pelatihan model delta (`HistGradientBoostingRegressor`) dan evaluasi kronologis.
- `predictor.py`: Pembungkus inferensi dengan validasi rentang fisik sensor dan pengaman nilai ekstrim.
- `rules.py`: Logika penentuan status risiko (`max(level_now, level_30m)`) dan histeresis kontrol pompa.
- `ai_server.py`: Server MQTT yang memproses telemetri Edge 1 & 2, menerbitkan prediksi dan command otomatis.

## Cara Menjalankan

### 1. Training Model (Task 05)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r ai\requirements.txt
python ai\train.py --seed 42 --days 60
```
Menghasilkan `ai/model.joblib`, `ai/model_meta.json`, dan `docs/AI_EVALUATION.md`.

### 2. Menjalankan AI Server (Task 06)
Pastikan `PROJECT_ID` sudah diatur di file `.env` root repo:
```powershell
python ai\ai_server.py
```
Opsi flags:
- `--host`: MQTT broker host (default: `broker.hivemq.com` atau env `MQTT_HOST`)
- `--port`: MQTT broker port (default: `1883` atau env `MQTT_PORT`)

### 3. Menjalankan Pengujian
```powershell
python -m pytest ai -q
```


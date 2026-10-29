# Kontrak MQTT SiagaRob

- **Sumber Kebenaran**: `00-PRD-CONTEXT.md` §9
- **Broker Host**: `broker.hivemq.com`
- **Port TCP (Firmware & Python)**: `1883`
- **Port WebSocket TLS (Dashboard Browser)**: `8884` (URL: `wss://broker.hivemq.com:8884/mqtt`)
- **Prefix Topik**: `siagarob/{PROJECT_ID}/`

---

## 1. Tabel Topik & Parameter Komunikasi

| Suffix Topik | Topik Lengkap | Arah | QoS | Retain | Keterangan |
|---|---|---|:---:|:---:|---|
| `edge/edge1/telemetry` | `siagarob/{PROJECT_ID}/edge/edge1/telemetry` | Edge 1 &rarr; Cloud | 0 | `false` | Data telemetri tinggi pasang air (setiap 2 detik) |
| `edge/edge2/telemetry` | `siagarob/{PROJECT_ID}/edge/edge2/telemetry` | Edge 2 &rarr; Cloud | 0 | `false` | Data telemetri hujan, cuaca & status aktuator |
| `edge/edge1/status` | `siagarob/{PROJECT_ID}/edge/edge1/status` | Edge 1 &rarr; Cloud | 1 | `true` | Status koneksi: `online` saat terhubung, `offline` via LWT |
| `edge/edge2/status` | `siagarob/{PROJECT_ID}/edge/edge2/status` | Edge 2 &rarr; Cloud | 1 | `true` | Status koneksi: `online` saat terhubung, `offline` via LWT |
| `ai/prediction` | `siagarob/{PROJECT_ID}/ai/prediction` | AI &rarr; Dashboard | 0 | `true` | Prediksi ketinggian air +30 menit dan status risiko |
| `edge/edge2/commands` | `siagarob/{PROJECT_ID}/edge/edge2/commands` | AI / Dash &rarr; Edge 2 | 1 | `false` | Perintah kendali pompa, sirine, dan mode (dilarang retained) |

---

## 2. Struktur Skema JSON Payload

### 2.1 Telemetri Edge 1 (`edge/edge1/telemetry`)
Dipublikasikan setiap 2 detik (1 pesan mewakili 1 menit waktu simulasi):
```json
{
  "device_id": "edge1",
  "seq": 42,
  "level_cm": 82.4,
  "rate_cm_min": 1.8,
  "sensor_ok": true,
  "uptime_ms": 84000
}
```

### 2.2 Telemetri Edge 2 (`edge/edge2/telemetry`)
Dipublikasikan setiap 2 detik untuk melaporkan kondisi sensor dan keadaan aktual aktuator:
```json
{
  "device_id": "edge2",
  "seq": 40,
  "rain_mm_h": 24.0,
  "temp_c": 27.5,
  "hum_pct": 91,
  "pump": "ON",
  "siren": false,
  "mode": "AUTO",
  "uptime_ms": 80000
}
```

### 2.3 Prediksi AI (`ai/prediction`)
Dipublikasikan setiap ada pesan baru dari Edge 1:
```json
{
  "level_now": 82.4,
  "level_30m": 118.2,
  "status": "SIAGA_2",
  "reason": "model+rule",
  "seq": 42
}
```

### 2.4 Perintah Aktuator (`edge/edge2/commands`)
Diterbitkan oleh AI Server (mode AUTO) atau Dashboard (mode MANUAL):
```json
{
  "pump": "ON",
  "siren": false,
  "mode": "AUTO",
  "source": "ai"
}
```
*Catatan Perintah Dashboard*: Menggunakan `source: "dashboard"` dan dapat beralih antara `mode: "MANUAL"` atau `mode: "AUTO"`.


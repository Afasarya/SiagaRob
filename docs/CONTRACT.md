# Kontrak MQTT SiagaRob

Sumber kebenaran: `docs/prd/00-PRD-CONTEXT.md` §9. Implementasi TypeScript: `dashboard/src/lib/contract.ts`. Contoh payload: `docs/examples/`.

## PROJECT_ID

- Hanya huruf, angka, underscore. Harus unik per tim.
- Diatur lewat `.env` (salin dari `.env.example`): `PROJECT_ID` (Python/dokumentasi) dan `NEXT_PUBLIC_PROJECT_ID` (dashboard). Nilainya harus sama.
- Placeholder: `GANTI_DENGAN_ID_UNIK_TIM`. Ganti, mis. `kelas_iot_siagarob_07`.
- Firmware Wokwi tidak membaca `.env`; salin `PROJECT_ID` ke konstanta di sketch (dicatat pada Task 02/03).
- Broker publik: jangan taruh rahasia/token.

## Topic

Prefix: `siagarob/PROJECT_ID/`

| Topic suffix | Arah | QoS | Retain |
|---|---|---:|---|
| `edge/edge1/telemetry` | Edge 1 → cloud | 0 | false |
| `edge/edge2/telemetry` | Edge 2 → cloud | 0 | false |
| `edge/edge1/status` | status/LWT | 1 | true |
| `edge/edge2/status` | status/LWT | 1 | true |
| `ai/prediction` | AI → dashboard | 0 | true |
| `edge/edge2/commands` | AI/dashboard → Edge 2 | 1 | false |

- Status: `online` saat connect, LWT `offline`.
- Reconnect jeda 3 detik. Client ID unik, mis. `siagarob-edge1-PROJECT_ID`.
- Broker: `broker.hivemq.com:1883` (TCP, edge/AI); `wss://broker.hivemq.com:8884/mqtt` (dashboard).
- Command tidak retained.

## Payload

Lihat `docs/examples/*.json` (sama persis dengan PRD §9.1–9.4).

| Berkas | Topic |
|---|---|
| `edge1_telemetry.json` | `edge/edge1/telemetry` |
| `edge2_telemetry.json` | `edge/edge2/telemetry` |
| `ai_prediction.json` | `ai/prediction` |
| `edge2_command_ai.json` | `edge/edge2/commands` (source `ai`) |
| `edge2_command_dashboard.json` | `edge/edge2/commands` (source `dashboard`, MANUAL) |
| `edge_status_online.json` / `edge_status_offline.json` | `edge/*/status` (teks mentah, bukan JSON) |

Berkas status berisi string polos `online` / `offline`.
`edge2_command_dashboard.json` adalah contoh turunan sesuai PRD §9.4 ("source dashboard, mode MANUAL"); nilai `pump` contoh hanya ilustrasi.

## Metadata data (PRD §3)

`source`, `source_type` (`official|iot_simulated|derived|model_prediction|demo`), `observed_at`/`issued_at`, `fetched_at`, `stale_after_seconds`, `status` (`LIVE|STALE|UNAVAILABLE|SIMULATED|DEMO`), unit, lokasi. Tipe ada di `dashboard/src/lib/contract.ts`.


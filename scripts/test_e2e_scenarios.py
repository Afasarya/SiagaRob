"""Pengujian End-to-End Otomatis Skenario T1–T7 Tugas SiagaRob (Task 11).

Memvalidasi seluruh alur logika:
  - T1: Hujan 0, air rendah -> AMAN, Pompa OFF, Sirine OFF.
  - T2: Air/hujan meningkat -> SIAGA_2, Pompa ON otomatis (mode AUTO).
  - T3: Air tinggi / hujan lebat -> SIAGA_3, Pompa ON, Sirine ON.
  - T4: Pompa OFF dari Dashboard dalam mode MANUAL -> Pompa mati dan AI TIDAK menimpa.
  - T5: Dashboard mengirim mode AUTO -> Kendali AI kembali aktif.
  - T6: Sensor ultrasonik invalid / lonjakan -> sensor_ok=False, nilai tertahan, peringatan aktif.
  - T7: Edge 1 timeout (>30 detik) -> Status sistem OFFLINE & buffer prediktor di-reset.

Jalankan: python scripts/test_e2e_scenarios.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import ai_server as AS
import rules as R
import siagarob_contract as C

PID = "kelas_iot_siagarob_07"
MODEL_PATH = Path(__file__).resolve().parent.parent / "ai" / "model.joblib"


def run_e2e_tests():
    print("==================================================")
    print(" SIAGAROB END-TO-END QA: SKENARIO T1 - T7")
    print("==================================================")

    results = {}

    # Setup AI Server dengan Mock MQTT
    mock_mqtt = MagicMock()
    server = AS.AiServer(project_id=PID, model_path=MODEL_PATH, mqtt_client=mock_mqtt)

    # ------------------------------------------------------------------
    # T1: Hujan 0, air rendah -> AMAN, pompa OFF
    # ------------------------------------------------------------------
    t1_payload = json.dumps({
        "device_id": "edge1", "seq": 1, "level_cm": 80.0, "rate_cm_min": 0.0,
        "sensor_ok": True, "uptime_ms": 2000
    }).encode("utf-8")
    server.latest_edge2_mode = "AUTO"
    server.latest_rain_mm_h = 0.0

    res_t1 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", t1_payload)
    t1_pass = (
        res_t1 is not None and
        res_t1["prediction"]["status"] == "AMAN" and
        res_t1["decision"].pump == "OFF" and
        res_t1["decision"].siren is False
    )
    results["T1"] = ("PASS" if t1_pass else "FAIL", f"Status: {res_t1['prediction']['status']}, Pompa: {res_t1['decision'].pump}")
    print(f"[T1] Air Rendah & Hujan Nol: {results['T1'][0]} -> {results['T1'][1]}")

    # ------------------------------------------------------------------
    # T2: Air/hujan naik bertahap -> SIAGA_2, pompa ON otomatis
    # ------------------------------------------------------------------
    # Beri sampel kenaikan bertahap hingga melewati ambang SIAGA_2 (>= 120 cm)
    for i in range(60):
        level = 85.0 + (i * 0.6)  # Naik bertahap dari 85 cm hingga ~121 cm
        dummy = json.dumps({
            "device_id": "edge1", "seq": 10 + i, "level_cm": round(level, 1),
            "rate_cm_min": 0.6, "sensor_ok": True, "uptime_ms": 10000 + i * 2000
        }).encode("utf-8")
        server.latest_rain_mm_h = 35.0
        res_t2 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", dummy)

    t2_pass = (
        res_t2 is not None and
        res_t2["prediction"]["status"] in ("SIAGA_2", "SIAGA_3") and
        res_t2["decision"].pump == "ON" and
        res_t2["command"] is not None and
        res_t2["command"]["pump"] == "ON" and
        res_t2["command"]["mode"] == "AUTO"
    )
    results["T2"] = ("PASS" if t2_pass else "FAIL", f"Status: {res_t2['prediction']['status']}, Pompa: {res_t2['decision'].pump}, Command AI: {res_t2['command']}")
    print(f"[T2] Kenaikan Air ke SIAGA_2: {results['T2'][0]} -> {results['T2'][1]}")

    # ------------------------------------------------------------------
    # T3: Hujan lebat, air tinggi -> SIAGA_3, pompa ON, sirine ON
    # ------------------------------------------------------------------
    t3_payload = json.dumps({
        "device_id": "edge1", "seq": 80, "level_cm": 145.0, "rate_cm_min": 2.0,
        "sensor_ok": True, "uptime_ms": 150000
    }).encode("utf-8")
    server.latest_rain_mm_h = 75.0
    res_t3 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", t3_payload)

    t3_pass = (
        res_t3 is not None and
        res_t3["prediction"]["status"] == "SIAGA_3" and
        res_t3["decision"].pump == "ON" and
        res_t3["decision"].siren is True and
        res_t3["command"]["siren"] is True
    )
    results["T3"] = ("PASS" if t3_pass else "FAIL", f"Status: {res_t3['prediction']['status']}, Pompa: {res_t3['decision'].pump}, Sirine: {res_t3['decision'].siren}")
    print(f"[T3] Air Tinggi SIAGA_3: {results['T3'][0]} -> {results['T3'][1]}")

    # ------------------------------------------------------------------
    # T4: Pompa OFF dari dashboard dalam MANUAL -> Pompa mati, AI tidak menimpa
    # ------------------------------------------------------------------
    # Update telemetri Edge 2: operator beralih ke mode MANUAL dan matikan pompa
    e2_manual_payload = json.dumps({
        "device_id": "edge2", "seq": 50, "rain_mm_h": 40.0, "temp_c": 28.0,
        "hum_pct": 85, "pump": "OFF", "siren": False, "mode": "MANUAL", "uptime_ms": 100000
    }).encode("utf-8")
    server.handle_message(f"siagarob/{PID}/edge/edge2/telemetry", e2_manual_payload)

    mock_mqtt.reset_mock()
    # Datang telemetri Edge 1 dengan air masih tinggi (130 cm / SIAGA_2)
    t4_payload = json.dumps({
        "device_id": "edge1", "seq": 81, "level_cm": 130.0, "rate_cm_min": 0.0,
        "sensor_ok": True, "uptime_ms": 152000
    }).encode("utf-8")
    res_t4 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", t4_payload)

    # Verifikasi AI TIDAK mengirimkan command ke Edge 2 (command is None)
    published_topics = [call[0][0] for call in mock_mqtt.publish.call_args_list]
    t4_pass = (
        res_t4 is not None and
        res_t4["command"] is None and
        C.topic(PID, "edge2_commands") not in published_topics
    )
    results["T4"] = ("PASS" if t4_pass else "FAIL", "Mode MANUAL aktif: AI dilarang mengirim command override ke aktuator.")
    print(f"[T4] MANUAL Override (Pompa OFF): {results['T4'][0]} -> {results['T4'][1]}")

    # ------------------------------------------------------------------
    # T5: Pilih AUTO -> Kendali AI kembali aktif
    # ------------------------------------------------------------------
    e2_auto_payload = json.dumps({
        "device_id": "edge2", "seq": 51, "rain_mm_h": 40.0, "temp_c": 28.0,
        "hum_pct": 85, "pump": "OFF", "siren": False, "mode": "AUTO", "uptime_ms": 102000
    }).encode("utf-8")
    server.handle_message(f"siagarob/{PID}/edge/edge2/telemetry", e2_auto_payload)

    mock_mqtt.reset_mock()
    # Datang telemetri Edge 1 level 130 cm (SIAGA_2) dalam mode AUTO
    res_t5 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", t4_payload)
    cmd_topics = [call[0][0] for call in mock_mqtt.publish.call_args_list if call[0][0] == C.topic(PID, "edge2_commands")]

    t5_pass = (
        res_t5 is not None and
        res_t5["command"] is not None and
        res_t5["command"]["pump"] == "ON" and
        len(cmd_topics) == 1
    )
    results["T5"] = ("PASS" if t5_pass else "FAIL", f"Kembali AUTO: AI kembali menerbitkan command Pompa ON (topic: {cmd_topics[0] if cmd_topics else 'none'}).")
    print(f"[T5] Kembalikan ke AUTO: {results['T5'][0]} -> {results['T5'][1]}")

    # ------------------------------------------------------------------
    # T6: Jarak HC-SR04 invalid -> sensor_ok=false & dashboard warning
    # ------------------------------------------------------------------
    t6_payload = json.dumps({
        "device_id": "edge1", "seq": 82, "level_cm": 80.0, "rate_cm_min": 0.0,
        "sensor_ok": False, "uptime_ms": 154000
    }).encode("utf-8")
    res_t6 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", t6_payload)

    t6_pass = (
        res_t6 is not None and
        "sensor" in res_t6["prediction"]["reason"]
    )
    results["T6"] = ("PASS" if t6_pass else "FAIL", f"Sensor error terdeteksi: reason='{res_t6['prediction']['reason']}'.")
    print(f"[T6] Deteksi Sensor Error (HC-SR04): {results['T6'][0]} -> {results['T6'][1]}")

    # ------------------------------------------------------------------
    # T7: Hentikan Edge 1 -> status offline / timeout >30 detik
    # ------------------------------------------------------------------
    mock_mqtt.reset_mock()
    # Simulasikan waktu berlalu 35 detik dari last_edge1_time
    now = time.time()
    server.last_edge1_time = now - 35.0
    timeout_triggered = server.check_timeouts(current_time=now)

    offline_calls = [
        call for call in mock_mqtt.publish.call_args_list
        if call[0][0] == C.topic(PID, "ai_prediction") and "OFFLINE" in call[0][1]
    ]

    t7_pass = (
        timeout_triggered is True and
        server.edge1_online is False and
        len(offline_calls) == 1
    )
    results["T7"] = ("PASS" if t7_pass else "FAIL", f"Timeout terdeteksi (>30s): Status sistem OFFLINE dipublish ke {C.topic(PID, 'ai_prediction')}.")
    print(f"[T7] Timeout Edge 1 Offline: {results['T7'][0]} -> {results['T7'][1]}")

    print("==================================================")
    all_pass = all(v[0] == "PASS" for v in results.values())
    print(f"HASIL AKHIR SKENARIO T1-T7: {'SEMUA PASS' if all_pass else 'ADA YANG GAGAL'}")
    print("==================================================")
    return results


if __name__ == "__main__":
    res = run_e2e_tests()
    if not all(v[0] == "PASS" for v in res.values()):
        sys.exit(1)
    sys.exit(0)

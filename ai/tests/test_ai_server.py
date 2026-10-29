import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import ai_server as AS  # noqa: E402
import rules as R  # noqa: E402
import siagarob_contract as C  # noqa: E402

PID = "kelas_iot_siagarob_07"
MODEL_PATH = Path(__file__).resolve().parent.parent / "model.joblib"


# ==========================================
# 1. Uji Ambang Batas & Aturan Status Risiko
# ==========================================
@pytest.mark.parametrize(
    "now,pred30,expected",
    [
        (80.0, 80.0, "AMAN"),
        (104.9, 100.0, "AMAN"),
        (105.0, 90.0, "SIAGA_1"),
        (90.0, 105.0, "SIAGA_1"),  # Menguji max(level_now, level_30m)
        (119.9, 100.0, "SIAGA_1"),
        (120.0, 80.0, "SIAGA_2"),
        (85.0, 120.0, "SIAGA_2"),  # Prediksi naik memicu siaga
        (139.9, 130.0, "SIAGA_2"),
        (140.0, 80.0, "SIAGA_3"),
        (80.0, 140.0, "SIAGA_3"),
    ],
)
def test_threshold_risk_status(now, pred30, expected):
    assert R.determine_status(now, pred30) == expected


# ==========================================
# 2. Uji Histeresis Kontrol Pompa
# ==========================================
def test_hysteresis_pump_off():
    eng = R.DecisionEngine()

    # Awal aman -> pompa OFF
    d = eng.evaluate(80.0, 80.0)
    assert d.pump == "OFF" and not d.siren

    # Air naik ke SIAGA_2 (120 cm) -> Pompa ON
    d = eng.evaluate(125.0, 125.0)
    assert d.pump == "ON" and not d.siren

    # Air turun sedikit ke 115 cm (di bawah 120, tapi belum di bawah 110 cm)
    # Pompa harus TETAP ON karena belum melewati batas histeresis 10 cm
    d = eng.evaluate(115.0, 115.0)
    assert d.pump == "ON"
    assert eng.below_count == 0  # 115 >= 110, counter tidak jalan

    # Air turun ke 105 cm (< 110 cm) -> Sampel 1 s.d. 4: Pompa TETAP ON
    for i in range(1, 5):
        d = eng.evaluate(105.0, 105.0)
        assert d.pump == "ON", f"Pompa harus tetap ON pada sampel ke-{i}"
        assert d.hysteresis_count == i

    # Sampel ke-5 berturut-turut di bawah 110 cm -> Pompa baru boleh OFF!
    d = eng.evaluate(105.0, 105.0)
    assert d.pump == "OFF"
    assert "hys_cleared" in d.reason


def test_hysteresis_reset_if_level_rises():
    eng = R.DecisionEngine()
    eng.evaluate(125.0, 125.0)  # Pompa ON

    # 3 sampel di bawah 110 cm
    for _ in range(3):
        eng.evaluate(105.0, 105.0)
    assert eng.below_count == 3

    # Naik lagi ke 115 cm -> counter reset ke 0
    eng.evaluate(115.0, 115.0)
    assert eng.below_count == 0
    assert eng.pump_on is True


def test_siren_trigger_and_stop():
    eng = R.DecisionEngine()
    # SIAGA_3 -> Pompa ON, Sirine ON
    d = eng.evaluate(145.0, 145.0)
    assert d.pump == "ON" and d.siren is True

    # Turun ke SIAGA_2 -> Pompa ON, Sirine langsung OFF
    d = eng.evaluate(125.0, 125.0)
    assert d.pump == "ON" and d.siren is False


# ==========================================
# 3. Uji AI Server, Kontrak, dan AUTO/MANUAL
# ==========================================
@pytest.fixture
def mock_mqtt():
    return MagicMock()


@pytest.fixture
def server(mock_mqtt):
    return AS.AiServer(project_id=PID, model_path=MODEL_PATH, mqtt_client=mock_mqtt)


def test_server_reject_invalid_edge1_telemetry(server, mock_mqtt):
    # JSON rusak
    res = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", b"{rusak")
    assert res is None
    assert mock_mqtt.publish.call_count == 0


def test_server_edge2_telemetry_updates_mode_and_rain(server):
    payload = json.dumps({
        "device_id": "edge2",
        "seq": 10,
        "rain_mm_h": 45.0,
        "temp_c": 28.0,
        "hum_pct": 85,
        "pump": "OFF",
        "siren": False,
        "mode": "MANUAL",
        "uptime_ms": 20000,
    }).encode("utf-8")

    res = server.handle_message(f"siagarob/{PID}/edge/edge2/telemetry", payload)
    assert res is not None
    assert server.latest_rain_mm_h == 45.0
    assert server.latest_edge2_mode == "MANUAL"


def test_server_ai_command_only_in_auto_mode(server, mock_mqtt):
    # Buat telemetri Edge 1 dengan level air tinggi (SIAGA_2 -> butuh pompa ON)
    e1_payload = json.dumps({
        "device_id": "edge1",
        "seq": 1,
        "level_cm": 125.0,
        "rate_cm_min": 1.0,
        "sensor_ok": True,
        "uptime_ms": 2000,
    }).encode("utf-8")

    # KASUS A: Mode MANUAL (AI TIDAK boleh publish command)
    server.latest_edge2_mode = "MANUAL"
    res = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", e1_payload)
    assert res is not None
    assert res["command"] is None  # Tidak mengirim command ke Edge 2

    # Verifikasi hanya topic ai/prediction yang dipublish, BUKAN command
    published_topics = [call[0][0] for call in mock_mqtt.publish.call_args_list]
    assert C.topic(PID, "ai_prediction") in published_topics
    assert C.topic(PID, "edge2_commands") not in published_topics

    mock_mqtt.reset_mock()

    # KASUS B: Mode AUTO (AI BOLEH publish command)
    server.latest_edge2_mode = "AUTO"
    res2 = server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", e1_payload)
    assert res2 is not None
    assert res2["command"] is not None
    assert res2["command"]["pump"] == "ON"
    assert res2["command"]["mode"] == "AUTO"
    assert res2["command"]["source"] == "ai"

    # Verifikasi command terkirim dengan QoS 1 dan retain=False
    cmd_call = [c for c in mock_mqtt.publish.call_args_list if c[0][0] == C.topic(PID, "edge2_commands")]
    assert len(cmd_call) == 1
    assert cmd_call[0][1]["qos"] == 1
    assert cmd_call[0][1]["retain"] is False


def test_server_edge1_timeout_detection(server, mock_mqtt):
    t0 = 1000.0
    e1_payload = json.dumps({
        "device_id": "edge1",
        "seq": 5,
        "level_cm": 80.0,
        "rate_cm_min": 0.0,
        "sensor_ok": True,
        "uptime_ms": 10000,
    }).encode("utf-8")

    server.handle_message(f"siagarob/{PID}/edge/edge1/telemetry", e1_payload, current_time=t0)
    assert server.edge1_online is True

    # 10 detik kemudian -> belum timeout
    assert server.check_timeouts(current_time=t0 + 10.0) is False
    assert server.edge1_online is True

    # 31 detik kemudian -> terdeteksi timeout (> 30s)
    mock_mqtt.reset_mock()
    assert server.check_timeouts(current_time=t0 + 31.0) is True
    assert server.edge1_online is False

    # Verifikasi payload OFFLINE dipublish
    pred_call = [c for c in mock_mqtt.publish.call_args_list if c[0][0] == C.topic(PID, "ai_prediction")]
    assert len(pred_call) == 1
    payload = json.loads(pred_call[0][0][1])
    assert "OFFLINE" in payload["reason"]
    assert payload["seq"] == 5


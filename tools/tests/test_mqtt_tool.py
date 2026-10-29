import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mqtt_tool as T  # noqa: E402
import siagarob_contract as C  # noqa: E402

PID = "kelas_iot_siagarob_07"
NOW = datetime(2026, 10, 29, 21, 0, 0, tzinfo=timezone.utc)


def test_describe_valid():
    t = C.topic(PID, "edge1_telemetry")
    lines, ok = T.describe_message(PID, t, b'{"device_id":"edge1","seq":1,"level_cm":80,"rate_cm_min":0,"sensor_ok":true,"uptime_ms":2000}', False, NOW)
    assert ok
    assert "2026-10-29 21:00:00" in lines[0] and t in lines[0]
    assert "OK sesuai kontrak" in lines[2]


def test_describe_json_rusak():
    lines, ok = T.describe_message(PID, C.topic(PID, "edge2_telemetry"), b"{rusak", False, NOW)
    assert not ok and "TIDAK VALID: JSON tidak valid" in lines[2]


def test_describe_retained_dan_status():
    lines, ok = T.describe_message(PID, C.topic(PID, "edge1_status"), b"offline", True, NOW)
    assert ok and "(retained)" in lines[0]


def test_describe_topic_di_luar_kontrak():
    lines, ok = T.describe_message(PID, f"siagarob/{PID}/lain", b"x", False, NOW)
    assert ok and "di luar kontrak" in lines[2]


def test_confirm():
    assert T.confirm("p", True, False)
    assert not T.confirm("p", False, False)  # tanpa TTY dan tanpa --yes
    assert T.confirm("p", False, True, input_fn=lambda _: "YA")
    assert not T.confirm("p", False, True, input_fn=lambda _: "ya")
    assert not T.confirm("p", False, True, input_fn=lambda _: "")


def test_publish_tanpa_konfirmasi_tidak_menyambung(monkeypatch, capsys):
    monkeypatch.setenv("PROJECT_ID", PID)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)

    def boom(*a, **k):
        raise AssertionError("tidak boleh membuat client/koneksi tanpa konfirmasi")

    monkeypatch.setattr(T, "_make_client", boom)
    rc = T.main(["publish-command", "--pump", "ON", "--siren", "false", "--mode", "AUTO", "--source", "ai"])
    err = capsys.readouterr()
    assert rc == 4 and "DIBATALKAN" in err.err and "retain=false" in err.out


def test_publish_invalid_ditolak_sebelum_koneksi(monkeypatch):
    monkeypatch.setenv("PROJECT_ID", PID)
    monkeypatch.setattr(T, "_make_client", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no net")))
    monkeypatch.setattr(C, "build_command", lambda *a: (_ for _ in ()).throw(ValueError("x")))
    assert T.main(["publish-command", "--pump", "ON", "--siren", "true", "--mode", "AUTO", "--source", "ai", "--yes"]) == 2


def test_publish_qos1_retain_false(monkeypatch):
    """Dengan konfirmasi, publish memakai QoS1 dan retain=False (client palsu, tanpa jaringan)."""
    monkeypatch.setenv("PROJECT_ID", PID)
    calls = {}

    class Info:
        def wait_for_publish(self, timeout=None):
            pass

        def is_published(self):
            return True

    class Fake:
        def publish(self, topic, body, qos, retain):
            calls.update(topic=topic, body=body, qos=qos, retain=retain)
            return Info()

        def loop_stop(self):
            pass

        def disconnect(self):
            pass

    monkeypatch.setattr(T, "_make_client", lambda *a, **k: Fake())
    monkeypatch.setattr(T, "_connect", lambda *a, **k: None)
    rc = T.main(["publish-command", "--pump", "OFF", "--siren", "false", "--mode", "MANUAL", "--source", "dashboard", "--yes"])
    assert rc == 0
    assert calls["topic"] == f"siagarob/{PID}/edge/edge2/commands"
    assert calls["qos"] == 1 and calls["retain"] is False
    assert json.loads(calls["body"]) == {"pump": "OFF", "siren": False, "mode": "MANUAL", "source": "dashboard"}


def test_topics_dan_validate_offline(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("PROJECT_ID", PID)
    assert T.main(["topics"]) == 0
    out = capsys.readouterr().out
    assert f"siagarob/{PID}/edge/edge2/commands" in out and "QoS1" in out
    ex = Path(__file__).resolve().parents[2] / "docs" / "examples" / "edge1_telemetry.json"
    assert T.main(["validate", "edge1_telemetry", str(ex)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{rusak", encoding="utf-8")
    assert T.main(["validate", "edge1_telemetry", str(bad)]) == 1
    assert "JSON tidak valid" in capsys.readouterr().err


def test_placeholder_ditolak_cli(monkeypatch, capsys):
    monkeypatch.setenv("PROJECT_ID", C.PLACEHOLDER_PROJECT_ID)
    assert T.main(["topics"]) == 2
    assert "placeholder" in capsys.readouterr().err


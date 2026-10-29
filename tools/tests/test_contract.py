import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import siagarob_contract as C  # noqa: E402

EX = Path(__file__).resolve().parents[2] / "docs" / "examples"
PID = "kelas_iot_siagarob_07"


# ---- PROJECT_ID ----
def test_project_id_dari_env():
    assert C.load_project_id({"PROJECT_ID": PID}, dotenv=Path("tidak_ada")) == PID


def test_project_id_dari_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text('# komentar\nPROJECT_ID="abc_123"\nLAIN=1\n', encoding="utf-8")
    assert C.load_project_id({}, dotenv=f) == "abc_123"


def test_env_mengalahkan_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("PROJECT_ID=dari_file\n", encoding="utf-8")
    assert C.load_project_id({"PROJECT_ID": "dari_env"}, dotenv=f) == "dari_env"


@pytest.mark.parametrize("bad", ["", None, C.PLACEHOLDER_PROJECT_ID, "ada spasi", "a/b", "a#b", "a+b", "id-strip"])
def test_project_id_tidak_valid(bad):
    with pytest.raises(C.ProjectIdError):
        C.validate_project_id(bad)


def test_project_id_hilang(tmp_path):
    with pytest.raises(C.ProjectIdError):
        C.load_project_id({}, dotenv=tmp_path / "x.env")


# ---- Topic ----
def test_topic_dari_satu_project_id():
    assert C.topic(PID, "edge1_telemetry") == f"siagarob/{PID}/edge/edge1/telemetry"
    assert C.topic(PID, "edge2_commands") == f"siagarob/{PID}/edge/edge2/commands"
    assert C.topic(PID, "ai_prediction") == f"siagarob/{PID}/ai/prediction"
    assert all(C.topic(PID, k).startswith(f"siagarob/{PID}/") for k in C.TOPICS)


def test_tabel_qos_retain_sesuai_prd():
    t = C.TOPICS
    assert t["edge1_telemetry"][1:] == (0, False)
    assert t["edge2_telemetry"][1:] == (0, False)
    assert t["edge1_status"][1:] == (1, True)
    assert t["edge2_status"][1:] == (1, True)
    assert t["ai_prediction"][1:] == (0, True)
    assert t["edge2_commands"][1:] == (1, False)
    assert len(t) == 6


def test_classify():
    for k in C.TOPICS:
        assert C.classify_topic(PID, C.topic(PID, k)) == k
    assert C.classify_topic(PID, f"siagarob/{PID}/lain") is None
    assert C.classify_topic(PID, "siagarob/id_lain/edge/edge1/telemetry") is None


# ---- Contoh payload dokumentasi harus valid ----
@pytest.mark.parametrize("fname,key", [
    ("edge1_telemetry.json", "edge1_telemetry"),
    ("edge2_telemetry.json", "edge2_telemetry"),
    ("ai_prediction.json", "ai_prediction"),
    ("edge2_command_ai.json", "edge2_commands"),
    ("edge2_command_dashboard.json", "edge2_commands"),
    ("edge_status_online.json", "edge1_status"),
    ("edge_status_offline.json", "edge2_status"),
])
def test_contoh_docs_valid(fname, key):
    v = C.validate_payload(key, (EX / fname).read_text(encoding="utf-8"))
    assert v.ok, v.errors
    assert not v.warnings


# ---- Payload invalid ----
def test_json_rusak_pesan_jelas():
    v = C.validate_payload("edge1_telemetry", '{"device_id": "edge1", ')
    assert not v.ok and "JSON tidak valid" in v.errors[0] and "baris" in v.errors[0]


@pytest.mark.parametrize("raw,frag", [
    ("", "kosong"),
    ("[1,2]", "objek"),
    ("123", "objek"),
    ("null", "objek"),
])
def test_bukan_objek(raw, frag):
    v = C.validate_payload("edge2_telemetry", raw)
    assert not v.ok and frag in v.errors[0]


def test_bukan_utf8():
    v = C.validate_payload("edge1_telemetry", b"\xff\xfe\x00")
    assert not v.ok and "UTF-8" in v.errors[0]


def _e1(**kw):
    d = json.loads((EX / "edge1_telemetry.json").read_text())
    d.update(kw)
    return json.dumps(d)


def _e2(**kw):
    d = json.loads((EX / "edge2_telemetry.json").read_text())
    d.update(kw)
    return json.dumps(d)


def test_field_hilang():
    d = json.loads(_e1())
    del d["level_cm"]
    v = C.validate_payload("edge1_telemetry", json.dumps(d))
    assert not v.ok and any("level_cm" in e and "hilang" in e for e in v.errors)


@pytest.mark.parametrize("kw", [
    {"device_id": "edge2"},
    {"seq": -1},
    {"seq": 1.5},
    {"seq": True},
    {"level_cm": "82.4"},
    {"level_cm": True},
    {"level_cm": None},
    {"sensor_ok": 1},
    {"sensor_ok": "true"},
    {"uptime_ms": -5},
])
def test_edge1_invalid(kw):
    assert not C.validate_payload("edge1_telemetry", _e1(**kw)).ok


def test_edge1_nan_ditolak():
    # json.dumps menghasilkan NaN (JSON non-standar); parser Python menerimanya -> validator harus menolak
    v = C.validate_payload("edge1_telemetry", '{"device_id":"edge1","seq":1,"level_cm":NaN,"rate_cm_min":0,"sensor_ok":true,"uptime_ms":1}')
    assert not v.ok


@pytest.mark.parametrize("kw", [
    {"device_id": "edge1"},
    {"rain_mm_h": -1},
    {"rain_mm_h": 80.5},
    {"hum_pct": 101},
    {"temp_c": 200},
    {"pump": "on"},
    {"pump": 1},
    {"siren": "false"},
    {"mode": "HYBRID"},
])
def test_edge2_invalid(kw):
    assert not C.validate_payload("edge2_telemetry", _e2(**kw)).ok


def test_edge2_batas_valid():
    assert C.validate_payload("edge2_telemetry", _e2(rain_mm_h=0, hum_pct=0)).ok
    assert C.validate_payload("edge2_telemetry", _e2(rain_mm_h=80, hum_pct=100)).ok


def test_field_tambahan_hanya_peringatan():
    v = C.validate_payload("edge1_telemetry", _e1(ekstra=1))
    assert v.ok and v.warnings and "ekstra" in v.warnings[0]


def test_prediction():
    ok = '{"level_now":82.4,"level_30m":118.2,"status":"SIAGA_2","reason":"model+rule","seq":42}'
    assert C.validate_payload("ai_prediction", ok).ok
    for s in ("AMAN", "SIAGA_1", "SIAGA_2", "SIAGA_3"):
        assert C.validate_payload("ai_prediction", ok.replace("SIAGA_2", s)).ok
    assert not C.validate_payload("ai_prediction", ok.replace("SIAGA_2", "SIAGA_4")).ok
    assert not C.validate_payload("ai_prediction", ok.replace('"reason":"model+rule"', '"reason":""')).ok


def test_command_invalid_cermin_firmware():
    base = {"pump": "ON", "siren": False, "mode": "AUTO", "source": "ai"}
    assert C.validate_payload("edge2_commands", json.dumps(base)).ok
    for k, bad in [("pump", "on"), ("pump", "MAYBE"), ("siren", "yes"), ("mode", "HYBRID"), ("source", "hacker")]:
        d = dict(base, **{k: bad})
        assert not C.validate_payload("edge2_commands", json.dumps(d)).ok, (k, bad)
    d = dict(base)
    del d["source"]
    assert not C.validate_payload("edge2_commands", json.dumps(d)).ok


def test_status_teks():
    for k in ("edge1_status", "edge2_status"):
        assert C.validate_payload(k, "online").ok
        assert C.validate_payload(k, b"offline\n").ok
        assert not C.validate_payload(k, "ONLINE").ok
        assert not C.validate_payload(k, '{"status":"online"}').ok


def test_key_tidak_dikenal():
    assert not C.validate_payload("nope", "{}").ok


def test_build_command():
    assert C.build_command("OFF", False, "MANUAL", "dashboard") == {"pump": "OFF", "siren": False, "mode": "MANUAL", "source": "dashboard"}
    with pytest.raises(ValueError):
        C.build_command("on", False, "MANUAL", "dashboard")


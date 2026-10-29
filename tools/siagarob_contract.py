"""Kontrak MQTT SiagaRob untuk alat Python (PRD §9). Tanpa dependensi jaringan.

Satu sumber PROJECT_ID: variabel lingkungan PROJECT_ID, atau berkas .env di root repo.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PLACEHOLDER_PROJECT_ID = "GANTI_DENGAN_ID_UNIK_TIM"
_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9_]+$")
REPO_ROOT = Path(__file__).resolve().parent.parent

# key -> (suffix, qos, retain) sesuai PRD §9
TOPICS: dict[str, tuple[str, int, bool]] = {
    "edge1_telemetry": ("edge/edge1/telemetry", 0, False),
    "edge2_telemetry": ("edge/edge2/telemetry", 0, False),
    "edge1_status": ("edge/edge1/status", 1, True),
    "edge2_status": ("edge/edge2/status", 1, True),
    "ai_prediction": ("ai/prediction", 0, True),
    "edge2_commands": ("edge/edge2/commands", 1, False),
}

STATUSES = ("AMAN", "SIAGA_1", "SIAGA_2", "SIAGA_3")


class ProjectIdError(ValueError):
    pass


def _read_dotenv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def validate_project_id(pid: str | None) -> str:
    if not pid:
        raise ProjectIdError("PROJECT_ID belum diatur. Isi di .env (salin dari .env.example) atau set variabel lingkungan PROJECT_ID.")
    if pid == PLACEHOLDER_PROJECT_ID:
        raise ProjectIdError(f"PROJECT_ID masih placeholder '{PLACEHOLDER_PROJECT_ID}'. Ganti dengan ID unik tim, mis. kelas_iot_siagarob_07.")
    if not _PROJECT_ID_RE.match(pid):
        raise ProjectIdError(f"PROJECT_ID '{pid}' tidak valid: hanya huruf, angka, dan underscore.")
    return pid


def load_project_id(env: dict[str, str] | None = None, dotenv: Path | None = None) -> str:
    """Prioritas: variabel lingkungan, lalu .env root repo."""
    env = os.environ if env is None else env
    pid = env.get("PROJECT_ID")
    if not pid:
        pid = _read_dotenv(dotenv or (REPO_ROOT / ".env")).get("PROJECT_ID")
    return validate_project_id(pid)


def prefix(project_id: str) -> str:
    return f"siagarob/{validate_project_id(project_id)}/"


def topic(project_id: str, key: str) -> str:
    return prefix(project_id) + TOPICS[key][0]


def classify_topic(project_id: str, full_topic: str) -> str | None:
    """Kembalikan key kontrak untuk topic penuh, atau None jika bukan topic kontrak."""
    p = prefix(project_id)
    if not full_topic.startswith(p):
        return None
    suffix = full_topic[len(p):]
    for key, (s, _, _) in TOPICS.items():
        if s == suffix:
            return key
    return None


@dataclass
class Validation:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    data: Any = None


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _check_fields(obj: dict, spec: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    for name, check in spec.items():
        if name not in obj:
            errors.append(f"field '{name}' hilang")
        else:
            msg = check(obj[name])
            if msg:
                errors.append(f"field '{name}': {msg} (nilai: {obj[name]!r})")
    for extra in obj:
        if extra not in spec:
            warnings.append(f"field tambahan '{extra}' tidak ada di kontrak")


def _num(lo: float | None = None, hi: float | None = None):
    def f(v):
        if not _is_num(v):
            return "harus angka"
        if lo is not None and v < lo:
            return f"harus >= {lo}"
        if hi is not None and v > hi:
            return f"harus <= {hi}"
        return None
    return f


def _int(lo: int = 0, hi: int | None = None):
    def f(v):
        if not _is_int(v):
            return "harus bilangan bulat"
        if v < lo:
            return f"harus >= {lo}"
        if hi is not None and v > hi:
            return f"harus <= {hi}"
        return None
    return f


def _bool(v):
    return None if isinstance(v, bool) else "harus boolean true/false"


def _enum(*allowed):
    def f(v):
        return None if (isinstance(v, str) and v in allowed) else f"harus salah satu dari {list(allowed)}"
    return f


def _str(v):
    return None if isinstance(v, str) and v else "harus string tidak kosong"


SPECS: dict[str, dict[str, Any]] = {
    "edge1_telemetry": {
        "device_id": _enum("edge1"),
        "seq": _int(0),
        "level_cm": _num(),
        "rate_cm_min": _num(),
        "sensor_ok": _bool,
        "uptime_ms": _int(0),
    },
    "edge2_telemetry": {
        "device_id": _enum("edge2"),
        "seq": _int(0),
        "rain_mm_h": _num(0, 80),
        "temp_c": _num(-40, 80),
        "hum_pct": _num(0, 100),
        "pump": _enum("ON", "OFF"),
        "siren": _bool,
        "mode": _enum("AUTO", "MANUAL"),
        "uptime_ms": _int(0),
    },
    "ai_prediction": {
        "level_now": _num(),
        "level_30m": _num(),
        "status": _enum(*STATUSES),
        "reason": _str,
        "seq": _int(0),
    },
    "edge2_commands": {
        "pump": _enum("ON", "OFF"),
        "siren": _bool,
        "mode": _enum("AUTO", "MANUAL"),
        "source": _enum("ai", "dashboard"),
    },
}


def validate_payload(key: str, raw: bytes | str) -> Validation:
    """Validasi ringan payload untuk key topic kontrak. JSON invalid ditolak dengan pesan jelas."""
    if key not in TOPICS:
        return Validation(False, [f"key topic tidak dikenal: {key}"])
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            return Validation(False, [f"payload bukan UTF-8 yang valid: {e}"])
    else:
        text = raw

    if key in ("edge1_status", "edge2_status"):
        t = text.strip()
        if t in ("online", "offline"):
            return Validation(True, data=t)
        return Validation(False, [f"status harus teks 'online' atau 'offline' (nilai: {text!r})"])

    if not text.strip():
        return Validation(False, ["payload kosong"])
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        return Validation(False, [f"JSON tidak valid: {e.msg} (baris {e.lineno}, kolom {e.colno})"])
    if not isinstance(obj, dict):
        return Validation(False, [f"JSON harus objek, bukan {type(obj).__name__}"])

    errors: list[str] = []
    warnings: list[str] = []
    _check_fields(obj, SPECS[key], errors, warnings)
    return Validation(not errors, errors, warnings, obj)


def build_command(pump: str, siren: bool, mode: str, source: str) -> dict:
    """Bangun payload command (PRD §9.4). Melempar ValueError jika tidak valid."""
    obj = {"pump": pump, "siren": siren, "mode": mode, "source": source}
    v = validate_payload("edge2_commands", json.dumps(obj))
    if not v.ok:
        raise ValueError("; ".join(v.errors))
    return obj


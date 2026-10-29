"""Validasi fondasi SiagaRob (Task 01).

Jalankan dari root repo: python scripts/validate_foundation.py
Memeriksa: AOI (struktur + identik byte-per-byte dengan sumber PRD), contoh payload
vs kontrak PRD, dan tidak ada file .env di repo.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        errors.append(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- AOI ---
aoi = ROOT / "data/geo/aoi_semarang_pilot.geojson"
src = ROOT / "docs/prd/aoi_semarang_pilot.geojson"
check(aoi.exists(), "AOI ada di data/geo/")
d = json.loads(aoi.read_text(encoding="utf-8"))
check(d.get("type") == "FeatureCollection", "AOI FeatureCollection")
check(len(d["features"]) == 1, "AOI tepat 1 feature")
f = d["features"][0]
check(f["geometry"]["type"] == "Polygon", "AOI geometri Polygon")
ring = f["geometry"]["coordinates"][0]
check(ring[0] == ring[-1], "ring tertutup")
check(all(-180 <= x <= 180 and -90 <= y <= 90 for x, y in ring), "koordinat lon/lat WGS84 valid")
p = f["properties"]
check(p["nama"] == "AOI Pilot Pasang Surut", "properti nama")
check(p["wilayah"] == "Semarang Utara dan Semarang Timur", "properti wilayah")
check("Tanjungmas" in p["kelurahan_target"], "properti kelurahan_target")
check(p["verifikasi_batas"]["luas_aoi_km2"] == 98.4, "luas 98,4 km2")
check(sha(aoi) == sha(src), "data/geo identik dengan sumber PRD (sha256)")
pub = ROOT / "dashboard/public/geo/aoi_semarang_pilot.geojson"
check(pub.exists() and sha(pub) == sha(aoi), "salinan dashboard/public/geo identik")

# --- Payload ---
ex = ROOT / "docs/examples"
e1 = json.loads((ex / "edge1_telemetry.json").read_text())
check(e1 == {"device_id": "edge1", "seq": 42, "level_cm": 82.4, "rate_cm_min": 1.8, "sensor_ok": True, "uptime_ms": 84000}, "edge1 payload = PRD 9.1")
e2 = json.loads((ex / "edge2_telemetry.json").read_text())
check(e2 == {"device_id": "edge2", "seq": 40, "rain_mm_h": 24.0, "temp_c": 27.5, "hum_pct": 91, "pump": "ON", "siren": False, "mode": "AUTO", "uptime_ms": 80000}, "edge2 payload = PRD 9.2")
pr = json.loads((ex / "ai_prediction.json").read_text())
check(pr == {"level_now": 82.4, "level_30m": 118.2, "status": "SIAGA_2", "reason": "model+rule", "seq": 42}, "prediction payload = PRD 9.3")
cmd = json.loads((ex / "edge2_command_ai.json").read_text())
check(cmd == {"pump": "ON", "siren": False, "mode": "AUTO", "source": "ai"}, "command payload = PRD 9.4")
cd = json.loads((ex / "edge2_command_dashboard.json").read_text())
check(cd["source"] == "dashboard" and cd["mode"] == "MANUAL", "command dashboard MANUAL")
check((ex / "edge_status_online.json").read_text().strip() == "online" and (ex / "edge_status_offline.json").read_text().strip() == "offline", "status online/offline")

# --- Kontrak topic: docs/CONTRACT.md dan contract.ts memuat semua suffix ---
suffixes = ["edge/edge1/telemetry", "edge/edge2/telemetry", "edge/edge1/status", "edge/edge2/status", "ai/prediction", "edge/edge2/commands"]
ts = (ROOT / "dashboard/src/lib/contract.ts").read_text(encoding="utf-8")
md = (ROOT / "docs/CONTRACT.md").read_text(encoding="utf-8")
check(all(s in ts for s in suffixes), "contract.ts memuat 6 topic")
check(all(s in md for s in suffixes), "CONTRACT.md memuat 6 topic")

# --- Secret ---
env_files = [x for x in ROOT.rglob(".env*") if "node_modules" not in x.parts and x.name != ".env.example"]
check(not env_files, "tidak ada file .env (hanya .env.example)")
ex_env = (ROOT / ".env.example").read_text()
check(not re.search(r"(?i)(password|secret|token|api_?key)\s*=\s*\S", ex_env), ".env.example tanpa secret")

print("\nGAGAL: %d" % len(errors) if errors else "\nSEMUA LULUS")
sys.exit(1 if errors else 0)


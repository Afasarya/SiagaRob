import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from starlette.testclient import TestClient

from app.cache import SimpleCache
from app.adapters.bmkg import parse_bmkg_payload, fetch_bmkg_forecast
from app.adapters.pantaubanjir import get_pantaubanjir_status
from app.adapters.big_tides import get_big_tides_status
from app.main import app

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "bmkg_sample.json"


@pytest.fixture
def sample_json():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ==========================================
# 1. Uji Parser BMKG
# ==========================================
def test_parse_bmkg_payload(sample_json):
    parsed = parse_bmkg_payload(sample_json)
    assert "Bandarharjo" in parsed["location_name"]
    assert "Semarang Utara" in parsed["location_name"]
    assert parsed["adm4"] == "33.74.02.1001"

    current = parsed["current"]
    assert current is not None
    assert current["temp_c"] == 28
    assert current["humidity_pct"] == 83
    assert current["rain_forecast_mm"] == 2.7
    assert current["weather_desc"] == "Hujan Ringan"
    assert current["icon_url"].endswith(".svg")

    assert len(parsed["hourly_series"]) == 2


# ==========================================
# 2. Uji Adapter BMKG dengan Fixture
# ==========================================
@pytest.mark.asyncio
async def test_fetch_bmkg_forecast_offline_fixture(sample_json):
    cache = SimpleCache()
    rec = await fetch_bmkg_forecast(cache=cache, offline_json=sample_json)

    assert rec.source == "BMKG Data Terbuka"
    assert rec.source_type == "official"
    assert rec.status == "LIVE"
    assert rec.category == "FORECAST"
    assert "Bandarharjo" in rec.location
    assert rec.attribution.startswith("Data Terbuka BMKG")
    assert "prakiraan cuaca regional" in rec.notes


# ==========================================
# 3. Uji Caching & Fallback STALE/UNAVAILABLE
# ==========================================
def test_simple_cache_ttl():
    cache = SimpleCache()
    cache.set("key1", "val1", ttl_seconds=100)
    item = cache.get("key1")
    assert item is not None
    assert item.value == "val1"
    assert not item.is_expired

    # Expired item
    cache.set("key2", "val2", ttl_seconds=-1)
    assert cache.get("key2").is_expired


@pytest.mark.asyncio
async def test_bmkg_fallback_stale_and_unavailable(sample_json):
    cache = SimpleCache()

    # Injeksi cache awal yang kedaluwarsa
    rec_init = await fetch_bmkg_forecast(cache=cache, offline_json=sample_json)
    cache.set("bmkg_forecast_33.74.02.1001", rec_init, ttl_seconds=-1)

    # Buat dummy client yang selalu raise ConnectionError
    class FailingClient:
        async def get(self, url):
            raise ConnectionError("Network unreachable")

        async def aclose(self):
            pass

    # Harus fallback ke STALE
    rec_stale = await fetch_bmkg_forecast(cache=cache, client=FailingClient())
    assert rec_stale.status == "STALE"
    assert "cache" in rec_stale.notes

    # Jika cache kosong total -> UNAVAILABLE
    cache.clear()
    rec_unavail = await fetch_bmkg_forecast(cache=cache, client=FailingClient())
    assert rec_unavail.status == "UNAVAILABLE"
    assert rec_unavail.stale_after_seconds == 0


# ==========================================
# 4. Uji Adapter PantauBanjir & BIG (UNAVAILABLE)
# ==========================================
def test_pantaubanjir_adapter_status():
    rec = get_pantaubanjir_status()
    assert rec.source == "PantauBanjir Semarang"
    assert rec.status == "UNAVAILABLE"
    assert rec.category == "WATER_LEVEL"
    assert "pantaubanjir.semarangkota.go.id" in rec.source_url
    assert "Scraping dilarang" in rec.notes


def test_big_tides_adapter_status():
    rec = get_big_tides_status()
    assert rec.source == "BIG / SRGI Pasang Surut Semarang"
    assert rec.status == "UNAVAILABLE"
    assert rec.category == "TIDES"
    assert "srgi.big.go.id" in rec.source_url


# ==========================================
# 5. Uji Endpoint FastAPI
# ==========================================
def test_fastapi_endpoints():
    client = TestClient(app)

    # Health check
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    # All external data bundle
    resp_bundle = client.get("/api/external-data")
    assert resp_bundle.status_code == 200
    data = resp_bundle.json()
    assert "records" in data
    assert len(data["records"]) == 3

    sources = [r["source"] for r in data["records"]]
    assert "BMKG Data Terbuka" in sources
    assert "PantauBanjir Semarang" in sources
    assert "BIG / SRGI Pasang Surut Semarang" in sources

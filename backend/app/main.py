"""Aplikasi FastAPI Backend Adapter Sumber Data Eksternal SiagaRob (Port 8000).

Satu-satunya backend adapter resmi sesuai PRD §8 (tidak menggunakan Flask).
Menangani caching, normalisasi, kesegaran data (freshness), CORS, dan fallback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.big_tides import get_big_tides_status
from .adapters.bmkg import fetch_bmkg_forecast
from .adapters.pantaubanjir import get_pantaubanjir_status
from .cache import SimpleCache
from .models import ExternalDataBundle, ExternalDataRecord

app = FastAPI(
    title="SiagaRob External Data Adapter",
    description="Adapter sumber eksternal resmi (BMKG, PantauBanjir, BIG) dengan metadata provenance dan status kesegaran.",
    version="1.0.0",
)

# Konfigurasi CORS agar Dashboard Next.js (port 3000) dapat memanggil endpoint ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = SimpleCache()


@app.get("/")
def read_root():
    return {
        "service": "SiagaRob External Data Adapter",
        "status": "healthy",
        "docs": "/docs",
        "endpoint": "/api/external-data",
    }


@app.get("/api/external-data", response_model=ExternalDataBundle)
async def get_all_external_data():
    """Mengambil semua sumber eksternal (BMKG live/cache, PantauBanjir, BIG)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    bmkg_record = await fetch_bmkg_forecast(cache=cache)
    pantaubanjir_record = get_pantaubanjir_status()
    big_record = get_big_tides_status()

    records: list[ExternalDataRecord] = [
        bmkg_record,
        pantaubanjir_record,
        big_record,
    ]
    return ExternalDataBundle(timestamp=now_iso, records=records)


@app.get("/api/external-data/bmkg", response_model=ExternalDataRecord)
async def get_bmkg():
    """Endpoint spesifik untuk data cuaca dan prakiraan BMKG."""
    return await fetch_bmkg_forecast(cache=cache)


@app.get("/api/external-data/pantaubanjir", response_model=ExternalDataRecord)
def get_pantaubanjir():
    """Endpoint spesifik status PantauBanjir Kota Semarang."""
    return get_pantaubanjir_status()


@app.get("/api/external-data/big-tides", response_model=ExternalDataRecord)
def get_big():
    """Endpoint spesifik status pasang surut BIG / SRGI."""
    return get_big_tides_status()


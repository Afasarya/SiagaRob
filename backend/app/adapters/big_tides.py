"""Adapter Pasang Surut BIG / SRGI Stasiun Semarang (PRD §2.2).

Dokumentasi: https://srgi.big.go.id/tides/smrg
Catatan audit: Halaman stasiun tersedia secara publik di portal Badan Informasi Geospasial,
namun tidak ada endpoint REST API programatik publik yang stabil atau bebas token.
Sesuai aturan PRD §2.2, sistem tidak melakukan scraping atau menebak API.
Status: UNAVAILABLE dengan link ke portal stasiun resmi.
"""
from __future__ import annotations

from datetime import datetime, timezone
from ..models import ExternalDataRecord

PORTAL_URL = "https://srgi.big.go.id/tides/smrg"
ATTRIBUTION = "Badan Informasi Geospasial (BIG) - SRGI Pasang Surut"


def get_big_tides_status() -> ExternalDataRecord:
    now_iso = datetime.now(timezone.utc).isoformat()
    return ExternalDataRecord(
        source="BIG / SRGI Pasang Surut Semarang",
        source_type="official",
        status="UNAVAILABLE",
        category="TIDES",
        location="Stasiun Pasang Surut Pelabuhan Semarang",
        fetched_at=now_iso,
        stale_after_seconds=0,
        source_url=PORTAL_URL,
        attribution=ATTRIBUTION,
        notes="Tidak tersedia endpoint API publik programatik tanpa autentikasi khusus. Akses data aktual dan prediksi pasang surut dapat dilihat melalui portal resmi BIG SRGI.",
    )


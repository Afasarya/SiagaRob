"""Adapter PantauBanjir Kota Semarang (PRD §2.2).

Dokumentasi: https://pantaubanjir.semarangkota.go.id/
Catatan audit: Situs web Pemkot Semarang tidak menyediakan endpoint REST API publik
yang terdokumentasi dan stabil secara terbuka. Sesuai aturan PRD §2.2, sistem
TIDAK melakukan web-scraping agresif dan TIDAK mengarang data stasiun fiktif.
Status: UNAVAILABLE dengan link ke portal resmi.
"""
from __future__ import annotations

from datetime import datetime, timezone
from ..models import ExternalDataRecord

PORTAL_URL = "https://pantaubanjir.semarangkota.go.id/"
ATTRIBUTION = "Pemerintah Kota Semarang (Sistem Pantau Banjir)"


def get_pantaubanjir_status() -> ExternalDataRecord:
    now_iso = datetime.now(timezone.utc).isoformat()
    return ExternalDataRecord(
        source="PantauBanjir Semarang",
        source_type="official",
        status="UNAVAILABLE",
        category="WATER_LEVEL",
        location="Stasiun Pompa & Pintu Air Semarang",
        fetched_at=now_iso,
        stale_after_seconds=0,
        source_url=PORTAL_URL,
        attribution=ATTRIBUTION,
        notes="Tidak tersedia API publik terbuka yang terdokumentasi. Scraping dilarang oleh kebijakan PRD; silakan pantau langsung melalui portal resmi Pemkot Semarang.",
    )


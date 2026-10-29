"""Adapter data terbuka BMKG (Prakiraan Cuaca per Wilayah Administrasi).

Sumber: https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=33.74.02.1001
Lokasi: Semarang Utara, Kelurahan Bandarharjo (Wilayah Target AOI Pilot).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from ..cache import SimpleCache
from ..models import ExternalDataRecord

logger = logging.getLogger("bmkg_adapter")

BMKG_ADM4_SEMARANG_UTARA = "33.74.02.1001"
BMKG_API_URL = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={BMKG_ADM4_SEMARANG_UTARA}"
BMKG_PORTAL_URL = "https://data.bmkg.go.id/prakiraan-cuaca/"
BMKG_ATTRIBUTION = "Data Terbuka BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)"
CACHE_TTL_SECONDS = 1800  # 30 menit
REQUEST_TIMEOUT_SECONDS = 6.0


def parse_bmkg_payload(raw_json: dict) -> dict:
    """Normalisasi respons JSON BMKG ke bentuk yang ringkas dan bersih."""
    lokasi_meta = raw_json.get("lokasi", {})
    lokasi_str = f"{lokasi_meta.get('desa', 'Bandarharjo')}, {lokasi_meta.get('kecamatan', 'Semarang Utara')}, {lokasi_meta.get('kotkab', 'Kota Semarang')}"

    data_list = raw_json.get("data", [])
    cuaca_series = []
    current_forecast = None

    if data_list and isinstance(data_list, list):
        cuaca_groups = data_list[0].get("cuaca", [])
        # Gabungkan semua hari perkiraan
        all_forecasts = []
        for group in cuaca_groups:
            if isinstance(group, list):
                all_forecasts.extend(group)

        if all_forecasts:
            # Ambil prakiraan terdekat (elemen pertama)
            first = all_forecasts[0]
            current_forecast = {
                "datetime": first.get("datetime"),
                "local_datetime": first.get("local_datetime"),
                "temp_c": first.get("t"),
                "humidity_pct": first.get("hu"),
                "rain_forecast_mm": first.get("tp"),
                "weather_desc": first.get("weather_desc"),
                "wind_speed_kmh": first.get("ws"),
                "wind_dir": first.get("wd"),
                "icon_url": first.get("image"),
            }
            # Simpan 6 horizon ke depan untuk ringkasan
            for item in all_forecasts[:6]:
                cuaca_series.append({
                    "local_datetime": item.get("local_datetime"),
                    "temp_c": item.get("t"),
                    "rain_forecast_mm": item.get("tp"),
                    "weather_desc": item.get("weather_desc"),
                    "icon_url": item.get("image"),
                })

    analysis_date = None
    if all_forecasts and "analysis_date" in all_forecasts[0]:
        analysis_date = all_forecasts[0].get("analysis_date")

    return {
        "location_name": lokasi_str,
        "adm4": BMKG_ADM4_SEMARANG_UTARA,
        "analysis_date": analysis_date,
        "current": current_forecast,
        "hourly_series": cuaca_series,
    }


async def fetch_bmkg_forecast(
    cache: SimpleCache,
    client: Optional[httpx.AsyncClient] = None,
    offline_json: Optional[dict] = None,
) -> ExternalDataRecord:
    now_iso = datetime.now(timezone.utc).isoformat()
    cache_key = f"bmkg_forecast_{BMKG_ADM4_SEMARANG_UTARA}"

    # Jika mode pengujian offline dengan payload terinjeksi
    if offline_json is not None:
        parsed = parse_bmkg_payload(offline_json)
        return ExternalDataRecord(
            source="BMKG Data Terbuka",
            source_type="official",
            status="LIVE",
            category="FORECAST",
            location=parsed["location_name"],
            issued_at=parsed["analysis_date"],
            fetched_at=now_iso,
            stale_after_seconds=CACHE_TTL_SECONDS,
            unit="mm (prakiraan hujan per periode), °C, %",
            data=parsed,
            source_url=BMKG_PORTAL_URL,
            attribution=BMKG_ATTRIBUTION,
            notes="Data diperoleh dari API Prakiraan Cuaca Terbuka BMKG. Ini adalah prakiraan cuaca regional, bukan pengukuran hujan lokal terukur.",
        )

    # 1. Cek cache in-memory
    cached = cache.get(cache_key)
    if cached and not cached.is_expired:
        rec: ExternalDataRecord = cached.value
        return rec

    # 2. Ambil dari API BMKG langsung
    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
        should_close_client = True

    try:
        resp = await client.get(BMKG_API_URL)
        resp.raise_for_status()
        raw_json = resp.json()
        parsed = parse_bmkg_payload(raw_json)

        record = ExternalDataRecord(
            source="BMKG Data Terbuka",
            source_type="official",
            status="LIVE",
            category="FORECAST",
            location=parsed["location_name"],
            issued_at=parsed["analysis_date"],
            fetched_at=now_iso,
            stale_after_seconds=CACHE_TTL_SECONDS,
            unit="mm (prakiraan hujan per periode), °C, %",
            data=parsed,
            source_url=BMKG_PORTAL_URL,
            attribution=BMKG_ATTRIBUTION,
            notes="Data diperoleh dari API Prakiraan Cuaca Terbuka BMKG. Ini adalah prakiraan cuaca regional, bukan pengukuran hujan lokal terukur.",
        )
        cache.set(cache_key, record, ttl_seconds=CACHE_TTL_SECONDS)
        return record

    except Exception as exc:
        logger.warning("Gagal mengambil data BMKG: %s", exc)
        # Fallback ke cache kadaluwarsa (STALE) bila ada
        if cached is not None:
            stale_rec: ExternalDataRecord = cached.value.model_copy(
                update={
                    "status": "STALE",
                    "notes": f"Penyedia tidak merespons ({exc}). Menampilkan data riwayat dalam cache (usia {cached.age_seconds}s).",
                }
            )
            return stale_rec

        # Fallback bila tidak ada cache sama sekali (UNAVAILABLE)
        return ExternalDataRecord(
            source="BMKG Data Terbuka",
            source_type="official",
            status="UNAVAILABLE",
            category="FORECAST",
            location="Semarang Utara (Kel. Bandarharjo)",
            fetched_at=now_iso,
            stale_after_seconds=0,
            source_url=BMKG_PORTAL_URL,
            attribution=BMKG_ATTRIBUTION,
            notes=f"API BMKG saat ini tidak dapat diakses ({type(exc).__name__}). Tidak mengarang data contoh.",
        )
    finally:
        if should_close_client:
            await client.aclose()


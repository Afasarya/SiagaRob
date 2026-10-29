"""Model data eksternal sesuai standar metadata PRD Induk §3."""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

SourceType = Literal["official", "iot_simulated", "derived", "model_prediction", "demo"]
DataStatus = Literal["LIVE", "STALE", "UNAVAILABLE"]
DataCategory = Literal["FORECAST", "TIDES", "WATER_LEVEL", "WARNING", "BASEMAP"]


class ExternalDataRecord(BaseModel):
    source: str = Field(..., description="Nama resmi penyedia data")
    source_type: SourceType = Field("official", description="Tipe sumber data")
    status: DataStatus = Field(..., description="Status kesegaran data")
    category: DataCategory = Field(..., description="Kategori data (e.g. FORECAST, TIDES)")
    location: str = Field(..., description="Nama wilayah / stasiun / AOI")
    issued_at: Optional[str] = Field(None, description="Waktu rilis dari sumber (ISO 8601)")
    observed_at: Optional[str] = Field(None, description="Waktu observasi bila tersedia")
    fetched_at: str = Field(..., description="Waktu adapter mengambil data (ISO 8601)")
    stale_after_seconds: int = Field(..., description="Masa berlaku cache dalam detik")
    unit: Optional[str] = Field(None, description="Satuan nilai utama")
    data: Optional[Any] = Field(None, description="Isi data normalisasi")
    source_url: str = Field(..., description="Tautan dokumentasi / portal resmi")
    attribution: str = Field(..., description="Teks atribusi hak cipta penyedia data")
    notes: Optional[str] = Field(None, description="Catatan teknis / alasan jika UNAVAILABLE")


class ExternalDataBundle(BaseModel):
    timestamp: str
    records: list[ExternalDataRecord]


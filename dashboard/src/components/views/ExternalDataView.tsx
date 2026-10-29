"use client";

import React, { useEffect, useState } from "react";
import {
  ExternalLink,
  Database,
  RefreshCw,
  AlertTriangle,
  CloudSun,
} from "lucide-react";

export interface ExternalRecord {
  source: string;
  source_type: "official" | "iot_simulated" | "derived" | "model_prediction" | "demo";
  status: "LIVE" | "STALE" | "UNAVAILABLE";
  category: "FORECAST" | "TIDES" | "WATER_LEVEL" | "WARNING" | "BASEMAP";
  location: string;
  issued_at?: string;
  observed_at?: string;
  fetched_at: string;
  stale_after_seconds: number;
  unit?: string;
  data?: Record<string, unknown> | null;
  source_url: string;
  attribution: string;
  notes?: string;
}

export interface ExternalBundle {
  timestamp: string;
  records: ExternalRecord[];
}

const ADAPTER_URL = process.env.NEXT_PUBLIC_ADAPTER_URL || "http://localhost:8000";

const statusBadges = {
  LIVE: "bg-emerald-50 text-emerald-700 border-emerald-200",
  STALE: "bg-yellow-50 text-yellow-800 border-yellow-200",
  UNAVAILABLE: "bg-neutral-100 text-neutral-600 border-neutral-200",
};

export function ExternalDataView() {
  const [bundle, setBundle] = useState<ExternalBundle | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    let isMounted = true;

    fetch(`${ADAPTER_URL}/api/external-data`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: Gagal memuat data dari adapter FastAPI`);
        }
        return res.json();
      })
      .then((data: ExternalBundle) => {
        if (isMounted) {
          setBundle(data);
          setErrorMsg(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.warn("FastAPI adapter offline:", err);
          setErrorMsg(
            "Backend adapter FastAPI (port 8000) belum terhubung atau offline. Jalankan: uvicorn app.main:app --app-dir backend --port 8000"
          );
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [refreshKey]);

  const handleRefresh = () => {
    setLoading(true);
    setRefreshKey((prev) => prev + 1);
  };

  // Fallback records jika backend FastAPI belum menyala
  const displayRecords: ExternalRecord[] = bundle?.records || [
    {
      source: "BMKG Data Terbuka",
      source_type: "official",
      status: "UNAVAILABLE",
      category: "FORECAST",
      location: "Semarang Utara (Kel. Bandarharjo)",
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 0,
      source_url: "https://data.bmkg.go.id/prakiraan-cuaca/",
      attribution: "Data Terbuka BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)",
      notes: "Menunggu koneksi backend FastAPI adapter (port 8000). Data live belum dapat dimuat.",
    },
    {
      source: "PantauBanjir Semarang",
      source_type: "official",
      status: "UNAVAILABLE",
      category: "WATER_LEVEL",
      location: "Stasiun Pompa & Pintu Air Semarang",
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 0,
      source_url: "https://pantaubanjir.semarangkota.go.id/",
      attribution: "Pemerintah Kota Semarang (Sistem Pantau Banjir)",
      notes: "Tidak tersedia API publik terbuka yang stabil. Akses melalui portal resmi.",
    },
    {
      source: "BIG / SRGI Pasang Surut Semarang",
      source_type: "official",
      status: "UNAVAILABLE",
      category: "TIDES",
      location: "Stasiun Pasang Surut Pelabuhan Semarang",
      fetched_at: new Date().toISOString(),
      stale_after_seconds: 0,
      source_url: "https://srgi.big.go.id/tides/smrg",
      attribution: "Badan Informasi Geospasial (BIG) - SRGI Pasang Surut",
      notes: "Tidak tersedia API publik programatik tanpa autentikasi khusus.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900">
                Panel Sumber Data Resmi Publik (FastAPI Adapter Port 8000)
              </h3>
              <p className="text-xs text-neutral-500">
                Provenance, Atribusi, Waktu Pengambilan, dan Status Kesegaran (PRD §2 & §3)
              </p>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-neutral-200 bg-neutral-50 hover:bg-neutral-100 text-neutral-700 text-xs font-medium transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-amber-600" : ""}`} />
            <span>Segarkan</span>
          </button>
        </div>

        <p className="text-xs text-neutral-600 leading-relaxed">
          Semua sumber eksternal dinormalisasi melalui backend FastAPI untuk menangani pembatasan CORS, caching, dan status kesegaran (<code>LIVE</code>, <code>STALE</code>, <code>UNAVAILABLE</code>).
          Prakiraan cuaca BMKG secara ketat diberi label <strong>FORECAST</strong> (bukan pengukuran curah hujan lokal terukur).
        </p>

        {errorMsg && (
          <div className="p-3 bg-amber-50/80 border border-amber-200/90 rounded-xl text-xs text-amber-900 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Kartu-kartu Sumber Data */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {displayRecords.map((rec) => {
          const bmkgData = (rec.category === "FORECAST" && rec.status === "LIVE" ? rec.data : null) as Record<string, unknown> | null;
          const currentForecast = bmkgData?.current as Record<string, unknown> | undefined;

          return (
            <div
              key={rec.source}
              className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded uppercase tracking-wider bg-neutral-100 text-neutral-700 border border-neutral-200">
                    {rec.category}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border tracking-wider ${
                      statusBadges[rec.status] || statusBadges.UNAVAILABLE
                    }`}
                  >
                    {rec.status}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-neutral-900">{rec.source}</h4>
                  <p className="text-xs text-neutral-500 mt-0.5">{rec.location}</p>
                </div>

                {/* Khusus jika data BMKG LIVE berhasil diambil */}
                {currentForecast && (
                  <div className="p-3.5 bg-neutral-50 rounded-xl border border-neutral-100 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {currentForecast.icon_url ? (
                          /* eslint-disable-next-line @next/next/no-img-element */
                          <img
                            src={String(currentForecast.icon_url)}
                            alt="BMKG Weather"
                            className="w-8 h-8 shrink-0 object-contain"
                          />
                        ) : (
                          <CloudSun className="w-6 h-6 text-amber-500" />
                        )}
                        <div>
                          <div className="text-xs font-semibold text-neutral-800">
                            {String(currentForecast.weather_desc || "Cerah")}
                          </div>
                          <div className="text-[11px] text-neutral-500">
                            Prakiraan Terdekat
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-neutral-900">
                          {String(currentForecast.temp_c)}°C
                        </div>
                        <div className="text-[10px] text-neutral-400">
                          RH: {String(currentForecast.humidity_pct)}%
                        </div>
                      </div>
                    </div>
                    <div className="text-[11px] text-neutral-600 pt-1.5 border-t border-neutral-200/60 flex justify-between">
                      <span>Prakiraan Presipitasi:</span>
                      <span className="font-semibold">{String(currentForecast.rain_forecast_mm)} mm</span>
                    </div>
                  </div>
                )}

                {/* Catatan / Keterangan Sumber */}
                {rec.notes && (
                  <p className="text-[11px] text-neutral-500 leading-relaxed italic bg-neutral-50/60 p-2.5 rounded-lg border border-neutral-100">
                    {rec.notes}
                  </p>
                )}
              </div>

              {/* Atribusi & Tautan */}
              <div className="pt-3 border-t border-neutral-100 space-y-2 text-[10px] text-neutral-400">
                <div className="truncate">
                  <strong>Atribusi:</strong> {rec.attribution}
                </div>
                <div className="flex items-center justify-between">
                  <span className="truncate">
                    Diambil: {rec.fetched_at ? new Date(rec.fetched_at).toLocaleTimeString("id-ID") : "-"}
                  </span>
                  <a
                    href={rec.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-amber-600 font-medium hover:underline shrink-0 ml-2"
                  >
                    <span>Portal Resmi</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, Tooltip, useMap } from "react-leaflet";
import type { FeatureCollection } from "geojson";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { AlertTriangle, Layers, Info } from "lucide-react";
import type { DeviceState } from "@/hooks/useMqttLive";
import type { Edge1Telemetry, Edge2Telemetry } from "@/lib/contract";

// Helper untuk fitBounds ke layer GeoJSON
function AutoFitBounds({ data }: { data: FeatureCollection }) {
  const map = useMap();
  useEffect(() => {
    if (data && data.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(data);
        const bounds = geoJsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [30, 30] });
        }
      } catch (err) {
        console.error("Gagal fit bounds:", err);
      }
    }
  }, [data, map]);
  return null;
}

interface MapClientProps {
  height?: string;
  showDetails?: boolean;
  edge1State?: DeviceState<Edge1Telemetry>;
  edge2State?: DeviceState<Edge2Telemetry>;
}

// Koordinat Pos Stasiun IoT Virtual
const EDGE1_COORDS: [number, number] = [-6.9545, 110.4285]; // Muara Pelabuhan Tanjung Mas
const EDGE2_COORDS: [number, number] = [-6.9482, 110.4392]; // Polder Tambak Lorok

export default function MapClient({
  height = "480px",
  showDetails = true,
  edge1State,
  edge2State,
}: MapClientProps) {
  const [geoData, setGeoData] = useState<FeatureCollection | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const e1 = edge1State?.data;
  const e2 = edge2State?.data;

  useEffect(() => {
    let isMounted = true;
    fetch("/geo/aoi_semarang_pilot.geojson")
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Gagal memuat GeoJSON (HTTP ${res.status})`);
        }
        return res.json();
      })
      .then((data: FeatureCollection) => {
        if (isMounted) {
          setGeoData(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error("Gagal mengambil file GeoJSON:", err);
          setError("Gagal memuat batas AOI GeoJSON. Periksa ketersediaan file di public/geo.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const defaultCenter: [number, number] = [-6.96, 110.44];

  return (
    <div className="relative w-full rounded-2xl overflow-hidden border border-neutral-200 bg-neutral-100 shadow-sm flex flex-col">
      {/* Fallback Banner jika GeoJSON Error */}
      {error && (
        <div className="p-3 bg-red-50 border-b border-red-200 text-red-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Kontainer Leaflet */}
      <div style={{ height }} className="w-full relative z-0">
        <MapContainer
          center={defaultCenter}
          zoom={12}
          scrollWheelZoom={true}
          style={{ height: "100%", width: "100%" }}
          className="z-0"
        >
          {/* Basemap Nyata OpenStreetMap */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />

          {/* Render Batas Poligon AOI Pilot yang Dibekukan */}
          {geoData && (
            <>
              <GeoJSON
                data={geoData}
                style={{
                  color: "#d97706",
                  weight: 2.5,
                  opacity: 0.9,
                  fillColor: "#f59e0b",
                  fillOpacity: 0.12,
                  dashArray: "4, 4",
                }}
                onEachFeature={(feature, layer) => {
                  const props = feature.properties || {};
                  layer.bindPopup(`
                    <div style="font-family: sans-serif; font-size: 12px; line-height: 1.4;">
                      <strong style="color: #92400e; font-size: 13px;">${props.nama || "AOI Pasang Surut"}</strong>
                      <p style="margin: 4px 0 2px; color: #4b5563;"><strong>Wilayah:</strong> ${props.wilayah || "Semarang Utara & Timur"}</p>
                      <p style="margin: 2px 0; color: #4b5563;"><strong>Kelurahan Sasaran:</strong> ${props.kelurahan_target || "-"}</p>
                      <p style="margin: 2px 0; color: #4b5563;"><strong>Luas Wilayah:</strong> ${props.verifikasi_batas?.luas_aoi_km2 || 98.4} km²</p>
                      <div style="margin-top: 6px; padding: 4px; background: #fef3c7; border-radius: 4px; color: #78350f; font-size: 10px;">
                        Status: Geometri Dibekukan (2026-08-24). Bukan klaim semua area tergenang.
                      </div>
                    </div>
                  `);
                }}
              />
              <AutoFitBounds data={geoData} />
            </>
          )}

          {/* Marker Real-Time: Edge 1 Pos Air Pelabuhan */}
          <CircleMarker
            center={EDGE1_COORDS}
            radius={9}
            pathOptions={{
              color: "#1d4ed8",
              fillColor: "#3b82f6",
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
              <div className="font-sans text-xs">
                <strong>Edge 1 (Pos Air):</strong> {e1 ? `${e1.level_cm.toFixed(1)} cm` : "Offline"}
              </div>
            </Tooltip>
            <Popup>
              <div style={{ fontFamily: "sans-serif", fontSize: "12px", minWidth: "170px" }}>
                <strong style={{ color: "#1d4ed8", fontSize: "13px" }}>Edge 1 — Pos Pantau Air</strong>
                <p style={{ margin: "4px 0 2px", color: "#64748b" }}>Pelabuhan Tanjung Mas</p>
                <div style={{ margin: "6px 0", padding: "6px", background: "#eff6ff", borderRadius: "6px" }}>
                  <div>Status: <strong>{edge1State?.status || "OFFLINE"}</strong></div>
                  <div>Tinggi Air: <strong>{e1 ? `${e1.level_cm.toFixed(1)} cm` : "--"}</strong></div>
                  <div>Laju: <strong>{e1 ? `${e1.rate_cm_min.toFixed(2)} cm/m` : "--"}</strong></div>
                  <div>Sensor: <strong>{e1?.sensor_ok ? "Normal" : "Error"}</strong></div>
                </div>
              </div>
            </Popup>
          </CircleMarker>

          {/* Marker Real-Time: Edge 2 Pos Hujan & Rumah Pompa */}
          <CircleMarker
            center={EDGE2_COORDS}
            radius={9}
            pathOptions={{
              color: "#b45309",
              fillColor: "#f59e0b",
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -8]} opacity={0.95}>
              <div className="font-sans text-xs">
                <strong>Edge 2 (Hujan & Pompa):</strong> {e2 ? `${e2.rain_mm_h.toFixed(1)} mm/h` : "Offline"}
              </div>
            </Tooltip>
            <Popup>
              <div style={{ fontFamily: "sans-serif", fontSize: "12px", minWidth: "170px" }}>
                <strong style={{ color: "#b45309", fontSize: "13px" }}>Edge 2 — Pos Cuaca & Rumah Pompa</strong>
                <p style={{ margin: "4px 0 2px", color: "#64748b" }}>Polder Tambak Lorok</p>
                <div style={{ margin: "6px 0", padding: "6px", background: "#fffbeb", borderRadius: "6px" }}>
                  <div>Status: <strong>{edge2State?.status || "OFFLINE"}</strong></div>
                  <div>Curah Hujan: <strong>{e2 ? `${e2.rain_mm_h.toFixed(1)} mm/jam` : "--"}</strong></div>
                  <div>Pompa: <strong>{e2?.pump || "OFF"}</strong></div>
                  <div>Sirine: <strong>{e2?.siren ? "AKTIF" : "MATI"}</strong></div>
                  <div>Mode: <strong>{e2?.mode || "AUTO"}</strong></div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        </MapContainer>

        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-white/70 backdrop-blur-sm z-10 flex items-center justify-center gap-2 text-sm text-neutral-600 font-medium">
            <div className="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
            <span>Memuat data geografis AOI...</span>
          </div>
        )}

        {/* Legenda Peta (Floating Overlay) */}
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur-sm p-3.5 rounded-xl border border-neutral-200 shadow-md z-[1000] text-xs max-w-xs space-y-2">
          <div className="font-semibold text-neutral-800 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-amber-600" />
            <span>Legenda Layer Geografis</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-600">
            <span className="w-4 h-3.5 rounded border border-amber-600 bg-amber-500/20 inline-block shrink-0" />
            <span>Batas AOI Pilot Semarang (98,4 km²)</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-600">
            <span className="w-3 h-3 rounded-full bg-blue-500 border border-blue-700 inline-block shrink-0" />
            <span>Edge 1: Pos Pantau Air (Pelabuhan)</span>
          </div>
          <div className="flex items-center gap-2 text-neutral-600">
            <span className="w-3 h-3 rounded-full bg-amber-500 border border-amber-700 inline-block shrink-0" />
            <span>Edge 2: Pos Cuaca & Pompa (Tambak Lorok)</span>
          </div>
          <div className="text-[10px] text-neutral-400 border-t border-neutral-100 pt-1.5 flex items-start gap-1">
            <Info className="w-3 h-3 text-neutral-400 shrink-0 mt-0.5" />
            <span>Klik marker pos untuk melihat status real-time sensor & pompa.</span>
          </div>
        </div>
      </div>

      {/* Info Tambahan di bawah peta (Opsional) */}
      {showDetails && geoData?.features?.[0]?.properties && (
        <div className="p-4 bg-white border-t border-neutral-200 text-xs text-neutral-600 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <span className="text-neutral-400 block text-[11px]">Kelurahan Sasaran:</span>
            <span className="font-medium text-neutral-800">
              {geoData.features[0].properties.kelurahan_target || "Tanjungmas, Bandarharjo, Kemijen, dkk."}
            </span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[11px]">Luas AOI Pilot:</span>
            <span className="font-medium text-neutral-800">98,4 km² (Diperluas untuk routing memutar)</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[11px]">Status Batas:</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              Dibekukan (2026-08-24)
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React from "react";
import { MapView } from "../Map";
import { MapPin, Layers } from "lucide-react";
import type { DeviceState } from "@/hooks/useMqttLive";
import type { Edge1Telemetry, Edge2Telemetry } from "@/lib/contract";

interface MapRiskViewProps {
  edge1State?: DeviceState<Edge1Telemetry>;
  edge2State?: DeviceState<Edge2Telemetry>;
}

export function MapRiskView({ edge1State, edge2State }: MapRiskViewProps) {
  const e1 = edge1State?.data;
  const e2 = edge2State?.data;

  return (
    <div className="space-y-6">
      {/* Kartu Informasi AOI Geografis */}
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-700">
              <MapPin className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900">
                Area of Interest (AOI) Pilot Pasang Surut Semarang
              </h3>
              <p className="text-xs text-neutral-500">
                Batas poligon resmi: <code>data/geo/aoi_semarang_pilot.geojson</code>
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            Geometri Dibekukan (2026-08-24)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
          <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">Wilayah Target</span>
            <span className="text-xs font-semibold text-neutral-800 mt-0.5 block">Semarang Utara & Timur</span>
          </div>
          <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">Luas Poligon AOI</span>
            <span className="text-xs font-semibold text-neutral-800 mt-0.5 block">98,4 km² (~3,6x kelurahan)</span>
          </div>
          <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">Level Air Edge 1</span>
            <span className="text-xs font-bold text-blue-700 mt-0.5 block font-mono">
              {e1 ? `${e1.level_cm.toFixed(1)} cm` : "Offline"}
            </span>
          </div>
          <div className="p-3 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">Curah Hujan Edge 2</span>
            <span className="text-xs font-bold text-amber-700 mt-0.5 block font-mono">
              {e2 ? `${e2.rain_mm_h.toFixed(1)} mm/h` : "Offline"}
            </span>
          </div>
        </div>

        <div className="text-xs text-neutral-600 bg-amber-50/60 p-3.5 rounded-xl border border-amber-200/70 leading-relaxed">
          <strong>Mengapa AOI 98,4 km² lebih luas dari kelurahan sasaran (27,6 km²)?</strong>
          <br />
          Sesuai catatan PRD §6, kelebihan ini disengaja agar mesin routing darat memiliki ruang untuk mencari rute alternatif memutar ketika ruas jalan di pesisir tergenang air pasang rob. AOI bukan bukti bahwa semua wilayah di dalamnya berisiko banjir.
        </div>
      </div>

      {/* Peta Full-Height */}
      <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-neutral-500" />
            <h4 className="text-sm font-semibold text-neutral-800">Visualisasi Peta Leaflet + OSM Basemap</h4>
          </div>
          <span className="text-[11px] font-mono text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200">
            EPSG:4326 (WGS84)
          </span>
        </div>

        <MapView height="520px" showDetails={true} edge1State={edge1State} edge2State={edge2State} />
      </div>
    </div>
  );
}

"use client";

import React from "react";
import { OverviewMetricCards } from "../MetricCards";
import { MapView } from "../Map";
import { LiveCharts } from "../LiveCharts";
import { ShieldAlert, Radio, Activity, AlertTriangle } from "lucide-react";
import { topic } from "@/lib/contract";
import type { DeviceState, ChartPoint, ConnectionStatus } from "@/hooks/useMqttLive";
import type { Edge1Telemetry, Edge2Telemetry, AiPrediction } from "@/lib/contract";

interface OverviewViewProps {
  edge1State: DeviceState<Edge1Telemetry>;
  edge2State: DeviceState<Edge2Telemetry>;
  aiPrediction: DeviceState<AiPrediction>;
  chartData: ChartPoint[];
  connectionStatus: ConnectionStatus;
  connectionError?: string | null;
}

export function OverviewView({
  edge1State,
  edge2State,
  aiPrediction,
  chartData,
  connectionStatus,
  connectionError,
}: OverviewViewProps) {
  const e1 = edge1State.data;
  const e2 = edge2State.data;

  return (
    <div className="space-y-6">
      {/* Banner Disclaimer Prototipe PRD §1 */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 flex items-start gap-3.5">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-950 space-y-1">
          <p className="font-semibold text-sm text-amber-900">
            Prototipe Pemantauan Risiko Rob & Banjir — Area Pilot Semarang Utara & Timur
          </p>
          <p className="text-neutral-600 leading-relaxed">
            Sistem memvisualisasikan data telemetri IoT simulasi (ESP32 Wokwi), model prediksi AI eksperimental (+30m), dan batas geografis nyata OpenStreetMap.
            Bukan sistem keselamatan publik yang tervalidasi di lapangan.
          </p>
        </div>
      </div>

      {/* Peringatan jika koneksi error */}
      {connectionError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
          <span>Error koneksi MQTT WebSocket: {connectionError} (Memeriksa ulang sambungan...)</span>
        </div>
      )}

      {/* Kartu Ringkasan Metrik Live Reaktif */}
      <OverviewMetricCards
        edge1State={edge1State}
        edge2State={edge2State}
        aiPrediction={aiPrediction}
        connectionStatus={connectionStatus}
      />

      {/* Grafik Ketinggian Air Aktual vs Prediksi AI (Maks 60 Titik) */}
      <LiveCharts data={chartData} />

      {/* Peta Utama Area Pilot */}
      <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <h3 className="text-sm font-semibold text-neutral-800">
              Peta Geografis AOI Pilot Pasang Surut Semarang
            </h3>
          </div>
          <span className="text-[11px] font-mono text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200">
            EPSG:4326 (WGS84)
          </span>
        </div>

        {/* Dynamic Leaflet Map */}
        <MapView height="420px" showDetails={true} edge1State={edge1State} edge2State={edge2State} />
      </div>

      {/* Panel Status 2 Edge IoT Virtual & Kontrak MQTT */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Edge 1 Pos Air Card */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <h4 className="text-sm font-semibold text-neutral-800">Edge 1 — Pos Air Virtual</h4>
            </div>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                edge1State.status === "ONLINE"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : edge1State.status === "STALE"
                  ? "bg-yellow-50 text-yellow-800 border-yellow-200"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {edge1State.status}
            </span>
          </div>
          <p className="text-xs text-neutral-500 leading-relaxed">
            {e1 ? (
              <span>
                Level Terkini: <strong>{e1.level_cm.toFixed(1)} cm</strong> | Laju: <strong>{e1.rate_cm_min.toFixed(1)} cm/min</strong> | Sensor OK: <strong>{e1.sensor_ok ? "Ya" : "TIDAK (Error)"}</strong> | Seq: #{e1.seq}
              </span>
            ) : (
              "ESP32 + HC-SR04 (GPIO 5, 18). Menunggu paket telemetri pertama dari broker..."
            )}
          </p>
          <div className="text-[11px] font-mono bg-neutral-50 p-2 rounded border border-neutral-200/70 text-neutral-600 truncate">
            Topic: {topic("edge1Telemetry")}
          </div>
        </div>

        {/* Edge 2 Pos Hujan & Aktuator Card */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-amber-600" />
              <h4 className="text-sm font-semibold text-neutral-800">Edge 2 — Pos Hujan & Aktuator</h4>
            </div>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                edge2State.status === "ONLINE"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : edge2State.status === "STALE"
                  ? "bg-yellow-50 text-yellow-800 border-yellow-200"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {edge2State.status}
            </span>
          </div>
          <p className="text-xs text-neutral-500 leading-relaxed">
            {e2 ? (
              <span>
                Hujan: <strong>{e2.rain_mm_h.toFixed(1)} mm/h</strong> | Pompa: <strong>{e2.pump}</strong> | Sirine: <strong>{e2.siren ? "ON" : "OFF"}</strong> | Mode: <strong>{e2.mode}</strong> | Seq: #{e2.seq}
              </span>
            ) : (
              "ESP32 + DHT22 + Potensiometer + Relay & Buzzer. Menunggu paket telemetri..."
            )}
          </p>
          <div className="text-[11px] font-mono bg-neutral-50 p-2 rounded border border-neutral-200/70 text-neutral-600 truncate">
            Topic: {topic("edge2Telemetry")}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React from "react";
import { Activity, Radio, Waves, CloudRain, Thermometer, Droplets, Zap, Volume2, ShieldCheck, AlertTriangle } from "lucide-react";
import { topic } from "@/lib/contract";
import type { DeviceState, ChartPoint } from "@/hooks/useMqttLive";
import type { Edge1Telemetry, Edge2Telemetry } from "@/lib/contract";

interface TelemetryViewProps {
  edge1State: DeviceState<Edge1Telemetry>;
  edge2State: DeviceState<Edge2Telemetry>;
  chartData?: ChartPoint[];
}

export function TelemetryView({ edge1State, edge2State }: TelemetryViewProps) {
  const e1 = edge1State.data;
  const e2 = edge2State.data;

  const isE1Online = edge1State.status === "ONLINE";
  const isE2Online = edge2State.status === "ONLINE";

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-neutral-900">
            Telemetri Real-Time Perangkat IoT Virtual Wokwi
          </h3>
          <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            Live Stream Broker HiveMQ
          </span>
        </div>
        <p className="text-xs text-neutral-500 leading-relaxed">
          Menampilkan paket telemetri aktif dari dua perangkat virtual ESP32. Data disiarkan setiap interval siklus simulasi melalui protokol MQTT standar industri.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ================= EDGE 1: POS AIR ================= */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-neutral-900">Edge 1 — Pos Pantau Air</h4>
                <p className="text-[11px] text-neutral-500">Muara Pelabuhan Tanjung Mas (ESP32 + HC-SR04)</p>
              </div>
            </div>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                isE1Online
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : edge1State.status === "STALE"
                  ? "bg-yellow-50 text-yellow-800 border-yellow-200"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {edge1State.status}
            </span>
          </div>

          {/* Nilai Utama Level Air */}
          <div className="p-4 bg-gradient-to-br from-blue-50/50 to-neutral-50 rounded-xl border border-blue-100/60 flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wider block">
                Ketinggian Air Pasang / Rob
              </span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-bold font-mono text-neutral-900">
                  {e1 ? e1.level_cm.toFixed(1) : "--.-"}
                </span>
                <span className="text-sm font-medium text-neutral-500">cm</span>
              </div>
              <span className="text-xs text-neutral-500 mt-1 block">
                Laju perubahan:{" "}
                <strong className={e1 && e1.rate_cm_min > 0 ? "text-amber-600" : "text-neutral-700"}>
                  {e1 ? `${e1.rate_cm_min >= 0 ? "+" : ""}${e1.rate_cm_min.toFixed(2)} cm/menit` : "-"}
                </strong>
              </span>
            </div>
            <Waves className="w-12 h-12 text-blue-400/40" />
          </div>

          {/* Rincian Sensor & Paket */}
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Kondisi Sensor HC-SR04:</span>
              <span className={`font-semibold flex items-center gap-1 ${e1?.sensor_ok ? "text-emerald-600" : "text-red-600"}`}>
                {e1?.sensor_ok ? (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Normal (Valid)
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Error / Putus (Hold Value)
                  </>
                )}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Nomor Urut Paket (Seq):</span>
              <span className="font-mono text-neutral-800">#{e1?.seq ?? "-"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Uptime Perangkat:</span>
              <span className="font-mono text-neutral-800">
                {e1 ? `${(e1.uptime_ms / 1000).toFixed(1)} detik` : "-"}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Pembaruan Terakhir:</span>
              <span className="font-mono text-neutral-600">
                {edge1State.lastUpdated ? edge1State.lastUpdated.toLocaleTimeString("id-ID") : "Menunggu paket..."}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-neutral-500">Topik Telemetri:</span>
              <span className="font-mono text-[11px] text-amber-700 truncate max-w-[220px]">
                {topic("edge1Telemetry")}
              </span>
            </div>
          </div>

          {/* Raw Payload Preview */}
          <div className="pt-2">
            <span className="text-[11px] font-semibold text-neutral-400 block mb-1">RAW JSON PAYLOAD:</span>
            <pre className="p-3 bg-neutral-900 text-emerald-400 font-mono text-[11px] rounded-xl overflow-x-auto">
              {e1 ? JSON.stringify(e1, null, 2) : "// Menunggu paket telemetri pertama..."}
            </pre>
          </div>
        </div>

        {/* ================= EDGE 2: POS HUJAN & AKTUATOR ================= */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <Radio className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-neutral-900">Edge 2 — Pos Cuaca & Rumah Pompa</h4>
                <p className="text-[11px] text-neutral-500">Polder Tambak Lorok (ESP32 + DHT22 + Relay)</p>
              </div>
            </div>
            <span
              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                isE2Online
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : edge2State.status === "STALE"
                  ? "bg-yellow-50 text-yellow-800 border-yellow-200"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {edge2State.status}
            </span>
          </div>

          {/* Nilai Utama Curah Hujan & Lingkungan */}
          <div className="grid grid-cols-3 gap-2">
            <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100/60 text-center">
              <CloudRain className="w-5 h-5 text-blue-500 mx-auto mb-1" />
              <span className="text-[10px] font-semibold text-neutral-500 uppercase block">Curah Hujan</span>
              <span className="text-lg font-bold font-mono text-neutral-900 block mt-0.5">
                {e2 ? e2.rain_mm_h.toFixed(1) : "--.-"}
              </span>
              <span className="text-[10px] text-neutral-500">mm/jam</span>
            </div>

            <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-100/60 text-center">
              <Thermometer className="w-5 h-5 text-amber-500 mx-auto mb-1" />
              <span className="text-[10px] font-semibold text-neutral-500 uppercase block">Suhu Udara</span>
              <span className="text-lg font-bold font-mono text-neutral-900 block mt-0.5">
                {e2 ? e2.temp_c.toFixed(1) : "--.-"}
              </span>
              <span className="text-[10px] text-neutral-500">°C</span>
            </div>

            <div className="p-3 bg-emerald-50/50 rounded-xl border border-emerald-100/60 text-center">
              <Droplets className="w-5 h-5 text-emerald-500 mx-auto mb-1" />
              <span className="text-[10px] font-semibold text-neutral-500 uppercase block">Kelembapan</span>
              <span className="text-lg font-bold font-mono text-neutral-900 block mt-0.5">
                {e2 ? e2.hum_pct.toFixed(0) : "--"}
              </span>
              <span className="text-[10px] text-neutral-500">%</span>
            </div>
          </div>

          {/* Status Aktuator Fisik */}
          <div className="grid grid-cols-3 gap-2 pt-1">
            <div className="p-2.5 bg-neutral-50 rounded-xl border border-neutral-100 text-center">
              <span className="text-[10px] text-neutral-400 block uppercase">Pompa Air</span>
              <span className={`text-xs font-bold inline-flex items-center gap-1 mt-1 ${e2?.pump === "ON" ? "text-emerald-600" : "text-neutral-600"}`}>
                <Zap className="w-3 h-3" />
                {e2?.pump ?? "OFF"}
              </span>
            </div>
            <div className="p-2.5 bg-neutral-50 rounded-xl border border-neutral-100 text-center">
              <span className="text-[10px] text-neutral-400 block uppercase">Sirine Alarm</span>
              <span className={`text-xs font-bold inline-flex items-center gap-1 mt-1 ${e2?.siren ? "text-red-600" : "text-neutral-600"}`}>
                <Volume2 className="w-3 h-3" />
                {e2?.siren ? "AKTIF" : "MATI"}
              </span>
            </div>
            <div className="p-2.5 bg-neutral-50 rounded-xl border border-neutral-100 text-center">
              <span className="text-[10px] text-neutral-400 block uppercase">Mode Kontrol</span>
              <span className="text-xs font-bold text-neutral-800 mt-1 block font-mono">
                {e2?.mode ?? "AUTO"}
              </span>
            </div>
          </div>

          {/* Rincian Paket */}
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Nomor Urut Paket (Seq):</span>
              <span className="font-mono text-neutral-800">#{e2?.seq ?? "-"}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-neutral-100">
              <span className="text-neutral-500">Pembaruan Terakhir:</span>
              <span className="font-mono text-neutral-600">
                {edge2State.lastUpdated ? edge2State.lastUpdated.toLocaleTimeString("id-ID") : "Menunggu paket..."}
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-neutral-500">Topik Telemetri:</span>
              <span className="font-mono text-[11px] text-amber-700 truncate max-w-[220px]">
                {topic("edge2Telemetry")}
              </span>
            </div>
          </div>

          {/* Raw Payload Preview */}
          <div className="pt-2">
            <span className="text-[11px] font-semibold text-neutral-400 block mb-1">RAW JSON PAYLOAD:</span>
            <pre className="p-3 bg-neutral-900 text-amber-400 font-mono text-[11px] rounded-xl overflow-x-auto">
              {e2 ? JSON.stringify(e2, null, 2) : "// Menunggu paket telemetri pertama..."}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React from "react";
import {
  Waves,
  Cpu,
  Radio,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CloudRain,
  Flame,
} from "lucide-react";
import type { Edge1Telemetry, Edge2Telemetry, AiPrediction } from "@/lib/contract";
import type { DeviceState, ConnectionStatus } from "@/hooks/useMqttLive";

interface MetricCardProps {
  title: string;
  sourceBadge: {
    label: string;
    variant: "simulated" | "experimental" | "actuator" | "official" | "standby" | "warning" | "danger";
  };
  value: string;
  unit?: string;
  subValue?: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor?: string;
}

const badgeStyles = {
  simulated: "bg-blue-50 text-blue-700 border-blue-200",
  experimental: "bg-purple-50 text-purple-700 border-purple-200",
  actuator: "bg-amber-50 text-amber-800 border-amber-200",
  official: "bg-emerald-50 text-emerald-700 border-emerald-200",
  standby: "bg-neutral-100 text-neutral-600 border-neutral-200",
  warning: "bg-yellow-50 text-yellow-800 border-yellow-200",
  danger: "bg-red-50 text-red-700 border-red-200",
};

export function MetricCard({
  title,
  sourceBadge,
  value,
  unit,
  subValue,
  icon: Icon,
  accentColor,
}: MetricCardProps) {
  return (
    <div className={`bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between ${accentColor || ""}`}>
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider truncate">
            {title}
          </span>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border uppercase tracking-wider shrink-0 ${
              badgeStyles[sourceBadge.variant] || badgeStyles.standby
            }`}
          >
            {sourceBadge.label}
          </span>
        </div>

        <div className="flex items-baseline gap-1.5 mt-1">
          <span className="text-2xl font-bold tracking-tight text-neutral-900">{value}</span>
          {unit && <span className="text-xs font-medium text-neutral-500">{unit}</span>}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-neutral-100 flex items-center justify-between text-xs text-neutral-500">
        <span className="truncate">{subValue || "Menunggu data..."}</span>
        <Icon className="w-4 h-4 text-neutral-400 shrink-0 ml-2" />
      </div>
    </div>
  );
}

interface OverviewMetricCardsProps {
  edge1State: DeviceState<Edge1Telemetry>;
  edge2State: DeviceState<Edge2Telemetry>;
  aiPrediction: DeviceState<AiPrediction>;
  connectionStatus: ConnectionStatus;
}

export function OverviewMetricCards({
  edge1State,
  edge2State,
  aiPrediction,
}: OverviewMetricCardsProps) {
  // 1. Status Risiko
  const pred = aiPrediction.data;
  let statusText = "STANDBY";
  let statusVariant: "standby" | "official" | "warning" | "danger" = "standby";

  if (pred?.status) {
    statusText = pred.status;
    if (pred.status === "AMAN") statusVariant = "official";
    else if (pred.status === "SIAGA_1") statusVariant = "warning";
    else if (pred.status === "SIAGA_2" || pred.status === "SIAGA_3") statusVariant = "danger";
  }

  // 2. Edge 1 Pos Air
  const e1 = edge1State.data;
  const isE1Online = edge1State.status === "ONLINE";
  const e1Value = e1 ? e1.level_cm.toFixed(1) : "--.-";
  let e1Sub = e1
    ? (isE1Online
        ? `Laju: ${e1.rate_cm_min >= 0 ? "+" : ""}${e1.rate_cm_min.toFixed(1)} cm/m`
        : `[${edge1State.status}] Data terakhir diterima`)
    : "Menunggu paket telemetri Edge 1...";
  if (e1 && !e1.sensor_ok) {
    e1Sub = "PERINGATAN: Sensor error (hold value)";
  }

  // 3. Prediksi +30m
  const isAiOnline = aiPrediction.status === "ONLINE";
  const predValue = pred ? pred.level_30m.toFixed(1) : "--.-";
  const predDelta = pred && e1 ? (pred.level_30m - e1.level_cm) : null;
  const predSub = predDelta !== null
    ? `Estimasi perubahan: ${predDelta >= 0 ? "+" : ""}${predDelta.toFixed(1)} cm`
    : (pred?.reason || (isAiOnline ? "Inferensi aktif" : "Menunggu server AI..."));

  // 4. Edge 2 Aktuator & Hujan
  const e2 = edge2State.data;
  const isE2Online = edge2State.status === "ONLINE";
  const e2Value = e2 ? `${e2.mode} (P: ${e2.pump})` : "--";
  const e2Sub = e2
    ? `Hujan: ${e2.rain_mm_h.toFixed(1)} mm/h | Suhu: ${e2.temp_c}°C`
    : "Menunggu paket telemetri Edge 2...";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Kartu 1: Status Risiko */}
      <MetricCard
        title="Status Risiko Wilayah"
        sourceBadge={{
          label: isAiOnline ? `RISIKO: ${statusText}` : "AI STANDBY",
          variant: statusVariant,
        }}
        value={statusText}
        subValue={pred?.reason ? `Aturan: ${pred.reason}` : "Ambang: AMAN <105 | SIAGA2 >=120"}
        icon={statusText.startsWith("SIAGA") ? ShieldAlert : ShieldCheck}
      />

      {/* Kartu 2: Tinggi Pasang Air Edge 1 */}
      <MetricCard
        title="Tinggi Pasang Air (Edge 1)"
        sourceBadge={{
          label: !isE1Online ? `EDGE1 ${edge1State.status}` : (e1 && !e1.sensor_ok ? "SENSOR ERROR" : "IoT SIMULATED"),
          variant: e1 && !e1.sensor_ok ? "danger" : (isE1Online ? "simulated" : "standby"),
        }}
        value={e1Value}
        unit="cm"
        subValue={e1Sub}
        icon={e1 && !e1.sensor_ok ? AlertTriangle : Waves}
      />

      {/* Kartu 3: Prediksi Level +30 Menit */}
      <MetricCard
        title="Prediksi Level (+30m)"
        sourceBadge={{
          label: isAiOnline ? "EXPERIMENTAL AI" : "AI STANDBY",
          variant: isAiOnline ? "experimental" : "standby",
        }}
        value={predValue}
        unit="cm"
        subValue={predSub}
        icon={Cpu}
      />

      {/* Kartu 4: Curah Hujan & Status Aktuator */}
      <MetricCard
        title="Aktuator & Hujan (Edge 2)"
        sourceBadge={{
          label: isE2Online && e2 ? `${e2.mode} / ${e2.pump}` : `EDGE2 ${edge2State.status}`,
          variant: e2?.pump === "ON" ? "danger" : (isE2Online ? "actuator" : "standby"),
        }}
        value={e2Value}
        subValue={e2Sub}
        icon={e2?.siren ? Flame : (e2?.pump === "ON" ? Radio : CloudRain)}
      />
    </div>
  );
}

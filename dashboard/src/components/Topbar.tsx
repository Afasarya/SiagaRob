"use client";

import React, { useEffect, useState } from "react";
import { Clock, Wifi, WifiOff, AlertCircle } from "lucide-react";
import { NavTab } from "./Sidebar";
import type { ConnectionStatus } from "@/hooks/useMqttLive";

interface TopbarProps {
  currentTab: NavTab;
  connectionStatus?: ConnectionStatus;
  connectionError?: string | null;
}

const titles: Record<NavTab, { title: string; subtitle: string }> = {
  overview: {
    title: "Ringkasan Sistem & Wilayah Pilot",
    subtitle: "Peta pasang surut Semarang Utara & Timur, metrik telemetri, dan peringatan dini.",
  },
  "map-risk": {
    title: "Peta & Batas AOI Geografis",
    subtitle: "Batas 98,4 km² 6 kelurahan pesisir sasaran berbasis OpenStreetMap & GeoJSON dibekukan.",
  },
  telemetry: {
    title: "Telemetri Edge IoT Virtual",
    subtitle: "Status dan pembacaan sensor Pos Air (HC-SR04) & Pos Hujan (DHT22, Potensiometer).",
  },
  prediction: {
    title: "Prediksi Model AI (+30 Menit)",
    subtitle: "Model HistGradientBoostingRegressor (Delta) & histeresis ambang bahaya.",
  },
  actuator: {
    title: "Kontrol Aktuator & Alarm",
    subtitle: "Status pompa air (relay) dan sirine bahaya (buzzer) dengan mode AUTO / MANUAL.",
  },
  "external-data": {
    title: "Sumber Data Resmi & Cuaca Publik",
    subtitle: "Integrasi BMKG, PantauBanjir, dan BIG melalui adapter FastAPI (Task 08).",
  },
  "testing-info": {
    title: "Informasi Pengujian & Skenario T1–T7",
    subtitle: "Checklist pengujian end-to-end, verifikasi kontrak MQTT, dan rubrik tugas.",
  },
};

export function Topbar({
  currentTab,
  connectionStatus = "disconnected",
  connectionError = null,
}: TopbarProps) {
  const [timeStr, setTimeStr] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString("id-ID", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          timeZoneName: "short",
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const { title, subtitle } = titles[currentTab];

  const statusConfig = {
    connected: {
      label: "MQTT Live",
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
      dot: "bg-emerald-500",
      icon: Wifi,
    },
    connecting: {
      label: "Menghubungkan...",
      color: "bg-amber-50 text-amber-800 border-amber-200",
      dot: "bg-amber-500 animate-pulse",
      icon: Wifi,
    },
    disconnected: {
      label: "Terputus",
      color: "bg-neutral-100 text-neutral-600 border-neutral-200",
      dot: "bg-neutral-400",
      icon: WifiOff,
    },
    error: {
      label: "Error Broker",
      color: "bg-red-50 text-red-700 border-red-200",
      dot: "bg-red-500",
      icon: AlertCircle,
    },
  }[connectionStatus];

  const StatusIcon = statusConfig.icon;

  return (
    <header className="h-20 border-b border-neutral-200 bg-white px-8 flex items-center justify-between shrink-0">
      <div>
        <h2 className="text-lg font-semibold text-neutral-900 leading-tight">{title}</h2>
        <p className="text-xs text-neutral-500 mt-0.5">{subtitle}</p>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection status indicator */}
        <div
          title={connectionError || undefined}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${statusConfig.color}`}
        >
          <span className={`w-2 h-2 rounded-full ${statusConfig.dot}`} />
          <StatusIcon className="w-3.5 h-3.5" />
          <span>{statusConfig.label}</span>
        </div>

        {/* Clock */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50/70 border border-amber-200/80 text-amber-950 text-xs font-mono">
          <Clock className="w-3.5 h-3.5 text-amber-600" />
          <span>{timeStr || "--:--:--"}</span>
        </div>
      </div>
    </header>
  );
}

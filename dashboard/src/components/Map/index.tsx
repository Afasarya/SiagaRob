"use client";

import dynamic from "next/dynamic";
import React from "react";
import type { DeviceState } from "@/hooks/useMqttLive";
import type { Edge1Telemetry, Edge2Telemetry } from "@/lib/contract";

// Wajib PRD §8 & §12: Leaflet hanya dirender di client melalui dynamic import dengan ssr: false
const DynamicMapClient = dynamic(() => import("./MapClient"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[480px] rounded-2xl bg-neutral-100 border border-neutral-200 flex flex-col items-center justify-center gap-3 text-neutral-400">
      <div className="w-8 h-8 border-3 border-amber-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-xs font-medium">Inisialisasi Peta Leaflet & OpenStreetMap...</span>
    </div>
  ),
});

export interface MapViewProps {
  height?: string;
  showDetails?: boolean;
  edge1State?: DeviceState<Edge1Telemetry>;
  edge2State?: DeviceState<Edge2Telemetry>;
}

export function MapView(props: MapViewProps) {
  return <DynamicMapClient {...props} />;
}

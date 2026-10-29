"use client";

import React from "react";
import { Cpu, TrendingUp } from "lucide-react";
import { topic } from "@/lib/contract";
import type { DeviceState } from "@/hooks/useMqttLive";
import type { AiPrediction } from "@/lib/contract";

interface PredictionViewProps {
  aiPrediction: DeviceState<AiPrediction>;
}

export function PredictionView({ aiPrediction }: PredictionViewProps) {
  const pred = aiPrediction.data;
  const isOnline = aiPrediction.status === "ONLINE";

  let statusBadge = {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-200",
    label: "AMAN",
  };

  if (pred?.status === "SIAGA_1") {
    statusBadge = { bg: "bg-yellow-50", text: "text-yellow-800", border: "border-yellow-200", label: "SIAGA 1 (WASPADA)" };
  } else if (pred?.status === "SIAGA_2") {
    statusBadge = { bg: "bg-orange-50", text: "text-orange-800", border: "border-orange-200", label: "SIAGA 2 (KRITIS)" };
  } else if (pred?.status === "SIAGA_3") {
    statusBadge = { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", label: "SIAGA 3 (BAHAYA)" };
  }

  const delta = pred ? pred.level_30m - pred.level_now : 0;

  return (
    <div className="space-y-6">
      {/* Kartu Status Prediksi Live Streaming */}
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900">
                Streaming Inferensi Model AI (+30 Menit Simulasi)
              </h3>
              <p className="text-xs text-neutral-500">
                Topik: <code className="text-amber-700 font-mono">{topic("aiPrediction")}</code>
              </p>
            </div>
          </div>
          <span
            className={`text-xs font-semibold px-3 py-1 rounded-full border flex items-center gap-1.5 ${
              isOnline
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : "bg-neutral-100 text-neutral-600 border-neutral-200"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isOnline ? "bg-emerald-500 animate-ping" : "bg-neutral-400"}`} />
            {isOnline ? "MODEL AKTIF STREAMING" : "MENUNGGU SERVER AI"}
          </span>
        </div>

        {/* Nilai Utama Prediksi */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-semibold text-neutral-400 block uppercase">Level Air Saat Ini</span>
            <div className="flex items-baseline gap-1.5 mt-1">
              <span className="text-2xl font-bold font-mono text-neutral-900">
                {pred ? pred.level_now.toFixed(1) : "--.-"}
              </span>
              <span className="text-xs text-neutral-500">cm</span>
            </div>
            <span className="text-[10px] text-neutral-400 mt-1 block">Dari sensor ultrasonik Edge 1</span>
          </div>

          <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-100">
            <span className="text-[11px] font-semibold text-purple-700 block uppercase">Estimasi Level +30 Menit</span>
            <div className="flex items-baseline gap-1.5 mt-1">
              <span className="text-2xl font-bold font-mono text-purple-900">
                {pred ? pred.level_30m.toFixed(1) : "--.-"}
              </span>
              <span className="text-xs text-purple-700">cm</span>
            </div>
            <span className="text-[10px] text-purple-600 mt-1 block flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              Proyeksi $\Delta$: {delta >= 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)} cm
            </span>
          </div>

          <div className={`p-4 rounded-xl border ${statusBadge.bg} ${statusBadge.border}`}>
            <span className="text-[11px] font-semibold text-neutral-500 block uppercase">Status Tingkat Bahaya</span>
            <div className="text-lg font-bold font-mono mt-1 text-neutral-900">
              {statusBadge.label}
            </div>
            <span className="text-[10px] text-neutral-500 mt-1 block truncate">
              Dasar: {pred?.reason || "Menunggu inferensi..."}
            </span>
          </div>
        </div>

        {/* Rincian Inferensi */}
        <div className="space-y-2 text-xs pt-1">
          <div className="flex justify-between py-1.5 border-b border-neutral-100">
            <span className="text-neutral-500">Pembaruan Paket Prediksi:</span>
            <span className="font-mono text-neutral-700">
              {aiPrediction.lastUpdated ? aiPrediction.lastUpdated.toLocaleTimeString("id-ID") : "-"}
            </span>
          </div>
          <div className="flex justify-between py-1.5 border-b border-neutral-100">
            <span className="text-neutral-500">Model Machine Learning:</span>
            <span className="font-mono text-neutral-800">HistGradientBoostingRegressor (Delta Estimator)</span>
          </div>
          <div className="flex justify-between py-1.5">
            <span className="text-neutral-500">Fitur Masukan:</span>
            <span className="text-neutral-600 text-right">
              level_cm (lag 1..6, roll mean, diff), rain_mm_h, temp_c, hum_pct
            </span>
          </div>
        </div>

        {/* Raw Payload Prediksi */}
        <div className="pt-2">
          <span className="text-[11px] font-semibold text-neutral-400 block mb-1">RAW PREDICTION PAYLOAD:</span>
          <pre className="p-3 bg-neutral-900 text-purple-300 font-mono text-[11px] rounded-xl overflow-x-auto">
            {pred ? JSON.stringify(pred, null, 2) : "// Menunggu paket inferensi dari ai_server.py..."}
          </pre>
        </div>
      </div>

      {/* Rangkuman Evaluasi Model Historis (Task 05) */}
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
        <h4 className="text-sm font-semibold text-neutral-900">
          Metrik Evaluasi Offline Model Delta (Validasi Kronologis)
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">MAE Model Delta</span>
            <span className="text-xl font-bold text-neutral-900 mt-0.5 block">2,026 cm</span>
            <span className="text-[10px] text-neutral-400">Baseline persistence: 2,480 cm</span>
          </div>
          <div className="p-4 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">Perbaikan Relatif</span>
            <span className="text-xl font-bold text-emerald-600 mt-0.5 block">+18,3%</span>
            <span className="text-[10px] text-neutral-400">Mendekati target teoritis 20%</span>
          </div>
          <div className="p-4 bg-neutral-50 rounded-xl border border-neutral-100">
            <span className="text-[11px] font-medium text-neutral-400 block uppercase">MAE Saat Siaga (&ge;105cm)</span>
            <span className="text-xl font-bold text-purple-700 mt-0.5 block">1,807 cm</span>
            <span className="text-[10px] text-neutral-400">Baseline: 2,461 cm (Akurasi Tinggi)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

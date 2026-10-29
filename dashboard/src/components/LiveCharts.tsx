"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { ChartPoint } from "@/hooks/useMqttLive";
import { Activity, Info } from "lucide-react";

interface LiveChartsProps {
  data: ChartPoint[];
}

export function LiveCharts({ data }: LiveChartsProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-8 rounded-2xl border border-neutral-200/90 shadow-sm flex flex-col items-center justify-center gap-3 text-center min-h-[360px]">
        <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
          <Activity className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-neutral-800">Menunggu Sinyal Telemetri</h4>
          <p className="text-xs text-neutral-500 mt-1 max-w-sm">
            Grafik waktu nyata akan otomatis terisi saat telemetri Edge 1 dan AI Server mulai aktif menerbitkan data.
          </p>
        </div>
        <div className="text-[11px] font-mono text-neutral-400 bg-neutral-50 px-3 py-1 rounded border border-neutral-200/70">
          Maksimal 60 sampel riwayat (Rolling Window)
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-neutral-900">
            Tren Ketinggian Air Aktual vs Prediksi Model (+30 Menit)
          </h4>
          <p className="text-xs text-neutral-500 mt-0.5">
            Dikompresi: 1 sampel = 1 menit waktu simulasi (interval 2 detik real-time)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
            60 TITIK TREN
          </span>
        </div>
      </div>

      {/* Main Water Level Chart */}
      <div className="h-[360px] w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="timeLabel"
              tick={{ fontSize: 10, fill: "#64748b" }}
              axisLine={{ stroke: "#cbd5e1" }}
              tickLine={false}
            />
            <YAxis
              domain={[60, 160]}
              tick={{ fontSize: 10, fill: "#64748b" }}
              unit=" cm"
              axisLine={{ stroke: "#cbd5e1" }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#ffffff",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                fontSize: "11px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
              formatter={(value, name) => {
                if (typeof value === "number") {
                  return [`${value.toFixed(1)} cm`, name];
                }
                return ["-", name];
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
              iconType="circle"
            />

            {/* Garis Ambang Referensi PRD §11 */}
            <ReferenceLine
              y={105}
              stroke="#eab308"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{ value: "SIAGA 1 (105cm)", position: "insideTopRight", fill: "#ca8a04", fontSize: 10 }}
            />
            <ReferenceLine
              y={120}
              stroke="#f97316"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{ value: "SIAGA 2 / Pompa ON (120cm)", position: "insideTopRight", fill: "#c2410c", fontSize: 10 }}
            />
            <ReferenceLine
              y={140}
              stroke="#dc2626"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={{ value: "SIAGA 3 / Bahaya (140cm)", position: "insideTopRight", fill: "#b91c1c", fontSize: 10 }}
            />

            {/* Garis Data Aktual Edge 1 */}
            <Line
              type="monotone"
              dataKey="levelActual"
              name="Tinggi Air Aktual (Edge 1)"
              stroke="#0284c7"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5 }}
            />

            {/* Garis Data Prediksi AI */}
            <Line
              type="monotone"
              dataKey="levelPredicted"
              name="Prediksi AI (+30m)"
              stroke="#9333ea"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={false}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-2 p-3 bg-neutral-50 rounded-xl border border-neutral-100 text-[11px] text-neutral-500">
        <Info className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
        <span>
          Grafik mempertahankan riwayat geser 60 sampel terakhir. Garis putus-putus ungu menunjukkan estimasi ketinggian air 30 menit ke depan oleh model AI.
        </span>
      </div>
    </div>
  );
}


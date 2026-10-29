import React from "react";
import {
  LayoutDashboard,
  Map,
  Activity,
  Cpu,
  Radio,
  ExternalLink,
  ClipboardCheck,
  ShieldAlert,
} from "lucide-react";
import { PROJECT_ID } from "@/lib/contract";

export type NavTab =
  | "overview"
  | "map-risk"
  | "telemetry"
  | "prediction"
  | "actuator"
  | "external-data"
  | "testing-info";

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

const navItems: { id: NavTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "map-risk", label: "Peta & Risiko AOI", icon: Map },
  { id: "telemetry", label: "Telemetri IoT", icon: Activity },
  { id: "prediction", label: "Prediksi AI (+30m)", icon: Cpu },
  { id: "actuator", label: "Kontrol Aktuator", icon: Radio },
  { id: "external-data", label: "Sumber Data Resmi", icon: ExternalLink },
  { id: "testing-info", label: "Pengujian & Info PRD", icon: ClipboardCheck },
];

export function Sidebar({ currentTab, onSelectTab }: SidebarProps) {
  return (
    <aside className="w-64 border-r border-neutral-200 bg-white flex flex-col justify-between shrink-0 min-h-screen">
      {/* Brand & Identity */}
      <div>
        <div className="p-5 border-b border-neutral-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold shadow-sm shadow-amber-200">
            <ShieldAlert className="w-5 h-5 text-amber-950" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-neutral-900 leading-tight">SiagaRob</h1>
            <p className="text-xs text-neutral-500">Semarang Utara & Timur</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-neutral-400 uppercase">
            Menu Pemantauan
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                  isActive
                    ? "bg-amber-50 text-amber-900 font-semibold border-l-4 border-amber-500 pl-2.5 shadow-sm"
                    : "text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? "text-amber-600" : "text-neutral-400"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Project ID & Disclaimer Footer */}
      <div className="p-4 border-t border-neutral-100 bg-neutral-50/60 m-3 rounded-xl border space-y-2">
        <div className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
          Konfigurasi Project
        </div>
        <div className="text-xs font-mono bg-white px-2.5 py-1.5 rounded border border-neutral-200 text-neutral-700 truncate">
          {PROJECT_ID}
        </div>
        <p className="text-[10px] text-neutral-500 leading-relaxed">
          <strong>Prototipe Akademik:</strong> Sensor virtual Wokwi & model eksperimen sintetis. Bukan sistem keselamatan publik tervalidasi.
        </p>
      </div>
    </aside>
  );
}


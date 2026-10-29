import React from "react";
import { ClipboardCheck } from "lucide-react";

export function TestingInfoView() {
  const testScenarios = [
    { id: "T1", desc: "Hujan 0, air rendah -> AMAN, Pompa OFF", status: "Teruji di AI/Firmware", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T2", desc: "Hujan bertahap naik, air naik -> SIAGA_2, Pompa ON otomatis", status: "Teruji di AI/Firmware", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T3", desc: "Hujan lebat, air tinggi -> SIAGA_3, Pompa ON, Sirine ON", status: "Teruji di AI/Firmware", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T4", desc: "Pompa OFF dari Dashboard dalam MANUAL -> Pompa mati, AI ditolak", status: "Teruji di AI/Firmware", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T5", desc: "Pilih mode AUTO -> AI kembali mengendalikan pompa", status: "Teruji di AI/Firmware", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T6", desc: "Jarak sensor tidak valid/lonjakan >50cm -> sensor_ok=false", status: "Teruji di Firmware Edge 1", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
    { id: "T7", desc: "Edge 1 berhenti kirim telemetri -> LWT Offline & Timeout 30s", status: "Teruji di AI Server", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 flex items-center justify-center">
              <ClipboardCheck className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900">
                Matriks Pengujian & Verifikasi PRD (Skenario T1–T7)
              </h3>
              <p className="text-xs text-neutral-500">
                Spesifikasi Uji Tugas Kuliah IoT SiagaRob (PRD §16)
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            100% LULUS (PASS)
          </span>
        </div>

        <p className="text-xs text-neutral-600 leading-relaxed">
          Seluruh skenario pengujian T1 hingga T7 telah diverifikasi secara otomatis dan LULUS 100% pada broker live (Lihat <code>docs/TEST-REPORT.md</code>).
        </p>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
        <h4 className="text-sm font-semibold text-neutral-800">Daftar Skenario Uji T1–T7</h4>
        <div className="divide-y divide-neutral-100">
          {testScenarios.map((t) => (
            <div key={t.id} className="py-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-neutral-100 border border-neutral-200 flex items-center justify-center font-bold text-xs text-neutral-700">
                  {t.id}
                </span>
                <span className="text-xs text-neutral-700 font-medium">{t.desc}</span>
              </div>
              <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full border shrink-0 ${t.color}`}>
                {t.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import {
  Radio,
  Power,
  Lock,
  Unlock,
  Bell,
  BellOff,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
} from "lucide-react";
import { topic, type ActuatorMode } from "@/lib/contract";
import type { DeviceState, CommandFeedback } from "@/hooks/useMqttLive";
import type { Edge2Telemetry } from "@/lib/contract";

interface ActuatorViewProps {
  edge2State: DeviceState<Edge2Telemetry>;
  commandFeedback: CommandFeedback;
  sendCommand: (cmd: { pump: "ON" | "OFF"; siren: boolean; mode: ActuatorMode }) => boolean;
  isConnected: boolean;
}

export function ActuatorView({
  edge2State,
  commandFeedback,
  sendCommand,
  isConnected,
}: ActuatorViewProps) {
  const e2 = edge2State.data;
  const isOnline = edge2State.status === "ONLINE" && isConnected;
  const currentMode = e2?.mode || "AUTO";
  const currentPump = e2?.pump || "OFF";
  const currentSiren = e2?.siren || false;

  const [confirmPrompt, setConfirmPrompt] = useState<{
    actionName: string;
    actionFn: () => void;
  } | null>(null);

  const isPending = commandFeedback.status === "pending";

  const handleModeSwitch = (newMode: ActuatorMode) => {
    sendCommand({
      mode: newMode,
      pump: currentPump,
      siren: currentSiren,
    });
  };

  const handlePumpControl = (newPumpState: "ON" | "OFF") => {
    // Jika mematikan pompa dalam kondisi siaga, beri konfirmasi
    if (newPumpState === "OFF") {
      setConfirmPrompt({
        actionName: "Mematikan Pompa Air Drainase (MANUAL)",
        actionFn: () => {
          sendCommand({
            mode: "MANUAL",
            pump: "OFF",
            siren: currentSiren,
          });
          setConfirmPrompt(null);
        },
      });
    } else {
      sendCommand({
        mode: "MANUAL",
        pump: "ON",
        siren: currentSiren,
      });
    }
  };

  const handleSirenControl = (newSirenState: boolean) => {
    sendCommand({
      mode: "MANUAL",
      pump: currentPump,
      siren: newSirenState,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="bg-white p-6 rounded-2xl border border-neutral-200/90 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-800 border border-amber-200 flex items-center justify-center">
              <Radio className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-neutral-900">
                Panel Kontrol Aktuator Dua Arah (Task 10)
              </h3>
              <p className="text-xs text-neutral-500">
                Relay Pompa Air (GPIO 26) & Buzzer Sirine Bahaya (GPIO 27)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                isOnline
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              EDGE 2 {edge2State.status}
            </span>
          </div>
        </div>

        <p className="text-xs text-neutral-600 leading-relaxed">
          Semua perintah dikirim ke <code>{topic("edge2Commands")}</code> dengan <strong>QoS 1, retain=false, source=dashboard</strong>.
          Kontrol tidak mengubah status lokal secara prematur; perubahan hanya dinyatakan <strong>TERKONFIRMASI</strong> setelah telemetri Edge 2 berikutnya diterima.
        </p>

        {!isOnline && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              Edge 2 belum online atau MQTT terputus. Tombol interaksi dinonaktifkan demi keselamatan perangkat.
            </span>
          </div>
        )}
      </div>

      {/* Status Feedback Perintah Terakhir */}
      <div
        className={`p-4 rounded-2xl border text-xs flex items-center justify-between transition-colors ${
          commandFeedback.status === "pending"
            ? "bg-amber-50 border-amber-300 text-amber-900"
            : commandFeedback.status === "confirmed"
            ? "bg-emerald-50 border-emerald-300 text-emerald-900"
            : commandFeedback.status === "failed"
            ? "bg-red-50 border-red-300 text-red-900"
            : "bg-neutral-50 border-neutral-200 text-neutral-700"
        }`}
      >
        <div className="flex items-center gap-2.5">
          {commandFeedback.status === "pending" ? (
            <Loader2 className="w-4 h-4 animate-spin text-amber-600 shrink-0" />
          ) : commandFeedback.status === "confirmed" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : commandFeedback.status === "failed" ? (
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
          ) : (
            <Clock className="w-4 h-4 text-neutral-400 shrink-0" />
          )}
          <span className="font-medium">{commandFeedback.message}</span>
        </div>
        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded border border-current opacity-80 shrink-0">
          FEEDBACK: {commandFeedback.status}
        </span>
      </div>

      {/* Grid Kontrol Aktuator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1. Kontrol Mode Operasi */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              {currentMode === "AUTO" ? (
                <Lock className="w-4 h-4 text-emerald-600" />
              ) : (
                <Unlock className="w-4 h-4 text-amber-600" />
              )}
              <h4 className="text-sm font-semibold text-neutral-900">Mode Operasi</h4>
            </div>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                currentMode === "AUTO"
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                  : "bg-amber-50 text-amber-800 border-amber-200"
              }`}
            >
              {currentMode}
            </span>
          </div>

          <p className="text-xs text-neutral-500 leading-relaxed">
            {currentMode === "AUTO"
              ? "Edge 2 mematuhi keputusan server AI secara otomatis. Beralih ke MANUAL untuk mengambil alih kendali."
              : "Mode MANUAL aktif! AI DILARANG menimpa kendali aktuator operator dashboard (Aturan T4-T5)."}
          </p>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => handleModeSwitch("MANUAL")}
              disabled={!isOnline || isPending || currentMode === "MANUAL"}
              className="w-full py-2.5 px-3 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-900 font-semibold text-xs border border-amber-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Unlock className="w-3.5 h-3.5" />
              <span>Beralih ke MANUAL</span>
            </button>
            <button
              onClick={() => handleModeSwitch("AUTO")}
              disabled={!isOnline || isPending || currentMode === "AUTO"}
              className="w-full py-2.5 px-3 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-semibold text-xs border border-emerald-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Kembalikan ke AUTO (AI)</span>
            </button>
          </div>
        </div>

        {/* 2. Kontrol Pompa Air Drainase */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <Power className="w-4 h-4 text-neutral-600" />
              <h4 className="text-sm font-semibold text-neutral-900">Pompa Air (Relay)</h4>
            </div>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                currentPump === "ON"
                  ? "bg-red-50 text-red-700 border-red-200 font-bold"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {currentPump}
            </span>
          </div>

          <p className="text-xs text-neutral-500 leading-relaxed">
            Relay GPIO 26. Mengendalikan pompa drainase. Mengaktifkan tombol di bawah otomatis menetapkan mode ke <strong>MANUAL</strong>.
          </p>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => handlePumpControl("ON")}
              disabled={!isOnline || isPending}
              className={`w-full py-2.5 px-3 rounded-xl font-semibold text-xs border transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                currentPump === "ON"
                  ? "bg-red-600 text-white border-red-700 shadow-sm"
                  : "bg-neutral-50 hover:bg-neutral-100 text-neutral-800 border-neutral-200"
              }`}
            >
              <Power className="w-3.5 h-3.5" />
              <span>Nyalakan Pompa (ON)</span>
            </button>
            <button
              onClick={() => handlePumpControl("OFF")}
              disabled={!isOnline || isPending}
              className={`w-full py-2.5 px-3 rounded-xl font-semibold text-xs border transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                currentPump === "OFF"
                  ? "bg-neutral-700 text-white border-neutral-800 shadow-sm"
                  : "bg-neutral-50 hover:bg-neutral-100 text-neutral-800 border-neutral-200"
              }`}
            >
              <Power className="w-3.5 h-3.5" />
              <span>Matikan Pompa (OFF)</span>
            </button>
          </div>
        </div>

        {/* 3. Kontrol Sirine Bahaya */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/90 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-100">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-neutral-600" />
              <h4 className="text-sm font-semibold text-neutral-900">Sirine Bahaya (Buzzer)</h4>
            </div>
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
                currentSiren
                  ? "bg-red-50 text-red-700 border-red-200 font-bold animate-pulse"
                  : "bg-neutral-100 text-neutral-600 border-neutral-200"
              }`}
            >
              {currentSiren ? "BUNYI (ON)" : "SENYAP (OFF)"}
            </span>
          </div>

          <p className="text-xs text-neutral-500 leading-relaxed">
            Buzzer 2 kHz GPIO 27. Aktif otomatis saat risiko SIAGA_3 (&ge;140 cm). Dapat dibunyikan atau diheningkan manual.
          </p>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => handleSirenControl(true)}
              disabled={!isOnline || isPending}
              className={`w-full py-2.5 px-3 rounded-xl font-semibold text-xs border transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                currentSiren
                  ? "bg-red-600 text-white border-red-700 shadow-sm"
                  : "bg-neutral-50 hover:bg-neutral-100 text-neutral-800 border-neutral-200"
              }`}
            >
              <Bell className="w-3.5 h-3.5" />
              <span>Bunyikan Sirine (ON)</span>
            </button>
            <button
              onClick={() => handleSirenControl(false)}
              disabled={!isOnline || isPending}
              className={`w-full py-2.5 px-3 rounded-xl font-semibold text-xs border transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                !currentSiren
                  ? "bg-neutral-700 text-white border-neutral-800 shadow-sm"
                  : "bg-neutral-50 hover:bg-neutral-100 text-neutral-800 border-neutral-200"
              }`}
            >
              <BellOff className="w-3.5 h-3.5" />
              <span>Heningkan Sirine (OFF)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Modal / Dialog Konfirmasi Sederhana */}
      {confirmPrompt && (
        <div className="fixed inset-0 bg-neutral-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-5 shadow-xl border border-neutral-200 space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-neutral-900">Konfirmasi Tindakan</h4>
                <p className="text-xs text-neutral-500 mt-1 leading-relaxed">
                  Apakah Anda yakin ingin mengeksekusi <strong>{confirmPrompt.actionName}</strong>?
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setConfirmPrompt(null)}
                className="py-2 px-3 text-xs font-semibold text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
              >
                Batal
              </button>
              <button
                onClick={confirmPrompt.actionFn}
                className="py-2 px-3.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-sm transition-colors"
              >
                Ya, Jalankan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import mqtt, { type MqttClient } from "mqtt";
import {
  MQTT_WS_URL,
  PROJECT_ID as DEFAULT_PROJECT_ID,
  topic,
  type Edge1Telemetry,
  type Edge2Telemetry,
  type AiPrediction,
  type Edge2Command,
  type ActuatorMode,
} from "@/lib/contract";

export type ConnectionStatus = "connected" | "connecting" | "disconnected" | "error";

export interface ChartPoint {
  timeLabel: string;
  seq: number;
  levelActual?: number;
  levelPredicted?: number;
  rain?: number;
  sensorOk: boolean;
}

export interface DeviceState<T> {
  data: T | null;
  lastUpdated: Date | null;
  status: "ONLINE" | "STALE" | "OFFLINE";
}

export type CommandFeedbackStatus = "idle" | "pending" | "confirmed" | "failed";

export interface CommandFeedback {
  status: CommandFeedbackStatus;
  targetCommand: {
    pump: "ON" | "OFF";
    siren: boolean;
    mode: ActuatorMode;
  } | null;
  sentAt: Date | null;
  message: string;
}

const MAX_CHART_POINTS = 60;
const STALE_TIMEOUT_MS = 30000;   // 30 detik tanpa data -> STALE
const OFFLINE_TIMEOUT_MS = 60000;  // 60 detik tanpa data -> OFFLINE
const COMMAND_TIMEOUT_MS = 8000;   // 8 detik menunggu feedback telemetri

export function useMqttLive(customProjectId?: string) {
  const rawProjectId = customProjectId || DEFAULT_PROJECT_ID;
  const projectId = (!rawProjectId || rawProjectId === "GANTI_DENGAN_ID_UNIK_TIM")
    ? "siagarob_1739233"
    : rawProjectId;

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const [edge1State, setEdge1State] = useState<DeviceState<Edge1Telemetry>>({
    data: null,
    lastUpdated: null,
    status: "OFFLINE",
  });

  const [edge2State, setEdge2State] = useState<DeviceState<Edge2Telemetry>>({
    data: null,
    lastUpdated: null,
    status: "OFFLINE",
  });

  const [aiPrediction, setAiPrediction] = useState<DeviceState<AiPrediction>>({
    data: null,
    lastUpdated: null,
    status: "OFFLINE",
  });

  const [commandFeedback, setCommandFeedback] = useState<CommandFeedback>({
    status: "idle",
    targetCommand: null,
    sentAt: null,
    message: "Siap menerima instruksi operator.",
  });

  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const clientRef = useRef<MqttClient | null>(null);
  const lastSeqEdge1Ref = useRef<number>(-1);
  const feedbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Inisialisasi koneksi MQTT Browser via WebSocket TLS
  useEffect(() => {
    if (typeof window === "undefined") return;

    const clientId = `siagarob-dash-${projectId}-${Math.random().toString(16).substring(2, 8)}`;

    const client = mqtt.connect(MQTT_WS_URL, {
      clientId,
      clean: true,
      reconnectPeriod: 3000,
      connectTimeout: 10000,
      protocol: "wss",
    });

    clientRef.current = client;

    const tEdge1 = topic("edge1Telemetry", projectId);
    const tEdge2 = topic("edge2Telemetry", projectId);
    const tEdge1Status = topic("edge1Status", projectId);
    const tEdge2Status = topic("edge2Status", projectId);
    const tAiPred = topic("aiPrediction", projectId);

    client.on("connect", () => {
      setConnectionStatus("connected");
      setConnectionError(null);

      // Subscribe ke seluruh topic proyek (wildcard + topic eksplisit)
      const wildcard = `siagarob/${projectId}/#`;
      client.subscribe(
        [wildcard, tEdge1, tEdge2, tEdge1Status, tEdge2Status, tAiPred],
        { qos: 1 },
        (err) => {
          if (err) {
            console.error("Gagal subscribe topic MQTT:", err);
          } else {
            console.log(`[MQTT] Berhasil subscribe ke topic proyek: ${wildcard}`);
          }
        }
      );
    });

    client.on("reconnect", () => {
      setConnectionStatus("connecting");
    });

    client.on("close", () => {
      setConnectionStatus("disconnected");
    });

    client.on("error", (err) => {
      console.warn("MQTT connection error:", err);
      setConnectionStatus("error");
      setConnectionError(err.message || "Gagal menyambung ke broker MQTT.");
    });

    client.on("message", (recvTopic, payloadBuffer) => {
      const payloadStr = payloadBuffer.toString("utf-8");
      const now = new Date();

      try {
        // 1. Edge 1 Telemetry
        if (recvTopic === tEdge1 || recvTopic.endsWith("/edge/edge1/telemetry")) {
          const parsed: Edge1Telemetry = JSON.parse(payloadStr);
          if (parsed && (parsed.device_id === "edge1" || typeof parsed.level_cm === "number")) {
            setEdge1State({
              data: parsed,
              lastUpdated: now,
              status: "ONLINE",
            });

            // Filter sequence duplikat pada grafik
            if (parsed.seq !== lastSeqEdge1Ref.current) {
              lastSeqEdge1Ref.current = parsed.seq;
              const timeLabel = now.toLocaleTimeString("id-ID", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              });

              setChartData((prev) => {
                const nextPoint: ChartPoint = {
                  timeLabel,
                  seq: parsed.seq,
                  levelActual: parsed.sensor_ok ? Number(parsed.level_cm.toFixed(1)) : undefined,
                  sensorOk: parsed.sensor_ok,
                };

                const updated = [...prev, nextPoint];
                if (updated.length > MAX_CHART_POINTS) {
                  return updated.slice(updated.length - MAX_CHART_POINTS);
                }
                return updated;
              });
            }
          }
        }

        // 2. Edge 2 Telemetry (dan verifikasi feedback command)
        else if (recvTopic === tEdge2 || recvTopic.endsWith("/edge/edge2/telemetry")) {
          const parsed: Edge2Telemetry = JSON.parse(payloadStr);
          if (parsed && (parsed.device_id === "edge2" || typeof parsed.rain_mm_h === "number")) {
            setEdge2State({
              data: parsed,
              lastUpdated: now,
              status: "ONLINE",
            });

            // Evaluasi Feedback Loop Konfirmasi (PRD Task 10)
            setCommandFeedback((prev) => {
              if (prev.status === "pending" && prev.targetCommand) {
                const isModeMatch = parsed.mode === prev.targetCommand.mode;
                const isPumpMatch = parsed.pump === prev.targetCommand.pump;
                const isSirenMatch = parsed.siren === prev.targetCommand.siren;

                if (isModeMatch && isPumpMatch && isSirenMatch) {
                  if (feedbackTimeoutRef.current) {
                    clearTimeout(feedbackTimeoutRef.current);
                    feedbackTimeoutRef.current = null;
                  }
                  return {
                    status: "confirmed",
                    targetCommand: prev.targetCommand,
                    sentAt: prev.sentAt,
                    message: `Terkonfirmasi oleh Edge 2: Mode ${parsed.mode}, Pompa ${parsed.pump}, Sirine ${parsed.siren ? "ON" : "OFF"}.`,
                  };
                }
              }
              return prev;
            });

            // Update curah hujan pada titik grafik terakhir
            setChartData((prev) => {
              if (prev.length === 0) return prev;
              const last = { ...prev[prev.length - 1], rain: Number(parsed.rain_mm_h.toFixed(1)) };
              return [...prev.slice(0, prev.length - 1), last];
            });
          }
        }

        // 3. AI Prediction
        else if (recvTopic === tAiPred || recvTopic.endsWith("/ai/prediction")) {
          const parsed: AiPrediction = JSON.parse(payloadStr);
          if (parsed && typeof parsed.level_30m === "number") {
            setAiPrediction({
              data: parsed,
              lastUpdated: now,
              status: "ONLINE",
            });

            // Update prediksi pada titik grafik terakhir
            setChartData((prev) => {
              if (prev.length === 0) return prev;
              const last = { ...prev[prev.length - 1], levelPredicted: Number(parsed.level_30m.toFixed(1)) };
              return [...prev.slice(0, prev.length - 1), last];
            });
          }
        }

        // 4. LWT Status Edge 1
        else if (recvTopic === tEdge1Status || recvTopic.endsWith("/edge/edge1/status")) {
          const statusText = payloadStr.trim().toLowerCase();
          if (statusText === "offline") {
            setEdge1State((prev) => ({ ...prev, status: "OFFLINE" }));
          } else if (statusText === "online") {
            setEdge1State((prev) => ({ ...prev, status: "ONLINE", lastUpdated: now }));
          }
        }

        // 5. LWT Status Edge 2
        else if (recvTopic === tEdge2Status || recvTopic.endsWith("/edge/edge2/status")) {
          const statusText = payloadStr.trim().toLowerCase();
          if (statusText === "offline") {
            setEdge2State((prev) => ({ ...prev, status: "OFFLINE" }));
          } else if (statusText === "online") {
            setEdge2State((prev) => ({ ...prev, status: "ONLINE", lastUpdated: now }));
          }
        }
      } catch (err) {
        console.warn("Payload JSON rusak diabaikan:", recvTopic, err);
      }
    });

    // Cleanup saat unmount: putuskan koneksi MQTT dengan aman
    return () => {
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }
      client.end(true);
      clientRef.current = null;
    };
  }, [projectId]);

  // Fungsi pengiriman perintah aktuator (Task 10)
  // Wajib: source="dashboard", QoS 1, retain=false (PRD §9.4)
  const sendCommand = useCallback(
    (cmd: { pump: "ON" | "OFF"; siren: boolean; mode: ActuatorMode }) => {
      const client = clientRef.current;
      if (!client || !client.connected) {
        setCommandFeedback({
          status: "failed",
          targetCommand: cmd,
          sentAt: new Date(),
          message: "Gagal: Klien MQTT dashboard tidak terhubung ke broker.",
        });
        return false;
      }

      if (edge2State.status === "OFFLINE") {
        setCommandFeedback({
          status: "failed",
          targetCommand: cmd,
          sentAt: new Date(),
          message: "Ditolak: Edge 2 berstatus OFFLINE. Perintah tidak dapat dieksekusi.",
        });
        return false;
      }

      const payload: Edge2Command = {
        pump: cmd.pump,
        siren: cmd.siren,
        mode: cmd.mode,
        source: "dashboard",
      };

      const cmdTopic = topic("edge2Commands", projectId);
      const payloadStr = JSON.stringify(payload);

      // Bersihkan timer sebelumnya jika ada
      if (feedbackTimeoutRef.current) {
        clearTimeout(feedbackTimeoutRef.current);
      }

      setCommandFeedback({
        status: "pending",
        targetCommand: cmd,
        sentAt: new Date(),
        message: `Mengirim perintah ${cmd.mode} (Pompa: ${cmd.pump}, Sirine: ${cmd.siren ? "ON" : "OFF"}). Menunggu konfirmasi telemetri Edge 2...`,
      });

      client.publish(cmdTopic, payloadStr, { qos: 1, retain: false }, (err) => {
        if (err) {
          setCommandFeedback({
            status: "failed",
            targetCommand: cmd,
            sentAt: new Date(),
            message: `Gagal menerbitkan command: ${err.message}`,
          });
        }
      });

      // Watchdog timeout konfirmasi telemetri (8 detik)
      feedbackTimeoutRef.current = setTimeout(() => {
        setCommandFeedback((prev) => {
          if (prev.status === "pending") {
            return {
              status: "failed",
              targetCommand: prev.targetCommand,
              sentAt: prev.sentAt,
              message: "Timeout: Edge 2 tidak memberikan konfirmasi telemetri dalam 8 detik.",
            };
          }
          return prev;
        });
      }, COMMAND_TIMEOUT_MS);

      return true;
    },
    [projectId, edge2State.status]
  );

  // Periodic Watchdog Timer untuk deteksi STALE dan OFFLINE
  useEffect(() => {
    const interval = setInterval(() => {
      const nowMs = Date.now();

      // Cek Edge 1
      if (edge1State.lastUpdated) {
        const diff = nowMs - edge1State.lastUpdated.getTime();
        if (diff > OFFLINE_TIMEOUT_MS && edge1State.status !== "OFFLINE") {
          setEdge1State((prev) => ({ ...prev, status: "OFFLINE" }));
        } else if (diff > STALE_TIMEOUT_MS && edge1State.status === "ONLINE") {
          setEdge1State((prev) => ({ ...prev, status: "STALE" }));
        }
      }

      // Cek Edge 2
      if (edge2State.lastUpdated) {
        const diff = nowMs - edge2State.lastUpdated.getTime();
        if (diff > OFFLINE_TIMEOUT_MS && edge2State.status !== "OFFLINE") {
          setEdge2State((prev) => ({ ...prev, status: "OFFLINE" }));
        } else if (diff > STALE_TIMEOUT_MS && edge2State.status === "ONLINE") {
          setEdge2State((prev) => ({ ...prev, status: "STALE" }));
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [edge1State.lastUpdated, edge1State.status, edge2State.lastUpdated, edge2State.status]);

  return {
    connectionStatus,
    connectionError,
    edge1State,
    edge2State,
    aiPrediction,
    chartData,
    projectId,
    commandFeedback,
    sendCommand,
  };
}

/**
 * Definisi tunggal kontrak MQTT SiagaRob di sisi dashboard.
 * Sumber: docs/prd/00-PRD-CONTEXT.md §9 dan docs/CONTRACT.md.
 */

export const PROJECT_ID_PLACEHOLDER = "siagarob_1739233";

export const PROJECT_ID: string = "siagarob_1739233";

export const MQTT_WS_URL: string =
  process.env.NEXT_PUBLIC_MQTT_WS_URL || "wss://broker.hivemq.com:8884/mqtt";

export function topicPrefix(projectId: string = PROJECT_ID): string {
  return `siagarob/${projectId}/`;
}

export const TOPIC_SUFFIX = {
  edge1Telemetry: "edge/edge1/telemetry",
  edge2Telemetry: "edge/edge2/telemetry",
  edge1Status: "edge/edge1/status",
  edge2Status: "edge/edge2/status",
  aiPrediction: "ai/prediction",
  edge2Commands: "edge/edge2/commands",
} as const;

export type TopicKey = keyof typeof TOPIC_SUFFIX;

export const TOPIC_QOS: Record<TopicKey, 0 | 1> = {
  edge1Telemetry: 0,
  edge2Telemetry: 0,
  edge1Status: 1,
  edge2Status: 1,
  aiPrediction: 0,
  edge2Commands: 1,
};

export const TOPIC_RETAIN: Record<TopicKey, boolean> = {
  edge1Telemetry: false,
  edge2Telemetry: false,
  edge1Status: true,
  edge2Status: true,
  aiPrediction: true,
  edge2Commands: false,
};

export function topic(key: TopicKey, projectId: string = PROJECT_ID): string {
  return `${topicPrefix(projectId)}${TOPIC_SUFFIX[key]}`;
}

export const RECONNECT_MS = 3000;

export interface Edge1Telemetry {
  device_id: "edge1";
  seq: number;
  level_cm: number;
  rate_cm_min: number;
  sensor_ok: boolean;
  uptime_ms: number;
}

export type ActuatorMode = "AUTO" | "MANUAL";

export interface Edge2Telemetry {
  device_id: "edge2";
  seq: number;
  rain_mm_h: number;
  temp_c: number;
  hum_pct: number;
  pump: "ON" | "OFF";
  siren: boolean;
  mode: ActuatorMode;
  uptime_ms: number;
}

export type RiskStatus = "AMAN" | "SIAGA_1" | "SIAGA_2" | "SIAGA_3";

export interface AiPrediction {
  level_now: number;
  level_30m: number;
  status: RiskStatus;
  reason: string;
  seq: number;
}

export interface Edge2Command {
  pump: "ON" | "OFF";
  siren: boolean;
  mode: ActuatorMode;
  source: "ai" | "dashboard";
}

export type EdgeStatus = "online" | "offline";

// Metadata data (PRD §3)
export type SourceType =
  | "official"
  | "iot_simulated"
  | "derived"
  | "model_prediction"
  | "demo";

export type DataStatus = "LIVE" | "STALE" | "UNAVAILABLE" | "SIMULATED" | "DEMO";

export interface DataMeta {
  source: string;
  source_type: SourceType;
  observed_at?: string;
  issued_at?: string;
  fetched_at: string;
  stale_after_seconds: number;
  status: DataStatus;
  unit?: string;
  location?: string;
}


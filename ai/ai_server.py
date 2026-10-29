"""AI Server SiagaRob (Task 06).

Menghubungkan model prediksi dan engine aturan ke broker MQTT:
  - Subscribe: siagarob/PROJECT_ID/edge/+/telemetry dan status.
  - Memperbarui fitur identik dengan training secara streaming (Predictor).
  - Menghitung status risiko (max(level_now, level_30m)) dan histeresis pompa.
  - Menerbitkan prediksi ke ai/prediction (QoS 0, retain=True).
  - Mengirim command ke edge/edge2/commands (QoS 1, retain=False) HANYA jika Edge 2 dalam mode AUTO.
  - Deteksi timeout: jika Edge 1 tidak mengirim telemetri >30 detik real time, tandai OFFLINE.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import predictor as P  # noqa: E402
import rules as R  # noqa: E402
import siagarob_contract as C  # noqa: E402

EDGE1_TIMEOUT_SECONDS = 30.0

logger = logging.getLogger("ai_server")


class AiServer:
    def __init__(
        self,
        project_id: str,
        model_path: str | Path,
        mqtt_client: Any = None,
    ) -> None:
        self.project_id = C.validate_project_id(project_id)
        self.predictor = P.Predictor.load(model_path)
        self.decision_engine = R.DecisionEngine()
        self.mqtt_client = mqtt_client

        # State tracking
        self.latest_rain_mm_h: float = 0.0
        self.latest_edge2_mode: str = "AUTO"
        self.latest_edge2_pump: str = "OFF"
        self.latest_edge2_siren: bool = False
        self.last_edge1_time: float = 0.0
        self.edge1_online: bool = False
        self.last_edge1_seq: int = 0
        self.last_sent_command: dict[str, Any] | None = None

        # Topics
        self.topic_edge_wildcard = f"siagarob/{self.project_id}/edge/+/telemetry"
        self.topic_status_wildcard = f"siagarob/{self.project_id}/edge/+/status"
        self.topic_pred = C.topic(self.project_id, "ai_prediction")
        self.topic_cmd = C.topic(self.project_id, "edge2_commands")

    def handle_message(self, topic: str, payload_bytes: bytes, current_time: float | None = None) -> dict[str, Any] | None:
        """Pusat pemrosesan pesan (dapat dipanggil langsung di unit test)."""
        now = time.time() if current_time is None else current_time
        classified = C.classify_topic(self.project_id, topic)

        # 1. Edge 2 Telemetry (Update hujan dan mode aktuator)
        if classified == "edge2_telemetry":
            v = C.validate_payload("edge2_telemetry", payload_bytes)
            if not v.ok:
                logger.warning("Telemetry Edge 2 tidak valid: %s", v.errors)
                return None
            data = v.data
            self.latest_rain_mm_h = float(data["rain_mm_h"])
            self.latest_edge2_mode = data["mode"]
            self.latest_edge2_pump = data["pump"]
            self.latest_edge2_siren = data["siren"]
            return {"type": "edge2_telemetry", "mode": self.latest_edge2_mode, "rain": self.latest_rain_mm_h}

        # 2. Edge 1 Status (LWT)
        if classified == "edge1_status":
            v = C.validate_payload("edge1_status", payload_bytes)
            if v.ok and v.data == "offline":
                logger.info("Edge 1 melaporkan status LWT: offline")
                self._handle_edge1_offline(now, reason="edge1_lwt_offline")
            return {"type": "edge1_status", "status": v.data if v.ok else "invalid"}

        # 3. Edge 1 Telemetry (Pemicu inferensi dan kontrol)
        if classified == "edge1_telemetry":
            v = C.validate_payload("edge1_telemetry", payload_bytes)
            if not v.ok:
                logger.warning("Telemetry Edge 1 tidak valid: %s", v.errors)
                return None

            data = v.data
            self.last_edge1_time = now
            self.edge1_online = True
            self.last_edge1_seq = int(data["seq"])

            level_now = float(data["level_cm"])
            sensor_ok = bool(data["sensor_ok"])

            # Update predictor streaming
            try:
                pred = self.predictor.update(level_now, self.latest_rain_mm_h, sensor_ok=sensor_ok)
            except P.InvalidInput as err:
                logger.error("Predictor menolak input: %s", err)
                return None

            if pred is None:
                # Masa warmup (60 sampel pertama)
                level_30m = level_now
                status_reason = "warmup_persistence;baseline"
            else:
                level_30m = pred.level_30m
                status_reason = "model+rule"
                if not pred.reliable:
                    status_reason += ";unreliable_sensor"

            decision = self.decision_engine.evaluate(level_now, level_30m, sensor_ok=sensor_ok)

            # Siapkan payload prediksi (PRD §9.3)
            pred_payload = {
                "level_now": round(level_now, 1),
                "level_30m": round(level_30m, 1),
                "status": decision.status,
                "reason": status_reason,
                "seq": self.last_edge1_seq,
            }

            # Publikasikan prediksi (QoS 0, retain=True)
            self._publish(self.topic_pred, json.dumps(pred_payload), qos=0, retain=True)

            # Evaluasi dan publikasikan command AI ke Edge 2 HANYA jika mode AUTO
            cmd_payload = None
            if self.latest_edge2_mode == "AUTO":
                cmd_payload = {
                    "pump": decision.pump,
                    "siren": decision.siren,
                    "mode": "AUTO",
                    "source": "ai",
                }
                # Kirim jika berbeda dengan command terakhir atau state edge2 saat ini
                state_mismatch = (self.latest_edge2_pump != decision.pump) or (self.latest_edge2_siren != decision.siren)
                if state_mismatch or self.last_sent_command != cmd_payload:
                    self._publish(self.topic_cmd, json.dumps(cmd_payload), qos=1, retain=False)
                    self.last_sent_command = cmd_payload
                    logger.info("Command AI dikirim ke Edge 2: %s", cmd_payload)
            else:
                logger.debug("Edge 2 dalam mode MANUAL; AI tidak mengirim command (tidak menimpa operator).")

            return {
                "type": "prediction_and_decision",
                "prediction": pred_payload,
                "decision": decision,
                "command": cmd_payload,
            }

        return None

    def check_timeouts(self, current_time: float | None = None) -> bool:
        """Periksa apakah Edge 1 mengalami timeout (> 30s real time)."""
        now = time.time() if current_time is None else current_time
        if self.edge1_online and self.last_edge1_time > 0 and (now - self.last_edge1_time > EDGE1_TIMEOUT_SECONDS):
            logger.warning("Timeout: Edge 1 tidak mengirim telemetri selama %.1f detik.", now - self.last_edge1_time)
            self._handle_edge1_offline(now, reason="edge1_timeout>30s")
            return True
        return False

    def _handle_edge1_offline(self, now: float, reason: str) -> None:
        self.edge1_online = False
        self.predictor.reset()
        self.decision_engine.reset()

        # Terbitkan status OFFLINE pada prediksi
        offline_payload = {
            "level_now": 0.0,
            "level_30m": 0.0,
            "status": "AMAN",
            "reason": f"OFFLINE;{reason}",
            "seq": self.last_edge1_seq,
        }
        self._publish(self.topic_pred, json.dumps(offline_payload), qos=0, retain=True)

    def _publish(self, topic: str, payload_str: str, qos: int, retain: bool) -> None:
        if self.mqtt_client is not None:
            try:
                self.mqtt_client.publish(topic, payload_str, qos=qos, retain=retain)
            except Exception as e:
                logger.error("Gagal publish ke %s: %s", topic, e)


def run_server(project_id: str | None = None, host: str = "broker.hivemq.com", port: int = 1883) -> int:
    import paho.mqtt.client as mqtt

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    pid = project_id or C.load_project_id()
    model_path = Path(__file__).resolve().parent / "model.joblib"
    if not model_path.is_file():
        logger.error("Model tidak ditemukan di %s. Jalankan ai/train.py terlebih dahulu.", model_path)
        return 1

    client_id = f"siagarob-ai-server-{pid}-{int(time.time())}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    server = AiServer(project_id=pid, model_path=model_path, mqtt_client=client)

    def on_connect(c, userdata, flags, rc, props):
        logger.info("Tersambung ke broker %s:%d. Subscribe topics...", host, port)
        c.subscribe([(server.topic_edge_wildcard, 0), (server.topic_status_wildcard, 1)])

    def on_message(c, userdata, msg):
        server.handle_message(msg.topic, msg.payload)

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Memulai AI Server untuk PROJECT_ID=%s", pid)
    client.connect(host, port, keepalive=30)
    client.loop_start()

    try:
        while True:
            time.sleep(1.0)
            server.check_timeouts()
    except KeyboardInterrupt:
        logger.info("AI Server dihentikan pengguna.")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("MQTT_HOST", "broker.hivemq.com"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MQTT_PORT", 1883)))
    args = parser.parse_args(argv)
    return run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    sys.exit(main())


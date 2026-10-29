// SiagaRob — Edge 1 Pos Air (ESP32 + HC-SR04), simulasi Wokwi.
// Kontrak: docs/CONTRACT.md. Catatan desain: edge1_wokwi/README.md.
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "edge1_logic.h"

// ====== KONFIGURASI (samakan PROJECT_ID dengan .env / dashboard) ======
#define PROJECT_ID "siagarob_1739233"
// ======================================================================

static const int PIN_TRIG = 5;
static const int PIN_ECHO = 18;
static const int PIN_LED = 2;

static const char *MQTT_HOST = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const uint32_t PUBLISH_INTERVAL_MS = 2000;  // 1 pesan = 1 menit simulasi
static const uint32_t RECONNECT_DELAY_MS = 3000;

static const char *TOPIC_TELEMETRY = "siagarob/" PROJECT_ID "/edge/edge1/telemetry";
static const char *TOPIC_STATUS = "siagarob/" PROJECT_ID "/edge/edge1/status";
static const char *CLIENT_ID = "siagarob-edge1-" PROJECT_ID;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
edge1::Processor processor;

static uint32_t seq = 0;
static uint32_t lastPublish = 0;
static uint32_t lastReconnectAttempt = 0;
static bool lastSensorOk = false;

// Jarak HC-SR04 dalam cm; 0 jika echo timeout (tidak ada pantulan).
static float readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  unsigned long us = pulseIn(PIN_ECHO, HIGH, 30000UL);  // timeout 30 ms (~5 m)
  if (us == 0) return 0.0f;
  return (float)us * 0.0343f / 2.0f;
}

static void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

// Coba satu kali; dipanggil dari loop dengan jeda 3 detik. LWT: offline, QoS1, retained.
static bool connectMqtt() {
  bool ok = mqtt.connect(CLIENT_ID, nullptr, nullptr, TOPIC_STATUS, 1, true, "offline");
  if (ok) {
    // PubSubClient hanya menerbitkan QoS0; retained=true dipertahankan.
    mqtt.publish(TOPIC_STATUS, "online", true);
  }
  return ok;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  connectWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(15);
}

void loop() {
  connectWifi();

  uint32_t now = millis();
  if (!mqtt.connected()) {
    digitalWrite(PIN_LED, LOW);
    if (now - lastReconnectAttempt >= RECONNECT_DELAY_MS) {
      lastReconnectAttempt = now;
      if (connectMqtt()) Serial.println("MQTT tersambung");
      else Serial.println("MQTT gagal, ulangi 3 detik");
    }
  } else {
    mqtt.loop();
  }

  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;
    float d = readDistanceCm();
    edge1::Result r = processor.process(d);
    lastSensorOk = r.sensor_ok;
    // LED menyala bila sensor OK dan MQTT tersambung.
    digitalWrite(PIN_LED, (r.sensor_ok && mqtt.connected()) ? HIGH : LOW);

    char buf[256];
    int n = edge1::formatTelemetry(buf, sizeof(buf), ++seq, r, now);
    Serial.printf("jarak=%.1f %s\n", d, buf);
    if (n > 0 && n < (int)sizeof(buf) && mqtt.connected()) {
      mqtt.publish(TOPIC_TELEMETRY, buf, false);
    }
  }
}


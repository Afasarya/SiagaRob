// SiagaRob — Edge 2 Pos Hujan + Aktuator (ESP32, DHT22, potensiometer, relay/LED, buzzer), Wokwi.
// Kontrak: docs/CONTRACT.md. Catatan desain: edge2_wokwi/README.md.
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include "edge2_logic.h"

// ====== KONFIGURASI (samakan PROJECT_ID dengan .env / dashboard) ======
#define PROJECT_ID "siagarob_1739233"
// ======================================================================

static const int PIN_DHT = 15;
static const int PIN_POT = 34;
static const int PIN_PUMP = 26;    // relay / LED merah
static const int PIN_BUZZER = 27;
static const int BUZZER_HZ = 2000;

static const char *MQTT_HOST = "broker.hivemq.com";
static const uint16_t MQTT_PORT = 1883;
static const uint32_t PUBLISH_INTERVAL_MS = 2000;
static const uint32_t RECONNECT_DELAY_MS = 3000;

static const char *TOPIC_TELEMETRY = "siagarob/" PROJECT_ID "/edge/edge2/telemetry";
static const char *TOPIC_STATUS = "siagarob/" PROJECT_ID "/edge/edge2/status";
static const char *TOPIC_COMMANDS = "siagarob/" PROJECT_ID "/edge/edge2/commands";
static const char *CLIENT_ID = "siagarob-edge2-" PROJECT_ID;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
DHT dht(PIN_DHT, DHT22);
edge2::RainAverager rainAvg;
edge2::State state;

static uint32_t seq = 0;
static uint32_t lastPublish = 0;
static uint32_t lastReconnectAttempt = 0;
static float lastTemp = 0.0f;  // nilai valid terakhir; 0 sebelum pembacaan DHT22 pertama berhasil
static float lastHum = 0.0f;

static void applyOutputs() {
  digitalWrite(PIN_PUMP, state.pump ? HIGH : LOW);
  if (state.siren) tone(PIN_BUZZER, BUZZER_HZ);
  else noTone(PIN_BUZZER);
}

static void onMessage(char *topic, uint8_t *payload, unsigned int length) {
  (void)topic;
  edge2::CmdResult r = edge2::applyCommand(state, (const char *)payload, length);
  Serial.printf("command (%u byte): %s\n", length, edge2::cmdResultText(r));
  if (r == edge2::CmdResult::APPLIED) {
    applyOutputs();  // keadaan dilaporkan pada telemetri berikutnya
  }
}

static void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
  }
}

// Satu percobaan; dipanggil dari loop dengan jeda 3 detik. LWT: offline, QoS1, retained.
static bool connectMqtt() {
  bool ok = mqtt.connect(CLIENT_ID, nullptr, nullptr, TOPIC_STATUS, 1, true, "offline");
  if (ok) {
    mqtt.publish(TOPIC_STATUS, "online", true);  // PubSubClient: QoS0, retained
    mqtt.subscribe(TOPIC_COMMANDS, 1);
  }
  return ok;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_POT, INPUT);
  applyOutputs();  // mulai: pompa OFF, sirine OFF, mode AUTO
  dht.begin();

  connectWifi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(15);
  mqtt.setCallback(onMessage);
}

void loop() {
  connectWifi();

  uint32_t now = millis();
  if (!mqtt.connected()) {
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

    float rain = rainAvg.add(edge2::adcToRainMmH(analogRead(PIN_POT)));

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (!isnan(t)) lastTemp = t;  // gagal baca: pertahankan nilai valid terakhir
    if (!isnan(h)) lastHum = h;

    char buf[256];
    size_t n = edge2::formatTelemetry(buf, sizeof(buf), ++seq, rain, lastTemp, (int)lroundf(lastHum), state, now);
    Serial.println(n ? buf : "format telemetri gagal");
    if (n > 0 && mqtt.connected()) {
      mqtt.publish(TOPIC_TELEMETRY, buf, false);
    }
  }
}


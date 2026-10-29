/*
  SiagaRob - Edge 2: Pos Hujan dan Aktuator (Rumah Pompa Kali Baru)
  Board   : ESP32 DevKit v4 (Wokwi)
  Sensors : DHT22 dan potensiometer (simulasi curah hujan)
  Outputs : modul relay pada GPIO 26, buzzer pada GPIO 27

  Kontrak MQTT mengikuti PRD SiagaRob.
  PENTING: samakan PROJECT_ID dengan Edge 1, ai_server.py, dan dashboard/index.html.
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <math.h>
#include <string.h>

// -------------------- Identitas proyek --------------------
const char* PROJECT_ID = "siagarob_1739233"; 
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;

// -------------------- Pin Edge 2 --------------------
constexpr uint8_t DHT_PIN = 15;
constexpr uint8_t DHT_TYPE = DHT22;
constexpr uint8_t RAIN_POT_PIN = 34;
constexpr uint8_t PUMP_RELAY_PIN = 26;
constexpr uint8_t SIREN_BUZZER_PIN = 27;

constexpr float MAX_RAIN_MM_H = 80.0f;
constexpr uint32_t PUBLISH_INTERVAL_MS = 2000UL; // 2 detik nyata = 1 menit simulasi
constexpr uint32_t RECONNECT_INTERVAL_MS = 3000UL;
constexpr uint16_t SIREN_FREQUENCY_HZ = 2200;

// Diagram memakai relay Wokwi dengan transistor="npn" (aktif HIGH).
constexpr uint8_t RELAY_ON_LEVEL = HIGH;
constexpr uint8_t RELAY_OFF_LEVEL = LOW;

DHT dht(DHT_PIN, DHT_TYPE);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

String topicPrefix;
String telemetryTopic;
String statusTopic;
String commandsTopic;
String mqttClientId;

uint32_t lastPublishMs = 0;
uint32_t lastWifiAttemptMs = 0;
uint32_t lastMqttAttemptMs = 0;
uint32_t sequenceNumber = 0;

float rainSamples[3] = {0.0f, 0.0f, 0.0f};
uint8_t rainSampleCount = 0;
float lastTemperatureC = 0.0f;
float lastHumidityPct = 0.0f;
float filteredRainMmH = 0.0f;

bool pumpOn = false;
bool sirenOn = false;
bool sirenOutputActive = false;
String controlMode = "AUTO";

float updateRainMovingAverage(float currentRainMmH) {
  if (rainSampleCount < 3) {
    rainSamples[rainSampleCount++] = currentRainMmH;
  } else {
    rainSamples[0] = rainSamples[1];
    rainSamples[1] = rainSamples[2];
    rainSamples[2] = currentRainMmH;
  }

  float sum = 0.0f;
  for (uint8_t i = 0; i < rainSampleCount; i++) {
    sum += rainSamples[i];
  }
  return sum / rainSampleCount;
}

void applyActuatorOutputs() {
  digitalWrite(PUMP_RELAY_PIN, pumpOn ? RELAY_ON_LEVEL : RELAY_OFF_LEVEL);

  if (sirenOn) {
    tone(SIREN_BUZZER_PIN, SIREN_FREQUENCY_HZ);
    sirenOutputActive = true;
  } else if (sirenOutputActive) {
    noTone(SIREN_BUZZER_PIN);
    sirenOutputActive = false;
  }
}

void handleMqttMessage(char* topic, byte* payload, unsigned int length) {
  if (String(topic) != commandsTopic) {
    return;
  }

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.print("JSON perintah tidak valid: ");
    Serial.println(error.c_str());
    return;
  }

  const char* source = doc["source"] | "unknown";
  const char* requestedMode = doc["mode"] | "";

  // Lapisan pengaman tambahan: AI tidak boleh mengambil alih saat MANUAL.
  // Server AI juga wajib tidak menerbitkan perintah ketika mode Edge 2 MANUAL.
  if (strcmp(source, "ai") == 0 && controlMode == "MANUAL") {
    Serial.println("Perintah AI diabaikan karena perangkat sedang dalam mode MANUAL.");
    return;
  }

  if (strcmp(requestedMode, "MANUAL") == 0) {
    controlMode = "MANUAL";
  } else if (strcmp(requestedMode, "AUTO") == 0) {
    controlMode = "AUTO";
  }

  if (doc["pump"].is<const char*>()) {
    const char* requestedPump = doc["pump"] | "";
    if (strcmp(requestedPump, "ON") == 0) {
      pumpOn = true;
    } else if (strcmp(requestedPump, "OFF") == 0) {
      pumpOn = false;
    }
  }

  if (doc["siren"].is<bool>()) {
    sirenOn = doc["siren"].as<bool>();
  }

  applyActuatorOutputs();

  Serial.print("Perintah diterima dari ");
  Serial.print(source);
  Serial.print(" | mode=");
  Serial.print(controlMode);
  Serial.print(" | pump=");
  Serial.print(pumpOn ? "ON" : "OFF");
  Serial.print(" | siren=");
  Serial.println(sirenOn ? "ON" : "OFF");
}

void connectMqttIfNeeded() {
  if (WiFi.status() != WL_CONNECTED || mqtt.connected()) {
    return;
  }

  uint32_t now = millis();
  if (now - lastMqttAttemptMs < RECONNECT_INTERVAL_MS) {
    return;
  }
  lastMqttAttemptMs = now;

  Serial.print("Menghubungkan ke MQTT: ");
  Serial.println(MQTT_HOST);

  // Last Will retained, dengan status yang spesifik untuk Edge 2.
  bool connected = mqtt.connect(
    mqttClientId.c_str(),
    statusTopic.c_str(),
    1,
    true,
    "offline"
  );

  if (connected) {
    mqtt.publish(statusTopic.c_str(), "online", true);
    mqtt.subscribe(commandsTopic.c_str(), 1);
    Serial.println("MQTT tersambung; status online dipublikasikan.");
    Serial.print("Subscribe perintah: ");
    Serial.println(commandsTopic);
  } else {
    Serial.print("MQTT gagal, state=");
    Serial.println(mqtt.state());
  }
}

void maintainConnections() {
  uint32_t now = millis();

  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiAttemptMs >= RECONNECT_INTERVAL_MS) {
      lastWifiAttemptMs = now;
      Serial.println("Wi-Fi terputus; mencoba menyambungkan ulang...");
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
    }
    return;
  }

  connectMqttIfNeeded();
  if (mqtt.connected()) {
    mqtt.loop();
  }
}

void sampleAndPublishTelemetry() {
  // Potensiometer menjadi simulator curah hujan 0-80 mm/jam.
  int adc = analogRead(RAIN_POT_PIN);
  float currentRainMmH = (static_cast<float>(adc) / 4095.0f) * MAX_RAIN_MM_H;
  filteredRainMmH = updateRainMovingAverage(currentRainMmH);

  // Simpan pembacaan terakhir yang valid bila DHT sesaat gagal dibaca.
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();
  if (!isnan(temp)) {
    lastTemperatureC = temp;
  }
  if (!isnan(humidity)) {
    lastHumidityPct = humidity;
  }

  JsonDocument doc;
  doc["device_id"] = "edge2";
  doc["seq"] = ++sequenceNumber;
  doc["rain_mm_h"] = filteredRainMmH;
  doc["temp_c"] = lastTemperatureC;
  doc["hum_pct"] = lastHumidityPct;
  doc["pump"] = pumpOn ? "ON" : "OFF";
  doc["siren"] = sirenOn;
  doc["mode"] = controlMode;
  doc["uptime_ms"] = millis();

  char payload[256];
  size_t payloadLength = serializeJson(doc, payload, sizeof(payload));

  if (payloadLength == 0 || !mqtt.publish(telemetryTopic.c_str(), payload)) {
    Serial.println("Telemetri gagal dikirim.");
    return;
  }

  Serial.print("Telemetri Edge 2: ");
  Serial.println(payload);
}

void setup() {
  Serial.begin(115200);

  pinMode(RAIN_POT_PIN, INPUT);
  pinMode(PUMP_RELAY_PIN, OUTPUT);
  pinMode(SIREN_BUZZER_PIN, OUTPUT);
  analogReadResolution(12);

  // Pastikan aktuator mati sebelum jaringan mulai tersambung.
  pumpOn = false;
  sirenOn = false;
  controlMode = "AUTO";
  digitalWrite(PUMP_RELAY_PIN, RELAY_OFF_LEVEL);

  dht.begin();

  topicPrefix = String("siagarob/") + PROJECT_ID;
  telemetryTopic = topicPrefix + "/edge/edge2/telemetry";
  statusTopic = topicPrefix + "/edge/edge2/status";
  commandsTopic = topicPrefix + "/edge/edge2/commands";
  mqttClientId = String("siagarob-edge2-") + PROJECT_ID;

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
  lastWifiAttemptMs = millis();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(handleMqttMessage);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(30);
  mqtt.setSocketTimeout(5);

  Serial.println("SiagaRob Edge 2 dimulai.");
  Serial.print("Topic telemetri: ");
  Serial.println(telemetryTopic);
  Serial.print("Topic perintah: ");
  Serial.println(commandsTopic);
}

void loop() {
  maintainConnections();

  uint32_t now = millis();
  if (mqtt.connected() && now - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    lastPublishMs = now;
    sampleAndPublishTelemetry();
  }

  delay(5);
}
